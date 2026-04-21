import streamlit as st
import yfinance as yf

st.set_page_config(page_title="India Macro Dashboard", layout="wide")

st.title("🇮🇳 India Macro + Market Dashboard")

# -----------------------------
# SAFE DATA FETCH
# -----------------------------
def get_data(symbol):
    try:
        data = yf.download(symbol, period="1mo", progress=False)
        if data is None or data.empty:
            return None
        return data
    except:
        return None

# Global signals
us_bonds = get_data("TLT")
dxy = get_data("DX-Y.NYB")
gold = get_data("GC=F")

# India index
nifty = get_data("^NSEI")

# -----------------------------
# VALUE EXTRACTOR
# -----------------------------
def get_latest(data):
    try:
        return float(data["Close"].iloc[-1])
    except:
        return None

def get_trend(data):
    try:
        if len(data) > 5:
            return float(data["Close"].iloc[-1]) - float(data["Close"].iloc[-5])
    except:
        return None

# Extract values
bond_trend = get_trend(us_bonds)
dxy_trend = get_trend(dxy)
nifty_val = get_latest(nifty)

# -----------------------------
# GLOBAL SIGNAL
# -----------------------------
st.subheader("🌍 Global Liquidity Signal")

if bond_trend is not None:
    if bond_trend > 0:
        st.success("🟢 Liquidity improving (Bullish)")
    else:
        st.error("🔴 Liquidity tightening (Risk)")
else:
    st.warning("Data not available")

# -----------------------------
# FII FLOW LOGIC
# -----------------------------
st.subheader("💰 FII Flow Indicator")

if bond_trend is not None and dxy_trend is not None:
    if bond_trend > 0 and dxy_trend < 0:
        fii = "Strong Inflows"
        st.success("🟢 FII Inflows Likely")
    elif bond_trend < 0 and dxy_trend > 0:
        fii = "Outflows"
        st.error("🔴 FII Outflows Likely")
    else:
        fii = "Neutral"
        st.warning("⚠️ Mixed Signals")
else:
    fii = "Unknown"
    st.warning("Data insufficient")

# -----------------------------
# NIFTY SIGNAL
# -----------------------------
st.subheader("📈 Nifty View")

if nifty is not None:
    trend = get_trend(nifty)

    if trend is not None:
        if trend > 0:
            st.success(f"🟢 Bullish | Nifty: {round(nifty_val,0)}")
        else:
            st.error(f"🔴 Weak | Nifty: {round(nifty_val,0)}")
    else:
        st.warning("Trend not available")

# -----------------------------
# SECTOR STRATEGY
# -----------------------------
st.subheader("🏦 Sector Strategy")

if fii == "Strong Inflows":
    st.markdown("""
    **🔥 Focus:**
    - Banks 🏦
    - Infra 🏗️
    - Capital Goods ⚙️
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
    **⚖️ Mixed:**
    - Stock specific approach
    """)

# -----------------------------
# FINAL ACTION
# -----------------------------
st.subheader("🎯 What You Should Do")

if fii == "Strong Inflows":
    st.success("✅ BUY ON DIPS | Bullish environment")

elif fii == "Outflows":
    st.error("❌ REDUCE RISK | Avoid aggressive buying")

else:
    st.warning("⚠️ WAIT & WATCH")

# -----------------------------
# CHARTS
# -----------------------------
st.subheader("📊 Market Charts")

if nifty is not None:
    st.line_chart(nifty["Close"])

if us_bonds is not None:
    st.line_chart(us_bonds["Close"])

if dxy is not None:
    st.line_chart(dxy["Close"])
