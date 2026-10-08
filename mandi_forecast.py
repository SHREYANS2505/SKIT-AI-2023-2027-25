#!/usr/bin/env python3
"""
Mandi price forecaster  -  predicts the next 7 days of Modal Price.

Works on ANY Agmarknet-style CSV (wheat, mustard, bajra, onion ...). It needs
only these columns (names are auto-detected, case-insensitive):
    Price Date | Modal Price | Commodity | Market   (Commodity/Market optional)

Usage:
    python mandi_forecast.py --file combined.csv
    python mandi_forecast.py --file mustard.csv --market "Bassi APMC"
    python mandi_forecast.py --file all_crops.csv --commodity Bajra
    python mandi_forecast.py --file x.csv --horizon 7 --out results/

If the file holds several commodities, every commodity is forecast
separately (or pick one with --commodity).
"""
import argparse, json, os, re, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
SEED = 42


# ----------------------------------------------------------------- 1. LOAD
def find_col(cols, key, exclude=()):
    for c in cols:
        if key in c.lower() and not any(e in c.lower() for e in exclude):
            return c
    return None


def load(path, commodity=None, market=None):
    df = pd.read_csv(path)
    dcol = find_col(df.columns, "date")
    pcol = find_col(df.columns, "modal")
    ccol = find_col(df.columns, "commodity", exclude=("group",))
    mcol = find_col(df.columns, "market")
    if dcol is None or pcol is None:
        raise SystemExit("CSV needs a date column and a 'Modal Price' column")

    # dates: mixed formats like '8/6/2026' and '27-05-2026' (day-first)
    ds = df[dcol].astype(str).str.strip()
    iso = ds.str.match(r"^\d{4}-\d{1,2}-\d{1,2}")           # 2026-05-12 -> year-month-day
    dates = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    if iso.any():
        dates[iso] = pd.to_datetime(ds[iso].str[:10], format="%Y-%m-%d", errors="coerce")
    if (~iso).any():                                          # 8/6/2026, 27-05-2026 -> day-first
        dates[~iso] = pd.to_datetime(ds[~iso], dayfirst=True, format="mixed", errors="coerce")
    df["date"] = dates
    df["price"] = pd.to_numeric(df[pcol].astype(str).str.replace(",", ""), errors="coerce")
    df["commodity"] = df[ccol] if ccol else "Commodity"
    df["market"] = df[mcol] if mcol else "ALL"
    n0 = len(df)
    df = df.dropna(subset=["date", "price"])
    df = df[df["price"] > 0]
    if commodity:
        df = df[df["commodity"].str.lower() == commodity.lower()]
    if market:
        df = df[df["market"].str.lower() == market.lower()]
    if df.empty:
        raise SystemExit("No rows left after filtering - check --commodity / --market")
    return df[["date", "price", "commodity", "market"]].sort_values("date"), n0


# ----------------------------------------------------------------- 2. CLEAN
def remove_outliers(df):
    """Drop rows that jump >30% away from the local (+-30 day) median (typos)."""
    s = df.set_index("date")["price"]
    med = s.rolling("61D", center=True, min_periods=5).median()
    ok = ((s / med - 1).abs() <= 0.30) | med.isna()
    removed = int((~ok.values).sum())
    return df[ok.values], removed


def daily_series(df):
    """One value per calendar day: median Modal Price over all rows that day."""
    d = df.groupby("date")["price"].median()
    full = pd.date_range(d.index.min(), d.index.max(), freq="D")
    observed = pd.Series(full.isin(d.index), index=full)
    y = d.reindex(full).interpolate(limit=10, limit_area="inside")  # short gaps only
    cnt = df.groupby("date").size().reindex(full).fillna(0)
    return y, observed, cnt


# ------------------------------------------------------------ 3. FEATURES
LAGS = [0, 1, 2, 3, 5, 7, 10, 14, 21, 28]


