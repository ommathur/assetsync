import pandas as pd
import numpy as np
from datetime import datetime
import os

# === USER INPUTS ===
capital = float(input("Enter total capital: "))
start_date = input("Enter start date (YYYY-MM-DD): ").strip()
end_date = input("Enter end date (YYYY-MM-DD): ").strip()

unit_allocation = capital / 40
cash = capital
holdings = {}  # { stock: [ (buy_price, qty), ... ] }
actions_log = []
realized_pnl_log = {}  # { stock: pnl }

# === Load daily data ===
df = pd.read_csv("Output files/daily_ma_nifty50.csv", index_col="Stock")
df = df.transpose()
df.index = pd.to_datetime(df.index)

# === Filter date range ===
df = df.loc[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]

# === Helper functions ===
def compute_20dma(price_df, current_date):
    past_20 = price_df.loc[:current_date].tail(20)
    return past_20.mean()

def get_avg_buy_price(stock):
    total_qty = sum(q for _, q in holdings[stock])
    total_cost = sum(p * q for p, q in holdings[stock])
    return total_cost / total_qty if total_qty else 0

def buy(stock, price, date, mode="BUY"):
    global cash
    if cash < unit_allocation:
        return
    qty = unit_allocation // price
    if qty == 0: return
    cost = qty * price
    cash -= cost
    holdings.setdefault(stock, []).append((price, qty))
    actions_log.append([date.strftime("%Y-%m-%d"), mode, stock, price, qty, ""])

def sell(stock, price, date):
    global cash
    total_qty = sum(q for _, q in holdings[stock])
    avg_price = get_avg_buy_price(stock)
    proceeds = price * total_qty
    pnl = proceeds - (avg_price * total_qty)
    cash += proceeds
    realized_pnl_log[stock] = realized_pnl_log.get(stock, 0) + pnl
    del holdings[stock]
    actions_log.append([date.strftime("%Y-%m-%d"), "SELL", stock, price, total_qty, round(pnl, 2)])

# === Strategy Execution ===
for date in df.index:
    prices_today = df.loc[date].replace("null", np.nan).dropna().astype(float)
    dma = compute_20dma(df.replace("null", np.nan).astype(float), date).dropna()
    
    # Entry: Find 5 worst deviations below 20-DMA
    deviations = ((prices_today - dma) / dma).dropna()
    top_fallers = deviations.sort_values().head(5)

    buy_count = 0
    # Try max 2 buys from top fallers (new only)
    for stock in top_fallers.index:
        if stock in holdings:
            continue
        price = prices_today.get(stock)
        if not np.isnan(price):
            buy(stock, price, date)
            buy_count += 1
        if buy_count == 2:
            break

    # Averaging mode
    if buy_count == 0:
        drops = []
        for stock in holdings:
            price = prices_today.get(stock)
            if pd.notna(price):
                avg = get_avg_buy_price(stock)
                if price < 0.97 * avg:
                    drops.append((avg - price, stock, price))
        if drops:
            drops.sort(reverse=True)
            _, stock, price = drops[0]
            buy(stock, price, date, mode="AVERAGE")

    # Exit: Sell one stock that gained 5%
    for stock in list(holdings):
        price = prices_today.get(stock)
        if pd.notna(price):
            avg = get_avg_buy_price(stock)
            if price >= 1.05 * avg:
                sell(stock, price, date)
                break

# === Final Summary ===
total_realized_pnl = sum(realized_pnl_log.values())
unrealized_holdings = {}

# Calculate unrealized value of remaining holdings
for stock in holdings:
    qty = sum(q for _, q in holdings[stock])
    avg_price = get_avg_buy_price(stock)
    last_price = df.iloc[-1][stock]
    if last_price == "null" or pd.isna(last_price): continue
    last_price = float(last_price)
    current_value = qty * last_price
    cost = qty * avg_price
    unrealized_pnl = current_value - cost
    unrealized_holdings[stock] = {
        "Holdings Value": current_value,
        "Qty": qty,
        "Unrealized PnL": unrealized_pnl
    }

# Build final summary DataFrame
summary_rows = []
all_stocks = set(list(realized_pnl_log.keys()) + list(unrealized_holdings.keys()))
for stock in sorted(all_stocks):
    realized = realized_pnl_log.get(stock, 0)
    hold_data = unrealized_holdings.get(stock, {"Holdings Value": 0, "Qty": 0, "Unrealized PnL": 0})
    summary_rows.append({
        "Stock": stock,
        "Realized PnL": round(realized, 2),
        "Holdings Value": round(hold_data["Holdings Value"], 2),
        "Qty": int(hold_data["Qty"]),
        "Unrealized PnL": round(hold_data["Unrealized PnL"], 2)
    })

summary_df = pd.DataFrame(summary_rows)

# Totals and CAGR
total_holdings_value = sum(d["Holdings Value"] for d in unrealized_holdings.values())
total_unrealized_pnl = sum(d["Unrealized PnL"] for d in unrealized_holdings.values())
final_value = cash + total_realized_pnl + total_holdings_value
days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
cagr = ((final_value / capital) ** (365 / days)) - 1 if days > 0 else 0

# Add footer rows
summary_df.loc[len(summary_df.index)] = ["TOTAL", round(total_realized_pnl, 2), round(total_holdings_value, 2), "", round(total_unrealized_pnl, 2)]
summary_df.loc[len(summary_df.index)] = ["CASH LEFT", "", "", "", round(cash, 2)]
summary_df.loc[len(summary_df.index)] = ["PORTFOLIO VALUE", "", "", "", round(final_value, 2)]
summary_df.loc[len(summary_df.index)] = ["CAGR", "", "", "", f"{cagr*100:.2f}%"]

# Save files
os.makedirs("Output files", exist_ok=True)
pd.DataFrame(actions_log, columns=["Date", "Action", "Stock", "Price", "Qty", "PnL"])\
    .to_csv("Output files/portfolio_log.csv", index=False)
summary_df.to_csv("Output files/final_result.csv", index=False)

print("\n✅ Backtest complete.")
print("🔸 Log: Output files/portfolio_log.csv")
print("🔸 Summary: Output files/final_result.csv")