from datetime import datetime, timezone

from fastapi import HTTPException, status

import repositories.admin_repository as admin_repo
import repositories.solicitacao_repository as solicitacao_repo

_TRANSICOES_SOLICITACAO = {
    "RECEBIDA": ["EM_ANALISE"],
    "EM_ANALISE": ["CONFIRMADA", "RECUSADA_SEM_COBERTURA"],
    "CONFIRMADA": ["EM_ATENDIMENTO"],
    "EM_ATENDIMENTO": ["PRESTADOR_ACIONADO", "CONCLUIDA"],
    "PRESTADOR_ACIONADO": ["CONCLUIDA"],
    "RECUSADA_SEM_COBERTURA": [],
    "CONCLUIDA": [],
}

_TRANSICOES_ASSISTENCIA = {
    "INCLUIDA": ["AGUARDANDO_PRESTADOR", "PRESTADOR_ACIONADO", "REMOVIDA", "CANCELADA"],
    "AGUARDANDO_PRESTADOR": ["PRESTADOR_ACIONADO", "REMOVIDA", "CANCELADA"],
    "PRESTADOR_ACIONADO": ["EM_DESLOCAMENTO", "CONCLUIDA", "CANCELADA"],
    "EM_DESLOCAMENTO": ["CONCLUIDA", "CANCELADA"],
    "CONCLUIDA": [],
    "CANCELADA": [],
    "REMOVIDA": [],
}

_MUTABLE_REQUEST_STATUSES = ("CONFIRMADA", "EM_ATENDIMENTO", "PRESTADOR_ACIONADO")
_STATUS_TERMINAIS_SOLICITACAO = ("CONCLUIDA", "RECUSADA_SEM_COBERTURA")
_STATUS_TERMINAIS_ASSISTENCIA = ("CONCLUIDA", "CANCELADA", "REMOVIDA")
_STATUS_COMENTARIO_OBRIGATORIO = ("PRESTADOR_ACIONADO", "EM_DESLOCAMENTO", "CONCLUIDA")


class AdminError(HTTPException):
    def __init__(self, code: str, message: str, fields: list | None = None,
                 http_code: int = 422, current: dict | None = None):
        detail: dict = {"code": code, "message": message}
        if fields:
            detail["fields"] = fields
        if current:
            detail["current"] = current
        super().__init__(status_code=http_code, detail=detail)


def _agora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(value)


def _date_iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    return str(value)[:10]


def _seguradora_ids(session: dict) -> set[int]:
    ids = set()
    for item in session.get("seguradoras") or []:
        if item.get("id_pj"):
            ids.add(int(item["id_pj"]))
    seguradora = session.get("seguradora")
    if isinstance(seguradora, dict) and seguradora.get("id_pj"):
        ids.add(int(seguradora["id_pj"]))
    if session.get("fk_seguradora"):
        ids.add(int(session["fk_seguradora"]))
    return ids


def _require_analyst(session: dict) -> set[int]:
    if session.get("perfil") != "ANALISTA":
        raise AdminError("AUTH_FORBIDDEN", "Sua sessão administrativa não está disponível.", http_code=403)
    ids = _seguradora_ids(session)
    if not ids:
        raise AdminError("AUTH_FORBIDDEN", "Sua sessão administrativa não está disponível.", http_code=403)
    return ids


def _require_visible(row: dict, session: dict) -> None:
    if not row or row.get("fk_seguradora_id") not in _seguradora_ids(session):
        raise AdminError("REQUEST_NOT_FOUND", "Solicitação não encontrada.", http_code=404)


def _require_responsavel(row: dict, session: dict) -> None:
    if row.get("fk_analista_responsavel") != session.get("id_usuario"):
        raise AdminError(
            "AUTH_FORBIDDEN",
            "Solicitação não está sob sua responsabilidade.",
            http_code=403,
        )


