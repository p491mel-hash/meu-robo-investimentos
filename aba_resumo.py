import streamlit as st
import feedparser
from google import genai

def render_resumo():
    st.header("🧠 Resumo do Dia - Análise das IAs")
    st.write("Esta aba usa a API do Google Gemini para ler as notícias do mercado e gerar um resumo.")
    
    try:
        gemini_key = st.secrets["GEMINI_API_KEY"]
    except:
        gemini_key = None

    if not gemini_key:
        st.warning("⚠️ Chave da API do Gemini não encontrada nos Secrets.")
        return

    if st.button("🔄 Gerar Resumo do Dia (IA)", use_container_width=True):
        with st.spinner("A IA está lendo as notícias e analisando o mercado..."):
            try:
                # Usa o feedparser para ler o RSS do Google News (Economia/Brasil)
                url_rss = "https://news.google.com/rss/search?q=economia+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
                feed = feedparser.parse(url_rss)
                
                # Extrai os títulos das notícias
                noticias = [entry.title for entry in feed.entries[:10]]
                
                if not noticias:
                    st.warning("Não foi possível extrair notícias do RSS. Tente novamente em alguns instantes.")
                else:
                    prompt = f"""
                    Você é um analista de mercado financeiro brasileiro.
                    Analise as seguintes notícias do dia e gere um resumo claro e objetivo em português.
                    Destaque:
                    1. O sentimento geral do mercado (positivo, negativo ou neutro).
                    2. Os setores ou ativos que podem ser afetados.
                    3. Uma recomendação simples (cautela, oportunidade de compra, etc.).
                    
                    Notícias:
                    {chr(10).join(noticias)}
                    """
                    
                    client = genai.Client(api_key=gemini_key)
                    resposta = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=prompt
                    )
                    
                    st.success("✅ Resumo gerado pela IA:")
                    st.markdown(resposta.text)
                    
                    with st.expander("Ver notícias usadas na análise"):
                        for i, noticia in enumerate(noticias, 1):
                            st.write(f"{i}. {noticia}")
                            
            except Exception as e:
                st.error(f"Erro ao gerar resumo: {e}")
    
    st.info("💡 Dica: O resumo é gerado sob demanda. Clique no botão para a IA analisar as notícias do momento.")
