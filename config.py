import streamlit as st

# Configurações da Alpaca
try:
    ALPACA_API_KEY = st.secrets["ALPACA_API_KEY"]
    ALPACA_SECRET_KEY = st.secrets["ALPACA_SECRET_KEY"]
    ALPACA_CONFIGURADA = True
except:
    ALPACA_CONFIGURADA = False

# Configurações do Gemini
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    GEMINI_CONFIGURADA = True
except:
    GEMINI_CONFIGURADA = False
