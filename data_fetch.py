import yfinance as yf
import pandas as pd
from io import StringIO
import requests
import os
import warnings
import numpy as np
from datetime import datetime, timedelta

warnings.simplefilter(action='ignore', category=FutureWarning)

# === Step 1: Get Nifty 50 Tickers ===
def get_nifty_50_symbols():
    url = "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
        df = pd.read_csv(StringIO(res.text))
        return list(df['Symbol'].str.strip().str.upper())  # only symbol, no .NS
    else:
        raise Exception("Failed to fetch Nifty 50 list from NSE.")

# === Step 2: Get Daily Close Prices ===
def get_daily_closing_prices(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, interval="1d", progress=False)
        if df.empty or "Close" not in df.columns:
            print(f"⚠️ No data for {ticker}")
            return None
        close_series = df["Close"]
        close_series.index = close_series.index.strftime("%Y-%m-%d")
        return close_series
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {e}")
        return None

# === Step 3: Build and Append Daily Data ===
def append_daily_nifty_csv():
    output_path = "daily_ma_nifty50_June1.csv"

    if os.path.exists(output_path):
        df_existing = pd.read_csv(output_path, index_col="Stock")
        existing_dates = list(df_existing.columns)
        last_date = max(pd.to_datetime(existing_dates))
        fetch_start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        df_existing = None
        fetch_start = "2025-06-01"

    fetch_end = datetime.today().strftime("%Y-%m-%d")
    print(f"\n📅 Fetching data from {fetch_start} to {fetch_end}")

    symbols = get_nifty_50_symbols()
    all_data = {}
    all_dates = set()
    daily_data = {}

    for symbol in symbols:
        full_symbol = f"{symbol}.NS"  # Use .NS for yfinance
        print(f"\n📈 Fetching {full_symbol}...")
        close_series = get_daily_closing_prices(full_symbol, start=fetch_start, end=fetch_end)
        if close_series is not None:
            daily_data[symbol] = close_series  # Save only the symbol
            all_dates.update(close_series.index)
        else:
            daily_data[symbol] = None

    sorted_dates = sorted(all_dates)

    if not sorted_dates:
        print("✅ No new data to append.")
        return

    for symbol in symbols:
        series = daily_data.get(symbol)
        if series is None:
            all_data[symbol] = ["null"] * len(sorted_dates)
        else:
            series = series.reindex(sorted_dates)
            values = series.values.flatten()
            row = []
            for val in values:
                if isinstance(val, (int, float, np.integer, np.floating)):
                    row.append(f"{val:.2f}")
                else:
                    row.append("null")
            all_data[symbol] = row

    df_new = pd.DataFrame.from_dict(all_data, orient="index", columns=sorted_dates)
    df_new.index.name = "Stock"

    if df_existing is not None:
        df_combined = pd.concat([df_existing, df_new], axis=1)
    else:
        df_combined = df_new

    df_combined.to_csv(output_path)
    print(f"\n✅ Updated CSV saved to '{output_path}'")

# === Run Script ===
if __name__ == "__main__":
    append_daily_nifty_csv()