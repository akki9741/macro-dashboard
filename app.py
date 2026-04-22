import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time

st.set_page_config(page_title="Dynamic Market Scanner", layout="wide")
st.title("🚀 Fully Dynamic Stock Screener (No Fixed Stocks)")

# =========================
# FETCH NSE STOCK LIST (DYNAMIC)
# =========================
@st.cache_data(ttl=86400)
def get_nse_stocks():
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df = pd.read_csv(url)

        symbols = df["SYMBOL"].tolist()

        # Convert to Yahoo format
        stocks = [s + ".NS" for s in symbols]

        return stocks[:300]   # limit for performance

    except:
        return []

stocks = get_nse_stocks()

st.header("📋 Total NSE Stocks Loaded")
st.write(len(stocks))

# =========================
# MACRO (SIMPLE VERSION)
# =========================
st.header("🌍 Market Context")

st.info("Using price-action based detection (no external dependency)")

# =========================
# GOLD (FIXED)
# =========================
def get_gold():
    for s in ["GC=F", "GLD"]:
        try:
            df = yf.download(s, period="3mo", progress=False)
            if not df.empty:
                return df
        except:
            pass
    return None

gold = get_gold()

if gold is not None:
    st.success("Gold data loaded")
else:
    st.error("Gold failed")

# =========================
# DIAGNOSTICS
# =========================
st.header("🧠 Diagnostics (Why Not Selected)")

diagnostics = []

def safe_download(ticker):
    try:
        df = yf.download(ticker, period="3mo", progress=False)
        if df is not None and not df.empty:
            return df
    except:
        return None
    return None

for ticker in stocks:
    try:
        df = safe_download(ticker)

        if df is None or len(df) < 50:
            diagnostics.append({
                "Stock": ticker,
                "Status": "Skipped",
                "Reason": "No data"
            })
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

        if len(reasons) == 0:
            status = "Selected"
            reason = "Strong setup"
        else:
            status = "Rejected"
            reason = ", ".join(reasons)

        diagnostics.append({
            "Stock": ticker,
            "Momentum %": round(momentum, 2),
            "Status": status,
            "Reason": reason
        })

    except:
        diagnostics.append({
            "Stock": ticker,
            "Status": "Error",
            "Reason": "Fetch issue"
        })

diag_df = pd.DataFrame(diagnostics)

st.dataframe(diag_df)

# =========================
# EARLY UPTREND DETECTION
# =========================
st.header("🎯 Stocks About to Enter Uptrend")

early = []

for ticker in stocks:
    try:
        df = safe_download(ticker)

        if df is None or len(df) < 50:
            continue

        close = df["Close"]
        price = close.iloc[-1]

        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]

        momentum = ((price - close.iloc[-5]) / close.iloc[-5]) * 100
        high = close[-20:].max()

        cond1 = abs(price - ma20) / ma20 < 0.03
        cond2 = ma20 >= ma50 * 0.98
        cond3 = 0 < momentum < 3
        cond4 = price >= 0.9 * high

        score = sum([cond1, cond2, cond3, cond4])

        if score >= 3:
            early.append({
                "Stock": ticker,
                "Price": round(price, 2),
                "Entry": round(ma20, 2),
                "Breakout": round(high, 2),
                "Momentum": round(momentum, 2)
            })

    except:
        pass

early_df = pd.DataFrame(early)

if not early_df.empty:
    st.success(f"{len(early_df)} stocks ready")
    st.dataframe(early_df)
else:
    st.warning("No stocks ready yet")

# =========================
# FINAL STRATEGY
# =========================
st.header("🎯 Final Strategy")

st.warning("Selective buying only — Market not trending strongly")
