import time

import httpx

from ...core.config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID
from .types import PublishResult

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
CONTAINER_POLL_ATTEMPTS = 10
CONTAINER_POLL_DELAY_SECONDS = 2


def build_caption(content: str, hashtags: list[str] | None = None) -> str:
    """Compose the final Instagram caption from post content + hashtags."""
    content = (content or "").strip()
    tags = [tag.lstrip("#") for tag in (hashtags or []) if tag.strip()]
    if not tags:
        return content
    tag_line = " ".join(f"#{tag}" for tag in tags)
    return f"{content}\n\n{tag_line}" if content else tag_line


def _redact(text: str) -> str:
    if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCESS_TOKEN in text:
        text = text.replace(INSTAGRAM_ACCESS_TOKEN, "***REDACTED***")
    return text


def _extract_graph_error(exc: httpx.HTTPStatusError) -> str:
    try:
        message = exc.response.json().get("error", {}).get("message")
    except Exception:
        message = None
    if message:
        return _redact(f"Instagram API error: {message}")
    return _redact(f"Instagram API error: HTTP {exc.response.status_code}")


def _wait_for_container_ready(client: httpx.Client, creation_id: str, headers: dict) -> None:
    """Poll the media container until Meta finishes processing it (or raise)."""
    for _ in range(CONTAINER_POLL_ATTEMPTS):
        response = client.get(
            f"{GRAPH_API_BASE}/{creation_id}",
            params={"fields": "status_code"},
            headers=headers,
        )
        response.raise_for_status()
        status_code = response.json().get("status_code")
        if status_code == "FINISHED":
            return
        if status_code == "ERROR":
            raise RuntimeError("Instagram media container processing failed")
        time.sleep(CONTAINER_POLL_DELAY_SECONDS)
    raise TimeoutError("Instagram media container did not finish processing in time")


def _fetch_permalink(client: httpx.Client, media_id: str, headers: dict) -> str | None:
    try:
        response = client.get(
            f"{GRAPH_API_BASE}/{media_id}",
            params={"fields": "permalink"},
            headers=headers,
        )
        response.raise_for_status()
        return response.json().get("permalink")
    except Exception:
        return None


def publish(
    caption: str, image_url: str | None, hashtags: list[str] | None = None
) -> PublishResult:
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_ACCOUNT_ID:
        return PublishResult(
            status="failed", error="Instagram credentials are not configured"
        )
    if not image_url:
        return PublishResult(status="failed", error="Instagram requires an image")

    full_caption = build_caption(caption, hashtags)
    # Auth via header (not query params) so the token never ends up in a logged/thrown URL.
    headers = {"Authorization": f"Bearer {INSTAGRAM_ACCESS_TOKEN}"}

    try:
        with httpx.Client(timeout=30) as client:
            container_response = client.post(
                f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media",
                params={"image_url": image_url, "caption": full_caption},
                headers=headers,
            )
            container_response.raise_for_status()
            creation_id = container_response.json()["id"]

            _wait_for_container_ready(client, creation_id, headers)

            publish_response = client.post(
                f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
                params={"creation_id": creation_id},
                headers=headers,
            )
            publish_response.raise_for_status()
            media_id = publish_response.json()["id"]

            permalink = _fetch_permalink(client, media_id, headers)

        return PublishResult(status="published", post_id=media_id, url=permalink)
    except httpx.HTTPStatusError as exc:
        return PublishResult(status="failed", error=_extract_graph_error(exc))
    except Exception as exc:
        return PublishResult(status="failed", error=_redact(str(exc)))
