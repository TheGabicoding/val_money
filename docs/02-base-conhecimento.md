# Base de Conhecimento

## Dados Utilizados

| Arquivo | Formato | Como Val utiliza os dados |
|---------|---------|---------------------|
| `historico_atendimento.csv` | CSV | Ter uma noção do contexto das interações para evitar repetitividade |
| `perfil_usuario.json` | JSON | Tornar a experiência mais alinhada e personalizada com o usuário |
| `produtos_financeiros.json` | JSON | Ensinar diferentes tipos de investimentos ao usuário |
| `transacoes.csv` | CSV | Analisar perfil de gastos e padrão de transferências do usuário |


## Adaptações nos Dados

Os dados mockados foram expandidos com auxílio de inteligência artificial para criar 4 novos perfis de usuário com 4 diferentes tipos de gastos, remuneração e históricos. Além disso foram adicionados alguns produtos financeiros.

---

## Estratégia de Integração

### Como os dados são carregados?

Os dados podem ser inseridos diretamente no prompt(colando os dados para o agente) ou podem ser importados com o script python a seguir:
```python
import pandas as pd
import json

#CSV
historico = pd.read.csv("data/historico_atendimento.csv")
transacoes = pd.read_csv("data/transacoes.csv")

#JSON
with open("data/perfil_usuario.json", "r", encoding-"utf-8") as f:
    perfil = json.load(f)

with open("data/produtos_financeiros.json", "r", encoding-"utf-8") as f:
    produtos = json.load(f)    
```

### Como os dados são usados no prompt?
> Os dados vão no system prompt? São consultados dinamicamente?

Os dados podem ser injetados diretamente no prompt para assegurar um contexto completo para o agente. Para soluções mais robustas o ideal é que tudo seja carregado dinâmicamente aumentando a flexibilidade.

```text
DADOS DO USUÁRIO(JSON):
{
    "nome": "Joao Silva",
    "idade": 32,
    "profissao": "Analista de Sistemas",
    "renda_mensal": 5000.00,
    "perfil_investidor": "moderado",
    "objetivo_principal": "Construir reserva de emergencia",
    "patrimonio_total": 15000.00,
    "reserva_emergencia_atual": 10000.00,
    "aceita_risco": false,
    "metas": [
      {
        "meta": "Completar reserva de emergencia",
        "valor_necessario": 15000.00,
        "prazo": "2026-06"
      }
    ]
  }

TRANSAÇÕES DO USUÁRIO(CSV):
data,cliente,descricao,categoria,valor,tipo
2025-10-01,Joao Silva,Salário,receita,5000.00,entrada
2025-10-02,Joao Silva,Aluguel,moradia,1200.00,saida
2025-10-03,Joao Silva,Supermercado,alimentacao,450.00,saida
2025-10-05,Joao Silva,Netflix,lazer,55.90,saida
2025-10-07,Joao Silva,Farmácia,saude,89.00,saida
2025-10-10,Joao Silva,Restaurante,alimentacao,120.00,saida
2025-10-12,Joao Silva,Uber,transporte,45.00,saida
2025-10-15,Joao Silva,Conta de Luz,moradia,180.00,saida
2025-10-20,Joao Silva,Academia,saude,99.00,saida
2025-10-25,Joao Silva,Combustível,transporte,250.00,saida

HISTÓRICO DE ATENDIMENTO DO USUÁRIO(CSV):
data,cliente,canal,tema,resumo,resolvido
2025-09-15,Joao Silva,chat,CDB,Cliente perguntou sobre rentabilidade e prazos,sim
2025-09-22,Joao Silva,telefone,Problema no app,Erro ao visualizar extrato foi corrigido,sim
2025-10-01,Joao Silva,chat,Tesouro Selic,Cliente pediu explicação sobre o funcionamento do Tesouro Direto,sim
2025-10-12,Joao Silva,chat,Metas financeiras,Cliente acompanhou o progresso da reserva de emergência,sim
2025-10-25,Joao Silva,email,Atualização cadastral,Cliente atualizou e-mail e telefone,sim

PRODUTOS DISPONÍVEIS PARA APRENDIZADO(JSON):
[
  {
    "nome": "Tesouro Selic",
    "categoria": "renda_fixa",
    "risco": "baixo",
    "rentabilidade": "100% da Selic",
    "aporte_minimo": 30.00,
    "indicado_para": "Reserva de emergência e iniciantes"
  },
  {
    "nome": "CDB Liquidez Diária",
    "categoria": "renda_fixa",
    "risco": "baixo",
    "rentabilidade": "102% do CDI",
    "aporte_minimo": 100.00,
    "indicado_para": "Quem busca segurança com rendimento diário"
  },
  {
    "nome": "LCI/LCA",
    "categoria": "renda_fixa",
    "risco": "baixo",
    "rentabilidade": "95% do CDI",
    "aporte_minimo": 1000.00,
    "indicado_para": "Quem pode esperar 90 dias (isento de IR)"
  },
  {
    "nome": "Fundo Multimercado",
    "categoria": "fundo",
    "risco": "medio",
    "rentabilidade": "CDI + 2%",
    "aporte_minimo": 500.00,
    "indicado_para": "Perfil moderado que busca diversificação"
  },
  {
    "nome": "Fundo de Ações",
    "categoria": "fundo",
    "risco": "alto",
    "rentabilidade": "Variável",
    "aporte_minimo": 100.00,
    "indicado_para": "Perfil arrojado com foco no longo prazo"
  },
  {
    "nome": "Tesouro IPCA+",
    "categoria": "renda_fixa",
    "risco": "baixo",
    "rentabilidade": "IPCA + 6%",
    "aporte_minimo": 30.00,
    "indicado_para": "Proteção contra inflação no longo prazo"
  },
  {
    "nome": "Fundo Imobiliário (FII)",
    "categoria": "renda_variavel",
    "risco": "medio",
    "rentabilidade": "Rendimento mensal variável",
    "aporte_minimo": 100.00,
    "indicado_para": "Quem busca renda passiva mensal"
  },
  {
    "nome": "ETF BOVA11",
    "categoria": "renda_variavel",
    "risco": "alto",
    "rentabilidade": "Acompanha o Ibovespa",
    "aporte_minimo": 110.00,
    "indicado_para": "Diversificação simples em ações brasileiras"
  }
]
```

---

## Exemplo de Contexto Montado

Os prompts seguirão o seguinte modelo, extraindo as informações mais relevantes otimizando o consumo de tokens. Apesar disso, o principal foco é passar e ensinar as informações relevantes para o usuário:

```
Dados do Cliente:
- Nome: João Silva
- Perfil: Moderado
- Saldo disponível: R$ 5.000
- Objetivo: Construir reseva de emergência
- Reserva atual R$ 10.000 (meta de R$ 15.000)

Resumo de gastos:
-  Supermercado - R$ 450
-  Streaming - R$ 55.90
-  Aluguel - R$ 1200
-  Farmácia - R$89
-  Restaurante - R$120
-  Uber - R$ 45
-  Conta de luz - R$ 180
-  Academia - R$ 99
-  Combustível - R$250

Produtos disponíveis para explicar:

- Tesouro selic (risco baixo)
- CDB Liquidez Diária(risco baixo)
- LCI/LCA (risco baixo)
- Fundo Imobiliário - FII(risco médio)
...
```
