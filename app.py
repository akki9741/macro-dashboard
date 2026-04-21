import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Macro Dashboard", layout="wide")

st.title("📊 Financial Repression Tracker")

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

# Use TLT (bond ETF) instead of TNX (more stable)
us10y = get_data("TLT")     
gold = get_data("GC=F")     
dxy = get_data("DX-Y.NYB")  

# -----------------------------
# VALUE EXTRACTOR
# -----------------------------
def get_latest(data):
    try:
        return round(float(data["Close"].iloc[-1]), 2)
    except:
        return None

us10y_val = get_latest(us10y)
gold_val = get_latest(gold)
dxy_val = get_latest(dxy)

# CPI (manual for now)
cpi = 3.2

# -----------------------------
# DISPLAY
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("🇺🇸 US Bonds (TLT)", f"{us10y_val}" if us10y_val is not None else "N/A")
col2.metric("📉 Inflation (CPI)", f"{cpi}%")
col3.metric("🧠 Proxy Signal", "Check below")

# -----------------------------
# SIGNAL LOGIC
# -----------------------------
st.subheader("🔎 System Signal")

if us10y is not None:
    trend = us10y["Close"].iloc[-1] - us10y["Close"].iloc[-5]

    if trend > 0:
        st.success("🟢 Falling yields → Liquidity improving → Bullish")
    else:
        st.error("🔴 Rising yields → Tight conditions → Risk")

else:
    st.warning("⚠️ Data not available")

# -----------------------------
# INDIA VIEW
# -----------------------------
st.subheader("🇮🇳 India Market View")

if us10y is not None:
    if trend > 0:
        st.markdown("""
        **🔥 Bullish for India**
        - FII inflows likely  
        - Equities supported  
        """)
    else:
        st.markdown("""
        **❌ Risk-Off**
        - FII outflows possible  
        """)

# -----------------------------
# CHARTS
# -----------------------------
st.subheader("📈 Market Trends")

if us10y is not None:
    st.line_chart(us10y["Close"])

if dxy is not None:
    st.line_chart(dxy["Close"])

if gold is not None:
    st.line_chart(gold["Close"])