def _require_version(row: dict, version: int) -> None:
    if row.get("version") != version:
        raise AdminError(
            "REQUEST_VERSION_CONFLICT",
            "A solicitação mudou desde que você abriu esta tela. Revise os dados atuais.",
            http_code=409,
            current={"status": row.get("status_codigo"), "version": row.get("version")},
        )


def _cliente_dto(row: dict) -> dict:
    if row.get("isJuridico"):
        return {
            "id_pessoa": row.get("fk_pessoa_id") or row["fk_pessoa"],
            "tipo_pessoa": "JURIDICA",
            "razao_social": row.get("cliente_razao_social"),
            "nome_fantasia": row.get("cliente_nome_fantasia"),
            "cnpj_mascarado": row.get("cliente_cnpj"),
        }
    return {
        "id_pessoa": row.get("fk_pessoa_id") or row["fk_pessoa"],
        "tipo_pessoa": "FISICA",
        "nome": row.get("cliente_nome"),
        "cpf_mascarado": row.get("cliente_cpf"),
    }


def _veiculo_dto(row: dict) -> dict:
    return {
        "id_veiculo": row.get("fk_veiculo_id") or row["id_veiculo"],
        "marca": row.get("marca"),
        "modelo": row.get("modelo"),
        "versao": row.get("versao"),
        "ano_fabricacao": row.get("ano_fabricado"),
        "ano_modelo": row.get("ano_modelo"),
        "placa_mascarada": row.get("placa_mascarada"),
        "blindado": bool(row.get("blindado")),
    }


def _apolice_dto(row: dict) -> dict | None:
    apolice = solicitacao_repo.apolice_resumo_by_id(row["fk_apolice_id"])
    if not apolice:
        return None
    return {
        "id_apolice": row["fk_apolice_id"],
        "numero_apolice_mascarado": apolice.get("numero_apolice_mascarado"),
        "data_inicio": _date_iso(apolice.get("data_inicio")),
        "data_fim": _date_iso(apolice.get("data_fim")),
        "status": apolice.get("apolice_status"),
    }


def _seguradora_dto(row: dict) -> dict:
    return {
        "id_pj": row.get("fk_seguradora_id"),
        "nome_fantasia": row.get("seguradora_nome"),
    }


def _ocorrencia_dto(row: dict) -> dict:
    return {
        "id_tipo_ocorrencia": row.get("fk_tipo_ocorrencia_id"),
        "codigo": row.get("ocorrencia_codigo"),
        "nome": row.get("ocorrencia_nome"),
        "descricao": row.get("ocorrencia_descricao"),
    }


def _local_dto(row: dict) -> dict:
    return {
        "endereco": row.get("endereco"),
        "numero_local": row.get("numero_local"),
        "cidade": row.get("cidade"),
        "estado": row.get("estado"),
        "ponto_referencia": row.get("ponto_referencia"),
    }


def _analista_dto(row: dict) -> dict | None:
    if not row.get("fk_analista_responsavel"):
        return None
    return {
        "id_usuario": row.get("fk_analista_responsavel"),
        "nome_exibicao": row.get("analista_nome"),
    }


def _solicitacao_core_dto(row: dict) -> dict:
    return {
        "id_solicitacao": row["id_solicitacao"],
        "id_solicitacao_cliente": row.get("id_solicitacao_cliente"),
        "numero_solicitacao": row.get("numero_solicitacao"),
        "descricao_evento": row.get("descricao_evento"),
        "possui_feridos": bool(row.get("possui_feridos")),
        "risco_imediato": bool(row.get("risco_imediato")),
        "prioridade": row.get("prioridade"),
        "local": _local_dto(row),
        "status": row.get("status_codigo"),
        "data_criacao_cliente": _iso(row.get("data_criacao_cliente")),
        "data_recebimento": _iso(row.get("data_recebimento")),
        "data_decisao": _iso(row.get("data_decisao")),
        "motivo_recusa": row.get("motivo_recusa"),
        "version": row.get("version"),
        "analista": _analista_dto(row),
    }