def make_features(y, cnt):
    """Features known at origin day t (no future information)."""
    ly = np.log(y)
    f = pd.DataFrame(index=y.index)
    for k in LAGS:
        f[f"lag{k}"] = ly.shift(k) - ly            # relative to today's price
    for w in (7, 14, 30, 60):
        f[f"rmean{w}"] = ly.rolling(w, min_periods=3).mean() - ly
    for w in (7, 30):
        f[f"rstd{w}"] = ly.diff().rolling(w, min_periods=3).std()
    f["mom7"] = ly - ly.shift(7)
    f["mom30"] = ly - ly.shift(30)
    f["n7"] = cnt.rolling(7).sum()
    f["dow"] = y.index.dayofweek
    f["lvl"] = ly - ly.rolling(365, min_periods=60).mean()   # distance from 1y level
    f["doy_s"] = np.sin(2 * np.pi * y.index.dayofyear / 365.25)
    f["doy_c"] = np.cos(2 * np.pi * y.index.dayofyear / 365.25)
    return f


def build_xy(y, f, h):
    """Target = log(y[t+h]) - log(y[t])."""
    tgt = np.log(y).shift(-h) - np.log(y)
    d = f.copy()
    d["tdow"] = (y.index + pd.Timedelta(days=h)).dayofweek
    d["target"] = tgt
    return d


MODELS = {
    "ridge": lambda: make_pipeline(StandardScaler(), Ridge(alpha=30.0)),
    "gbm": lambda: HistGradientBoostingRegressor(
        max_depth=3, learning_rate=0.05, max_iter=150, min_samples_leaf=30,
        l2_regularization=1.0, random_state=SEED),
}


def fit_predict(train, test_X, names):
    """Train each model on train, return dict name -> predictions (log-return)."""
    Xcols = [c for c in train.columns if c != "target"]
    out = {"naive": np.zeros(len(test_X))}
    tr = train.dropna()
    for n in names:
        m = MODELS[n]()
        m.fit(tr[Xcols].values, tr["target"].values)
        out[n] = m.predict(test_X[Xcols].fillna(0).values)
    out["ensemble"] = (out["ridge"] + out["gbm"]) / 2 if {"ridge", "gbm"} <= set(names) else out[names[0]]
    return out


# ------------------------------------------------------------ 4. BACKTEST
def backtest(y, observed, f, horizon, test_days=365, step=30):
    """Expanding-window walk-forward. Returns per-model/per-horizon errors."""
    names = list(MODELS)
    idx = y.index
    last_origin = idx[-1] - pd.Timedelta(days=horizon)
    start = max(idx[0] + pd.Timedelta(days=400), last_origin - pd.Timedelta(days=test_days))
    folds = pd.date_range(start, last_origin, freq=f"{step}D")
    rows = []
    for fs in folds:
        fe = min(fs + pd.Timedelta(days=step - 1), last_origin)
        for h in range(1, horizon + 1):
            d = build_xy(y, f, h)
            train = d[d.index + pd.Timedelta(days=h) <= fs]       # target known by fold start
            test = d[(d.index >= fs) & (d.index <= fe)].dropna(subset=["target"])
            tgt_dates = test.index + pd.Timedelta(days=h)
            keep = observed.reindex(tgt_dates).values               # score on real observations only
            test = test[keep]
            if len(test) == 0 or train.dropna().shape[0] < 200:
                continue
            preds = fit_predict(train, test, names)
            base = y.reindex(test.index).values
            actual = base * np.exp(test["target"].values)
            for n, p in preds.items():
                rows.append(pd.DataFrame({
                    "model": n, "h": h, "actual": actual, "pred": base * np.exp(p),
                    "logerr": test["target"].values - p}))
    return pd.concat(rows, ignore_index=True)


def summarize(bt):
    bt = bt.copy()
    bt["ae"] = (bt.actual - bt.pred).abs()
    bt["ape"] = bt.ae / bt.actual * 100
    s = bt.groupby("model").agg(MAE=("ae", "mean"), MAPE=("ape", "mean"), n=("ae", "size"))
    return s.sort_values("MAE")


