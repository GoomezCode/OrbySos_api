from core.database import get_connection

_REVISION_KEY = "revision"
_UPDATED_AT_KEY = "updated_at"

_GET_VERSION = """
SELECT chave, valor
FROM orbyt_meta
WHERE chave IN (%s, %s)
"""

_REVISION_INC = """
INSERT INTO orbyt_meta (chave, valor)
VALUES (%s, %s)
ON DUPLICATE KEY UPDATE valor = CAST(valor AS UNSIGNED) + 1
"""

_UPDATED_AT_SET = """
INSERT INTO orbyt_meta (chave, valor)
VALUES (%s, %s)
ON DUPLICATE KEY UPDATE valor = %s
"""


def _fetch_version() -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(_GET_VERSION, (_REVISION_KEY, _UPDATED_AT_KEY))
        rows = {row["chave"]: row["valor"] for row in cur.fetchall()}
        return rows
    finally:
        cur.close()
        conn.close()


def get_version() -> dict:
    rows = _fetch_version()
    revision = rows.get(_REVISION_KEY)
    updated_at = rows.get(_UPDATED_AT_KEY)
    return {
        "revision": int(revision) if revision is not None else 0,
        "updated_at": updated_at if updated_at else None,
    }


def bump_revision_cursor(cur, now) -> None:
    cur.execute(_REVISION_INC, (_REVISION_KEY, "1"))
    cur.execute(_UPDATED_AT_SET, (_UPDATED_AT_KEY, now, now))


def bump_revision(now: str) -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor()
        bump_revision_cursor(cur, now)
        conn.commit()
    finally:
        cur.close()
        conn.close()
    return get_version()