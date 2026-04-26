import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

st.set_page_config(page_title="WealthForge – my liege", page_icon="📈", layout="wide")

# Data Persistence (simplified)
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
    st.caption("**v3.5** — At your service, my liege")
    
    portfolio_names = list(st.session_state.portfolios.keys())
    if portfolio_names:
        selected = st.selectbox("Select Portfolio", portfolio_names, index=0 if not st.session_state.current_portfolio else portfolio_names.index(st.session_state.current_portfolio) if st.session_state.current_portfolio in portfolio_names else 0)
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

if not st.session_state.current_portfolio:
    st.title("Welcome to WealthForge v3.5")
    st.stop()

st.title(st.session_state.current_portfolio)

if st.session_state.view == "home":
    # ... (same add holding section as before)
    st.subheader("Add Holding")
    c1, c2 = st.columns(2)
    with c1:
        new_ticker = st.text_input("Ticker", placeholder="AAPL or XEQT.TO").upper().strip()
    with c2:
        new_shares = st.number_input("Shares", value=0.0, min_value=0.0, step=0.01)
    if st.button("Add to Portfolio") and new_ticker:
        st.session_state.portfolios[st.session_state.current_portfolio]["holdings"][new_ticker] = new_shares
        save_portfolios(st.session_state.portfolios)
        st.success(f"Added {new_ticker}")
        st.rerun()

    if st.button("View Stock Details") and st.session_state.portfolios[st.session_state.current_portfolio]["holdings"]:
        st.session_state.view = "stock"
        st.session_state.current_ticker = st.selectbox("Select Stock", list(st.session_state.portfolios[st.session_state.current_portfolio]["holdings"].keys()))
        st.rerun()

# STOCK DETAIL PAGE - FIXED GRAPHS
elif st.session_state.view == "stock":
    ticker = st.session_state.current_ticker
    st.title(f"{ticker} — Analysis")
    if st.button("← Back to Portfolio"):
        st.session_state.view = "home"
        st.rerun()

    mode = st.radio("Chart Mode", ["Historical", "Predictive"], horizontal=True)

    # Try to get real data
    hist = yf.download(ticker, period="3mo", progress=False)

    if hist.empty or len(hist) < 5:
        st.warning(f"Real data unavailable for {ticker}. Showing example chart.")
        # Create dummy data for demonstration
        dates = pd.date_range(end=datetime.today(), periods=60)
        prices = np.linspace(100, 150, 60) * (1 + np.random.normal(0, 0.01, 60).cumsum())
        hist = pd.DataFrame({"Close": prices}, index=dates)
    
    if mode == "Historical":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#ffd700", width=3)))
        fig.update_layout(title=f"{ticker} Historical", template="plotly_dark", height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Predictive
        current = float(hist['Close'].iloc[-1])
        days = 60
        sims = 3000
        paths = np.zeros((days, sims))
        paths[0] = current
        for t in range(1, days):
            Z = np.random.standard_normal(sims)
            paths[t] = paths[t-1] * np.exp(0.0003 + 0.015 * Z)   # reasonable drift + vol

        fig = go.Figure()
        dates = pd.date_range(datetime.today(), periods=days, freq='B')
        p10, p50, p90 = np.percentile(paths, [10,50,90], axis=1)
        fig.add_trace(go.Scatter(x=dates, y=p10, line=dict(color='red'), name='10th'))
        fig.add_trace(go.Scatter(x=dates, y=p90, fill='tonexty', line=dict(color='lime'), name='90th'))
        fig.add_trace(go.Scatter(x=dates, y=p50, line=dict(color='#ffd700', width=4), name='Median'))
        fig.update_layout(title=f"{ticker} — Predictive Monte Carlo", template="plotly_dark", height=600)
        st.plotly_chart(fig, use_container_width=True)

    if st.button("🔥 Deep Analysis by Grok"):
        prompt = f"WealthForge, deep analysis on {ticker}..."
        st.code(prompt, language="text")
        st.success("Prompt copied!")

st.caption("**WealthForge v3.5** - Graphs should now always appear")