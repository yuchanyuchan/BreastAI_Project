import tweepy

from ...core.config import X_ACCESS_SECRET, X_ACCESS_TOKEN, X_API_KEY, X_API_SECRET
from .types import PublishResult


def _get_clients() -> tuple[tweepy.API, tweepy.Client]:
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        raise RuntimeError("X API credentials are not configured")

    auth = tweepy.OAuth1UserHandler(
        X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
    )
    api_v1 = tweepy.API(auth)
    client_v2 = tweepy.Client(
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )
    return api_v1, client_v2


def publish(text: str, image_path: str | None) -> PublishResult:
    try:
        api_v1, client_v2 = _get_clients()

        media_ids = None
        if image_path:
            media = api_v1.media_upload(filename=image_path)
            media_ids = [media.media_id]

        response = client_v2.create_tweet(text=text, media_ids=media_ids)
        tweet_id = response.data["id"]
        return PublishResult(
            status="published",
            post_id=str(tweet_id),
            url=f"https://x.com/i/web/status/{tweet_id}",
        )
    except tweepy.errors.TweepyException as exc:
        detail = str(exc)
        response = getattr(exc, "response", None)
        if response is not None:
            detail = f"{detail} | body: {response.text}"
        return PublishResult(status="failed", error=detail)
    except Exception as exc:
        return PublishResult(status="failed", error=str(exc))
