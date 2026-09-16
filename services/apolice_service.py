from datetime import datetime, timezone

from fastapi import HTTPException, status

import repositories.apolice_repository as apolice_repo
import repositories.client_repository as client_repo

_STATUS_APOLICE_ATIVOS = ("ATIVA", "SUSPENSA", "INATIVA")


class ApoliceError(HTTPException):
    def __init__(self, code: str, message: str, http_code: int = 422, current=None):
        detail = {"code": code, "message": message}
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
        raise ApoliceError("AUTH_FORBIDDEN", "Sua sessão administrativa não está disponível.", http_code=403)
    ids = _seguradora_ids(session)
    if not ids:
        raise ApoliceError("AUTH_FORBIDDEN", "Sua sessão administrativa não está disponível.", http_code=403)
    return ids


def _require_visible(row: dict, session: dict) -> None:
    if not row or row.get("fk_segurado_id") not in _seguradora_ids(session):
        raise ApoliceError("POLICY_NOT_FOUND", "Apólice não encontrada.", http_code=404)


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


def _cliente_dto(row: dict) -> dict:
    if row.get("isJuridico"):
        return {
            "id_pessoa": row.get("fk_pessoa_id"),
            "tipo_pessoa": "JURIDICA",
            "razao_social": row.get("cliente_razao_social"),
            "nome_fantasia": row.get("cliente_nome_fantasia"),
            "cnpj_mascarado": row.get("cliente_cnpj"),
        }
    return {
        "id_pessoa": row.get("fk_pessoa_id"),
        "tipo_pessoa": "FISICA",
        "nome": row.get("cliente_nome"),
        "cpf_mascarado": row.get("cliente_cpf"),
    }


def _veiculo_dto(row: dict) -> dict:
    return {
        "id_veiculo": row.get("fk_veiculo_id"),
        "marca": row.get("marca"),
        "modelo": row.get("modelo"),
        "versao": row.get("veiculo_versao"),
        "ano_fabricacao": row.get("ano_fabricado"),
        "ano_modelo": row.get("ano_modelo"),
        "placa_mascarada": row.get("placa_mascarada"),
        "blindado": bool(row.get("blindado")),
    }


def _apolice_dto(row: dict) -> dict:
    return {
        "id_apolice": row.get("id_apolice"),
        "numero_apolice": row.get("numero_apolice"),
        "numero_apolice_mascarado": row.get("numero_apolice_mascarado"),
        "data_inicio": _date_iso(row.get("data_inicio")),
        "data_fim": _date_iso(row.get("data_fim")),
        "cobertura": row.get("cobertura"),
        "assistencia": row.get("assistencia"),
        "endosso": row.get("endosso"),
        "perfil": row.get("perfil"),
        "status": row.get("apolice_status"),
        "versao": row.get("versao"),
        "possui_solicitacao_ativa": bool(row.get("possui_solicitacao_ativa")),
        "cliente": _cliente_dto(row),
        "seguradora": {
            "id_pj": row.get("fk_segurado_id"),
            "nome_fantasia": row.get("seguradora_nome_fantasia"),
        },
        "veiculo": _veiculo_dto(row),
        "local_pernoite": row.get("local_pernoite"),
        "forma_pagamento": row.get("forma_pagamento"),
    }


def _contatos_dto(pessoa_id: int) -> list[dict]:
    return [
        {
            "tipo": c["tipo_contato"],
            "rotulo": c["rotulo"],
            "valor": c["valor_contato"],
            "principal": bool(c["principal"]),
        }
        for c in client_repo.contatos_by_pessoa(pessoa_id)
    ]


def _detalhe_dto(row: dict) -> dict:
    dto = _apolice_dto(row)
    dto["cliente"]["contatos"] = _contatos_dto(row.get("fk_pessoa_id"))
    dto["seguradora"]["contatos"] = _contatos_dto(row.get("fk_segurado_id"))
    return dto


