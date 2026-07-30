import httpx
import pytest
import respx

from backend.app.services.social import instagram_publisher as ig

GRAPH_API_BASE = ig.GRAPH_API_BASE
ACCOUNT_ID = "17800000000000000"
TOKEN = "super-secret-token"


@pytest.fixture(autouse=True)
def _configure_credentials(monkeypatch):
    monkeypatch.setattr(ig, "INSTAGRAM_ACCESS_TOKEN", TOKEN)
    monkeypatch.setattr(ig, "INSTAGRAM_ACCOUNT_ID", ACCOUNT_ID)
    monkeypatch.setattr(ig, "CONTAINER_POLL_DELAY_SECONDS", 0)


def test_build_caption_combines_content_and_hashtags():
    caption = ig.build_caption("こんにちは", ["乳がん", "#検診"])
    assert caption == "こんにちは\n\n#乳がん #検診"


def test_build_caption_without_hashtags_returns_content_only():
    assert ig.build_caption("こんにちは", []) == "こんにちは"
    assert ig.build_caption("こんにちは", None) == "こんにちは"


def test_publish_missing_credentials(monkeypatch):
    monkeypatch.setattr(ig, "INSTAGRAM_ACCESS_TOKEN", None)
    result = ig.publish("caption", "https://example.com/image.png")
    assert result.status == "failed"
    assert "not configured" in result.error


def test_publish_missing_image():
    result = ig.publish("caption", None)
    assert result.status == "failed"
    assert "image" in result.error


@respx.mock
def test_publish_success_creates_container_polls_and_publishes():
    media_route = respx.post(f"{GRAPH_API_BASE}/{ACCOUNT_ID}/media").mock(
        return_value=httpx.Response(200, json={"id": "container-1"})
    )
    status_route = respx.get(f"{GRAPH_API_BASE}/container-1").mock(
        return_value=httpx.Response(200, json={"status_code": "FINISHED"})
    )
    publish_route = respx.post(f"{GRAPH_API_BASE}/{ACCOUNT_ID}/media_publish").mock(
        return_value=httpx.Response(200, json={"id": "media-1"})
    )
    permalink_route = respx.get(f"{GRAPH_API_BASE}/media-1").mock(
        return_value=httpx.Response(
            200, json={"permalink": "https://www.instagram.com/p/abc123/"}
        )
    )

    result = ig.publish(
        "本文です", "https://example.com/image.png", hashtags=["乳がん"]
    )

    assert result.status == "published"
    assert result.post_id == "media-1"
    assert result.url == "https://www.instagram.com/p/abc123/"

    assert media_route.called
    assert status_route.called
    assert publish_route.called
    assert permalink_route.called

    # caption sent to Graph API must be content + hashtags, and auth must be via header,
    # never as a query param (so the token can't end up in a logged URL).
    sent_request = media_route.calls.last.request
    assert sent_request.url.params["caption"] == "本文です\n\n#乳がん"
    assert "access_token" not in sent_request.url.params
    assert sent_request.headers["Authorization"] == f"Bearer {TOKEN}"


@respx.mock
def test_publish_polls_until_container_finished():
    respx.post(f"{GRAPH_API_BASE}/{ACCOUNT_ID}/media").mock(
        return_value=httpx.Response(200, json={"id": "container-1"})
    )
    respx.get(f"{GRAPH_API_BASE}/container-1").mock(
        side_effect=[
            httpx.Response(200, json={"status_code": "IN_PROGRESS"}),
            httpx.Response(200, json={"status_code": "FINISHED"}),
        ]
    )
    respx.post(f"{GRAPH_API_BASE}/{ACCOUNT_ID}/media_publish").mock(
        return_value=httpx.Response(200, json={"id": "media-1"})
    )
    respx.get(f"{GRAPH_API_BASE}/media-1").mock(
        return_value=httpx.Response(200, json={"permalink": "https://x/"})
    )

    result = ig.publish("caption", "https://example.com/image.png")

    assert result.status == "published"


@respx.mock
def test_publish_container_error_status_fails():
    respx.post(f"{GRAPH_API_BASE}/{ACCOUNT_ID}/media").mock(
        return_value=httpx.Response(200, json={"id": "container-1"})
    )
    respx.get(f"{GRAPH_API_BASE}/container-1").mock(
        return_value=httpx.Response(200, json={"status_code": "ERROR"})
    )

    result = ig.publish("caption", "https://example.com/image.png")

    assert result.status == "failed"
    assert "processing failed" in result.error


@respx.mock
def test_publish_graph_api_error_never_leaks_token():
    respx.post(f"{GRAPH_API_BASE}/{ACCOUNT_ID}/media").mock(
        return_value=httpx.Response(
            400,
            json={"error": {"message": "Invalid parameter", "code": 100}},
        )
    )

    result = ig.publish("caption", "https://example.com/image.png")

    assert result.status == "failed"
    assert "Invalid parameter" in result.error
    assert TOKEN not in result.error


@respx.mock
def test_publish_network_error_never_leaks_token():
    respx.post(f"{GRAPH_API_BASE}/{ACCOUNT_ID}/media").mock(
        side_effect=httpx.ConnectError(f"connection failed to {GRAPH_API_BASE}?access_token={TOKEN}")
    )

    result = ig.publish("caption", "https://example.com/image.png")

    assert result.status == "failed"
    assert TOKEN not in result.error
