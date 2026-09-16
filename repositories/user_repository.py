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


_FIND_CLIENT_BY_CPF = """
SELECT
    u.id_user, u.fk_pessoa, u.login, u.senha, u.perfil, u.fk_status,
    u.nome_exibicao, u.email,
    s.codigo AS status_codigo,
    pf.nome, pf.cpf, pf.cpf_mascarado
FROM tb_user u
JOIN tb_status s ON u.fk_status = s.id_status
JOIN tb_pessoa_fisica pf ON u.fk_pessoa = pf.id_pf
WHERE pf.cpf = %s AND u.perfil = 'CLIENTE'
LIMIT 1
"""

_FIND_ANALYST_BY_LOGIN = """
SELECT
    u.id_user, u.fk_pessoa, u.login, u.senha, u.perfil, u.fk_status,
    u.nome_exibicao, u.email, u.fk_seguradora,
    s.codigo AS status_codigo
FROM tb_user u
JOIN tb_status s ON u.fk_status = s.id_status
WHERE u.login = %s AND u.perfil = 'ANALISTA'
LIMIT 1
"""

_FIND_ANALYST_INSURERS = """
SELECT pj.id_pj, pj.nome_fantasia
FROM tb_analista_seguradora asa
JOIN tb_pessoa_juridica pj ON asa.fk_seguradora = pj.id_pj
WHERE asa.fk_analista = %s AND asa.ativo = 1
"""

_FIND_INSURER_BY_ID = """
SELECT pj.id_pj, pj.nome_fantasia
FROM tb_pessoa_juridica pj
WHERE pj.id_pj = %s
LIMIT 1
"""


def find_client_by_cpf(cpf: str) -> dict | None:
    return _fetch_one(_FIND_CLIENT_BY_CPF, (cpf,))


def find_analyst_by_login(login: str) -> dict | None:
    return _fetch_one(_FIND_ANALYST_BY_LOGIN, (login,))


def find_analyst_insurers(analyst_id: int) -> list[dict]:
    return _fetch_all(_FIND_ANALYST_INSURERS, (analyst_id,))


def find_insurer(insurer_id: int) -> dict | None:
    return _fetch_one(_FIND_INSURER_BY_ID, (insurer_id,))
