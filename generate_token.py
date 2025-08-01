import os
from dotenv import load_dotenv
from kiteconnect import KiteConnect
from urllib.parse import urlparse, parse_qs
import webbrowser

# === Load API key and secret from .env ===
load_dotenv()
api_key = os.getenv("ZERODHA_API_KEY")
api_secret = os.getenv("ZERODHA_API_SECRET")

if not api_key or not api_secret:
    print("❌ ZERODHA_API_KEY or ZERODHA_API_SECRET not set in .env.")
    exit()

# === Step 1: Generate Login URL and open in browser ===
kite = KiteConnect(api_key=api_key)
login_url = kite.login_url()
print(f"🔗 Open this URL to login:\n{login_url}")
webbrowser.open(login_url)

# === Step 2: Wait for manual paste ===
redirect_url = input("\n🔗 Paste full redirect URL after login: ").strip()

# === Step 3: Extract request_token ===
parsed_url = urlparse(redirect_url)
query_params = parse_qs(parsed_url.query)
request_token = query_params.get("request_token", [None])[0]

if not request_token:
    print("❌ Could not extract request_token from URL.")
    exit()

print(f"🔑 Extracted request_token: {request_token}")

# === Step 4: Generate access_token ===
try:
    session_data = kite.generate_session(request_token, api_secret=api_secret)
    access_token = session_data["access_token"]
    print(f"\n✅ Access Token: {access_token}")

    # === Step 5: Save access_token to .env ===
    env_path = "real_time_zerodha/.env"
    with open(env_path, "r") as f:
        lines = f.readlines()

    with open(env_path, "w") as f:
        found = False
        for line in lines:
            if line.startswith("ZERODHA_ACCESS_TOKEN="):
                f.write(f"ZERODHA_ACCESS_TOKEN={access_token}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"ZERODHA_ACCESS_TOKEN={access_token}\n")

    print("💾 Access token saved to .env as ZERODHA_ACCESS_TOKEN.")

except Exception as e:
    print(f"❌ Error generating access token: {e}")