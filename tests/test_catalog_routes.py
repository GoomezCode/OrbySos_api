import json
from unittest import mock

from fastapi.testclient import TestClient

from main import app
from core.security import create_access_token
import repositories.catalog_repository as catalog_repo

client = TestClient(app)

OCCURRENCE_ROWS = [
    {"id_ocorrencia": 1, "codigo": "PANE_MECANICA", "nome": "Pane mecânica", "descricao": "Falha mecânica.", "ativo": 1},
    {"id_ocorrencia": 5, "codigo": "OUTRO", "nome": "Outro", "descricao": "Outra ocorrência.", "ativo": 0},
]

CONFIG_ROW = {
    "pais": "BR",
    "mensagem": "Orbyt Assistência 24h.",
    "servicos_json": json.dumps([
        {"codigo": "SAMU", "nome": "SAMU", "telefone": "192"},
    ]),
}


def token():
    return create_access_token(
        subject=801,
        extra={
            "id_usuario": 801,
            "id_pessoa": 1,
            "perfil": "CLIENTE",
            "nome_exibicao": "Marina Exemplo",
            "seguradora": None,
            "seguradoras": [],
        },
    )


def test_tipos_ocorrencia_requires_token():
    with mock.patch.object(catalog_repo, "find_occurrences", return_value=[]):
        assert client.get("/api/v1/tipos-ocorrencia").status_code == 401


def test_tipos_ocorrencia_returns_items():
    with mock.patch.object(catalog_repo, "find_occurrences", return_value=OCCURRENCE_ROWS):
        response = client.get(
            "/api/v1/tipos-ocorrencia",
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["items"][0]["codigo"] == "PANE_MECANICA"
    assert body["items"][0]["ativo"] is True
    assert "schema_version" not in body


def test_tipos_ocorrencia_passes_ativo_query():
    with mock.patch.object(catalog_repo, "find_occurrences", return_value=[OCCURRENCE_ROWS[0]]) as mk:
        response = client.get(
            "/api/v1/tipos-ocorrencia",
            params={"ativo": "true"},
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code == 200
    assert mk.call_args == mock.call(True)
    assert len(response.json()["items"]) == 1


def test_configuracoes_publicas_requires_token():
    with mock.patch.object(catalog_repo, "get_app_configuration", return_value=CONFIG_ROW):
        assert client.get("/api/v1/configuracoes/publicas").status_code == 401


def test_configuracoes_publicas_returns_dto():
    with mock.patch.object(catalog_repo, "get_app_configuration", return_value=CONFIG_ROW):
        response = client.get(
            "/api/v1/configuracoes/publicas",
            headers={"Authorization": f"Bearer {token()}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["pais"] == "BR"
    assert body["servicos"][0]["telefone"] == "192"
    assert "response" not in body


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = []
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception as exc:
            failed.append(test.__name__)
            print(f"FAIL  {test.__name__}: {type(exc).__name__}: {exc}")
    if failed:
        raise SystemExit(f"Falhou: {failed}")
    print(f"\nCATALOG_ROUTES_TESTS_OK ({len(tests)} testes)")