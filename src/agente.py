import os
import re
import json
from datetime import date
import pandas as pd
from google import genai
from src.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

NOME_MODELO = "gemini-3.6-flash"


# ── Carregamento de dados ────────────────────────────────────────────────────

def carregar_dados(nome_usuario: str):
    """
    Carrega produtos e transações filtrados para o usuário logado.
    Gastos mensais são calculados diretamente do CSV (fonte única da verdade).

    Returns:
        Tuple (produtos, transacoes_usuario, gastos_por_categoria)
    """
    with open(os.path.join(DATA_DIR, "produtos_financeiros.json"), "r", encoding="utf-8") as f:
        produtos = json.load(f)

    df_transacoes = pd.read_csv(os.path.join(DATA_DIR, "transacoes.csv"))
    transacoes_usuario = df_transacoes[df_transacoes["cliente"] == nome_usuario]

    # Gastos mensais calculados das saídas (CSV é a única fonte de verdade)
    gastos_por_categoria: dict = {}
    if not transacoes_usuario.empty:
        saidas = transacoes_usuario[transacoes_usuario["tipo"] == "saida"]
        if not saidas.empty:
            gastos_por_categoria = (
                saidas.groupby("categoria")["valor"]
                .sum()
                .round(2)
                .to_dict()
            )

    return produtos, transacoes_usuario, gastos_por_categoria


# ── Persistência de gastos no CSV ────────────────────────────────────────────

_PALAVRAS_GASTOS = [
    "aluguel", "alimentação", "comida", "mercado", "lazer", "transporte",
    "netflix", "internet", "conta", "gasto", "despesa", "mensalidade",
    "academia", "luz", "água", "plano", "combustível", "roupas", "saúde",
    "r$", "reais", "faculdade", "escola", "seguro", "moradia",
]

_PROMPT_EXTRACAO = """Analise o texto abaixo e extraia SOMENTE categorias de gastos mensais com seus respectivos valores em Reais.

Regras:
- Retorne APENAS um JSON válido no formato: {"Categoria": valor_numerico, ...}
- Use nomes de categoria simples, sem acentos, em minúsculo (ex: "aluguel", "alimentacao", "lazer")
- Converta os valores para float (ex: "R$ 1.200,00" → 1200.0)
- Se o texto NÃO contiver gastos financeiros explícitos com valores, retorne apenas: null

Texto:
"""


def _pode_conter_gastos(texto: str) -> bool:
    """Heurística leve para evitar chamadas desnecessárias à API de extração."""
    tem_numero = bool(re.search(r"\d", texto))
    return tem_numero and any(kw in texto.lower() for kw in _PALAVRAS_GASTOS)


def extrair_gastos(texto: str) -> dict | None:
    """
    Usa o Gemini para extrair categorias de gastos do texto do usuário.
    Retorna dict {categoria: valor_float} ou None se não houver gastos.
    """
    if not _pode_conter_gastos(texto):
        return None
    try:
        interaction = client.interactions.create(
            model=NOME_MODELO,
            input=_PROMPT_EXTRACAO + texto,
        )
        resultado = interaction.output_text.strip()
        if not resultado or resultado.lower() == "null":
            return None
        resultado = re.sub(r"```(?:json)?", "", resultado).strip().rstrip("`").strip()
        gastos = json.loads(resultado)
        if isinstance(gastos, dict) and len(gastos) > 0:
            return {k.lower().replace(" ", "_"): float(v) for k, v in gastos.items()}
    except Exception:
        pass
    return None


# ── Extração automática de aportes ──────────────────────────────────────────

_PALAVRAS_APORTE = [
    "guardei", "guardar", "investi", "investir", "depositei", "sobrou", 
    "aporte", "poupanca", "poupança", "meta", "reserva"
]

_PROMPT_EXTRACAO_APORTE = """Analise o texto abaixo e extraia SOMENTE o valor financeiro (em Reais) que o usuário explicitamente afirma ter guardado, investido, poupado ou depositado neste momento.

Regras:
- Retorne APENAS um número float (ex: se for R$ 500,00 retorne 500.0).
- Se o usuário estiver apenas fazendo uma pergunta ou planejamento (ex: "quanto eu guardo?", "vou guardar 100"), NÃO extraia. Extraia apenas se ele indicar que JÁ guardou ou ESTÁ guardando agora (ex: "guardei 50", "consegui juntar 200").
- Se não houver aporte explícito, retorne apenas: null

Texto:
"""

