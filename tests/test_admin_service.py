from unittest import mock

import repositories.admin_repository as admin_repo
import repositories.solicitacao_repository as solicitacao_repo
import services.admin_service as svc


def _session():
    return {
        "id_usuario": 901,
        "id_pessoa": 4,
        "perfil": "ANALISTA",
        "nome_exibicao": "Analista Horizonte",
        "seguradora": {"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"},
        "seguradoras": [{"id_pj": 10, "nome_fantasia": "Seguradora Horizonte"}],
    }


def _row(**overrides):
    base = {
        "id_solicitacao": 51,
        "id_solicitacao_cliente": "00000000-0000-4000-8000-000000000051",
        "numero_solicitacao": "ORB-2026-000051",
        "protocolo_solicitacao": "ORB-2026-000051",
        "descricao_evento": "Cenario ficticio critico.",
        "possui_feridos": True,
        "risco_imediato": False,
        "prioridade": "CRITICA",
        "data_criacao_cliente": None,
        "data_recebimento": None,
        "data_decisao": None,
        "motivo_recusa": None,
        "version": 1,
        "fk_pessoa": 1,
        "fk_apolice_id": 1002,
        "fk_seguradora_id": 10,
        "fk_veiculo_id": 202,
        "fk_tipo_ocorrencia_id": 2,
        "fk_analista_responsavel": None,
        "status_codigo": "RECEBIDA",
        "isJuridico": 0,
        "endereco": "Avenida Modelo",
        "numero_local": "100",
        "cidade": "Cidade Exemplo",
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
        "ocorrencia_codigo": "ACIDENTE",
        "ocorrencia_nome": "Acidente",
        "ocorrencia_descricao": "Colisao ou outro evento acidental.",
        "seguradora_nome": "Seguradora Horizonte",
        "analista_nome": None,
    }
    base.update(overrides)
    return base


def _assistencia(status="INCLUIDA", version=1, **overrides):
    base = {
        "id_solicitacao_assistencia": 8010,
        "fk_solicitacao": 51,
        "status": status,
        "comentario": None,
        "data_inclusao": None,
        "data_atualizacao": None,
        "version": version,
        "id_tipo_assistencia": 1,
        "tipo_codigo": "GUINCHO",
        "tipo_nome": "Guincho",
        "id_usuario": 901,
        "nome_exibicao": "Analista Horizonte",
    }
    base.update(overrides)
    return base


def _assert_error(fn, code, http):
    try:
        fn()
    except svc.AdminError as exc:
        assert exc.status_code == http
        assert exc.detail["code"] == code
        return
    raise AssertionError(f"esperado AdminError {code}")


def test_requires_analyst():
    session = {**_session(), "perfil": "CLIENTE"}
    _assert_error(
        lambda: svc.get_dashboard(session),
        "AUTH_FORBIDDEN",
        403,
    )


def test_dashboard_metricas_e_fila():
    rows = [
        _row(id_solicitacao=1, prioridade="CRITICA", status_codigo="RECEBIDA"),
        _row(id_solicitacao=2, prioridade="CRITICA", status_codigo="CONCLUIDA"),
        _row(id_solicitacao=3, prioridade="NORMAL", status_codigo="EM_ATENDIMENTO"),
        _row(id_solicitacao=4, prioridade="NORMAL", status_codigo="RECUSADA_SEM_COBERTURA"),
        _row(id_solicitacao=5, prioridade="MEDIA", status_codigo="PRESTADOR_ACIONADO"),
        _row(id_solicitacao=6, prioridade="BAIXA", status_codigo="CONFIRMADA"),
        _row(id_solicitacao=7, prioridade="NORMAL", status_codigo="RECEBIDA"),
    ]
    with mock.patch.object(admin_repo, "find_solicitacoes", return_value=rows), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.get_dashboard(_session())
    assert result["metricas"] == {
        "criticas_abertas": 1,
        "aguardando_analise": 2,
        "confirmadas_em_atendimento": 2,
        "prestadores_acionados": 1,
        "concluidas": 1,
        "recusadas_sem_cobertura": 1,
    }
    assert len(result["fila_prioritaria"]["items"]) == 5


