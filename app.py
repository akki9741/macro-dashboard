import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Pro Macro + India Screener", layout="wide")

fred = Fred(api_key=st.secrets["FRED_API_KEY"])

# =========================
# SAFE FETCH FUNCTION
# =========================
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
        st.warning("Macro data unavailable")
        macro_signal = "NEUTRAL"

    else:
        us10y_val = float(us10y["Close"].iloc[-1])
        cpi = cpi.dropna()
        cpi_latest = float(cpi.iloc[-1])
        cpi_prev = float(cpi.iloc[-12])

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
# 🇮🇳 STOCK LIST
# =========================
st.header("📊 India Early Breakout Screener")

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

# =========================
# SCREENER LOGIC
# =========================
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
        # 🚀 EARLY BREAKOUT LOGIC
        # =========================
        recent_high = float(close[-20:].max())
        recent_low = float(close[-20:].min())

        # 1. Compression (SIDEWAYS BASE)
        range_pct = ((recent_high - recent_low) / recent_low) * 100
        is_compressed = range_pct < 8

        # 2. Fresh breakout (JUST STARTING)
        breakout = price > recent_high * 0.995

        # 3. Not extended (VERY IMPORTANT)
        distance = ((price - ma20) / ma20) * 100
        not_extended = distance < 4

        # =========================
        # FINAL SELECTION
        # =========================
        if is_compressed and breakout and not_extended:

            reasons = []

            if is_compressed:
                reasons.append("Tight consolidation")

            if breakout:
                reasons.append("Fresh breakout")

            if not_extended:
                reasons.append("Early stage move")

            selected_data.append({
                "Stock": stock,
                "Momentum %": round(distance, 2),
                "Trend %": round(((ma20 - ma50)/ma50)*100, 2),
                "Reason": ", ".join(reasons)
            })

        else:
            reason = []

            if not is_compressed:
                reason.append("Already moved / volatile")

            if not breakout:
                reason.append("No breakout")

            if not not_extended:
                reason.append("Extended move")

            rejected.append((stock, ", ".join(reason)))

    except:
        rejected.append((stock, "Calculation error"))

# =========================
# OUTPUT
# =========================
st.subheader("🚀 Stocks About to Enter Uptrend")

if selected_data:
    df_sel = pd.DataFrame(selected_data).sort_values(by="Momentum %", ascending=False)
    st.dataframe(df_sel)
else:
    st.warning("No early breakout stocks right now")

# =========================
# REJECTION TABLE
# =========================
st.subheader("🧠 Why Stocks Were Rejected")

df_rej = pd.DataFrame(rejected, columns=["Stock", "Reason"])
st.dataframe(df_rej)

# =========================
# FINAL STRATEGY
# =========================
st.header("🎯 Final Strategy")

if macro_signal == "BULLISH" and selected_data:
    st.success("Buy early breakout stocks")

elif macro_signal == "NEUTRAL":
    st.warning("Selective buying only")

else:
    st.error("Avoid aggressive buying")
