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


_PERSON_BY_ID = """
SELECT p.id_pessoa, p.isJuridico
FROM tb_pessoa p
WHERE p.id_pessoa = %s
LIMIT 1
"""

_PESSOA_FISICA_BY_ID = """
SELECT
    pf.id_pf, pf.nome, pf.cpf, pf.cpf_mascarado, pf.data_nascimento
FROM tb_pessoa_fisica pf
WHERE pf.id_pf = %s
LIMIT 1
"""

_PESSOA_JURIDICA_BY_ID = """
SELECT
    pj.id_pj, pj.razao_social, pj.nome_fantasia, pj.cnpj, pj.cnpj_mascarado
FROM tb_pessoa_juridica pj
WHERE pj.id_pj = %s
LIMIT 1
"""

_CONTATOS_BY_PESSOA = """
SELECT tc.tipo_contato, tc.valor_contato, tc.principal, tc.rotulo
FROM tb_contato tc
WHERE tc.fk_pessoa = %s
ORDER BY tc.principal DESC, tc.id_contato
"""

_POLICIES_BY_PESSOA = """
SELECT
    ap.id_apolice, ap.numero_apolice, ap.numero_apolice_mascarado,
    ap.data_inicio, ap.data_fim, ap.fk_pessoa, ap.fk_veiculo, ap.fk_segurado,
    sap.codigo AS apolice_status,
    tv.id_veiculo, tv.marca, tv.modelo, tv.versao, tv.ano_fabricado, tv.ano_modelo,
    tv.placa, tv.placa_mascarada, tv.blindado,
    tpj.id_pj, tpj.nome_fantasia
FROM tb_apolice ap
JOIN tb_status sap ON ap.fk_status = sap.id_status
JOIN tb_veiculo tv ON ap.fk_veiculo = tv.id_veiculo
JOIN tb_pessoa_juridica tpj ON ap.fk_segurado = tpj.id_pj
WHERE ap.fk_pessoa = %s
ORDER BY ap.id_apolice
"""

_ACTIVE_REQUEST_BY_POLICY = """
SELECT
    ts.id_solicitacao, ts.numero_solicitacao, ts.prioridade, ts.data_recebimento,
    st.codigo AS status_codigo
FROM tb_solicitacao ts
JOIN tb_status st ON ts.fk_status = st.id_status
WHERE ts.fk_apolice = %s
  AND st.codigo IN ('RECEBIDA','EM_ANALISE','CONFIRMADA','EM_ATENDIMENTO','PRESTADOR_ACIONADO')
ORDER BY ts.data_recebimento DESC, ts.id_solicitacao DESC
LIMIT 1
"""

_REQUESTS_BY_PESSOA = """
SELECT
    ts.id_solicitacao, ts.numero_solicitacao, st.codigo AS status_codigo,
    ts.prioridade, ts.descricao_evento, ts.possui_feridos, ts.risco_imediato,
    ts.data_recebimento, ts.data_decisao, ts.motivo_recusa, ts.version,
    tv.id_veiculo, tv.marca, tv.modelo, tv.ano_modelo, tv.placa_mascarada,
    toc.id_ocorrencia, toc.codigo, toc.nome
FROM tb_solicitacao ts
JOIN tb_status st ON ts.fk_status = st.id_status
JOIN tb_veiculo tv ON ts.fk_veiculo = tv.id_veiculo
JOIN tb_ocorrencia toc ON ts.fk_tipo_ocorrencia = toc.id_ocorrencia
WHERE ts.fk_pessoa = %s
ORDER BY ts.data_recebimento DESC, ts.id_solicitacao DESC
"""

_REQUESTS_BY_PESSOA_STATUS = """
SELECT
    ts.id_solicitacao, ts.numero_solicitacao, st.codigo AS status_codigo,
    ts.prioridade, ts.descricao_evento, ts.possui_feridos, ts.risco_imediato,
    ts.data_recebimento, ts.data_decisao, ts.motivo_recusa, ts.version,
    tv.id_veiculo, tv.marca, tv.modelo, tv.ano_modelo, tv.placa_mascarada,
    toc.id_ocorrencia, toc.codigo, toc.nome
FROM tb_solicitacao ts
JOIN tb_status st ON ts.fk_status = st.id_status
JOIN tb_veiculo tv ON ts.fk_veiculo = tv.id_veiculo
JOIN tb_ocorrencia toc ON ts.fk_tipo_ocorrencia = toc.id_ocorrencia
WHERE ts.fk_pessoa = %s
  AND st.codigo = %s
ORDER BY ts.data_recebimento DESC, ts.id_solicitacao DESC
"""

