from backend.app.db.models import DraftStatus, SnsDraft
from backend.app.services import sns_pipeline
from backend.app.services.social import instagram_publisher, threads_publisher, x_publisher
from backend.app.services.social.types import PublishResult


def _make_draft(db_session, status: str, publish_results: dict | None = None) -> SnsDraft:
    draft = SnsDraft(
        account="doctor",
        source_papers=[],
        summary_ja="要約",
        x_post="Xの投稿",
        instagram_caption="Instagramの本文",
        threads_post="Threadsの投稿",
        illustration_prompt="prompt",
        image_path="/tmp/image.png",
        image_url="https://example.com/image.png",
        status=status,
        publish_results=publish_results or {},
    )
    db_session.add(draft)
    db_session.commit()
    db_session.refresh(draft)
    return draft


def test_draft_status_pending_cannot_be_published(db_session, monkeypatch):
    calls = []
    monkeypatch.setattr(
        instagram_publisher, "publish", lambda *a, **k: calls.append("instagram")
    )
    draft = _make_draft(db_session, DraftStatus.PENDING_APPROVAL.value)

    result = sns_pipeline.publish_approved_drafts(db_session)

    assert result == []
    assert calls == []
    db_session.refresh(draft)
    assert draft.status == DraftStatus.PENDING_APPROVAL.value
    assert draft.publish_results == {}


def test_rejected_draft_cannot_be_published(db_session, monkeypatch):
    calls = []
    monkeypatch.setattr(
        instagram_publisher, "publish", lambda *a, **k: calls.append("instagram")
    )
    _make_draft(db_session, DraftStatus.REJECTED.value)

    result = sns_pipeline.publish_approved_drafts(db_session)

    assert result == []
    assert calls == []


def test_approved_draft_all_success_becomes_published(db_session, monkeypatch):
    monkeypatch.setattr(
        x_publisher, "publish", lambda *a, **k: PublishResult(status="published", post_id="x1")
    )
    monkeypatch.setattr(
        instagram_publisher,
        "publish",
        lambda *a, **k: PublishResult(status="published", post_id="ig1"),
    )
    monkeypatch.setattr(
        threads_publisher,
        "publish",
        lambda *a, **k: PublishResult(status="published", post_id="th1"),
    )
    draft = _make_draft(db_session, DraftStatus.APPROVED.value)

    sns_pipeline.publish_approved_drafts(db_session)

    db_session.refresh(draft)
    assert draft.status == DraftStatus.PUBLISHED.value
    assert draft.published_at is not None
    assert draft.publish_results["instagram"]["status"] == "published"


def test_instagram_failure_keeps_status_approved(db_session, monkeypatch):
    monkeypatch.setattr(
        x_publisher, "publish", lambda *a, **k: PublishResult(status="published", post_id="x1")
    )
    monkeypatch.setattr(
        instagram_publisher,
        "publish",
        lambda *a, **k: PublishResult(status="failed", error="Instagram API error: rate limited"),
    )
    monkeypatch.setattr(
        threads_publisher,
        "publish",
        lambda *a, **k: PublishResult(status="published", post_id="th1"),
    )
    draft = _make_draft(db_session, DraftStatus.APPROVED.value)

    sns_pipeline.publish_approved_drafts(db_session)

    db_session.refresh(draft)
    # Draft must stay approved (not move to a terminal "failed" state) so it can be retried.
    assert draft.status == DraftStatus.APPROVED.value
    assert draft.published_at is None
    assert draft.publish_results["instagram"]["status"] == "failed"
    assert draft.publish_results["x"]["status"] == "published"


def test_retry_skips_platforms_already_published(db_session, monkeypatch):
    x_calls = []
    ig_calls = []
    monkeypatch.setattr(
        x_publisher,
        "publish",
        lambda *a, **k: x_calls.append(1) or PublishResult(status="published", post_id="x1"),
    )
    monkeypatch.setattr(
        instagram_publisher,
        "publish",
        lambda *a, **k: ig_calls.append(1) or PublishResult(status="published", post_id="ig1"),
    )
    monkeypatch.setattr(
        threads_publisher,
        "publish",
        lambda *a, **k: PublishResult(status="published", post_id="th1"),
    )
    draft = _make_draft(
        db_session,
        DraftStatus.APPROVED.value,
        publish_results={
            "x": {"status": "published", "post_id": "x1", "url": None, "error": None},
            "instagram": {"status": "failed", "post_id": None, "url": None, "error": "boom"},
            "threads": {"status": "failed", "post_id": None, "url": None, "error": "boom"},
        },
    )

    sns_pipeline.publish_approved_drafts(db_session)

    db_session.refresh(draft)
    assert x_calls == []  # already published - must not be re-posted
    assert ig_calls == [1]  # previously failed - retried
    assert draft.status == DraftStatus.PUBLISHED.value
