from fastapi import APIRouter
from fastapi.responses import StreamingResponse

import services.sync_service as sync_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/version")
def sync_version() -> dict:
    return sync_service.get_version()


@router.get("/events")
def sync_events() -> StreamingResponse:
    return StreamingResponse(
        sync_service.version_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )