import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

st.set_page_config(page_title="Pro Investing Dashboard", layout="wide")

st.title("🇮🇳 Pro Macro + Screener Dashboard")

# =========================
# FRED MACRO
# =========================
from fredapi import Fred

fred_key = st.secrets.get("FRED_API_KEY", None)
fred = Fred(api_key=fred_key) if fred_key else None

us10y_val, cpi_val, real_rate = None, None, None

if fred:
    try:
        us10y = fred.get_series("DGS10").dropna()
        us10y_val = round(float(us10y.iloc[-1]), 2)
    except:
        pass

    try:
        cpi = fred.get_series("CPIAUCSL")
        cpi_yoy = (cpi.pct_change(12) * 100).dropna()
        cpi_val = round(float(cpi_yoy.iloc[-1]), 2)
    except:
        pass

if us10y_val and cpi_val:
    real_rate = round(us10y_val - cpi_val, 2)

# =========================
# DATA FETCH
# =========================
def get_data(symbols):
    for symbol in symbols:
        for _ in range(3):
            try:
                data = yf.download(symbol, period="3mo", progress=False)
                if data is not None and not data.empty:
                    return data
            except:
                pass
            time.sleep(1)
    return None

def get_trend(data):
    try:
        if data is not None and len(data) > 5:
            return float(data["Close"].iloc[-1]) - float(data["Close"].iloc[-5])
    except:
        return 0
    return 0

# Market proxies
dxy = get_data(["UUP"])
gold = get_data(["GLD", "GC=F"])

dxy_trend = get_trend(dxy)
gold_trend = get_trend(gold)

# =========================
# MACRO
# =========================
st.header("🌍 Macro")

col1, col2, col3 = st.columns(3)
col1.metric("US 10Y", f"{us10y_val}%" if us10y_val else "N/A")
col2.metric("CPI", f"{cpi_val}%" if cpi_val else "N/A")
col3.metric("Real Rate", f"{real_rate}%" if real_rate else "N/A")

# =========================
# MARKET SIGNAL
# =========================
st.subheader("💧 Market Signal")

if real_rate:
    if real_rate < 0:
        st.success("🟢 Bullish Liquidity")
    elif real_rate < 1:
        st.warning("⚠️ Neutral Market")
    else:
        st.error("🔴 Tight Liquidity")

# =========================
# GOLD
# =========================
st.subheader("🥇 Gold View")

if real_rate and gold_trend:
    if real_rate < 0:
        st.success("🟢 HOLD / ADD GOLD")
    elif real_rate > 1:
        st.warning("⚠️ HOLD (avoid adding)")
    else:
        st.info("⚖️ Neutral Gold")

# =========================
# SCREENER QUERY
# =========================
query = """
Market Capitalization > 15000 AND
Return on capital employed > 18 AND
Return on equity > 15 AND
Debt to equity < 0.5 AND
Sales growth 5Years > 10 AND
Profit growth 5Years > 12 AND
Interest Coverage > 4 AND
Promoter holding > 50
"""

# =========================
# FETCH SCREENER
# =========================
def fetch_screener():
    try:
        url = "https://www.screener.in/api/screen/results/"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.screener.in/"
        }

        payload = {"query": query, "limit": 200}

        session = requests.Session()
        res = session.post(url, headers=headers, data=payload)

        return res.json().get("data", [])

    except:
        return []

data = fetch_screener()

# =========================
# SHOW RAW STOCKS
# =========================
st.header("📋 Screener Stocks")

names = [stock["name"] for stock in data]
st.write(f"Total Stocks: {len(names)}")
st.dataframe(pd.DataFrame(names, columns=["Stock Names"]))

# =========================
# UPTREND ENGINE
# =========================
st.header("🚀 Stocks Entering Uptrend")

results = []

for stock in data:
    try:
        ticker = stock["code"] + ".NS"
        df = yf.download(ticker, period="3mo", progress=False)

        if df is None or len(df) < 50:
            continue

        close = df["Close"]
        price = close.iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        momentum = ((price - close.iloc[-5]) / close.iloc[-5]) * 100
        recent_high = close[-20:].max()

        score = 0

        if price > ma20:
            score += 1
        if ma20 > ma50:
            score += 1
        if momentum > 1:
            score += 1
        if price >= 0.98 * recent_high:
            score += 1

        if score >= 3:
            results.append({
                "Stock": stock["name"],
                "Price": round(price, 2),
                "Momentum %": round(momentum, 2),
                "Score": score,
                "Entry Zone": round(ma20, 2)
            })

    except:
        pass

df = pd.DataFrame(results)

if not df.empty:
    df = df.sort_values(by="Score", ascending=False)

    st.success(f"🔥 {len(df)} stocks ready")

    st.subheader("🏆 Top Picks")
    st.dataframe(df.head(10))

    st.subheader("📊 Full List")
    st.dataframe(df)

else:
    st.warning("No strong setups right now")

# =========================
# FINAL DECISION
# =========================
st.header("🎯 Action")

if real_rate and real_rate < 0:
    st.success("Aggressive buying allowed")

elif real_rate and real_rate > 1:
    st.error("Reduce risk")

else:
    st.warning("Selective buying only")
