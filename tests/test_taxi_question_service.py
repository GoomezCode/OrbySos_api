from unittest import mock

import repositories.solicitacao_repository as solicitacao_repo
from schemas.client import PerguntaRespostaRequest
from services import taxi_question_service as svc

SESSION = {"id_pessoa": 1}

PENDENTE = {
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

SOLIC = {"fk_pessoa": 1}


def _body(**kwargs):
    base = {
        "necessita_taxi": True,
        "quantidade_passageiros": 2,
        "necessita_acessibilidade": True,
        "quantidade_criancas": 1,
        "quantidade_animais": 0,
        "bagagem": "Mala",
        "version": 1,
    }
    base.update(kwargs)
    return PerguntaRespostaRequest(**base)


def _assert_code(status_partial, expected):
    for e in expected:
        try:
            svc._validate_input(e)
            assert False, f"deveria falhar: {e}"
        except svc.QuestionError as exc:
            assert exc.status_code == 422
            assert exc.detail["code"] == "VALIDATION_ERROR"


def test_validate_necessita_taxi_nao_boolean():
    from pydantic import ValidationError
    try:
        PerguntaRespostaRequest(necessita_taxi=None, version=1)
        assert False, "schema deveria rejeitar não-booleano"
    except ValidationError:
        pass


def test_validate_necessita_false_ok():
    fields = svc._validate_input(PerguntaRespostaRequest(necessita_taxi=False, version=1))
    assert fields == []


def test_validate_faltando_passageiro():
    _assert_code(None, [
        _body(quantidade_passageiros=0),
        _body(quantidade_passageiros=-1),
    ])


def test_validate_faltando_acessibilidade():
    _assert_code(None, [_body(necessita_acessibilidade=None)])


def test_validate_faltando_bagagem():
    _assert_code(None, [_body(bagagem=None), _body(bagagem="   ")])


def test_validate_ok():
    fields = svc._validate_input(_body())
    assert fields == []


def test_responder_ownership_denied():
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=PENDENTE), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value={"fk_pessoa": 999}):
        try:
            svc.responder_pergunta(SESSION, 7001, _body())
            assert False, "deveria ter levantado 404"
        except svc.QuestionError as exc:
            assert exc.status_code == 404


def test_responder_ok():
    answered = {
        **PENDENTE,
        "status_codigo": "RESPONDIDA",
        "necessita_taxi": True,
        "qtd_passageiros": 2,
        "necessita_acessibilidade": True,
        "qtd_criancas": 1,
        "qtd_animais": 0,
        "bagagem": "Mala",
        "version": 2,
    }
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", side_effect=[PENDENTE, answered]), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLIC), \
         mock.patch.object(solicitacao_repo, "answer_pergunta", return_value=True):
        result = svc.responder_pergunta(SESSION, 7001, _body())
    assert result["pergunta"]["status"] == "RESPONDIDA"
    assert result["pergunta"]["version"] == 2


def test_responder_version_conflict():
    with mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=PENDENTE), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLIC):
        try:
            svc.responder_pergunta(SESSION, 7001, _body(version=9))
            assert False, "deveria ter levantado 409"
        except svc.QuestionError as exc:
            assert exc.status_code == 409


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
    print(f"\nTAXI_QUESTION_SERVICE_TESTS_OK ({len(tests)} testes)")