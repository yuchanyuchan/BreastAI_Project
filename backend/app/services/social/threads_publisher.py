import httpx

from ...core.config import THREADS_ACCESS_TOKEN
from .types import PublishResult

GRAPH_API_BASE = "https://graph.threads.net/v1.0"


def publish(text: str, image_url: str | None) -> PublishResult:
    if not THREADS_ACCESS_TOKEN:
        return PublishResult(
            status="failed", error="Threads credentials are not configured"
        )

    try:
        params = {
            "media_type": "IMAGE" if image_url else "TEXT",
            "text": text,
            "access_token": THREADS_ACCESS_TOKEN,
        }
        if image_url:
            params["image_url"] = image_url

        with httpx.Client(timeout=30) as client:
            container_response = client.post(
                f"{GRAPH_API_BASE}/me/threads", params=params
            )
            container_response.raise_for_status()
            creation_id = container_response.json()["id"]

            publish_response = client.post(
                f"{GRAPH_API_BASE}/me/threads_publish",
                params={
                    "creation_id": creation_id,
                    "access_token": THREADS_ACCESS_TOKEN,
                },
            )
            publish_response.raise_for_status()
            post_id = publish_response.json()["id"]

        return PublishResult(status="published", post_id=post_id)
    except Exception as exc:
        return PublishResult(status="failed", error=str(exc))
