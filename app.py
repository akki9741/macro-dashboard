import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Macro Dashboard", layout="wide")

st.title("📊 Financial Repression Tracker")

# Fetch data safely
def get_data(symbol):
    try:
        data = yf.download(symbol, period="5d", progress=False)
        if data.empty:
            return None
        return data
    except:
        return None

us10y = get_data("^TNX")
gold = get_data("GC=F")
dxy = get_data("DX-Y.NYB")

# CPI (manual for now)
cpi = 3.2

# Safe extraction
def get_latest(data, divide=1):
    try:
        return round(data["Close"].iloc[-1] / divide, 2)
    except:
        return None

us10y_val = get_latest(us10y, 10)
gold_val = get_latest(gold)
dxy_val = get_latest(dxy)

# Display
col1, col2, col3 = st.columns(3)

col1.metric("US 10Y Yield", f"{us10y_val}%" if us10y_val else "N/A")
col2.metric("Inflation (CPI)", f"{cpi}%")
col3.metric("Real Rate", f"{round(us10y_val - cpi,2)}%" if us10y_val else "N/A")

# Signal
st.subheader("Signal")

if us10y_val:
    if us10y_val - cpi < 0:
        st.error("🔴 Financial Repression ON")
    else:
        st.success("🟢 Normal Conditions")
else:
    st.warning("⚠️ Data not available")

# Charts
st.subheader("Market Trends")

if us10y is not None:
    st.line_chart(us10y["Close"])

if dxy is not None:
    st.line_chart(dxy["Close"])

if gold is not None:
    st.line_chart(gold["Close"])
