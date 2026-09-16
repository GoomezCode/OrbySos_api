from unittest import mock

import repositories.admin_repository as admin_repo
import repositories.solicitacao_repository as solicitacao_repo
import repositories.sync_repository as sync_repo


class FakeCursor:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.executed = []
        self.rowcount = 1
        self.lastrowid = 100
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append(query)

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        return []

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, rows=None):
        self.cursor_obj = FakeCursor(rows)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, dictionary=False):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _assert_bump_within_transaction(fake_conn, bump_mock):
    assert bump_mock.call_count == 1
    called_cur, called_now = bump_mock.call_args.args
    assert called_cur is fake_conn.cursor_obj
    assert called_now is not None
    assert fake_conn.committed is True
    assert fake_conn.rolled_back is False


def test_bump_revision_cursor_executes_increment_and_updated_at():
    cursor = FakeCursor()
    now = "2026-09-15 10:00:00"
    sync_repo.bump_revision_cursor(cursor, now)
    assert len(cursor.executed) == 2
    assert "orbyt_meta" in cursor.executed[0]
    assert "orbyt_meta" in cursor.executed[1]
    assert "CAST(valor AS UNSIGNED) + 1" in cursor.executed[0]


def test_get_version_returns_zero_when_empty():
    with mock.patch.object(sync_repo, "get_connection") as mk:
        fake_conn = FakeConnection(rows=[])
        mk.return_value = fake_conn
        result = sync_repo.get_version()
    assert result == {"revision": 0, "updated_at": None}


def test_create_solicitacao_bumps_within_transaction():
    bom = sync_repo.bump_revision_cursor
    status_conn = FakeConnection(rows=[{"id_status": 7}])
    fake_conn = FakeConnection()

    with mock.patch.object(
        solicitacao_repo, "get_connection", side_effect=[status_conn, fake_conn]
    ), mock.patch.object(
        sync_repo, "bump_revision_cursor", wraps=bom
    ) as bump_mock:
        result = solicitacao_repo.create_solicitacao(
            id_solicitacao_cliente="uuid-1",
            protocolo_solicitacao="ORB-2026-000058",
            numero_solicitacao="ORB-2026-000058",
            descricao_evento="Falha mecanica.",
            possui_feridos=False,
            risco_imediato=False,
            prioridade="NORMAL",
            data_criacao_cliente=None,
            data_recebimento="2026-09-15 10:00:00",
            fk_apolice=1002,
            fk_pessoa=1,
            fk_seguradora=10,
            fk_veiculo=202,
            fk_tipo_ocorrencia=1,
            endereco="Rua A",
            numero_local="10",
            cidade="SP",
            estado="SP",
            ponto_referencia=None,
            nome_responsavel="Marina",
        )
    assert result == 100
    _assert_bump_within_transaction(fake_conn, bump_mock)


def test_answer_pergunta_bumps_within_transaction():
    bom = sync_repo.bump_revision_cursor
    status_conn = FakeConnection(rows=[{"id_status": 9}])
    fake_conn = FakeConnection()

    with mock.patch.object(
        solicitacao_repo, "get_connection", side_effect=[status_conn, fake_conn]
    ), mock.patch.object(
        sync_repo, "bump_revision_cursor", wraps=bom
    ) as bump_mock:
        result = solicitacao_repo.answer_pergunta(
            id_pergunta=7001,
            necessita_taxi=True,
            quantidade_passageiros=2,
            necessita_acessibilidade=False,
            quantidade_criancas=0,
            quantidade_animais=0,
            bagagem="Mala",
            observacoes=None,
            data_resposta="2026-09-15 10:30:00",
            version=1,
        )
    assert result is True
    _assert_bump_within_transaction(fake_conn, bump_mock)


def test_transicionar_bumps_within_transaction():
    bom = sync_repo.bump_revision_cursor
    rows = [{"id_status": 3}, {"id_status": 2}]

    with mock.patch.object(admin_repo, "get_connection") as mk, \
         mock.patch.object(
             sync_repo, "bump_revision_cursor", wraps=bom
         ) as bump_mock:
        fake_conn = FakeConnection(rows=rows)
        mk.return_value = fake_conn
        result = admin_repo.transicionar_solicitacao(
            id_solicitacao=51,
            from_status_codigo="EM_ANALISE",
            to_status_codigo="CONFIRMADA",
            version=2,
            id_usuario=901,
            nome_exibicao="Analista Horizonte",
            comentario="Confirmado.",
            now="2026-09-15 11:00:00",
            set_decisao=True,
            motivo_recusa=None,
        )
    assert result is True
    _assert_bump_within_transaction(fake_conn, bump_mock)


