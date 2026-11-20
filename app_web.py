import streamlit as st
from config import ALPACA_CONFIGURADA, GEMINI_CONFIGURADA
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

aba_resumo = st.tabs(["🧠 Resumo das IAs"])

with aba_resumo[0]:
    render_resumo()
