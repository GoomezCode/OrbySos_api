from fastapi import HTTPException, status

import repositories.sync_repository as sync_repo
from core.database import get_connection


def _fetch_one(query: str, params: tuple) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()


def _fetch_all(query: str, params: tuple) -> list[dict]:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()


_APOLICE_BASE_SELECT = """
SELECT
    ap.id_apolice, ap.numero_apolice, ap.numero_apolice_mascarado,
    ap.data_inicio, ap.data_fim, ap.cobertura, ap.assistencia, ap.endosso,
    ap.perfil, ap.versao, ap.possui_solicitacao_ativa,
    ap.fk_pessoa AS fk_pessoa_id, ap.fk_segurado AS fk_segurado_id,
    ap.fk_veiculo AS fk_veiculo_id,
    ap.fk_local_pernoite AS fk_local_pernoite_id,
    ap.fk_forma_pagamento AS fk_forma_pagamento_id,
    st.codigo AS apolice_status,
    p.isJuridico,
    pf.nome AS cliente_nome, pf.cpf_mascarado AS cliente_cpf,
    pj.razao_social AS cliente_razao_social, pj.nome_fantasia AS cliente_nome_fantasia,
    pj.cnpj_mascarado AS cliente_cnpj,
    tsp.nome_fantasia AS seguradora_nome_fantasia,
    tv.id_veiculo, tv.marca, tv.modelo, tv.versao AS veiculo_versao,
    tv.ano_fabricado, tv.ano_modelo, tv.placa, tv.placa_mascarada, tv.blindado,
    tl.local AS local_pernoite,
    tf.forma AS forma_pagamento
FROM tb_apolice ap
JOIN tb_status st ON ap.fk_status = st.id_status
JOIN tb_pessoa p ON ap.fk_pessoa = p.id_pessoa
LEFT JOIN tb_pessoa_fisica pf ON pf.id_pf = p.id_pessoa
LEFT JOIN tb_pessoa_juridica pj ON pj.id_pj = p.id_pessoa
JOIN tb_pessoa_juridica tsp ON ap.fk_segurado = tsp.id_pj
JOIN tb_veiculo tv ON ap.fk_veiculo = tv.id_veiculo
LEFT JOIN tb_local_pernoite tl ON ap.fk_local_pernoite = tl.id_local_pernoite
LEFT JOIN tb_forma_pagamento tf ON ap.fk_forma_pagamento = tf.id_forma_pagamento
"""

_APOLICE_BY_ID = _APOLICE_BASE_SELECT + """
WHERE ap.id_apolice = %s
LIMIT 1
"""

_APOLICE_BY_ID_FOR_UPDATE = _APOLICE_BASE_SELECT + """
WHERE ap.id_apolice = %s
LIMIT 1
FOR UPDATE
"""

_APOLICE_WITH_VERSION = """
SELECT ap.id_apolice, ap.versao, st.codigo AS apolice_status
FROM tb_apolice ap
JOIN tb_status st ON ap.fk_status = st.id_status
WHERE ap.id_apolice = %s
LIMIT 1
"""

_SORT_ALLOWED = {
    "id_apolice": "ap.id_apolice",
    "numero_apolice": "ap.numero_apolice",
    "data_inicio": "ap.data_inicio",
    "data_fim": "ap.data_fim",
    "status": "st.codigo",
}


def _parse_sort(sort: str | None) -> str:
    if not sort:
        return "ORDER BY ap.id_apolice DESC"
    field, _, direction = sort.partition(":")
    column = _SORT_ALLOWED.get(field.strip().lower())
    if not column:
        return "ORDER BY ap.id_apolice DESC"
    direction = direction.strip().lower()
    if direction not in ("asc", "desc"):
        direction = "asc"
    return f"ORDER BY {column} {direction}, ap.id_apolice {direction}"


_FILTER_CLAUSES = {
    "status": "st.codigo = %s",
    "numero_apolice": "ap.numero_apolice LIKE %s",
    "pessoa": "(pf.nome LIKE %s OR pf.cpf_mascarado LIKE %s OR pj.razao_social LIKE %s OR pj.nome_fantasia LIKE %s)",
    "placa": "tv.placa_mascarada LIKE %s",
    "seguradora": "tsp.id_pj = %s",
}


def find_apolices(insurer_ids: list[int], filters: dict | None = None, sort: str | None = None) -> list[dict]:
    allowed = [int(i) for i in insurer_ids if int(i) > 0]
    if not allowed:
        return []
    placeholders = ", ".join(["%s"] * len(allowed))
    clauses = [f"ap.fk_segurado IN ({placeholders})"]
    params: list = list(allowed)

    filters = filters or {}
    for key, clause in _FILTER_CLAUSES.items():
        value = filters.get(key)
        if value in (None, ""):
            continue
        if key in ("numero_apolice", "pessoa", "placa"):
            like_value = f"%{value}%"
            if key == "pessoa":
                params.extend([like_value] * 4)
            else:
                params.append(like_value)
        else:
            params.append(value)
        clauses.append(clause)

    query = (
        _APOLICE_BASE_SELECT
        + " WHERE "
        + " AND ".join(clauses)
        + " "
        + _parse_sort(sort)
    )
    return _fetch_all(query, tuple(params))


def apolice_by_id(apolice_id: int) -> dict | None:
    return _fetch_one(_APOLICE_BY_ID, (apolice_id,))


def apolice_with_version(apolice_id: int) -> dict | None:
    return _fetch_one(_APOLICE_WITH_VERSION, (apolice_id,))


