import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

st.set_page_config(page_title="WealthForge – my liege", page_icon="📈", layout="wide")

# Data Persistence
def load_portfolios():
    if os.path.exists("wealthforge_data.json"):
        try:
            with open("wealthforge_data.json", "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_portfolios(portfolios):
    with open("wealthforge_data.json", "w") as f:
        json.dump(portfolios, f)

if "portfolios" not in st.session_state:
    st.session_state.portfolios = load_portfolios()
if "current_portfolio" not in st.session_state:
    st.session_state.current_portfolio = None
if "view" not in st.session_state:
    st.session_state.view = "home"
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = None

# Sidebar
with st.sidebar:
    st.title("📈 WealthForge")
    st.caption("v3.2.7 - At your service, my liege")
    
    portfolio_names = list(st.session_state.portfolios.keys())
    if portfolio_names:
        selected = st.selectbox("Select Portfolio", portfolio_names, 
                              index=portfolio_names.index(st.session_state.current_portfolio) if st.session_state.current_portfolio in portfolio_names else 0)
        st.session_state.current_portfolio = selected

    st.divider()
    new_name = st.text_input("New Portfolio Name")
    if st.button("Create Portfolio") and new_name:
        st.session_state.portfolios[new_name] = {"holdings": {}}
        st.session_state.current_portfolio = new_name
        save_portfolios(st.session_state.portfolios)
        st.success(f"Created {new_name}")
        st.rerun()

    if st.session_state.current_portfolio and st.button("Delete Portfolio"):
        del st.session_state.portfolios[st.session_state.current_portfolio]
        st.session_state.current_portfolio = None
        save_portfolios(st.session_state.portfolios)
        st.rerun()

# Main App
if not st.session_state.current_portfolio:
    st.title("Welcome to WealthForge v3.2.7")
    st.stop()

st.title(st.session_state.current_portfolio)

if st.session_state.view == "home":
    holdings = st.session_state.portfolios[st.session_state.current_portfolio]["holdings"]

    if holdings:
        tickers = list(holdings.keys())
        data = yf.download(tickers, period="5d", progress=False)['Close']
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest

        total_value = 0
        rows = []
        for t in tickers:
            shares = holdings[t]
            price = float(latest[t])
            change = float(((latest[t] - prev[t]) / prev[t] * 100).round(2))
            value = shares * price
            total_value += value
            rows.append({
                "Ticker": t,
                "Shares": f"{shares:.4f}",
                "Price": f"${price:,.2f}",
                "Change": f"{change:+.2f}%",
                "Value": f"${value:,.2f}"
            })

        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.metric("Total Portfolio Value", f"${total_value:,.2f}")

    st.subheader("Add Holding")
    col1, col2 = st.columns(2)
    with col1:
        new_ticker = st.text_input("Ticker Symbol", placeholder="XEQT.TO or AAPL").upper().strip()
    with col2:
        new_shares = st.number_input("Number of Shares", value=0.0, min_value=0.0, step=0.01)
    
    if st.button("Add to Portfolio") and new_ticker:
        st.session_state.portfolios[st.session_state.current_portfolio]["holdings"][new_ticker] = new_shares
        save_portfolios(st.session_state.portfolios)
        st.success(f"Added {new_ticker}")
        st.rerun()

    if st.button("View Stock Details") and holdings:
        st.session_state.view = "stock"
        st.session_state.current_ticker = st.selectbox("Choose a stock", list(holdings.keys()))
        st.rerun()

# ====================== STOCK DETAIL PAGE WITH CHARTS ======================
elif st.session_state.view == "stock":
    ticker = st.session_state.current_ticker
    st.title(f"{ticker} — Analysis")
    if st.button("← Back to Portfolio"):
        st.session_state.view = "home"
        st.rerun()

    tf_options = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
    timeframe = st.selectbox("Timeframe", list(tf_options.keys()))
    mode = st.radio("Chart Mode", ["Historical", "Predictive"], horizontal=True)

    hist = yf.download(ticker, period=tf_options[timeframe], progress=False)

    if mode == "Historical":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#ffd700", width=3)))
        fig.update_layout(title=f"{ticker} Historical ({timeframe})", template="plotly_dark", height=650)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Predictive Monte Carlo
        returns = hist['Close'].pct_change().dropna()
        current = float(hist['Close'].iloc[-1])
        days = 60
        sims = 4000
        paths = np.zeros((days, sims))
        paths[0] = current
        for t in range(1, days):
            Z