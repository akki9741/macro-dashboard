import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred
import time

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="India Pro Macro Dashboard", layout="wide")

st.title("🇮🇳 Pro Macro + India Market Dashboard")

# =========================
# FRED SETUP (REAL DATA)
# =========================
fred = Fred(api_key="YOUR_API_KEY_HERE")

# Get US 10Y
try:
    us10y = fred.get_series("DGS10").dropna()
    us10y_val = round(us10y.iloc[-1], 2)
except:
    us10y_val = None

# Get CPI
try:
    cpi = fred.get_series("CPIAUCSL")
    cpi_yoy = (cpi.pct_change(12) * 100).dropna()
    cpi_val = round(cpi_yoy.iloc[-1], 2)
except:
    cpi_val = None

# Real Rate
if us10y_val and cpi_val:
    real_rate = round(us10y_val - cpi_val, 2)
else:
    real_rate = None

# =========================
# MARKET DATA (ETF PROXIES)
# =========================
def get_data(symbol):
    for _ in range(3):
        try:
            data = yf.download(symbol, period="1mo", progress=False)
            if data is not None and not data.empty:
                return data
        except:
            pass
        time.sleep(1)
    return None

dxy = get_data("UUP")
nifty = get_data("NIFTYBEES.NS")

def get_trend(data):
    try:
        if len(data) > 5:
            return float(data["Close"].iloc[-1]) - float(data["Close"].iloc[-5])
    except:
        return None

dxy_trend = get_trend(dxy)
nifty_trend = get_trend(nifty)

# =========================
# DISPLAY CORE METRICS
# =========================
st.subheader("🌍 Global Macro")

col1, col2, col3 = st.columns(3)

col1.metric("US 10Y Yield", f"{us10y_val}%" if us10y_val else "N/A")
col2.metric("Inflation (CPI YoY)", f"{cpi_val}%" if cpi_val else "N/A")
col3.metric("Real Rate", f"{real_rate}%" if real_rate else "N/A")

# =========================
# LIQUIDITY SIGNAL
# =========================
st.subheader("💧 Liquidity Signal")

if real_rate is not None:
    if real_rate < 0:
        st.success("🟢 Financial Repression → Liquidity Positive")
    elif real_rate < 1:
        st.warning("⚠️ Neutral Zone")
    else:
        st.error("🔴 Tight Liquidity")
else:
    st.warning("Data unavailable")

# =========================
# FII MODEL
# =========================
st.subheader("💰 FII Flow Model")

if real_rate is not None and dxy_trend is not None:
    if real_rate < 0 and dxy_trend < 0:
        fii = "Strong Inflows"
        st.success("🟢 Strong FII Inflows")
    elif real_rate > 1 and dxy_trend > 0:
        fii = "Outflows"
        st.error("🔴 FII Outflows")
    else:
        fii = "Neutral"
        st.warning("⚖️ Mixed Flow")
else:
    fii = "Neutral"
    st.warning("Data incomplete")

# =========================
# INDIA MARKET VIEW
# =========================
st.subheader("📈 India Market View")

if nifty_trend is not None:
    if nifty_trend > 0:
        st.success("🟢 Bullish Trend")
    else:
        st.error("🔴 Weak Trend")
else:
    st.warning("Trend not available")

# =========================
# SECTOR ROTATION
# =========================
st.subheader("🏦 Sector Strategy")

if fii == "Strong Inflows":
    st.markdown("""
    **🔥 Overweight:**
    - Banks 🏦
    - Capital Goods ⚙️
    - Infra 🏗️
    - Midcaps 🚀
    """)
elif fii == "Outflows":
    st.markdown("""
    **⚠️ Defensive:**
    - IT 💻
    - Pharma 💊
    - FMCG 🛒
    """)
else:
    st.markdown("""
    **⚖️ Neutral:**
    - Stock specific
    """)

# =========================
# FINAL ACTION
# =========================
st.subheader("🎯 Final Call")

if fii == "Strong Inflows":
    st.success("✅ BUY ON DIPS")

elif fii == "Outflows":
    st.error("❌ REDUCE EXPOSURE")

else:
    st.warning("⚠️ WAIT & WATCH")

# =========================
# CHARTS
# =========================
st.subheader("📊 Charts")

if nifty is not None:
    st.line_chart(nifty["Close"])

if dxy is not None:
    st.line_chart(dxy["Close"])
