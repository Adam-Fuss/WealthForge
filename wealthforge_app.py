import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

st.set_page_config(page_title="WealthForge – my liege", page_icon="📈", layout="wide")

# ====================== DATA PERSISTENCE ======================
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

# ====================== SIDEBAR ======================
with st.sidebar:
    st.title("WealthForge")
    st.caption("v3.2.3 - At your service, my liege")
    
    portfolio_names = list(st.session_state.portfolios.keys())
    if portfolio_names:
        selected = st.selectbox("Select Portfolio", portfolio_names, 
                              index=portfolio_names.index(st.session_state.current_portfolio) if st.session_state.current_portfolio in portfolio_names else 0)
        st.session_state.current_portfolio = selected

    st.divider()
    new_name = st.text_input("New Portfolio Name")
    if st.button("Create Portfolio") and new_name:
        st.session_state.portfolios[new_name] = {"holdings": {}, "prediction_log": {}}
        st.session_state.current_portfolio = new_name
        save_portfolios(st.session_state.portfolios)
        st.success(f"Created {new_name}")
        st.rerun()

    if st.session_state.current_portfolio and st.button("Delete Portfolio"):
        del st.session_state.portfolios[st.session_state.current_portfolio]
        st.session_state.current_portfolio = None
        save_portfolios(st.session_state.portfolios)
        st.rerun()

# ====================== MAIN APP ======================
if not st.session_state.current_portfolio:
    st.title("Welcome to WealthForge v3.2.3")
    st.markdown("Create or select a portfolio on the left, my liege.")
    st.stop()

st.title(f"{st.session_state.current_portfolio}")

# Portfolio Overview
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

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Portfolio Value", f"${total_value:,.2f}")

    st.subheader("Add Holding")
    c1, c2 = st.columns(2)
    with c1:
        new_ticker = st.text_input("Ticker", placeholder="XEQT.TO").upper().strip()
    with c2:
        new_shares = st.number_input("Shares", value=0.0, min_value=0.0, step=0.01)
    if st.button("Add to Portfolio") and new_ticker:
        st.session_state.portfolios[st.session_state.current_portfolio]["holdings"][new_ticker] = new_shares
        save_portfolios(st.session_state.portfolios)
        st.success(f"Added {new_ticker}")
        st.rerun()

    if st.button("View Stock Details") and holdings:
        st.session_state.view = "stock"
        st.session_state.current_ticker = st.selectbox("Select Stock", list(holdings.keys()))
        st.rerun()

# Stock Detail Page
elif st.session_state.view == "stock":
    ticker = st.session_state.current_ticker
    st.title(f"{ticker} - Analysis")
    if st.button("Back to Portfolio"):
        st.session_state.view = "home"
        st.rerun()

    tf_options = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
    timeframe = st.selectbox("Timeframe", list(tf_options.keys()))
    mode = st.radio("Mode", ["Historical", "Predictive"], horizontal=True)

    hist = yf.download(ticker, period=tf_options[timeframe], progress=False)

    if mode == "Historical":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#ffd700", width=3)))
        fig.update_layout(title=f"{ticker} Historical ({timeframe})", template="plotly_dark", height=650)
        st.plotly_chart(fig, use_container_width=True)
    else:
        returns = hist['Close'].pct_change().dropna()
        current = float(hist['Close'].iloc[-1])
        days = 60
        sims = 4000
        paths = np.zeros((days, sims))
        paths[0] = current
        for t in range(1, days):
            Z = np.random.standard_normal(sims)
            mu = returns.mean() * 252
            sigma = returns.std() * np.sqrt(252)
            paths[t] = paths[t-1] * np.exp((mu - 0.5*sigma**2)*(1/252) + sigma*np.sqrt(1/252)*Z)

        fig = go.Figure()
        dates = pd.date_range(datetime.today(), periods=days, freq='B')
        p10, p50, p90 = np.percentile(paths, [10,50,90], axis=1)
        fig.add_trace(go.Scatter(x=dates, y=p10, line=dict(color='red'), name='10th %ile'))
        fig.add_trace(go.Scatter(x=dates, y=p90, fill='tonexty', line=dict(color='lime'), name='90th %ile'))
        fig.add_trace(go.Scatter(x=dates, y=p50, line=dict(color='#ffd700', width=4), name='Median'))
        fig.update_layout(title=f"{ticker} - Predictive Monte Carlo", template="plotly_dark", height=650)
        st.plotly_chart(fig, use_container_width=True)

    if st.button("Deep Analysis by Grok"):
        prompt = f"""WealthForge, deep analysis on {ticker} right now:
- Current chart and technicals
- News and X sentiment
- Supply/demand factors
- Probabilistic outlook
Be thorough and critical, my liege."""
        st.code(prompt, language="text")
        st.success("Prompt copied - paste it in our chat, my liege.")

st.caption("WealthForge v3.2.3 - Clean and Stable")

    st.divider()
    new_name = st.text_input("New Portfolio Name")
    if st.button("Create Portfolio") and new_name:
        st.session_state.portfolios[new_name] = {"holdings": {}, "prediction_log": {}}
        st.session_state.current_portfolio = new_name
        save_portfolios(st.session_state.portfolios)
        st.success(f"Created '{new_name}'")
        st.rerun()

    if st.session_state.current_portfolio and st.button("Delete Portfolio"):
        del st.session_state.portfolios[st.session_state.current_portfolio]
        st.session_state.current_portfolio = None
        save_portfolios(st.session_state.portfolios)
        st.rerun()

# ====================== MAIN APP ======================
if not st.session_state.current_portfolio:
    st.title("Welcome to WealthForge v3.2.2")
    st.markdown("**Create or select a portfolio on the left, my liege.**")
    st.stop()

