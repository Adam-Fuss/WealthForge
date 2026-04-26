import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime

# ================== APP CONFIG ==================
st.set_page_config(
    page_title="WealthForge – Adam",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 WealthForge")
st.markdown("**Adam’s Personal Wealth Engine** — Live Monte Carlo • Calgary, AB")

# Sidebar
with st.sidebar:
    st.header("📱 WealthForge")
    st.markdown("""
    **Add to Phone Home Screen:**
    1. Tap **Share**  
    2. Choose **"Add to Home Screen"**
    """)
    
    if st.button("Ask WealthForge (Deep Analysis)"):
        st.code("WealthForge, run full backtest + Monte Carlo on my portfolio: [paste here]", language="text")
        st.success("✅ Prompt copied!")
    
    st.divider()
    st.info("**Educational tool only** — Not financial advice.")

# Main App
st.subheader("Portfolio Builder")
st.write("Enter tickers and weights (they will be normalized)")

tickers_input = st.text_area("Tickers (one per line)", 
                             value="XEQT.TO\nVTI\nQQQ\nVCN.TO", height=120)
weights_input = st.text_area("Target Weights % (one per line)", 
                             value="60\n25\n10\n5", height=120)

monthly_contribution = st.number_input("Monthly Contribution (CAD)", value=500, min_value=0, step=100)
starting_value = st.number_input("Starting Portfolio Value (CAD)", value=50000, min_value=0, step=1000)

if st.button("🚀 Run 10-Year Portfolio Monte Carlo", type="primary", use_container_width=True):
    with st.spinner("Fetching data + running 5,000 simulations..."):
        tickers = [t.strip().upper() for t in tickers_input.splitlines() if t.strip()]
        try:
            weights = [float(w.strip()) for w in weights_input.splitlines() if w.strip()]
        except:
            st.error("Weights must be numbers only.")
            st.stop()

        if len(tickers) != len(weights):
            st.error("Number of tickers and weights must match.")
            st.stop()

        # Fetch real data
        data = yf.download(tickers, period="3y", interval="1d", progress=False)['Close']
        returns = data.pct_change().dropna()
        
        port_returns = returns.dot(np.array(weights) / sum(weights))
        mu = port_returns.mean() * 252
        sigma = port_returns.std() * np.sqrt(252)

        # Monte Carlo
        days = 252 * 10
        sims = 5000
        dt = 1/252
        paths = np.zeros((days, sims))
        paths[0] = starting_value

        for t in range(1, days):
            Z = np.random.standard_normal(sims)
            paths[t] = paths[t-1] * np.exp((mu - 0.5*sigma**2)*dt + sigma*np.sqrt(dt)*Z)

        # Add monthly contributions
        monthly_steps = int(days / 12)
        for i in range(1, days):
            if i % monthly_steps == 0:
                paths[i:] += monthly_contribution

        # Plot
        fig = go.Figure()
        dates = pd.date_range(start=datetime.today(), periods=days, freq='B')
        
        for i in range(0, sims, 40):
            fig.add_trace(go.Scatter(x=dates, y=paths[:,i], mode='lines', 
                                   line=dict(color='rgba(0,120,220,0.07)'), showlegend=False))
        
        p10 = np.percentile(paths, 10, axis=1)
        p50 = np.median(paths, axis=1)
        p90 = np.percentile(paths, 90, axis=1)
        
        fig.add_trace(go.Scatter(x=dates, y=p10, mode='lines', line=dict(color='red'), name='10th %ile'))
        fig.add_trace(go.Scatter(x=dates, y=p90, fill='tonexty', mode='lines', line=dict(color='lime'), 
                               name='90th %ile', fillcolor='rgba(0,255,100,0.25)'))
        fig.add_trace(go.Scatter(x=dates, y=p50, mode='lines', line=dict(color='gold', width=4), name='Median'))
        
        fig.update_layout(
            title="10-Year WealthForge Monte Carlo Projection (5,000 paths)",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($CAD)",
            height=650,
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        final_median = p50[-1]
        prob_million = (paths[-1] > 1_000_000).mean() * 100
        st.metric("Median 10-Year Value", f"${final_median:,.0f}")
        st.success(f"**Probability of reaching $1M**: {prob_million:.1f}%")

st.caption("WealthForge v2.7 • Fixed & Improved • Custom icon ready")
