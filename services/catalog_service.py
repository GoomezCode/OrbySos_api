import json

from fastapi import HTTPException, status

import repositories.catalog_repository as catalog_repo

_CATALOG_UNAVAILABLE = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Catálogo de tipos de ocorrência indisponível.",
)
_CONFIG_UNAVAILABLE = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Configurações públicas indisponíveis.",
)


def list_occurrence_types(ativo: bool | None) -> dict:
    try:
        rows = catalog_repo.find_occurrences(ativo)
    except HTTPException:
        raise
    except Exception:
        raise _CATALOG_UNAVAILABLE

    items = [
        {
            "id_tipo_ocorrencia": row["id_ocorrencia"],
            "codigo": row["codigo"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "ativo": bool(row["ativo"]),
            "ordem": row["id_ocorrencia"],
        }
        for row in rows
    ]
    return {"items": items}


def get_public_configurations() -> dict:
    try:
        row = catalog_repo.get_app_configuration()
        servicos = json.loads(row["servicos_json"]) if row else None
    except HTTPException:
        raise
    except Exception:
        raise _CONFIG_UNAVAILABLE

    if row is None:
        raise _CONFIG_UNAVAILABLE

    return {
        "pais": row["pais"],
        "mensagem": row["mensagem"],
        "servicos": servicos,
    }