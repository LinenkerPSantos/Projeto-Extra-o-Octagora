from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config

router = APIRouter(prefix="/api/settings", tags=["settings"])


class CredentialsUpdate(BaseModel):
    user: Optional[str] = None
    password: Optional[str] = None


@router.get("/credentials")
def get_credentials():
    """Usuário cadastrado e se há senha definida, por região. Nunca retorna a senha."""
    return config.get_credentials_status()


@router.put("/credentials/{regiao}")
def update_credentials(regiao: str, body: CredentialsUpdate):
    regiao = regiao.upper()
    if regiao not in config.REGIOES:
        raise HTTPException(status_code=404, detail=f"Região '{regiao}' não encontrada. Use uma de {config.REGIOES}.")

    user = (body.user or "").strip()
    password = (body.password or "").strip()
    if not user and not password:
        raise HTTPException(status_code=400, detail="Informe usuário e/ou senha para salvar.")

    config.save_credentials(regiao, user=user, password=password)
    return {"message": f"Credenciais de {regiao} atualizadas."}
