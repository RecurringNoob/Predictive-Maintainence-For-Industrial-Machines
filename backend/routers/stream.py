import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from services.sse_manager import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stream"])


async def _event_generator(q: asyncio.Queue):
    """
    Yields SSE-formatted strings from the client's personal queue.
    Sends a comment ping every 30s to keep the connection alive through
    proxies and load balancers that close idle connections.
    """
    try:
        while True:
            try:
                # Wait up to 30s for a message; send a keepalive ping if nothing arrives
                message = await asyncio.wait_for(q.get(), timeout=30.0)
                yield message
            except asyncio.TimeoutError:
                yield ": ping\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        sse_manager.disconnect(q)
        logger.debug("SSE generator cleaned up")


@router.get("/stream")
async def stream(
):
    """
    Server-Sent Events endpoint. Connect once; the server pushes:
      - event: reading   (on every IoT poll)
      - event: prediction (on every IoT poll, after reading)

    Example client (JS):
      const es = new EventSource('/v1/stream');
      es.addEventListener('reading', e => console.log(JSON.parse(e.data)));
      es.addEventListener('prediction', e => console.log(JSON.parse(e.data)));
    """
    q = sse_manager.connect()
    return StreamingResponse(
        _event_generator(q),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
            "Connection": "keep-alive",
        },
    )