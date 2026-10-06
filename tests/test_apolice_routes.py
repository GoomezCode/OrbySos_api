from unittest import mock

from fastapi.testclient import TestClient

from main import app
from core.security import create_access_token
import repositories.apolice_repository as apolice_repo
import repositories.client_repository as client_repo

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
        "id_apolice": 1001,
        "numero_apolice": "ORB-2026-1001",
        "numero_apolice_mascarado": "ORB-****-1001",
        "data_inicio": None,
        "data_fim": None,
        "cobertura": 50000.0,
        "assistencia": "Guincho",
        "endosso": None,
        "perfil": "Particular",
        "versao": 1,
        "possui_solicitacao_ativa": 0,
        "fk_pessoa_id": 1,
        "fk_segurado_id": 10,
        "fk_veiculo_id": 201,
        "fk_local_pernoite_id": 1,
        "fk_forma_pagamento_id": 1,
        "apolice_status": "ATIVA",
        "isJuridico": 0,
        "cliente_nome": "Marina Exemplo",
        "cliente_cpf": "***.444.***-**",
        "cliente_razao_social": None,
        "cliente_nome_fantasia": None,
        "cliente_cnpj": None,
        "seguradora_nome_fantasia": "Seguradora Horizonte",
        "id_veiculo": 201,
        "marca": "Marca Exemplo",
        "modelo": "Modelo A",
        "veiculo_versao": "1.0",
        "ano_fabricado": 2023,
        "ano_modelo": 2024,
        "placa": "ABC1A23",
        "placa_mascarada": "ABC-1*23",
        "blindado": 0,
        "local_pernoite": "Garagem Residencial Fechada",
        "forma_pagamento": "Pix",
    }
    base.update(overrides)
    return base


def _create_payload(**overrides):
    payload = {
        "numero_apolice": "ORB-2026-7777",
        "fk_pessoa": 1,
        "fk_segurado": 10,
        "fk_veiculo": 201,
        "data_inicio": "2026-01-01T00:00:00Z",
        "data_fim": "2026-12-31T00:00:00Z",
        "cobertura": 50000.0,
        "assistencia": "Guincho",
        "endosso": None,
        "perfil": "Particular",
        "fk_local_pernoite": 1,
        "fk_forma_pagamento": 1,
    }
    payload.update(overrides)
    return payload


def test_listar_requer_token():
    with mock.patch.object(apolice_repo, "find_apolices") as find:
        resp = client.get("/api/v1/admin/apolices")
    assert resp.status_code == 401
    find.assert_not_called()


def test_listar_requer_perfil_analista():
    with mock.patch.object(apolice_repo, "find_apolices") as find:
        resp = client.get("/api/v1/admin/apolices", headers=_auth("CLIENTE"))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"
    find.assert_not_called()


def test_listar_retorna_items_paginados():
    with mock.patch.object(apolice_repo, "find_apolices", return_value=[_row()]) as find:
        resp = client.get("/api/v1/admin/apolices?status=ATIVA&page=1&page_size=20", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert body["pagination"]["total_items"] == 1
    assert body["items"][0]["id_apolice"] == 1001
    assert body["items"][0]["status"] == "ATIVA"
    find.assert_called_once()


def test_detalhe_retorna_aggregate():
    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row()):
        with mock.patch.object(client_repo, "contatos_by_pessoa", return_value=[]):
            resp = client.get("/api/v1/admin/apolices/1001", headers=_auth())
    assert resp.status_code == 200
    body = resp.json()
    assert body["apolice"]["numero_apolice_mascarado"] == "ORB-****-1001"
    assert body["apolice"]["cliente"]["nome"] == "Marina Exemplo"
    assert body["apolice"]["seguradora"]["nome_fantasia"] == "Seguradora Horizonte"


def test_detalhe_inexistente_404():
    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=None):
        resp = client.get("/api/v1/admin/apolices/1", headers=_auth())
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "POLICY_NOT_FOUND"


def test_criar_ok_201():
    with mock.patch.object(apolice_repo, "create_apolice", return_value=_row(numero_apolice="ORB-2026-7777")) as create:
        resp = client.post("/api/v1/admin/apolices", json=_create_payload(), headers=_auth())
    assert resp.status_code == 201
    body = resp.json()
    assert body["apolice"]["id_apolice"] == 1001
    create.assert_called_once()


def test_criar_validacao_422():
    with mock.patch.object(apolice_repo, "create_apolice") as create:
        resp = client.post(
            "/api/v1/admin/apolices",
            json=_create_payload(numero_apolice=""),
            headers=_auth(),
        )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    create.assert_not_called()


def test_atualizar_ok_200():
    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row(versao=1)):
        with mock.patch.object(apolice_repo, "update_apolice", return_value=_row(versao=2)) as update:
            resp = client.patch(
                "/api/v1/admin/apolices/1001",
                json={"version": 1, "cobertura": 999.0},
                headers=_auth(),
            )
    assert resp.status_code == 200
    assert resp.json()["apolice"]["versao"] == 2
    update.assert_called_once()


def test_atualizar_version_conflito_409():
    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row(versao=5)):
        resp = client.patch(
            "/api/v1/admin/apolices/1001",
            json={"version": 1, "cobertura": 999.0},
            headers=_auth(),
        )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "POLICY_VERSION_CONFLICT"


def test_status_ok_200():
    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row(versao=1, apolice_status="ATIVA")):
        with mock.patch.object(apolice_repo, "update_apolice_status", return_value=_row(versao=2, apolice_status="SUSPENSA")) as upd:
            resp = client.post(
                "/api/v1/admin/apolices/1001/status",
                json={"version": 1, "status": "SUSPENSA"},
                headers=_auth(),
            )
    assert resp.status_code == 200
    assert resp.json()["apolice"]["status"] == "SUSPENSA"
    upd.assert_called_once()


def test_status_invalido_409():
    resp = client.post(
        "/api/v1/admin/apolices/1001/status",
        json={"version": 1, "status": "REMOVIDA"},
        headers=_auth(),
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "INVALID_POLICY_STATUS"


if __name__ == "__main__":
    import sys, traceback

    failures = 0
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"{name}: OK")
            except Exception:
                failures += 1
                print(f"{name}: FALHOU")
                traceback.print_exc()
    print(f"\nAPOLICE_ROUTES_TESTS_OK" if failures == 0 else f"\n{failures} FALHAS")
    sys.exit(1 if failures else 0)