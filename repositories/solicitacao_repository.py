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


_SOLICITACAO_BY_ID = """
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
WHERE ts.id_solicitacao = %s
LIMIT 1
"""

_APOLICE_RESUMO_BY_ID = """
SELECT
    ap.id_apolice, ap.numero_apolice_mascarado, ap.data_inicio, ap.data_fim,
    sap.codigo AS apolice_status
FROM tb_apolice ap
JOIN tb_status sap ON ap.fk_status = sap.id_status
WHERE ap.id_apolice = %s
LIMIT 1
"""

_ASSISTENCIAS_BY_SOLICITACAO = """
SELECT
    tsa.id_solicitacao_assistencia, tsa.status, tsa.comentario,
    tsa.data_inclusao, tsa.data_atualizacao, tsa.version,
    tta.id_tipo_assistencia, tta.codigo AS tipo_codigo, tta.nome AS tipo_nome,
    tu.id_usuario, tu.nome_exibicao
FROM tb_solicitacao_assistencia tsa
JOIN tb_assistencia ta ON tsa.fk_assistencia = ta.id_assistencia
JOIN tb_tipo_assistencia tta ON ta.fk_id_tipo_assistencia = tta.id_tipo_assistencia
LEFT JOIN tb_user tu ON tsa.fk_usuario_responsavel = tu.id_user
WHERE tsa.fk_solicitacao = %s
ORDER BY tsa.id_solicitacao_assistencia
"""

_PERGUNTAS_BY_SOLICITACAO = """
SELECT
    tp.id_pergunta, tp.origem, tp.tipo, tp.necessita_taxi,
    tp.qtd_passageiros, tp.necessita_acessibilidade, tp.qtd_criancas,
    tp.qtd_animais, tp.bagagem, tp.observacoes, tp.data_criacao,
    tp.data_resposta, tp.version,
    st.codigo AS status_codigo
FROM tb_pergunta tp
JOIN tb_status st ON tp.fk_status = st.id_status
WHERE tp.fk_solicitacao = %s
ORDER BY tp.id_pergunta
"""

_HISTORICO_BY_SOLICITACAO = """
SELECT
    th.id_historico, th.status, th.data_status, th.comentario,
    th.nome_responsavel, th.fk_usuario_responsavel,
    tu.nome_exibicao
FROM tb_historico_status th
LEFT JOIN tb_user tu ON th.fk_usuario_responsavel = tu.id_user
WHERE th.fk_solicitacao = %s
ORDER BY th.data_status, th.id_historico
"""

_ID_STATUS_CREATE = """
SELECT ts2.id_status
FROM tb_status ts2
WHERE ts2.codigo = 'RECEBIDA' AND ts2.entidade = 'SOLICITACAO'
LIMIT 1
"""

_PERGUNTA_BY_ID = """
SELECT
    tp.id_pergunta, tp.origem, tp.tipo, tp.necessita_taxi,
    tp.qtd_passageiros, tp.necessita_acessibilidade, tp.qtd_criancas,
    tp.qtd_animais, tp.bagagem, tp.observacoes, tp.data_criacao,
    tp.data_resposta, tp.version, tp.fk_solicitacao,
    st.codigo AS status_codigo
FROM tb_pergunta tp
JOIN tb_status st ON tp.fk_status = st.id_status
WHERE tp.id_pergunta = %s
LIMIT 1
"""

_ID_STATUS_PERGUNTA_RESPONDIDA = """
SELECT ts2.id_status
FROM tb_status ts2
WHERE ts2.codigo = 'RESPONDIDA' AND ts2.entidade = 'PERGUNTA'
LIMIT 1
"""

_ANSWER_PERGUNTA = """
UPDATE tb_pergunta
SET necessita_taxi = %s,
    qtd_passageiros = %s,
    necessita_acessibilidade = %s,
    qtd_criancas = %s,
    qtd_animais = %s,
    bagagem = %s,
    observacoes = %s,
    data_resposta = %s,
    version = version + 1,
    fk_status = %s
WHERE id_pergunta = %s AND version = %s
"""


def solicitacao_by_id(solicitacao_id: int) -> dict | None:
    return _fetch_one(_SOLICITACAO_BY_ID, (solicitacao_id,))


def apolice_resumo_by_id(apolice_id: int) -> dict | None:
    return _fetch_one(_APOLICE_RESUMO_BY_ID, (apolice_id,))


def assistencias_by_solicitacao(solicitacao_id: int) -> list[dict]:
    return _fetch_all(_ASSISTENCIAS_BY_SOLICITACAO, (solicitacao_id,))