def _id_status(cur, codigo: str, entidade: str) -> int | None:
    cur.execute(
        "SELECT id_status FROM tb_status WHERE codigo = %s AND entidade = %s LIMIT 1",
        (codigo, entidade),
    )
    row = cur.fetchone()
    return int(row["id_status"]) if row else None


def _validate_status_apolice(cur, codigo: str) -> int:
    status_id = _id_status(cur, codigo, "APOLICE")
    if status_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "INVALID_POLICY_STATUS", "message": "Status de apólice inválido."},
        )
    return status_id


def _require_pessoa_veiculo(cur, pessoa_id: int, veiculo_id: int) -> None:
    cur.execute(
        "SELECT 1 FROM tb_veiculo tv WHERE tv.id_veiculo = %s",
        (veiculo_id,),
    )
    if not cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "VEHICLE_NOT_FOUND", "message": "Veículo informado não existe."},
        )
    cur.execute(
        "SELECT 1 FROM tb_veiculo tv WHERE tv.id_veiculo = %s AND tv.fk_pessoa = %s",
        (veiculo_id, pessoa_id),
    )
    if not cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "VEHICLE_OWNER_MISMATCH", "message": "O veículo não pertence ao segurado informado."},
        )


def _require_segurado(cur, segurado_id: int) -> None:
    cur.execute(
        "SELECT 1 FROM tb_pessoa_juridica tpj WHERE tpj.id_pj = %s AND tpj.isSeguradora = 1",
        (segurado_id,),
    )
    if not cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": "INSURER_NOT_FOUND", "message": "Seguradora informada não existe."},
        )


_INSERT_APOLICE = """
INSERT INTO tb_apolice (
    numero_apolice, numero_apolice_mascarado, fk_pessoa, fk_segurado, fk_veiculo,
    data_inicio, data_fim, cobertura, assistencia, endosso, versao, perfil,
    fk_local_pernoite, fk_status, fk_forma_pagamento, possui_solicitacao_ativa
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s, 0)
"""

_UPDATE_APOLICE = """
UPDATE tb_apolice
SET numero_apolice = %s,
    data_inicio = %s,
    data_fim = %s,
    cobertura = %s,
    assistencia = %s,
    endosso = %s,
    perfil = %s,
    versao = versao + 1
WHERE id_apolice = %s AND versao = %s
"""

_UPDATE_APOLICE_STATUS = """
UPDATE tb_apolice
SET fk_status = %s,
    versao = versao + 1
WHERE id_apolice = %s AND versao = %s AND fk_status = %s
"""


def create_apolice(*, data: dict, now) -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        _require_segurado(cur, data["fk_segurado"])
        _require_pessoa_veiculo(cur, data["fk_pessoa"], data["fk_veiculo"])
        status_id = _validate_status_apolice(cur, "ATIVA")

        numero = data["numero_apolice"]
        mascara = "ORB-****-XXXX"
        if len(numero) >= 4:
            mascara = f"ORB-****-{numero[-4:]}"

        cur.execute(
            _INSERT_APOLICE,
            (
                numero,
                mascara,
                data["fk_pessoa"],
                data["fk_segurado"],
                data["fk_veiculo"],
                data["data_inicio"],
                data["data_fim"],
                data["cobertura"],
                data.get("assistencia") or "",
                data.get("endosso"),
                data.get("perfil") or "",
                data["fk_local_pernoite"],
                status_id,
                data["fk_forma_pagamento"],
            ),
        )
        created_id = int(cur.lastrowid)

        sync_repo.bump_revision_cursor(cur, now)
        conn.commit()

        row = _fetch_one(_APOLICE_BY_ID, (created_id,))
        return row or {}
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def update_apolice(*, apolice_id: int, version: int, patch: dict, now) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT ap.id_apolice, ap.versao FROM tb_apolice ap WHERE ap.id_apolice = %s FOR UPDATE",
            (apolice_id,),
        )
        if not cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "POLICY_NOT_FOUND", "message": "Apólice não encontrada."},
            )

        cur.execute(
            _UPDATE_APOLICE,
            (
                patch["numero_apolice"],
                patch["data_inicio"],
                patch["data_fim"],
                patch["cobertura"],
                patch.get("assistencia") or "",
                patch.get("endosso"),
                patch.get("perfil") or "",
                apolice_id,
                version,
            ),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return None

        sync_repo.bump_revision_cursor(cur, now)
        conn.commit()

        return _fetch_one(_APOLICE_BY_ID, (apolice_id,))
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def update_apolice_status(*, apolice_id: int, version: int, to_status: str, now) -> dict | None:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT ap.id_apolice, ap.versao, ap.fk_status FROM tb_apolice ap WHERE ap.id_apolice = %s FOR UPDATE",
            (apolice_id,),
        )
        current = cur.fetchone()
        if not current:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "POLICY_NOT_FOUND", "message": "Apólice não encontrada."},
            )
        current_status_id = int(current["fk_status"])

        to_status_id = _validate_status_apolice(cur, to_status)
        if to_status_id == current_status_id:
            conn.rollback()
            return None

        cur.execute(
            _UPDATE_APOLICE_STATUS,
            (to_status_id, apolice_id, version, current_status_id),
        )
        if cur.rowcount != 1:
            conn.rollback()
            return None

        sync_repo.bump_revision_cursor(cur, now)
        conn.commit()

        return _fetch_one(_APOLICE_BY_ID, (apolice_id,))
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()