# ------------------------------------------------------------ 5. FORECAST
def forecast(y, f, horizon, best, bt):
    rows = []
    names = list(MODELS)
    x_now = f.iloc[[-1]]
    for h in range(1, horizon + 1):
        d = build_xy(y, f, h)
        train = d[d.index + pd.Timedelta(days=h) <= y.index[-1]]
        x = x_now.copy()
        x["tdow"] = (y.index[-1] + pd.Timedelta(days=h)).dayofweek
        p = fit_predict(train, x, names)[best][0]
        resid = bt[(bt.model == best) & (bt.h == h)]["logerr"]
        lo_q, hi_q = (resid.quantile([0.10, 0.90]).values if len(resid) > 20 else (-0.04, 0.04))
        base = y.iloc[-1]
        rows.append({
            "date": (y.index[-1] + pd.Timedelta(days=h)).date(),
            "forecast_rs_per_quintal": round(base * np.exp(p), 1),
            "low_80": round(base * np.exp(p + lo_q), 1),
            "high_80": round(base * np.exp(p + hi_q), 1)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------- 6. PLOT
def plot(y, fc, name, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 4.5))
    h = y.iloc[-120:]
    ax.plot(h.index, h.values, color="#1f4e79", lw=1.6, label="Actual (daily median)")
    fd = pd.to_datetime(fc["date"])
    ax.plot(fd, fc.forecast_rs_per_quintal, color="#d95f02", marker="o", lw=2, label="7-day forecast")
    ax.fill_between(fd, fc.low_80, fc.high_80, color="#d95f02", alpha=0.2, label="80% range")
    ax.set_title(f"{name} - Modal price forecast (Rs/Quintal)")
    ax.grid(alpha=0.3); ax.legend(); fig.autofmt_xdate(); fig.tight_layout()
    fig.savefig(path, dpi=130); plt.close(fig)


# ---------------------------------------------------------------- MAIN
def run_one(df, label, horizon, outdir, quiet=False):
    df, removed = remove_outliers(df)
    y, observed, cnt = daily_series(df)
    f = make_features(y, cnt)
    bt = backtest(y, observed, f, horizon)
    summ = summarize(bt)
    best = summ.index[0]
    fc = forecast(y, f, horizon, best, bt)
    per_h = (bt[bt.model == best].assign(ape=lambda d: (d.actual - d.pred).abs() / d.actual * 100)
             .groupby("h")["ape"].mean().round(2).to_dict())
    safe = re.sub(r"[^A-Za-z0-9]+", "_", label).strip("_")
    os.makedirs(outdir, exist_ok=True)
    fc.to_csv(os.path.join(outdir, f"forecast_{safe}.csv"), index=False)
    plot(y, fc, label, os.path.join(outdir, f"forecast_{safe}.png"))
    res = {"label": label, "rows_used": int(len(df)), "outliers_removed": removed,
           "data_from": str(y.index[0].date()), "data_to": str(y.index[-1].date()),
           "last_price": round(float(y.iloc[-1]), 1), "best_model": best,
           "backtest": summ.round(2).reset_index().to_dict("records"),
           "mape_by_horizon_best_model": per_h,
           "forecast": fc.to_dict("records")}
    with open(os.path.join(outdir, f"report_{safe}.json"), "w") as fh:
        json.dump(res, fh, indent=2, default=str)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--commodity"); ap.add_argument("--market")
    ap.add_argument("--horizon", type=int, default=7)
    ap.add_argument("--out", default="forecast_output")
    a = ap.parse_args()

    df, n0 = load(a.file, a.commodity, a.market)
    print(f"Loaded {n0} rows, {len(df)} usable | {df.date.min().date()} -> {df.date.max().date()}")
    results = []
    for com, g in df.groupby("commodity"):
        label = com + (f" [{a.market}]" if a.market else " [all mandis]")
        if g.date.nunique() < 500:
            print(f"Skipping {com}: only {g.date.nunique()} price days (need 500+)"); continue
        r = run_one(g, label, a.horizon, a.out)
        results.append(r)
        print(f"\n=== {label} ===  last actual ({r['data_to']}): Rs {r['last_price']}/qtl")
        print("Backtest (last ~12 months, walk-forward):")
        for b in r["backtest"]:
            print(f"   {b['model']:9s} MAE Rs {b['MAE']:7.1f}   MAPE {b['MAPE']:.2f}%")
        print(f"Best model: {r['best_model']}")
        print(pd.DataFrame(r["forecast"]).to_string(index=False))
    return results


if __name__ == "__main__":
    main()
