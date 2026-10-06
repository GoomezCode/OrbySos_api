from unittest import mock

from fastapi.testclient import TestClient

from main import app
from core.security import create_access_token
import repositories.admin_repository as admin_repo
import repositories.solicitacao_repository as solicitacao_repo

client = TestClient(app)


def _token(perfil="ANALISTA"):
    return create_access_token(
        subject=901,
        extra={
            "id_usuario": 901,
            "id_pessoa": 4,
            "perfil": perfil,
            "nome_exibicao": "Analista Horizonte",
            "seguradora": {"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"},
            "seguradoras": [{"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"}],
        },
    )


def _auth(perfil="ANALISTA"):
    return {"Authorization": f"Bearer {_token(perfil)}"}


def _row(**overrides):
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
        "version": 1,
        "fk_pessoa": 1,
        "fk_apolice_id": 1002,
        "fk_seguradora_id": 10,
        "fk_veiculo_id": 202,
        "fk_tipo_ocorrencia_id": 2,
        "fk_analista_responsavel": None,
        "status_codigo": "RECEBIDA",
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
        "analista_nome": None,
    }
    base.update(overrides)
    return base


def _apolice():
    return {"id_apolice": 1002, "numero_apolice_mascarado": "ORB-****-1002",
            "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"}


def _assistencia(**overrides):
    base = {
        "id_solicitacao_assistencia": 8010,
        "fk_solicitacao": 51,
        "status": "INCLUIDA",
        "comentario": None,
        "data_inclusao": None,
        "data_atualizacao": None,
        "version": 1,
        "id_tipo_assistencia": 1,
        "tipo_codigo": "GUINCHO",
        "tipo_nome": "Guincho",
        "id_usuario": 901,
        "nome_exibicao": "Analista Horizonte",
    }
    base.update(overrides)
    return base


def test_admin_requires_token():
    response = client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


def test_admin_requires_analista_perfil():
    response = client.get("/api/v1/admin/dashboard", headers=_auth(perfil="CLIENTE"))
    assert response.status_code == 403


def test_dashboard_ok():
    rows = [_row(status_codigo="RECEBIDA"), _row(id_solicitacao=52, status_codigo="CONCLUIDA")]
    with mock.patch.object(admin_repo, "find_solicitacoes", return_value=rows), \
         mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.get("/api/v1/admin/dashboard", headers=_auth())
    assert response.status_code == 200
    body = response.json()
    assert "metricas" in body
    assert body["fila_prioritaria"]["items"][0]["status"] == "RECEBIDA"


def test_solicitacoes_ok():
    rows = [_row()]
    with mock.patch.object(admin_repo, "find_solicitacoes", return_value=rows), \
         mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.get(
            "/api/v1/admin/solicitacoes",
            params={"status": "RECEBIDA", "page": 1, "page_size": 20},
            headers=_auth(),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total_items"] == 1
    assert body["items"][0]["cliente"]["nome"] == "Marina Exemplo"
    assert body["items"][0]["analista"] is None


def test_detalhe_solicitacao_ok():
    row = _row(fk_analista_responsavel=901, analista_nome="Analista Horizonte")
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(admin_repo, "tipos_assistencia_ativos", return_value=[
             {"id_tipo_assistencia": 1, "codigo": "GUINCHO", "nome": "Guincho",
              "descricao": "R.", "ativo": True},
         ]), \
         mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[_assistencia()]), \
         mock.patch.object(solicitacao_repo, "perguntas_by_solicitacao", return_value=[]), \
         mock.patch.object(solicitacao_repo, "historico_by_solicitacao", return_value=[]), \
         mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.get("/api/v1/admin/solicitacoes/51", headers=_auth())
    assert response.status_code == 200
    assert response.json()["solicitacao"]["numero_solicitacao"] == "ORB-2026-000051"
    assert response.json()["tipos_assistencia_disponiveis"][0]["codigo"] == "GUINCHO"


def test_detalhe_nao_encontrado():
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=None):
        response = client.get("/api/v1/admin/solicitacoes/9999", headers=_auth())
    assert response.status_code == 404


def test_tipos_assistencia_ok():
    with mock.patch.object(admin_repo, "tipos_assistencia_ativos", return_value=[
        {"id_tipo_assistencia": 1, "codigo": "GUINCHO", "nome": "Guincho", "descricao": "R.", "ativo": True},
    ]):
        response = client.get("/api/v1/admin/tipos-assistencia", headers=_auth())
    assert response.status_code == 200
    assert response.json()["items"][0]["codigo"] == "GUINCHO"


