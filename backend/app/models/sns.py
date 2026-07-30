from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class PaperRef(BaseModel):
    pmid: str
    title: str
    url: str
    published_date: str | None = None


class GeneratedContent(BaseModel):
    """Structured output requested from the model for one draft."""

    summary_ja: str
    x_post: str
    instagram_caption: str
    threads_post: str
    illustration_prompt: str


class GenerateBeautyRequest(BaseModel):
    topic: str = "豊胸手術（乳房インプラント）に関する一般的な情報"


class DraftOut(BaseModel):
    id: UUID
    created_at: datetime
    account: str
    source_papers: list[PaperRef]
    summary_ja: str
    x_post: str
    instagram_caption: str
    threads_post: str
    illustration_prompt: str
    image_url: str | None
    status: str
    approved_at: datetime | None
    published_at: datetime | None
    publish_results: dict[str, Any]

    model_config = {"from_attributes": True}
