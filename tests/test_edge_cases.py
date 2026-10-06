from unittest import mock

from fastapi.testclient import TestClient

from main import app
from core.security import create_access_token
import repositories.client_repository as client_repo
import repositories.solicitacao_repository as solicitacao_repo

client = TestClient(app, raise_server_exceptions=False)


def _token(perfil="CLIENTE", pessoa_id=1):
    if perfil == "ANALISTA":
        return create_access_token(
            subject=901,
            extra={
                "id_usuario": 901,
                "id_pessoa": 4,
                "perfil": "ANALISTA",
                "nome_exibicao": "Analista Horizonte",
                "seguradora": {"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"},
                "seguradoras": [{"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"}],
            },
        )
    return create_access_token(
        subject=801 if perfil == "CLIENTE" else 901,
        extra={
            "id_usuario": 801 if perfil == "CLIENTE" else 901,
            "id_pessoa": pessoa_id,
            "perfil": perfil,
            "nome_exibicao": "Marina",
            "seguradora": None,
            "seguradoras": [],
        },
    )


def _auth(perfil="CLIENTE", **kw):
    return {"Authorization": f"Bearer {_token(perfil, **kw)}"}


def _assert_envelope(response, http_status, code):
    assert response.status_code == http_status
    body = response.json()
    assert "error" in body
    assert "trace_id" in body
    assert body["trace_id"].startswith("trace-")
    assert body["error"]["code"] == code
    assert "message" in body["error"]
    return body


def _payload(uid="uuid-edge-1"):
    return {
        "id_solicitacao_cliente": uid,
        "apolice_id": 10,
        "tipo_ocorrencia_id": 1,
        "descricao_evento": "Falha",
        "possui_feridos": False,
        "risco_imediato": False,
        "local": {"endereco": "Rua A", "numero_local": "10", "cidade": "SP", "estado": "SP", "ponto_referencia": None},
        "data_criacao_cliente": "2026-08-11T15:00:00Z",
    }


def test_401_missing_token_uses_envelope():
    response = client.get("/api/v1/clientes/me")
    _assert_envelope(response, 401, "UNAUTHORIZED")


def test_401_invalid_token_uses_envelope():
    response = client.get("/api/v1/clientes/me", headers={"Authorization": "Bearer token.invalido"})
    _assert_envelope(response, 401, "INVALID_TOKEN")


def test_403_cliente_vs_rota_analista_uses_envelope():
    response = client.get("/api/v1/admin/dashboard", headers=_auth(perfil="CLIENTE"))
    _assert_envelope(response, 403, "FORBIDDEN")


def test_404_nao_encontrado_uses_envelope():
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=None):
        response = client.get("/api/v1/solicitacoes/9999", headers=_auth())
    _assert_envelope(response, 404, "NOT_FOUND")


def test_409_policy_active_request_uses_envelope():
    with \
        mock.patch.object(client_repo, "request_by_client_uuid", return_value={"id_solicitacao": 1}), \
        mock.patch.object(client_repo, "policy_by_id_for_pessoa", return_value=None), \
        mock.patch.object(client_repo, "occurrence_by_id", return_value={"ativo": 1}):
        response = client.post(
            "/api/v1/solicitacoes",
            json=_payload(uid="uuid-edge-2"),
            headers={**_auth(), "Idempotency-Key": "uuid-edge-2"},
        )
    _assert_envelope(response, 409, "POLICY_ACTIVE_REQUEST_EXISTS")


def test_422_login_validation_has_fields():
    response = client.post("/api/v1/auth/clientes/login", json={"cpf": "", "senha": "x"})
    body = _assert_envelope(response, 422, "VALIDATION_ERROR")
    assert isinstance(body["error"]["fields"], list)
    assert any(f["field"] == "cpf" for f in body["error"]["fields"])


def test_422_pydantic_field_errors_on_create_solicitacao():
    with mock.patch.object(client_repo, "request_by_client_uuid", return_value=None):
        response = client.post(
            "/api/v1/solicitacoes",
            json={
                "id_solicitacao_cliente": "uuid-edge-3",
                "apolice_id": "nao-numero",
                "tipo_ocorrencia_id": 1,
                "descricao_evento": "Falha",
                "possui_feridos": "nao-booleano",
                "risco_imediato": False,
                "local": {"endereco": "", "numero_local": "10", "cidade": "SP", "estado": "SP", "ponto_referencia": None},
                "data_criacao_cliente": "2026-08-11T15:00:00Z",
            },
            headers={**_auth(), "Idempotency-Key": "uuid-edge-3"},
        )
    body = _assert_envelope(response, 422, "VALIDATION_ERROR")
    fields = {f["field"]: f["message"] for f in body["error"]["fields"]}
    assert "apolice_id" in fields
    assert "possui_feridos" in fields


def test_500_unhandled_error_uses_envelope():
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=RuntimeError("db down")):
        response = client.get("/api/v1/solicitacoes/51", headers=_auth())
    body = _assert_envelope(response, 500, "INTERNAL_ERROR")
    assert "RuntimeError" not in body["error"]["message"]


def test_422_admin_transicao_invalida_uses_envelope():
    row = {
        "id_solicitacao": 51, "fk_seguradora_id": 10, "fk_analista_responsavel": 901,
        "status_codigo": "RECEBIDA", "version": 1,
    }
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        response = client.post(
            "/api/v1/admin/solicitacoes/51/confirmar",
            json={"version": 1, "comentario": "ok"},
            headers=_auth(perfil="ANALISTA"),
        )
    _assert_envelope(response, 422, "REQUEST_INVALID_STATUS_TRANSITION")


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
    print(f"\nEDGE_CASES_TESTS_OK ({len(tests)} testes)")