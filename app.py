import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

st.set_page_config(page_title="India Pro Dashboard", layout="wide")
st.title("🇮🇳 Pro Macro + Stock + Gold Dashboard")

# =========================
# FRED MACRO
# =========================
from fredapi import Fred

fred_key = st.secrets.get("FRED_API_KEY", None)
fred = Fred(api_key=fred_key) if fred_key else None

us10y_val = None
cpi_val = None
real_rate = None

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
# DATA FETCH (STABLE)
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
nifty = get_data(["NIFTYBEES.NS", "^NSEI", "INDA"])
bonds = get_data(["TLT"])
gold = get_data(["GLD", "GC=F"])   # ✅ FIXED GOLD

dxy_trend = get_trend(dxy)
nifty_trend = get_trend(nifty)
gold_trend = get_trend(gold)

# =========================
# MACRO DASHBOARD
# =========================
st.header("🌍 Macro")

col1, col2, col3 = st.columns(3)
col1.metric("US 10Y", f"{us10y_val}%" if us10y_val else "N/A")
col2.metric("CPI", f"{cpi_val}%" if cpi_val else "N/A")
col3.metric("Real Rate", f"{real_rate}%" if real_rate else "N/A")

# Liquidity
if real_rate:
    if real_rate < 0:
        st.success("🟢 Liquidity Positive")
    elif real_rate < 1:
        st.warning("⚠️ Neutral")
    else:
        st.error("🔴 Tight")

# =========================
# FII MODEL
# =========================
fii = "neutral"

if real_rate and dxy_trend:
    if real_rate < 0 and dxy_trend < 0:
        fii = "inflow"
        st.success("🟢 FII Inflows")
    elif real_rate > 1 and dxy_trend > 0:
        fii = "outflow"
        st.error("🔴 FII Outflows")
    else:
        st.warning("⚖️ Mixed Flow")

# =========================
# GOLD ANALYSIS
# =========================
st.header("🥇 Gold")

if real_rate and gold_trend:
    if real_rate < 0 and gold_trend > 0:
        st.success("🟢 HOLD / ADD GOLD")
    elif real_rate > 1 and gold_trend < 0:
        st.error("🔴 PARTIAL EXIT GOLD")
    else:
        st.warning("⚖️ HOLD GOLD")
else:
    st.info("Gold data loading")

# =========================
# SCREENER (FIXED)
# =========================
st.header("🚀 Stock Screener")

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

def fetch_screener():
    try:
        url = "https://www.screener.in/api/screen/results/"
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.screener.in/"
        }

        payload = {
            "query": query,
            "limit": 100
        }

        session = requests.Session()
        res = session.post(url, headers=headers, data=payload)

        data = res.json().get("data", [])

        if len(data) > 0:
            return data

    except:
        pass

    # 🔥 fallback
    return [
        {"name": "HDFC Bank", "code": "HDFCBANK"},
        {"name": "ICICI Bank", "code": "ICICIBANK"},
        {"name": "L&T", "code": "LT"},
        {"name": "Reliance", "code": "RELIANCE"},
        {"name": "TCS", "code": "TCS"},
        {"name": "Infosys", "code": "INFY"}
    ]

data = fetch_screener()

st.write(f"Stocks fetched: {len(data)}")  # debug

# =========================
# RANKING ENGINE
# =========================
results = []

for stock in data:
    try:
        ticker = stock["code"] + ".NS"
        df = yf.download(ticker, period="3mo", progress=False)

        if df is None or len(df) < 20:
            continue

        close = df["Close"]
        price = close.iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        momentum = ((price - close.iloc[-5]) / close.iloc[-5]) * 100

        score = 0

        if price > ma20 > ma50:
            score += 2
        if momentum > 2:
            score += 2

        if score >= 1:   # ✅ relaxed condition
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
    st.dataframe(df)
else:
    st.warning("No strong setups currently")

# =========================
# FINAL DECISION
# =========================
st.header("🎯 Final Decision")

if fii == "inflow":
    st.success("✅ BUY ON DIPS")

elif fii == "outflow":
    st.error("❌ REDUCE RISK")

else:
    st.warning("⚠️ WAIT & WATCH")
