from typing import Any

from fastapi import Depends, HTTPException, Request, status

from core.config import get_settings


def get_current_session(request: Request) -> dict[str, Any]:
    session = getattr(request.state, "session", None)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Autenticação necessária."},
        )
    return session


def require_perfil(*perfis: str):
    def dependency(session: dict[str, Any] = Depends(get_current_session)) -> dict[str, Any]:
        if session.get("perfil") not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Perfil sem permissão para esta ação."},
            )
        return session

    return dependency