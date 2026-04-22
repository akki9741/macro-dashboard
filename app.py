import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from fredapi import Fred

# =========================
# SETUP
# =========================
st.set_page_config(page_title="Macro + India Dashboard", layout="wide")

fred = Fred(api_key=st.secrets["FRED_API_KEY"])

def fetch(ticker, period="6mo"):
    try:
        data = yf.download(ticker, period=period, progress=False)
        return data if not data.empty else None
    except:
        return None

# =========================
# 🇺🇸 US FINANCIAL REPRESSION
# =========================
st.header("🇺🇸 US Financial Repression")

try:
    us10y = fetch("^TNX", "5d")
    cpi = fred.get_series("CPIAUCSL")

    if us10y is None or cpi is None or len(cpi) < 12:
        st.warning("US macro data unavailable")

    else:
        us10y_val = float(us10y["Close"].dropna().iloc[-1]) / 10
        cpi_yoy = ((cpi.iloc[-1] / cpi.iloc[-12]) - 1) * 100
        real_rate = us10y_val - cpi_yoy

        col1, col2, col3 = st.columns(3)
        col1.metric("US 10Y", f"{round(us10y_val,2)}%")
        col2.metric("CPI YoY", f"{round(cpi_yoy,2)}%")
        col3.metric("Real Rate", f"{round(real_rate,2)}%")

        if real_rate < 0:
            st.success("Liquidity Positive (Bullish)")
        elif real_rate > 1.5:
            st.error("Liquidity Tightening")
        else:
            st.warning("Neutral Zone")

except Exception as e:
    st.error(f"US macro error: {e}")

# =========================
# 🪙 GOLD
# =========================
st.header("🪙 Gold View")

gold = fetch("GC=F", "3mo")

if gold is None or gold.empty:
    st.warning("Gold data unavailable")
else:
    close = gold["Close"].dropna()

    if len(close) < 25:
        st.warning("Gold data insufficient")
    else:
        price = float(close.iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])

        if pd.isna(price) or pd.isna(ma20):
            st.warning("Gold data incomplete")
        else:
            if price > ma20:
                st.success(f"Bullish ({round(price,2)})")
            else:
                st.warning(f"Cooling ({round(price,2)})")

        st.line_chart(close)

# =========================
# 📊 NSE STOCK UNIVERSE
# =========================
st.header("📊 Stock Screener (Dynamic)")

# Large universe (you can expand)
stocks = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "SBIN.NS","LT.NS","AXISBANK.NS","ITC.NS","HCLTECH.NS",
    "ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS","TATAMOTORS.NS",
    "WIPRO.NS","ULTRACEMCO.NS","NTPC.NS","POWERGRID.NS",
    "BAJFINANCE.NS","HINDUNILVR.NS","KOTAKBANK.NS",
    "ADANIENT.NS","ADANIPORTS.NS","TATASTEEL.NS","ONGC.NS",
    "COALINDIA.NS","IOC.NS","BPCL.NS","GRASIM.NS","JSWSTEEL.NS"
]

selected = []
rejected = []

for stock in stocks:
    data = fetch(stock)

    if data is None or len(data) < 60:
        rejected.append((stock, "Insufficient data"))
        continue

    close = data["Close"].dropna()

    try:
        price = float(close.iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])
        ma50 = float(close.rolling(50).mean().iloc[-1])

        # Uptrend logic
        if price > ma20 and ma20 > ma50:
            selected.append(stock)
        else:
            reason = []
            if price <= ma20:
                reason.append("Below 20DMA")
            if ma20 <= ma50:
                reason.append("Weak trend")
            rejected.append((stock, ", ".join(reason)))

    except:
        rejected.append((stock, "Calculation error"))

# =========================
# 🎯 RESULTS
# =========================
st.subheader("🚀 Stocks About to Enter Uptrend")

if selected:
    for s in selected[:5]:
        st.success(s)
else:
    st.warning("No strong setups right now")

# =========================
# 🧠 WHY NOT SELECTED
# =========================
st.subheader("🧠 Why Stocks Were Rejected")

df = pd.DataFrame(rejected, columns=["Stock", "Reason"])
st.dataframe(df)

# =========================
# 🎯 FINAL STRATEGY
# =========================
st.header("🎯 Final Strategy")

if selected:
    st.success("Selective buying → Focus on shortlisted stocks")
else:
    st.warning("WAIT & WATCH → No high probability trades")