def list_apolices(
    session: dict,
    *,
    status_filter: str | None = None,
    numero_apolice: str | None = None,
    pessoa: str | None = None,
    placa: str | None = None,
    seguradora: int | None = None,
    sort: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    ids = _require_analyst(session)
    filters = {
        "status": status_filter,
        "numero_apolice": numero_apolice,
        "pessoa": pessoa,
        "placa": placa,
        "seguradora": seguradora,
    }
    rows = apolice_repo.find_apolices(list(ids), filters=filters, sort=sort)
    items = [_apolice_dto(r) for r in rows]
    return _paginate(items, page, page_size)


def get_detalhe(session: dict, apolice_id: int) -> dict:
    _require_analyst(session)
    row = apolice_repo.apolice_by_id(apolice_id)
    _require_visible(row, session)
    return {"apolice": _detalhe_dto(row)}


def criar_apolice(session: dict, body) -> dict:
    ids = _require_analyst(session)
    if body.fk_segurado not in ids:
        raise ApoliceError(
            "AUTH_FORBIDDEN",
            "A seguradora informada não pertence à sua sessão.",
            http_code=403,
        )
    if body.data_fim < body.data_inicio:
        raise ApoliceError(
            "VALIDATION_ERROR",
            "A data de fim deve ser posterior à data de início.",
        )
    row = apolice_repo.create_apolice(data=body.model_dump(), now=_agora())
    return {"apolice": _apolice_dto(row)}


def atualizar_apolice(session: dict, apolice_id: int, body) -> dict:
    _require_analyst(session)
    current = apolice_repo.apolice_by_id(apolice_id)
    _require_visible(current, session)
    if current.get("versao") != body.version:
        raise ApoliceError(
            "POLICY_VERSION_CONFLICT",
            "A apólice mudou desde que você abriu esta tela. Revise os dados atuais.",
            http_code=409,
            current={"status": current.get("apolice_status"), "versao": current.get("versao")},
        )
    data_inicio = body.data_inicio if body.data_inicio is not None else current.get("data_inicio")
    data_fim = body.data_fim if body.data_fim is not None else current.get("data_fim")
    if data_fim and data_inicio and data_fim < data_inicio:
        raise ApoliceError(
            "VALIDATION_ERROR",
            "A data de fim deve ser posterior à data de início.",
        )

    patch = {
        "numero_apolice": body.numero_apolice if body.numero_apolice is not None else current["numero_apolice"],
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "cobertura": body.cobertura if body.cobertura is not None else current.get("cobertura"),
        "assistencia": body.assistencia if body.assistencia is not None else current.get("assistencia"),
        "endosso": body.endosso if body.endosso is not None else current.get("endosso"),
        "perfil": body.perfil if body.perfil is not None else current.get("perfil"),
    }
    row = apolice_repo.update_apolice(apolice_id=apolice_id, version=body.version, patch=patch, now=_agora())
    if not row:
        raise ApoliceError(
            "POLICY_VERSION_CONFLICT",
            "A apólice mudou desde que você abriu esta tela. Revise os dados atuais.",
            http_code=409,
            current={"status": current.get("apolice_status"), "versao": current.get("versao")},
        )
    return {"apolice": _apolice_dto(row)}


def alterar_status_apolice(session: dict, apolice_id: int, body) -> dict:
    _require_analyst(session)
    if body.status not in _STATUS_APOLICE_ATIVOS:
        raise ApoliceError("INVALID_POLICY_STATUS", "Status de apólice inválido.", http_code=409)
    current = apolice_repo.apolice_by_id(apolice_id)
    _require_visible(current, session)
    if current.get("versao") != body.version:
        raise ApoliceError(
            "POLICY_VERSION_CONFLICT",
            "A apólice mudou desde que você abriu esta tela. Revise os dados atuais.",
            http_code=409,
            current={"status": current.get("apolice_status"), "versao": current.get("versao")},
        )
    if current.get("apolice_status") == body.status:
        raise ApoliceError(
            "INVALID_POLICY_STATUS",
            f"A apólice já está {body.status}.",
            http_code=409,
        )
    row = apolice_repo.update_apolice_status(
        apolice_id=apolice_id,
        version=body.version,
        to_status=body.status,
        now=_agora(),
    )
    if not row:
        raise ApoliceError(
            "POLICY_VERSION_CONFLICT",
            "A apólice mudou desde que você abriu esta tela. Revise os dados atuais.",
            http_code=409,
            current={"status": current.get("apolice_status"), "versao": current.get("versao")},
        )
    return {"apolice": _apolice_dto(row)}