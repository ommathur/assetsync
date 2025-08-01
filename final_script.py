import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
from kiteconnect import KiteConnect

load_dotenv()

# === Zerodha Setup ===
api_key = os.getenv("ZERODHA_API_KEY")
access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# === Constants ===
CSV_PATH = "daily_ma_nifty50_June1.csv"
LOG_PATH = "live_portfolio_log.csv"
HOLDINGS_PATH = "current_holdings.csv"
CAPITAL = 200000
UNIT_ALLOCATION = CAPITAL / 40

# === Load Nifty 50 Symbols and 20DMA ===
nifty_50 = set(pd.read_csv(CSV_PATH, index_col="Stock").index.tolist())
df_price = pd.read_csv(CSV_PATH, index_col="Stock").transpose()
df_price.index = pd.to_datetime(df_price.index)

# === Load Zerodha Holdings and filter for Nifty 50 ===
try:
    zerodha_holdings = kite.holdings()
    df_zerodha = pd.DataFrame([{
        "Stock": h["tradingsymbol"],
        "Qty": h["quantity"],
        "Avg Buy Price": h["average_price"],
        "Exchange": None
    } for h in zerodha_holdings if h["tradingsymbol"] in nifty_50])
    print("\n📥 Zerodha Nifty 50 Holdings:")
    print(df_zerodha if not df_zerodha.empty else "No holdings in Nifty 50")
except Exception as e:
    print("Error fetching holdings from Zerodha:", e)
    df_zerodha = pd.DataFrame(columns=["Stock", "Qty", "Avg Buy Price", "Exchange"])

# === Load previous holdings CSV and merge ===
if os.path.exists(HOLDINGS_PATH):
    df_prev_holdings = pd.read_csv(HOLDINGS_PATH)
    df_holdings = pd.concat([df_prev_holdings, df_zerodha]).drop_duplicates(subset="Stock", keep="last")
else:
    df_holdings = df_zerodha.copy()
    if df_holdings.empty:
        df_holdings = pd.DataFrame(columns=["Stock", "Qty", "Avg Buy Price", "Exchange"])

# === Setup Log ===
if os.path.exists(LOG_PATH):
    df_log = pd.read_csv(LOG_PATH)
else:
    df_log = pd.DataFrame(columns=["Date", "Action", "Stock", "Price", "Qty", "Exchange", "PnL", "Cash Left", "Holdings Value", "Total PnL"])

# === Utility Functions ===
def get_best_buy_price(symbol):
    prices = {}
    try:
        nse = yf.Ticker(symbol + ".NS").history(period="1d", interval="1m")
        if not nse.empty:
            prices["NSE"] = float(nse.iloc[-1]['Close'])
    except:
        pass
    try:
        bse = yf.Ticker(symbol + ".BO").history(period="1d", interval="1m")
        if not bse.empty:
            prices["BSE"] = float(bse.iloc[-1]['Close'])
    except:
        pass
    if prices:
        best_exchange = min(prices, key=prices.get)
        return prices[best_exchange], best_exchange
    return None, None

def get_best_sell_price(symbol, preferred_ex=None):
    try:
        suffix = ".NS" if preferred_ex == "NSE" else ".BO" if preferred_ex == "BSE" else ""
        if suffix:
            ticker = yf.Ticker(symbol + suffix).history(period="1d", interval="1m")
            if not ticker.empty:
                return float(ticker.iloc[-1]['Close'])
    except:
        pass
    return None

def compute_20dma(symbol):
    series = df_price[symbol].replace("null", np.nan).dropna().astype(float)
    if len(series) >= 20:
        dma_series = series[-20:]
        return dma_series.mean()
    return None

def update_holdings(stock, qty, price, action, exchange):
    global df_holdings
    existing = df_holdings[df_holdings.Stock == stock]
    if action in ["BUY", "AVERAGE"]:
        if not existing.empty:
            total_qty = int(existing.iloc[0]['Qty']) + qty
            old_price = float(existing.iloc[0]['Avg Buy Price'])
            new_price = ((old_price * int(existing.iloc[0]['Qty'])) + (price * qty)) / total_qty
            df_holdings.loc[df_holdings.Stock == stock, ['Qty', 'Avg Buy Price', 'Exchange']] = [total_qty, round(new_price, 2), exchange]
        else:
            df_holdings.loc[len(df_holdings)] = [stock, qty, price, exchange]
    elif action == "SELL":
        df_holdings = df_holdings[df_holdings.Stock != stock]

def calculate_holdings_value():
    value = 0
    for _, row in df_holdings.iterrows():
        stock = row["Stock"]
        qty = int(row["Qty"])
        ex = row.get("Exchange")
        price = get_best_sell_price(stock, ex)
        if price:
            value += price * qty
    return value

