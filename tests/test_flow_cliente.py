from unittest import mock

from validate_docbr import CPF
from fastapi.testclient import TestClient

from main import app
from core.security import hash_password
import repositories.client_repository as client_repo
import repositories.solicitacao_repository as solicitacao_repo
import repositories.user_repository as user_repo

client = TestClient(app)

CPF_VALIDO = CPF().generate(mask=False)
SENHA = "senha-segura-123"

CLIENT_ROW = {
    "id_user": 801,
    "fk_pessoa": 1,
    "login": CPF_VALIDO,
    "perfil": "CLIENTE",
    "fk_status": 8,
    "nome_exibicao": "Marina Exemplo",
    "email": "marina@example.com",
    "status_codigo": "ATIVO",
    "nome": "Marina Exemplo",
    "cpf": CPF_VALIDO,
    "cpf_mascarado": "***.444.***-**",
    "senha": hash_password(SENHA),
}

PERSON = {"id_pessoa": 1, "isJuridico": 0}
PF = {"id_pf": 1, "nome": "Marina Exemplo", "cpf": CPF_VALIDO,
      "cpf_mascarado": "***.444.***-**", "data_nascimento": None}
CONTATO_CLIENTE = [{"tipo_contato": "CELULAR", "valor_contato": "11999990000",
                    "principal": 1, "rotulo": None}]
SEGURADORA = {"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"}
CONTATO_SEG = [{"tipo_contato": "SAC", "valor_contato": "0800-000-0000",
                "principal": 1, "rotulo": "SAC"}]

POLICY = {
    "id_apolice": 1002,
    "numero_apolice_mascarado": "ORB-****-1002",
    "data_inicio": None,
    "data_fim": None,
    "fk_pessoa": 1,
    "fk_veiculo": 202,
    "fk_segurado": 10,
    "apolice_status": "ATIVA",
    "marca": "Marca Demo",
    "modelo": "Modelo Prata",
    "ano_fabricado": 2021,
    "ano_modelo": 2022,
    "placa_mascarada": "TST-****",
}

OCCURRENCE = {"id_ocorrencia": 1, "codigo": "FURTO", "nome": "Furto",
              "descricao": "Furto do veículo.", "ativo": 1}

SOLICITACAO_ROW = {
    "id_solicitacao": 58,
    "id_solicitacao_cliente": "uuid-fluxo-1",
    "numero_solicitacao": "ORB-2026-000058",
    "protocolo_solicitacao": "ORB-2026-000058",
    "descricao_evento": "Furto na rua.",
    "possui_feridos": False,
    "risco_imediato": False,
    "prioridade": "NORMAL",
    "data_criacao_cliente": None,
    "data_recebimento": None,
    "data_decisao": None,
    "motivo_recusa": None,
    "version": 1,
    "fk_pessoa": 1,
    "fk_apolice_id": 1002,
    "fk_seguradora_id": 10,
    "fk_veiculo_id": 202,
    "fk_tipo_ocorrencia_id": 1,
    "fk_analista_responsavel": None,
    "status_codigo": "RECEBIDA",
    "isJuridico": 0,
    "endereco": "Rua das Flores",
    "numero_local": "100",
    "cidade": "São Paulo",
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
    "ocorrencia_codigo": "FURTO",
    "ocorrencia_nome": "Furto",
    "ocorrencia_descricao": "Furto do veículo.",
    "seguradora_nome": "Seguradora Horizonte",
    "analista_nome": None,
}

APOLICE_RESUMO = {
    "id_apolice": 1002,
    "numero_apolice_mascarado": "ORB-****-1002",
    "data_inicio": None,
    "data_fim": None,
    "apolice_status": "ATIVA",
}


def _pergunta(status="PENDENTE", version=1):
    return {
        "id_pergunta": 7001,
        "origem": "GUINCHO",
        "tipo": "TAXI",
        "status_codigo": status,
        "necessita_taxi": None,
        "qtd_passageiros": None,
        "necessita_acessibilidade": None,
        "qtd_criancas": None,
        "qtd_animais": None,
        "bagagem": None,
        "observacoes": None,
        "data_criacao": None,
        "data_resposta": None,
        "version": version,
        "fk_solicitacao": 58,
    }


def _historico():
    return {
        "id_historico": 1,
        "status": "RECEBIDA",
        "data_status": None,
        "comentario": "Solicitação recebida.",
        "nome_responsavel": "Marina Exemplo",
        "fk_usuario_responsavel": None,
    }


