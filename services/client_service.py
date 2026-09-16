from datetime import datetime, timezone

from fastapi import HTTPException, status

import repositories.client_repository as client_repo
import repositories.solicitacao_repository as solicitacao_repo

_NOTIFICACAO_CONFLITO = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail={
        "code": "POLICY_ACTIVE_REQUEST_EXISTS",
        "message": "Esta apólice já possui uma solicitação em andamento.",
    },
)


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


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _cliente_dto(row: dict) -> dict:
    if row.get("isJuridico"):
        return {
            "id_pessoa": row["fk_pessoa"],
            "tipo_pessoa": "JURIDICA",
            "razao_social": row.get("cliente_razao_social"),
            "nome_fantasia": row.get("cliente_nome_fantasia"),
            "cnpj_mascarado": row.get("cliente_cnpj"),
        }
    return {
        "id_pessoa": row["fk_pessoa"],
        "tipo_pessoa": "FISICA",
        "nome": row.get("cliente_nome"),
        "cpf_mascarado": row.get("cliente_cpf"),
    }


def _veiculo_dto(row: dict) -> dict:
    return {
        "id_veiculo": row["id_veiculo"],
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


def _solicitacao_dto(row: dict) -> dict:
    return {
        "id_solicitacao": row["id_solicitacao"],
        "id_solicitacao_cliente": row.get("id_solicitacao_cliente"),
        "numero_solicitacao": row.get("numero_solicitacao"),
        "descricao_evento": row.get("descricao_evento"),
        "possui_feridos": bool(row.get("possui_feridos")),
        "risco_imediato": bool(row.get("risco_imediato")),
        "prioridade": row.get("prioridade"),
        "local": {
            "endereco": row.get("endereco"),
            "numero_local": row.get("numero_local"),
            "cidade": row.get("cidade"),
            "estado": row.get("estado"),
            "ponto_referencia": row.get("ponto_referencia"),
        },
        "status": row.get("status_codigo"),
        "data_criacao_cliente": _iso(row.get("data_criacao_cliente")),
        "data_recebimento": _iso(row.get("data_recebimento")),
        "data_decisao": _iso(row.get("data_decisao")),
        "motivo_recusa": row.get("motivo_recusa"),
        "version": row.get("version"),
    }


def get_perfil(session: dict) -> dict:
    pessoa_id = session["id_pessoa"]
    person = client_repo.person_by_id(pessoa_id)
    if not person:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado.")

    contatos_dto = [
        {
            "tipo": c["tipo_contato"],
            "valor_mascarado": c["valor_contato"],
            "principal": bool(c["principal"]),
        }
        for c in client_repo.contatos_by_pessoa(pessoa_id)
    ]

    if person.get("isJuridico"):
        pj = client_repo.pessoa_juridica_by_id(pessoa_id) or {}
        return {
            "id_pessoa": pessoa_id,
            "tipo_pessoa": "JURIDICA",
            "razao_social": pj.get("razao_social"),
            "nome_fantasia": pj.get("nome_fantasia"),
            "cnpj_mascarado": pj.get("cnpj_mascarado"),
            "contatos": contatos_dto,
        }

    pf = client_repo.pessoa_fisica_by_id(pessoa_id) or {}
    return {
        "id_pessoa": pessoa_id,
        "tipo_pessoa": "FISICA",
        "nome": pf.get("nome"),
        "cpf_mascarado": pf.get("cpf_mascarado"),
        "data_nascimento": _date_iso(pf.get("data_nascimento")),
        "contatos": contatos_dto,
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


def list_apolices(session: dict, status: str | None = None, page: int = 1, page_size: int = 20) -> dict:
    pessoa_id = session["id_pessoa"]
    person = client_repo.person_by_id(pessoa_id) or {}
    cliente_info = {"fk_pessoa": pessoa_id, "isJuridico": person.get("isJuridico", 0)}
    if person.get("isJuridico"):
        pj = client_repo.pessoa_juridica_by_id(pessoa_id) or {}
        cliente_info["cliente_razao_social"] = pj.get("razao_social")
        cliente_info["cliente_nome_fantasia"] = pj.get("nome_fantasia")
        cliente_info["cliente_cnpj"] = pj.get("cnpj_mascarado")
    else:
        pf = client_repo.pessoa_fisica_by_id(pessoa_id) or {}
        cliente_info["cliente_nome"] = pf.get("nome")
        cliente_info["cliente_cpf"] = pf.get("cpf_mascarado")

    items = []
    for p in client_repo.policies_by_pessoa(pessoa_id):
        if status and p.get("apolice_status") != status:
            continue
        ativa = client_repo.active_request_by_policy(p["id_apolice"])
        seguradora = client_repo.pessoa_juridica_by_id(p["fk_segurado"]) or {}
        seguradora_contatos = [
            {
                "tipo": c["tipo_contato"],
                "rotulo": c.get("rotulo"),
                "valor": c["valor_contato"],
            }
            for c in client_repo.contatos_by_pessoa(p["fk_segurado"])
        ]
        items.append({
            "id_apolice": p["id_apolice"],
            "numero_apolice_mascarado": p.get("numero_apolice_mascarado"),
            "data_inicio": _date_iso(p.get("data_inicio")),
            "data_fim": _date_iso(p.get("data_fim")),
            "status": p.get("apolice_status"),
            "possui_solicitacao_ativa": bool(ativa),
            "cliente": _cliente_dto(cliente_info),
            "seguradora": {
                "id_pj": p.get("fk_segurado"),
                "nome_fantasia": seguradora.get("nome_fantasia"),
                "contatos": seguradora_contatos,
            },
            "veiculo": {
                "id_veiculo": p.get("fk_veiculo"),
                "marca": p.get("marca"),
                "modelo": p.get("modelo"),
                "ano_fabricacao": p.get("ano_fabricado"),
                "ano_modelo": p.get("ano_modelo"),
                "placa_mascarada": p.get("placa_mascarada"),
            },
            "solicitacao_ativa": {
                "id_solicitacao": ativa["id_solicitacao"],
                "numero_solicitacao": ativa["numero_solicitacao"],
                "status": ativa["status_codigo"],
                "prioridade": ativa["prioridade"],
                "data_recebimento": _iso(ativa["data_recebimento"]),
            } if ativa else None,
        })
    return _paginate(items, page, page_size)


def list_solicitacoes(session: dict, status_filter: str | None = None,
                      active_only: bool = False, page: int = 1, page_size: int = 20) -> dict:
    pessoa_id = session["id_pessoa"]
    rows = client_repo.requests_by_pessoa(pessoa_id, status=status_filter, active_only=active_only)
    items = [
        {
            "id_solicitacao": r["id_solicitacao"],
            "numero_solicitacao": r["numero_solicitacao"],
            "status": r["status_codigo"],
            "prioridade": r["prioridade"],
            "descricao_evento": r["descricao_evento"],
            "possui_feridos": bool(r["possui_feridos"]),
            "risco_imediato": bool(r["risco_imediato"]),
            "data_recebimento": _iso(r["data_recebimento"]),
            "data_decisao": _iso(r["data_decisao"]),
            "motivo_recusa": r["motivo_recusa"],
            "version": r["version"],
            "veiculo": {
                "id_veiculo": r["id_veiculo"],
                "marca": r["marca"],
                "modelo": r["modelo"],
                "ano_modelo": r["ano_modelo"],
                "placa_mascarada": r["placa_mascarada"],
            },
            "ocorrencia": {
                "id_tipo_ocorrencia": r["id_ocorrencia"],
                "codigo": r["codigo"],
                "nome": r["nome"],
            },
        }
        for r in rows
    ]
    return _paginate(items, page, page_size)


def _next_numero() -> str:
    seq = client_repo.next_solicitacao_seq()
    return f"ORB-{datetime.now(timezone.utc).year}-{seq:06d}"


def criar_solicitacao(session: dict, body, idempotency_key: str) -> dict:
    pessoa_id = session["id_pessoa"]

    if body.id_solicitacao_cliente != idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "REQUEST_IDEMPOTENCY_CONFLICT",
                "message": "Idempotency-Key e id_solicitacao_cliente devem ser iguais.",
            },
        )

    duplicada = client_repo.request_by_client_uuid(body.id_solicitacao_cliente)
    if duplicada:
        raise _NOTIFICACAO_CONFLITO

    occurrence = client_repo.occurrence_by_id(body.tipo_ocorrencia_id)
    if not occurrence or not occurrence.get("ativo"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "REQUEST_VALIDATION_ERROR", "message": "Tipo de ocorrência inválido."},
        )

    policy = client_repo.policy_by_id_for_pessoa(body.apolice_id, pessoa_id)
    if not policy or policy.get("apolice_status") != "ATIVA":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "REQUEST_VALIDATION_ERROR", "message": "Selecione uma apólice ativa."},
        )

    if client_repo.active_request_by_policy(policy["id_apolice"]):
        raise _NOTIFICACAO_CONFLITO

    prioridade = "CRITICA" if body.possui_feridos or body.risco_imediato else "NORMAL"
    numero = _next_numero()
    agora = datetime.now(timezone.utc).replace(tzinfo=None)

    id_solicitacao = solicitacao_repo.create_solicitacao(
        id_solicitacao_cliente=body.id_solicitacao_cliente,
        protocolo_solicitacao=numero,
        numero_solicitacao=numero,
        descricao_evento=body.descricao_evento,
        possui_feridos=body.possui_feridos,
        risco_imediato=body.risco_imediato,
        prioridade=prioridade,
        data_criacao_cliente=_parse_dt(body.data_criacao_cliente),
        data_recebimento=agora,
        fk_apolice=policy["id_apolice"],
        fk_pessoa=pessoa_id,
        fk_seguradora=policy["fk_segurado"],
        fk_veiculo=policy["fk_veiculo"],
        fk_tipo_ocorrencia=occurrence["id_ocorrencia"],
        endereco=body.local.endereco,
        numero_local=body.local.numero_local,
        cidade=body.local.cidade,
        estado=body.local.estado,
        ponto_referencia=body.local.ponto_referencia,
        nome_responsavel=session.get("nome_exibicao"),
    )
    return get_detalhe_solicitacao(session, id_solicitacao)


