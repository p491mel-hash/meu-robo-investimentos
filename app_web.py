import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")
st.title("🌎 Super Robô de Day Trade - Global")

# --- FUNÇÃO DE AUTO-REFRESH (Atualiza a página sozinha) ---
# Isso faz o site recarregar a cada X segundos sem precisar apertar F5
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

tempo_decorrido = time.time() - st.session_state.last_update
if tempo_decorrido > 30:
    st.session_state.last_update = time.time()
    st.rerun()

# --- BARRA LATERAL ---
st.sidebar.header("Configurações")
stop_loss_pct = st.sidebar.number_input("Stop Loss (%):", min_value=0.1, max_value=5.0, value=2.0, step=0.1) / 100
ativo_grafico = st.sidebar.selectbox("Ativo para o Gráfico:", ["PETR4", "VALE3", "ITUB4"])
timeframe = st.sidebar.selectbox("Tempo Gráfico (Timeframe):", ["1m", "5m", "15m", "1h"])

st.sidebar.info(f"⏱️ O site atualiza sozinho a cada 30 segundos.")

# --- FUNÇÕES DE BUSCA ---
def buscar_dados(ativo):
    try:
        url = f"https://brapi.dev/api/quote/{ativo}?range=1d&interval={timeframe}"
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
            st.error("Erro ao buscar")

# --- ABAS ---
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

# --- GRÁFICO PROFISSIONAL (Com Velas, Médias Móveis e Stop Loss) ---
st.divider()
st.subheader(f"🕯️ Gráfico Profissional: {ativo_grafico} ({timeframe})")

try:
    url_hist = f"https://brapi.dev/api/v2/stocks/historical?symbols={ativo_grafico}&range=5d&interval={timeframe}"
    resp_hist = requests.get(url_hist, timeout=10)
    dados_hist = resp_hist.json()
    
    if dados_hist.get('results') and len(dados_hist['results']) > 0:
        hist_data = dados_hist['results'][0].get('data', {})
        if 'historicalDataPrice' in hist_data:
            candles = hist_data['historicalDataPrice']
            df = pd.DataFrame(candles)
            df['date'] = pd.to_datetime(df['date'], unit='s')
            
            # Calcula Médias Móveis
            df['MM9'] = df['close'].rolling(window=9).mean()
            df['MM21'] = df['close'].rolling(window=21).mean()
            
            # Cria a figura com o gráfico de velas
            fig = go.Figure()
            
            # Adiciona as Velas
            fig.add_trace(go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Preço',
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4d4d'
            ))
            
            # Adiciona as Médias Móveis
            fig.add_trace(go.Scatter(x=df['date'], y=df['MM9'], line=dict(color='yellow', width=1.5), name='MM 9'))
            fig.add_trace(go.Scatter(x=df['date'], y=df['MM21'], line=dict(color='orange', width=1.5), name='MM 21'))
            
            # Adiciona a Linha de Stop Loss (baseada no último preço de fechamento)
            ultimo_preco = df['close'].iloc[-1]
            linha_stop = ultimo_preco * (1 - stop_loss_pct)
            fig.add_hline(y=linha_stop, line_dash="dash", line_color="red", annotation_text=f"Stop Loss: R$ {linha_stop:.2f}", annotation_position="bottom right")
            
            fig.update_layout(
                template='plotly_dark',
                xaxis_rangeslider_visible=False,
                height=600,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("A API não retornou dados de velas (OHLC) para este ativo. O plano gratuito pode ter limitações.")
    else:
        st.warning("Não foi possível carregar o histórico. Verifique se o ticker está correto.")
except Exception as e:
    st.error(f"Erro ao carregar gráfico: {e}")