def test_assumir_ok():
    row = _row(status_codigo="RECEBIDA", version=1)
    updated = _row(status_codigo="EM_ANALISE", version=2, fk_analista_responsavel=901,
                   analista_nome="Analista Horizonte")
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
         mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/assumir",
            json={"version": 1},
            headers=_auth(),
        )
    assert response.status_code == 200
    assert response.json()["solicitacao"]["status"] == "EM_ANALISE"


def test_assumir_versao_conflitante():
    row = _row(status_codigo="RECEBIDA", version=4)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=False):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/assumir",
            json={"version": 1},
            headers=_auth(),
        )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "REQUEST_VERSION_CONFLICT"


def test_confirmar_transicao_invalida():
    row = _row(status_codigo="RECEBIDA", version=1, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/confirmar",
            json={"version": 1, "comentario": "ok"},
            headers=_auth(),
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_INVALID_STATUS_TRANSITION"


def test_recusar_motivo_obrigatorio():
    row = _row(status_codigo="EM_ANALISE", version=2, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/recusar",
            json={"version": 2, "motivo_recusa": "  "},
            headers=_auth(),
        )
    assert response.status_code == 422


def test_adicionar_assistencia_201():
    row = _row(status_codigo="CONFIRMADA", version=3, fk_analista_responsavel=901)
    updated = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    pergunta = {
        "id_pergunta": 7010, "origem": "GUINCHO", "tipo": "TAXI", "status_codigo": "PENDENTE",
        "necessita_taxi": None, "qtd_passageiros": None, "necessita_acessibilidade": None,
        "qtd_criancas": None, "qtd_animais": None, "bagagem": None, "observacoes": None,
        "data_criacao": None, "data_resposta": None, "version": 1,
    }
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(admin_repo, "tipo_assistencia_by_id",
                           return_value={"id_tipo_assistencia": 1, "codigo": "GUINCHO",
                                         "nome": "Guincho", "descricao": "R.", "ativo": True}), \
         mock.patch.object(admin_repo, "add_assistencia", return_value={
             "assistencia": _assistencia(), "pergunta_id": 7010,
         }), \
         mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=pergunta), \
         mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=_apolice()):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/assistencias",
            json={"tipo_assistencia_id": 1, "comentario": "pos cobertura", "request_version": 3},
            headers=_auth(),
        )
    assert response.status_code == 201
    body = response.json()
    assert body["assistencia"]["status"] == "INCLUIDA"
    assert body["pergunta_criada"]["status"] == "PENDENTE"
    assert body["solicitacao"]["status"] == "EM_ATENDIMENTO"


def test_adicionar_assistencia_tipo_invalido():
    row = _row(status_codigo="CONFIRMADA", version=3, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(admin_repo, "tipo_assistencia_by_id", return_value=None):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/assistencias",
            json={"tipo_assistencia_id": 99, "request_version": 3},
            headers=_auth(),
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_patch_assistencia_ok():
    assistencia = _assistencia()
    row = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    atualizada = {
        "status": "PRESTADOR_ACIONADO", "comentario": "Protocolo DEMO-1.",
        "data_atualizacao": None, "version": 2, "id_usuario": 901,
        "nome_exibicao": "Analista Horizonte", "fk_solicitacao": 51,
    }
    with mock.patch.object(admin_repo, "assistencia_by_id", return_value=assistencia), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(admin_repo, "update_assistencia_status", return_value=atualizada):
        response = client.patch(
            "/api/v1/admin/solicitacao-assistencias/8010",
            json={"status": "PRESTADOR_ACIONADO", "comentario": "Protocolo DEMO-1.", "version": 1},
            headers=_auth(),
        )
    assert response.status_code == 200
    assert response.json()["assistencia"]["status"] == "PRESTADOR_ACIONADO"


def test_patch_assistencia_versao_conflitante():
    assistencia = _assistencia(version=3)
    row = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    with mock.patch.object(admin_repo, "assistencia_by_id", return_value=assistencia), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        response = client.patch(
            "/api/v1/admin/solicitacao-assistencias/8010",
            json={"status": "PRESTADOR_ACIONADO", "comentario": "x", "version": 1},
            headers=_auth(),
        )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ASSISTANCE_VERSION_CONFLICT"


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
    print(f"\nADMIN_ROUTES_TESTS_OK ({len(tests)} testes)")