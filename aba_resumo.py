import streamlit as st
import feedparser
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
                # 1. Busca as notícias (o código busca, não a IA)
                url_rss = "https://news.google.com/rss/search?q=economia+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
                feed = feedparser.parse(url_rss)
                noticias = [entry.title for entry in feed.entries[:10]]
                
                if not noticias:
                    st.warning("Não foi possível extrair notícias do RSS.")
                    return

                # 2. Monta o prompt para a IA AGIR e PRESTAR CONTAS
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
                
                # 3. Chama a IA
                client = genai.Client(api_key=gemini_key)
                resposta = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt
                )
                
                # 4. Mostra o resultado (a "prestação de contas")
                st.success("✅ Relatório da IA:")
                st.markdown(resposta.text)
                
                # 5. Mostra as notícias que ela usou (transparência total)
                with st.expander("🔍 Ver as notícias que a IA leu"):
                    for i, noticia in enumerate(noticias, 1):
                        st.write(f"{i}. {noticia}")
                        
            except Exception as e:
                st.error(f"Erro na análise: {e}")
    
    st.info("💡 A IA agora lê as notícias, decide o melhor caminho e te mostra o relatório do que ela fez.")
