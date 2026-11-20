import streamlit as st
from google import genai
from google.genai import types

def render_resumo():
    st.header("🧠 Análise Autônoma das IAs")
    st.write("A IA vai pesquisar no Google em tempo real, ler as notícias que ela achar relevantes e decidir o que fazer com elas.")
    
    try:
        gemini_key = st.secrets["GEMINI_API_KEY"]
    except:
        gemini_key = None

    if not gemini_key:
        st.warning("⚠️ Chave da API do Gemini não encontrada nos Secrets.")
        return

    if st.button("🔄 Analisar Mercado (IA Autônoma)", use_container_width=True):
        with st.spinner("A IA está pesquisando notícias no Google e tomando decisões..."):
            try:
                # Configura o cliente
                client = genai.Client(api_key=gemini_key)
                
                # Define a ferramenta de busca do Google
                grounding_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )
                
                # Configura a requisição
                config = types.GenerateContentConfig(
                    tools=[grounding_tool]
                )
                
                # O prompt agora é uma ORDEM para a IA agir, não para ela resumir algo que já temos
                prompt = """
                Você é um analista de investimentos sênior e autônomo.
                
                Sua tarefa:
                1. Pesquise no Google as notícias mais recentes (últimas 24h) sobre o mercado brasileiro (Ibovespa, Dólar, PETR4, VALE3, e economia em geral).
                2. Leia os resultados que você encontrar.
                3. Baseado APENAS no que você leu, decida: O mercado está em viés de ALTA, BAIXA ou NEUTRO?
                4. Justifique sua decisão citando as notícias que você encontrou.
                5. Dê uma recomendação clara: COMPRAR, VENDER ou AGUARDAR.
                
                Responda em português, de forma direta e objetiva.
                """
                
                # Chama a IA (agora com a ferramenta de busca ativa)
                resposta = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt,
                    config=config
                )
                
                st.success("✅ Análise Autônoma Concluída:")
                st.markdown(resposta.text)
                
                # Mostra as fontes que a IA usou (se disponível)
                if hasattr(resposta, 'candidates') and resposta.candidates:
                    metadata = resposta.candidates[0].grounding_metadata
                    if metadata and metadata.grounding_chunks:
                        with st.expander("🔗 Fontes consultadas pela IA"):
                            for chunk in metadata.grounding_chunks:
                                if hasattr(chunk, 'web') and chunk.web:
                                    st.write(f"- [{chunk.web.title}]({chunk.web.uri})")
                                    
            except Exception as e:
                st.error(f"Erro na análise autônoma: {e}")
    
    st.info("💡 Dica: A IA agora decide sozinha o que pesquisar no Google. Ela lê as notícias e toma a decisão baseada no que encontrou.")
