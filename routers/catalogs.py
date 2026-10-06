from fastapi import APIRouter, Depends, Query
from typing import Any

from core.deps import get_current_session
import services.catalog_service as catalog_service

router = APIRouter(tags=["catalogos"])


@router.get("/tipos-ocorrencia")
def tipos_ocorrencia(
    ativo: bool | None = Query(default=None),
    _session: dict[str, Any] = Depends(get_current_session),
) -> dict:
    return catalog_service.list_occurrence_types(ativo)


@router.get("/configuracoes/publicas")
def configuracoes_publicas(_session: dict[str, Any] = Depends(get_current_session)) -> dict:
    return catalog_service.get_public_configurations()