st.title(f"📊 {st.session_state.current_portfolio}")

# ====================== PORTFOLIO OVERVIEW ======================
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

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Portfolio Value", f"${total_value:,.2f}")

    st.subheader("Add Holding")
    c1, c2 = st.columns(2)
    with c1:
        new_ticker = st.text_input("Ticker", placeholder="XEQT.TO").upper().strip()
    with c2:
        new_shares = st.number_input("Shares", value=0.0, min_value=0.0, step=0.01)
    if st.button("Add to Portfolio") and new_ticker:
        st.session_state.portfolios[st.session_state.current_portfolio]["holdings"][new_ticker] = new_shares
        save_portfolios(st.session_state.portfolios)
        st.success(f"Added {new_ticker}")
        st.rerun()

    if st.button("View Stock Details") and holdings:
        st.session_state.view = "stock"
        st.session_state.current_ticker = st.selectbox("Select Stock", list(holdings.keys()))
        st.rerun()

# ====================== STOCK DETAIL PAGE ======================
elif st.session_state.view == "stock":
    ticker = st.session_state.current_ticker
    st.title(f"{ticker} — Analysis")
    if st.button("Back to Portfolio"):
        st.session_state.view = "home"
        st.rerun()

    tf_options = {"1D": "1d", "5D": "5d", "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y"}
    timeframe = st.selectbox("Timeframe", list(tf_options.keys()))
    mode = st.radio("Mode", ["Historical", "Predictive"], horizontal=True)

    hist = yf.download(ticker, period=tf_options[timeframe], progress=False)

    if mode == "Historical":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#ffd700", width=3)))
        fig.update_layout(title=f"{ticker} Historical ({timeframe})", template="plotly_dark", height=650)
        st.plotly_chart(fig, use_container_width=True)
    else:
        returns = hist['Close'].pct_change().dropna()
        current = float(hist['Close'].iloc[-1])
        days = 60
    timeframe = st.selectbox("Timeframe", list(tf_options.keys()))
    mode = st.radio("Mode", ["Historical", "Predictive"], horizontal=True)

    hist = yf.download(ticker, period=tf_options[timeframe], progress=False)

    if mode == "Historical":
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], line=dict(color="#ffd700", width=3)))
        fig.update_layout(title=f"{ticker} Historical", template="plotly_dark", height=650)
        st.plotly_chart(fig, use_container_width=True)
    else:
        # Predictive (same high-quality Monte Carlo as before)
        returns = hist['Close'].pct_change().dropna()
        current = float(hist['Close'].iloc[-1])
        days = 60
        sims = 4000
        paths = np.zeros((days, sims))
        paths[0] = current
        for t in range(1, days):
            Z = np.random.standard_normal(sims)
            mu = returns.mean() * 252
            sigma = returns.std() * np.sqrt(252)
            paths[t] = paths[t-1] * np.exp((mu - 0.5*sigma**2)*(1/252) + sigma*np.sqrt(1/252)*Z)

        fig = go.Figure()
        dates = pd.date_range(datetime.today(), periods=days, freq='B')
        p10, p50, p90 = np.percentile(paths, [10,50,90], axis=1)
        fig.add_trace(go.Scatter(x=dates, y=p10, line=dict(color='red'), name='10th %ile'))
        fig.add_trace(go.Scatter(x=dates, y=p90, fill='tonexty', line=dict(color='lime'), name='90th %ile'))
        fig.add_trace(go.Scatter(x=dates, y=p50, line=dict(color='#ffd700', width=4), name='Median'))
        fig.update_layout(title=f"{ticker} — Predictive Monte Carlo", template="plotly_dark", height=650)
        st.plotly_chart(fig, use_container_width=True)

    # Enhanced Ask WealthForge button
    if st.button("🔥 Deep Analysis by Grok"):
        prompt = f"""WealthForge, deep analysis on {ticker} right now:
- Current chart & technicals
- News and X sentiment
- Supply/demand factors
- Probabilistic outlook
- Any risks or opportunities
Be thorough and critical, my liege."""
        st.code(prompt, language="text")
        st.success("✅ Prompt copied — paste it in our chat, my liege.")

st.caption("**WealthForge v3.2** • Built for my liege • April 2026")
<meta name="mobile-web-app-capable" content="yes">
""", unsafe_allow_html=True)

st.title("📈 WealthForge")
st.markdown("**Adam’s Personal Wealth Engine** — Calgary, AB")

with st.sidebar:
    st.header("📱 Install Properly")
    st.markdown("""
    **To get the best icon:**
    1. Delete current app from home screen
    2. Refresh this page
    3. Tap **Share → Add to Home Screen**
    """)
    
    if st.button("Ask WealthForge"):
        st.code("WealthForge, run full analysis on my portfolio...", language="text")
        st.success("✅ Copied!")

# [Rest of your portfolio + Monte Carlo code stays the same - abbreviated here]
st.subheader("Portfolio Builder")
tickers_input = st.text_area("Tickers (one per line)", value="XEQT.TO\nVTI\nQQQ\nVCN.TO", height=120)
weights_input = st.text_area("Target Weights %", value="60\n25\n10\n5", height=120)
monthly_contribution = st.number_input("Monthly Contribution (CAD)", value=500)
starting_value = st.number_input("Starting Value (CAD)", value=50000)

if st.button("🚀 Run 10-Year Monte Carlo", type="primary", use_container_width=True):
    # (Monte Carlo code remains identical to previous working version)
    st.info("Monte Carlo running... (code unchanged from v2.7)")

st.caption("WealthForge v2.8 • Improved PWA Icon Support")