def _aggregate_dto(row: dict) -> dict:
    return {
        **_solicitacao_core_dto(row),
        "cliente": _cliente_dto(row),
        "apolice": _apolice_dto(row),
        "veiculo": _veiculo_dto(row),
        "seguradora": _seguradora_dto(row),
        "ocorrencia": _ocorrencia_dto(row),
    }


def _assistencia_dto(row: dict) -> dict:
    responsavel = (
        {"id_usuario": row.get("id_usuario"), "nome_exibicao": row.get("nome_exibicao")}
        if row.get("id_usuario")
        else None
    )
    return {
        "id_solicitacao_assistencia": row["id_solicitacao_assistencia"],
        "tipo": {
            "id_tipo_assistencia": row.get("id_tipo_assistencia"),
            "codigo": row.get("tipo_codigo"),
            "nome": row.get("tipo_nome"),
        },
        "status": row.get("status"),
        "comentario": row.get("comentario"),
        "responsavel": responsavel,
        "data_inclusao": _iso(row.get("data_inclusao")),
        "data_atualizacao": _iso(row.get("data_atualizacao")),
        "version": row.get("version"),
    }


def _pergunta_dto(row: dict) -> dict:
    return {
        "id_pergunta": row["id_pergunta"],
        "origem": row.get("origem"),
        "tipo": row.get("tipo"),
        "status": row.get("status_codigo"),
        "necessita_taxi": row.get("necessita_taxi"),
        "quantidade_passageiros": row.get("qtd_passageiros"),
        "necessita_acessibilidade": row.get("necessita_acessibilidade"),
        "quantidade_criancas": row.get("qtd_criancas"),
        "quantidade_animais": row.get("qtd_animais"),
        "bagagem": row.get("bagagem"),
        "observacoes": row.get("observacoes"),
        "data_criacao": _iso(row.get("data_criacao")),
        "data_resposta": _iso(row.get("data_resposta")),
        "version": row.get("version"),
    }


def _historico_dto(row: dict) -> dict:
    if row.get("fk_usuario_responsavel"):
        responsavel = {
            "id_usuario": row["fk_usuario_responsavel"],
            "nome_exibicao": row.get("nome_exibicao"),
        }
    else:
        responsavel = {
            "id_usuario": None,
            "nome_exibicao": row.get("nome_responsavel") or "Sistema",
        }
    return {
        "id_historico": row["id_historico"],
        "status": row["status"],
        "data_status": _iso(row.get("data_status")),
        "responsavel": responsavel,
        "comentario": row["comentario"],
    }


