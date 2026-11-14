import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")
st.title("🌎 Super Robô de Day Trade - Global")

# --- BARRA LATERAL ---
st.sidebar.header("Configurações")
stop_loss_pct = st.sidebar.number_input("Stop Loss (%):", min_value=0.1, max_value=5.0, value=2.0, step=0.1) / 100
ativo_grafico = st.sidebar.selectbox("Ativo para o Gráfico de Velas:", ["PETR4", "VALE3", "ITUB4"])

# --- FUNÇÃO DE BUSCA DE DADOS ATUAIS ---
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

with aba_acoes:
    acoes = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3']
    colunas = st.columns(len(acoes))
    for i, ativo in enumerate(acoes):
        mostrar_ativo(ativo, colunas[i])

with aba_fiis:
    fiis = ['HGLG11', 'KNRI11', 'MXRF11', 'XPML11', 'VRTA11']
    colunas = st.columns(len(fiis))
    for i, ativo in enumerate(fiis):
        mostrar_ativo(ativo, colunas[i])

with aba_commodities:
    st.info("ETFs e BDRs de Commodities negociados na B3.")
    commodities = ['CMDB11', 'GOLD11', 'BIAU39', 'BSLV39', 'BCOM39', 'BBOI11']
    colunas = st.columns(len(commodities))
    for i, ativo in enumerate(commodities):
        mostrar_ativo(ativo, colunas[i])

with aba_internacional:
    st.info("ETFs Internacionais negociados na B3.")
    internacional = ['IVVB11', 'SPXI11', 'BEWJ39', 'BEWG39', 'ACWX39']
    colunas = st.columns(len(internacional))
    for i, ativo in enumerate(internacional):
        mostrar_ativo(ativo, colunas[i])

# --- GRÁFICO DE VELAS (CANDLESTICK) ---
st.divider()
st.subheader(f"🕯️ Gráfico de Velas: {ativo_grafico}")

# Tenta buscar dados históricos para desenhar as velas
try:
    url_hist = f"https://brapi.dev/api/v2/stocks/historical?symbols={ativo_grafico}&range=1d&interval=5m"
    resp_hist = requests.get(url_hist, timeout=10)
    dados_hist = resp_hist.json()
    
    if dados_hist.get('results') and len(dados_hist['results']) > 0:
        hist_data = dados_hist['results'][0].get('data', {})
        if 'historicalDataPrice' in hist_data:
            candles = hist_data['historicalDataPrice']
            df_candles = pd.DataFrame(candles)
            df_candles['date'] = pd.to_datetime(df_candles['date'], unit='s')
            
            fig = go.Figure(data=[go.Candlestick(
                x=df_candles['date'],
                open=df_candles['open'],
                high=df_candles['high'],
                low=df_candles['low'],
                close=df_candles['close'],
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4d4d'
            )])
            fig.update_layout(
                template='plotly_dark',
                xaxis_rangeslider_visible=False,
                height=500,
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("A API não retornou dados de velas (OHLC) para este ativo. O plano gratuito pode ter limitações. Exibindo gráfico de linha simples.")
            dados_simples = []
            for ativo in ['PETR4', 'VALE3', 'ITUB4']:
                p = buscar_dados(ativo)[0]
                if p:
                    dados_simples.append({'Ativo': ativo, 'Preço': p})
            if dados_simples:
                st.bar_chart(pd.DataFrame(dados_simples).set_index('Ativo'))
    else:
        st.warning("Não foi possível carregar o histórico. Verifique se o ticker está correto ou se a API está disponível.")
except Exception as e:
    st.error(f"Erro ao carregar gráfico de velas: {e}")
    st.info("Devido às limitações da API gratuita, o gráfico de velas pode não estar disponível.")
