from fastapi.testclient import TestClient

from main import app
from core.security import create_access_token

client = TestClient(app)


def token_cliente():
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


def token_analista():
    return create_access_token(
        subject=901,
        extra={
            "id_usuario": 901,
            "id_pessoa": 101,
            "perfil": "ANALISTA",
            "nome_exibicao": "Analista Horizonte",
            "seguradora": {"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"},
            "seguradoras": [
                {"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"},
                {"id_pj": 20, "nome_fantasia": "Seguradora Orbita"},
            ],
        },
    )


def test_login_endpoints_public():
    assert client.post("/api/v1/auth/clientes/login", json={"cpf": "000", "senha": "x"}).status_code != 401
    assert client.post("/api/v1/auth/analistas/login", json={"login": "x", "senha": "x"}).status_code != 401


def test_login_client_invalid_cpf_is_401():
    response = client.post(
        "/api/v1/auth/clientes/login",
        json={"cpf": "11122233344", "senha": "qualquer"},
    )
    assert response.status_code == 401


def test_login_validation_422_when_body_invalid():
    response = client.post("/api/v1/auth/clientes/login", json={})
    assert response.status_code == 422
    response = client.post("/api/v1/auth/analistas/login", json={"login": ""})
    assert response.status_code == 422


def test_me_requires_token():
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_with_cliente_token():
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_cliente()}"})
    assert response.status_code == 200
    session = response.json()["session"]
    assert session["perfil"] == "CLIENTE"
    assert session["id_usuario"] == 801
    assert session["seguradoras"] == []


def test_me_with_analista_token():
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_analista()}"})
    assert response.status_code == 200
    session = response.json()["session"]
    assert session["perfil"] == "ANALISTA"
    assert session["seguradora"]["id_pj"] == 10
    assert len(session["seguradoras"]) == 2


def test_logout_requires_token():
    assert client.post("/api/v1/auth/logout").status_code == 401


def test_logout_returns_204_with_token():
    response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token_cliente()}"})
    assert response.status_code == 204


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
    print(f"\nAUTH_ROUTES_TESTS_OK ({len(tests)} testes)")