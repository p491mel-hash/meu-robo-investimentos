import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")

st.title("🌎 Super Robô de Day Trade - Global")
st.markdown("Monitoramento de Força (BOP) em Ações, FIIs, Commodities e Índices Internacionais.")

# --- BARRA LATERAL (Configurações) ---
st.sidebar.header("Configurações")
intervalo = st.sidebar.slider("Atualizar a cada (segundos):", 10, 60, 15)
stop_loss_pct = st.sidebar.number_input("Stop Loss (%):", min_value=0.1, max_value=5.0, value=2.0, step=0.1) / 100

# --- FUNÇÃO DE BUSCA (A mesma de antes) ---
def buscar_dados(ativo):
    try:
        url = f"https://brapi.dev/api/quote/{ativo}?range=1d&interval=5m"
        resposta = requests.get(url, timeout=5)
        dados = resposta.json()
        if dados.get('results'):
            info = dados['results'][0]
            preco = info.get('regularMarketPrice', 0)
            variacao = info.get('regularMarketChangePercent', 0)
            abertura = info.get('regularMarketOpen', preco)
            maxima = info.get('regularMarketDayHigh', preco)
            minima = info.get('regularMarketDayLow', preco)
            
            if maxima == minima:
                maxima += 0.01
                minima -= 0.01
                
            bop = (preco - abertura) / (maxima - minima)
            forca_compra = min(100, max(0, (bop + 1) * 50))
            forca_venda = 100 - forca_compra
            return preco, variacao, forca_compra, forca_venda
    except:
        pass
    return None, 0, 50, 50

# --- FUNÇÃO PARA DESENHAR O CARD DO ATIVO ---
def mostrar_ativo(ativo, coluna):
    preco, var, f_compra, f_venda = buscar_dados(ativo)
    
    with coluna:
        st.subheader(ativo)
        if preco is not None:
            st.metric(label="Preço", value=f"R$ {preco:.2f}", delta=f"{var:+.2f}%")
            
            st.write("🟦 Força de Compra:")
            st.progress(min(int(f_compra), 100))
            st.caption(f"{f_compra:.0f}%")
            
            st.write("🟥 Força de Venda:")
            st.progress(min(int(f_venda), 100))
            st.caption(f"{f_venda:.0f}%")
            
            if f_compra > 65 and var > 0.3:
                st.success(">>> COMPRA! <<<")
                preco_stop = preco * (1 - stop_loss_pct)
                st.warning(f"🛑 Stop: R$ {preco_stop:.2f}")
            elif f_venda > 65 and var < -0.3:
                st.error(">>> VENDA! <<<")
            else:
                st.info("Aguardar")
        else:
            st.error("Erro ao buscar (Limite da API)")

# --- CRIAÇÃO DAS ABAS ---
aba_acoes, aba_fiis, aba_commodities, aba_internacional = st.tabs([
    "📈 Ações B3", "🏢 FIIs Nacionais", "🛢️ Commodities", "🌍 Internacional"
])

# 1. Aba de Ações
with aba_acoes:
    acoes = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3']
    colunas = st.columns(len(acoes))
    for i, ativo in enumerate(acoes):
        mostrar_ativo(ativo, colunas[i])

# 2. Aba de FIIs Nacionais
with aba_fiis:
    fiis = ['HGLG11', 'KNRI11', 'MXRF11', 'XPML11', 'VRTA11']
    colunas = st.columns(len(fiis))
    for i, ativo in enumerate(fiis):
        mostrar_ativo(ativo, colunas[i])

# 3. Aba de Commodities (ETFs e BDRs)
with aba_commodities:
    st.info("ETFs e BDRs de Commodities negociados na B3.")
    commodities = ['CMDB11', 'GOLD11', 'BIAU39', 'BSLV39', 'BCOM39', 'BBOI11']
    colunas = st.columns(len(commodities))
    for i, ativo in enumerate(commodities):
        mostrar_ativo(ativo, colunas[i])

# 4. Aba Internacional (Índices e FIIs Globais via BDRs)
with aba_internacional:
    st.info("ETFs Internacionais negociados na B3.")
    internacional = ['IVVB11', 'SPXI11', 'BEWJ39', 'BEWG39', 'ACWX39']
    colunas = st.columns(len(internacional))
    for i, ativo in enumerate(internacional):
        mostrar_ativo(ativo, colunas[i])
