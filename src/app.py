import pandas as pd
import streamlit as st
from auth import (
    inicializar_usuarios,
    verificar_login,
    username_existe,
    cadastrar_usuario,
    atualizar_dados_perfil,
    adicionar_patrimonio,
)
from agente import gerar_resposta_val, carregar_dados, extrair_gastos, salvar_gastos_no_csv, extrair_aporte

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Val — Educador Financeiro",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Garante que os usuários de teste existam ao iniciar o app
inicializar_usuarios()

# ── Estado da sessão ────────────────────────────────────────────────────────
DEFAULTS = {
    "logged_in": False,
    "current_user": None,
    "historico_chat": [],
    "interaction_id": None,
}
for _key, _val in DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val


# ── Helpers ─────────────────────────────────────────────────────────────────
def _logout():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v
    st.rerun()


def _fmt_brl(valor) -> str:
    try:
        return f"R\\$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "—"


def _perfil_badge(perfil_inv: str) -> str:
    cores = {
        "conservador": "🟢",
        "moderado": "🟡",
        "arrojado": "🔴",
        "nao_investidor": "⚪",
    }
    return cores.get(perfil_inv, "⚫")


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                          TELA DE LOGIN / CADASTRO                       ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def _form_login():
    """Renderiza o formulário de login."""
    with st.form("form_login", clear_on_submit=False):
        username = st.text_input(
            "Usuário",
            placeholder="Ex: joao123",
            label_visibility="visible",
        )
        senha = st.text_input(
            "Senha",
            type="password",
            placeholder="Sua senha",
        )
        entrar = st.form_submit_button("Entrar →", use_container_width=True, type="primary")

    if entrar:
        if not username or not senha:
            st.error("Preencha usuário e senha.")
            return
        perfil = verificar_login(username.strip(), senha)
        if perfil:
            st.session_state.logged_in = True
            st.session_state.current_user = perfil
            st.session_state.historico_chat = []
            st.session_state.interaction_id = None
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos. Tente novamente.")

    st.markdown("---")
    st.caption(
        "**Contas de teste disponíveis** — senha de todos: `senha123`\n\n"
        "`joao123` · `ana123` · `carlos123` · `lucas123` · `mariana123`"
    )


def _form_cadastro():
    """Renderiza o formulário de cadastro de novo usuário."""
    st.markdown("#### Dados pessoais")
    col_a, col_b = st.columns(2)
    with col_a:
        nome       = st.text_input("Nome completo *", key="cad_nome")
        profissao  = st.text_input("Profissão *", key="cad_prof")
        renda      = st.number_input("Renda mensal (R$) *", min_value=0.0, step=100.0, key="cad_renda")
    with col_b:
        idade       = st.number_input("Idade *", min_value=1, max_value=120, step=1, value=18, key="cad_idade")
        perfil_inv  = st.selectbox(
            "Perfil investidor *",
            ["conservador", "moderado", "arrojado", "nao_investidor"],
            format_func=lambda x: x.replace("_", " ").title(),
            key="cad_perf",
        )
        aceita_risco = st.checkbox("Aceito exposição a riscos moderados", key="cad_risco")



    st.markdown("#### Meta principal")
    col_c, col_d, col_e = st.columns([3, 2, 2])
    with col_c:
        meta_desc  = st.text_input("Qual sua maior meta? (Ex: Comprar carro) *", key="cad_meta_desc")
    with col_d:
        meta_valor = st.number_input("Valor alvo (R$) *", min_value=0.0, step=100.0, key="cad_meta_val")
    with col_e:
        meta_prazo = st.text_input("Prazo (AAAA-MM) *", placeholder="2027-06", key="cad_meta_prazo")

    st.markdown("#### Credenciais de acesso")
    col_f, col_g, col_h = st.columns(3)
    with col_f:
        new_username = st.text_input("Usuário *", key="cad_user")
    with col_g:
        new_senha    = st.text_input("Senha *", type="password", key="cad_pw")
    with col_h:
        conf_senha   = st.text_input("Confirmar senha *", type="password", key="cad_pw2")

    st.caption("Campos com * são obrigatórios.")

    if st.button("Criar minha conta →", use_container_width=True, type="primary", key="btn_cadastro"):
        erros = []
        if not nome.strip():       erros.append("Nome é obrigatório.")
        if not meta_desc.strip():  erros.append("A descrição da meta é obrigatória.")
        if meta_valor <= 0:        erros.append("O valor da meta deve ser maior que zero.")
        if not meta_prazo.strip(): erros.append("O prazo da meta é obrigatório.")
        if not new_username.strip(): erros.append("Usuário é obrigatório.")
        if not new_senha:          erros.append("Senha é obrigatória.")
        if new_senha != conf_senha: erros.append("As senhas não coincidem.")
        if username_existe(new_username.strip()): erros.append("Este nome de usuário já está em uso.")

        if erros:
            for e in erros:
                st.error(e)
            return

        dados_perfil = {
            "nome": nome.strip(),
            "idade": int(idade),
            "profissao": profissao.strip(),
            "renda_mensal": float(renda),
            "perfil_investidor": perfil_inv,
            "patrimonio_total": 0.0,
            "reserva_emergencia_atual": 0.0,
            "aceita_risco": aceita_risco,
            "metas": [
                {
                    "meta": meta_desc.strip(),
                    "valor_necessario": float(meta_valor),
                    "prazo": meta_prazo.strip(),
                }
            ],
        }

        sucesso = cadastrar_usuario(new_username.strip(), new_senha, dados_perfil)
        if sucesso:
            st.success("Conta criada com sucesso! Entrando...")
            st.session_state.logged_in = True
            st.session_state.current_user = dados_perfil
            st.session_state.historico_chat = []
            st.session_state.interaction_id = None
            st.rerun()
        else:
            st.error("Não foi possível criar a conta. Tente novamente.")


