import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="MF Tracker", layout="wide")

# -----------------------------
# TITLE
# -----------------------------
st.title("📊 MF Tracker")

# -----------------------------
# CACHE
# -----------------------------
@st.cache_data
def fetch_data(ticker, period):
    data = yf.Ticker(ticker).history(period=period)
    data.index = data.index.tz_localize(None)  # 🔥 FIX HERE
    return data

@st.cache_data
def fetch_info(ticker):
    return yf.Ticker(ticker).info

# -----------------------------
# INPUT
# -----------------------------
ticker_symbol = "0P0001YOWM.BO"

period = st.selectbox(
    "Select Time Period",
    ["1mo", "3mo", "6mo", "1y", "5y"],
    index=3
)

# -----------------------------
# FETCH DATA
# -----------------------------
hist = fetch_data(ticker_symbol, period)
nifty = fetch_data("^NSEI", period)
sensex = fetch_data("^BSESN", period)

info = fetch_info(ticker_symbol)

# -----------------------------
# METRICS
# -----------------------------
nav = info.get("currentPrice", None)
prev_close = info.get("previousClose", None)

col1, col2 = st.columns(2)

with col1:
    st.metric("💰 NAV", nav)

with col2:
    st.metric("📉 Previous Close", prev_close)

# -----------------------------
# ALIGN DATA
# -----------------------------
df = pd.DataFrame({
    "iSIF": hist["Close"],
    "NIFTY": nifty["Close"],
    "SENSEX": sensex["Close"]
}).dropna()

# -----------------------------
# DATE FILTER (FIXED ✅)
# -----------------------------
start_date = st.date_input("Start Date", df.index.min())
end_date = st.date_input("End Date", df.index.max())

start = pd.to_datetime(start_date)
end = pd.to_datetime(end_date)

df = df[(df.index >= start) & (df.index <= end)]

# -----------------------------
# RESET BUTTON
# -----------------------------
if st.button("Reset Filters"):
    st.rerun()

# -----------------------------
# NORMALIZATION
# -----------------------------
normalize = st.checkbox("Normalize to Base 100", value=True)

def normalize_series(series):
    return series / series.iloc[0] * 100

# -----------------------------
# RETURNS
# -----------------------------
returns = (df.iloc[-1] / df.iloc[0] - 1) * 100

col3, col4, col5 = st.columns(3)

with col3:
    st.metric("Fund Return %", f"{returns['iSIF']:.2f}%")

with col4:
    st.metric("NIFTY Return %", f"{returns['NIFTY']:.2f}%")

with col5:
    st.metric("SENSEX Return %", f"{returns['SENSEX']:.2f}%")

# -----------------------------
# USER SELECTION
# -----------------------------
options = st.multiselect(
    "Select data to display",
    ["Fund NAV", "NIFTY 50", "SENSEX"],
    default=["Fund NAV", "NIFTY 50"]
)

# -----------------------------
# PLOT
# -----------------------------
fig = go.Figure()

if "Fund NAV" in options:
    y = df["iSIF"]
    if normalize:
        y = normalize_series(y)
    fig.add_trace(go.Scatter(x=df.index, y=y, name="Fund NAV"))

if "NIFTY 50" in options:
    y = df["NIFTY"]
    if normalize:
        y = normalize_series(y)
    fig.add_trace(go.Scatter(x=df.index, y=y, name="NIFTY 50"))

if "SENSEX" in options:
    y = df["SENSEX"]
    if normalize:
        y = normalize_series(y)
    fig.add_trace(go.Scatter(x=df.index, y=y, name="SENSEX"))

fig.update_layout(
    title="Performance Comparison",
    template="plotly_dark",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# DRAWDOWN
# -----------------------------
st.subheader("📉 Drawdown Analysis")

drawdown = df / df.cummax() - 1

fig_dd = go.Figure()
fig_dd.add_trace(go.Scatter(x=df.index, y=drawdown["iSIF"], name="Fund Drawdown"))

fig_dd.update_layout(template="plotly_dark")

st.plotly_chart(fig_dd, use_container_width=True)

# -----------------------------
# DATA TABLE
# -----------------------------
st.subheader("📋 Data Table")
st.dataframe(df.tail(50))

# -----------------------------
# PERCENTAGE CHANGE
# -----------------------------
# -----------------------------
# PERCENTAGE CHANGE (NO STYLE)
# -----------------------------
pct_df = df.pct_change() * 100
pct_df.columns = ["Fund %", "NIFTY %", "SENSEX %"]
pct_df = pct_df.dropna()

st.subheader("📊 Daily Percentage Change")
st.dataframe(pct_df.tail(50).round(2), width="stretch")


# -----------------------------
# PORTFOLIO CALCULATIONS
# -----------------------------
units = 105365.478
initial_investment = 1_000_000

portfolio_df = df.copy()

portfolio_df["Fund Value"] = portfolio_df["iSIF"] * units
portfolio_df["Daily Change ₹"] = portfolio_df["Fund Value"].diff()
portfolio_df["Daily Change %"] = portfolio_df["Fund Value"].pct_change() * 100
portfolio_df["PnL ₹"] = portfolio_df["Fund Value"] - initial_investment
portfolio_df["PnL %"] = (
    portfolio_df["Fund Value"] / initial_investment - 1
) * 100

portfolio_df = portfolio_df.dropna()

# -----------------------------
# CREATE DISPLAY DF (FIXED ✅)
# -----------------------------
display_df = portfolio_df[
    ["iSIF", "Fund Value", "Daily Change ₹", "Daily Change %", "PnL ₹", "PnL %"]
].copy()

# -----------------------------
# ROUND VALUES
# -----------------------------
display_df["iSIF"] = display_df["iSIF"].round(2)
display_df["Fund Value"] = display_df["Fund Value"].round(0)
display_df["Daily Change ₹"] = display_df["Daily Change ₹"].round(0)
display_df["PnL ₹"] = display_df["PnL ₹"].round(0)

display_df["Daily Change %"] = display_df["Daily Change %"].round(2)
display_df["PnL %"] = display_df["PnL %"].round(2)

# -----------------------------
# DISPLAY
# -----------------------------
st.subheader("💰 Portfolio Performance (Using Units)")
st.dataframe(display_df.tail(50), width="stretch")
