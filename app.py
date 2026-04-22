import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(layout="wide")
st.title("🚀 Pro Macro + India Stock Screener")

# =========================
# SAFE DOWNLOAD FUNCTION
# =========================
def fetch(ticker, period="6mo"):
    try:
        df = yf.download(ticker, period=period, progress=False)
        if df is not None and not df.empty and len(df) > 50:
            return df
    except:
        return None
    return None

# =========================
# 🇺🇸 US MACRO (REPRESSION)
# =========================
st.header("🇺🇸 US Financial Repression")

# US 10Y
tnx = fetch("^TNX", "5d")
us10y = round(tnx["Close"].iloc[-1] / 10, 2) if tnx is not None else None

# CPI (fallback static — stable)
cpi = 3.2

# DXY
dxy = fetch("DX-Y.NYB", "5d")
dxy_val = round(dxy["Close"].iloc[-1], 2) if dxy is not None else None

# Real Rate
real_rate = round(us10y - cpi, 2) if us10y else None

col1, col2, col3 = st.columns(3)
col1.metric("US 10Y", f"{us10y}%" if us10y else "N/A")
col2.metric("CPI", f"{cpi}%")
col3.metric("Real Rate", f"{real_rate}%" if real_rate else "N/A")

# Signal
if real_rate is None:
    st.warning("Data unavailable")
elif real_rate < 0:
    st.success("🔥 Liquidity Boom → Bullish")
elif real_rate < 1:
    st.warning("⚠️ Neutral → Selective Buying")
else:
    st.error("❌ Tight Liquidity → Risk-Off")

# =========================
# 🪙 GOLD
# =========================
st.header("🪙 Gold View")

gold = fetch("GC=F", "3mo")
if gold is not None:
    price = round(gold["Close"].iloc[-1], 2)
    ma20 = gold["Close"].rolling(20).mean().iloc[-1]

    if price > ma20:
        st.success(f"Gold Bullish ({price})")
    else:
        st.warning(f"Gold Cooling ({price})")

    st.line_chart(gold["Close"])
else:
    st.error("Gold data failed")

# =========================
# 📋 NSE STOCK LIST (DYNAMIC)
# =========================
@st.cache_data(ttl=86400)
def get_nse():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    df = pd.read_csv(url)
    return [s + ".NS" for s in df["SYMBOL"].tolist()]

stocks = get_nse()[:300]

st.header("📊 NSE Universe")
st.write(f"Stocks Loaded: {len(stocks)}")

# =========================
# STEP 1 → QUALITY FILTER
# =========================
st.header("📊 Step 1: Quality Stocks")

quality = []

for s in stocks:
    df = fetch(s)
    if df is None:
        continue

    close = df["Close"]

    ma50 = close.rolling(50).mean().iloc[-1]
    ma100 = close.rolling(100).mean().iloc[-1]
    volatility = close.pct_change().std()

    if (
        close.iloc[-1] > ma50
        and ma50 > ma100
        and volatility < 0.035
    ):
        quality.append(s)

quality = quality[:60]

st.success(f"{len(quality)} stocks shortlisted")
st.dataframe(pd.DataFrame(quality, columns=["Stocks"]))

# =========================
# STEP 2 → EARLY UPTREND
# =========================
st.header("🎯 Stocks About to Enter Uptrend")

selected = []
rejected = []

for s in quality:
    df = fetch(s)
    if df is None:
        continue

    close = df["Close"]
    price = close.iloc[-1]

    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    momentum = ((price - close.iloc[-5]) / close.iloc[-5]) * 100
    high = close[-20:].max()

    reasons = []

    cond1 = abs(price - ma20) / ma20 < 0.025
    cond2 = ma20 >= ma50 * 0.98
    cond3 = 0 < momentum < 2.5
    cond4 = price >= 0.92 * high

    if not cond1:
        reasons.append("Not near support")
    if not cond2:
        reasons.append("Weak trend")
    if not cond3:
        reasons.append("Momentum low/high")
    if not cond4:
        reasons.append("No breakout setup")

    if cond1 and cond2 and cond3 and cond4:
        selected.append({
            "Stock": s,
            "Entry": round(ma20,2),
            "Breakout": round(high,2),
            "Momentum": round(momentum,2)
        })
    else:
        rejected.append({
            "Stock": s,
            "Reason": ", ".join(reasons)
        })

selected = selected[:5]

# =========================
# DISPLAY SELECTED
# =========================
if selected:
    st.success(f"{len(selected)} High Probability Stocks")
    st.dataframe(pd.DataFrame(selected))
else:
    st.warning("No stocks ready")

# =========================
# DIAGNOSTICS
# =========================
st.header("🧠 Why Stocks Are Not Selected")

if rejected:
    st.dataframe(pd.DataFrame(rejected))
else:
    st.write("All passed (rare case)")

# =========================
# FINAL STRATEGY
# =========================
st.header("🎯 Final Strategy")

if real_rate and real_rate < 1:
    st.warning("Selective buying only — Focus on breakouts")
elif real_rate and real_rate >= 1:
    st.error("Avoid aggressive buying")
else:
    st.info("Wait for clarity")
