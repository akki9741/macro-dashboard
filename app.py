import streamlit as st
import yfinance as yf
import pandas as pd
from fredapi import Fred

st.set_page_config(page_title="Dynamic India Screener", layout="wide")

fred = Fred(api_key=st.secrets["FRED_API_KEY"])

# =========================
# FETCH FUNCTION
# =========================
def fetch(ticker):
    try:
        df = yf.download(ticker, period="6mo", progress=False)

        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df
    except:
        return None

# =========================
# 🇺🇸 US MACRO
# =========================
st.header("🇺🇸 US Macro")

try:
    us10y = fetch("^TNX")
    cpi = fred.get_series("CPIAUCSL").dropna()

    us10y_val = float(us10y["Close"].iloc[-1]) / 10
    cpi_yoy = ((float(cpi.iloc[-1]) / float(cpi.iloc[-12])) - 1) * 100
    real_rate = us10y_val - cpi_yoy

    st.write(f"US 10Y: {round(us10y_val,2)}%")
    st.write(f"CPI: {round(cpi_yoy,2)}%")
    st.write(f"Real Rate: {round(real_rate,2)}%")

except:
    st.warning("Macro unavailable")

# =========================
# 📊 DYNAMIC STOCK UNIVERSE
# =========================
st.header("📊 India Dynamic Screener")

# 🔥 BIGGER UNIVERSE (NOT HAND-PICKED)
stocks = pd.read_csv(
    "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
)

stocks = stocks["SYMBOL"].tolist()

# Convert to yfinance format
stocks = [s + ".NS" for s in stocks]

# Limit for performance (important)
stocks = stocks[:400]

selected = []
rejected = []

for stock in stocks:

    df = fetch(stock)

    if df is None or len(df) < 60:
        continue

    try:
        close = df["Close"].dropna()

        price = float(close.iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])
        ma50 = float(close.rolling(50).mean().iloc[-1])

        recent_high = float(close[-20:].max())
        recent_low = float(close[-20:].min())

        # =========================
        # 🎯 TRUE EARLY BREAKOUT
        # =========================
        range_pct = ((recent_high - recent_low) / recent_low) * 100
        is_compressed = range_pct < 8

        breakout = price > recent_high * 0.995

        distance = ((price - ma20) / ma20) * 100
        not_extended = distance < 4

        if is_compressed and breakout and not_extended:

            selected.append({
                "Stock": stock,
                "Momentum %": round(distance, 2),
                "Reason": "Compression + Fresh Breakout"
            })

        else:
            reason = []

            if not is_compressed:
                reason.append("No base")

            if not breakout:
                reason.append("No breakout")

            if not not_extended:
                reason.append("Extended")

            rejected.append((stock, ", ".join(reason)))

    except:
        rejected.append((stock, "Error"))

# =========================
# OUTPUT
# =========================
st.subheader("🚀 Early Breakout Stocks")

if selected:
    df_sel = pd.DataFrame(selected).sort_values(by="Momentum %")
    st.dataframe(df_sel.head(5))   # only top 5
else:
    st.warning("No early setups")

# =========================
# WHY NOT SELECTED
# =========================
st.subheader("🧠 Rejected Stocks")

st.dataframe(pd.DataFrame(rejected[:50], columns=["Stock","Reason"]))