def get_detalhe_solicitacao(session: dict, solicitacao_id: int) -> dict:
    row = solicitacao_repo.solicitacao_by_id(solicitacao_id)
    if not row or row["fk_pessoa"] != session["id_pessoa"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitação não encontrada.")

    assistencias = [
        {
            "id_solicitacao_assistencia": a["id_solicitacao_assistencia"],
            "tipo": {
                "id_tipo_assistencia": a["id_tipo_assistencia"],
                "codigo": a["tipo_codigo"],
                "nome": a["tipo_nome"],
            },
            "status": a["status"],
            "comentario": a["comentario"],
            "responsavel": (
                {"id_usuario": a["id_usuario"], "nome_exibicao": a["nome_exibicao"]}
                if a.get("id_usuario")
                else None
            ),
            "data_inclusao": _iso(a["data_inclusao"]),
            "data_atualizacao": _iso(a["data_atualizacao"]),
            "version": a["version"],
        }
        for a in solicitacao_repo.assistencias_by_solicitacao(solicitacao_id)
    ]

    perguntas = [
        {
            "id_pergunta": p["id_pergunta"],
            "origem": p["origem"],
            "tipo": p["tipo"],
            "status": p["status_codigo"],
            "necessita_taxi": p.get("necessita_taxi"),
            "quantidade_passageiros": p.get("qtd_passageiros"),
            "necessita_acessibilidade": p.get("necessita_acessibilidade"),
            "quantidade_criancas": p.get("qtd_criancas"),
            "quantidade_animais": p.get("qtd_animais"),
            "bagagem": p.get("bagagem"),
            "observacoes": p.get("observacoes"),
            "data_criacao": _iso(p["data_criacao"]),
            "data_resposta": _iso(p["data_resposta"]),
            "version": p["version"],
        }
        for p in solicitacao_repo.perguntas_by_solicitacao(solicitacao_id)
    ]

    historico = [
        {
            "id_historico": h["id_historico"],
            "status": h["status"],
            "data_status": _iso(h["data_status"]),
            "responsavel": (
                {"id_usuario": h["fk_usuario_responsavel"], "nome_exibicao": h["nome_exibicao"]}
                if h.get("fk_usuario_responsavel")
                else {"id_usuario": None, "nome_exibicao": h.get("nome_responsavel") or "Sistema"}
            ),
            "comentario": h["comentario"],
        }
        for h in solicitacao_repo.historico_by_solicitacao(solicitacao_id)
    ]

    return {
        "solicitacao": _solicitacao_dto(row),
        "cliente": _cliente_dto(row),
        "apolice": _apolice_dto(row),
        "veiculo": _veiculo_dto(row),
        "seguradora": {
            "id_pj": row.get("fk_seguradora_id"),
            "nome_fantasia": row.get("seguradora_nome"),
            "contatos": [
                {
                    "tipo": c["tipo_contato"],
                    "rotulo": c.get("rotulo"),
                    "valor": c["valor_contato"],
                }
                for c in client_repo.contatos_by_pessoa(row.get("fk_seguradora_id"))
            ],
        },
        "ocorrencia": {
            "id_tipo_ocorrencia": row.get("fk_tipo_ocorrencia_id"),
            "codigo": row.get("ocorrencia_codigo"),
            "nome": row.get("ocorrencia_nome"),
            "descricao": row.get("ocorrencia_descricao"),
        },
        "analista": (
            {"id_usuario": row.get("fk_analista_responsavel"), "nome_exibicao": row.get("analista_nome")}
            if row.get("fk_analista_responsavel")
            else None
        ),
        "assistencias": assistencias,
        "perguntas": perguntas,
        "historico": historico,
    }