def perguntas_by_solicitacao(solicitacao_id: int) -> list[dict]:
    return _fetch_all(_PERGUNTAS_BY_SOLICITACAO, (solicitacao_id,))


def historico_by_solicitacao(solicitacao_id: int) -> list[dict]:
    return _fetch_all(_HISTORICO_BY_SOLICITACAO, (solicitacao_id,))


def pergunta_by_id(id_pergunta: int) -> dict | None:
    return _fetch_one(_PERGUNTA_BY_ID, (id_pergunta,))


def _id_status_pergunta_respondida() -> int | None:
    row = _fetch_one(_ID_STATUS_PERGUNTA_RESPONDIDA, ())
    return row["id_status"] if row else None


def answer_pergunta(
    *,
    id_pergunta: int,
    necessita_taxi: bool,
    quantidade_passageiros: int | None,
    necessita_acessibilidade: bool | None,
    quantidade_criancas: int | None,
    quantidade_animais: int | None,
    bagagem: str | None,
    observacoes: str | None,
    data_resposta,
    version: int,
) -> bool:
    status_id = _id_status_pergunta_respondida()
    if status_id is None:
        raise RuntimeError("Status PERGUNTA/RESPONDIDA não encontrado no banco.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            _ANSWER_PERGUNTA,
            (
                necessita_taxi,
                quantidade_passageiros,
                necessita_acessibilidade,
                quantidade_criancas,
                quantidade_animais,
                bagagem,
                observacoes,
                data_resposta,
                status_id,
                id_pergunta,
                version,
            ),
        )
        affected = cur.rowcount
        sync_repo.bump_revision_cursor(cur, data_resposta)
        conn.commit()
        return affected == 1
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


_INSERT_LOCAL = """
INSERT INTO tb_solicitacao_local (endereco, numero_local, cidade, estado, ponto_referencia)
VALUES (%s, %s, %s, %s, %s)
"""

_INSERT_SOLICITACAO = """
INSERT INTO tb_solicitacao (
    id_solicitacao_cliente, protocolo_solicitacao, numero_solicitacao,
    descricao_evento, possui_feridos, risco_imediato, prioridade,
    data_criacao_cliente, data_recebimento, version,
    fk_apolice, fk_pessoa, fk_seguradora, fk_veiculo, fk_tipo_ocorrencia,
    fk_local, fk_status
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

_INSERT_HISTORICO = """
INSERT INTO tb_historico_status (
    status, data_status, comentario, nome_responsavel, fk_solicitacao
) VALUES ('RECEBIDA', %s, 'Solicitação recebida.', %s, %s)
"""

_UPDATE_APOLICE_ATIVA = """
UPDATE tb_apolice SET possui_solicitacao_ativa = 1 WHERE id_apolice = %s
"""


def _id_status_recebida() -> int | None:
    row = _fetch_one(_ID_STATUS_CREATE, ())
    return row["id_status"] if row else None


def create_solicitacao(
    *,
    id_solicitacao_cliente: str,
    protocolo_solicitacao: str,
    numero_solicitacao: str,
    descricao_evento: str,
    possui_feridos: bool,
    risco_imediato: bool,
    prioridade: str,
    data_criacao_cliente,
    data_recebimento,
    fk_apolice: int,
    fk_pessoa: int,
    fk_seguradora: int,
    fk_veiculo: int,
    fk_tipo_ocorrencia: int,
    endereco: str,
    numero_local: str,
    cidade: str,
    estado: str,
    ponto_referencia: str | None,
    nome_responsavel: str | None,
) -> int:
    status_id = _id_status_recebida()
    if status_id is None:
        raise RuntimeError("Status SOLICITACAO/RECEBIDA não encontrado no banco.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            _INSERT_LOCAL,
            (endereco, numero_local, cidade, estado, ponto_referencia),
        )
        fk_local = cur.lastrowid

        cur.execute(
            _INSERT_SOLICITACAO,
            (
                id_solicitacao_cliente, protocolo_solicitacao, numero_solicitacao,
                descricao_evento, 1 if possui_feridos else 0, 1 if risco_imediato else 0,
                prioridade, data_criacao_cliente, data_recebimento, 1,
                fk_apolice, fk_pessoa, fk_seguradora, fk_veiculo, fk_tipo_ocorrencia,
                fk_local, status_id,
            ),
        )
        id_solicitacao = cur.lastrowid

        cur.execute(_INSERT_HISTORICO, (data_recebimento, nome_responsavel, id_solicitacao))
        cur.execute(_UPDATE_APOLICE_ATIVA, (fk_apolice,))
        sync_repo.bump_revision_cursor(cur, data_recebimento)
        conn.commit()
        return id_solicitacao
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()