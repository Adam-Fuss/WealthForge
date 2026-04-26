import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import datetime
import json
import os

st.set_page_config(page_title="WealthForge – my liege", page_icon="📈", layout="wide")

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

with st.sidebar:
    st.title("WealthForge")
    st.caption("v3.2.5 - At your service, my liege")
    
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
    st.title("Welcome to WealthForge v3.2.5")
    st.stop()

st.title(st.session_state.current_portfolio)

st.caption("WealthForge v3.2.5 - Clean version")