import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import time

st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")
st.title("🌎 Super Robô de Day Trade - Global")

# --- AUTO-REFRESH ---
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if time.time() - st.session_state.last_update > 30:
    st.session_state.last_update = time.time()
    st.rerun()

# --- BARRA LATERAL ---
st.sidebar.header("Configurações")
stop_loss_pct = st.sidebar.number_input("Stop Loss (%):", min_value=0.1, max_value=5.0, value=2.0, step=0.1) / 100
ativo_grafico = st.sidebar.selectbox("Ativo para o Gráfico:", ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BOVA11.SA", "USDB11.SA"])
timeframe = st.sidebar.selectbox("Tempo Gráfico (Timeframe):", ["1m", "5m", "15m", "1h"])

# --- FUNÇÕES DE BUSCA (Brapi) ---
def buscar_dados(ativo):
    ticker_brapi = ativo.replace(".SA", "")
    try:
        url = f"https://brapi.dev/api/quote/{ticker_brapi}?range=1d&interval={timeframe}"
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
        st.subheader(ativo.replace(".SA", ""))
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
aba_acoes, aba_fiis, aba_commodities, aba_internacional, aba_indices = st.tabs([
    "📈 Ações B3", "🏢 FIIs", "🛢️ Commodities", "🌍 Internacional", "💵 Dólar e Índice"
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

with aba_indices:
    st.info("Dólar e Ibovespa via ETFs (BOVA11 e USDB11).")
    indices = ['BOVA11', 'USDB11', 'BOVV11', 'DOLA11']
    colunas = st.columns(len(indices))
    for i, ativo in enumerate(indices):
        mostrar_ativo(ativo, colunas[i])

# --- GRÁFICO E SINAL CLARO ---
st.divider()
st.subheader(f"🐊 Análise de Fluxo e SINAL: {ativo_grafico} ({timeframe})")

try:
    df = yf.download(ativo_grafico, period="1d", interval=timeframe, progress=False)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        coluna_data = 'Datetime' if 'Datetime' in df.columns else 'Date'
        df['date'] = pd.to_datetime(df[coluna_data])
        df = df[(df['date'].dt.hour >= 10) & (df['date'].dt.hour <= 17)]
        
        if len(df) > 5:
            # --- INDICADORES ---
            df['mandibula'] = df['Close'].ewm(span=13, adjust=False).mean().shift(8)
            df['dentes'] = df['Close'].ewm(span=8, adjust=False).mean().shift(5)
            df['labios'] = df['Close'].ewm(span=5, adjust=False).mean().shift(3)
            
            df['range'] = df['High'] - df['Low']
            df['range'] = df['range'].replace(0, 0.01) 
            df['bop'] = (df['Close'] - df['Open']) / df['range']
            df['forca_compra'] = (df['bop'] + 1) * 50
            df['forca_compra'] = df['forca_compra'].clip(0, 100)
            cores_forca = ['#4da6ff' if fc >= 50 else '#ff4d4d' for fc in df['forca_compra']]
            
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            exp1 = df['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df['Close'].ewm(span=26, adjust=False).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Sinal'] = df['MACD'].ewm(span=9, adjust=False).mean()
            
            df['MA_Curta'] = df['Close'].rolling(window=9).mean()
            df['MA_Longa'] = df['Close'].rolling(window=21).mean()
            
            # --- LÓGICA DO SINAL CLARO (CONFLUÊNCIA) ---
            ultimo = df.iloc[-1]
            
            # 1. Condições de COMPRA
            cond_giba_compra = ultimo['MA_Curta'] > ultimo['MA_Longa']
            cond_jacare_compra = ultimo['labios'] > ultimo['dentes'] > ultimo['mandibula']
            cond_forca_compra = ultimo['forca_compra'] > 60
            cond_rsi_compra = ultimo['RSI'] < 70 # Não sobrecomprado
            cond_macd_compra = ultimo['MACD'] > ultimo['MACD_Sinal']
            
            # 2. Condições de VENDA
            cond_giba_venda = ultimo['MA_Curta'] < ultimo['MA_Longa']
            cond_jacare_venda = ultimo['labios'] < ultimo['dentes'] < ultimo['mandibula']
            cond_forca_venda = ultimo['forca_compra'] < 40
            cond_rsi_venda = ultimo['RSI'] > 30 # Não sobrevendido
            cond_macd_venda = ultimo['MACD'] < ultimo['MACD_Sinal']
            
            # --- EXIBE O VEREDITO ---
            if all([cond_giba_compra, cond_jacare_compra, cond_forca_compra, cond_rsi_compra, cond_macd_compra]):
                st.success("### 🟢 SINAL DE COMPRA CONFIRMADO! Todos os indicadores estão alinhados.")
            elif all([cond_giba_venda, cond_jacare_venda, cond_forca_venda, cond_rsi_venda, cond_macd_venda]):
                st.error("### 🔴 SINAL DE VENDA CONFIRMADO! Todos os indicadores estão alinhados.")
            else:
                st.warning("### ⏳ AGUARDAR. Os indicadores não estão alinhados. Não entre agora.")
            
            # Explicação do que faltou
            with st.expander("Ver detalhes dos indicadores"):
                st.write(f"**Gibex (Tendência):** {'Alta' if cond_giba_compra else 'Baixa'}")
                st.write(f"**Jacaré:** {'Boca aberta para cima' if cond_jacare_compra else 'Boca aberta para baixo' if cond_jacare_venda else 'Boca fechada/Lateral'}")
                st.write(f"**Força (BOP):** {ultimo['forca_compra']:.1f}%")
                st.write(f"**RSI:** {ultimo['RSI']:.1f}")
                st.write(f"**MACD:** {'Cruzado para cima' if cond_macd_compra else 'Cruzado para baixo'}")

            # --- DESENHA O GRÁFICO ---
            fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.15, 0.15, 0.2])
            
            fig.add_trace(go.Candlestick(x=df['date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Preço', increasing_line_color='#00ff88', decreasing_line_color='#ff4d4d', showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['mandibula'], line=dict(color='#4da6ff', width=1.5), name='Mandíbula'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['dentes'], line=dict(color='#ff4d4d', width=1.5), name='Dentes'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['labios'], line=dict(color='#00ff88', width=1.5), name='Lábios'), row=1, col=1)
            
            ultimo_preco = df['Close'].iloc[-1]
            linha_stop = ultimo_preco * (1 - stop_loss_pct)
            fig.add_hline(y=linha_stop, line_dash="dash", line_color="#ffcc00", annotation_text=f"Stop: R$ {linha_stop:.2f}", annotation_position="top right", row=1, col=1)
            
            fig.add_trace(go.Bar(x=df['date'], y=df['forca_compra'], name='Força', marker_color=cores_forca, showlegend=False), row=2, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
            
            fig.add_trace(go.Scatter(x=df['date'], y=df['RSI'], line=dict(color='#ffcc00', width=1.5), name='RSI'), row=3, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            
            fig.add_trace(go.Scatter(x=df['date'], y=df['MACD'], line=dict(color='#4da6ff', width=1.5), name='MACD'), row=4, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['MACD_Sinal'], line=dict(color='#ff4d4d', width=1.5), name='Sinal'), row=4, col=1)
            cores_hist = ['#00ff88' if val >= 0 else '#ff4d4d' for val in df['MACD_Hist']]
            fig.add_trace(go.Bar(x=df['date'], y=df['MACD_Hist'], name='Histograma', marker_color=cores_hist, opacity=0.6, showlegend=False), row=4, col=1)
            
            fig.update_layout(template='plotly_dark', xaxis_rangeslider_visible=False, height=900, margin=dict(l=20, r=20, t=40, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)))
            fig.update_xaxes(showticklabels=False, row=1, col=1)
            fig.update_xaxes(showticklabels=False, row=2, col=1)
            fig.update_xaxes(showticklabels=False, row=3, col=1)
            fig.update_yaxes(title_text="Preço", row=1, col=1, side="right")
            fig.update_yaxes(title_text="Força", range=[0, 100], row=2, col=1, side="right")
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1, side="right")
            fig.update_yaxes(title_text="MACD", row=4, col=1, side="right")
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Poucos dados para o gráfico hoje. O mercado pode estar fechado.")
    else:
        st.warning("Yahoo Finance não retornou dados para este ativo.")
except Exception as e:
    st.error(f"Erro ao carregar gráfico do Yahoo: {e}")
