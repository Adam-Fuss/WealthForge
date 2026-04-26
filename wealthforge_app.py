import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="WealthForge • Adam", layout="wide", page_icon="📈")
st.title("📈 WealthForge v2.1")
st.markdown("**Adam’s Personal AI Wealth Engine** — Live Portfolio • Monte Carlo Predictions • Calgary, AB")

with st.sidebar:
    st.header("WealthForge Agent")
    st.caption("Connected to Grok • SuperGrok")
    if st.button("Ask WealthForge (Deep Analysis)"):
        st.code("WealthForge, run full backtest + Monte Carlo on my portfolio: [paste details here]", language="text")
        st.success("✅ Prompt copied!")
    st.divider()
    st.info("**Educational tool only** — Not financial advice.")

# Portfolio Input
st.subheader("Portfolio Builder")
st.write("Add tickers and target weights (they will be normalized)")

tickers_input = st.text_area("Tickers (one per line, e.g. XEQT.TO)", 
                             value="XEQT.TO\nVTI\nQQQ\nVCN.TO", height=150)
weights_input = st.text_area("Target Weights % (one per line, matching tickers)", 
                             value="60\n25\n10\n5", height=150)

monthly_contribution = st.number_input("Monthly Contribution (CAD)", value=500, min_value=0, step=100)

if st.button("Run Full Portfolio Monte Carlo", type="primary"):
    with st.spinner("Downloading data + running 5,000 simulations..."):
        tickers = [t.strip().upper() for t in tickers_input.splitlines() if t.strip()]
        try:
            weights = [float(w.strip()) for w in weights_input.splitlines() if w.strip()]
        except:
            st.error("Weights must be numbers")
            st.stop()

        if len(tickers) != len(weights):
            st.error("Number of tickers and weights must match")
            st.stop()

        # Fetch data
        data = yf.download(tickers, period="3y", interval="1d", progress=False)['Close']
        returns = data.pct_change().dropna()
        
        # Portfolio stats
        port_returns = returns.dot(np.array(weights) / sum(weights))
        mu = port_returns.mean() * 252
        sigma = port_returns.std() * np.sqrt(252)
        current_value = 50000  # Default starting value - you can make this editable later

        st.success(f"Portfolio: {len(tickers)} assets | Expected Return: {mu*100:.1f}% | Volatility: {sigma*100:.1f}%")

        # Monte Carlo
        days = 252 * 10  # 10 years
        sims = 5000
        dt = 1/252
        paths = np.zeros((days, sims))
        paths[0] = current_value

        for t in range(1, days):
            Z = np.random.standard_normal(sims)
            paths[t] = paths[t-1] * np.exp((mu - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*Z)

        # Add contributions
        monthly_steps = int(days / 12)
        for i in range(1, days):
            if i % monthly_steps == 0:
                paths[i:] += monthly_contribution

        # Plot
        fig = go.Figure()
        dates = pd.date_range(start=datetime.today(), periods=days, freq='B')
        
        # Fan effect
        for i in range(0, sims, 40):
            fig.add_trace(go.Scatter(x=dates, y=paths[:,i], mode='lines', 
                                   line=dict(color='rgba(0,120,220,0.07)'), showlegend=False))
        
        p10 = np.percentile(paths, 10, axis=1)
        p50 = np.median(paths, axis=1)
        p90 = np.percentile(paths, 90, axis=1)
        
        fig.add_trace(go.Scatter(x=dates, y=p10, mode='lines', line=dict(color='red'), name='10th %ile (Bad)'))
        fig.add_trace(go.Scatter(x=dates, y=p90, fill='tonexty', mode='lines', line=dict(color='lime'), 
                               name='90th %ile (Great)', fillcolor='rgba(0,255,100,0.25)'))
        fig.add_trace(go.Scatter(x=dates, y=p50, mode='lines', line=dict(color='gold', width=4), name='Median'))
        
        fig.update_layout(title="10-Year Portfolio Monte Carlo (5,000 paths)", 
                         xaxis_title="Date", yaxis_title="Projected Portfolio Value ($)",
                         height=700, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        final_median = p50[-1]
        prob_million = (paths[-1] > 1_000_000).mean() * 100
        st.metric("Median 10-Year Value", f"${final_median:,.0f}")
        st.success(f"**Probability of reaching $1M**: {prob_million:.1f}%")

st.caption("WealthForge v2.1 • Built live for Adam • Tell me what to add next")
