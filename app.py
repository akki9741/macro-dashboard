import streamlit as st
import yfinance as yf
import pandas as pd
import time
from fredapi import Fred

st.set_page_config(page_title="Pro Market Dashboard", layout="wide")
st.title("🇮🇳 Pro Macro + Stock Screener (Stable Version)")

# =========================
# FRED MACRO
# =========================
fred_key = st.secrets.get("FRED_API_KEY", None)
fred = Fred(api_key=fred_key) if fred_key else None

us10y_val, cpi_val, real_rate = None, None, None

if fred:
    try:
        us10y = fred.get_series("DGS10").dropna()
        us10y_val = round(float(us10y.iloc[-1]), 2)
    except:
        pass

    try:
        cpi = fred.get_series("CPIAUCSL")
        cpi_yoy = (cpi.pct_change(12) * 100).dropna()
        cpi_val = round(float(cpi_yoy.iloc[-1]), 2)
    except:
        pass

if us10y_val and cpi_val:
    real_rate = round(us10y_val - cpi_val, 2)

# =========================
# GOLD FIX (RELIABLE)
# =========================
def get_gold():
    for symbol in ["GC=F", "GLD"]:
        try:
            df = yf.download(symbol, period="3mo", progress=False)
            if df is not None and not df.empty:
                return df
        except:
            pass
        time.sleep(1)
    return None

gold = get_gold()

def get_trend(df):
    try:
        return df["Close"].iloc[-1] - df["Close"].iloc[-5]
    except:
        return 0

gold_trend = get_trend(gold)

# =========================
# MACRO DISPLAY
# =========================
st.header("🌍 Macro")

col1, col2, col3 = st.columns(3)
col1.metric("US 10Y", f"{us10y_val}%" if us10y_val else "N/A")
col2.metric("CPI YoY", f"{cpi_val}%" if cpi_val else "N/A")
col3.metric("Real Rate", f"{real_rate}%" if real_rate else "N/A")

# =========================
# MARKET SIGNAL
# =========================
st.subheader("💧 Market Signal")

if real_rate:
    if real_rate < 0:
        st.success("🟢 Bullish Liquidity")
    elif real_rate < 1:
        st.warning("⚠️ Neutral → Selective buying")
    else:
        st.error("🔴 Tight liquidity")

# =========================
# GOLD VIEW
# =========================
st.subheader("🥇 Gold View")

if gold is not None:
    if real_rate and real_rate < 0:
        st.success("🟢 HOLD / ADD GOLD")
    elif real_rate and real_rate > 1:
        st.warning("⚠️ HOLD (avoid adding)")
    else:
        st.info("⚖️ Neutral Gold")
else:
    st.error("Gold data failed")

# =========================
# STOCK UNIVERSE (NIFTY STYLE)
# =========================
def get_stock_list():
    return [
        "RELIANCE.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS","TCS.NS",
        "LT.NS","SBIN.NS","AXISBANK.NS","KOTAKBANK.NS","BAJFINANCE.NS",
        "ITC.NS","HINDUNILVR.NS","ASIANPAINT.NS","MARUTI.NS","SUNPHARMA.NS",
        "NTPC.NS","POWERGRID.NS","TITAN.NS","ULTRACEMCO.NS","WIPRO.NS",
        "TECHM.NS","HCLTECH.NS","ADANIENT.NS","ADANIPORTS.NS","JSWSTEEL.NS",
        "TATASTEEL.NS","COALINDIA.NS","ONGC.NS","BPCL.NS","IOC.NS"
    ]

stocks = get_stock_list()

# =========================
# SHOW STOCK LIST
# =========================
st.header("📋 Stock Universe")

st.write(f"Total Stocks: {len(stocks)}")
st.dataframe(pd.DataFrame(stocks, columns=["Stocks"]))

# =========================
# DIAGNOSTICS
# =========================
st.header("🧠 Why Stocks Are Not Selected")

diagnostics = []

for ticker in stocks:
    try:
        df = yf.download(ticker, period="3mo", progress=False)

        if df is None or len(df) < 50:
            continue

        close = df["Close"]
        price = close.iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        momentum = ((price - close.iloc[-5]) / close.iloc[-5]) * 100
        recent_high = close[-20:].max()

        reasons = []

        if price < ma20:
            reasons.append("Below 20DMA")
        if ma20 < ma50:
            reasons.append("Weak Trend")
        if momentum < 1:
            reasons.append("Low Momentum")
        if price < 0.98 * recent_high:
            reasons.append("Not near breakout")

        status = "Selected" if len(reasons) == 0 else "Rejected"

        diagnostics.append({
            "Stock": ticker,
            "Momentum %": round(momentum,2),
            "Status": status,
            "Reason": ", ".join(reasons)
        })

    except:
        pass

st.dataframe(pd.DataFrame(diagnostics))

# =========================
# EARLY UPTREND DETECTION
# =========================
st.header("🎯 Stocks About to Enter Uptrend")

early_list = []

for ticker in stocks:
    try:
        df = yf.download(ticker, period="3mo", progress=False)

        if df is None or len(df) < 50:
            continue

        close = df["Close"]
        price = close.iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        momentum = ((price - close.iloc[-5]) / close.iloc[-5]) * 100
        recent_high = close[-20:].max()

        cond1 = abs(price - ma20)/ma20 < 0.03
        cond2 = ma20 >= ma50 * 0.98
        cond3 = 0 < momentum < 3
        cond4 = price >= 0.90 * recent_high

        score = sum([cond1, cond2, cond3, cond4])

        if score >= 3:
            early_list.append({
                "Stock": ticker,
                "Price": round(price,2),
                "Entry": round(ma20,2),
                "Breakout": round(recent_high,2),
                "Momentum": round(momentum,2)
            })

    except:
        pass

df_early = pd.DataFrame(early_list)

if not df_early.empty:
    st.success(f"{len(df_early)} stocks ready")
    st.dataframe(df_early)
else:
    st.warning("No stocks ready yet")

# =========================
# FINAL STRATEGY
# =========================
st.header("🎯 Final Strategy")

if real_rate and real_rate < 0:
    st.success("Aggressive buying")
elif real_rate and real_rate > 1:
    st.error("Reduce risk")
else:
    st.warning("Selective buying only")