def _pode_conter_aporte(texto: str) -> bool:
    tem_numero = bool(re.search(r"\d", texto))
    return tem_numero and any(kw in texto.lower() for kw in _PALAVRAS_APORTE)

def extrair_aporte(texto: str) -> float | None:
    """
    Extrai o valor que o usuário afirma ter guardado/investido.
    """
    if not _pode_conter_aporte(texto):
        return None
    try:
        interaction = client.interactions.create(
            model=NOME_MODELO,
            input=_PROMPT_EXTRACAO_APORTE + texto,
        )
        resultado = interaction.output_text.strip()
        if not resultado or resultado.lower() == "null":
            return None
        # Remove caracteres indesejados e converte
        valor_limpo = re.sub(r"[^\d\.]", "", resultado)
        if valor_limpo:
            return float(valor_limpo)
    except Exception:
        pass
    return None


def salvar_gastos_no_csv(nome_usuario: str, gastos: dict) -> None:
    """
    Salva os gastos informados pelo usuário no transacoes.csv.
    Remove entradas anteriores do mesmo usuário que sejam do tipo 'saida'
    com fonte 'manual' antes de inserir, evitando duplicatas.
    """
    csv_path = os.path.join(DATA_DIR, "transacoes.csv")
    df = pd.read_csv(csv_path)

    # Remove gastos manuais antigos deste usuário, se existirem
    if "fonte" in df.columns:
        df = df[~((df["cliente"] == nome_usuario) & (df["fonte"] == "manual"))]

    hoje = date.today().strftime("%Y-%m-%d")
    novas_linhas = []
    for categoria, valor in gastos.items():
        linha = {
            "data":      hoje,
            "cliente":   nome_usuario,
            "descricao": categoria.replace("_", " ").title(),
            "categoria": categoria,
            "valor":     float(valor),
            "tipo":      "saida",
        }
        if "fonte" in df.columns:
            linha["fonte"] = "manual"
        novas_linhas.append(linha)

    df_novas = pd.DataFrame(novas_linhas)

    # Adiciona coluna 'fonte' ao df original se ainda não existir
    if "fonte" not in df.columns:
        df["fonte"] = "banco"
        df_novas["fonte"] = "manual"

    df_final = pd.concat([df, df_novas], ignore_index=True)
    df_final.to_csv(csv_path, index=False)


# ── Prompt do sistema ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Você é o Val, um agente educador financeiro didático, amigável e acolhedor.
Seu objetivo é ensinar pessoas e desmistificar o mundo das finanças, explicando conceitos de forma simples, usando os dados do usuário como exemplos práticos.

REGRAS GERAIS:
1. Sempre baseie suas respostas nos dados fornecidos.
2. Nunca invente informações financeiras.
3. Se não souber algo, admita e ofereça alternativas.
4. Ao recomendar investimentos, sempre enfatize o risco ao usuário.
5. Sempre pergunte se o cliente entendeu; caso não tenha entendido, reexplique de outra maneira.
6. Sempre mantenha paciência e tom amigável.
7. Use os dados fornecidos para dar exemplos personalizados.
8. Responda de maneira objetiva e simples, usando emojis, listas e tabelas para facilitar a compreensão.
9. Não faça mais de uma pergunta por vez. Seja natural e proativo.
10. Não revele informações sensíveis ou dados de outros usuários.

REGRAS SOBRE GASTOS E ANÁLISE FINANCEIRA:
11. O campo "GASTOS MENSAIS DO CSV" contém os gastos reais do usuário, calculados automaticamente
    de suas transações. Use-os como base principal para qualquer análise financeira.

12. SE o campo "GASTOS MENSAIS DO CSV" estiver vazio ou indicar "Nenhuma transação registrada":
    - Na PRIMEIRA interação financeira relevante (sobre organização, orçamento, investimentos,
      metas ou dinheiro em geral), peça os gastos mensais por categoria ANTES de dar qualquer conselho.
    - Use exatamente este formato de exemplo para orientar o usuário:
        Aluguel: R$ 800,00
        Alimentação: R$ 300,00
        Lazer: R$ 500,00
        Internet: R$ 100,00
      (Adapte as sugestões de categorias ao perfil do usuário — estudante, profissional etc.)
    - Informe que as informações serão salvas para que não precise repetir futuramente.

