import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import time
import numpy as np
from backtesting import Backtest, Strategy

# Importa as configurações
from config import ALPACA_CONFIGURADA, GEMINI_CONFIGURADA

# Importa a aba de resumo
from aba_crew import render_crew

# Tenta importar a Alpaca
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest, StopLossRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
    ALPACA_DISPONIVEL = True
except ImportError:
    ALPACA_DISPONIVEL = False

st.set_page_config(page_title="Super Robô - Global", layout="wide", page_icon="🌎")

# --- AUTO-REFRESH ---
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if time.time() - st.session_state.last_update > 30:
    st.session_state.last_update = time.time()
    st.rerun()

# --- BARRA LATERAL ---
st.sidebar.title("🌎 Super Robô")

lista_ativos = [
    "USDB11.SA", "BOVA11.SA",
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "ABEV3.SA", "WEGE3.SA", "BBAS3.SA", "MGLU3.SA", "B3SA3.SA",
    "HGLG11.SA", "KNRI11.SA", "MXRF11.SA", "XPML11.SA", "VRTA11.SA", "BTLG11.SA", "VISC11.SA", "XPLG11.SA",
    "CMDB11.SA", "GOLD11.SA", "BIAU39.SA", "BSLV39.SA", "BCOM39.SA", "BBOI11.SA", "CORN11.SA",
    "IVVB11.SA", "SPXI11.SA", "BEWJ39.SA", "BEWG39.SA", "ACWX39.SA", "NASD11.SA", "TECK11.SA"
]

st.sidebar.header("Configurações")
ativo_grafico = st.sidebar.selectbox("Ativo Principal:", lista_ativos)
stop_loss_pct = st.sidebar.number_input("Stop Loss (%):", min_value=0.5, max_value=10.0, value=2.0, step=0.5) / 100

st.sidebar.divider()

# --- COTAÇÕES RÁPIDAS ---
st.sidebar.subheader("📈 Cotações Rápidas")
acoes_lista = ['PETR4', 'VALE3', 'ITUB4', 'BBDC4', 'ABEV3', 'WEGE3']

def buscar_dados_yahoo(ativo):
    if not ativo.endswith(".SA") and not ativo.endswith("=X") and not ativo.endswith("=F"):
        ticker = f"{ativo}.SA"
    else:
        ticker = ativo
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        preco = info['lastPrice']
        anterior = info['previousClose']
        if preco and anterior:
            variacao = ((preco - anterior) / anterior) * 100
            return preco, variacao
    except:
        pass
    return None, 0

for ativo_nome in acoes_lista:
    preco, var = buscar_dados_yahoo(ativo_nome)
    if preco:
        st.sidebar.metric(ativo_nome, f"R$ {preco:.2f}", f"{var:+.2f}%")
    else:
        st.sidebar.metric(ativo_nome, "Offline", "")

st.sidebar.divider()

# --- ALERTA SONORO ---
st.sidebar.subheader("🔊 Alerta Sonoro")
som_ativo = st.sidebar.checkbox("Ativar som nos sinais", value=False)

st.sidebar.divider()

# --- ALPACA (Status na Sidebar) ---
st.sidebar.subheader("🤖 Alpaca (Paper Trading)")
if ALPACA_CONFIGURADA and ALPACA_DISPONIVEL:
    st.sidebar.success("✅ Alpaca configurada!")
    try:
        trade_client = TradingClient(st.secrets["ALPACA_API_KEY"], st.secrets["ALPACA_SECRET_KEY"], paper=True)
        account = trade_client.get_account()
        st.sidebar.metric("Saldo Paper", f"$ {float(account.cash):,.2f}")
    except:
        st.sidebar.warning("Erro ao conectar.")
        trade_client = None
else:
    st.sidebar.info("Configure as chaves da Alpaca nos Secrets.")
    trade_client = None

