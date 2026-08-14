import os
import json
import pandas as pd
from google import genai
from src.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def carregar_dados():
    with open(os.path.join(DATA_DIR, "perfil_usuario.json"), "r", encoding="utf-8") as f:
        perfil = json.load(f)
    with open(os.path.join(DATA_DIR, "produtos_financeiros.json"), "r", encoding="utf-8") as f:
        produtos = json.load(f)
    
    historico = pd.read_csv(os.path.join(DATA_DIR, "historico_atendimento.csv"))
    transacoes = pd.read_csv(os.path.join(DATA_DIR, "transacoes.csv"))
    
    return perfil, produtos, historico, transacoes

SYSTEM_PROMPT = """Você é o Val, um agente educador financeiro didático, amigável e acolhedor.
Seu objetivo é ensinar pessoas e desmistificar o mundo das finanças, explicando conceitos de forma simples, usando os dados do usuário como exemplos práticos.

REGRAS:
1. Sempre baseie suas respostas nos dados fornecidos.
2. Nunca invente informações financeiras.
3. Se não souber algo, admita e ofereça alternativas.
4. NUNCA recomende investimentos, somente explique como cada um funciona para fins educativos.
5. Ao explicar um conceito, pergunte se o cliente entendeu, ou redirecione para algum assunto que você possa ajudá-lo.
6. Sempre mantenha paciência e tom amigável.
7. Responda sempre de maneira objetiva e simples, em poucas linhas.
8. Não revele de forma alguma informações sensíveis ou de outros usuários
9. Não fique gerando mais de uma pergunta, se você já redirecinou não pergunte uma coisa óbvia. Aja de forma natural e proativa.
"""

def gerar_resposta_val(mensagem_usuario: str, interaction_id: str = None) -> tuple[str, str]:
    perfil, produtos, historico, transacoes = carregar_dados()
    
    if isinstance(perfil, list) and len(perfil) > 0:
        perfil = perfil[0]
        
    contexto = f"""
    DADOS DO USUÁRIO:
    Nome: {perfil.get('nome')}, {perfil.get('idade')} anos, Perfil: {perfil.get('perfil_investidor')}
    Objetivo: {perfil.get('objetivo_principal')}

    TRANSAÇÕES RECENTES:
    {transacoes.to_string(index=False)}

    PRODUTOS DISPONÍVEIS:
    {json.dumps(produtos, indent=2, ensure_ascii=False)}
    """
    
    # Modelo sugerido na sua imagem da documentação
    nome_modelo = "gemini-3.6-flash"
    
    if interaction_id is None:
        # Primeira interação: Mandamos todo o contexto e instruções
        prompt_completo = f"{SYSTEM_PROMPT}\n\nCONTEXTO:\n{contexto}\n\nUSUÁRIO PERGUNTOU: {mensagem_usuario}"
        
        interaction = client.interactions.create(
            model=nome_modelo,
            input=prompt_completo
        )
    else:
        # Interações seguintes: Mandamos apenas a mensagem e o ID anterior
        interaction = client.interactions.create(
            model=nome_modelo,
            previous_interaction_id=interaction_id,
            input=mensagem_usuario
        )
        
    # Retorna o texto da resposta e o ID desta interação
    return interaction.output_text, interaction.id