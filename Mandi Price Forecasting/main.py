import os
import sys
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Fix Windows console encoding for characters & symbols
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# File Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'wheat_data.csv')
MODEL_FILE = os.path.join(BASE_DIR, 'mandi_model.pth')
SCALER_FILE = os.path.join(BASE_DIR, 'scaler.pkl')
CHART_FILE = os.path.join(BASE_DIR, 'forecast_graph.png')

# Model Parameters
LOOKBACK = 30       # Input window (last 30 days)
HORIZON = 7         # Multi-step forecast (next 7 days)
HIDDEN_SIZE = 64    # LSTM hidden units
NUM_LAYERS = 2      # Stacked LSTM layers
BATCH_SIZE = 16
LEARNING_RATE = 0.002
EPOCHS = 80
PATIENCE = 10

# -------------------------------------------------------------
# 1. Neural Network Architecture (Stacked LSTM)
# -------------------------------------------------------------
class MandiPriceLSTM(nn.Module):
    """
    2-Layer Stacked LSTM with Dropout and Dense Projection Head.
    Directly predicts all 7 future days to eliminate compounding rollout errors.
    """
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=7, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        out, _ = self.lstm(x)
        last_hidden = out[:, -1, :]
        return self.fc(last_hidden)

# -------------------------------------------------------------
# 2. PyTorch Dataset & Sliding Window
# -------------------------------------------------------------
class TimeSeriesDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def create_sequences(data, lookback=30, horizon=7):
    X, y = [], []
    for i in range(len(data) - lookback - horizon + 1):
        X.append(data[i : i + lookback])
        y.append(data[i + lookback : i + lookback + horizon, 0])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)

