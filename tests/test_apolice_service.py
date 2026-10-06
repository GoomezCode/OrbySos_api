from unittest import mock

from fastapi import HTTPException

import repositories.apolice_repository as apolice_repo
import repositories.client_repository as client_repo
import services.apolice_service as service


SESSION = {
    "id_usuario": 901,
    "id_pessoa": 4,
    "perfil": "ANALISTA",
    "nome_exibicao": "Analista Horizonte",
    "seguradora": {"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"},
    "seguradoras": [{"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"}],
}


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


def _session_outras_seguradoras():
    return {
        **SESSION,
        "seguradora": {"id_pj": 99, "nome_fantasia": "Outra"},
        "seguradoras": [{"id_pj": 99, "nome_fantasia": "Outra"}],
    }


def _request(klass, payload):
    return klass.model_validate(payload)


def test_list_seus_filtros_passam_ao_repo():
    with mock.patch.object(apolice_repo, "find_apolices", return_value=[_row()]) as find:
        result = service.list_apolices(
            SESSION,
            status_filter="ATIVA",
            numero_apolice="1001",
            pessoa="Marina",
            placa="ABC",
            seguradora=10,
            sort="id_apolice",
            page=1,
            page_size=20,
        )
    find.assert_called_once()
    args, kwargs = find.call_args
    assert args[0] == [10]
    assert kwargs["filters"] == {
        "status": "ATIVA",
        "numero_apolice": "1001",
        "pessoa": "Marina",
        "placa": "ABC",
        "seguradora": 10,
    }
    assert kwargs["sort"] == "id_apolice"
    assert result["pagination"]["total_items"] == 1
    assert result["items"][0]["id_apolice"] == 1001


def test_list_sem_perfil_analista_403():
    session = {**SESSION, "perfil": "CLIENTE"}
    try:
        service.list_apolices(session)
        assert False, "deveria levantar 403"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail["code"] == "AUTH_FORBIDDEN"


def test_list_ignora_outras_seguradoras_no_repo():
    with mock.patch.object(apolice_repo, "find_apolices", return_value=[]) as find:
        service.list_apolices(_session_outras_seguradoras())
    assert find.call_args.args[0] == [99]


def test_detalhe_montar_aggregate_com_contatos():
    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row()) as get:
        with mock.patch.object(client_repo, "contatos_by_pessoa", return_value=[]) as contatos:
            result = service.get_detalhe(SESSION, 1001)
    get.assert_called_once_with(1001)
    assert contatos.call_count == 2
    apolice = result["apolice"]
    assert apolice["numero_apolice_mascarado"] == "ORB-****-1001"
    assert apolice["status"] == "ATIVA"
    assert apolice["cliente"]["nome"] == "Marina Exemplo"
    assert apolice["veiculo"]["placa_mascarada"] == "ABC-1*23"


def test_detalhe_de_outra_seguradora_404():
    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row()):
        try:
            service.get_detalhe(_session_outras_seguradoras(), 1001)
            assert False, "deveria levantar 404"
        except HTTPException as exc:
            assert exc.status_code == 404
            assert exc.detail["code"] == "POLICY_NOT_FOUND"


def test_detalhe_inexistente_404():
    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=None):
        try:
            service.get_detalhe(SESSION, 999)
            assert False, "deveria levantar 404"
        except HTTPException as exc:
            assert exc.status_code == 404


def test_criar_sem_permissao_da_seguradora_403():
    from schemas.apolice import ApoliceCreateRequest

    body = _request(ApoliceCreateRequest, {
        "numero_apolice": "ORB-2026-9999",
        "fk_pessoa": 1,
        "fk_segurado": 999,
        "fk_veiculo": 201,
        "data_inicio": "2026-01-01T00:00:00Z",
        "data_fim": "2026-12-31T00:00:00Z",
        "cobertura": 50000.0,
        "assistencia": "Guincho",
        "perfil": "Particular",
        "fk_local_pernoite": 1,
        "fk_forma_pagamento": 1,
    })
    try:
        service.criar_apolice(SESSION, body)
        assert False, "deveria levantar 403"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert exc.detail["code"] == "AUTH_FORBIDDEN"


def test_criar_data_fim_antes_inicio_422():
    from schemas.apolice import ApoliceCreateRequest

    body = _request(ApoliceCreateRequest, {
        "numero_apolice": "ORB-2026-9999",
        "fk_pessoa": 1,
        "fk_segurado": 10,
        "fk_veiculo": 201,
        "data_inicio": "2026-12-31T00:00:00Z",
        "data_fim": "2026-01-01T00:00:00Z",
        "cobertura": 50000.0,
        "assistencia": "Guincho",
        "perfil": "Particular",
        "fk_local_pernoite": 1,
        "fk_forma_pagamento": 1,
    })
    try:
        service.criar_apolice(SESSION, body)
        assert False, "deveria levantar 422"
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["code"] == "VALIDATION_ERROR"


