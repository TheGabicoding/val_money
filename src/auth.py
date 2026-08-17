import os
import json
import hashlib
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.json")
PERFIS_FILE = os.path.join(DATA_DIR, "perfil_usuario.json")


# ── Utilitários internos ────────────────────────────────────────────────────

def hash_senha(senha: str) -> str:
    """Retorna o hash SHA-256 da senha fornecida."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def _carregar_usuarios() -> list:
    if not os.path.exists(USUARIOS_FILE):
        return []
    with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar_usuarios(usuarios: list) -> None:
    with open(USUARIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)


def _carregar_perfis() -> list:
    with open(PERFIS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar_perfis(perfis: list) -> None:
    with open(PERFIS_FILE, "w", encoding="utf-8") as f:
        json.dump(perfis, f, indent=2, ensure_ascii=False)


# ── Seed de usuários de teste ───────────────────────────────────────────────

def inicializar_usuarios() -> None:
    """
    Cria o arquivo usuarios.json com os logins de teste caso ainda não exista.
    Também adiciona `perfil_id` a cada perfil existente no perfil_usuario.json.
    """
    perfis = _carregar_perfis()

    # IDs e usernames fixos para os 5 perfis de teste
    seeds = [
        {"perfil_id": "perfil_joao",    "username": "joao123"},
        {"perfil_id": "perfil_ana",     "username": "ana123"},
        {"perfil_id": "perfil_carlos",  "username": "carlos123"},
        {"perfil_id": "perfil_lucas",   "username": "lucas123"},
        {"perfil_id": "perfil_mariana", "username": "mariana123"},
    ]

    # Garante que cada perfil existente tenha um perfil_id
    perfis_alterados = False
    for i, perfil in enumerate(perfis):
        if "perfil_id" not in perfil:
            perfil["perfil_id"] = seeds[i]["perfil_id"] if i < len(seeds) else str(uuid.uuid4())
            perfis_alterados = True

    if perfis_alterados:
        _salvar_perfis(perfis)

    # Só cria o arquivo de usuários se não existir
    if os.path.exists(USUARIOS_FILE):
        return

    senha_hash = hash_senha("senha123")
    usuarios = [
        {
            "username": s["username"],
            "senha_hash": senha_hash,
            "perfil_id": s["perfil_id"],
        }
        for s in seeds
    ]
    _salvar_usuarios(usuarios)


# ── API pública ─────────────────────────────────────────────────────────────

def carregar_perfil(perfil_id: str) -> dict | None:
    """Retorna apenas o perfil com o `perfil_id` informado, ou None."""
    for perfil in _carregar_perfis():
        if perfil.get("perfil_id") == perfil_id:
            return perfil
    return None


def verificar_login(username: str, senha: str) -> dict | None:
    """
    Valida as credenciais. Retorna o dicionário de perfil do usuário
    autenticado, ou None se inválido.
    """
    senha_hash = hash_senha(senha)
    for u in _carregar_usuarios():
        if u["username"] == username and u["senha_hash"] == senha_hash:
            return carregar_perfil(u["perfil_id"])
    return None


def username_existe(username: str) -> bool:
    return any(u["username"] == username for u in _carregar_usuarios())


def atualizar_dados_perfil(perfil_id: str, novos_dados: dict) -> bool:
    """
    Atualiza os dados de um perfil existente.
    """
    perfis = _carregar_perfis()
    for perfil in perfis:
        if perfil.get("perfil_id") == perfil_id:
            perfil.update(novos_dados)
            _salvar_perfis(perfis)
            return True
    return False


def cadastrar_usuario(username: str, senha: str, dados_perfil: dict) -> bool:
    """
    Registra um novo usuário. Salva o perfil em perfil_usuario.json e as
    credenciais em usuarios.json. Retorna True em caso de sucesso.
    """
    if username_existe(username):
        return False

    perfil_id = str(uuid.uuid4())
    dados_perfil["perfil_id"] = perfil_id

    perfis = _carregar_perfis()
    perfis.append(dados_perfil)
    _salvar_perfis(perfis)

    usuarios = _carregar_usuarios()
    usuarios.append(
        {
            "username": username,
            "senha_hash": hash_senha(senha),
            "perfil_id": perfil_id,
        }
    )
    _salvar_usuarios(usuarios)
    return True

def adicionar_patrimonio(perfil_id: str, valor_adicional: float) -> bool:
    """
    Soma o valor informado ao patrimônio total e à reserva de emergência do usuário.
    """
    perfis = _carregar_perfis()
    for perfil in perfis:
        if perfil.get("perfil_id") == perfil_id:
            patrimonio_atual = perfil.get("patrimonio_total", 0.0)
            reserva_atual = perfil.get("reserva_emergencia_atual", 0.0)
            
            perfil["patrimonio_total"] = patrimonio_atual + valor_adicional
            perfil["reserva_emergencia_atual"] = reserva_atual + valor_adicional
            
            _salvar_perfis(perfis)
            return True
    return False
