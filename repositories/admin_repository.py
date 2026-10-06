from fastapi import HTTPException, status

import repositories.sync_repository as sync_repo
from core.database import get_connection

_TERMINAL_ASSISTANCE_STATUSES = ("CONCLUIDA", "CANCELADA", "REMOVIDA")
_MUTABLE_REQUEST_STATUSES = ("CONFIRMADA", "EM_ATENDIMENTO", "PRESTADOR_ACIONADO")


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


_ADMIN_BASE_SELECT = """
SELECT
    ts.id_solicitacao, ts.id_solicitacao_cliente, ts.numero_solicitacao,
    ts.protocolo_solicitacao, ts.descricao_evento, ts.possui_feridos,
    ts.risco_imediato, ts.prioridade, ts.data_criacao_cliente,
    ts.data_recebimento, ts.data_decisao, ts.motivo_recusa, ts.version,
    ts.fk_pessoa, ts.fk_apolice AS fk_apolice_id,
    ts.fk_seguradora AS fk_seguradora_id, ts.fk_veiculo AS fk_veiculo_id,
    ts.fk_tipo_ocorrencia AS fk_tipo_ocorrencia_id, ts.fk_analista_responsavel,
    st.codigo AS status_codigo,
    lsl.endereco, lsl.numero_local, lsl.cidade, lsl.estado, lsl.ponto_referencia,
    p.isJuridico,
    pf.nome AS cliente_nome, pf.cpf_mascarado AS cliente_cpf,
    pj.razao_social AS cliente_razao_social, pj.nome_fantasia AS cliente_nome_fantasia,
    pj.cnpj_mascarado AS cliente_cnpj,
    tv.id_veiculo, tv.marca, tv.modelo, tv.versao, tv.ano_fabricado, tv.ano_modelo,
    tv.placa_mascarada, tv.blindado,
    toc.codigo AS ocorrencia_codigo, toc.nome AS ocorrencia_nome,
    toc.descricao AS ocorrencia_descricao,
    tpj.nome_fantasia AS seguradora_nome,
    tu.nome_exibicao AS analista_nome
FROM tb_solicitacao ts
JOIN tb_status st ON ts.fk_status = st.id_status
JOIN tb_solicitacao_local lsl ON ts.fk_local = lsl.id_local
JOIN tb_pessoa p ON ts.fk_pessoa = p.id_pessoa
LEFT JOIN tb_pessoa_fisica pf ON pf.id_pf = p.id_pessoa
LEFT JOIN tb_pessoa_juridica pj ON pj.id_pj = p.id_pessoa
JOIN tb_apolice ap ON ts.fk_apolice = ap.id_apolice
JOIN tb_veiculo tv ON ts.fk_veiculo = tv.id_veiculo
JOIN tb_ocorrencia toc ON ts.fk_tipo_ocorrencia = toc.id_ocorrencia
JOIN tb_pessoa_juridica tpj ON ts.fk_seguradora = tpj.id_pj
LEFT JOIN tb_user tu ON ts.fk_analista_responsavel = tu.id_user
"""

_SORT_ALLOWED = {
    "data_recebimento": "ts.data_recebimento",
    "data_decisao": "ts.data_decisao",
    "data_criacao_cliente": "ts.data_criacao_cliente",
    "prioridade": "ts.prioridade",
    "numero_solicitacao": "ts.numero_solicitacao",
    "id_solicitacao": "ts.id_solicitacao",
}


def _parse_sort(sort: str | None) -> str:
    if not sort:
        return "ORDER BY ts.data_recebimento DESC, ts.id_solicitacao DESC"
    field, _, direction = sort.partition(":")
    column = _SORT_ALLOWED.get(field.strip().lower())
    if not column:
        return "ORDER BY ts.data_recebimento DESC, ts.id_solicitacao DESC"
    direction = direction.strip().lower()
    if direction not in ("asc", "desc"):
        direction = "asc"
    return f"ORDER BY {column} {direction}, ts.id_solicitacao {direction}"