# --- FUNÇÃO PARA OS CARDS ---
def mostrar_card_ativo(ativo, coluna, timeframe="1d"):
    preco, var = buscar_dados_yahoo(ativo)
    with coluna:
        st.subheader(ativo.replace(".SA", ""))
        if preco is not None:
            st.metric(label="Preço", value=f"R$ {preco:.2f}", delta=f"{var:+.2f}%")
            if var > 0:
                f_compra = min(100, 50 + (var * 10))
            else:
                f_compra = max(0, 50 + (var * 10))
            f_venda = 100 - f_compra
            
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <p style="margin: 0; color: #ffffff;">🟦 Força de Compra:</p>
                <div style="width: 100%; background-color: #333; border-radius: 5px; height: 10px;">
                    <div style="width: {f_compra}%; background-color: #4da6ff; height: 10px; border-radius: 5px;"></div>
                </div>
                <p style="margin: 0; font-size: 12px; color: #888;">{f_compra:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <p style="margin: 0; color: #ffffff;">🟥 Força de Venda:</p>
                <div style="width: 100%; background-color: #333; border-radius: 5px; height: 10px;">
                    <div style="width: {f_venda}%; background-color: #ff4d4d; height: 10px; border-radius: 5px;"></div>
                </div>
                <p style="margin: 0; font-size: 12px; color: #888;">{f_venda:.0f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            if f_compra > 65 and var > 0.5:
                st.success(">>> COMPRA! <<<")
                st.warning(f"🛑 Stop: R$ {preco * (1 - stop_loss_pct):.2f}")
            elif f_venda > 65 and var < -0.5:
                st.error(">>> VENDA! <<<")
            else:
                st.info("Aguardar")
        else:
            st.error("Erro ao buscar")

# --- CRIAÇÃO DAS ABAS ---
aba_resumo, aba_crew, aba_daytrade, aba_swing, aba_fiis, aba_commodities, aba_internacional, aba_cripto, aba_corretora, aba_backtest = st.tabs([
    "🧠 Resumo das IAs", "🤝 Time de IAs", "📊 Day Trade", "📈 Swing Trade", "🏢 FIIs", "🛢️ Commodities", "🌍 Internacional", "🪙 Cripto", "🤖 Corretora", "🧪 Backtesting"
])

# --- ABA RESUMO DAS IAS ---
with aba_crew:
    render_crew()

# --- ABA DAY TRADE ---
with aba_daytrade:
    st.header(f"🐊 Análise de Fluxo: {ativo_grafico.replace('.SA', '')} (1m)")
    
    if ALPACA_CONFIGURADA and trade_client:
        auto_day = st.checkbox("🤖 Enviar ordem automática para a Alpaca (Day Trade)", value=False)
    else:
        auto_day = False
        st.info("Configure a Alpaca para ativar a automação.")
    
    try:
        df = yf.download(ativo_grafico, period="1d", interval="1m", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.reset_index()
            coluna_data = 'Datetime' if 'Datetime' in df.columns else 'Date'
            df['date'] = pd.to_datetime(df[coluna_data])
            df = df[(df['date'].dt.hour >= 10) & (df['date'].dt.hour <= 17)]
            
            if len(df) > 5:
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
                df['MACD_Hist'] = df['MACD'] - df['MACD_Sinal']
                df['MA_Curta'] = df['Close'].rolling(window=9).mean()
                df['MA_Longa'] = df['Close'].rolling(window=21).mean()
                
                ultimo = df.iloc[-1]
                cond_giba_compra = ultimo['MA_Curta'] > ultimo['MA_Longa']
                cond_jacare_compra = ultimo['labios'] > ultimo['dentes'] > ultimo['mandibula']
                cond_forca_compra = ultimo['forca_compra'] > 60
                cond_rsi_compra = ultimo['RSI'] < 70
                cond_macd_compra = ultimo['MACD'] > ultimo['MACD_Sinal']
                cond_giba_venda = ultimo['MA_Curta'] < ultimo['MA_Longa']
                cond_jacare_venda = ultimo['labios'] < ultimo['dentes'] < ultimo['mandibula']
                cond_forca_venda = ultimo['forca_compra'] < 40
                cond_rsi_venda = ultimo['RSI'] > 30
                cond_macd_venda = ultimo['MACD'] < ultimo['MACD_Sinal']
                
                sinal = "AGUARDAR"
                if all([cond_giba_compra, cond_jacare_compra, cond_forca_compra, cond_rsi_compra, cond_macd_compra]):
                    sinal = "COMPRA"
                    st.success("### 🟢 SINAL DE COMPRA CONFIRMADO! (Day Trade)")
                elif all([cond_giba_venda, cond_jacare_venda, cond_forca_venda, cond_rsi_venda, cond_macd_venda]):
                    sinal = "VENDA"
                    st.error("### 🔴 SINAL DE VENDA CONFIRMADO! (Day Trade)")
                else:
                    st.warning("### ⏳ AGUARDAR. Indicadores não alinhados (Day Trade).")
                
                if auto_day and sinal in ["COMPRA", "VENDA"]:
                    ticker_alpaca = "SPY"
                    try:
                        if sinal == "COMPRA":
                            ordem = MarketOrderRequest(symbol=ticker_alpaca, qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
                            trade_client.submit_order(ordem)
                            st.info(f"🤖 Ordem de COMPRA (Day Trade) enviada para {ticker_alpaca}")
                        else:
                            ordem = MarketOrderRequest(symbol=ticker_alpaca, qty=1, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
                            trade_client.submit_order(ordem)
                            st.info(f"🤖 Ordem de VENDA (Day Trade) enviada para {ticker_alpaca}")
                    except Exception as e:
                        st.error(f"Erro ao enviar ordem automática: {e}")
                
                if som_ativo and sinal in ["COMPRA", "VENDA"]:
                    sample_rate = 44100
                    t = np.linspace(0, 0.3, int(sample_rate * 0.3), False)
                    som = np.sin(880 * t * 2 * np.pi) * 0.5
                    st.audio(som, sample_rate=sample_rate, format="audio/wav")

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
                fig.update_layout(template='plotly_dark', xaxis_rangeslider_visible=False, height=800, margin=dict(l=20, r=20, t=20, b=20))
                fig.update_xaxes(showticklabels=False, row=1, col=1)
                fig.update_xaxes(showticklabels=False, row=2, col=1)
                fig.update_xaxes(showticklabels=False, row=3, col=1)
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro no Day Trade: {e}")

# --- ABA SWING TRADE ---
with aba_swing:
    st.header(f"📈 Estratégia Swing Trade: {ativo_grafico.replace('.SA', '')}")
    
    if ALPACA_CONFIGURADA and trade_client:
        auto_swing = st.checkbox("🤖 Enviar ordem automática para a Alpaca (Swing)", value=False)
        use_trailing = st.checkbox("📈 Usar Trailing Stop na ordem automática", value=False)
    else:
        auto_swing = False
        use_trailing = False
        st.info("Configure a Alpaca para ativar a automação.")
    
    try:
        df = yf.download(ativo_grafico, period="1y", interval="1d", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.reset_index()
            df['date'] = pd.to_datetime(df['Date'])
            df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
            df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            ultimo = df.iloc[-1]
            cond_tendencia_alta = ultimo['Close'] > ultimo['EMA_200']
            cond_ema_alinhada = ultimo['EMA_50'] > ultimo['EMA_200']
            cond_rsi_compra = 40 < ultimo['RSI'] < 70
            cond_rsi_venda = ultimo['RSI'] > 70
            cond_perdeu_ema50 = ultimo['Close'] < ultimo['EMA_50']
            
            sinal_swing = "AGUARDAR"
            if cond_tendencia_alta and cond_ema_alinhada and cond_rsi_compra:
                sinal_swing = "COMPRA"
                st.success("### 🟢 SINAL DE COMPRA (SWING)! Tendência de alta.")
                st.write(f"**Alvo:** R$ {ultimo['Close'] * 1.10:.2f} (+10%)")
            elif cond_rsi_venda:
                sinal_swing = "VENDA"
                st.error("### 🔴 SINAL DE VENDA (SWING)! Sobrecomprado (RSI > 70). Realize o lucro.")
            elif cond_perdeu_ema50 and ultimo['Close'] < ultimo['EMA_200']:
                sinal_swing = "VENDA"
                st.error("### 🔴 SINAL DE VENDA (SWING)! Tendência virou para baixa.")
            else:
                st.warning("### ⏳ AGUARDAR (SWING).")
            
            if auto_swing and sinal_swing in ["COMPRA", "VENDA"]:
                ticker_alpaca = "SPY"
                try:
                    if sinal_swing == "COMPRA":
                        if use_trailing:
                            ordem = MarketOrderRequest(
                                symbol=ticker_alpaca, qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
                                order_class="oto",
                                stop_loss=StopLossRequest(stop_price=round(ultimo['Close'] * (1 - stop_loss_pct), 2))
                            )
                            trade_client.submit_order(ordem)
                            st.info(f"🤖 Ordem de COMPRA (Swing) enviada para {ticker_alpaca}")
                        else:
                            ordem = MarketOrderRequest(symbol=ticker_alpaca, qty=1, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
                            trade_client.submit_order(ordem)
                            st.info(f"🤖 Ordem de COMPRA (Swing) enviada para {ticker_alpaca}")
                    else:
                        ordem = MarketOrderRequest(symbol=ticker_alpaca, qty=1, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
                        trade_client.submit_order(ordem)
                        st.info(f"🤖 Ordem de VENDA (Swing) enviada para {ticker_alpaca}")
                except Exception as e:
                    st.error(f"Erro ao enviar ordem automática: {e}")
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=df['date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Preço', increasing_line_color='#00ff88', decreasing_line_color='#ff4d4d'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['EMA_50'], line=dict(color='#ffcc00', width=1.5), name='EMA 50'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['EMA_200'], line=dict(color='#ff4d4d', width=1.5), name='EMA 200'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df['date'], y=df['RSI'], line=dict(color='#4da6ff', width=1.5), name='RSI'), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            fig.update_layout(template='plotly_dark', xaxis_rangeslider_visible=False, height=600, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erro no Swing Trade: {e}")

# --- ABA FIIs ---
with aba_fiis:
    st.header("🏢 Fundos Imobiliários")
    fiis = ['HGLG11', 'KNRI11', 'MXRF11', 'XPML11', 'VRTA11', 'BTLG11', 'VISC11', 'XPLG11', 'SNEL11', 'RBRF11', 'KNCR11', 'VGHF11', 'MALL11']
    colunas = st.columns(len(fiis))
    for i, ativo in enumerate(fiis):
        mostrar_card_ativo(ativo, colunas[i])

# --- ABA COMMODITIES ---
with aba_commodities:
    st.header("🛢️ Commodities")
    commodities = ['CMDB11', 'GOLD11', 'BIAU39', 'BSLV39', 'BCOM39', 'BBOI11', 'CORN11']
    colunas = st.columns(len(commodities))
    for i, ativo in enumerate(commodities):
        mostrar_card_ativo(ativo, colunas[i])

# --- ABA INTERNACIONAL ---
with aba_internacional:
    st.header("🌍 Internacional")
    internacional = ['IVVB11', 'SPXI11', 'BEWJ39', 'BEWG39', 'ACWX39', 'NASD11', 'TECK11']
    colunas = st.columns(len(internacional))
    for i, ativo in enumerate(internacional):
        mostrar_card_ativo(ativo, colunas[i])

# --- ABA CRIPTO ---
with aba_cripto:
    st.header("🪙 Criptomoedas (CoinGecko)")
    st.write("Monitoramento de preços das principais criptomoedas via API pública da CoinGecko.")
    
    def buscar_cripto_coingecko(coin_id):
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url, timeout=10)
            data = response.json()
            if coin_id in data:
                preco = data[coin_id].get('usd', 0)
                variacao = data[coin_id].get('usd_24h_change', 0)
                return preco, variacao
        except:
            pass
        return None, None
    
    criptos = {
        "Bitcoin": "bitcoin",
        "Ethereum": "ethereum",
        "Solana": "solana",
        "XRP": "ripple",
        "Cardano": "cardano",
        "Dogecoin": "dogecoin",
        "Chainlink": "chainlink",
        "Polygon": "matic-network",
        "Avalanche": "avalanche-2",
        "Polkadot": "polkadot"
    }
    
    colunas_cripto = st.columns(3)
    for i, (nome, coin_id) in enumerate(criptos.items()):
        preco, var = buscar_cripto_coingecko(coin_id)
        with colunas_cripto[i % 3]:
            st.subheader(nome)
            if preco is not None:
                st.metric(label="Preço", value=f"${preco:,.2f}", delta=f"{var:+.2f}%" if var else None)
            else:
                st.error("Erro ao buscar")
    
    st.divider()
    st.subheader("🔍 MMI Infinity (Monitoramento Separado)")
    st.write("A MMI não está listada na CoinGecko. O pool na QuickSwap tem liquidez extremamente baixa.")
    
    def buscar_mmi_dexscreener():
        try:
            url = "https://api.dexscreener.com/latest/dex/pairs/polygon/0xba2aebf8f68e347d37a5101dd466f81bccc56084"
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                pair = data['pairs'][0]
                preco = float(pair.get('priceUsd', 0))
                liquidez = pair.get('liquidity', {}).get('usd', 0)
                volume = pair.get('volume', {}).get('h24', 0)
                return preco, liquidez, volume
        except:
            pass
        return None, None, None
    
    preco_mmi, liq_mmi, vol_mmi = buscar_mmi_dexscreener()
    if preco_mmi:
        col_mmi1, col_mmi2, col_mmi3 = st.columns(3)
        col_mmi1.metric("Preço MMI", f"${preco_mmi:.8f}")
        col_mmi2.metric("Liquidez", f"${liq_mmi:,.2f}")
        col_mmi3.metric("Volume 24h", f"${vol_mmi:,.2f}")
        if liq_mmi and liq_mmi < 1000:
            st.error("⚠️ LIQUIDEZ CRÍTICA! Pool com menos de $1.000. Risco altíssimo de não conseguir vender.")
    else:
        st.warning("Não foi possível buscar o preço da MMI na DexScreener no momento. O pool pode estar sem indexação.")
    
    st.info("💡 Dica: A MMI Infinity tem liquidez de apenas ~$80. Não é possível operar esse token com segurança. Use este painel apenas para acompanhar o preço.")

# --- ABA CORRETORA ---
with aba_corretora:
    st.header("🤖 Corretora (Paper Trading)")
    st.write("Aqui você pode enviar ordens de compra e venda para a sua conta de simulação da Alpaca.")

    if not ALPACA_CONFIGURADA or not trade_client:
        st.warning("⚠️ A Alpaca não está configurada. Vá em 'Settings > Secrets' no Streamlit Cloud e adicione suas chaves.")
    else:
        try:
            account = trade_client.get_account()
            st.metric("Saldo Disponível (Paper)", f"$ {float(account.cash):,.2f}")
        except:
            st.error("Não foi possível obter o saldo da Alpaca.")

        st.divider()
        st.subheader("📝 Enviar Ordem Manual")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            ativo_ordem = st.selectbox("Ativo (EUA):", ["SPY", "AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "NFLX", "AMD", "INTC", "JPM", "V", "DIS"])
        with col2:
            quantidade = st.number_input("Quantidade:", min_value=1, value=1, step=1)
        with col3:
            st.write("")
            st.write("")
            col_buy, col_sell = st.columns(2)
            with col_buy:
                if st.button("🟢 COMPRAR", use_container_width=True):
                    try:
                        preco_atual = yf.Ticker(ativo_ordem).fast_info['lastPrice']
                        preco_stop = preco_atual * (1 - stop_loss_pct)
                        ordem = MarketOrderRequest(
                            symbol=ativo_ordem, qty=quantidade, side=OrderSide.BUY, time_in_force=TimeInForce.DAY,
                            order_class="bracket", stop_loss=StopLossRequest(stop_price=round(preco_stop, 2))
                        )
                        trade_client.submit_order(ordem)
                        st.success(f"✅ Ordem de COMPRA enviada: {quantidade} x {ativo_ordem} (Stop: ${preco_stop:.2f})")
                    except Exception as e:
                        st.error(f"Erro ao comprar: {e}")
            with col_sell:
                if st.button("🔴 VENDER", use_container_width=True):
                    try:
                        ordem = MarketOrderRequest(symbol=ativo_ordem, qty=quantidade, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
                        trade_client.submit_order(ordem)
                        st.success(f"✅ Ordem de VENDA enviada: {quantidade} x {ativo_ordem}")
                    except Exception as e:
                        st.error(f"Erro ao vender: {e}")

        st.divider()
        st.subheader("📋 Suas Posições Abertas")
        try:
            posicoes = trade_client.get_all_positions()
            if posicoes:
                for pos in posicoes:
                    st.write(f"**{pos.symbol}**: {pos.qty} unidades @ R$ {float(pos.avg_entry_price):.2f} (Lucro: R$ {float(pos.unrealized_pl):.2f})")
            else:
                st.info("Você não tem posições abertas.")
        except Exception as e:
            st.error(f"Erro ao buscar posições: {e}")

        st.divider()
        st.subheader("📜 Histórico de Ordens")
        try:
            request = GetOrdersRequest(status=OrderStatus.ALL, limit=20)
            ordens = trade_client.get_orders(filter=request)
            if ordens:
                dados_ordens = []
                for o in ordens:
                    dados_ordens.append({
                        "Data": str(o.submitted_at).split(".")[0] if o.submitted_at else "",
                        "Ativo": o.symbol,
                        "Lado": str(o.side.value).upper() if o.side else "",
                        "Qtd": float(o.qty) if o.qty else 0,
                        "Preço": float(o.filled_avg_price) if o.filled_avg_price else 0,
                        "Status": str(o.status.value).upper() if o.status else ""
                    })
                df_ordens = pd.DataFrame(dados_ordens)
                st.dataframe(df_ordens, use_container_width=True)
            else:
                st.info("Nenhuma ordem encontrada.")
        except Exception as e:
            st.error(f"Erro ao buscar histórico: {e}")

# --- ABA BACKTESTING ---
with aba_backtest:
    st.header("🧪 Backtesting da Estratégia de Swing Trade")
    st.write("Teste a estratégia com dados históricos para ver como ela teria se saído no passado.")
    
    col1, col2 = st.columns(2)
    with col1:
        ativo_backtest = st.selectbox("Ativo para Backtest:", lista_ativos)
    with col2:
        periodo_backtest = st.selectbox("Período:", ["1y", "2y", "5y"])
    
    if st.button("🚀 Rodar Backtest", use_container_width=True):
        with st.spinner("Baixando dados e rodando o backtest..."):
            try:
                df = yf.download(ativo_backtest, period=periodo_backtest, interval="1d", progress=False)
                if df.empty:
                    st.error("Não foi possível baixar os dados.")
                else:
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    df_bt = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
                    df_bt.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    df_bt.index = pd.to_datetime(df_bt.index)
                    
                    class SwingStrategy(Strategy):
                        def init(self):
                            self.ema50 = self.I(lambda x: pd.Series(x).ewm(span=50, adjust=False).mean(), self.data.Close)
                            self.ema200 = self.I(lambda x: pd.Series(x).ewm(span=200, adjust=False).mean(), self.data.Close)
                            self.rsi = self.I(self.calc_rsi, self.data.Close)
                        
                        def calc_rsi(self, close):
                            delta = pd.Series(close).diff()
                            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                            rs = gain / loss
                            return 100 - (100 / (1 + rs))
                        
                        def next(self):
                            if len(self.data) < 200:
                                return
                            if (self.data.Close[-1] > self.ema200[-1] and 
                                self.ema50[-1] > self.ema200[-1] and 
                                40 < self.rsi[-1] < 70 and 
                                not self.position):
                                self.buy()
                            elif self.position:
                                if self.rsi[-1] > 70 or self.data.Close[-1] < self.ema50[-1]:
                                    self.position.close()
                    
                    bt = Backtest(df_bt, SwingStrategy, cash=10000, commission=.002, exclusive_orders=True)
                    stats = bt.run()
                    
                    st.subheader("📊 Resultados do Backtest")
                    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
                    with col_res1:
                        st.metric("Retorno Total", f"{stats['Return [%]']:.2f}%")
                    with col_res2:
                        st.metric("Taxa de Acerto", f"{stats['Win Rate [%]']:.2f}%")
                    with col_res3:
                        st.metric("Nº de Trades", f"{stats['# Trades']}")
                    with col_res4:
                        st.metric("Drawdown Máx.", f"{stats['Max. Drawdown [%]']:.2f}%")
                    
                    st.divider()
                    st.subheader("📈 Gráfico da Curva de Capital")
                    equity = stats['_equity_curve']
                    fig_bt = go.Figure()
                    fig_bt.add_trace(go.Scatter(x=equity.index, y=equity['Equity'], name='Capital', line=dict(color='#00ff88', width=2)))
                    fig_bt.update_layout(template='plotly_dark', height=400, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_bt, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Erro no backtest: {e}")
