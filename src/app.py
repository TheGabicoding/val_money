import os
from google import genai
import streamlit as st
import json
from operator import index
import pandas as pd

#carregando os dados
perfil = json.load(open("./data/perfil_usuario.json"))
produtos = json.load(open("./data/produtos_financeiros.json"))
historico = pd.read_csv("./data/historico_atendimento")
transacoes = pd.read_csv("./data/transacoes")

#montando contexto
contexto = f"""
USUÁRIO: {perfil["nome"]}, {perfil["idade"]} anos, perfil {perfil["perfil_investidor"]}

OBJETIVO: {perfil["objetivo_principal"]}

TRANSAÇÕES RECENTES 
{transacoes.to_string(index = False)}

ATENDIMENTOS ANTERIORES:
{historico.to_string(index = False)}

PRODUTOS DISPONÍVEIS:
{json.dumps(produtos, indent = 2, ensure_ascii = False)}

"""

SYSTEM_PROMPT = """ Você é o Val, um agente educador financeiro didático, amigável e acolhedor.
Seu objetivo é ensinar pessoas e desmistificar o mundo das finanças, explicando conceitos de forma simples, usando os dados do usuário como exemplos práticos.

REGRAS:
1. Sempre baseie suas respostas nos dados fornecidos.
2. Nunca invente informações financeiras.
3. Se não souber algo, admita e ofereça alternativas.
4. NUNCA recomende investimentos, somente explique como cada um funciona para fins educativos. A decisão final cabe sempre ao usuário.
5. Sempre pergunte se o cliente entendeu, caso não tenha entendido, reexplique de outra maneira.
6. Sempre mantenha paciência e tom amigável.
7. Busque usar os dados fornecidos para dar exemplos personalizados.
8. Responda sempre de maneira objetiva e simples, em poucas linhas
"""

client = genai.Client(api_key=os.environ["sua_chave_de_api_aqui"])

def pergunta(mensagem):
    resposta = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SYSTEM_PROMPT}\n\n{contexto}\n\nUSUÁRIO PERGUNTOU: {mensagem}",
    )
    return resposta.text

st.title("Val - Agente Educador Financeiro")

if pergunta := st.text_input("Digite sua pergunta sobre finanças:"):
    st.chat_message("user").write(pergunta)
    with st.spinner("Aguarde enquanto o Val responde..."):
        st.chat_message("assistant").write(pergunta(pergunta))

    