def test_transicionar_stale_version_no_bump():
    bom = sync_repo.bump_revision_cursor
    rows = [{"id_status": 3}, {"id_status": 2}]

    with mock.patch.object(admin_repo, "get_connection") as mk, \
         mock.patch.object(
             sync_repo, "bump_revision_cursor", wraps=bom
         ) as bump_mock:
        fake_conn = FakeConnection(rows=rows)
        fake_conn.cursor_obj.rowcount = 0
        mk.return_value = fake_conn
        result = admin_repo.transicionar_solicitacao(
            id_solicitacao=51,
            from_status_codigo="EM_ANALISE",
            to_status_codigo="CONFIRMADA",
            version=2,
            id_usuario=901,
            nome_exibicao="Analista Horizonte",
            comentario="Confirmado.",
            now="2026-09-15 11:00:00",
        )
    assert result is False
    assert bump_mock.call_count == 0
    assert fake_conn.rolled_back is True
    assert fake_conn.committed is False


def test_add_assistencia_bumps_within_transaction():
    bom = sync_repo.bump_revision_cursor
    rows = [
        {"id_solicitacao": 51, "fk_apolice": 1002, "version": 3, "status_codigo": "CONFIRMADA"},
        {"id_tipo_assistencia": 1, "codigo": "GUINCHO", "nome": "Guincho", "descricao": "R."},
        None,
        None,
        None,
        {"id_status": 30},
        {"id_status": 5},
    ]

    with mock.patch.object(admin_repo, "get_connection") as mk, \
         mock.patch.object(
             sync_repo, "bump_revision_cursor", wraps=bom
         ) as bump_mock:
        fake_conn = FakeConnection(rows=rows)
        mk.return_value = fake_conn
        result = admin_repo.add_assistencia(
            id_solicitacao=51,
            id_usuario=901,
            nome_exibicao="Analista Horizonte",
            tipo_assistencia_id=1,
            comentario=None,
            now="2026-09-15 11:30:00",
        )
    assert result["assistencia"]["status"] == "INCLUIDA"
    _assert_bump_within_transaction(fake_conn, bump_mock)


def test_update_assistencia_status_bumps_within_transaction():
    bom = sync_repo.bump_revision_cursor
    rows = [{"id_status": 6}]

    with mock.patch.object(admin_repo, "get_connection") as mk, \
         mock.patch.object(
             sync_repo, "bump_revision_cursor", wraps=bom
         ) as bump_mock:
        fake_conn = FakeConnection(rows=rows)
        mk.return_value = fake_conn
        result = admin_repo.update_assistencia_status(
            assistance_id=8010,
            status_destino="PRESTADOR_ACIONADO",
            comentario="Protocolo DEMO-1.",
            version=1,
            id_usuario=901,
            nome_exibicao="Analista Horizonte",
            now="2026-09-15 12:00:00",
            fk_solicitacao=51,
            request_status_codigo="EM_ATENDIMENTO",
        )
    assert result["status"] == "PRESTADOR_ACIONADO"
    _assert_bump_within_transaction(fake_conn, bump_mock)


def test_add_assistencia_calls_bump():
    bom = sync_repo.bump_revision_cursor
    rows = [
        {"id_solicitacao": 51, "fk_apolice": 1002, "version": 3, "status_codigo": "CONFIRMADA"},
        {"id_tipo_assistencia": 1, "codigo": "GUINCHO", "nome": "Guincho", "descricao": "R."},
        None,
        None,
        None,
        {"id_status": 30},
        {"id_status": 5},
    ]

    with mock.patch.object(admin_repo, "get_connection") as mk, \
         mock.patch.object(
             sync_repo, "bump_revision_cursor", wraps=bom
         ) as bump_mock:
        fake_conn = FakeConnection(rows=rows)
        mk.return_value = fake_conn
        admin_repo.add_assistencia(
            id_solicitacao=51,
            id_usuario=901,
            nome_exibicao="Analista Horizonte",
            tipo_assistencia_id=1,
            comentario=None,
            now="2026-09-15 11:30:00",
        )
    orbyt_executes = [
        q for q in fake_conn.cursor_obj.executed if "orbyt_meta" in q
    ]
    assert len(orbyt_executes) == 2
    expected_index = fake_conn.cursor_obj.executed.index(orbyt_executes[0])
    queued = fake_conn.cursor_obj.executed[-1]
    assert expected_index < len(fake_conn.cursor_obj.executed)
    assert queued == orbyt_executes[1]
    assert bump_mock.call_count == 1


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
    print(f"\nREVISION_INTEGRATION_TESTS_OK ({len(tests)} testes)")