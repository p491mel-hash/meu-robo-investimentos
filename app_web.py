import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# Importa as configurações
from config import ALPACA_CONFIGURADA, GEMINI_CONFIGURADA

# Importa as abas (vamos criar as outras depois)
from aba_resumo import render_resumo

st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")

st.sidebar.title("🌎 Super Robô")
st.sidebar.info("Status das Conexões:")
if ALPACA_CONFIGURADA:
    st.sidebar.success("✅ Alpaca Configurada")
else:
    st.sidebar.warning("⚠️ Alpaca não configurada")

if GEMINI_CONFIGURADA:
    st.sidebar.success("✅ Gemini Configurado")
else:
    st.sidebar.warning("⚠️ Gemini não configurado")

# --- CRIAÇÃO DAS ABAS ---
# Por enquanto, só temos a aba de resumo. As outras virão depois.
aba_resumo = st.tabs(["🧠 Resumo das IAs"])

# --- CONTEÚDO DAS ABAS ---
with aba_resumo[0]:
    render_resumo()

# (As outras abas serão adicionadas aqui no futuro)
