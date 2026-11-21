import streamlit as st
import feedparser
import yfinance as yf
from crew_agentes import executar_time_ias

def render_crew():
    st.header("🤝 Time de IAs (CrewAI)")
    st.write("Várias IAs especialistas trabalham juntas para decidir o melhor caminho.")
    
    if st.button("🔄 Convocar o Time de IAs", use_container_width=True):
        with st.spinner("As IAs estão se reunindo, analisando os dados e votando..."):
            try:
                # 1. Busca Notícias
                url_rss = "https://news.google.com/rss/search?q=economia+brasil&hl=pt-BR&gl=BR&ceid=BR:pt-419"
                feed = feedparser.parse(url_rss)
                noticias = [entry.title for entry in feed.entries[:5]] # Pega as 5 principais
                
                # 2. Busca FIIs (Exemplo com HGLG11 e SNEL11)
                fiis = []
                for ticker in ["HGLG11.SA", "SNEL11.SA"]:
                    try:
                        preco = yf.Ticker(ticker).fast_info['lastPrice']
                        fiis.append(f"{ticker}: R$ {preco:.2f}")
                    except:
                        pass
                
                # 3. Busca Commodities (Exemplo com Ouro e Petróleo)
                commodities = []
                for ticker in ["GOLD11.SA", "PETR4.SA"]:
                    try:
                        preco = yf.Ticker(ticker).fast_info['lastPrice']
                        commodities.append(f"{ticker}: R$ {preco:.2f}")
                    except:
                        pass

                # 4. Chama o time de IAs
                resultado = executar_time_ias(
                    noticias="\n".join(noticias),
                    dados_fiis=", ".join(fiis),
                    dados_commodities=", ".join(commodities)
                )
                
                st.success("✅ Veredito Final do Time de IAs:")
                st.markdown(resultado)
                
            except Exception as e:
                st.error(f"Erro na reunião das IAs: {e}")
    
    st.info("💡 Dica: O time usa 4 chamadas de API por vez. Se der erro de cota (429), espere um pouco antes de tentar de novo.")
