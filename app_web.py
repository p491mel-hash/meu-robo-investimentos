import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import time
import numpy as np

# Tenta importar a Alpaca
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    ALPACA_DISPONIVEL = True
except ImportError:
    ALPACA_DISPONIVEL = False

st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")

# --- AUTO-REFRESH ---
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if time.time() - st.session_state.last_update > 60: # Atualiza a cada 60s no swing
    st.session_state.last_update = time.time()
    st.rerun()

# --- BARRA LATERAL (ESQUERDA) ---
st.sidebar.title("🌎 Super Robô")

# Configurações
st.sidebar.header("Configurações")
ativo_grafico = st.sidebar.selectbox("Ativo Principal:", ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BOVA11.SA", "USDB11.SA"])
timeframe = st.sidebar.selectbox("Tempo Gráfico:", ["1d", "1wk"]) # Swing usa Diário/Semanal
stop_loss_pct = st.sidebar.number_input("Stop Loss (%):", min_value=0.5, max_value=10.0, value=3.0, step=0.5) / 100

st.sidebar.divider()

# Cotações Rápidas
st.sidebar.subheader("📈 Cotações Rápidas")
acoes_lista = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3']

def buscar_dados(ativo):
    ticker_brapi = ativo.replace(".SA", "")
    try:
        url = f"https://brapi.dev/api/quote/{ticker_brapi}?range=1d&interval=1d"
        resposta = requests.get(url, timeout=5)
        dados = resposta.json()
        if dados.get('results'):
            info = dados['results'][0]
            preco = info.get('regularMarketPrice', 0)
            variacao = info.get('regularMarketChangePercent', 0)
            return preco, variacao
    except:
        pass
    return None, 0

for ativo_nome in acoes_lista:
    preco, var = buscar_dados(ativo_nome)
    if preco:
        st.sidebar.metric(ativo_nome, f"R$ {preco:.2f}", f"{var:+.2f}%")
    else:
        st.sidebar.metric(ativo_nome, "Offline", "")

st.sidebar.divider()

# Alerta Sonoro
st.sidebar.subheader("🔊 Alerta Sonoro")
som_ativo = st.sidebar.checkbox("Ativar som nos sinais", value=False)

st.sidebar.divider()

# Alpaca (Paper Trading)
st.sidebar.subheader("🤖 Alpaca (Paper Trading)")
try:
    alpaca_key = st.secrets["ALPACA_API_KEY"]
    alpaca_secret = st.secrets["ALPACA_SECRET_KEY"]
    alpaca_configurada = True
except:
    alpaca_configurada = False

if alpaca_configurada and ALPACA_DISPONIVEL:
    st.sidebar.success("✅ Alpaca configurada!")
    trade_client = TradingClient(alpaca_key, alpaca_secret, paper=True)
    try:
        account = trade_client.get_account()
        st.sidebar.metric("Saldo Paper", f"$ {float(account.cash):,.2f}")
    except:
        st.sidebar.warning("Não foi possível conectar à Alpaca.")
else:
    st.sidebar.info("Configure as chaves da Alpaca nos Secrets.")
    trade_client = None

# --- CRIAÇÃO DAS ABAS ---
aba_daytrade, aba_swing = st.tabs(["📊 Day Trade (Curto Prazo)", "📈 Swing Trade (Médio Prazo)"])

# --- ABA DAY TRADE (A que você já tinha) ---
with aba_daytrade:
    st.header(f"🐊 Análise de Fluxo: {ativo_grafico.replace('.SA', '')} (1m)")
    # (Aqui entra o código do gráfico de 1m que você já tinha, mas para não ficar gigante, 
    # vou colocar um placeholder. Se quiser o day trade de volta, é só me pedir)
    st.info("Mude para a aba 'Swing Trade' para ver a nova estratégia.")
    # Para manter o código limpo, a análise de 1m fica na outra aba.

# --- ABA SWING TRADE (A NOVA ESTRATÉGIA) ---
with aba_swing:
    st.header(f"📈 Estratégia Swing Trade: {ativo_grafico.replace('.SA', '')}")
    
    try:
        # Busca dados DIÁRIOS para swing
        df = yf.download(ativo_grafico, period="1y", interval="1d", progress=False)
        
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.reset_index()
            df['date'] = pd.to_datetime(df['Date'])
            
            # --- INDICADORES DE SWING ---
            # Médias Móveis Exponenciais (EMA 50 e 200) - Clássicas para Swing [citation:1][citation:4]
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
            
            # RSI (14) para medir força
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # --- LÓGICA DE SINAL SWING ---
            ultimo = df.iloc[-1]
            penultimo = df.iloc[-2]
            
            # CONDIÇÕES DE COMPRA (Tendência de Alta + RSI Saudável)
            # Preço acima da EMA 200 (Tendência principal de alta) [citation:4]
            cond_tendencia_alta = ultimo['Close'] > ultimo['EMA_200']
            # EMA 50 acima da EMA 200 (Golden Cross)
            cond_ema_alinhada = ultimo['EMA_50'] > ultimo['EMA_200']
            # RSI entre 40 e 70 (Não sobrecomprado, mas com força)
            cond_rsi_compra = 40 < ultimo['RSI'] < 70
            
            # CONDIÇÕES DE VENDA (Topo / Exaustão)
            # RSI acima de 70 (Sobrecomprado - Hora de realizar lucro) [citation:1]
            cond_rsi_venda = ultimo['RSI'] > 70
            # Preço perdeu a EMA 50 (Perda de força de curto prazo)
            cond_perdeu_ema50 = ultimo['Close'] < ultimo['EMA_50']
            
            # --- EXIBE O VEREDITO ---
            if cond_tendencia_alta and cond_ema_alinhada and cond_rsi_compra:
                st.success("### 🟢 SINAL DE COMPRA (SWING)! A tendência é de alta e o RSI está saudável.")
                st.write(f"**Preço Atual:** R$ {ultimo['Close']:.2f}")
                st.write(f"**Alvo (Take Profit):** R$ {ultimo['Close'] * 1.10:.2f} (+10%) ou aguardar RSI > 70")
                st.write(f"**Stop Loss Sugerido:** R$ {ultimo['Close'] * (1 - stop_loss_pct):.2f}")
                
            elif cond_rsi_venda:
                st.error("### 🔴 SINAL DE VENDA (SWING)! O preço está sobrecomprado (RSI > 70). Realize o lucro.")
                st.write(f"**Preço Atual:** R$ {ultimo['Close']:.2f}")
                st.write(f"**RSI:** {ultimo['RSI']:.1f}")
                
            elif cond_perdeu_ema50 and ultimo['Close'] < ultimo['EMA_200']:
                st.error("### 🔴 SINAL DE VENDA (SWING)! O preço perdeu a força e a tendência virou para baixa.")
                st.write(f"**Preço Atual:** R$ {ultimo['Close']:.2f}")
                
            else:
                st.warning("### ⏳ AGUARDAR. A tendência ainda não está clara ou o preço está no meio do caminho.")
                st.write(f"**RSI:** {ultimo['RSI']:.1f}")
                st.write(f"**Preço vs EMA 200:** {'Acima' if ultimo['Close'] > ultimo['EMA_200'] else 'Abaixo'}")
            
            # --- DETALHES ---
            with st.expander("Ver detalhes dos indicadores de Swing"):
                st.write(f"**EMA 50:** R$ {ultimo['EMA_50']:.2f}")
                st.write(f"**EMA 200:** R$ {ultimo['EMA_200']:.2f}")
                st.write(f"**RSI (14):** {ultimo['RSI']:.1f}")
                st.write(f"**Tendência Principal:** {'ALTA' if cond_tendencia_alta else 'BAIXA'}")

            # --- GRÁFICO DE SWING ---
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3], subplot_titles=("Preço + EMA 50/200", "RSI"))
            
            fig.add_trace(go.Candlestick(x=df['date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Preço', increasing_line_color='#00ff88', decreasing_line_color='#ff4d4d'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['EMA_50'], line=dict(color='#ffcc00', width=1.5), name='EMA 50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['EMA_200'], line=dict(color='#ff4d4d', width=1.5), name='EMA 200'), row=1, col=1)
            
            # Linha de Stop Loss no gráfico (baseada no último preço)
            linha_stop = ultimo['Close'] * (1 - stop_loss_pct)
            fig.add_hline(y=linha_stop, line_dash="dash", line_color="#ff4d4d", annotation_text=f"Stop: R$ {linha_stop:.2f}", annotation_position="top right", row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df['date'], y=df['RSI'], line=dict(color='#4da6ff', width=1.5), name='RSI'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig.update_layout(template='plotly_dark', xaxis_rangeslider_visible=False, height=800, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            fig.update_yaxes(title_text="Preço", row=1, col=1, side="right")
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1, side="right")
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Yahoo Finance não retornou dados históricos.")
    except Exception as e:
        st.error(f"Erro ao carregar gráfico: {e}")
