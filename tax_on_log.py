import pandas as pd

# Constants
STAMP_DUTY_BUY = 0.00015         # 0.015%
STT_SELL = 0.001                 # 0.1%
TXN_CHARGES = 0.0000297          # 0.00297% (NSE assumed)
SEBI_CHARGES = 10 / 1e7          # 10 per crore = 0.0001%
GST_RATE = 0.18
DP_CHARGES = 15.93               # Flat on SELL side per txn

# Load the portfolio log
df = pd.read_csv("Output files/portfolio_log_3000000.csv")

# Convert price and qty columns to float if not already
df["Price"] = df["Price"].astype(float)
df["Qty"] = df["Qty"].astype(int)

# Calculate turnover
df["Turnover"] = df["Price"] * df["Qty"]

# Initialize charge columns
df["Brokerage"] = 0.0
df["STT"] = 0.0
df["Txn Charges"] = 0.0
df["SEBI Charges"] = 0.0
df["GST"] = 0.0
df["Stamp Duty"] = 0.0
df["DP Charges"] = 0.0
df["Total Charges"] = 0.0

# Row-wise calculation
for idx, row in df.iterrows():
    turnover = row["Turnover"]
    action = row["Action"].strip().upper()

    txn_charge = turnover * TXN_CHARGES
    sebi = turnover * SEBI_CHARGES
    gst = (txn_charge + sebi) * GST_RATE
    stt = 0
    stamp = 0
    dp = 0

    if action == "BUY":
        stamp = turnover * STAMP_DUTY_BUY
    elif action == "SELL":
        stt = turnover * STT_SELL
        dp = DP_CHARGES  # flat per sell txn

    total = txn_charge + sebi + gst + stt + stamp + dp

    # Assign
    df.at[idx, "Txn Charges"] = round(txn_charge, 2)
    df.at[idx, "SEBI Charges"] = round(sebi, 2)
    df.at[idx, "GST"] = round(gst, 2)
    df.at[idx, "STT"] = round(stt, 2)
    df.at[idx, "Stamp Duty"] = round(stamp, 2)
    df.at[idx, "DP Charges"] = round(dp, 2)
    df.at[idx, "Total Charges"] = round(total, 2)

# Save to new CSV
df.to_csv("portfolio_charges.csv", index=False)

# Print total charges
print("\n✅ Charges per transaction saved to: portfolio_charges.csv")
print("💰 Total Charges Summary:")
print(df[["Brokerage", "STT", "Txn Charges", "SEBI Charges", "GST", "Stamp Duty", "DP Charges", "Total Charges"]].sum().round(2))