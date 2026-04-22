import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

st.set_page_config(page_title="Pro Macro + Screener", layout="wide")
st.title("🇮🇳 Macro + Early Uptrend Screener")

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
# DATA HELPERS
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

# =========================
# MARKET PROXIES
# =========================
dxy = get_data(["UUP"])
gold = get_data(["GLD", "GC=F"])

dxy_trend = get_trend(dxy)
gold_trend = get_trend(gold)

# =========================
# MACRO DISPLAY
# =========================
st.header("🌍 Macro")

col1, col2, col3 = st.columns(3)
col1.metric("US 10Y", f"{us10y_val}%" if us10y_val else "N/A")
col2.metric("CPI YoY", f"{cpi_val}%" if cpi_val else "N/A")
col3.metric("Real Rate", f"{real_rate}%" if real_rate else "N/A")

# Market signal
st.subheader("💧 Market Signal")
if real_rate:
    if real_rate < 0:
        st.success("🟢 Liquidity supportive → Risk ON")
    elif real_rate < 1:
        st.warning("⚠️ Neutral → Selective buying")
    else:
        st.error("🔴 Tight liquidity → Risk OFF")

# =========================
# GOLD VIEW
# =========================
st.subheader("🥇 Gold View")

if real_rate and gold_trend:
    if real_rate < 0:
        st.success("🟢 HOLD / ADD GOLD")
    elif real_rate > 1:
        st.warning("⚠️ HOLD (avoid adding)")
    else:
        st.info("⚖️ Neutral gold")
else:
    st.info("Gold data loading")

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
# FETCH SCREENER DATA
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
# RAW STOCK LIST
# =========================
st.header("📋 Screener Stocks")

names = [stock["name"] for stock in data]
st.write(f"Total Stocks: {len(names)}")
st.dataframe(pd.DataFrame(names, columns=["Stock Names"]))

# =========================
# DIAGNOSTICS
# =========================
st.header("🧠 Why Stocks Are Not Selected")

diagnostics = []

for stock in data:
    try:
        ticker = stock["code"] + ".NS"
        df = yf.download(ticker, period="3mo", progress=False)

        if df is None or len(df) < 50:
            diagnostics.append({
                "Stock": stock["name"],
                "Status": "Skipped",
                "Reason": "Insufficient data"
            })
            continue

        close = df["Close"]
        price = close.iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        momentum = ((price - close.iloc[-5]) / close.iloc[-5]) * 100
        recent_high = close[-20:].max()

        cond1 = price > ma20
        cond2 = ma20 > ma50
        cond3 = momentum > 1
        cond4 = price >= 0.98 * recent_high

        reasons = []
        if not cond1:
            reasons.append("Below 20DMA")
        if not cond2:
            reasons.append("Weak Trend")
        if not cond3:
            reasons.append("Low Momentum")
        if not cond4:
            reasons.append("Not near breakout")

        status = "Selected" if cond1 and cond2 and cond3 and cond4 else "Rejected"

        diagnostics.append({
            "Stock": stock["name"],
            "Momentum %": round(momentum, 2),
            "Status": status,
            "Reason": ", ".join(reasons)
        })

    except:
        diagnostics.append({
            "Stock": stock["name"],
            "Status": "Error",
            "Reason": "Data issue"
        })

st.dataframe(pd.DataFrame(diagnostics))

# =========================
# EARLY UPTREND (MAIN LOGIC)
# =========================
st.header("🎯 Stocks About to Enter Uptrend")

early_list = []

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

        cond1 = price > (0.97 * ma20) and price < (1.05 * ma20)
        cond2 = ma20 >= (0.98 * ma50)
        cond3 = momentum > 0 and momentum < 3
        cond4 = price >= (0.90 * recent_high) and price < recent_high

        score = sum([cond1, cond2, cond3, cond4])

        if score >= 3:
            early_list.append({
                "Stock": stock["name"],
                "Price": round(price, 2),
                "Momentum %": round(momentum, 2),
                "Entry Zone": round(ma20, 2),
                "Breakout Level": round(recent_high, 2),
                "Score": score
            })

    except:
        pass

early_df = pd.DataFrame(early_list)

if not early_df.empty:
    early_df = early_df.sort_values(by="Score", ascending=False)

    st.success(f"🔥 {len(early_df)} stocks preparing for breakout")
    st.dataframe(early_df)

    st.markdown("""
    **Action Plan:**
    - Buy near Entry Zone (20DMA)
    - Add on breakout above Breakout Level
    """)

else:
    st.warning("⚠️ No stocks ready yet")

# =========================
# FINAL ACTION
# =========================
st.header("🎯 Final Strategy")

if real_rate and real_rate < 0:
    st.success("Aggressive buying allowed")

elif real_rate and real_rate > 1:
    st.error("Reduce risk")

else:
    st.warning("Selective buying only")
