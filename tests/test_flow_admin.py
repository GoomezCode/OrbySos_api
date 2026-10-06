from unittest import mock

from fastapi.testclient import TestClient

from main import app
from core.security import hash_password
import repositories.admin_repository as admin_repo
import repositories.solicitacao_repository as solicitacao_repo
import repositories.user_repository as user_repo

client = TestClient(app)

SENHA = "senha-segura-123"

ANALYST_ROW = {
    "id_user": 901,
    "fk_pessoa": 4,
    "login": "analista.horizonte",
    "perfil": "ANALISTA",
    "fk_status": 8,
    "nome_exibicao": "Analista Horizonte",
    "email": "analista@example.com",
    "fk_seguradora": 10,
    "status_codigo": "ATIVO",
    "senha": hash_password(SENHA),
}

INSURERS = [{"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"}]

SESSÃO_REAL = None


def _row(status="RECEBIDA", version=1, **overrides):
    base = {
        "id_solicitacao": 51,
        "id_solicitacao_cliente": "00000000-0000-4000-8000-000000000051",
        "numero_solicitacao": "ORB-2026-000051",
        "protocolo_solicitacao": "ORB-2026-000051",
        "descricao_evento": "Cenario ficticio critico.",
        "possui_feridos": True,
        "risco_imediato": False,
        "prioridade": "CRITICA",
        "data_criacao_cliente": None,
        "data_recebimento": None,
        "data_decisao": None,
        "motivo_recusa": None,
        "version": version,
        "fk_pessoa": 1,
        "fk_apolice_id": 1002,
        "fk_seguradora_id": 10,
        "fk_veiculo_id": 202,
        "fk_tipo_ocorrencia_id": 2,
        "fk_analista_responsavel": 901,
        "status_codigo": status,
        "isJuridico": 0,
        "endereco": "Avenida Modelo",
        "numero_local": "100",
        "cidade": "Cidade Exemplo",
        "estado": "SP",
        "ponto_referencia": None,
        "cliente_nome": "Marina Exemplo",
        "cliente_cpf": "***.444.***-**",
        "id_veiculo": 202,
        "marca": "Marca Demo",
        "modelo": "Modelo Prata",
        "versao": None,
        "ano_fabricado": 2021,
        "ano_modelo": 2022,
        "placa_mascarada": "TST-****",
        "blindado": False,
        "ocorrencia_codigo": "ACIDENTE",
        "ocorrencia_nome": "Acidente",
        "ocorrencia_descricao": "Colisao.",
        "seguradora_nome": "Seguradora Horizonte",
        "analista_nome": "Analista Horizonte",
    }
    if status != "RECEBIDA":
        base["fk_analista_responsavel"] = 901
        base["analista_nome"] = "Analista Horizonte"
    base.update(overrides)
    return base


def _apolice():
    return {"id_apolice": 1002, "numero_apolice_mascarado": "ORB-****-1002",
            "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"}


def _assistencia(status="INCLUIDA", version=1, **overrides):
    base = {
        "id_solicitacao_assistencia": 8010,
        "fk_solicitacao": 51,
        "status": status,
        "comentario": None,
        "data_inclusao": None,
        "data_atualizacao": None,
        "version": version,
        "id_tipo_assistencia": 1,
        "tipo_codigo": "GUINCHO",
        "tipo_nome": "Guincho",
        "id_usuario": 901,
        "nome_exibicao": "Analista Horizonte",
    }
    base.update(overrides)
    return base


def _pergunta(status="PENDENTE", version=1):
    return {
        "id_pergunta": 7001, "origem": "GUINCHO", "tipo": "TAXI", "status_codigo": status,
        "necessita_taxi": None, "qtd_passageiros": None, "necessita_acessibilidade": None,
        "qtd_criancas": None, "qtd_animais": None, "bagagem": None, "observacoes": None,
        "data_criacao": None, "data_resposta": None, "version": version,
    }


def _historico(status):
    return {
        "id_historico": 1, "status": status, "data_status": None, "comentario": None,
        "nome_responsavel": "Analista Horizonte", "fk_usuario_responsavel": 901,
    }


