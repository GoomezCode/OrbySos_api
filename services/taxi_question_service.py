from datetime import datetime, timezone

from fastapi import HTTPException, status

import repositories.solicitacao_repository as solicitacao_repo

TAXI_QUESTION_STATUS_PENDENTE = "PENDENTE"
TAXI_QUESTION_STATUS_RESPONDIDA = "RESPONDIDA"


class QuestionError(HTTPException):
    def __init__(self, code: str, message: str, fields: list | None = None, http_code: int = 422):
        detail: dict = {"code": code, "message": message}
        if fields:
            detail["fields"] = fields
        super().__init__(status_code=http_code, detail=detail)


def _non_negative(value) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _validate_input(input_data) -> list[dict]:
    if not isinstance(input_data.necessita_taxi, bool):
        raise QuestionError(
            "VALIDATION_ERROR",
            "Informe se você precisa de táxi.",
            [{"field": "necessita_taxi", "message": "Escolha Sim ou Não."}],
        )
    if not input_data.necessita_taxi:
        return []

    passengers = _non_negative(input_data.quantidade_passageiros)
    children = _non_negative(input_data.quantidade_criancas)
    animals = _non_negative(input_data.quantidade_animais)
    baggage = str(input_data.bagagem or "").strip()
    fields = []
    if not passengers:
        fields.append({"field": "quantidade_passageiros", "message": "Informe ao menos um passageiro."})
    if not isinstance(input_data.necessita_acessibilidade, bool):
        fields.append({"field": "necessita_acessibilidade", "message": "Informe a necessidade de acessibilidade."})
    if children is None:
        fields.append({"field": "quantidade_criancas", "message": "Informe zero ou uma quantidade válida."})
    if animals is None:
        fields.append({"field": "quantidade_animais", "message": "Informe zero ou uma quantidade válida."})
    if not baggage:
        fields.append({"field": "bagagem", "message": "Informe a bagagem, mesmo que não haja."})
    if fields:
        raise QuestionError("VALIDATION_ERROR", "Revise os dados do táxi.", fields)
    return fields


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
        "data_criacao": row.get("data_criacao"),
        "data_resposta": row.get("data_resposta"),
        "version": row.get("version"),
    }


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(value)


def responder_pergunta(session: dict, id_pergunta: int, body) -> dict:
    row = solicitacao_repo.pergunta_by_id(id_pergunta)
    if not row:
        raise QuestionError("TAXI_QUESTION_NOT_FOUND", "Pergunta de táxi não encontrada.", http_code=404)

    solicitacao = solicitacao_repo.solicitacao_by_id(row["fk_solicitacao"])
    if not solicitacao or solicitacao["fk_pessoa"] != session["id_pessoa"]:
        raise QuestionError("TAXI_QUESTION_NOT_FOUND", "Pergunta de táxi não encontrada.", http_code=404)

    if row["status_codigo"] != TAXI_QUESTION_STATUS_PENDENTE:
        raise QuestionError("TAXI_QUESTION_ALREADY_ANSWERED", "Esta pergunta já foi respondida.", http_code=422)

    if row["version"] != body.version:
        raise QuestionError(
            "TAXI_QUESTION_VERSION_CONFLICT",
            "A pergunta foi atualizada. Recarregue os dados.",
            http_code=409,
        )

    _validate_input(body)

    aggora = datetime.now(timezone.utc).replace(tzinfo=None)
    if body.necessita_taxi:
        answered = solicitacao_repo.answer_pergunta(
            id_pergunta=id_pergunta,
            necessita_taxi=True,
            quantidade_passageiros=body.quantidade_passageiros,
            necessita_acessibilidade=body.necessita_acessibilidade,
            quantidade_criancas=body.quantidade_criancas,
            quantidade_animais=body.quantidade_animais,
            bagagem=body.bagagem.strip(),
            observacoes=body.observacoes.strip() if body.observacoes else None,
            data_resposta=aggora,
            version=body.version,
        )
    else:
        answered = solicitacao_repo.answer_pergunta(
            id_pergunta=id_pergunta,
            necessita_taxi=False,
            quantidade_passageiros=None,
            necessita_acessibilidade=None,
            quantidade_criancas=None,
            quantidade_animais=None,
            bagagem=None,
            observacoes=None,
            data_resposta=aggora,
            version=body.version,
        )

    if not answered:
        raise QuestionError(
            "TAXI_QUESTION_VERSION_CONFLICT",
            "A pergunta foi atualizada. Recarregue os dados.",
            http_code=409,
        )

    updated = solicitacao_repo.pergunta_by_id(id_pergunta)
    dto = _pergunta_dto(updated)
    dto["data_criacao"] = _iso(updated.get("data_criacao"))
    dto["data_resposta"] = _iso(updated.get("data_resposta"))
    return {"pergunta": dto}