_FILTER_CLAUSES = {
    "status": "st.codigo = %s",
    "prioridade": "ts.prioridade = %s",
    "tipo_ocorrencia_id": "ts.fk_tipo_ocorrencia = %s",
    "data_inicio": "DATE(ts.data_recebimento) >= %s",
    "data_fim": "DATE(ts.data_recebimento) <= %s",
    "numero_solicitacao": "ts.numero_solicitacao LIKE %s",
    "pessoa": "(pf.nome LIKE %s OR pf.cpf_mascarado LIKE %s OR pj.razao_social LIKE %s OR pj.nome_fantasia LIKE %s)",
    "placa": "tv.placa_mascarada LIKE %s",
}


def find_solicitacoes(insurer_ids: list[int], filters: dict | None = None, sort: str | None = None) -> list[dict]:
    allowed = [int(i) for i in insurer_ids if int(i) > 0]
    if not allowed:
        return []
    placeholders = ", ".join(["%s"] * len(allowed))
    clauses = [f"ts.fk_seguradora IN ({placeholders})"]
    params: list = list(allowed)

    filters = filters or {}
    for key, clause in _FILTER_CLAUSES.items():
        value = filters.get(key)
        if value in (None, ""):
            continue
        if key in ("data_inicio", "data_fim", "tipo_ocorrencia_id"):
            params.append(value)
            clauses.append(clause)
        elif key in ("numero_solicitacao", "pessoa", "placa"):
            like_value = f"%{value}%"
            if key == "pessoa":
                params.extend([like_value] * 4)
            else:
                params.append(like_value)
            clauses.append(clause)
        else:
            params.append(value)
            clauses.append(clause)

    query = (
        _ADMIN_BASE_SELECT
        + " WHERE "
        + " AND ".join(clauses)
        + " "
        + _parse_sort(sort)
    )
    return _fetch_all(query, tuple(params))


_TIPOS_ASSISTENCIA_ATIVOS = """
SELECT tta.id_tipo_assistencia, tta.codigo, tta.nome, tta.descricao, tta.ativo
FROM tb_tipo_assistencia tta
WHERE tta.ativo = 1
ORDER BY tta.id_tipo_assistencia
"""


def tipos_assistencia_ativos() -> list[dict]:
    return _fetch_all(_TIPOS_ASSISTENCIA_ATIVOS, ())


_TIPO_ASSISTENCIA_BY_ID = """
SELECT tta.id_tipo_assistencia, tta.codigo, tta.nome, tta.descricao, tta.ativo
FROM tb_tipo_assistencia tta
WHERE tta.id_tipo_assistencia = %s
LIMIT 1
"""


def tipo_assistencia_by_id(tipo_assistencia_id: int) -> dict | None:
    return _fetch_one(_TIPO_ASSISTENCIA_BY_ID, (tipo_assistencia_id,))


_ASSISTENCIA_BY_ID = """
SELECT
    tsa.id_solicitacao_assistencia, tsa.fk_solicitacao, tsa.status, tsa.comentario,
    tsa.data_inclusao, tsa.data_atualizacao, tsa.version,
    tta.id_tipo_assistencia, tta.codigo AS tipo_codigo, tta.nome AS tipo_nome,
    tu.id_user AS id_usuario, tu.nome_exibicao
FROM tb_solicitacao_assistencia tsa
JOIN tb_assistencia ta ON tsa.fk_assistencia = ta.id_assistencia
JOIN tb_tipo_assistencia tta ON ta.fk_id_tipo_assistencia = tta.id_tipo_assistencia
LEFT JOIN tb_user tu ON tsa.fk_usuario_responsavel = tu.id_user
WHERE tsa.id_solicitacao_assistencia = %s
LIMIT 1
"""


def assistencia_by_id(assistance_id: int) -> dict | None:
    return _fetch_one(_ASSISTENCIA_BY_ID, (assistance_id,))


