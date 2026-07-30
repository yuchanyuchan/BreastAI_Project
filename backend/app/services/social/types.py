from dataclasses import dataclass


@dataclass
class PublishResult:
    status: str  # "published" or "failed"
    post_id: str | None = None
    url: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "post_id": self.post_id,
            "url": self.url,
            "error": self.error,
        }