def test_list_solicitacoes_filtra_e_pagina():
    rows = [_row(id_solicitacao=i + 1) for i in range(15)]
    with mock.patch.object(admin_repo, "find_solicitacoes", return_value=rows), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.list_solicitacoes(_session(), status_filter="RECEBIDA", page=2, page_size=10)
        calls = admin_repo.find_solicitacoes.call_args_list[-1]
    assert result["pagination"] == {"page": 2, "page_size": 10, "total_items": 15, "total_pages": 2}
    assert len(result["items"]) == 5
    assert calls.args[1]["status"] == "RECEBIDA"
    assert calls.args[1]["pessoa"] is None


def test_detail_solicitacao_fora_da_seguradora():
    row = _row(fk_seguradora_id=99)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        _assert_error(
            lambda: svc.get_detalhe(_session(), 51),
            "REQUEST_NOT_FOUND",
            404,
        )


def test_detail_solicitacao_composicao():
    row = _row(fk_analista_responsavel=901, analista_nome="Analista Horizonte")
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(admin_repo, "tipos_assistencia_ativos", return_value=[
             {"id_tipo_assistencia": 1, "codigo": "GUINCHO", "nome": "Guincho",
              "descricao": "Remocao.", "ativo": True},
         ]), \
         mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[_assistencia()]), \
         mock.patch.object(solicitacao_repo, "perguntas_by_solicitacao", return_value=[
             {"id_pergunta": 7001, "origem": "GUINCHO", "tipo": "TAXI", "status_codigo": "PENDENTE",
              "necessita_taxi": None, "qtd_passageiros": None, "necessita_acessibilidade": None,
              "qtd_criancas": None, "qtd_animais": None, "bagagem": None, "observacoes": None,
              "data_criacao": None, "data_resposta": None, "version": 1},
         ]), \
         mock.patch.object(solicitacao_repo, "historico_by_solicitacao", return_value=[
             {"id_historico": 1, "status": "RECEBIDA", "data_status": None, "comentario": "ok",
              "nome_responsavel": "Marina", "fk_usuario_responsavel": None},
         ]), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.get_detalhe(_session(), 51)
    assert result["solicitacao"]["status"] == "RECEBIDA"
    assert result["solicitacao"]["analista"]["id_usuario"] == 901
    assert result["assistencias"][0]["tipo"]["codigo"] == "GUINCHO"
    assert result["perguntas"][0]["status"] == "PENDENTE"
    assert result["tipos_assistencia_disponiveis"][0]["codigo"] == "GUINCHO"
    assert result["analista"] == {"id_usuario": 901, "nome_exibicao": "Analista Horizonte"}


def test_list_tipos_assistencia():
    with mock.patch.object(admin_repo, "tipos_assistencia_ativos", return_value=[
        {"id_tipo_assistencia": 1, "codigo": "GUINCHO", "nome": "Guincho", "descricao": "R.", "ativo": True},
    ]):
        result = svc.list_tipos_assistencia(_session())
    assert result["items"][0]["codigo"] == "GUINCHO"
    assert result["items"][0]["ativo"] is True


def test_assumir_success():
    row = _row(status_codigo="RECEBIDA", version=1)
    updated = _row(status_codigo="EM_ANALISE", version=2, fk_analista_responsavel=901,
                   analista_nome="Analista Horizonte")
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.assumir(_session(), 51, 1)
        call = admin_repo.transicionar_solicitacao.call_args.kwargs
    assert result["solicitacao"]["status"] == "EM_ANALISE"
    assert result["solicitacao"]["version"] == 2
    assert call["from_status_codigo"] == "RECEBIDA"
    assert call["to_status_codigo"] == "EM_ANALISE"


def test_assumir_versao_desatualizada():
    row = _row(status_codigo="RECEBIDA", version=5)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=False):
        _assert_error(lambda: svc.assumir(_session(), 51, 1), "REQUEST_VERSION_CONFLICT", 409)


def test_assumir_transicao_invalida():
    row = _row(status_codigo="CONCLUIDA", version=1)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        _assert_error(lambda: svc.assumir(_session(), 51, 1), "REQUEST_INVALID_STATUS_TRANSITION", 422)