def _tipo_assistencia_dto(row: dict) -> dict:
    return {
        "id_tipo_assistencia": row["id_tipo_assistencia"],
        "codigo": row["codigo"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "ativo": bool(row["ativo"]),
    }


def _paginate(items: list, page: int, page_size: int) -> dict:
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    total_items = len(items)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    start = (page - 1) * page_size
    return {
        "items": items[start:start + page_size],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }


def get_dashboard(session: dict) -> dict:
    ids = _require_analyst(session)
    rows = admin_repo.find_solicitacoes(list(ids))
    aberta = lambda s: s not in _STATUS_TERMINAIS_SOLICITACAO
    metricas = {
        "criticas_abertas": sum(
            1 for r in rows if r.get("prioridade") == "CRITICA" and aberta(r.get("status_codigo"))
        ),
        "aguardando_analise": sum(1 for r in rows if r.get("status_codigo") == "RECEBIDA"),
        "confirmadas_em_atendimento": sum(
            1 for r in rows if r.get("status_codigo") in ("CONFIRMADA", "EM_ATENDIMENTO")
        ),
        "prestadores_acionados": sum(
            1 for r in rows if r.get("status_codigo") == "PRESTADOR_ACIONADO"
        ),
        "concluidas": sum(1 for r in rows if r.get("status_codigo") == "CONCLUIDA"),
        "recusadas_sem_cobertura": sum(
            1 for r in rows if r.get("status_codigo") == "RECUSADA_SEM_COBERTURA"
        ),
    }
    return {
        "metricas": metricas,
        "fila_prioritaria": {"items": [_aggregate_dto(r) for r in rows[:5]]},
    }


def list_solicitacoes(
    session: dict,
    *,
    status_filter: str | None = None,
    prioridade: str | None = None,
    tipo_ocorrencia_id: int | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
    numero_solicitacao: str | None = None,
    pessoa: str | None = None,
    placa: str | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    ids = _require_analyst(session)
    filters = {
        "status": status_filter,
        "prioridade": prioridade,
        "tipo_ocorrencia_id": tipo_ocorrencia_id,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "numero_solicitacao": numero_solicitacao,
        "pessoa": pessoa,
        "placa": placa,
    }
    rows = admin_repo.find_solicitacoes(list(ids), filters, sort=sort)
    items = [_aggregate_dto(r) for r in rows]
    return _paginate(items, page, page_size)


def get_detalhe(session: dict, solicitacao_id: int) -> dict:
    ids = _require_analyst(session)
    row = solicitacao_repo.solicitacao_by_id(solicitacao_id)
    _require_visible(row, session)

    return {
        "solicitacao": _solicitacao_core_dto(row),
        "cliente": _cliente_dto(row),
        "apolice": _apolice_dto(row),
        "veiculo": _veiculo_dto(row),
        "seguradora": _seguradora_dto(row),
        "ocorrencia": _ocorrencia_dto(row),
        "analista": _analista_dto(row),
        "assistencias": [
            _assistencia_dto(a) for a in solicitacao_repo.assistencias_by_solicitacao(solicitacao_id)
        ],
        "perguntas": [
            _pergunta_dto(p) for p in solicitacao_repo.perguntas_by_solicitacao(solicitacao_id)
        ],
        "historico": [
            _historico_dto(h) for h in solicitacao_repo.historico_by_solicitacao(solicitacao_id)
        ],
        "tipos_assistencia_disponiveis": [
            _tipo_assistencia_dto(t) for t in admin_repo.tipos_assistencia_ativos()
        ],
    }


def list_tipos_assistencia(session: dict) -> dict:
    _require_analyst(session)
    return {
        "items": [_tipo_assistencia_dto(t) for t in admin_repo.tipos_assistencia_ativos()],
    }


def _base_solicitacao(session: dict, solicitacao_id: int, responsavel: bool = True) -> dict:
    row = solicitacao_repo.solicitacao_by_id(solicitacao_id)
    _require_visible(row, session)
    if responsavel:
        _require_responsavel(row, session)
    return row


def _executar_transicao(
    session: dict,
    solicitacao_id: int,
    version: int,
    to_status: str,
    comentario: str,
    *,
    set_decisao: bool = False,
    motivo_recusa: str | None = None,
    release_policy: bool = False,
    responsavel: bool = True,
) -> dict:
    row = _base_solicitacao(session, solicitacao_id, responsavel=responsavel)
    if to_status not in _TRANSICOES_SOLICITACAO.get(row.get("status_codigo"), ()):
        raise AdminError(
            "REQUEST_INVALID_STATUS_TRANSITION",
            "Esta ação não está disponível no estado atual da solicitação.",
        )

    ok = admin_repo.transicionar_solicitacao(
        id_solicitacao=solicitacao_id,
        from_status_codigo=row["status_codigo"],
        to_status_codigo=to_status,
        version=version,
        id_usuario=session["id_usuario"],
        nome_exibicao=session.get("nome_exibicao") or "Analista",
        comentario=comentario,
        now=_agora(),
        set_decisao=set_decisao,
        motivo_recusa=motivo_recusa,
        release_policy=release_policy,
        fk_apolice=row.get("fk_apolice_id"),
    )
    if not ok:
        raise AdminError(
            "REQUEST_VERSION_CONFLICT",
            "A solicitação mudou desde que você abriu esta tela. Revise os dados atuais.",
            http_code=409,
            current={"status": row.get("status_codigo"), "version": row.get("version")},
        )
    return {"solicitacao": _aggregate_dto(solicitacao_repo.solicitacao_by_id(solicitacao_id))}


def assumir(session: dict, solicitacao_id: int, version: int) -> dict:
    _require_analyst(session)
    return _executar_transicao(
        session,
        solicitacao_id,
        version,
        "EM_ANALISE",
        "Solicitação assumida para análise.",
        responsavel=False,
    )


def confirmar(session: dict, solicitacao_id: int, version: int, comentario: str | None) -> dict:
    _require_analyst(session)
    return _executar_transicao(
        session,
        solicitacao_id,
        version,
        "CONFIRMADA",
        (comentario or "").strip() or "Cobertura confirmada manualmente pelo analista.",
        set_decisao=True,
        motivo_recusa=None,
    )


def recusar(session: dict, solicitacao_id: int, version: int, motivo_recusa: str) -> dict:
    _require_analyst(session)
    motivo = (motivo_recusa or "").strip()
    if not motivo:
        raise AdminError(
            "REQUEST_REJECTION_REASON_REQUIRED",
            "Informe o motivo da ausência de cobertura.",
            fields=[{"field": "motivo_recusa", "message": "Campo obrigatório."}],
        )
    return _executar_transicao(
        session,
        solicitacao_id,
        version,
        "RECUSADA_SEM_COBERTURA",
        f"Recusa por ausência de cobertura: {motivo}",
        set_decisao=True,
        motivo_recusa=motivo,
        release_policy=True,
    )


def iniciar_atendimento(session: dict, solicitacao_id: int, version: int, comentario: str | None) -> dict:
    _require_analyst(session)
    return _executar_transicao(
        session,
        solicitacao_id,
        version,
        "EM_ATENDIMENTO",
        (comentario or "").strip() or "Atendimento iniciado.",
    )


def registrar_prestador_acionado(session: dict, solicitacao_id: int, version: int, comentario: str | None) -> dict:
    _require_analyst(session)
    return _executar_transicao(
        session,
        solicitacao_id,
        version,
        "PRESTADOR_ACIONADO",
        (comentario or "").strip() or "Prestador acionado manualmente.",
    )


def concluir(session: dict, solicitacao_id: int, version: int, comentario: str | None) -> dict:
    _require_analyst(session)
    row = _base_solicitacao(session, solicitacao_id)
    if "CONCLUIDA" not in _TRANSICOES_SOLICITACAO.get(row.get("status_codigo"), ()):
        raise AdminError(
            "REQUEST_INVALID_STATUS_TRANSITION",
            "Esta ação não está disponível no estado atual da solicitação.",
        )
    assistencias = solicitacao_repo.assistencias_by_solicitacao(solicitacao_id)
    if not assistencias or not all(a.get("status") in _STATUS_TERMINAIS_ASSISTENCIA for a in assistencias):
        raise AdminError(
            "REQUEST_ASSISTANCES_PENDING",
            "Conclua ou encerre todas as assistências antes de concluir a solicitação.",
        )
    ok = admin_repo.transicionar_solicitacao(
        id_solicitacao=solicitacao_id,
        from_status_codigo=row["status_codigo"],
        to_status_codigo="CONCLUIDA",
        version=version,
        id_usuario=session["id_usuario"],
        nome_exibicao=session.get("nome_exibicao") or "Analista",
        comentario=(comentario or "").strip() or "Atendimento concluído.",
        now=_agora(),
        set_decisao=False,
        release_policy=True,
        fk_apolice=row.get("fk_apolice_id"),
    )
    if not ok:
        raise AdminError(
            "REQUEST_VERSION_CONFLICT",
            "A solicitação mudou desde que você abriu esta tela. Revise os dados atuais.",
            http_code=409,
            current={"status": row.get("status_codigo"), "version": row.get("version")},
        )
    return {"solicitacao": _aggregate_dto(solicitacao_repo.solicitacao_by_id(solicitacao_id))}


def adicionar_assistencia(session: dict, solicitacao_id: int, body) -> dict:
    _require_analyst(session)
    row = _base_solicitacao(session, solicitacao_id)
    _require_version(row, body.request_version)

    if row.get("status_codigo") not in _MUTABLE_REQUEST_STATUSES:
        raise AdminError(
            "REQUEST_INVALID_STATUS_TRANSITION",
            "Não é possível incluir assistência neste estado.",
        )

    tipo = admin_repo.tipo_assistencia_by_id(body.tipo_assistencia_id)
    if not tipo or not tipo.get("ativo"):
        raise AdminError(
            "VALIDATION_ERROR",
            "Selecione uma assistência ativa.",
            fields=[{"field": "tipo_assistencia_id", "message": "Campo obrigatório."}],
        )

    comentario = (body.comentario or "").strip()
    if row.get("status_codigo") == "PRESTADOR_ACIONADO" and not comentario:
        raise AdminError(
            "ASSISTANCE_COMMENT_REQUIRED",
            "Informe um comentário para alterações após o acionamento.",
        )

    resultado = admin_repo.add_assistencia(
        id_solicitacao=solicitacao_id,
        id_usuario=session["id_usuario"],
        nome_exibicao=session.get("nome_exibicao") or "Analista",
        tipo_assistencia_id=body.tipo_assistencia_id,
        comentario=comentario,
        now=_agora(),
    )

    pergunta = (
        solicitacao_repo.pergunta_by_id(resultado["pergunta_id"])
        if resultado.get("pergunta_id")
        else None
    )
    return {
        "assistencia": _assistencia_dto(resultado["assistencia"]),
        "pergunta_criada": _pergunta_dto(pergunta) if pergunta else None,
        "solicitacao": _aggregate_dto(solicitacao_repo.solicitacao_by_id(solicitacao_id)),
    }


def atualizar_assistencia(session: dict, assistance_id: int, body) -> dict:
    _require_analyst(session)
    assistencia = admin_repo.assistencia_by_id(assistance_id)
    if not assistencia:
        raise AdminError("ASSISTANCE_NOT_FOUND", "Assistência não encontrada.", http_code=404)

    row = _base_solicitacao(session, assistencia["fk_solicitacao"])
    if assistencia.get("version") != body.version:
        raise AdminError(
            "ASSISTANCE_VERSION_CONFLICT",
            "A assistência foi atualizada por outra operação.",
            http_code=409,
            current={"status": assistencia.get("status"), "version": assistencia.get("version")},
        )
    if body.status not in _TRANSICOES_ASSISTENCIA.get(assistencia.get("status"), ()):
        raise AdminError(
            "ASSISTANCE_INVALID_STATUS_TRANSITION",
            "Esta transição de assistência não é permitida.",
        )

    comentario = (body.comentario or "").strip()
    if body.status in _STATUS_COMENTARIO_OBRIGATORIO and not comentario:
        raise AdminError(
            "ASSISTANCE_COMMENT_REQUIRED",
            "Informe os dados recebidos do prestador para esta atualização.",
        )

    atualizada = admin_repo.update_assistencia_status(
        assistance_id=assistance_id,
        status_destino=body.status,
        comentario=comentario,
        version=body.version,
        id_usuario=session["id_usuario"],
        nome_exibicao=session.get("nome_exibicao") or "Analista",
        now=_agora(),
        fk_solicitacao=row["id_solicitacao"],
        request_status_codigo=row["status_codigo"],
    )
    return {"assistencia": _assistencia_dto({**assistencia, **atualizada})}