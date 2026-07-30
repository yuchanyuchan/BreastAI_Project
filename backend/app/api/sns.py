import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..db.models import DraftStatus, SnsDraft
from ..models.sns import DraftOut, GenerateBeautyRequest
from ..services.sns_pipeline import (
    generate_beauty_draft,
    generate_daily_draft,
    publish_approved_drafts,
)

router = APIRouter(prefix="/sns", tags=["sns"])


@router.get("/drafts", response_model=list[DraftOut])
def list_drafts(
    status: str | None = None, db: Session = Depends(get_db)
) -> list[SnsDraft]:
    query = db.query(SnsDraft)
    if status:
        query = query.filter(SnsDraft.status == status)
    return query.order_by(SnsDraft.created_at.desc()).all()


@router.get("/drafts/{draft_id}", response_model=DraftOut)
def get_draft(draft_id: uuid.UUID, db: Session = Depends(get_db)) -> SnsDraft:
    draft = db.get(SnsDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.post("/drafts/{draft_id}/approve", response_model=DraftOut)
def approve_draft(draft_id: uuid.UUID, db: Session = Depends(get_db)) -> SnsDraft:
    draft = db.get(SnsDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    draft.status = DraftStatus.APPROVED.value
    draft.approved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/drafts/{draft_id}/reject", response_model=DraftOut)
def reject_draft(draft_id: uuid.UUID, db: Session = Depends(get_db)) -> SnsDraft:
    draft = db.get(SnsDraft, draft_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    draft.status = DraftStatus.REJECTED.value
    db.commit()
    db.refresh(draft)
    return draft


@router.post("/tasks/generate-daily", response_model=DraftOut)
def trigger_generate_daily(db: Session = Depends(get_db)) -> SnsDraft:
    try:
        return generate_daily_draft(db)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Failed to generate draft: {exc}"
        ) from exc


@router.post("/tasks/generate-beauty", response_model=DraftOut)
def trigger_generate_beauty(
    payload: GenerateBeautyRequest = GenerateBeautyRequest(),
    db: Session = Depends(get_db),
) -> SnsDraft:
    try:
        return generate_beauty_draft(db, payload.topic)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Failed to generate draft: {exc}"
        ) from exc


@router.post("/tasks/publish-approved", response_model=list[DraftOut])
def trigger_publish_approved(db: Session = Depends(get_db)) -> list[SnsDraft]:
    return publish_approved_drafts(db)