def test_confirmar_success():
    row = _row(status_codigo="EM_ANALISE", version=2, fk_analista_responsavel=901)
    updated = _row(status_codigo="CONFIRMADA", version=3, fk_analista_responsavel=901,
                   data_decisao=None, motivo_recusa=None)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.confirmar(_session(), 51, 2, "Cobertura confirmada.")
        call = admin_repo.transicionar_solicitacao.call_args.kwargs
    assert result["solicitacao"]["status"] == "CONFIRMADA"
    assert call["to_status_codigo"] == "CONFIRMADA"
    assert call["set_decisao"] is True
    assert call["motivo_recusa"] is None


def test_confirmar_sem_responsabilidade():
    row = _row(status_codigo="EM_ANALISE", version=2, fk_analista_responsavel=999)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        _assert_error(lambda: svc.confirmar(_session(), 51, 2, None), "AUTH_FORBIDDEN", 403)


def test_recusar_motivo_obrigatorio():
    row = _row(status_codigo="EM_ANALISE", version=2, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        _assert_error(lambda: svc.recusar(_session(), 51, 2, "  "), "REQUEST_REJECTION_REASON_REQUIRED", 422)


def test_recusar_success():
    row = _row(status_codigo="EM_ANALISE", version=2, fk_analista_responsavel=901)
    updated = _row(status_codigo="RECUSADA_SEM_COBERTURA", version=3, fk_analista_responsavel=901,
                   motivo_recusa="Ausencia de cobertura.")
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.recusar(_session(), 51, 2, "Ausencia de cobertura.")
        call = admin_repo.transicionar_solicitacao.call_args.kwargs
    assert result["solicitacao"]["status"] == "RECUSADA_SEM_COBERTURA"
    assert call["release_policy"] is True
    assert call["set_decisao"] is True


def test_iniciar_atendimento_success():
    row = _row(status_codigo="CONFIRMADA", version=3, fk_analista_responsavel=901)
    updated = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.iniciar_atendimento(_session(), 51, 3, None)
    assert result["solicitacao"]["status"] == "EM_ATENDIMENTO"


def test_registrar_prestador_success():
    row = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    updated = _row(status_codigo="PRESTADOR_ACIONADO", version=5, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.registrar_prestador_acionado(_session(), 51, 4, None)
    assert result["solicitacao"]["status"] == "PRESTADOR_ACIONADO"


def test_concluir_bloqueado_sem_assistencias_finalizadas():
    row = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[
             _assistencia(status="PRESTADOR_ACIONADO", version=2),
         ]):
        _assert_error(lambda: svc.concluir(_session(), 51, 4, None), "REQUEST_ASSISTANCES_PENDING", 422)


def test_concluir_success():
    row = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    updated = _row(status_codigo="CONCLUIDA", version=5, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(solicitacao_repo, "assistencias_by_solicitacao", return_value=[
             _assistencia(status="CONCLUIDA", version=3),
         ]), \
         mock.patch.object(admin_repo, "transicionar_solicitacao", return_value=True), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.concluir(_session(), 51, 4, None)
        call = admin_repo.transicionar_solicitacao.call_args.kwargs
    assert result["solicitacao"]["status"] == "CONCLUIDA"
    assert call["release_policy"] is True


def test_adicionar_assistencia_guincho_cria_pergunta():
    row = _row(status_codigo="CONFIRMADA", version=3, fk_analista_responsavel=901)
    updated = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    pergunta = {
        "id_pergunta": 7010, "origem": "GUINCHO", "tipo": "TAXI", "status_codigo": "PENDENTE",
        "necessita_taxi": None, "qtd_passageiros": None, "necessita_acessibilidade": None,
        "qtd_criancas": None, "qtd_animais": None, "bagagem": None, "observacoes": None,
        "data_criacao": None, "data_resposta": None, "version": 1,
    }
    resultado = {
        "assistencia": _assistencia(),
        "pergunta_id": 7010,
    }
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", side_effect=[row, updated]), \
         mock.patch.object(admin_repo, "tipo_assistencia_by_id",
                           return_value={"id_tipo_assistencia": 1, "codigo": "GUINCHO",
                                         "nome": "Guincho", "descricao": "R.", "ativo": True}), \
         mock.patch.object(admin_repo, "add_assistencia", return_value=resultado), \
         mock.patch.object(solicitacao_repo, "pergunta_by_id", return_value=pergunta), \
         mock.patch.object(
             solicitacao_repo,
             "apolice_resumo_by_id",
             return_value={"numero_apolice_mascarado": "ORB-****-1002",
                           "data_inicio": None, "data_fim": None, "apolice_status": "ATIVA"},
         ):
        result = svc.adicionar_assistencia(_session(), 51, mock.Mock(
            tipo_assistencia_id=1, comentario=None, request_version=3))
    assert result["assistencia"]["tipo"]["codigo"] == "GUINCHO"
    assert result["pergunta_criada"]["status"] == "PENDENTE"
    assert result["solicitacao"]["status"] == "EM_ATENDIMENTO"


def test_adicionar_assistencia_tipo_invalido():
    row = _row(status_codigo="CONFIRMADA", version=3, fk_analista_responsavel=901)
    with mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(admin_repo, "tipo_assistencia_by_id", return_value=None):
        _assert_error(
            lambda: svc.adicionar_assistencia(_session(), 51, mock.Mock(
                tipo_assistencia_id=99, comentario=None, request_version=3)),
            "VALIDATION_ERROR",
            422,
        )


def test_atualizar_assistencia_success():
    assistencia = _assistencia()
    row = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    atualizada = {
        "status": "PRESTADOR_ACIONADO", "comentario": "Protocolo DEMO-1.",
        "data_atualizacao": None, "version": 2, "id_usuario": 901,
        "nome_exibicao": "Analista Horizonte", "fk_solicitacao": 51,
    }
    with mock.patch.object(admin_repo, "assistencia_by_id", return_value=assistencia), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row), \
         mock.patch.object(admin_repo, "update_assistencia_status", return_value=atualizada):
        result = svc.atualizar_assistencia(_session(), 8010, mock.Mock(
            status="PRESTADOR_ACIONADO", comentario="Protocolo DEMO-1.", version=1))
        call = admin_repo.update_assistencia_status.call_args.kwargs
    assert result["assistencia"]["status"] == "PRESTADOR_ACIONADO"
    assert result["assistencia"]["version"] == 2
    assert call["request_status_codigo"] == "EM_ATENDIMENTO"


