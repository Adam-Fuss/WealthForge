import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime

# ================== CUSTOM APP CONFIG FOR PHONE ==================

    menu_items={
        'Get Help': 'https://chat.x.ai',
        'Report a bug': None,
        'About': 'WealthForge v2.2 • Built for Adam in Calgary'
    }
)

st.title("📈 WealthForge")
st.markdown("**Adam’s Personal Wealth Engine** — Monte Carlo • Live Predictions • Calgary, AB")

# Sidebar with install instructions
with st.sidebar:
    st.header("📱 Install on Phone")
    st.markdown("""
    **How to add WealthForge as an App:**
    1. Open this page in **Chrome or Safari**
    2. Tap the **Share** button
    3. Choose **"Add to Home Screen"** (or "Install App")
    4. Tap **Add**
    
    You’ll get a real app icon (📈) on your home screen!
    """)
    
    if st.button("Ask WealthForge (Deep Analysis)"):
        st.code("WealthForge, run full backtest + Monte Carlo on my portfolio: [paste here]", language="text")
        st.success("✅ Prompt copied!")
    
    st.divider()
    st.info("**Educational simulations only** — Not financial advice.")

# Rest of your app (Portfolio Builder + Monte Carlo)
st.subheader("Portfolio Builder")
st.write("Add tickers and weights below")

tickers_input = st.text_area("Tickers (one per line)", 
                             value="XEQT.TO\nVTI\nQQQ\nVCN.TO", height=120)
weights_input = st.text_area("Target Weights % (one per line)", 
                             value="60\n25\n10\n5", height=120)

monthly_contribution = st.number_input("Monthly Contribution (CAD)", value=500, min_value=0, step=100)

if st.button("🚀 Run 10-Year Portfolio Monte Carlo", type="primary", use_container_width=True):
    with st.spinner("Running 5,000 simulations with live data..."):
        # (Same Monte Carlo logic as before - kept for brevity)
        tickers = [t.strip().upper() for t in tickers_input.splitlines() if t.strip()]
        try:
            weights = [float(w.strip()) for w in weights_input.splitlines() if w.strip()]
        except:
            st.error("Weights must be numbers.")
            st.stop()

        if len(tickers) != len(weights):
            st.error("Tickers and weights count must match.")
            st.stop()

        data = yf.download(tickers, period="3y", interval="1d", progress=False)['Close']
        returns = data.pct_change().dropna()
        port_returns = returns.dot(np.array(weights) / sum(weights))
        mu = port_returns.mean() * 252
        sigma = port_returns.std() * np.sqrt(252)

        days = 252 * 10
        sims = 5000
        dt = 1/252
        paths = np.zeros((days, sims))
        paths[0] = 50000  # starting value

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
        
        fig.update_layout(title="10-Year WealthForge Monte Carlo Projection (5,000 paths)", 
                         xaxis_title="Date", yaxis_title="Portfolio Value ($CAD)",
                         height=650, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        final_median = p50[-1]
        prob_million = (paths[-1] > 1_000_000).mean() * 100
        st.metric("Projected Median Value in 10 Years", f"${final_median:,.0f}")
        st.success(f"**Chance of reaching $1,000,000**: {prob_million:.1f}%")

st.caption("WealthForge v2.2 • Optimized for Phone • Updates via this chat")
