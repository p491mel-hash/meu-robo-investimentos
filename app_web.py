import streamlit as st

st.title("Teste de Conexão")
st.write("Se você está vendo isso, o site está lendo este arquivo.")

try:
    chave = st.secrets["ALPACA_API_KEY"]
    st.success("✅ A chave da Alpaca foi encontrada nos Secrets!")
    st.write(f"O primeiro pedaço da chave é: {chave[:5]}...")
except Exception as e:
    st.error(f"❌ Erro ao ler os Secrets: {e}")