# -------------------------------------------------------------
# 3. Main End-to-End Pipeline
# -------------------------------------------------------------
def run_pipeline():
    print("=" * 72)
    print("🌾 MANDI 7-DAY PRICE FORECASTING SYSTEM (DEEP LEARNING LSTM)")
    print("=" * 72)

    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found!")
        sys.exit(1)

    # Load dataset
    print(f"\n[1/5] Loading and preprocessing dataset: {os.path.basename(DATA_FILE)}...")
    df = pd.read_csv(DATA_FILE)
    df['Date'] = pd.to_datetime(df['Price Date'], format='%d/%m/%Y')
    df = df.sort_values('Date').reset_index(drop=True)

    commodity = df['Commodity'].iloc[0] if 'Commodity' in df.columns else 'Wheat'
    market = df['Market'].iloc[0] if 'Market' in df.columns else 'Jaipur APMC'

    # Resample to continuous daily series (forward-fill closed market days)
    df_daily = df.set_index('Date').resample('D').ffill().reset_index()
    prices = df_daily['Modal Price'].values.astype(np.float32).reshape(-1, 1)

    total_pts = len(prices)
    start_d = df_daily['Date'].min().strftime('%d %b %Y')
    end_d = df_daily['Date'].max().strftime('%d %b %Y')
    last_price = float(df_daily['Modal Price'].iloc[-1])

    print(f"  • Commodity:          {commodity} ({market})")
    print(f"  • Raw Records:        {len(df)} trade days")
    print(f"  • Continuous Days:    {total_pts} days ({start_d} -> {end_d})")
    print(f"  • Last Trading Price: ₹{last_price:.2f} / quintal")

    # Chronological Split: 80% Train, 10% Validation, 10% Test
    train_size = int(total_pts * 0.8)
    val_size = int(total_pts * 0.1)
    test_size = total_pts - train_size - val_size

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(prices[:train_size])

    with open(SCALER_FILE, 'wb') as f:
        pickle.dump(scaler, f)

    all_scaled = scaler.transform(prices)
    X_all, y_all = create_sequences(all_scaled, LOOKBACK, HORIZON)

    train_end = train_size - LOOKBACK - HORIZON + 1
    val_end = train_end + val_size

    X_train, y_train = X_all[:train_end], y_all[:train_end]
    X_val, y_val = X_all[train_end:val_end], y_all[train_end:val_end]
    X_test, y_test = X_all[val_end:], y_all[val_end:]

    train_loader = DataLoader(TimeSeriesDataset(X_train, y_train), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(TimeSeriesDataset(X_val, y_val), batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(TimeSeriesDataset(X_test, y_test), batch_size=BATCH_SIZE, shuffle=False)

    # Hardware Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'
    print(f"\n[2/5] Initializing LSTM model on: {device} ({device_name})...")

    torch.manual_seed(42)
    model = MandiPriceLSTM(
        input_size=1,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
        output_size=HORIZON,
        dropout=0.2
    ).to(device)

    criterion = nn.HuberLoss(delta=1.0)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    # Training
    print("\n[3/5] Training fresh LSTM model...")
    best_val_loss = float('inf')
    best_weights = None
    no_improve = 0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0.0
        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item() * len(bx)
        train_loss /= len(X_train)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(device), by.to(device)
                val_loss += criterion(model(bx), by).item() * len(bx)
        val_loss /= len(X_val)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = model.state_dict().copy()
            no_improve = 0
        else:
            no_improve += 1

        if epoch % 10 == 0 or epoch == 1:
            print(f"  • Epoch [{epoch:02d}/{EPOCHS}] | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")

        if no_improve >= PATIENCE:
            print(f"  • Early stopping triggered at epoch {epoch}")
            break

    model.load_state_dict(best_weights)
    torch.save(best_weights, MODEL_FILE)
    print(f"  ✓ Optimal model weights saved to {os.path.basename(MODEL_FILE)}")

    # Model Evaluation on Unseen Test Data
    print("\n[4/5] Evaluating performance on unseen test data...")
    model.eval()
    with torch.no_grad():
        preds, trues = [], []
        for bx, by in test_loader:
            bx = bx.to(device)
            preds.append(model(bx).cpu().numpy())
            trues.append(by.numpy())
        preds = np.vstack(preds)
        trues = np.vstack(trues)

    dummy = np.zeros((preds.shape[0] * HORIZON, 1))
    dummy[:, 0] = preds.flatten()
    preds_inr = scaler.inverse_transform(dummy).reshape(preds.shape)

    dummy[:, 0] = trues.flatten()
    trues_inr = scaler.inverse_transform(dummy).reshape(trues.shape)

    mae = float(mean_absolute_error(trues_inr, preds_inr))
    rmse = float(np.sqrt(mean_squared_error(trues_inr, preds_inr)))
    mape = float(np.mean(np.abs((trues_inr - preds_inr) / trues_inr)) * 100)
    acc = float(max(0.0, 100.0 - mape))
    r2 = float(r2_score(trues_inr.flatten(), preds_inr.flatten()))
    residuals = (trues_inr - preds_inr).flatten()
    res_std = float(np.std(residuals))

    print("-" * 72)
    print("📊 MODEL EVALUATION SCORECARD (TEST SET)")
    print("-" * 72)
    print(f"  • Forecast Accuracy:             {acc:.2f} %")
    print(f"  • Mean Absolute Error (MAE):     ₹ {mae:.2f} / quintal")
    print(f"  • Root Mean Squared Error (RMSE): ₹ {rmse:.2f} / quintal")
    print(f"  • Mean Absolute % Error (MAPE):  {mape:.2f} %")
    print(f"  • Coefficient of Determ. (R²):   {r2:.4f}")
    print(f"  • 95% Confidence Margin (±1.96σ): ± ₹ {1.96 * res_std:.2f}")

    # Generate 7-Day Forecast from the latest 30 days
    print("\n[5/5] Generating 7-Day Forward Price Forecast...")
    last_window = all_scaled[-LOOKBACK:].reshape(1, LOOKBACK, 1)
    with torch.no_grad():
        future_scaled = model(torch.tensor(last_window, dtype=torch.float32).to(device)).cpu().numpy().reshape(-1, 1)
        future_prices = scaler.inverse_transform(future_scaled).flatten()

    last_date = df_daily['Date'].iloc[-1]
    forecast_rows = []
    prev = last_price

    for day_i, price_val in enumerate(future_prices, start=1):
        target_date = last_date + pd.Timedelta(days=day_i)
        p_round = round(float(price_val), 2)
        delta = round(p_round - prev, 2)
        pct = round((delta / prev) * 100, 2) if prev != 0 else 0.0

        if delta > 1.5:
            trend = "Bullish ▲"
        elif delta < -1.5:
            trend = "Bearish ▼"
        else:
            trend = "Stable ▬"

        ci_low = round(p_round - 1.96 * res_std, 2)
        ci_high = round(p_round + 1.96 * res_std, 2)

        forecast_rows.append({
            "day": day_i,
            "date": target_date.strftime('%Y-%m-%d'),
            "day_name": target_date.strftime('%A'),
            "predicted_price": p_round,
            "delta": delta,
            "pct": pct,
            "trend": trend,
            "ci_low": ci_low,
            "ci_high": ci_high
        })
        prev = p_round

    # Display in Terminal
    print("\n" + "=" * 72)
    print(f"🔮 7-DAY MANDI PRICE FORECAST ({commodity.upper()} - {market.upper()})")
    print(f"Baseline (Last Recorded Close: {last_date.strftime('%d %b %Y')}): ₹ {last_price:.2f}")
    print("=" * 72)
    header = f"{'Day':<6} {'Date':<12} {'Day of Week':<11} {'Predicted':<12} {'Change (₹)':<11} {'Trend':<11} {'95% CI Range':<16}"
    print(header)
    print("-" * 72)

    for r in forecast_rows:
        d_str = f"{'+' if r['delta'] >= 0 else ''}{r['delta']:.2f} ({r['pct']:+.1f}%)"
        ci_str = f"₹{r['ci_low']:.0f} - ₹{r['ci_high']:.0f}"
        print(f"Day {r['day']:<2} {r['date']:<12} {r['day_name']:<11} ₹ {r['predicted_price']:<9.2f} {d_str:<11} {r['trend']:<11} {ci_str:<16}")

    print("=" * 72)

    # 7-Day Net Change Summary
    net_7d_change = forecast_rows[-1]['predicted_price'] - last_price
    net_7d_pct = (net_7d_change / last_price) * 100
    avg_predicted = np.mean([r['predicted_price'] for r in forecast_rows])
    overall_trend = "BULLISH (Upward Momentum)" if net_7d_change > 0 else "BEARISH (Downward Momentum)"

    print(f"• 7-Day Expected Average:    ₹ {avg_predicted:.2f} / quintal")
    print(f"• 7-Day Net Projected Shift: {'+' if net_7d_change >= 0 else ''}{net_7d_change:.2f} ₹ ({net_7d_pct:+.2f}%)")
    print(f"• Weekly Market Outlook:     {overall_trend}")
    print("=" * 72)

    # Save Graph
    save_forecast_graph(df_daily, forecast_rows, commodity, market, last_date, last_price, acc, mae, rmse)
    print(f"\n✓ High-resolution graph saved to: {CHART_FILE}")
    print("✓ Project execution complete!\n")

# -------------------------------------------------------------
# 4. Graph Generation
# -------------------------------------------------------------
def save_forecast_graph(df_daily, forecast_rows, commodity, market, last_date, last_price, acc, mae, rmse):
    recent_history = df_daily.tail(60).copy()
    fc_df = pd.DataFrame(forecast_rows)
    fc_df['Date'] = pd.to_datetime(fc_df['date'])

    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(
        2, 1, 
        figsize=(14, 8.5), 
        gridspec_kw={'height_ratios': [2.8, 1.2]}, 
        dpi=180
    )
    fig.patch.set_facecolor('#0d1117')
    ax1.set_facecolor('#161b22')
    ax2.set_facecolor('#161b22')

    # Top Panel: Price Line & Forecast
    ax1.plot(
        recent_history['Date'], 
        recent_history['Modal Price'], 
        color='#58a6ff', 
        linewidth=2.0, 
        label='Actual Mandi Price (Past 60 Days)'
    )
    ax1.fill_between(
        recent_history['Date'], 
        recent_history['Modal Price'], 
        recent_history['Modal Price'].min() - 20, 
        color='#58a6ff', 
        alpha=0.08
    )

    combined_dates = [last_date] + fc_df['Date'].tolist()
    combined_prices = [last_price] + fc_df['predicted_price'].tolist()
    combined_lowers = [last_price] + fc_df['ci_low'].tolist()
    combined_uppers = [last_price] + fc_df['ci_high'].tolist()

    ax1.plot(
        combined_dates, 
        combined_prices, 
        color='#3fb950', 
        linewidth=2.6, 
        linestyle='--', 
        marker='o', 
        markersize=6, 
        label='7-Day LSTM Forecast'
    )
    ax1.fill_between(
        combined_dates, 
        combined_lowers, 
        combined_uppers, 
        color='#238636', 
        alpha=0.25, 
        label='95% Confidence Interval'
    )

    ax1.axvline(x=last_date, color='#8b949e', linestyle=':', linewidth=1.4)
    ax1.scatter([last_date], [last_price], color='#f0883e', s=80, zorder=5, label=f'Close: ₹{last_price:.1f}')

    # Forecast price labels
    for _, row in fc_df.iterrows():
        sign = '+' if row['delta'] >= 0 else ''
        ax1.annotate(
            f"₹{row['predicted_price']:.1f}\n({sign}{row['delta']:.1f})",
            xy=(row['Date'], row['predicted_price']),
            xytext=(0, 14),
            textcoords='offset points',
            ha='center',
            fontsize=7.5,
            color='#56d364',
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#0d1117', edgecolor='#238636', alpha=0.9, linewidth=0.7)
        )

    ax1.set_title(
        f"Mandi Price Forecasting System — 7-Day AI Prediction\n"
        f"Commodity: {commodity.upper()} | Market: {market.upper()} | Model: 2-Layer LSTM",
        fontsize=13, fontweight='bold', color='#f0f6fc', pad=12
    )
    ax1.set_ylabel('Modal Price (₹/Quintal)', fontsize=10, color='#c9d1d9')
    ax1.grid(True, linestyle='--', alpha=0.25, color='#30363d')
    ax1.legend(loc='upper left', framealpha=0.88, facecolor='#161b22', edgecolor='#30363d', fontsize=8.5)

    # Scorecard Box
    info_str = f"Accuracy: {acc:.2f}%\nMAE:  ₹{mae:.2f}\nRMSE: ₹{rmse:.2f}"
    ax1.text(
        0.985, 0.95, info_str,
        transform=ax1.transAxes,
        fontsize=8.5,
        va='top',
        ha='right',
        fontfamily='monospace',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#090d13', edgecolor='#58a6ff', alpha=0.9)
    )

    # Bottom Panel: Daily Delta
    bar_colors = ['#238636' if d >= 0 else '#da3633' for d in fc_df['delta']]
    bars = ax2.bar(fc_df['Date'], fc_df['delta'], color=bar_colors, width=0.45, edgecolor='#30363d')
    ax2.axhline(0, color='#8b949e', linewidth=1.0)
    ax2.set_ylabel('Day Δ (₹)', fontsize=9.5, color='#c9d1d9')
    ax2.set_xlabel('Forecast Dates', fontsize=10, color='#c9d1d9')
    ax2.grid(True, linestyle='--', alpha=0.25, color='#30363d')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%a, %d %b'))
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))

    for bar, d, pct in zip(bars, fc_df['delta'], fc_df['pct']):
        y_p = bar.get_height() + (0.5 if d >= 0 else -1.2)
        color = '#3fb950' if d >= 0 else '#f85149'
        ax2.text(
            bar.get_x() + bar.get_width() / 2, 
            y_p, 
            f"{'+' if d >= 0 else ''}{d:.1f} ({pct:+.1f}%)", 
            ha='center', 
            va='bottom' if d >= 0 else 'top', 
            fontsize=7.5, 
            fontweight='bold', 
            color=color
        )

    for ax in [ax1, ax2]:
        for spine in ax.spines.values():
            spine.set_color('#30363d')
        ax.tick_params(colors='#8b949e', labelsize=8.5)

    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=8))

    plt.tight_layout()
    plt.savefig(CHART_FILE, dpi=180, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()

if __name__ == '__main__':
    run_pipeline()