def test_fluxo_admin_completo():
    with mock.patch.object(user_repo, "find_analyst_by_login", return_value=ANALYST_ROW), \
         mock.patch.object(user_repo, "find_analyst_insurers", return_value=INSURERS):
        response = client.post(
            "/api/v1/auth/analistas/login",
            json={"login": "analista.horizonte", "senha": SENHA},
        )
    assert response.status_code == 200
    envelope = response.json()
    token = envelope["access_token"]
    assert envelope["session"]["perfil"] == "ANALISTA"
    headers = {"Authorization": f"Bearer {token}"}

    with \
        mock.patch.object(admin_repo, "find_solicitacoes", return_value=[_row(status="RECEBIDA", version=1)]), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.get("/api/v1/admin/dashboard", headers=headers)
    assert response.status_code == 200
    assert response.json()["metricas"]["aguardando_analise"] == 1
    assert response.json()["fila_prioritaria"]["items"][0]["status"] == "RECEBIDA"

    row_recebida = _row(status="RECEBIDA", version=1)
    row_analise = _row(status="EM_ANALISE", version=2)
    with \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row_recebida, row_analise]), \
        mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/assumir",
            json={"version": 1},
            headers=headers,
        )
    assert response.status_code == 200
    assert response.json()["solicitacao"]["status"] == "EM_ANALISE"

    row_confirmada = _row(status="CONFIRMADA", version=3, data_decisao=None, motivo_recusa=None)
    with \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row_analise, row_confirmada]), \
        mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/confirmar",
            json={"version": 2, "comentario": "Cobertura confirmada."},
            headers=headers,
        )
    assert response.status_code == 200
    assert response.json()["solicitacao"]["status"] == "CONFIRMADA"

    row_atendimento = _row(status="EM_ATENDIMENTO", version=4)
    with \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row_confirmada, row_atendimento]), \
        mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/iniciar-atendimento",
            json={"version": 3, "comentario": "Iniciando atendimento."},
            headers=headers,
        )
    assert response.status_code == 200
    assert response.json()["solicitacao"]["status"] == "EM_ATENDIMENTO"

    add_result = {
        "assistencia": _assistencia(status="INCLUIDA", version=1),
        "pergunta_id": 7001,
    }
    with \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row_atendimento, row_atendimento]), \
        mock.patch.object(admin_repo, "tipo_assistencia_by_id",
                          return_value={"id_tipo_assistencia": 1, "codigo": "GUINCHO",
                                        "nome": "Guincho", "descricao": "R.", "ativo": True}), \
        mock.patch.object(admin_repo, "add_assistencia", return_value=add_result), \
        mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=_pergunta()), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/assistencias",
            json={"tipo_assistencia_id": 1, "comentario": "pos cobertura", "request_version": 4},
            headers=headers,
        )
    assert response.status_code == 201
    body = response.json()
    assert body["assistencia"]["status"] == "INCLUIDA"
    assert body["pergunta_criada"]["status"] == "PENDENTE"
    assert body["solicitacao"]["status"] == "EM_ATENDIMENTO"

    atualizada = {
        "status": "CONCLUIDA", "comentario": "Guincho concluido.",
        "data_atualizacao": None, "version": 2, "id_usuario": 901,
        "nome_exibicao": "Analista Horizonte", "fk_solicitacao": 51,
    }
    with \
        mock.patch.object(admin_repo, "assistencia_by_id", return_value=_assistencia(status="EM_DESLOCAMENTO", version=1)), \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row_atendimento), \
        mock.patch.object(admin_repo, "update_assistencia_status", return_value=atualizada):
        response = client.patch(
            "/api/v1/admin/solicitacao-assistencias/8010",
            json={"status": "CONCLUIDA", "comentario": "Guincho concluido.", "version": 1},
            headers=headers,
        )
    assert response.status_code == 200
    assert response.json()["assistencia"]["status"] == "CONCLUIDA"

    row_concluida = _row(status="CONCLUIDA", version=5, data_decisao=None, motivo_recusa=None)
    with \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row_atendimento, row_concluida]), \
        mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[
            _assistencia(status="CONCLUIDA", version=2),
        ]), \
        mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/concluir",
            json={"version": 4, "comentario": "Encerrado."},
            headers=headers,
        )
    assert response.status_code == 200
    assert response.json()["solicitacao"]["status"] == "CONCLUIDA"

    with \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row_concluida), \
        mock.patch.object(admin_repo, "tipos_assistencia_ativos", return_value=[
            {"id_tipo_assistencia": 1, "codigo": "GUINCHO", "nome": "Guincho",
             "descricao": "R.", "ativo": True},
        ]), \
        mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[
            _assistencia(status="CONCLUIDA", version=2),
        ]), \
        mock.patch.object(solicitacao_repo, "perguntas_by_solicitacao", return_value=[
            _pergunta(status="RESPONDIDA", version=2),
        ]), \
        mock.patch.object(solicitacao_repo, "historico_by_solicitacao", return_value=[
            _historico("RECEBIDA"), _historico("EM_ANALISE"), _historico("CONFIRMADA"),
            _historico("EM_ATENDIMENTO"), _historico("CONCLUIDA"),
        ]), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.get("/api/v1/admin/solicitacoes/51", headers=headers)
    assert response.status_code == 200
    detalhe = response.json()
    assert detalhe["solicitacao"]["status"] == "CONCLUIDA"
    assert detalhe["perguntas"][0]["status"] == "RESPONDIDA"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = []
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failed.append(test.__name__)
            print(f"FAIL  {test.__name__}: {exc}")
        except Exception as exc:
            failed.append(test.__name__)
            print(f"ERROR {test.__name__}: {type(exc).__name__}: {exc}")
    if failed:
        raise SystemExit(f"Falhou: {failed}")
    print(f"\nFLOW_ADMIN_TESTS_OK ({len(tests)} testes)")