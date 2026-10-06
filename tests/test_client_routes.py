from unittest import mock

from fastapi.testclient import TestClient

from main import app
from core.security import create_access_token
import repositories.client_repository as client_repo
import repositories.solicitacao_repository as solicitacao_repo
import services.client_service as svc

client = TestClient(app)

SESSION = {
    "id_usuario": 801,
    "id_pessoa": 1,
    "perfil": "CLIENTE",
    "nome_exibicao": "Marina",
}

PERSON = {"id_pessoa": 1, "isJuridico": 0}
PF = {"id_pf": 1, "nome": "Marina", "cpf": "12345678909", "cpf_mascarado": "***.444.***-**", "data_criacao": None}
CONTATOS = [{"tipo_contato": "CELULAR", "valor_contato": "11999990000", "principal": 1, "rotulo": None}]


def token():
    return create_access_token(
        subject=801,
        extra={
            "id_usuario": 801,
            "id_pessoa": 1,
            "perfil": "CLIENTE",
            "nome_exibicao": "Marina",
            "seguradora": None,
            "seguradoras": [],
        },
    )


def test_clientes_me_requires_token():
    with mock.patch.object(client_repo, "person_by_id", return_value=None):
        assert client.get("/api/v1/clientes/me").status_code == 401


def test_clientes_me_returns_perfil():
    with mock.patch.object(client_repo, "person_by_id", return_value=PERSON), \
         mock.patch.object(client_repo, "contatos_by_pessoa", return_value=CONTATOS), \
         mock.patch.object(client_repo, "pessoa_fisica_by_id", return_value=PF):
        response = client.get(
            "/api/v1/clientes/me",
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["tipo_pessoa"] == "FISICA"
    assert body["contatos"][0]["valor_mascarado"] == "11999990000"
    assert "response" not in body


def test_clientes_me_apolices_requires_token():
    with mock.patch.object(client_repo, "person_by_id", return_value=None):
        assert client.get("/api/v1/clientes/me/apolices").status_code == 401


def test_clientes_me_apolices_returns_paginated():
    with mock.patch.object(client_repo, "person_by_id", return_value=PERSON), \
         mock.patch.object(client_repo, "pessoa_fisica_by_id", return_value=PF), \
         mock.patch.object(client_repo, "policies_by_pessoa", return_value=[]), \
         mock.patch.object(client_repo, "contatos_by_pessoa", return_value=[]):
        response = client.get(
            "/api/v1/clientes/me/apolices",
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code == 200
    assert response.json()["pagination"]["total_items"] == 0


def test_solicitacoes_requires_idempotency_key():
    with mock.patch.object(client_repo, "request_by_client_uuid", return_value=None):
        response = client.post(
            "/api/v1/solicitacoes",
            json={
                "id_solicitacao_cliente": "uuid-1",
                "apolice_id": 10,
                "tipo_ocorrencia_id": 1,
                "descricao_evento": "Falha",
                "possui_feridos": False,
                "risco_imediato": False,
                "local": {"endereco": "Rua A", "numero_local": "10", "cidade": "SP", "estado": "SP", "ponto_referencia": None},
                "data_criacao_cliente": "2026-08-11T15:00:00Z",
            },
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code in (422, 409)


def test_solicitacoes_idempotency_key_mismatch():
    response = client.post(
        "/api/v1/solicitacoes",
        json={
            "id_solicitacao_cliente": "uuid-aaa",
            "apolice_id": 10,
            "tipo_ocorrencia_id": 1,
            "descricao_evento": "Falha",
            "possui_feridos": False,
            "risco_imediato": False,
            "local": {"endereco": "Rua A", "numero_local": "10", "cidade": "SP", "estado": "SP", "ponto_referencia": None},
            "data_criacao_cliente": "2026-08-11T15:00:00Z",
        },
        headers={
            "Authorization": f"Bearer {token()}",
            "Idempotency-Key": "uuid-bbb",
        },
    )
    assert response.status_code == 422


def test_solicitacoes_requires_token():
    response = client.post(
        "/api/v1/solicitacoes",
        json={
            "id_solicitacao_cliente": "uuid-1",
            "apolice_id": 10,
            "tipo_ocorrencia_id": 1,
            "descricao_evento": "Falha",
            "possui_feridos": False,
            "risco_imediato": False,
            "local": {"endereco": "Rua A", "numero_local": "10", "cidade": "SP", "estado": "SP", "ponto_referencia": None},
            "data_criacao_cliente": "2026-08-11T15:00:00Z",
        },
        headers={"Idempotency-Key": "uuid-1"},
    )
    assert response.status_code == 401


def test_clientes_me_solicitacoes_requires_token():
    with mock.patch.object(client_repo, "requests_by_pessoa", return_value=[]):
        assert client.get("/api/v1/clientes/me/solicitacoes").status_code == 401


def test_clientes_me_solicitacoes_returns_list():
    with mock.patch.object(client_repo, "requests_by_pessoa", return_value=[]):
        response = client.get(
            "/api/v1/clientes/me/solicitacoes",
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code == 200
    assert response.json()["pagination"]["total_items"] == 0


def test_solicitacao_detalhe_404_for_nonexistent():
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=None):
        response = client.get(
            "/api/v1/solicitacoes/9999",
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code == 404


def test_solicitacao_detalhe_404_for_wrong_owner():
    row = {"fk_pessoa": 999, "isJuridico": 0, "fk_apolice_id": 10, "fk_seguradora_id": 5, "id_veiculo": 1}
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        response = client.get(
            "/api/v1/solicitacoes/1",
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code == 404


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
    print(f"\nCLIENT_ROUTES_TESTS_OK ({len(tests)} testes)")
