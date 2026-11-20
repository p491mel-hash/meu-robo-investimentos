import streamlit as st
import requests
from google import genai

def render_resumo():
    st.header("🧠 Resumo do Dia - Análise das IAs")
    st.write("Esta aba usa a API do Google Gemini para ler as notícias do mercado e gerar um resumo.")
    
    # Tenta pegar a chave diretamente do Secrets
    try:
        gemini_key = st.secrets["GEMINI_API_KEY"]
    except:
        gemini_key = None

    if not gemini_key:
        st.warning("⚠️ Chave da API do Gemini não encontrada nos Secrets. Verifique em Settings > Secrets.")
        return

    if st.button("🔄 Gerar Resumo do Dia (IA)", use_container_width=True):
        with st.spinner("A IA está lendo as notícias e analisando o mercado..."):
            try:
                url_rss = "https://www.infomoney.com.br/feed/"
                response = requests.get(url_rss, timeout=10)
                
                import re
                titulos = re.findall(r'<title><!\[CDATA\[(.*?)\]\]></title>', response.text)
                noticias = titulos[:10] if len(titulos) > 10 else titulos
                
                if not noticias:
                    st.warning("Não foi possível extrair notícias do RSS.")
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