def test_atualizar_assistencia_versao_conflitante():
    assistencia = _assistencia(version=3)
    row = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    with mock.patch.object(admin_repo, "assistencia_by_id", return_value=assistencia), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        _assert_error(
            lambda: svc.atualizar_assistencia(_session(), 8010, mock.Mock(
                status="PRESTADOR_ACIONADO", comentario="x", version=1)),
            "ASSISTANCE_VERSION_CONFLICT",
            409,
        )


def test_atualizar_assistencia_transicao_invalida():
    assistencia = _assistencia(status="CONCLUIDA", version=1)
    row = _row(status_codigo="EM_ATENDIMENTO", version=4, fk_analista_responsavel=901)
    with mock.patch.object(admin_repo, "assistencia_by_id", return_value=assistencia), \
         mock.patch.object(solicitacao_repo, "solicitacao_by_id", return_value=row):
        _assert_error(
            lambda: svc.atualizar_assistencia(_session(), 8010, mock.Mock(
                status="PRESTADOR_ACIONADO", comentario="x", version=1)),
            "ASSISTANCE_INVALID_STATUS_TRANSITION",
            422,
        )


def test_atualizar_assistencia_não_encontrada():
    with mock.patch.object(admin_repo, "assistencia_by_id", return_value=None):
        _assert_error(
            lambda: svc.atualizar_assistencia(_session(), 9999, mock.Mock(
                status="REMOVIDA", comentario="x", version=1)),
            "ASSISTANCE_NOT_FOUND",
            404,
        )


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
    print(f"\nADMIN_SERVICE_TESTS_OK ({len(tests)} testes)")