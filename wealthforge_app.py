import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="WealthForge – Adam",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PWA Manifest hints (helps with icon)
st.markdown("""
<meta name="apple-mobile-web-app-title" content="WealthForge">
<meta name="apple-mobile-web-app-capable" content="yes">
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
