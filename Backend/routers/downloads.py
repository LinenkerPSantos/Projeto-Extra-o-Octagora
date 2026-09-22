import re
from io import BytesIO
from pathlib import Path
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

from config import DOWNLOADS_DIR, REGIOES

router = APIRouter(prefix="/api/downloads", tags=["downloads"])

_PREFIX_MAP = {
    "sumario":           "BaseGeral",
    "detalhe":           "BaseDetalhado",
    "evento":            "EventoUsuario",
    "nps_agencias":      "NPS_Agencias",
    "nps_especializado": "NPS_Especializado",
    "nps_video":         "NPS_Video",
}

_CONSOLIDATE_SHEETS = {
    "sumario":           "Sumario",
    "detalhe":           "Detalhe",
    "evento":            "EventoUsuario",
    "nps_agencias":      "NPS_Agencias",
    "nps_especializado": "NPS_Especializado",
    "nps_video":         "NPS_Video",
}


def _classify(name: str) -> str:
    for prefix, label in _PREFIX_MAP.items():
        if name.startswith(prefix):
            return label
    return "outro"


def _extract_date(stem: str) -> str | None:
    m = re.search(r"(\d{8})$", stem)
    if m:
        d = m.group(1)
        return f"{d[0:2]}/{d[2:4]}/{d[4:8]}"
    return None


def _validate_regiao(regiao: str) -> str:
    regiao = regiao.upper()
    if regiao not in REGIOES:
        raise HTTPException(status_code=404, detail=f"Região '{regiao}' não encontrada. Use uma de {REGIOES}.")
    return regiao


def _regiao_dir(regiao: str) -> Path:
    d = DOWNLOADS_DIR / regiao
    d.mkdir(parents=True, exist_ok=True)
    return d


def _collect_for_consolidation(folder: Path, prefix: str) -> list[tuple[Path, str]]:
    items = []
    for f in folder.glob(f"{prefix}*.csv"):
        date_str = _extract_date(f.stem)
        if date_str:
            items.append((f, date_str))
    items.sort(key=lambda item: item[1][6:] + item[1][3:5] + item[1][0:2])
    return items


def _read_csv(f: Path, date_str: str, regiao: str = None) -> pd.DataFrame:
    df = pd.read_csv(f, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False)
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
    if regiao:
        df.insert(0, "Regiao", regiao)
    df.insert(0 if not regiao else 1, "MesBase", date_str)
    return df


def _build_consolidado(folder: Path) -> BytesIO | None:
    sheets = {}
    for prefix, sheet_name in _CONSOLIDATE_SHEETS.items():
        dfs = [_read_csv(f, date_str) for f, date_str in _collect_for_consolidation(folder, prefix)]
        if dfs:
            sheets[sheet_name] = pd.concat(dfs, ignore_index=True)

    if not sheets:
        return None

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    buffer.seek(0)
    return buffer


# ── Por região — SP e ES são processados de forma totalmente independente,
# não existe mais consolidação cruzada entre regiões. ──────────────────────

@router.get("/{regiao}/consolidado")
def get_consolidado(regiao: str):
    regiao = _validate_regiao(regiao)
    buffer = _build_consolidado(_regiao_dir(regiao))
    if buffer is None:
        raise HTTPException(status_code=404, detail="Nenhum arquivo sumario/detalhe encontrado para consolidar.")

    return StreamingResponse(
        buffer,
        media_type="application/vnd.ms-excel",
        headers={"Content-Disposition": f'attachment; filename="Consolidado_{regiao}.xls"'},
    )


@router.get("/{regiao}/{filename}/download")
def download_file(regiao: str, filename: str):
    """Baixa o CSV bruto (fora do consolidado em Excel)."""
    regiao = _validate_regiao(regiao)
    if "/" in filename or "\\" in filename or filename != Path(filename).name:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    target = _regiao_dir(regiao) / filename
    if not target.is_file() or target.suffix.lower() != ".csv":
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    return FileResponse(target, filename=target.name)


@router.get("/{regiao}")
def list_downloads(regiao: str):
    regiao = _validate_regiao(regiao)
    folder = _regiao_dir(regiao)

    files = []
    dates_set: set = set()

    matched = sorted(folder.glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)
    for f in matched:
        date_str = _extract_date(f.stem)
        if date_str:
            dates_set.add(date_str)
        files.append({
            "name":     f.name,
            "type":     _classify(f.stem),
            "date":     date_str,
            "size_kb":  round(f.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })

    return {"files": files, "dates": sorted(dates_set, reverse=True)}


@router.delete("/{regiao}")
def delete_all_downloads(regiao: str):
    regiao = _validate_regiao(regiao)
    folder = _regiao_dir(regiao)

    deleted = 0
    for f in folder.glob("*.csv"):
        f.unlink()
        deleted += 1

    return {"message": f"{deleted} arquivo(s) excluído(s).", "deleted": deleted}


@router.delete("/{regiao}/{filename}")
def delete_download(regiao: str, filename: str):
    regiao = _validate_regiao(regiao)
    if "/" in filename or "\\" in filename or filename != Path(filename).name:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido.")

    target = _regiao_dir(regiao) / filename
    if not target.is_file() or target.suffix.lower() != ".csv":
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    target.unlink()
    return {"message": f"Arquivo '{filename}' excluído."}
