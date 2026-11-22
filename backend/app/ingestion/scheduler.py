"""Background scheduler for periodic ingestion (APScheduler).

For a single-process deployment (development, small production) an in-process
scheduler is sufficient. In a multi-worker production deployment this is meant
to be replaced by the Celery beat worker described in the README; the task
entrypoint (`app.ingestion.pipeline.run_ingestion`) stays the same.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.ingestion.pipeline import run_ingestion
from app.publishing import get_rules

logger = logging.getLogger("kassem.ingest.scheduler")

_scheduler: BackgroundScheduler | None = None


def _tick() -> None:
    db = SessionLocal()
    try:
        rules = get_rules(db)
        if rules.get("ingestion_paused"):
            logger.info("ingestion paused by rule; skipping tick")
            return
        run_ingestion(db, trigger="scheduled")
    except Exception:  # noqa: BLE001
        logger.exception("scheduled ingestion failed")
    finally:
        db.close()


def _kairos_tick() -> None:
    db = SessionLocal()
    try:
        from app.kairos import generate_kairos_analysis

        generate_kairos_analysis(db)
    except Exception:  # noqa: BLE001
        logger.exception("scheduled kairos analysis failed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    if not settings.ingestion_enabled:
        logger.info("ingestion disabled by configuration")
        return None
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _tick,
        "interval",
        minutes=settings.ingestion_interval_minutes,
        id="kassem-ingestion",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
        # Run once shortly after startup, then every interval, so a restart
        # never delays the first automatic collection.
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=15),
    )
    if settings.kairos_enabled:
        # Fire on the 5-hour window boundaries (00,05,10,15,20 UTC) so the label
        # used by generate_kairos_analysis stays aligned. A short catch-up job
        # runs once at startup so a restart never costs a whole window.
        interval = max(1, settings.kairos_interval_hours)
        _scheduler.add_job(
            _kairos_tick,
            CronTrigger(hour=",".join(str(h) for h in range(0, 24, interval)),
                        minute=2, timezone="UTC"),
            id="kairos-analysis",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        _scheduler.add_job(
            _kairos_tick,
            "date",
            run_date=datetime.now(timezone.utc) + timedelta(seconds=20),
            id="kairos-startup",
            max_instances=1,
            replace_existing=True,
        )
    _scheduler.start()
    logger.info("scheduler started", extra={"event": f"every {settings.ingestion_interval_minutes}m"})
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
