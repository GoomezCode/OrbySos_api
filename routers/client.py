from fastapi import APIRouter, Depends, Header, Query

from core.deps import require_perfil
from schemas.client import PerguntaRespostaRequest, SolicitacaoCreateRequest
import services.client_service as client_service
import services.taxi_question_service as taxi_question_service

router = APIRouter(tags=["clientes"])


@router.get("/clientes/me")
def cliente_me(session: dict = Depends(require_perfil("CLIENTE"))) -> dict:
    return client_service.get_perfil(session)


@router.get("/clientes/me/apolices")
def cliente_apolices(
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: dict = Depends(require_perfil("CLIENTE")),
) -> dict:
    return client_service.list_apolices(session, status=status, page=page, page_size=page_size)


@router.post("/solicitacoes", status_code=201)
def criar_solicitacao(
    body: SolicitacaoCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    session: dict = Depends(require_perfil("CLIENTE")),
) -> dict:
    return client_service.criar_solicitacao(session, body, idempotency_key or "")


@router.get("/clientes/me/solicitacoes")
def cliente_solicitacoes(
    status: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: dict = Depends(require_perfil("CLIENTE")),
) -> dict:
    return client_service.list_solicitacoes(session, status, active_only, page, page_size)


@router.get("/solicitacoes/{solicitacao_id}")
def detalhe_solicitacao(
    solicitacao_id: int,
    session: dict = Depends(require_perfil("CLIENTE")),
) -> dict:
    return client_service.get_detalhe_solicitacao(session, solicitacao_id)


@router.post("/perguntas/{pergunta_id}/resposta")
def responder_pergunta(
    pergunta_id: int,
    body: PerguntaRespostaRequest,
    session: dict = Depends(require_perfil("CLIENTE")),
) -> dict:
    return taxi_question_service.responder_pergunta(session, pergunta_id, body)