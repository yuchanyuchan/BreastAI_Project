from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..services.sns_pipeline import generate_daily_draft, publish_approved_drafts
from .config import SNS_GENERATE_HOUR, SNS_PUBLISH_INTERVAL_MINUTES, SNS_TIMEZONE
from .db import SessionLocal

scheduler = BackgroundScheduler(timezone=SNS_TIMEZONE)


def _run_generate_daily_draft() -> None:
    db = SessionLocal()
    try:
        generate_daily_draft(db)
    finally:
        db.close()


def _run_publish_approved_drafts() -> None:
    db = SessionLocal()
    try:
        publish_approved_drafts(db)
    finally:
        db.close()


def start_scheduler() -> None:
    scheduler.add_job(
        _run_generate_daily_draft,
        trigger=CronTrigger(hour=SNS_GENERATE_HOUR, minute=0),
        id="generate_daily_draft",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_publish_approved_drafts,
        trigger=IntervalTrigger(minutes=SNS_PUBLISH_INTERVAL_MINUTES),
        id="publish_approved_drafts",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
