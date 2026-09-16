import asyncio
from unittest import mock

from fastapi import HTTPException

import repositories.sync_repository as sync_repo
import services.sync_service as svc


async def _collect(gen, n):
    frames = []
    try:
        for _ in range(n):
            frames.append(await gen.__anext__())
    except StopAsyncIteration:
        pass
    finally:
        await gen.aclose()
    return frames


def _patch_sleep():
    return mock.patch.object(svc.asyncio, "sleep", new=mock.AsyncMock(return_value=None))


def test_get_version_payload():
    with mock.patch.object(sync_repo, "get_version",
                           return_value={"revision": 7, "updated_at": "2026-08-18T10:00:00Z"}):
        result = svc.get_version()
    assert result == {"revision": 7, "updated_at": "2026-08-18T10:00:00Z"}
    assert isinstance(result["revision"], int)


def test_get_version_repository_error_500():
    with mock.patch.object(sync_repo, "get_version", side_effect=RuntimeError("db down")):
        try:
            svc.get_version()
        except HTTPException as exc:
            assert exc.status_code == 500
            return
    raise AssertionError("esperado HTTPException 500")


def test_sse_frame_formato():
    version = {"revision": 3, "updated_at": "2026-08-18T10:00:00Z"}
    assert svc._sse_frame(version) == 'data: {"revision": 3, "updated_at": "2026-08-18T10:00:00Z"}\n\n'


def test_version_stream_envia_imediato_e_dedupica():
    versions = [
        {"revision": 1, "updated_at": "2026-08-18T10:00:00Z"},
        {"revision": 1, "updated_at": "2026-08-18T10:00:00Z"},
        {"revision": 2, "updated_at": "2026-08-18T10:00:05Z"},
        {"revision": 2, "updated_at": "2026-08-18T10:00:05Z"},
    ]
    with mock.patch.object(sync_repo, "get_version", side_effect=versions), \
         _patch_sleep():
        frames = asyncio.run(_collect(svc.version_stream(), 2))
    assert frames == [
        'data: {"revision": 1, "updated_at": "2026-08-18T10:00:00Z"}\n\n',
        'data: {"revision": 2, "updated_at": "2026-08-18T10:00:05Z"}\n\n',
    ]


def test_version_stream_default_quando_sem_banco():
    with mock.patch.object(sync_repo, "get_version",
                           return_value={"revision": 0, "updated_at": None}), \
         _patch_sleep():
        frames = asyncio.run(_collect(svc.version_stream(), 1))
    assert frames == ['data: {"revision": 0, "updated_at": null}\n\n']


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
    print(f"\nSYNC_SERVICE_TESTS_OK ({len(tests)} testes)")