def log_transaction(date, action, stock, price, qty, exchange, pnl, cash, holdings_val, total_value):
    global df_log
    df_log.loc[len(df_log)] = [date, action, stock, price, qty, exchange, pnl, cash, holdings_val, total_value]

# === Main Execution ===
now = datetime.now()
today_str = now.strftime("%Y-%m-%d")
print(f"\n🕒 Running strategy for {today_str} at {now.strftime('%H:%M:%S')}\n")

cash = CAPITAL - df_log["Price"].mul(df_log["Qty"]).sum() + df_log["PnL"].sum()
top_fallers = []

# === FIND FALLERS ===
for stock in nifty_50:
    price, ex = get_best_buy_price(stock)
    dma = compute_20dma(stock)
    if price and dma:
        deviation = (price - dma) / dma
        top_fallers.append((deviation, stock))
    price_str = f"{price:.2f}" if price else "N/A"
    dma_str = f"{dma:.2f}" if dma else "N/A"
    print(f"🔎 {stock}: Price = ₹{price_str} ({ex or 'NSE/BSE not found'}), 20DMA = ₹{dma_str}")

# === BUY ===
top_fallers.sort()
buy_count = 0
for _, stock in top_fallers:
    if buy_count >= 2:
        break
    if stock not in df_holdings.Stock.values:
        price, exchange = get_best_buy_price(stock)
        qty = int(UNIT_ALLOCATION // price)
        cost = qty * price
        if qty > 0 and cost <= cash:
            cash -= cost
            update_holdings(stock, qty, price, "BUY", exchange)
            holdings_val = calculate_holdings_value()
            total_val = cash + holdings_val
            print(f"🟢 BUY: {stock} @ ₹{price:.2f} × {qty} on {exchange}")
            log_transaction(today_str, "BUY", stock, price, qty, exchange, 0, round(cash, 2), round(holdings_val, 2), round(total_val, 2))
            buy_count += 1

# === AVERAGE DOWN ===
if buy_count == 0:
    drop_candidates = []
    for _, row in df_holdings.iterrows():
        stock = row["Stock"]
        avg = float(row["Avg Buy Price"])
        qty = int(row["Qty"])
        price, exchange = get_best_buy_price(stock)
        if price and price < 0.97 * avg:
            drop_candidates.append((avg - price, stock, price, exchange))
    if drop_candidates:
        drop_candidates.sort(reverse=True)
        _, stock, price, exchange = drop_candidates[0]
        qty = int(UNIT_ALLOCATION // price)
        if qty > 0 and (qty * price) <= cash:
            cash -= qty * price
            update_holdings(stock, qty, price, "AVERAGE", exchange)
            holdings_val = calculate_holdings_value()
            total_val = cash + holdings_val
            print(f"🟡 AVERAGE DOWN: {stock} @ ₹{price:.2f} × {qty} on {exchange}")
            log_transaction(today_str, "AVERAGE", stock, price, qty, exchange, 0, round(cash, 2), round(holdings_val, 2), round(total_val, 2))

# === SELL ===
for _, row in df_holdings.copy().iterrows():
    stock = row["Stock"]
    avg = float(row["Avg Buy Price"])
    qty = int(row["Qty"])
    ex = row.get("Exchange")
    price = get_best_sell_price(stock, ex)
    if price and price >= 1.05 * avg:
        proceeds = price * qty
        pnl = (price - avg) * qty
        cash += proceeds
        update_holdings(stock, qty, price, "SELL", ex)
        holdings_val = calculate_holdings_value()
        total_val = cash + holdings_val
        print(f"🔴 SELL: {stock} @ ₹{price:.2f} × {qty} on {ex} | PnL = ₹{pnl:.2f}")
        log_transaction(today_str, "SELL", stock, price, qty, ex, round(pnl, 2), round(cash, 2), round(holdings_val, 2), round(total_val, 2))
        break

# === FINAL SUMMARY ===
holdings_val = calculate_holdings_value()
total_realized_pnl = df_log[df_log['Action'] == 'SELL']['PnL'].sum()
final_value = cash + holdings_val

print(f"\n📊 Final Portfolio Summary ({today_str}):")
print(f"   💰 Cash Left         : ₹{cash:,.2f}")
print(f"   📦 Holdings Value    : ₹{holdings_val:,.2f}")
print(f"   ✅ Realized P&L      : ₹{total_realized_pnl:,.2f}")
print(f"   🧾 Total Portfolio   : ₹{final_value:,.2f}")

# === SAVE ===
save_response = input("\n💾 Save log and holdings? (yes/no): ").strip().lower()
if save_response == "yes":
    df_log.to_csv(LOG_PATH, index=False)
    df_holdings.to_csv(HOLDINGS_PATH, index=False)
    print("✅ Log and Holdings saved.")
else:
    print("❌ Not saved.")