import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred

# =========================
# SETUP
# =========================
st.set_page_config(page_title="Macro + India Dashboard", layout="wide")

fred = Fred(api_key=st.secrets["FRED_API_KEY"])

def fetch(ticker, period="6mo"):
    try:
        df = yf.download(ticker, period=period, progress=False)
        if df is None or df.empty:
            return None

        # Fix multi-index issue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df
    except:
        return None

# =========================
# 🇺🇸 US MACRO
# =========================
st.header("🇺🇸 US Financial Repression")

try:
    us10y = fetch("^TNX", "5d")
    cpi = fred.get_series("CPIAUCSL")

    if us10y is None or cpi is None or len(cpi) < 12:
        st.warning("US macro data unavailable")
        macro_signal = "NEUTRAL"

    else:
        us10y_val = float(us10y["Close"].dropna().iloc[-1]) / 10

        cpi_latest = float(cpi.dropna().iloc[-1])
        cpi_prev = float(cpi.dropna().iloc[-12])
        cpi_yoy = ((cpi_latest / cpi_prev) - 1) * 100

        real_rate = us10y_val - cpi_yoy

        col1, col2, col3 = st.columns(3)
        col1.metric("US 10Y Yield", f"{round(us10y_val,2)}%")
        col2.metric("CPI YoY", f"{round(cpi_yoy,2)}%")
        col3.metric("Real Rate", f"{round(real_rate,2)}%")

        if real_rate < 0:
            macro_signal = "BULLISH"
            st.success("Liquidity Positive → Bullish")
        elif real_rate > 1.5:
            macro_signal = "BEARISH"
            st.error("Liquidity Tightening")
        else:
            macro_signal = "NEUTRAL"
            st.warning("Neutral → Selective buying")

except Exception as e:
    st.error(f"Macro error: {e}")
    macro_signal = "NEUTRAL"

# =========================
# 🇮🇳 INDIA SCREENER
# =========================
st.header("📊 India Smart Screener")

stocks = [
    "RELIANCE.NS","TCS.NS","INFY.NS","HDFCBANK.NS","ICICIBANK.NS",
    "SBIN.NS","LT.NS","AXISBANK.NS","ITC.NS","HCLTECH.NS",
    "ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS","TATAMOTORS.NS",
    "WIPRO.NS","ULTRACEMCO.NS","NTPC.NS","POWERGRID.NS",
    "BAJFINANCE.NS","HINDUNILVR.NS","KOTAKBANK.NS",
    "ADANIENT.NS","ADANIPORTS.NS","TATASTEEL.NS","ONGC.NS",
    "COALINDIA.NS","IOC.NS","BPCL.NS","GRASIM.NS","JSWSTEEL.NS"
]

selected_data = []
rejected = []

for stock in stocks:
    df = fetch(stock)

    if df is None or len(df) < 60:
        rejected.append((stock, "No data"))
        continue

    try:
        close = df["Close"].dropna()

        price = float(close.iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])
        ma50 = float(close.rolling(50).mean().iloc[-1])

        if pd.isna(price) or pd.isna(ma20) or pd.isna(ma50):
            rejected.append((stock, "NaN values"))
            continue

        # =========================
        # 🚀 UPTREND LOGIC
        # =========================
        if price > ma20 and ma20 > ma50:

            momentum = ((price - ma20) / ma20) * 100
            trend_strength = ((ma20 - ma50) / ma50) * 100

            reasons = []

            if price > ma20:
                reasons.append("Above 20DMA")

            if ma20 > ma50:
                reasons.append("20DMA > 50DMA")

            if momentum > 2:
                reasons.append("Strong momentum")

            if trend_strength > 1:
                reasons.append("Trend strength good")

            selected_data.append({
                "Stock": stock,
                "Momentum %": round(momentum, 2),
                "Trend %": round(trend_strength, 2),
                "Reason": ", ".join(reasons)
            })

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
# 🚀 SELECTED STOCKS
# =========================
st.subheader("🚀 Stocks About to Enter Uptrend")

if selected_data:
    df_selected = pd.DataFrame(selected_data).sort_values(
        by="Momentum %", ascending=False
    )

    st.dataframe(df_selected)

else:
    st.warning("No strong stocks right now")

# =========================
# 🧠 REJECTED STOCKS
# =========================
st.subheader("🧠 Why Stocks Were Rejected")

df_rej = pd.DataFrame(rejected, columns=["Stock", "Reason"])
st.dataframe(df_rej)

# =========================
# 🎯 FINAL STRATEGY
# =========================
st.header("🎯 Final Decision")

if macro_signal == "BULLISH" and selected_data:
    st.success("BUY MODE → Focus on top momentum stocks")

elif macro_signal == "NEUTRAL":
    st.warning("Selective Buying → Only strong setups")

else:
    st.error("Risk-Off → Avoid aggressive buying")
