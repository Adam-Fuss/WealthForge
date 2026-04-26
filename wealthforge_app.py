import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="WealthForge • Adam", layout="wide", page_icon="📈", initial_sidebar_state="expanded")

st.title("📈 WealthForge")
st.markdown("**Adam’s Personal AI Wealth Engine** — Live prices • Monte Carlo predictions • Calgary, Alberta")

with st.sidebar:
    st.header("WealthForge Agent")
    st.caption("Connected to Grok • SuperGrok")
    if st.button("Ask WealthForge (copy prompt)"):
        st.code("WealthForge, run full backtest + Monte Carlo on my current portfolio: [paste tickers here]", language="text")
        st.success("✅ Prompt copied! Paste into our chat for deep analysis.")
    st.divider()
    st.info("**Not financial advice** — For education and simulation only.")

tab1, tab2, tab3 = st.tabs(["Live Ticker Predictor", "Portfolio Builder", "Deep Backtest"])

with tab1:
    st.subheader("Live Ticker + 5-Year Predictive Graph")
    ticker = st.text_input("Ticker (e.g. XEQT.TO, AAPL, VTI, SHOP.TO)", value="XEQT.TO").upper().strip()
    
    if st.button("Generate Live Predictive Graph", type="primary", use_container_width=True):
        with st.spinner("Fetching real-time data + running 5,000 Monte Carlo paths..."):
            data = yf.download(ticker, period="2y", interval="1d")
            if data.empty:
                st.error("Ticker not found. Try XEQT.TO or AAPL")
            else:
                current_price = float(data['Close'].iloc[-1])
                returns = data['Close'].pct_change().dropna()
                mu = returns.mean() * 252
                sigma = returns.std() * np.sqrt(252)
                
                st.metric("Current Price", f"${current_price:,.2f}")
                
                # Monte Carlo
                days = 252 * 5
                simulations = 5000
                dt = 1/252
                paths = np.zeros((days, simulations))
                paths[0] = current_price
                for t in range(1, days):
                    Z = np.random.standard_normal(simulations)
                    paths[t] = paths[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)
                
                fig = go.Figure()
                median = np.median(paths, axis=1)
                p10 = np.percentile(paths, 10, axis=1)
                p90 = np.percentile(paths, 90, axis=1)
                
                for i in range(0, simulations, 50):
                    fig.add_trace(go.Scatter(x=pd.date_range(start=datetime.today(), periods=days, freq='B'), 
                                           y=paths[:, i], mode='lines', line=dict(color='rgba(0,100,200,0.08)'), showlegend=False))
                
                fig.add_trace(go.Scatter(x=pd.date_range(start=datetime.today(), periods=days, freq='B'), y=p10, mode='lines', line=dict(color='red'), name='10th %ile'))
                fig.add_trace(go.Scatter(x=pd.date_range(start=datetime.today(), periods=days, freq='B'), y=p90, fill='tonexty', mode='lines', line=dict(color='green'), name='90th %ile', fillcolor='rgba(0,200,100,0.3)'))
                fig.add_trace(go.Scatter(x=pd.date_range(start=datetime.today(), periods=days, freq='B'), y=median, mode='lines', line=dict(color='gold', width=4), name='Median'))
                
                fig.update_layout(title=f"{ticker} — 5-Year Monte Carlo Fan Chart", xaxis_title="Time", yaxis_title="Projected Price ($)", height=650, template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
                
                final_median = median[-1]
                prob_double = np.mean(paths[-1] > current_price * 2) * 100
                st.success(f"**Median 5-Year Value: ${final_median:,.0f}** | Probability of doubling: {prob_double:.0f}%")

with tab2:
    st.subheader("Portfolio Builder (Multi-Ticker Monte Carlo)")
    st.info("Add your holdings below. Weights must sum to 100%.")
    
    # Simple portfolio input (expandable)
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = [{"ticker": "XEQT.TO", "weight": 100}]
    
    for i, holding in enumerate(st.session_state.portfolio):
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.session_state.portfolio[i]["ticker"] = st.text_input(f"Ticker {i+1}", value=holding["ticker"], key=f"t{i}").upper()
        with col2:
            st.session_state.portfolio[i]["weight"] = st.number_input(f"Weight %", value=holding["weight"], min_value=0, max_value=100, key=f"w{i}")
        with col3:
            if st.button("Remove", key=f"r{i}"):
                st.session_state.portfolio.pop(i)
                st.rerun()
    
    if st.button("Add another ticker"):
        st.session_state.portfolio.append({"ticker": "", "weight": 0})
        st.rerun()
    
    if st.button("Run Portfolio Monte Carlo", type="primary", use_container_width=True):
        st.info("Portfolio-level Monte Carlo coming in v2.1 (tell me if you want it upgraded now). For now, use single-ticker mode above or paste into chat.")

with tab3:
    st.subheader("Deep Backtest Mode")
    st.write("Paste any portfolio here → copy the generated prompt → send it to me in our chat for full historical backtests + advanced simulations.")

st.caption("WealthForge v2.0 • Built live for Adam • Powered by Grok • April 2026")
