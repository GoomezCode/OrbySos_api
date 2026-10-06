from datetime import datetime
from unittest import mock

import services.client_service as svc
import repositories.client_repository as client_repo
import repositories.solicitacao_repository as solicitacao_repo
from schemas.client import SolicitacaoCreateRequest

SESSION = {
    "id_usuario": 801,
    "id_pessoa": 1,
    "perfil": "CLIENTE",
    "nome_exibicao": "Marina",
}

PERSON = {"id_pessoa": 1, "isJuridico": 0}
PF = {"id_pf": 1, "nome": "Marina", "cpf": "12345678909", "cpf_mascarado": "***.444.***-**", "data_nascimento": datetime(1990, 1, 1)}
CONTATOS = [{"tipo_contato": "CELULAR", "valor_contato": "11999990000", "principal": 1, "rotulo": None}]


def _patch(name, val):
    return mock.patch.object(client_repo if name.startswith("person") or name.startswith("pessoa") or name.startswith("contatos") or name.startswith("policies") or name.startswith("active") or name.startswith("request") or name.startswith("policy") or name.startswith("occurrence") or name.startswith("next") else solicitacao_repo, name, return_value=val)


def test_get_perfil_fisica():
    with mock.patch.object(client_repo, "person_by_id", return_value=PERSON), \
         mock.patch.object(client_repo, "contatos_by_pessoa", return_value=CONTATOS), \
         mock.patch.object(client_repo, "pessoa_fisica_by_id", return_value=PF):
        result = svc.get_perfil(SESSION)
    assert result["tipo_pessoa"] == "FISICA"
    assert result["contatos"][0]["valor_mascarado"] == "11999990000"


def test_get_perfil_juridica():
    person = {"id_pessoa": 2, "isJuridico": 1}
    pj = {"id_pj": 2, "razao_social": "Acme LTDA", "nome_fantasia": "Acme", "cnpj_mascarado": "**.***.***/0001"}
    with mock.patch.object(client_repo, "person_by_id", return_value=person), \
         mock.patch.object(client_repo, "contatos_by_pessoa", return_value=[]), \
         mock.patch.object(client_repo, "pessoa_juridica_by_id", return_value=pj):
        result = svc.get_perfil({**SESSION, "id_pessoa": 2})
    assert result["tipo_pessoa"] == "JURIDICA"
    assert result["razao_social"] == "Acme LTDA"


def test_get_perfil_not_found():
    with mock.patch.object(client_repo, "person_by_id", return_value=None):
        try:
            svc.get_perfil(SESSION)
            assert False, "expected 404"
        except Exception as exc:
            assert exc.status_code == 404


def test_list_apolices_empty():
    with mock.patch.object(client_repo, "person_by_id", return_value=PERSON), \
         mock.patch.object(client_repo, "pessoa_fisica_by_id", return_value=PF), \
         mock.patch.object(client_repo, "policies_by_pessoa", return_value=[]), \
         mock.patch.object(client_repo, "contatos_by_pessoa", return_value=[]):
        result = svc.list_apolices(SESSION)
    assert result["items"] == []
    assert result["pagination"]["total_items"] == 0


def test_list_apolices_filters_by_status():
    policies = [
        {"id_apolice": 1, "apolice_status": "ATIVA", "fk_segurado": 5, "fk_veiculo": 7},
        {"id_apolice": 2, "apolice_status": "CANCELADA", "fk_segurado": 5, "fk_veiculo": 8},
    ]
    with mock.patch.object(client_repo, "person_by_id", return_value=PERSON), \
         mock.patch.object(client_repo, "pessoa_fisica_by_id", return_value=PF), \
         mock.patch.object(client_repo, "policies_by_pessoa", return_value=policies), \
         mock.patch.object(client_repo, "active_request_by_policy", return_value=None), \
         mock.patch.object(client_repo, "pessoa_juridica_by_id", return_value={}), \
         mock.patch.object(client_repo, "contatos_by_pessoa", return_value=[]):
        result = svc.list_apolices(SESSION, status="ATIVA")
    assert [item["id_apolice"] for item in result["items"]] == [1]
    assert result["pagination"]["total_items"] == 1


def test_criar_solicitacao_idempotency_key_mismatch():
    body = SolicitacaoCreateRequest(
        id_solicitacao_cliente="uuid-aaa",
        apolice_id=10,
        tipo_ocorrencia_id=1,
        descricao_evento="Falha",
        possui_feridos=False,
        risco_imediato=False,
        local={"endereco": "Rua A", "numero_local": "10", "cidade": "SP", "estado": "SP", "ponto_referencia": None},
        data_criacao_cliente="2026-08-11T15:00:00Z",
    )
    try:
        svc.criar_solicitacao(SESSION, body, "uuid-bbb")
        assert False, "expected 422"
    except Exception as exc:
        assert exc.status_code == 422


def test_criar_solicitacao_duplicate_uuid_conflict():
    body = SolicitacaoCreateRequest(
        id_solicitacao_cliente="uuid-dup",
        apolice_id=10,
        tipo_ocorrencia_id=1,
        descricao_evento="Falha",
        possui_feridos=False,
        risco_imediato=False,
        local={"endereco": "Rua A", "numero_local": "10", "cidade": "SP", "estado": "SP", "ponto_referencia": None},
        data_criacao_cliente="2026-08-11T15:00:00Z",
    )
    with mock.patch.object(client_repo, "request_by_client_uuid", return_value={"id_solicitacao": 5}):
        try:
            svc.criar_solicitacao(SESSION, body, "uuid-dup")
            assert False, "expected 409"
        except Exception as exc:
            assert exc.status_code == 409


def test_perguntas_preserves_null_and_string_bagagem():
    pending_row = {
        "id_pergunta": 901,
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
    answered_row = {**pending_row, "id_pergunta": 902,
                   "status_codigo": "RESPONDIDA",
                   "necessita_taxi": True,
                   "qtd_passageiros": 2,
                   "necessita_acessibilidade": False,
                   "qtd_criancas": 1,
                   "qtd_animais": 0,
                   "bagagem": "Mala grande",
                   "data_resposta": datetime(2026, 8, 11, 15, 30)}
    sol = {
        "id_solicitacao": 100, "fk_pessoa": 1, "status_codigo": "EM_ATENDIMENTO",
        "fk_analista_responsavel": None, "id_veiculo": 10, "fk_apolice_id": 1,
        "fk_seguradora_id": 5,
    }
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=sol), \
         mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value={}), \
         mock.patch.object(client_repo, "pessoa_juridica_by_id", return_value={"nome_fantasia": "Seg X"}), \
         mock.patch.object(client_repo, "contatos_by_pessoa", return_value=[]), \
         mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[]), \
         mock.patch.object(solicitacao_repo, "historico_by_solicitacao", return_value=[]), \
         mock.patch.object(solicitacao_repo, "perguntas_by_solicitacao", return_value=[pending_row, answered_row]):
        result = svc.get_detalhe_solicitacao(SESSION, 100)

    pending = next(p for p in result["perguntas"] if p["id_pergunta"] == 901)
    resp = next(p for p in result["perguntas"] if p["id_pergunta"] == 902)
    assert pending["necessita_taxi"] is None
    assert pending["necessita_acessibilidade"] is None
    assert pending["bagagem"] is None
    assert resp["necessita_taxi"] is True
    assert resp["bagagem"] == "Mala grande"


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
    print(f"\nCLIENT_SERVICE_TESTS_OK ({len(tests)} testes)")