def pagina_login():
    """Renderiza a tela de autenticação centralizada."""
    _, col_mid, _ = st.columns([1, 1.6, 1])

    with col_mid:
        st.markdown(
            """
            <div style="text-align:center; padding: 2rem 0 1rem;">
                <span style="font-size:3.5rem;">💰</span>
                <h1 style="margin:0.4rem 0 0.2rem; font-size:2rem; font-weight:700;">Val</h1>
                <p style="color:gray; font-size:1rem; margin:0;">
                    Seu educador financeiro pessoal
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        tab_entrar, tab_cadastro = st.tabs(["🔑  Entrar", "✨  Criar conta"])

        with tab_entrar:
            _form_login()

        with tab_cadastro:
            _form_cadastro()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                             TELA DE CHAT                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@st.dialog("✏️ Editar Perfil")
def _dialog_editar_perfil():
    perfil = st.session_state.current_user
    
    st.markdown("#### Dados Profissionais")
    nova_prof = st.text_input("Profissão", value=perfil.get("profissao", ""))
    nova_renda = st.number_input("Renda mensal (R$)", value=float(perfil.get("renda_mensal", 0.0)), step=100.0)
    
    st.markdown("#### Meta Principal")
    metas = perfil.get("metas", [])
    meta_atual = metas[0] if metas else {}
    nova_meta_desc = st.text_input("Descrição da meta", value=meta_atual.get("meta", ""))
    nova_meta_valor = st.number_input("Valor alvo (R$)", value=float(meta_atual.get("valor_necessario", 0.0)), step=100.0)
    nova_meta_prazo = st.text_input("Prazo (AAAA-MM)", value=meta_atual.get("prazo", ""))
    
    if st.button("Salvar alterações", type="primary", use_container_width=True):
        if not nova_meta_desc.strip() or nova_meta_valor <= 0 or not nova_meta_prazo.strip():
            st.error("A meta financeira (descrição, valor e prazo) deve ser preenchida corretamente.")
            return

        novos_dados = {
            "profissao": nova_prof.strip(),
            "renda_mensal": nova_renda,
            "metas": [
                {
                    "meta": nova_meta_desc.strip(),
                    "valor_necessario": nova_meta_valor,
                    "prazo": nova_meta_prazo.strip()
                }
            ]
        }
        perfil_id = perfil.get("perfil_id")
        if perfil_id and atualizar_dados_perfil(perfil_id, novos_dados):
            # Atualiza o estado da sessão local
            st.session_state.current_user.update(novos_dados)
            st.rerun()
        else:
            st.error("Erro ao salvar perfil.")

def pagina_chat():
    """Renderiza a interface de chat com o Val."""
    perfil = st.session_state.current_user
    nome_curto = perfil.get("nome", "Usuário").split()[0]

    # ── Sidebar ─────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"### 👤 {perfil.get('nome')}")
        st.caption(perfil.get("profissao", ""))

        st.markdown("---")

        st.markdown(
            f"**Renda mensal** &nbsp; {_fmt_brl(perfil.get('renda_mensal'))}"
        )
        badge = _perfil_badge(perfil.get("perfil_investidor", ""))
        st.markdown(
            f"**Perfil** &nbsp; {badge} "
            f"{perfil.get('perfil_investidor', '—').replace('_', ' ').title()}"
        )
        st.markdown(
            f"**Patrimônio** &nbsp; {_fmt_brl(perfil.get('patrimonio_total'))}"
        )
        st.markdown(
            f"**Reserva emergência** &nbsp; {_fmt_brl(perfil.get('reserva_emergencia_atual'))}"
        )



        metas = perfil.get("metas", [])
        if metas:
            meta = metas[0]
            valor_necessario = meta.get("valor_necessario", 0)
            patrimonio       = perfil.get("patrimonio_total", 0)
            st.markdown("**📌 Meta**")
            st.caption(
                f"{meta.get('meta', '—')}  \n"
                f"{_fmt_brl(meta.get('valor_necessario'))} até {meta.get('prazo', '—')}"
            )
            if valor_necessario > 0:
                progresso = min(patrimonio / valor_necessario, 1.0)
                st.progress(progresso, text=f"{progresso*100:.0f}% concluído")

        # ── Gastos mensais do CSV ──────────────────────────────────
        _, _, gastos_csv = carregar_dados(perfil.get("nome", ""))
        if gastos_csv:
            renda        = perfil.get("renda_mensal", 0)
            total_gastos = sum(gastos_csv.values())
            saldo_livre  = renda - total_gastos
            st.markdown("---")
            st.markdown("**💸 Gastos mensais**")

            # Gráfico de barras por categoria
            df_gastos = pd.DataFrame(
                {"Categoria": [k.replace("_", " ").title() for k in gastos_csv],
                 "Valor (R$)": list(gastos_csv.values())}
            ).sort_values("Valor (R$)", ascending=False)
            st.bar_chart(df_gastos.set_index("Categoria"), use_container_width=True, height=180)

            st.caption(
                f"🔴 Total: {_fmt_brl(total_gastos)} &nbsp;&nbsp; "
                f"🟢 Saldo livre: {_fmt_brl(saldo_livre)}"
            )

        st.markdown("---")

        if st.button("✏️ Editar perfil", use_container_width=True):
            _dialog_editar_perfil()

        if st.button("🔄 Nova conversa", use_container_width=True):
            st.session_state.historico_chat = []
            st.session_state.interaction_id = None
            st.rerun()

        if st.button("🚪 Sair", use_container_width=True):
            _logout()

    # ── Cabeçalho ───────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.25rem;">
            <span style="font-size:2rem;">💰</span>
            <div>
                <h2 style="margin:0; font-size:1.5rem; font-weight:700;">Val</h2>
                <p style="margin:0; font-size:0.85rem; color:gray;">
                    Educador financeiro · Olá, {nome_curto}! Pergunte à vontade 🌱
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Histórico de mensagens ───────────────────────────────────────────────
    for mensagem in st.session_state.historico_chat:
        avatar = "💰" if mensagem["role"] == "assistant" else "👤"
        st.chat_message(mensagem["role"], avatar=avatar).write(mensagem["content"])

    # ── Entrada do usuário ───────────────────────────────────────────────────
    user_input = st.chat_input("Pergunte algo sobre suas finanças...")

    if user_input:
        # Exibe e salva mensagem do usuário
        st.chat_message("user", avatar="👤").write(user_input)
        st.session_state.historico_chat.append({"role": "user", "content": user_input})

        # Chama o agente
        with st.spinner("Val está pensando..."):
            try:
                resposta_val, novo_id = gerar_resposta_val(
                    mensagem_usuario=user_input,
                    perfil=st.session_state.current_user,
                    interaction_id=st.session_state.interaction_id,
                )
                # Escapa cifrão para evitar interpretação como LaTeX
                resposta_val = resposta_val.replace("$", "\\$")

                st.session_state.interaction_id = novo_id
                
                # Tenta extrair aporte (dinheiro guardado) silenciosamente
                aporte = extrair_aporte(user_input)
                if aporte and aporte > 0:
                    perfil_id = st.session_state.current_user.get("perfil_id")
                    if perfil_id and adicionar_patrimonio(perfil_id, aporte):
                        # Atualiza sessão
                        st.session_state.current_user["patrimonio_total"] = st.session_state.current_user.get("patrimonio_total", 0.0) + aporte
                        st.session_state.current_user["reserva_emergencia_atual"] = st.session_state.current_user.get("reserva_emergencia_atual", 0.0) + aporte
                        st.toast(f"🎉 Parabéns! Patrimônio atualizado: +{_fmt_brl(aporte)}", icon="💰")
                        # Forçamos o rerun no final para atualizar a sidebar
                        st.session_state._forcar_rerun_apos_msg = True

                st.chat_message("assistant", avatar="💰").write(resposta_val)
                st.session_state.historico_chat.append(
                    {"role": "assistant", "content": resposta_val}
                )

                # ── Persistência de gastos no CSV ───────────────────────────────
                # Só tenta extrair se o usuário ainda não tem dados no CSV.
                # Assim evitamos sobrescrever dados reais existentes.
                nome_usuario = st.session_state.current_user.get("nome", "")
                _, _, gastos_csv = carregar_dados(nome_usuario)
                if not gastos_csv:
                    gastos_extraidos = extrair_gastos(user_input)
                    if gastos_extraidos:
                        salvar_gastos_no_csv(nome_usuario, gastos_extraidos)
                        st.toast(
                            "💾 Gastos salvos! Val já tem seus dados para as próximas conversôes.",
                            icon="✅",
                        )
            except Exception as e:
                st.error(f"Ops, ocorreu um erro de conexão: {e}")

        # Se a extração alterou a sessão (aporte), remontamos a barra lateral
        if st.session_state.get("_forcar_rerun_apos_msg"):
            st.session_state._forcar_rerun_apos_msg = False
            st.rerun()

# ── Roteador principal ──────────────────────────────────────────────────────
if st.session_state.logged_in:
    pagina_chat()
else:
    pagina_login()