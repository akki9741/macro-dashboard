import streamlit as st
import yfinance as yf
import pandas as pd
import time

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="India Pro Macro Dashboard", layout="wide")

st.title("🇮🇳 Pro Macro + India Market Dashboard")

# =========================
# FRED SETUP (SAFE)
# =========================
from fredapi import Fred
fred_key = st.secrets.get("FRED_API_KEY", None)

fred = None
if fred_key:
    try:
        fred = Fred(api_key=fred_key)
    except:
        fred = None

# =========================
# FETCH FRED DATA
# =========================
us10y_val = None
cpi_val = None
real_rate = None

if fred:
    try:
        us10y_series = fred.get_series("DGS10").dropna()
        if len(us10y_series) > 0:
            us10y_val = round(float(us10y_series.iloc[-1]), 2)
    except:
        pass

    try:
        cpi_series = fred.get_series("CPIAUCSL")
        cpi_yoy = (cpi_series.pct_change(12) * 100).dropna()
        if len(cpi_yoy) > 0:
            cpi_val = round(float(cpi_yoy.iloc[-1]), 2)
    except:
        pass

if us10y_val is not None and cpi_val is not None:
    real_rate = round(us10y_val - cpi_val, 2)

# =========================
# MARKET DATA (RETRY SAFE)
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

# ETFs (stable)
dxy = get_data("UUP")
nifty = get_data("NIFTYBEES.NS")
bonds = get_data("TLT")

def get_trend(data):
    try:
        if data is not None and len(data) > 5:
            return float(data["Close"].iloc[-1]) - float(data["Close"].iloc[-5])
    except:
        return None

dxy_trend = get_trend(dxy)
nifty_trend = get_trend(nifty)
bond_trend = get_trend(bonds)

# =========================
# DISPLAY MACRO
# =========================
st.subheader("🌍 Global Macro")

col1, col2, col3 = st.columns(3)

col1.metric("US 10Y Yield", f"{us10y_val}%" if us10y_val is not None else "N/A")
col2.metric("Inflation (CPI YoY)", f"{cpi_val}%" if cpi_val is not None else "N/A")
col3.metric("Real Rate", f"{real_rate}%" if real_rate is not None else "N/A")

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
    st.warning("⚠️ Macro data not available")

# =========================
# FII MODEL
# =========================
st.subheader("💰 FII Flow Model")

fii = "neutral"

if real_rate is not None and dxy_trend is not None:
    if real_rate < 0 and dxy_trend < 0:
        st.success("🟢 Strong FII Inflows")
        fii = "inflow"
    elif real_rate > 1 and dxy_trend > 0:
        st.error("🔴 FII Outflows")
        fii = "outflow"
    else:
        st.warning("⚖️ Mixed Flow")
else:
    st.warning("⚠️ Data incomplete")

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
    st.warning("⚠️ Nifty data unavailable")

# =========================
# SECTOR STRATEGY
# =========================
st.subheader("🏦 Sector Strategy")

if fii == "inflow":
    st.markdown("""
    **🔥 Overweight:**
    - Banks 🏦  
    - Capital Goods ⚙️  
    - Infra 🏗️  
    - Midcaps 🚀  
    """)

elif fii == "outflow":
    st.markdown("""
    **⚠️ Defensive:**
    - IT 💻  
    - Pharma 💊  
    - FMCG 🛒  
    """)

else:
    st.markdown("""
    **⚖️ Neutral:**
    - Stock specific approach  
    """)

# =========================
# FINAL ACTION
# =========================
st.subheader("🎯 Final Call")

if fii == "inflow":
    st.success("✅ BUY ON DIPS")

elif fii == "outflow":
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

if bonds is not None:
    st.line_chart(bonds["Close"])
