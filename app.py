import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Macro Dashboard", layout="wide")

st.title("📊 Financial Repression Tracker")

# Fetch data
us10y = yf.download("^TNX", period="5d")
gold = yf.download("GC=F", period="5d")
dxy = yf.download("DX-Y.NYB", period="5d")

# Latest values
us10y_val = us10y["Close"].iloc[-1] / 10
gold_val = gold["Close"].iloc[-1]
dxy_val = dxy["Close"].iloc[-1]

# Dummy CPI (manual for now)
cpi = 3.2

real_rate = us10y_val - cpi

# Display
col1, col2, col3 = st.columns(3)

col1.metric("US 10Y Yield", f"{us10y_val:.2f}%")
col2.metric("Inflation (CPI)", f"{cpi}%")
col3.metric("Real Rate", f"{real_rate:.2f}%")

# Signal
st.subheader("Signal")

if real_rate < 0:
    st.error("🔴 Financial Repression ON")
else:
    st.success("🟢 Normal Conditions")

# Charts
st.subheader("Market Trends")
st.line_chart(us10y["Close"])
st.line_chart(dxy["Close"])
st.line_chart(gold["Close"])
