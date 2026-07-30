import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db import Base

# Native JSONB on PostgreSQL, plain JSON (SQLite and others) everywhere else.
JsonVariant = JSON().with_variant(JSONB(), "postgresql")


class DraftStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    FAILED = "failed"


class SnsDraft(Base):
    __tablename__ = "sns_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    account: Mapped[str] = mapped_column(String, default="doctor")

    source_papers: Mapped[list] = mapped_column(JsonVariant, default=list)

    summary_ja: Mapped[str] = mapped_column(String, default="")
    x_post: Mapped[str] = mapped_column(String, default="")
    instagram_caption: Mapped[str] = mapped_column(String, default="")
    threads_post: Mapped[str] = mapped_column(String, default="")
    illustration_prompt: Mapped[str] = mapped_column(String, default="")

    image_path: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    status: Mapped[str] = mapped_column(
        String, default=DraftStatus.PENDING_APPROVAL.value
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    publish_results: Mapped[dict] = mapped_column(JsonVariant, default=dict)
