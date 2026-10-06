from fastapi import APIRouter, Depends, Response, status
from typing import Any

from core.deps import get_current_session
from schemas.auth import (
    AuthEnvelope,
    AnalistaLoginRequest,
    ClienteLoginRequest,
    SessaoInfo,
)
import services.auth_service as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/clientes/login", response_model=AuthEnvelope)
def login_cliente(dados: ClienteLoginRequest) -> AuthEnvelope:
    return auth_service.login_client(dados.cpf, dados.senha)


@router.post("/analistas/login", response_model=AuthEnvelope)
def login_analista(dados: AnalistaLoginRequest) -> AuthEnvelope:
    return auth_service.login_analyst(dados.login, dados.senha)


@router.get("/me")
def me(session: dict[str, Any] = Depends(get_current_session)) -> dict[str, Any]:
    return {"session": session}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)