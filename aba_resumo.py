import streamlit as st
import feedparser
import time
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
                url_rss = "https://news.google.com/rss/search?q=economia+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
                feed = feedparser.parse(url_rss)
                noticias = [entry.title for entry in feed.entries[:10]]
                
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
                    
                    # --- LÓGICA DE RETRY (TENTATIVA AUTOMÁTICA) ---
                    max_tentativas = 3
                    resposta = None
                    erro_final = None
                    
                    for tentativa in range(max_tentativas):
                        try:
                            resposta = client.models.generate_content(
                                model='gemini-3.8-flash',
                                contents=prompt
                            )
                            break  # Se funcionou, sai do loop
                        except Exception as e:
                            erro_final = e
                            if "503" in str(e) or "UNAVAILABLE" in str(e):
                                # Espera 2s, depois 4s, depois 8s
                                espera = 2 ** (tentativa + 1)
                                st.info(f"Servidor do Google ocupado. Tentando de novo em {espera} segundos... (Tentativa {tentativa + 1}/{max_tentativas})")
                                time.sleep(espera)
                            else:
                                raise e  # Se for outro erro, para tudo
                    
                    if resposta is None:
                        st.error(f"O Google não respondeu após {max_tentativas} tentativas. Tente novamente em alguns minutos. Erro: {erro_final}")
                    else:
                        st.success("✅ Resumo gerado pela IA:")
                        st.markdown(resposta.text)
                        
                        with st.expander("Ver notícias usadas na análise"):
                            for i, noticia in enumerate(noticias, 1):
                                st.write(f"{i}. {noticia}")
                            
            except Exception as e:
                st.error(f"Erro ao gerar resumo: {e}")
    
    st.info("💡 Dica: O resumo é gerado sob demanda. Clique no botão para a IA analisar as notícias do momento.")
