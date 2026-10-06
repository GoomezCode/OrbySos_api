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


_FIND_OCCURRENCES = """
SELECT id_ocorrencia, codigo, nome, descricao, ativo
FROM tb_ocorrencia
WHERE ativo = %s
ORDER BY id_ocorrencia
"""

_FIND_ALL_OCCURRENCES = """
SELECT id_ocorrencia, codigo, nome, descricao, ativo
FROM tb_ocorrencia
ORDER BY id_ocorrencia
"""

_FIND_APP_CONFIGURATION = """
SELECT pais, mensagem, servicos_json
FROM tb_configuracao
ORDER BY id_configuracao
LIMIT 1
"""


def find_occurrences(ativo: bool | None) -> list[dict]:
    if ativo is None:
        return _fetch_all(_FIND_ALL_OCCURRENCES, ())
    return _fetch_all(_FIND_OCCURRENCES, (1 if ativo else 0,))


def get_app_configuration() -> dict | None:
    return _fetch_one(_FIND_APP_CONFIGURATION, ())