13. Quando o usuário informar os gastos, confirme que os recebeu e faça a análise completa:
    - Liste os gastos recebidos de forma organizada
    - Calcule o total de gastos
    - Calcule o saldo livre (renda mensal - total gastos)
    - Sugira como destinar o saldo livre conforme o perfil investidor do usuário
    - Cite produtos financeiros disponíveis no contexto
    - Estime em quantos meses a meta principal pode ser alcançada

14. SE o campo "GASTOS MENSAIS DO CSV" já tiver dados, use-os diretamente.
    Não peça os gastos novamente — o usuário já os forneceu em uma sessão anterior.

REGRAS SOBRE APORTES E METAS:
15. Quando o usuário afirmar que conseguiu guardar, investir ou poupar dinheiro (ex: "guardei R$ 500 para a meta"):
    - Parabenize-o de forma muito calorosa pelo esforço e consistência!
    - Diga claramente que você está atualizando o patrimônio e a barra de progresso dele.
    - Mostre como isso o deixa mais perto do seu objetivo (use o campo "Metas" do contexto).
"""


# ── Resposta principal do agente ─────────────────────────────────────────────

def gerar_resposta_val(
    mensagem_usuario: str,
    perfil: dict,
    interaction_id: str = None,
) -> tuple[str, str]:
    """
    Gera uma resposta do Val para o usuário autenticado.

    Args:
        mensagem_usuario: Texto enviado pelo usuário.
        perfil: Dicionário com os dados do perfil do usuário logado.
        interaction_id: ID da interação anterior (para manutenção de contexto).

    Returns:
        Tuple (texto_da_resposta, novo_interaction_id).
    """
    nome_usuario = perfil.get("nome", "")
    produtos, transacoes, gastos_csv = carregar_dados(nome_usuario)

    metas_str = json.dumps(perfil.get("metas", []), indent=2, ensure_ascii=False)

    if gastos_csv:
        total_gastos = sum(gastos_csv.values())
        renda        = perfil.get("renda_mensal", 0)
        saldo_livre  = renda - total_gastos
        linhas_gastos = "\n    ".join(
            f"{cat.replace('_', ' ').title()}: R$ {val:,.2f}"
            for cat, val in sorted(gastos_csv.items())
        )
        gastos_str = (
            f"{linhas_gastos}\n\n"
            f"    Total de gastos: R$ {total_gastos:,.2f}\n"
            f"    Saldo livre estimado: R$ {saldo_livre:,.2f}"
        )
    else:
        gastos_str = "Nenhuma transação registrada para este usuário ainda."



    transacoes_str = (
        transacoes[["data", "descricao", "categoria", "valor", "tipo"]]
        .to_string(index=False)
        if not transacoes.empty
        else "Sem transações registradas."
    )

    contexto = f"""
    DADOS DO USUÁRIO:
    Nome: {perfil.get('nome')}, {perfil.get('idade')} anos
    Profissão: {perfil.get('profissao')}
    Renda mensal: R$ {perfil.get('renda_mensal', 0):,.2f}
    Perfil investidor: {perfil.get('perfil_investidor')}
    Patrimônio total: R$ {perfil.get('patrimonio_total', 0):,.2f}
    Reserva de emergência atual: R$ {perfil.get('reserva_emergencia_atual', 0):,.2f}
    Aceita risco: {perfil.get('aceita_risco', False)}
    Metas: {metas_str}

    GASTOS MENSAIS DO CSV (fonte única de verdade):
    {gastos_str}

    EXTRATO DE TRANSAÇÕES RECENTES:
    {transacoes_str}

    PRODUTOS FINANCEIROS DISPONÍVEIS:
    {json.dumps(produtos, indent=2, ensure_ascii=False)}
    """

    if interaction_id is None:
        prompt_completo = (
            f"{SYSTEM_PROMPT}\n\nCONTEXTO:\n{contexto}\n\nUSUÁRIO PERGUNTOU: {mensagem_usuario}"
        )
        interaction = client.interactions.create(
            model=NOME_MODELO,
            input=prompt_completo,
        )
    else:
        interaction = client.interactions.create(
            model=NOME_MODELO,
            previous_interaction_id=interaction_id,
            input=mensagem_usuario,
        )

    return interaction.output_text, interaction.id