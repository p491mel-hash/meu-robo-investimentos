import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Configuração da página (tem que ser a primeira coisa)
st.set_page_config(page_title="Robô de Day Trade Web", layout="wide", page_icon="🤖")

st.title("🤖 Super Robô de Day Trade - Versão Web")
st.markdown("Monitoramento de Força (BOP) e Stop Loss em tempo real.")

# --- BARRA LATERAL (Configurações) ---
st.sidebar.header("Configurações")
ativos_input = st.sidebar.text_input("Ativos (separados por vírgula):", "PETR4, VALE3, ITUB4, HGLG11, MXRF11")
intervalo = st.sidebar.slider("Atualizar a cada (segundos):", 10, 60, 15)
stop_loss_pct = st.sidebar.number_input("Stop Loss (%):", min_value=0.1, max_value=5.0, value=2.0, step=0.1) / 100

# Botão para forçar atualização
if st.sidebar.button("🔄 Atualizar Agora"):
    st.rerun()

# --- FUNÇÕES DE DADOS (As mesmas do robô desktop) ---
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

# --- INTERFACE PRINCIPAL ---
ativos = [a.strip().upper() for a in ativos_input.split(",") if a.strip()]

# Cria colunas para exibir os ativos
colunas = st.columns(len(ativos)) if ativos else []

for i, ativo in enumerate(ativos):
    preco, var, f_compra, f_venda = buscar_dados(ativo)
    
    with colunas[i]:
        st.subheader(ativo)
        if preco is not None:
            # Mostra o preço com cor
            cor = "normal" if var == 0 else ("inverse" if var > 0 else "off")
            st.metric(label="Preço", value=f"R$ {preco:.2f}", delta=f"{var:+.2f}%")
            
            # Barras de Força (usando o componente de progresso do Streamlit)
            st.write("🟦 Força de Compra:")
            st.progress(min(int(f_compra), 100))
            st.caption(f"{f_compra:.0f}%")
            
            st.write("🟥 Força de Venda:")
            st.progress(min(int(f_venda), 100))
            st.caption(f"{f_venda:.0f}%")
            
            # Lógica de Sinal
            if f_compra > 65 and var > 0.3:
                st.success(">>> COMPRA! <<<")
                preco_stop = preco * (1 - stop_loss_pct)
                st.warning(f"🛑 Stop: R$ {preco_stop:.2f}")
            elif f_venda > 65 and var < -0.3:
                st.error(">>> VENDA! <<<")
            else:
                st.info("Aguardar")
        else:
            st.error("Erro ao buscar dados")

# --- GRÁFICO DO PRIMEIRO ATIVO ---
if ativos:
    st.divider()
    st.subheader(f"📈 Gráfico do {ativos[0]}")
    
    # Buscar histórico simulado para desenhar (já que a API não dá o gráfico pronto)
    try:
        # Aqui usamos uma lógica simples para criar um gráfico de linha
        # Na prática, seria ideal ter um endpoint de histórico
        dados_grafico = pd.DataFrame({
            'Tempo': [datetime.now().strftime('%H:%M:%S')],
            'Preço': [buscar_dados(ativos[0])[0]]
        })
        st.line_chart(dados_grafico.set_index('Tempo'))
    except:
        st.info("Aguardando dados para desenhar o gráfico...")