def _id_status(cur, codigo: str, entidade: str) -> int | None:
    cur.execute(
        "SELECT id_status FROM tb_status WHERE codigo = %s AND entidade = %s LIMIT 1",
        (codigo, entidade),
    )
    row = cur.fetchone()
    return int(row["id_status"]) if row else None


_ID_TIPO_ASSISTENCIA_SQL = """
SELECT tta.id_tipo_assistencia, tta.codigo, tta.nome, tta.descricao
FROM tb_tipo_assistencia tta
WHERE tta.id_tipo_assistencia = %s AND tta.ativo = 1
LIMIT 1
"""

_ASSISTENCIA_CATALOG_BY_TIPO = """
SELECT ta.id_assistencia
FROM tb_assistencia ta
WHERE ta.fk_id_tipo_assistencia = %s
ORDER BY ta.id_assistencia
LIMIT 1
"""

_INSERT_ASSISTENCIA_CATALOG = """
INSERT INTO tb_assistencia (fk_id_tipo_assistencia, nome, descricao, fk_status)
SELECT tta.id_tipo_assistencia, tta.nome, tta.descricao, st.id_status
FROM tb_tipo_assistencia tta
JOIN tb_status st ON st.codigo = 'RECEBIDO' AND st.entidade = 'ASSISTENCIA'
WHERE tta.id_tipo_assistencia = %s
"""

_DUPLICATE_ASSISTENCIA = """
SELECT tsa.id_solicitacao_assistencia
FROM tb_solicitacao_assistencia tsa
JOIN tb_assistencia ta ON tsa.fk_assistencia = ta.id_assistencia
WHERE tsa.fk_solicitacao = %s
  AND ta.fk_id_tipo_assistencia = %s
  AND tsa.status NOT IN ('CANCELADA', 'REMOVIDA')
LIMIT 1
"""

_PERGUNTA_TAXI_EXISTENTE = """
SELECT tp.id_pergunta
FROM tb_pergunta tp
WHERE tp.fk_solicitacao = %s AND tp.tipo = 'TAXI'
LIMIT 1
"""

_INSERT_ASSISTENCIA_SOLICITACAO = """
INSERT INTO tb_solicitacao_assistencia (
    status, comentario, data_inclusao, data_atualizacao, version,
    fk_solicitacao, fk_assistencia, fk_usuario_responsavel
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

_INSERT_PERGUNTA_TAXI = """
INSERT INTO tb_pergunta (
    origem, tipo, data_criacao, version, fk_solicitacao, fk_assistencia, fk_status
) VALUES ('GUINCHO', 'TAXI', %s, 1, %s, %s, %s)
"""

_UPDATE_SOLICITACAO_STATUS_API = """
UPDATE tb_solicitacao
SET fk_status = %s,
    fk_analista_responsavel = %s,
    version = version + 1
WHERE id_solicitacao = %s
"""

_INSERT_HISTORICO = """
INSERT INTO tb_historico_status (
    status, data_status, comentario, nome_responsavel, fk_solicitacao, fk_usuario_responsavel
) VALUES (%s, %s, %s, %s, %s, %s)
"""

_UPDATE_ASSISTENCIA_STATUS = """
UPDATE tb_solicitacao_assistencia
SET status = %s,
    comentario = %s,
    fk_usuario_responsavel = %s,
    data_atualizacao = %s,
    version = version + 1
