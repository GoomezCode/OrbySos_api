from unittest import mock

from fastapi.testclient import TestClient

from main import app
from core.security import create_access_token
import repositories.solicitacao_repository as solicitacao_repo
from services import taxi_question_service as svc

client = TestClient(app)


def _token(perfil="CLIENTE", id_pessoa=1):
    return create_access_token(
        subject=801,
        extra={
            "id_usuario": 801,
            "id_pessoa": id_pessoa,
            "perfil": perfil,
            "nome_exibicao": "Marina",
            "seguradora": None,
            "seguradoras": [],
        },
    )


def _auth():
    return {"Authorization": f"Bearer {_token()}"}


PERGUNTA = {
    "id_pergunta": 7001,
    "fk_solicitacao": 58,
    "origem": "GUINCHO",
    "tipo": "TAXI",
    "status_codigo": "PENDENTE",
    "necessita_taxi": None,
    "qtd_passageiros": None,
    "necessita_acessibilidade": None,
    "qtd_criancas": None,
    "qtd_animais": None,
    "bagagem": None,
    "observacoes": None,
    "data_criacao": None,
    "data_resposta": None,
    "version": 1,
}

SOLICITACAO = {
    "id_solicitacao": 58,
    "fk_pessoa": 1,
    "fk_apolice_id": 10,
    "fk_seguradora_id": 5,
    "fk_veiculo_id": 7,
    "fk_tipo_ocorrencia_id": 1,
    "fk_analista_responsavel": None,
    "status_codigo": "RECEBIDA",
    "isJuridico": 0,
    "id_veiculo": 7,
}

RESPONDIDA = {
    **PERGUNTA,
    "status_codigo": "RESPONDIDA",
    "necessita_taxi": True,
    "qtd_passageiros": 3,
    "necessita_acessibilidade": True,
    "qtd_criancas": 1,
    "qtd_animais": 0,
    "bagagem": "Bagagem",
    "version": 2,
}

RESPONDIDA_FALSA = {
    **PERGUNTA,
    "status_codigo": "RESPONDIDA",
    "necessita_taxi": False,
    "version": 2,
}


def test_answer_requires_token():
    response = client.post("/api/v1/perguntas/7001/resposta", json={})
    assert response.status_code == 401


def test_answer_requires_client_perfil():
    response = client.post(
        "/api/v1/perguntas/7001/resposta",
        json={"necessita_taxi": False, "version": 1},
        headers={"Authorization": f"Bearer {_token(perfil='ANALISTA')}"},
    )
    assert response.status_code == 403


def test_answer_not_found():
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=None):
        response = client.post(
            "/api/v1/perguntas/9999/resposta",
            json={"necessita_taxi": False, "version": 1},
            headers=_auth(),
        )
    assert response.status_code == 404


def test_answer_ownership_denied():
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=PERGUNTA), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value={**SOLICITACAO, "fk_pessoa": 999}):
        response = client.post(
            "/api/v1/perguntas/7001/resposta",
            json={"necessita_taxi": False, "version": 1},
            headers=_auth(),
        )
    assert response.status_code == 404


def test_answer_already_answered():
    row = {**PERGUNTA, "status_codigo": "RESPONDIDA", "version": 2}
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=row), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO):
        response = client.post(
            "/api/v1/perguntas/7001/resposta",
            json={"necessita_taxi": False, "version": 2},
            headers=_auth(),
        )
    assert response.status_code == 422


def test_answer_version_conflict():
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=PERGUNTA), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO):
        response = client.post(
            "/api/v1/perguntas/7001/resposta",
            json={"necessita_taxi": False, "version": 9},
            headers=_auth(),
        )
    assert response.status_code == 409


def test_answer_success_necessita_taxi_true():
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", side_effect=[PERGUNTA, RESPONDIDA]), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO), \
         mock.patch.object(solicitacao_repo, "answer_pergunta", return_value=True):
        response = client.post(
            "/api/v1/perguntas/7001/resposta",
            json={
                "necessita_taxi": True,
                "quantidade_passageiros": 3,
                "necessita_acessibilidade": True,
                "quantidade_criancas": 1,
                "quantidade_animais": 0,
                "bagagem": "Bagagem",
                "observacoes": "obs",
                "version": 1,
            },
            headers=_auth(),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["pergunta"]["status"] == "RESPONDIDA"
    assert body["pergunta"]["necessita_taxi"] is True
    assert body["pergunta"]["quantidade_passageiros"] == 3
    assert body["pergunta"]["version"] == 2


def test_answer_success_necessita_taxi_false():
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", side_effect=[PERGUNTA, RESPONDIDA_FALSA]), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO), \
         mock.patch.object(solicitacao_repo, "answer_pergunta", return_value=True) as mk:
        response = client.post(
            "/api/v1/perguntas/7001/resposta",
            json={"necessita_taxi": False, "version": 1},
            headers=_auth(),
        )
    assert response.status_code == 200
    call = mk.call_args.kwargs
    assert call["necessita_taxi"] is False
    assert call["quantidade_passageiros"] is None
    assert response.json()["pergunta"]["necessita_taxi"] is False


def test_answer_validation_requires_fields():
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=PERGUNTA), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO):
        response = client.post(
            "/api/v1/perguntas/7001/resposta",
            json={"necessita_taxi": True, "version": 1},
            headers=_auth(),
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_answer_validation_passageiro_zero():
    body_payload = {
        "necessita_taxi": True,
        "quantidade_passageiros": 0,
        "necessita_acessibilidade": True,
        "quantidade_criancas": 0,
        "quantidade_animais": 0,
        "bagagem": "ok",
        "version": 1,
    }
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=PERGUNTA), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO):
        response = client.post(
            "/api/v1/perguntas/7001/resposta",
            json=body_payload,
            headers=_auth(),
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


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
    print(f"\nTAXI_QUESTION_ROUTES_TESTS_OK ({len(tests)} testes)")