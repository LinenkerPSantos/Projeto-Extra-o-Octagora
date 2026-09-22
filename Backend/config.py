import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Console do Windows usa cp1252 por padrão e não codifica caracteres como ✓/✗
# usados nos logs de extração — força stdout/stderr para UTF-8 quando disponível.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(Path(__file__).parent / ".env")

BASE_DIR = Path(__file__).parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

OCTAGORA_URL = "https://adm.octagora.com/Edp"

# Uma única aplicação Octagora atende as duas regiões — a diferença é o
# ambiente selecionado no login (dropdown IdArea) e as credenciais.
REGIOES = ("ES", "SP")

_OCTAGORA_ENV = {
    "ES": "Agências - ES",
    "SP": "Agências - SP",
}

# ── Credenciais configuráveis pela aba "Configurações" do frontend ─────────
# Guardadas em Backend/credentials.json (fora do git — ver .gitignore) para
# poderem ser cadastradas/alteradas em tempo de execução, sem precisar editar
# o .env nem reiniciar o servidor. O .env (OCTAGORA_ES_USER/PASS etc.) continua
# funcionando como valor padrão/fallback enquanto nada for salvo pela UI.
CREDENTIALS_FILE = BASE_DIR / "credentials.json"


def _load_credentials_file() -> dict:
    if CREDENTIALS_FILE.exists():
        try:
            return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_credentials(regiao: str, user: str = None, password: str = None):
    """Atualiza usuário e/ou senha de uma região no credentials.json.
    Campos não informados (None ou string vazia) preservam o valor atual —
    permite trocar só a senha sem reescrever o usuário, e vice-versa."""
    regiao = (regiao or "").upper()
    if regiao not in REGIOES:
        raise ValueError(f"Região inválida: {regiao!r}. Use uma de {REGIOES}.")

    data = _load_credentials_file()
    entry = data.get(regiao, {})
    if user:
        entry["user"] = user
    if password:
        entry["password"] = password
    data[regiao] = entry
    CREDENTIALS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_credentials_status() -> dict:
    """Retorna, por região, o usuário cadastrado e se há senha definida —
    nunca a senha em si (nem para exibição no frontend)."""
    data = _load_credentials_file()
    status = {}
    for regiao in REGIOES:
        entry = data.get(regiao, {})
        user = entry.get("user") or os.getenv(f"OCTAGORA_{regiao}_USER", "")
        has_password = bool(entry.get("password") or os.getenv(f"OCTAGORA_{regiao}_PASS", ""))
        status[regiao] = {"user": user, "has_password": has_password}
    return status


def get_regiao(regiao: str) -> dict:
    """Retorna env/usuário/senha/pasta de downloads para a região (ES ou SP).
    Usuário/senha vêm do credentials.json (cadastrados pela UI); se ausentes,
    cai para as variáveis OCTAGORA_{REGIAO}_USER/PASS do .env."""
    regiao = (regiao or "").upper()
    if regiao not in REGIOES:
        raise ValueError(f"Região inválida: {regiao!r}. Use uma de {REGIOES}.")
    downloads_dir = DOWNLOADS_DIR / regiao
    downloads_dir.mkdir(parents=True, exist_ok=True)

    entry = _load_credentials_file().get(regiao, {})
    user = entry.get("user") or os.getenv(f"OCTAGORA_{regiao}_USER", "")
    password = entry.get("password") or os.getenv(f"OCTAGORA_{regiao}_PASS", "")

    return {
        "env": _OCTAGORA_ENV[regiao],
        "user": user,
        "password": password,
        "downloads_dir": downloads_dir,
    }


# Modo headless do Chrome (sem janela visível). Defina OCTAGORA_HEADLESS=0 no
# .env (ou na variável de ambiente) para ver o navegador durante a extração.
OCTAGORA_HEADLESS = os.getenv("OCTAGORA_HEADLESS", "true").strip().lower() not in ("0", "false", "no")

CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")]
