from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..core.config import INSTAGRAM_HASHTAGS_BY_ACCOUNT
from ..db.models import DraftStatus, SnsDraft
from .image_service import generate_illustration
from .pubmed_service import fetch_latest_papers
from .sns_content_service import generate_sns_content
from .social import instagram_publisher, threads_publisher, x_publisher


def generate_daily_draft(db: Session) -> SnsDraft:
    papers = fetch_latest_papers()
    content = generate_sns_content(account="doctor", papers=papers)
    return _save_draft(db, account="doctor", content=content, source_papers=papers)


def generate_beauty_draft(db: Session, topic: str) -> SnsDraft:
    content = generate_sns_content(account="beauty", topic=topic)
    return _save_draft(db, account="beauty", content=content, source_papers=[])


def _save_draft(db: Session, account: str, content, source_papers: list[dict]) -> SnsDraft:
    draft = SnsDraft(
        account=account,
        source_papers=source_papers,
        summary_ja=content.summary_ja,
        x_post=content.x_post,
        instagram_caption=content.instagram_caption,
        threads_post=content.threads_post,
        illustration_prompt=content.illustration_prompt,
        status=DraftStatus.PENDING_APPROVAL.value,
    )
    db.add(draft)
    db.flush()  # assign draft.id so it can be used as the image filename

    image_path, image_url = generate_illustration(content.illustration_prompt, draft.id)
    draft.image_path = image_path
    draft.image_url = image_url

    db.commit()
    db.refresh(draft)
    return draft


def publish_approved_drafts(db: Session) -> list[SnsDraft]:
    # Only approved drafts are ever eligible for publishing - pending_approval/rejected/
    # published drafts must never be posted, even if this query is changed later.
    drafts = (
        db.query(SnsDraft).filter(SnsDraft.status == DraftStatus.APPROVED.value).all()
    )

    for draft in drafts:
        if draft.status != DraftStatus.APPROVED.value:
            continue

        results = dict(draft.publish_results or {})

        # Retries skip platforms that already succeeded, so a retry never double-posts.
        if results.get("x", {}).get("status") != "published":
            results["x"] = x_publisher.publish(draft.x_post, draft.image_path).to_dict()

        if results.get("instagram", {}).get("status") != "published":
            hashtags = INSTAGRAM_HASHTAGS_BY_ACCOUNT.get(draft.account, [])
            results["instagram"] = instagram_publisher.publish(
                draft.instagram_caption, draft.image_url, hashtags=hashtags
            ).to_dict()

        if results.get("threads", {}).get("status") != "published":
            results["threads"] = threads_publisher.publish(
                draft.threads_post, draft.image_url
            ).to_dict()

        draft.publish_results = results

        all_ok = all(
            results.get(platform, {}).get("status") == "published"
            for platform in ("x", "instagram", "threads")
        )
        if all_ok:
            draft.status = DraftStatus.PUBLISHED.value
            draft.published_at = datetime.now(timezone.utc)
        # else: leave status as APPROVED so a failed publish can be retried later.

    db.commit()
    return drafts
