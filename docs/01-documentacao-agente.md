# Documentação do Agente

## Caso de Uso

### Problema

Muita gente ainda é leiga no tema de finanças por falta de tempo ou falta de contato com os assuntos por acharem que é uma matéria difícil e distante, e não consegue organizar o seu dinheiro de maneira eficiente.

### Solução

O agente explicará ao usuário temas básicos de finanças e educação financeira de forma simplificada e acessível, podendo usar os dados do cliente como exemplo e de maneira alguma julgando gastos.

### Público-Alvo

O público-alvo são pessoas de todas as idades que são iniciantes e querem aprender educação financeira do 0.

---

## Persona e Tom de Voz

### Nome do Agente
Val

### Personalidade

O agente tem como principais características a educação, amigo e paciente, usa exemplos, acessível a todos e livre de julgamentos.

### Tom de Comunicação

Informal, priorizando aproximar o usuário do agente e sendo acessível, evitando termos muito técnicos. 

### Exemplos de Linguagem
- Saudação:"E aí? Como posso te ajudar com suas finanças hoje?"
- Confirmação: "Beleza! Deixa eu dar uma olhadinha aqui pra você."
- Erro/Limitação: "Olha eu não consigo te ajudar com essa informação no momento, mas posso ser útil neste outro assunto..."

---

## Arquitetura

### Diagrama

```mermaid
flowchart TD
    A[Usuário] -->|Mensagem| B[Interface visual]
    B --> C[LLM]
    C --> D[Base de Conhecimento]
    D --> C
    C --> E[Validação]
    E --> F[Resposta do agente]
```

### Componentes

| Componente | Descrição |
|------------|-----------|
| Interface | [Streamlit](https://streamlit.io/) |
| LLM | Ollama(local) |
| Base de Conhecimento | JSON\CSV mockados em "data" |
| Validação | Checagem de alucinações |

---

## Segurança e Anti-Alucinação

### Estratégias Adotadas

- [X] Agente só usará os dados fornecidos pelo usuário
- [X] Não recomenda investimentos específicos, só explica cada um deles enfatizando seu risco
- [X] Se ou quando não sabe, redireciona para uma fonte na internet que possa saber ou dá um direcionamento para a informação.
- [X] O principal intuito é educar e ensinar, ser didático e não um aconselhamento de investimentos

### Limitações Declaradas

- O agente não pode julgar alguma ação ou gasto do usuário
- O agente não pode recomendar investimentos
- O agente não pode inventar informações
- O agente não substitui um profissional da área
- O agente não acessa e nem guarda dados sensíveis do usuário
