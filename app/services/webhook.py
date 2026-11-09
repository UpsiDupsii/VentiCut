import datetime
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


async def dispatch_webhook(
    webhook_url: str | None,
    event: str,
    job_id: str,
    status: str,
    progress: int,
    message: str,
    payload: dict[str, Any] | None = None,
) -> bool:
    """Dispatches a non-blocking webhook notification to an external endpoint."""
    if not webhook_url:
        return False

    body = {
        "event": event,
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message,
        "payload": payload or {},
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(webhook_url, json=body)
            if resp.status_code >= 400:
                logger.warning(
                    f"Webhook target {webhook_url} responded with status {resp.status_code}"
                )
                return False
            logger.info(
                f"Webhook dispatched to {webhook_url} for event {event} (status {resp.status_code})"
            )
            return True
    except Exception as e:
        logger.warning(f"Failed to deliver webhook to {webhook_url}: {e}")
        return False