def test_fluxo_cliente_completo():
    token = None
    with mock.patch.object(user_repo, "find_client_by_cpf", return_value=CLIENT_ROW):
        response = client.post(
            "/api/v1/auth/clientes/login",
            json={"cpf": CPF_VALIDO, "senha": SENHA},
        )
    assert response.status_code == 200
    envelope = response.json()
    token = envelope["access_token"]
    assert envelope["session"]["perfil"] == "CLIENTE"
    headers = {"Authorization": f"Bearer {token}"}

    with \
        mock.patch.object(client_repo, "person_by_id", return_value=PERSON), \
        mock.patch.object(client_repo, "pessoa_fisica_by_id", return_value=PF), \
        mock.patch.object(client_repo, "policies_by_pessoa", return_value=[POLICY]), \
        mock.patch.object(client_repo, "active_request_by_policy", return_value=None), \
        mock.patch.object(client_repo, "pessoa_juridica_by_id", return_value=SEGURADORA), \
        mock.patch.object(client_repo, "contatos_by_pessoa", return_value=CONTATO_SEG):
        response = client.get("/api/v1/clientes/me/apolices?status=ATIVA", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total_items"] == 1
    assert body["items"][0]["numero_apolice_mascarado"] == "ORB-****-1002"
    assert body["items"][0]["status"] == "ATIVA"

    with \
        mock.patch.object(client_repo, "request_by_client_uuid", return_value=None), \
        mock.patch.object(client_repo, "occurrence_by_id", return_value=OCCURRENCE), \
        mock.patch.object(client_repo, "policy_by_id_for_pessoa", return_value=POLICY), \
        mock.patch.object(client_repo, "active_request_by_policy", return_value=None), \
        mock.patch.object(client_repo, "next_solicitacao_seq", return_value=58), \
        mock.patch.object(solicitacao_repo, "create_solicitacao", return_value=58), \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO_ROW), \
        mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[]), \
        mock.patch.object(solicitacao_repo, "perguntas_by_solicitacao", return_value=[_pergunta()]), \
        mock.patch.object(solicitacao_repo, "historico_by_solicitacao", return_value=[_historico()]), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=APOLICE_RESUMO), \
        mock.patch.object(client_repo, "contatos_by_pessoa", return_value=CONTATO_SEG):
        response = client.post(
            "/api/v1/solicitacoes",
            json={
                "id_solicitacao_cliente": "uuid-fluxo-1",
                "apolice_id": 1002,
                "tipo_ocorrencia_id": 1,
                "descricao_evento": "Furto na rua.",
                "possui_feridos": False,
                "risco_imediato": False,
                "local": {
                    "endereco": "Rua das Flores",
                    "numero_local": "100",
                    "cidade": "São Paulo",
                    "estado": "SP",
                    "ponto_referencia": None,
                },
                "data_criacao_cliente": "2026-09-15T10:00:00Z",
            },
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "uuid-fluxo-1"},
        )
    assert response.status_code == 201
    criada = response.json()
    assert criada["solicitacao"]["numero_solicitacao"] == "ORB-2026-000058"
    assert criada["solicitacao"]["status"] == "RECEBIDA"
    assert criada["perguntas"][0]["status"] == "PENDENTE"

    with \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO_ROW), \
        mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[]), \
        mock.patch.object(solicitacao_repo, "perguntas_by_solicitacao", return_value=[_pergunta()]), \
        mock.patch.object(solicitacao_repo, "historico_by_solicitacao", return_value=[_historico()]), \
        mock.patch.object(solicitacao_repo, "apolice_resumo_by_id", return_value=APOLICE_RESUMO), \
        mock.patch.object(client_repo, "contatos_by_pessoa", return_value=CONTATO_SEG):
        response = client.get("/api/v1/solicitacoes/58", headers=headers)
    assert response.status_code == 200
    detalhe = response.json()
    assert detalhe["solicitacao"]["id_solicitacao"] == 58
    assert detalhe["perguntas"][0]["id_pergunta"] == 7001

    respondida = _pergunta(status="RESPONDIDA", version=2)
    respondida["necessita_taxi"] = True
    respondida["qtd_passageiros"] = 2
    respondida["bagagem"] = "Mala"
    with \
        mock.patch.object(
            solicitacao_repo, "pergunta_by_id", side_effect=[_pergunta(), respondida]
        ), \
        mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=SOLICITACAO_ROW), \
        mock.patch.object(solicitacao_repo, "answer_pergunta", return_value=True):
        response = client.post(
            "/api/v1/perguntas/7001/resposta",
            json={
                "necessita_taxi": True,
                "quantidade_passageiros": 2,
                "necessita_acessibilidade": False,
                "quantidade_criancas": 0,
                "quantidade_animais": 0,
                "bagagem": "Mala",
                "observacoes": "",
                "version": 1,
            },
            headers=headers,
        )
    assert response.status_code == 200
    final = response.json()
    assert final["pergunta"]["status"] == "RESPONDIDA"
    assert final["pergunta"]["necessita_taxi"] is True
    assert final["pergunta"]["quantidade_passageiros"] == 2


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
    print(f"\nFLOW_CLIENTE_TESTS_OK ({len(tests)} testes)")