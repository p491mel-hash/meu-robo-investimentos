import os
from crewai import Agent, Task, Crew, Process, LLM
from config import GEMINI_API_KEY

# Configura o Gemini para o CrewAI (usando a API compatível com OpenAI)
os.environ["OPENAI_API_KEY"] = GEMINI_API_KEY
os.environ["OPENAI_API_BASE"] = "https://generativelanguage.googleapis.com/v1beta/openai/"
os.environ["OPENAI_MODEL_NAME"] = "gemini-3.8-flash"

# Cria a LLM que será usada por todos os agentes
gemini_llm = LLM(
    model="openai/gemini-3.8-flash",
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def executar_time_ias(noticias, dados_fiis, dados_commodities):
    # 1. Agente de Notícias
    agente_noticias = Agent(
        role="Analista de Notícias",
        goal="Ler as notícias e dizer se o sentimento do mercado é positivo, negativo ou neutro.",
        backstory="Você é um jornalista financeiro especialista em interpretar manchetes.",
        llm=gemini_llm,
        verbose=True
    )

    # 2. Agente de FIIs
    agente_fiis = Agent(
        role="Especialista em FIIs",
        goal="Analisar os preços dos FIIs e dizer se estão em boa hora de compra.",
        backstory="Você é um investidor experiente em fundos imobiliários.",
        llm=gemini_llm,
        verbose=True
    )

    # 3. Agente de Commodities
    agente_commodities = Agent(
        role="Especialista em Commodities",
        goal="Analisar os preços das commodities e identificar oportunidades.",
        backstory="Você é um trader focado em ouro, petróleo e boi gordo.",
        llm=gemini_llm,
        verbose=True
    )

    # 4. Agente Gerente (O Chefe)
    agente_gerente = Agent(
        role="Gestor de Fundos",
        goal="Receber os relatórios de todos e decidir o melhor caminho para o lucro.",
        backstory="Você é o chefe da mesa. Você lê o que os especialistas dizem e bate o martelo.",
        llm=gemini_llm,
        verbose=True
    )

    # Tarefas
    tarefa_noticias = Task(
        description=f"Analise estas notícias: {noticias}. Diga o sentimento (Positivo/Negativo/Neutro).",
        expected_output="Um relatório curto com o sentimento do mercado.",
        agent=agente_noticias
    )

    tarefa_fiis = Task(
        description=f"Analise estes FIIs: {dados_fiis}. Veja se estão baratos ou caros.",
        expected_output="Um relatório sobre FIIs.",
        agent=agente_fiis
    )

    tarefa_commodities = Task(
        description=f"Analise estas commodities: {dados_commodities}. Veja se estão subindo ou caindo.",
        expected_output="Um relatório sobre commodities.",
        agent=agente_commodities
    )

    tarefa_final = Task(
        description="Com base nos relatórios de notícias, FIIs e commodities, decida: COMPRAR, VENDER ou AGUARDAR. Justifique.",
        expected_output="Decisão final (COMPRAR/VENDER/AGUARDAR) e justificativa.",
        agent=agente_gerente,
        context=[tarefa_noticias, tarefa_fiis, tarefa_commodities] # O gerente lê o que os outros fizeram
    )

    # Cria a equipe e executa
    crew = Crew(
        agents=[agente_noticias, agente_fiis, agente_commodities, agente_gerente],
        tasks=[tarefa_noticias, tarefa_fiis, tarefa_commodities, tarefa_final],
        process=Process.sequential,
        verbose=True
    )

    return crew.kickoff()