_REQUESTS_BY_PESSOA_ACTIVE = """
SELECT
    ts.id_solicitacao, ts.numero_solicitacao, st.codigo AS status_codigo,
    ts.prioridade, ts.descricao_evento, ts.possui_feridos, ts.risco_imediato,
    ts.data_recebimento, ts.data_decisao, ts.motivo_recusa, ts.version,
    tv.id_veiculo, tv.marca, tv.modelo, tv.ano_modelo, tv.placa_mascarada,
    toc.id_ocorrencia, toc.codigo, toc.nome
FROM tb_solicitacao ts
JOIN tb_status st ON ts.fk_status = st.id_status
JOIN tb_veiculo tv ON ts.fk_veiculo = tv.id_veiculo
JOIN tb_ocorrencia toc ON ts.fk_tipo_ocorrencia = toc.id_ocorrencia
WHERE ts.fk_pessoa = %s
  AND st.codigo IN ('RECEBIDA','EM_ANALISE','CONFIRMADA','EM_ATENDIMENTO','PRESTADOR_ACIONADO')
ORDER BY ts.data_recebimento DESC, ts.id_solicitacao DESC
"""

_OCCURRENCE_BY_ID = """
SELECT oc.id_ocorrencia, oc.codigo, oc.nome, oc.descricao, oc.ativo
FROM tb_ocorrencia oc
WHERE oc.id_ocorrencia = %s
LIMIT 1
"""

_POLICY_BY_ID_FOR_PESSOA = """
SELECT
    ap.id_apolice, ap.fk_pessoa, ap.fk_segurado, ap.fk_veiculo,
    sap.codigo AS apolice_status
FROM tb_apolice ap
JOIN tb_status sap ON ap.fk_status = sap.id_status
WHERE ap.id_apolice = %s AND ap.fk_pessoa = %s
LIMIT 1
"""

_REQUEST_BY_CLIENT_UUID = """
SELECT ts.id_solicitacao
FROM tb_solicitacao ts
WHERE ts.id_solicitacao_cliente = %s
LIMIT 1
"""

_NEXT_SOLICITACAO_SEQ = """
SELECT COALESCE(MAX(ts.id_solicitacao), 0) + 1 AS prox_seq
FROM tb_solicitacao ts
"""


def person_by_id(pessoa_id: int) -> dict | None:
    return _fetch_one(_PERSON_BY_ID, (pessoa_id,))


def pessoa_fisica_by_id(id_pf: int) -> dict | None:
    return _fetch_one(_PESSOA_FISICA_BY_ID, (id_pf,))


def pessoa_juridica_by_id(id_pj: int) -> dict | None:
    return _fetch_one(_PESSOA_JURIDICA_BY_ID, (id_pj,))


def contatos_by_pessoa(pessoa_id: int) -> list[dict]:
    return _fetch_all(_CONTATOS_BY_PESSOA, (pessoa_id,))


def policies_by_pessoa(pessoa_id: int) -> list[dict]:
    return _fetch_all(_POLICIES_BY_PESSOA, (pessoa_id,))


def active_request_by_policy(policy_id: int) -> dict | None:
    return _fetch_one(_ACTIVE_REQUEST_BY_POLICY, (policy_id,))


def requests_by_pessoa(pessoa_id: int, status: str | None = None, active_only: bool = False) -> list[dict]:
    if status:
        return _fetch_all(_REQUESTS_BY_PESSOA_STATUS, (pessoa_id, status))
    if active_only:
        return _fetch_all(_REQUESTS_BY_PESSOA_ACTIVE, (pessoa_id,))
    return _fetch_all(_REQUESTS_BY_PESSOA, (pessoa_id,))


def occurrence_by_id(ocorrencia_id: int) -> dict | None:
    return _fetch_one(_OCCURRENCE_BY_ID, (ocorrencia_id,))


def policy_by_id_for_pessoa(policy_id: int, pessoa_id: int) -> dict | None:
    return _fetch_one(_POLICY_BY_ID_FOR_PESSOA, (policy_id, pessoa_id))


def request_by_client_uuid(uuid: str) -> dict | None:
    return _fetch_one(_REQUEST_BY_CLIENT_UUID, (uuid,))


def next_solicitacao_seq() -> int:
    row = _fetch_one(_NEXT_SOLICITACAO_SEQ, ())
    return int(row["prox_seq"]) if row else 1