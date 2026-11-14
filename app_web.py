import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")
st.title("🌎 Super Robô de Day Trade - Global")

# --- AUTO-REFRESH ---
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

# --- GRÁFICO COM JACARÉ E BARRAS DE FORÇA ---
st.divider()
st.subheader(f"🐊 Gráfico Integrado: {ativo_grafico} ({timeframe})")

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
            
            # --- CÁLCULO DO JACARÉ ---
            df['mandibula'] = df['close'].ewm(span=13, adjust=False).mean().shift(8)
            df['dentes'] = df['close'].ewm(span=8, adjust=False).mean().shift(5)
            df['labios'] = df['close'].ewm(span=5, adjust=False).mean().shift(3)
            
            # --- CÁLCULO DA FORÇA (BOP) PARA CADA CANDLE ---
            # Previne divisão por zero
            df['range'] = df['high'] - df['low']
            df['range'] = df['range'].replace(0, 0.01) 
            
            # BOP = (Fechamento - Abertura) / (Máxima - Mínima)
            df['bop'] = (df['close'] - df['open']) / df['range']
            
            # Converte o BOP para uma escala de 0 a 100 (Força de Compra)
            df['forca_compra'] = (df['bop'] + 1) * 50
            df['forca_compra'] = df['forca_compra'].clip(0, 100)
            
            # Força de venda é o inverso
            df['forca_venda'] = 100 - df['forca_compra']
            
            # Cor da barra de força (Verde se compra > venda, Vermelho se venda > compra)
            cores_forca = ['#4da6ff' if fc >= 50 else '#ff4d4d' for fc in df['forca_compra']]
            
            # Cria a figura com 2 linhas (Gráfico de Velas em cima, Força embaixo)
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.05,
                row_heights=[0.7, 0.3] # 70% para velas, 30% para força
            )
            
            # 1. Adiciona as Velas (Linha 1)
            fig.add_trace(go.Candlestick(
                x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'],
                name='Preço', increasing_line_color='#00ff88', decreasing_line_color='#ff4d4d'
            ), row=1, col=1)
            
            # 2. Adiciona o Jacaré (Linha 1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['mandibula'], line=dict(color='#4da6ff', width=1.5), name='Mandíbula (13)'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['dentes'], line=dict(color='#ff4d4d', width=1.5), name='Dentes (8)'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['labios'], line=dict(color='#00ff88', width=1.5), name='Lábios (5)'), row=1, col=1)
            
            # 3. Adiciona o Stop Loss (Linha 1)
            ultimo_preco = df['close'].iloc[-1]
            linha_stop = ultimo_preco * (1 - stop_loss_pct)
            fig.add_hline(y=linha_stop, line_dash="dash", line_color="red", annotation_text=f"Stop: R$ {linha_stop:.2f}", annotation_position="bottom right", row=1, col=1)
            
            # 4. Adiciona as Barras de Força (Linha 2)
            fig.add_trace(go.Bar(
                x=df['date'], y=df['forca_compra'],
                name='Força de Compra/Venda',
                marker_color=cores_forca,
                hovertemplate='Força: %{y:.1f}%<extra></extra>'
            ), row=2, col=1)
            
            # Linha de referência em 50% (equilíbrio)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
            
            # Configuração do Layout
            fig.update_layout(
                template='plotly_dark',
                xaxis_rangeslider_visible=False,
                height=700,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            # Remove o eixo X duplicado
            fig.update_xaxes(showticklabels=False, row=1, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # --- EXPLICAÇÃO DO JACARÉ ---
            st.markdown("""
            ### 🐊 Como ler o gráfico:
            *   **Em cima:** O Jacaré (Alligator). Boca fechada = mercado de lado. Boca aberta = tendência.
            *   **Embaixo:** A Força de cada candle (BOP).
                *   **Barra Azul:** Fechou mais perto da máxima (compra).
                *   **Barra Vermelha:** Fechou mais perto da mínima (venda).
            """)
            
        else:
            st.warning("A API não retornou dados de velas (OHLC) para este ativo.")
    else:
        st.warning("Não foi possível carregar o histórico.")
except Exception as e:
    st.error(f"Erro ao carregar gráfico: {e}")
