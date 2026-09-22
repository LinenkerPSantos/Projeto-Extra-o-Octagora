from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel

from services.job_runner import SCRIPTS, REGIOES, SP_ONLY_SCRIPTS, run_range_script, get_state, get_logs, clear_logs

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class JobStartRange(BaseModel):
    date_start: Optional[str] = None
    date_end: Optional[str] = None


def _yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")


@router.post("/start-range/{regiao}/{script_key}")
def start_range_job(regiao: str, script_key: str, body: JobStartRange, background_tasks: BackgroundTasks):
    regiao = regiao.upper()
    if regiao not in REGIOES:
        raise HTTPException(status_code=404, detail=f"Região '{regiao}' não encontrada. Use uma de {REGIOES}.")
    if script_key not in SCRIPTS:
        raise HTTPException(status_code=404, detail=f"Script '{script_key}' não encontrado.")
    if script_key in SP_ONLY_SCRIPTS and regiao != "SP":
        raise HTTPException(status_code=400, detail="Este relatório está disponível apenas para SP.")
    job_id = f"{regiao}:{script_key}"
    state = get_state()
    if state.get(job_id, {}).get("status") == "running":
        raise HTTPException(status_code=409, detail="Script já em execução.")
    date_start = body.date_start or _yesterday()
    date_end = body.date_end or date_start
    background_tasks.add_task(run_range_script, regiao, script_key, date_start, date_end)
    return {"message": f"'{job_id}' iniciado para {date_start} a {date_end}."}


@router.get("/status")
def get_status():
    return {"scripts": get_state(), "logs": get_logs()}


@router.delete("/logs")
def delete_logs():
    clear_logs()
    return {"message": "Logs limpos."}
