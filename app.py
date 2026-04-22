import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(layout="wide")
st.title("🚀 Pro Macro + Smart Stock Screener")

# =========================
# SAFE FETCH FUNCTION
# =========================
def fetch(ticker, period="6mo"):
    try:
        df = yf.download(ticker, period=period, progress=False, threads=False)
        if df is not None and not df.empty and len(df) > 50:
            return df
    except:
        return None
    return None

# =========================
# 🇺🇸 US MACRO
# =========================
st.header("🇺🇸 US Financial Repression")

tnx = fetch("^TNX", "5d")
us10y = None
if tnx is not None:
    try:
        us10y = float(tnx["Close"].dropna().iloc[-1]) / 10
        us10y = round(us10y, 2)
    except:
        us10y = None

cpi = 3.2

real_rate = round(us10y - cpi, 2) if us10y is not None else None

col1, col2, col3 = st.columns(3)
col1.metric("US 10Y", f"{us10y}%" if us10y else "N/A")
col2.metric("CPI", f"{cpi}%")
col3.metric("Real Rate", f"{real_rate}%" if real_rate else "N/A")

if real_rate is None:
    st.warning("Data unavailable")
elif real_rate < 0:
    st.success("🔥 Liquidity Boom → Bullish")
elif real_rate < 1:
    st.warning("⚠️ Neutral → Selective Buying")
else:
    st.error("❌ Tight Liquidity → Risk-Off")

# =========================
# 🪙 GOLD (CRASH-PROOF)
# =========================
st.header("🪙 Gold View")

gold = fetch("GC=F", "3mo")

if gold is None or gold.empty:
    st.error("Gold data not available")

else:
    close = gold["Close"].dropna()

    if len(close) < 25:
        st.warning("Gold data insufficient")
    else:
        try:
            price = close.iloc[-1]
            ma20 = close.rolling(20).mean().iloc[-1]

            if pd.isna(price) or pd.isna(ma20):
                st.warning("Gold data incomplete")
            else:
                price = float(price)
                ma20 = float(ma20)

                if price > ma20:
                    st.success(f"Gold Bullish ({round(price,2)})")
                else:
                    st.warning(f"Gold Cooling ({round(price,2)})")

                st.line_chart(close)

        except Exception as e:
            st.error(f"Gold processing error: {e}")

# =========================
# NSE STOCK LIST
# =========================
@st.cache_data(ttl=86400)
def get_nse():
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    df = pd.read_csv(url)
    return [s + ".NS" for s in df["SYMBOL"].tolist()]

stocks = get_nse()[:200]

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

    close = df["Close"].dropna()
    if len(close) < 100:
        continue

    try:
        ma50 = close.rolling(50).mean().iloc[-1]
        ma100 = close.rolling(100).mean().iloc[-1]
        vol = close.pct_change().std()

        if (
            close.iloc[-1] > ma50
            and ma50 > ma100
            and vol < 0.04
        ):
            quality.append(s)

    except:
        continue

    time.sleep(0.1)

quality = quality[:60]

st.success(f"{len(quality)} stocks passed quality filter")
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

    close = df["Close"].dropna()
    if len(close) < 60:
        continue

    try:
        price = float(close.iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])
        ma50 = float(close.rolling(50).mean().iloc[-1])

        momentum = ((price - close.iloc[-5]) / close.iloc[-5]) * 100
        high = close[-20:].max()

        cond1 = abs(price - ma20)/ma20 < 0.04
        cond2 = ma20 >= ma50 * 0.95
        cond3 = -1 < momentum < 3.5
        cond4 = price >= 0.88 * high

        score = sum([cond1, cond2, cond3, cond4])

        reasons = []
        if not cond1:
            reasons.append("Far from support")
        if not cond2:
            reasons.append("Weak trend")
        if not cond3:
            reasons.append("Momentum issue")
        if not cond4:
            reasons.append("No breakout setup")

        if score >= 3:
            selected.append({
                "Stock": s,
                "Score": score,
                "Entry": round(ma20,2),
                "Breakout": round(high,2),
                "Momentum": round(momentum,2)
            })
        else:
            rejected.append({
                "Stock": s,
                "Reason": ", ".join(reasons)
            })

    except:
        continue

    time.sleep(0.1)

selected = sorted(selected, key=lambda x: x["Score"], reverse=True)[:5]

# =========================
# DISPLAY
# =========================
st.write(f"Selected stocks: {len(selected)}")

if selected:
    st.success("🔥 High Probability Stocks")
    st.dataframe(pd.DataFrame(selected))
else:
    st.warning("No strong setups (market sideways)")

# =========================
# DIAGNOSTICS
# =========================
st.header("🧠 Why Stocks Not Selected")

if rejected:
    st.dataframe(pd.DataFrame(rejected))
else:
    st.write("All passed")

# =========================
# FINAL STRATEGY
# =========================
st.header("🎯 Final Strategy")

if real_rate is not None and real_rate < 1:
    st.warning("Selective buying — focus on breakout stocks only")
elif real_rate is not None and real_rate >= 1:
    st.error("Avoid aggressive buying")
else:
    st.info("Wait for clarity")