def test_criar_mantem_mascara():
    from schemas.apolice import ApoliceCreateRequest

    def fake_create(*, data, now):
        return _row(numero_apolice=data["numero_apolice"], numero_apolice_mascarado=f"ORB-****-{data['numero_apolice'][-4:]}")
    body = _request(ApoliceCreateRequest, {
        "numero_apolice": "ORB-2026-7777",
        "fk_pessoa": 1,
        "fk_segurado": 10,
        "fk_veiculo": 201,
        "data_inicio": "2026-01-01T00:00:00Z",
        "data_fim": "2026-12-31T00:00:00Z",
        "cobertura": 50000.0,
        "assistencia": "Guincho",
        "perfil": "Particular",
        "fk_local_pernoite": 1,
        "fk_forma_pagamento": 1,
    })
    with mock.patch.object(apolice_repo, "create_apolice", side_effect=fake_create) as create:
        result = service.criar_apolice(SESSION, body)
    create.assert_called_once()
    assert result["apolice"]["numero_apolice"] == "ORB-2026-7777"
    assert result["apolice"]["numero_apolice_mascarado"] == "ORB-****-7777"


def test_atualizar_version_conflitante_409():
    from schemas.apolice import ApoliceUpdateRequest

    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row(versao=5)):
        body = _request(ApoliceUpdateRequest, {"version": 1, "cobertura": 100.0})
        try:
            service.atualizar_apolice(SESSION, 1001, body)
            assert False, "deveria levantar 409"
        except HTTPException as exc:
            assert exc.status_code == 409
            assert exc.detail["code"] == "POLICY_VERSION_CONFLICT"


def test_atualizar_chama_repo_com_patch_mergido():
    from schemas.apolice import ApoliceUpdateRequest

    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row(versao=1)):
        with mock.patch.object(apolice_repo, "update_apolice", return_value=_row(versao=2)) as update:
            body = _request(ApoliceUpdateRequest, {"version": 1, "cobertura": 999.0})
            result = service.atualizar_apolice(SESSION, 1001, body)
    update.assert_called_once()
    _, kwargs = update.call_args
    assert kwargs["version"] == 1
    assert kwargs["patch"]["cobertura"] == 999.0
    assert kwargs["patch"]["numero_apolice"] == "ORB-2026-1001"
    assert result["apolice"]["versao"] == 2


def test_atualizar_repo_retorna_none_409():
    from schemas.apolice import ApoliceUpdateRequest

    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row(versao=1)):
        with mock.patch.object(apolice_repo, "update_apolice", return_value=None):
            body = _request(ApoliceUpdateRequest, {"version": 1, "cobertura": 999.0})
            try:
                service.atualizar_apolice(SESSION, 1001, body)
                assert False, "deveria levantar 409"
            except HTTPException as exc:
                assert exc.status_code == 409


def test_status_invalido_409():
    from schemas.apolice import ApoliceStatusRequest

    body = _request(ApoliceStatusRequest, {"version": 1, "status": "REMOVIDA"})
    try:
        service.alterar_status_apolice(SESSION, 1001, body)
        assert False, "deveria levantar 409"
    except HTTPException as exc:
        assert exc.status_code == 409
        assert exc.detail["code"] == "INVALID_POLICY_STATUS"


def test_status_igual_atual_409():
    from schemas.apolice import ApoliceStatusRequest

    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row(versao=1, apolice_status="ATIVA")):
        body = _request(ApoliceStatusRequest, {"version": 1, "status": "ATIVA"})
        try:
            service.alterar_status_apolice(SESSION, 1001, body)
            assert False, "deveria levantar 409"
        except HTTPException as exc:
            assert exc.status_code == 409


def test_status_ok_chama_repo():
    from schemas.apolice import ApoliceStatusRequest

    with mock.patch.object(apolice_repo, "apolice_by_id", return_value=_row(versao=1, apolice_status="ATIVA")):
        with mock.patch.object(apolice_repo, "update_apolice_status", return_value=_row(versao=2, apolice_status="SUSPENSA")) as upd:
            body = _request(ApoliceStatusRequest, {"version": 1, "status": "SUSPENSA"})
            result = service.alterar_status_apolice(SESSION, 1001, body)
    upd.assert_called_once()
    _, kwargs = upd.call_args
    assert kwargs["to_status"] == "SUSPENSA"
    assert result["apolice"]["status"] == "SUSPENSA"


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
    print(f"\nAPOLICE_SERVICE_TESTS_OK" if failures == 0 else f"\n{failures} FALHAS")
    sys.exit(1 if failures else 0)