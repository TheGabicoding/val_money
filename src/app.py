import streamlit as st
from agente import gerar_resposta_val

st.title("Val - Agente Educador Financeiro 💬")

# Inicializa as variáveis na sessão do Streamlit, se não existirem
if "interaction_id" not in st.session_state:
    st.session_state.interaction_id = None
    
if "historico_chat" not in st.session_state:
    st.session_state.historico_chat = []

# Mostra as mensagens anteriores na tela sempre que a página recarregar
for mensagem in st.session_state.historico_chat:
    st.chat_message(mensagem["role"]).write(mensagem["content"])

user_input = st.text_input("Digite sua pergunta sobre finanças:")

if user_input:
    # 1. Mostra a mensagem do usuário e salva no histórico
    st.chat_message("user").write(user_input)
    st.session_state.historico_chat.append({"role": "user", "content": user_input})
    
    with st.spinner("Aguarde enquanto o Val pensa..."):
        try:
            # 2. Chama a API passando a mensagem e o ID (se houver)
            resposta_val, novo_id = gerar_resposta_val(
                mensagem_usuario=user_input, 
                interaction_id=st.session_state.interaction_id
            )
            #corrige erros de formatação ao usar cifrão.
            resposta_val = resposta_val.replace("$", "\\$")
            
            # 3. Atualiza o ID da interação para a PRÓXIMA mensagem
            st.session_state.interaction_id = novo_id
            
            # 4. Mostra a resposta do bot e salva no histórico
            st.chat_message("assistant").write(resposta_val)
            st.session_state.historico_chat.append({"role": "assistant", "content": resposta_val})
            
        except Exception as e:
            st.error(f"Ops, ocorreu um erro de conexão: {e}")