WHERE id_solicitacao_assistencia = %s AND version = %s
"""

_UPDATE_SOLICITACAO_VERSION = """
UPDATE tb_solicitacao
SET version = version + 1
WHERE id_solicitacao = %s
"""


def add_assistencia(
    *,
    id_solicitacao: int,
    id_usuario: int,
    nome_exibicao: str,
    tipo_assistencia_id: int,
    comentario: str,
    now,
) -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            "SELECT ts.id_solicitacao, ts.fk_apolice, ts.version, st.codigo AS status_codigo "
            "FROM tb_solicitacao ts JOIN tb_status st ON ts.fk_status = st.id_status "
            "WHERE ts.id_solicitacao = %s FOR UPDATE",
            (id_solicitacao,),
        )
        request = cur.fetchone()
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "REQUEST_NOT_FOUND", "message": "Solicitação não encontrada."},
            )
        if request["status_codigo"] not in _MUTABLE_REQUEST_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "REQUEST_INVALID_STATUS_TRANSITION",
                        "message": "Não é possível incluir assistência neste estado."},
            )

        cur.execute(_ID_TIPO_ASSISTENCIA_SQL, (tipo_assistencia_id,))
        tipo = cur.fetchone()
        if not tipo:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "VALIDATION_ERROR", "message": "Selecione uma assistência ativa."},
            )

        if request["status_codigo"] == "PRESTADOR_ACIONADO" and not comentario:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "ASSISTANCE_COMMENT_REQUIRED",
                        "message": "Informe um comentário para alterações após o acionamento."},
            )

        cur.execute(_ASSISTENCIA_CATALOG_BY_TIPO, (tipo_assistencia_id,))
        catalog = cur.fetchone()
        if catalog:
            id_assistencia_catalog = int(catalog["id_assistencia"])
        else:
            cur.execute(_INSERT_ASSISTENCIA_CATALOG, (tipo_assistencia_id,))
            id_assistencia_catalog = cur.lastrowid

        cur.execute(_DUPLICATE_ASSISTENCIA, (id_solicitacao, tipo_assistencia_id))
        if cur.fetchone():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": "ASSISTANCE_ALREADY_ACTIVE",
                        "message": "Esta assistência já está ativa."},
            )

        cur.execute(
            _INSERT_ASSISTENCIA_SOLICITACAO,
            (
                "INCLUIDA",
                comentario or None,
                now,
                now,
                1,
                id_solicitacao,
                id_assistencia_catalog,
                id_usuario,
            ),
        )
        id_assistencia = cur.lastrowid

        pergunta_id = None
        if tipo["codigo"] == "GUINCHO":
            cur.execute(_PERGUNTA_TAXI_EXISTENTE, (id_solicitacao,))
            if not cur.fetchone():
                status_pergunta = _id_status(cur, "PENDENTE", "PERGUNTA")
                if status_pergunta is None:
                    raise RuntimeError("Status PERGUNTA/PENDENTE não encontrado no banco.")
                cur.execute(
                    _INSERT_PERGUNTA_TAXI,
                    (now, id_solicitacao, id_assistencia_catalog, status_pergunta),
                )
                pergunta_id = cur.lastrowid

        if request["status_codigo"] == "CONFIRMADA":
            status_em_atendimento = _id_status(cur, "EM_ATENDIMENTO", "SOLICITACAO")
            if status_em_atendimento is None:
                raise RuntimeError("Status SOLICITACAO/EM_ATENDIMENTO não encontrado no banco.")
            cur.execute(
                _UPDATE_SOLICITACAO_STATUS_API,
                (status_em_atendimento, id_usuario, id_solicitacao),
            )
            cur.execute(
                _INSERT_HISTORICO,
                (
                    "EM_ATENDIMENTO",
                    now,
                    "Atendimento iniciado com a inclusão e operação das assistências.",
                    nome_exibicao,
                    id_solicitacao,
                    id_usuario,
                ),
            )
        else:
            cur.execute(_UPDATE_SOLICITACAO_VERSION, (id_solicitacao,))

        sync_repo.bump_revision_cursor(cur, now)
        conn.commit()

        return {
            "assistencia": {
                "id_solicitacao_assistencia": id_assistencia,
                "status": "INCLUIDA",
                "comentario": comentario or None,
                "data_inclusao": now,
                "data_atualizacao": now,
                "version": 1,
                "id_tipo_assistencia": tipo["id_tipo_assistencia"],
                "tipo_codigo": tipo["codigo"],
                "tipo_nome": tipo["nome"],
                "id_usuario": id_usuario,
                "nome_exibicao": nome_exibicao,
            },
            "pergunta_id": pergunta_id,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def update_assistencia_status(
    *,
    assistance_id: int,
    status_destino: str,
    comentario: str,
    version: int,
    id_usuario: int,
    nome_exibicao: str,
    now,
    fk_solicitacao: int,
    request_status_codigo: str,
) -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        cur.execute(
            _UPDATE_ASSISTENCIA_STATUS,
            (status_destino, comentario or None, id_usuario, now, assistance_id, version),
        )
        if cur.rowcount != 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "ASSISTANCE_VERSION_CONFLICT",
                        "message": "A assistência foi atualizada por outra operação."},
            )

        if (
            request_status_codigo == "EM_ATENDIMENTO"
            and status_destino in ("PRESTADOR_ACIONADO", "EM_DESLOCAMENTO", "CONCLUIDA")
        ):
            status_prestador = _id_status(cur, "PRESTADOR_ACIONADO", "SOLICITACAO")
            if status_prestador is None:
                raise RuntimeError("Status SOLICITACAO/PRESTADOR_ACIONADO não encontrado no banco.")
            cur.execute(
                _UPDATE_SOLICITACAO_STATUS_API,
                (status_prestador, id_usuario, fk_solicitacao),
            )
            cur.execute(
                _INSERT_HISTORICO,
                (
                    "PRESTADOR_ACIONADO",
                    now,
                    "Prestador acionado em uma das assistências do atendimento.",
                    nome_exibicao,
                    fk_solicitacao,
                    id_usuario,
                ),
            )

        sync_repo.bump_revision_cursor(cur, now)
        conn.commit()

        return {
            "id_solicitacao_assistencia": assistance_id,
            "fk_solicitacao": fk_solicitacao,
            "status": status_destino,
            "comentario": comentario or None,
            "data_atualizacao": now,
            "version": version + 1,
            "id_usuario": id_usuario,
            "nome_exibicao": nome_exibicao,
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def transicionar_solicitacao(
    *,
    id_solicitacao: int,
    from_status_codigo: str,
    to_status_codigo: str,
    version: int,
    id_usuario: int,
    nome_exibicao: str,
    comentario: str,
    now,
    set_decisao: bool = False,
    motivo_recusa: str | None = None,
    release_policy: bool = False,
    fk_apolice: int | None = None,
) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)

        to_status_id = _id_status(cur, to_status_codigo, "SOLICITACAO")
        from_status_id = _id_status(cur, from_status_codigo, "SOLICITACAO")
        if to_status_id is None or from_status_id is None:
            raise RuntimeError("Status de SOLICITACAO não encontrado no banco.")

        sets = ["fk_status = %s", "fk_analista_responsavel = %s", "version = version + 1"]
        params: list = [to_status_id, id_usuario]
        if set_decisao:
            sets.append("data_decisao = %s")
            sets.append("motivo_recusa = %s")
            params.append(now)
            params.append(motivo_recusa)
        params.extend([id_solicitacao, version, from_status_id])

        query = (
            "UPDATE tb_solicitacao SET "
            + ", ".join(sets)
            + " WHERE id_solicitacao = %s AND version = %s AND fk_status = %s"
        )
        cur.execute(query, tuple(params))
        if cur.rowcount != 1:
            conn.rollback()
            return False

        cur.execute(
            _INSERT_HISTORICO,
            (to_status_codigo, now, comentario, nome_exibicao, id_solicitacao, id_usuario),
        )

        if release_policy and fk_apolice:
            cur.execute(
                "UPDATE tb_apolice SET possui_solicitacao_ativa = 0 WHERE id_apolice = %s",
                (fk_apolice,),
            )

        sync_repo.bump_revision_cursor(cur, now)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()