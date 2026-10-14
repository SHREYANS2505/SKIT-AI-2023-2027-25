import sqlite3
import requests
from datetime import datetime

# ================= 1. CONFIGURATION (Aap yahan change kar sakte ho) =================
API_KEY = ""

# State & District (Jaipur ya poora Rajasthan)
STATE = "Rajasthan"
DISTRICT = ""  # Agar specific "Jaipur" chahiye to "Jaipur" likhein, varna poore Rajasthan ke liye "" chhod dein

# Jo crops chahiye unke naam aur unki table ka naam:
# Yahan aap nayi crop add ya change kar sakte ho
CROPS = {
    "Wheat": "wheat",
    "Mustard": "mustard",
    "Bengal Gram(Gram)(Whole)": "gram"   # Chana / Gram
}

# SQLite database file ka naam
DB_NAME = "crop_prices.db"

# API details
API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
HEADERS = {"User-Agent": "Mozilla/5.0"}
# ===================================================================================


def init_db():
    """Har crop ke liye alag table banata hai"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for table_name in CROPS.values():
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                date TEXT PRIMARY KEY,
                min_price REAL,
                max_price REAL,
                modal_price REAL
            )
        """)
        print(f"Table ready: {table_name}")

    conn.commit()
    conn.close()


def parse_date(date_str):
    """Date ko model training ke liye standard 'YYYY-MM-DD' format me convert karta hai"""
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d")
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now().strftime("%Y-%m-%d")


def fetch_and_store():
    """Rajasthan mandi se data leke har crop ki table me store karta hai"""
    today_date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for crop_name, table_name in CROPS.items():
        print(f"\nFetching data for: {crop_name} ({STATE}{' - ' + DISTRICT if DISTRICT else ''})...")

        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": 500,
            "filters[state]": STATE,
            "filters[commodity]": crop_name
        }
        if DISTRICT:
            params["filters[district]"] = DISTRICT

        try:
            response = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
            records = response.json().get("records", [])

            if not records:
                print(f"Warning: {crop_name} ke liye aaj koi data nahi mila.")
                continue

            min_list = []
            max_list = []
            modal_list = []
            arrival_date_str = None

            for r in records:
                try:
                    min_p = float(r.get("min_price", 0))
                    max_p = float(r.get("max_price", 0))
                    modal_p = float(r.get("modal_price", 0))

                    if min_p > 0: min_list.append(min_p)
                    if max_p > 0: max_list.append(max_p)
                    if modal_p > 0: modal_list.append(modal_p)

                    if not arrival_date_str and r.get("arrival_date"):
                        arrival_date_str = r.get("arrival_date")
                except (ValueError, TypeError):
                    continue

            if not modal_list:
                print(f"{crop_name}: Valid prices nahi mile.")
                continue

            # Model training ke liye roz ka average price (Clean single row per day)
            avg_min = round(sum(min_list) / len(min_list), 2)
            avg_max = round(sum(max_list) / len(max_list), 2)
            avg_modal = round(sum(modal_list) / len(modal_list), 2)
            row_date = parse_date(arrival_date_str) if arrival_date_str else today_date

            # Table me date, min_price, max_price, modal_price store karein
            cursor.execute(f"""
                INSERT OR REPLACE INTO {table_name} (date, min_price, max_price, modal_price)
                VALUES (?, ?, ?, ?)
            """, (row_date, avg_min, avg_max, avg_modal))

            print(f"Data saved in '{table_name}': Date={row_date}, Min={avg_min}, Max={avg_max}, Modal={avg_modal}")

        except Exception as e:
            print(f"Error fetching {crop_name}: {e}")

    conn.commit()
    conn.close()
    print("\n Sabhi crops ka data database me successfully save ho gaya!")


if __name__ == "__main__":
    init_db()
    fetch_and_store()
