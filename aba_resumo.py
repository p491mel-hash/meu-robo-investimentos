import streamlit as st
import feedparser
import time
from google import genai

def render_resumo():
    st.header("🧠 Análise e Decisão das IAs")
    st.write("A IA lê as notícias, decide o melhor caminho e presta contas do que fez.")
    
    try:
        gemini_key = st.secrets["GEMINI_API_KEY"]
    except:
        gemini_key = None

    if not gemini_key:
        st.warning("⚠️ Chave da API do Gemini não encontrada nos Secrets.")
        return

    if st.button("🔄 Analisar e Decidir (IA)", use_container_width=True):
        with st.spinner("A IA está lendo as notícias, tomando a decisão e preparando o relatório..."):
            try:
                url_rss = "https://news.google.com/rss/search?q=economia+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
                feed = feedparser.parse(url_rss)
                noticias = [entry.title for entry in feed.entries[:10]]
                
                if not noticias:
                    st.warning("Não foi possível extrair notícias do RSS.")
                    return

                prompt = f"""
                Você é um gestor de fundos de investimento sênior e autônomo.
                
                Sua tarefa:
                1. Leia atentamente as notícias abaixo.
                2. Baseado APENAS no que você leu, decida qual é o melhor caminho para o mercado brasileiro hoje.
                3. Escolha UMA das três opções: COMPRAR (mercado em alta), VENDER (mercado em baixa) ou AGUARDAR (mercado neutro/incerto).
                4. JUSTIFIQUE sua decisão citando as notícias que te levaram a essa conclusão.
                5. Explique o que você fez: "Eu li as notícias, identifiquei que [resumo do que viu] e por isso decidi [decisão]".
                
                Formato da resposta (obrigatório):
                **DECISÃO:** [COMPRAR / VENDER / AGUARDAR]
                **JUSTIFICATIVA:** [Sua explicação baseada nas notícias]
                **O QUE EU FIZ:** [Seu relatório de ações]
                
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
                            espera = 2 ** (tentativa + 1)
                            st.info(f"Servidor do Google ocupado. Tentando de novo em {espera} segundos... (Tentativa {tentativa + 1}/{max_tentativas})")
                            time.sleep(espera)
                        else:
                            raise e
                
                if resposta is None:
                    st.error(f"O Google não respondeu após {max_tentativas} tentativas. Tente novamente em alguns minutos. Erro: {erro_final}")
                else:
                    st.success("✅ Relatório da IA:")
                    st.markdown(resposta.text)
                    
                    with st.expander("🔍 Ver as notícias que a IA leu"):
                        for i, noticia in enumerate(noticias, 1):
                            st.write(f"{i}. {noticia}")
                            
            except Exception as e:
                st.error(f"Erro na análise: {e}")
    
    st.info("💡 A IA agora lê as notícias, decide o melhor caminho e te mostra o relatório do que ela fez.")
