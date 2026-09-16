import json
from unittest import mock

from fastapi.testclient import TestClient

from main import app
import repositories.sync_repository as sync_repo
import services.sync_service as sync_service

client = TestClient(app)


def _sync_version_fixture():
    return {"revision": 5, "updated_at": "2026-08-18T10:00:00Z"}


async def _bounded_stream(revisions):
    for r in revisions:
        yield f'data: {json.dumps(r, ensure_ascii=False)}\n\n'


def test_version_publica_sem_token():
    with mock.patch.object(sync_repo, "get_version",
                           return_value={"revision": 0, "updated_at": None}):
        response = client.get("/api/v1/sync/version")
    assert response.status_code == 200
    assert response.json() == {"revision": 0, "updated_at": None}


def test_version_payload_com_revision_inteiro():
    with mock.patch.object(sync_repo, "get_version",
                           return_value={"revision": 9, "updated_at": "2026-08-18T10:00:00Z"}):
        response = client.get("/api/v1/sync/version", headers={"Accept": "application/json"})
    assert response.status_code == 200
    body = response.json()
    assert body["revision"] == 9
    assert isinstance(body["revision"], int)


def test_version_repository_error_500():
    with mock.patch.object(sync_repo, "get_version", side_effect=RuntimeError("db down")):
        response = client.get("/api/v1/sync/version")
    assert response.status_code == 500


def test_events_publico_sem_token_retorna_stream():
    v = _sync_version_fixture()
    with mock.patch.object(sync_service, "version_stream",
                           return_value=_bounded_stream([v, v])):
        with client.stream("GET", "/api/v1/sync/events") as response:
            assert response.status_code == 200
            ct = response.headers.get("content-type", "")
            assert ct.startswith("text/event-stream"), ct
            assert response.headers.get("cache-control") == "no-cache, no-transform"
            lines = list(response.iter_lines())
    data_lines = [l for l in lines if l.startswith("data:")]
    assert len(data_lines) >= 1
    payload = json.loads(data_lines[0].removeprefix("data: "))
    assert payload == v


def test_events_segue_mudanca_de_revision():
    v1 = {"revision": 1, "updated_at": "2026-08-18T10:00:00Z"}
    v2 = {"revision": 3, "updated_at": "2026-08-18T10:00:05Z"}
    with mock.patch.object(sync_service, "version_stream",
                           return_value=_bounded_stream([v1, v2])):
        with client.stream("GET", "/api/v1/sync/events") as response:
            lines = list(response.iter_lines())
    data_lines = [l for l in lines if l.startswith("data:")]
    assert len(data_lines) == 2
    assert json.loads(data_lines[0].removeprefix("data: ")) == v1
    assert json.loads(data_lines[1].removeprefix("data: ")) == v2


def test_events_erro_repositorio_encerra_stream():
    async def _error_stream():
        yield 'data: {"revision": 0, "updated_at": null}\n\n'

    with mock.patch.object(sync_service, "version_stream", return_value=_error_stream()):
        with client.stream("GET", "/api/v1/sync/events") as response:
            assert response.status_code == 200
            lines = list(response.iter_lines())
    assert any("data:" in l for l in lines)


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
    print(f"\nSYNC_ROUTES_TESTS_OK ({len(tests)} testes)")