from fastapi import APIRouter, Depends, Query

from core.deps import require_perfil
from schemas.admin import (
    AssistenciaAddRequest,
    AssistenciaStatusUpdateRequest,
    ConfirmarRequest,
    OperacaoRequest,
    RecusarRequest,
    VersionRequest,
)
import services.admin_service as admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(session: dict = Depends(require_perfil("ANALISTA"))) -> dict:
    return admin_service.get_dashboard(session)


@router.get("/solicitacoes")
def solicitacoes(
    status: str | None = Query(default=None),
    prioridade: str | None = Query(default=None),
    tipo_ocorrencia_id: int | None = Query(default=None),
    data_inicio: str | None = Query(default=None),
    data_fim: str | None = Query(default=None),
    numero_solicitacao: str | None = Query(default=None),
    pessoa: str | None = Query(default=None),
    placa: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.list_solicitacoes(
        session,
        status_filter=status,
        prioridade=prioridade,
        tipo_ocorrencia_id=tipo_ocorrencia_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        numero_solicitacao=numero_solicitacao,
        pessoa=pessoa,
        placa=placa,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/solicitacoes/{solicitacao_id}")
def detalhe_solicitacao(
    solicitacao_id: int,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.get_detalhe(session, solicitacao_id)


@router.get("/tipos-assistencia")
def tipos_assistencia(session: dict = Depends(require_perfil("ANALISTA"))) -> dict:
    return admin_service.list_tipos_assistencia(session)


@router.post("/solicitacoes/{solicitacao_id}/assumir")
def assumir(
    solicitacao_id: int,
    body: VersionRequest,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.assumir(session, solicitacao_id, body.version)


@router.post("/solicitacoes/{solicitacao_id}/confirmar")
def confirmar(
    solicitacao_id: int,
    body: ConfirmarRequest,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.confirmar(session, solicitacao_id, body.version, body.comentario)


@router.post("/solicitacoes/{solicitacao_id}/recusar")
def recusar(
    solicitacao_id: int,
    body: RecusarRequest,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.recusar(session, solicitacao_id, body.version, body.motivo_recusa)


@router.post("/solicitacoes/{solicitacao_id}/iniciar-atendimento")
def iniciar_atendimento(
    solicitacao_id: int,
    body: OperacaoRequest,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.iniciar_atendimento(session, solicitacao_id, body.version, body.comentario)


@router.post("/solicitacoes/{solicitacao_id}/registrar-prestador-acionado")
def registrar_prestador_acionado(
    solicitacao_id: int,
    body: OperacaoRequest,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.registrar_prestador_acionado(session, solicitacao_id, body.version, body.comentario)


@router.post("/solicitacoes/{solicitacao_id}/concluir")
def concluir(
    solicitacao_id: int,
    body: OperacaoRequest,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.concluir(session, solicitacao_id, body.version, body.comentario)


@router.post("/solicitacoes/{solicitacao_id}/assistencias", status_code=201)
def adicionar_assistencia(
    solicitacao_id: int,
    body: AssistenciaAddRequest,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.adicionar_assistencia(session, solicitacao_id, body)


@router.patch("/solicitacao-assistencias/{assistance_id}")
def atualizar_assistencia(
    assistance_id: int,
    body: AssistenciaStatusUpdateRequest,
    session: dict = Depends(require_perfil("ANALISTA")),
) -> dict:
    return admin_service.atualizar_assistencia(session, assistance_id, body)