"""Command-line entrypoint for ingestion.

Examples:
    python -m app.ingestion.cli run
    python -m app.ingestion.cli run --source bbc-arabic --source aljazeera-ar
"""
from __future__ import annotations

import argparse
import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.ingestion.pipeline import run_ingestion
from app.logging_config import configure_logging
from app.models import Source


def main() -> None:
    parser = argparse.ArgumentParser(description="KASSEM NEWS ingestion CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", help="run one ingestion pass")
    run_parser.add_argument("--source", action="append", default=None,
                            help="source slug (repeatable); default = all active sources")
    args = parser.parse_args()

    configure_logging(logging.INFO)
    db = SessionLocal()
    try:
        source_ids = None
        if args.source:
            rows = db.scalars(select(Source).where(Source.slug.in_(args.source))).all()
            source_ids = [s.id for s in rows]
            missing = set(args.source) - {s.slug for s in rows}
            if missing:
                print(f"مصادر غير موجودة: {', '.join(sorted(missing))}")
        run = run_ingestion(db, trigger="manual", source_ids=source_ids)
        print(
            f"اكتمل التوريد [{run.status.value}] | "
            f"مصادر: {run.sources_ok}/{run.sources_total} | "
            f"جديد: {run.articles_new} | منشور: {run.articles_published} | "
            f"مراجعة: {run.articles_review} | مكرر: {run.duplicates} | أخطاء: {run.errors}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
