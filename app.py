import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from fredapi import Fred

st.set_page_config(layout="wide")

fred = Fred(api_key=st.secrets["FRED_API_KEY"])

# =========================
# SAFE NSE FETCH (FIXED)
# =========================
def get_nse_stocks():

    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/csv"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return []

        df = pd.read_csv(pd.compat.StringIO(response.text))

        return [s + ".NS" for s in df["SYMBOL"].tolist()]

    except:
        return []

# =========================
# FETCH PRICE DATA
# =========================
def fetch(ticker):
    try:
        df = yf.download(ticker, period="6mo", progress=False)

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    except:
        return None

# =========================
# US MACRO
# =========================
st.header("🇺🇸 US Macro")

try:
    us10y = fetch("^TNX")
    cpi = fred.get_series("CPIAUCSL").dropna()

    us10y_val = float(us10y["Close"].iloc[-1]) / 10
    cpi_yoy = ((float(cpi.iloc[-1]) / float(cpi.iloc[-12])) - 1) * 100
    real_rate = us10y_val - cpi_yoy

    st.write(f"US 10Y: {round(us10y_val,2)}%")
    st.write(f"CPI: {round(cpi_yoy,2)}%")
    st.write(f"Real Rate: {round(real_rate,2)}%")

except:
    st.warning("Macro unavailable")

# =========================
# LOAD STOCKS
# =========================
st.header("📊 Dynamic Screener")

stocks = get_nse_stocks()

if not stocks:
    st.error("NSE blocked → Use local CSV fallback")
    st.stop()

# limit for speed
stocks = stocks[:300]

selected = []
rejected = []

# =========================
# SCREENER LOGIC
# =========================
for stock in stocks:

    df = fetch(stock)

    if df is None or len(df) < 60:
        continue

    try:
        close = df["Close"].dropna()

        price = float(close.iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])
        ma50 = float(close.rolling(50).mean().iloc[-1])

        recent_high = float(close[-20:].max())
        recent_low = float(close[-20:].min())

        # compression
        range_pct = ((recent_high - recent_low) / recent_low) * 100
        is_compressed = range_pct < 8

        # breakout
        breakout = price > recent_high * 0.995

        # not extended
        distance = ((price - ma20) / ma20) * 100
        not_extended = distance < 4

        if is_compressed and breakout and not_extended:

            selected.append({
                "Stock": stock,
                "Momentum %": round(distance,2),
                "Reason": "Compression + Fresh Breakout"
            })

        else:
            rejected.append((stock, "No early setup"))

    except:
        rejected.append((stock, "Error"))

# =========================
# OUTPUT
# =========================
st.subheader("🚀 Early Breakout Stocks")

if selected:
    st.dataframe(pd.DataFrame(selected).head(5))
else:
    st.warning("No setups right now")

st.subheader("🧠 Rejected")

st.dataframe(pd.DataFrame(rejected[:50], columns=["Stock","Reason"]))
