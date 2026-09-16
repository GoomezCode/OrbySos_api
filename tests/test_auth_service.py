from unittest import mock

from validate_docbr import CPF

from core.security import hash_password, decode_access_token
import services.auth_service as auth_service
import repositories.user_repository as user_repo

cpf_valid = CPF().generate(mask=False)
senha_ok = "senha-segura-123"
hash_ok = hash_password(senha_ok)

CLIENT_ROW = {
    "id_user": 801,
    "fk_pessoa": 1,
    "login": cpf_valid,
    "perfil": "CLIENTE",
    "fk_status": 8,
    "nome_exibicao": "Marina Exemplo",
    "email": "marina@example.com",
    "status_codigo": "ATIVO",
    "nome": "Marina Exemplo",
    "cpf": cpf_valid,
    "cpf_mascarado": "***.444.***-**",
    "senha": hash_ok,
}

ANALYST_ROW = {
    "id_user": 901,
    "fk_pessoa": 101,
    "login": "analista.horizonte",
    "perfil": "ANALISTA",
    "fk_status": 8,
    "nome_exibicao": "Analista Horizonte",
    "email": "analista@example.com",
    "fk_seguradora": 10,
    "status_codigo": "ATIVO",
    "senha": hash_ok,
}

INSURERS = [
    {"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"},
    {"id_pj": 20, "nome_fantasia": "Seguradora Orbita"},
]


def test_login_client_success():
    with mock.patch.object(user_repo, "find_client_by_cpf", return_value=CLIENT_ROW):
        envelope = auth_service.login_client(cpf_valid, senha_ok)
    assert envelope.token_type == "Bearer"
    assert envelope.expires_in == 3600
    assert envelope.session.perfil == "CLIENTE"
    assert envelope.session.id_usuario == 801
    assert envelope.session.id_pessoa == 1
    assert envelope.session.nome_exibicao == "Marina Exemplo"
    assert envelope.session.seguradoras == []
    assert decode_access_token(envelope.access_token)["perfil"] == "CLIENTE"


def test_login_client_invalid_cpf():
    try:
        auth_service.login_client("11122233344", senha_ok)
        assert False, "deveria ter levantado 401"
    except Exception as exc:
        assert exc.status_code == 401


def test_login_client_unknown_cpf():
    with mock.patch.object(user_repo, "find_client_by_cpf", return_value=None):
        try:
            auth_service.login_client(cpf_valid, senha_ok)
            assert False, "deveria ter levantado 401"
        except Exception as exc:
            assert exc.status_code == 401


def test_login_client_inactive():
    row = {**CLIENT_ROW, "status_codigo": "INATIVO"}
    with mock.patch.object(user_repo, "find_client_by_cpf", return_value=row):
        try:
            auth_service.login_client(cpf_valid, senha_ok)
            assert False, "deveria ter levantado 403"
        except Exception as exc:
            assert exc.status_code == 403


def test_login_client_wrong_password():
    with mock.patch.object(user_repo, "find_client_by_cpf", return_value=CLIENT_ROW):
        try:
            auth_service.login_client(cpf_valid, "senha-errada")
            assert False, "deveria ter levantado 401"
        except Exception as exc:
            assert exc.status_code == 401


def test_login_analyst_success():
    with mock.patch.object(user_repo, "find_analyst_by_login", return_value=ANALYST_ROW), \
         mock.patch.object(user_repo, "find_analyst_insurers", return_value=INSURERS):
        envelope = auth_service.login_analyst("  Analista.Horizonte  ", senha_ok)
    session = envelope.session
    assert session.perfil == "ANALISTA"
    assert session.id_usuario == 901
    assert [s.id_pj for s in session.seguradoras] == [10, 20]
    assert session.seguradora.id_pj == 10
    assert session.seguradora.nome_fantasia == "Seguradora Horizonte"
    payload = decode_access_token(envelope.access_token)
    assert payload["perfil"] == "ANALISTA"
    assert payload["seguradoras"][0]["nome_fantasia"] == "Seguradora Horizonte"


def test_login_analyst_lowercases_login():
    with mock.patch.object(user_repo, "find_analyst_by_login", return_value=ANALYST_ROW) as mk, \
         mock.patch.object(user_repo, "find_analyst_insurers", return_value=INSURERS):
        auth_service.login_analyst("  Analista.Horizonte  ", senha_ok)
    assert mk.call_args[0] == ("analista.horizonte",)


def test_login_analyst_wrong_password():
    with mock.patch.object(user_repo, "find_analyst_by_login", return_value=ANALYST_ROW):
        try:
            auth_service.login_analyst("analista.horizonte", "senha-errada")
            assert False, "deveria ter levantado 401"
        except Exception as exc:
            assert exc.status_code == 401


def test_login_analyst_inactive():
    row = {**ANALYST_ROW, "status_codigo": "INATIVO", "fk_seguradora": None}
    with mock.patch.object(user_repo, "find_analyst_by_login", return_value=row), \
         mock.patch.object(user_repo, "find_analyst_insurers", return_value=[]):
        try:
            auth_service.login_analyst("analista.horizonte", senha_ok)
            assert False, "deveria ter levantado 403"
        except Exception as exc:
            assert exc.status_code == 403


def test_normalize_cpf():
    assert auth_service.normalize_cpf("123.456.789-09") == "12345678909"


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
    print(f"\nAUTH_SERVICE_TESTS_OK ({len(tests)} testes)")