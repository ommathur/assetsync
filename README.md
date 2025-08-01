# AssetSync

**AssetSync** is an automated portfolio strategy and backtesting framework focused on Nifty 50 stocks. It combines:

- Real-time Zerodha Kite API integration
- Historical strategy simulation
- Dynamic averaging and P&L tracking
- NSE/BSE data with tax and charge calculations

---

## 📌 Features

- 🔄 **Real-Time Strategy Execution** using Zerodha Kite API  
- ⏳ **Backtesting Mode** over custom dates and capital levels  
- 📉 Trading Logic:
  - Buy top 2 fallers below 20-DMA
  - Average down if price drops ≥3%
  - Sell if returns exceed 5–6%
- ⚙️ Modular Architecture
- 📊 Realized/unrealized P&L, dynamic logging
- 🧾 Tax & charge breakdown compatible with Indian markets

---

## 🗂️ Project Structure
AssetSync/
├── data_fetch.py                  # Fetch latest Nifty 50 daily closes
├── final_script.py                # 🔴 Real-time Zerodha strategy execution
├── generate_token.py              # Auth flow for ZERODHA_ACCESS_TOKEN
├── mul_stratergy_per_capital.py   # Batch backtest across capital configs
├── stratergy.py                   # Ad-hoc manual backtest
├── tax_on_log.py                  # Transaction fee & tax estimation
├── real_time_zerodha/.env         # Store Kite API credentials (not included, please put yours)


---

## 🛠️ Setup Instructions

### 1. 📦 Install Dependencies

Required packages:

- `pandas`, `numpy`
- `yfinance`, `requests`
- `dotenv`
- `kiteconnect`

---

### 2. 🔐 Prepare `.env` File

Edit or create `real_time_zerodha/.env` with:
ZERODHA_API_KEY=your_api_key 
ZERODHA_API_SECRET=your_api_secret
ZERODHA_ACCESS_TOKEN=your_generated_access_token


---

### 3. 🔑 Generate Zerodha Access Token

python generate_token.py


This opens a login URL and stores `access_token` in `.env`.

---

### 4. 📥 Update Price CSV


Download or append daily close values for Nifty 50 stocks  
Output: `daily_ma_nifty50_10years.csv`

---

## 🚀 Run Live Strategy

python final_script.py


Features:

- Buys up to 2 top fallers < 20-DMA
- Averages down existing holdings on 3% drop
- Sells when stock gains ≥5%
- Logs all trades to `live_portfolio_log.csv`
- Tracks positions in `current_holdings.csv`

At the end of run, the script will prompt you to save logs.

---

## 🔙 Backtesting Mode

### A. Manual Backtest

python stratergy.py


Interactive CLI for:

- Entering capital, start, and end dates
- Generates:
  - `Output files/portfolio_log.csv`
  - `Output files/final_result.csv`

---

### B. Batch Backtesting

from mul_stratergy_per_capital import run_backtest
result = run_backtest( capital=3_000_000, start_date=“2018-01-01”, end_date=“2024-12-31”, output_suffix=“3000000” )


Results saved with prefix `portfolio_log_3000000.csv` and `final_result_3000000.csv`.

---

## 🧾 Estimate Taxes and Charges

python tax_on_log.py


Reads portfolio log and calculates:

| Type           | Rate / Amount    |
|----------------|------------------|
| Stamp Duty     | 0.015% (Buy)     |
| STT            | 0.1% (Sell)      |
| Transaction    | 0.00297%         |
| SEBI Charges   | ₹10 per crore    |
| DP Charges     | ₹15.93/txn (Sell)|
| GST            | 18% on brokerage/tx |

Output: `portfolio_charges.csv`

---

## 💡 Strategy Logic Overview

| Stage     | Criteria                                 |
|-----------|-------------------------------------------|
| **BUY**   | Stock in top 5 fallers below 20-DMA       |
| **AVG**   | If stock price < 97% of avg buy price     |
| **SELL**  | If price ≥ 105%–106% of avg buy (5–6%)    |

⚠️ Live uses 5%, backtest uses 6% to account for slippage.

---

## 📈 Outputs

| File                             | Purpose                          |
|----------------------------------|----------------------------------|
| `daily_ma_nifty50.csv`           | Updated price data               |
| `live_portfolio_log.csv`         | Logs live trades                 |
| `current_holdings.csv`           | Ongoing portfolio positions      |
| `portfolio_log.csv`              | Trade log for backtests          |
| `final_result.csv`               | P&L and summary backtest results |
| `portfolio_charges.csv`          | Tax + fee breakdown              |

---

## 🚧 Known Limitations

- Uses static Nifty 50 list — doesn’t track historical symbol changes.
- Yahoo Finance 1m interval data can have latency (~15s).
- DP charges are flat per sell.
- No stop-loss implemented yet.

---

## 📌 TODOs

- [ ] Add configurable stop-loss
- [ ] Integrate Telegram/email alerts for live runs
- [ ] Benchmark comparison (vs Nifty 50 ETF)
- [ ] Modular config for portfolio size, thresholds

---

## 👨‍💻 Author

Developed by Om Mathur 

---

## ✅ Quick Run Summary

| Mode           | Script                 | Output                        |
|----------------|------------------------|-------------------------------|
| Live Trade     | `final_script.py`      | `live_portfolio_log.csv`     |
| Manual Backtest| `stratergy.py`         | `portfolio_log.csv`          |
| Batch Backtest | `mul_stratergy_per_capital.py` | `portfolio_log_<cap>.csv` |
| Tax Estimation | `tax_on_log.py`        | `portfolio_charges.csv`      |

---

Happy Trading! 📈






