import asyncio
import json

from fastapi import HTTPException, status

import repositories.sync_repository as sync_repo

_POLL_INTERVAL_SECONDS = 2.0

_VERSION_UNAVAILABLE = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Versão do banco indisponível.",
)


def get_version() -> dict:
    try:
        return sync_repo.get_version()
    except HTTPException:
        raise
    except Exception:
        raise _VERSION_UNAVAILABLE


def _sse_frame(version: dict) -> str:
    return f"data: {json.dumps(version, ensure_ascii=False)}\n\n"


async def version_stream():
    last_revision = None
    while True:
        version = sync_repo.get_version()
        if version["revision"] != last_revision:
            last_revision = version["revision"]
            yield _sse_frame(version)
        await asyncio.sleep(_POLL_INTERVAL_SECONDS)