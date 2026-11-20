import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Importa as configurações do arquivo config.py
from config import ALPACA_CONFIGURADA, GEMINI_CONFIGURADA

st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")

st.title("🌎 Super Robô de Day Trade")
st.write("O robô está sendo reconstruído. Logo as abas de análise aparecerão aqui.")

# Mostra o status das conexões (só para confirmar que o config funcionou)
st.sidebar.title("Status das Conexões")
if ALPACA_CONFIGURADA:
    st.sidebar.success("✅ Alpaca Configurada")
else:
    st.sidebar.warning("⚠️ Alpaca não configurada")

if GEMINI_CONFIGURADA:
    st.sidebar.success("✅ Gemini Configurado")
else:
    st.sidebar.warning("⚠️ Gemini não configurado")
