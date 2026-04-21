import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Macro Dashboard", layout="wide")

st.title("📊 Financial Repression Tracker")

# -----------------------------
# SAFE DATA FETCH FUNCTION
# -----------------------------
def get_data(symbol):
    try:
        data = yf.download(symbol, period="5d", progress=False)
        if data is None or data.empty:
            return None
        return data
    except:
        return None

# -----------------------------
# FETCH DATA
# -----------------------------
us10y = get_data("^TNX")      # US 10Y yield
gold = get_data("GC=F")      # Gold
dxy = get_data("DX-Y.NYB")   # Dollar index

# -----------------------------
# SAFE VALUE EXTRACTOR
# -----------------------------
def get_latest(data, divide=1):
    try:
        value = data["Close"].iloc[-1]
        return round(float(value) / divide, 2)
    except:
        return None

us10y_val = get_latest(us10y, 10)   # TNX needs /10
gold_val = get_latest(gold)
dxy_val = get_latest(dxy)

# -----------------------------
# CPI (MANUAL FOR NOW)
# -----------------------------
cpi = 3.2

# -----------------------------
# DISPLAY METRICS
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric(
    "🇺🇸 US 10Y Yield",
    f"{us10y_val}%" if us10y_val is not None else "N/A"
)

col2.metric(
    "📉 Inflation (CPI)",
    f"{cpi}%"
)

col3.metric(
    "🧠 Real Rate",
    f"{round(us10y_val - cpi, 2)}%" if us10y_val is not None else "N/A"
)

# -----------------------------
# SIGNAL LOGIC
# -----------------------------
st.subheader("🔎 System Signal")

if us10y_val is not None:
    real_rate = us10y_val - cpi

    if real_rate < 0:
        st.error("🔴 Financial Repression ACTIVE")
    elif real_rate < 1:
        st.warning("🟡 Transition Zone")
    else:
        st.success("🟢 Normal Conditions")
else:
    st.warning("⚠️ Data not available")

# -----------------------------
# INDIA IMPACT
# -----------------------------
st.subheader("🇮🇳 India Market View")

if us10y_val is not None:
    real_rate = us10y_val - cpi

    if real_rate < 0:
        st.markdown("""
        **🔥 Bullish for India**
        - FII inflows likely ↑  
        - Equity markets strong  
        - Gold positive  
        """)
    elif real_rate < 1:
        st.markdown("""
        **⚠️ Mixed Zone**
        - Volatility expected  
        - Sector rotation  
        """)
    else:
        st.markdown("""
        **❌ Risk-Off**
        - FII outflows possible  
        - Pressure on equities  
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
