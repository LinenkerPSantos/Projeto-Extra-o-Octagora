"""
Responsável por disparar os scripts Python de extração como subprocessos
e rastrear o estado de cada job (por região) em memória.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_ROOT.parent

# ── Mapa de scripts disponíveis ────────────────────────────────────────────────
SCRIPTS: dict[str, str] = {
    "tempoprotocolo-sumario": "scripts/tempoprotocolo_sumario.py",
    "tempoprotocolo-detalhe": "scripts/tempoprotocolo_detalhe.py",
    "extrair-tudo":           "scripts/extrair_tudo.py",
    "evento-usuario":         "scripts/evento_usuario.py",
    "nps-agencias":           "scripts/formulario_nps_agencias.py",
    "nps-especializado":      "scripts/formulario_nps_especializado.py",
    "nps-video":              "scripts/formulario_nps_video.py",
}

# Relatórios que só existem no ambiente "Agências - SP" do Octagora (não têm
# formulário/menu equivalente cadastrado em "Agências - ES").
SP_ONLY_SCRIPTS = {"nps-agencias", "nps-especializado", "nps-video"}

REGIOES = ("ES", "SP")


def _job_id(regiao: str, script_key: str) -> str:
    return f"{regiao}:{script_key}"


# ── Estado em memória ──────────────────────────────────────────────────────────
_state: dict[str, dict] = {
    _job_id(regiao, key): {"status": "idle", "date": None, "started_at": None, "finished_at": None}
    for regiao in REGIOES
    for key in SCRIPTS
}
_logs: list[str] = []
_MAX_LOGS = 1000

PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"


def get_state() -> dict:
    return _state.copy()


def get_logs() -> list[str]:
    return list(_logs)


def clear_logs():
    _logs.clear()


def _add_log(msg: str):
    _logs.append(msg)
    if len(_logs) > _MAX_LOGS:
        del _logs[: len(_logs) - _MAX_LOGS]
    print(msg)


def _run_subprocess(args: list[str]) -> int:
    """Executa o subprocesso e transmite stdout/stderr para _logs linha a linha."""
    proc = subprocess.Popen(
        args,
        cwd=str(BACKEND_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env={**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
    )

    for line in proc.stdout:
        line = line.rstrip("\n")
        if line.strip():
            _add_log(line)

    proc.wait()
    return proc.returncode


def run_range_script(regiao: str, script_key: str, date_start: str, date_end: str):
    regiao = (regiao or "").upper()
    job_id = _job_id(regiao, script_key)
    script_rel = SCRIPTS[script_key]
    script_abs = BACKEND_ROOT / script_rel

    label = f"{date_start} a {date_end}" if date_start != date_end else date_start
    _state[job_id] = {
        "status": "running",
        "date": label,
        "started_at": datetime.now().isoformat(),
        "finished_at": None,
    }

    _add_log(f"\n{'-' * 60}")
    _add_log(f"[{job_id}] Iniciando para {label}")

    if not PYTHON.exists():
        msg = f"[{job_id}] [ERRO] Python não encontrado em {PYTHON}. Rode install.bat primeiro."
        _add_log(msg)
        _state[job_id]["status"] = "error"
        _state[job_id]["finished_at"] = datetime.now().isoformat()
        return

    returncode = _run_subprocess(
        [str(PYTHON), "-u", "-X", "utf8", str(script_abs),
         "--regiao", regiao, "--date-start", date_start, "--date-end", date_end]
    )

    status = "success" if returncode == 0 else "error"
    _state[job_id]["status"] = status
    _state[job_id]["finished_at"] = datetime.now().isoformat()
    _add_log(f"[{job_id}] {'✓ Concluído.' if status == 'success' else f'✗ Falhou (exit {returncode}).'}")
