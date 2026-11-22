"""FastAPI application entrypoint for KASSEM NEWS."""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app import media
from app.api import admin as admin_api
from app.api import auth as auth_api
from app.api import public as public_api
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.ingestion.scheduler import shutdown_scheduler, start_scheduler
from app.logging_config import configure_logging
from app.migrate import run_migrations
from app.models import Article, ArticleStatus
from app.publishing import ensure_default_rules

configure_logging(logging.DEBUG if settings.debug else logging.INFO)
logger = logging.getLogger("kassem.main")

SITE_URL = settings.site_url.rstrip("/")

# --- Naive in-memory rate limiter (per client IP). For multi-worker prod use
#     a shared store (Redis) or an edge rate limiter. ---
_HITS: dict[str, deque] = defaultdict(deque)
_RATE_LIMITED_PREFIXES = ("/api/auth/login", "/api/assistant/chat")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        run_migrations(engine, db)
        ensure_default_rules(db)
    finally:
        db.close()
    start_scheduler()
    logger.info("application started")
    yield
    shutdown_scheduler()
    logger.info("application stopped")


app = FastAPI(
    title=settings.app_name,
    description="منصة إخبارية رقمية عالمية — التركيز على لبنان والشرق الأوسط.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    path = request.url.path
    if any(path.startswith(p) for p in _RATE_LIMITED_PREFIXES):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = _HITS[ip]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= 10:
            return JSONResponse(status_code=429, content={"detail": "طلبات كثيرة جداً. حاول لاحقاً."})
        bucket.append(now)
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "حدث خطأ داخلي في الخادم"})


app.include_router(public_api.router)
app.include_router(auth_api.router)
app.include_router(admin_api.router)

# Served media (uploaded news videos). ``StaticFiles`` honours HTTP Range
# requests, which browsers rely on to seek within a video.
app.mount("/uploads", StaticFiles(directory=media.uploads_root()), name="uploads")


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"app": settings.app_name, "slogan": settings.app_slogan_ar, "docs": "/docs"}


@app.get("/robots.txt", include_in_schema=False)
def robots() -> PlainTextResponse:
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        "Disallow: /api/admin\n"
        f"Sitemap: {SITE_URL}/sitemap.xml\n"
    )
    return PlainTextResponse(content)


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Article).where(Article.status == ArticleStatus.published)
            .order_by(Article.published_at.desc()).limit(5000)
        ).all()
    finally:
        db.close()
    urls = [f"{SITE_URL}/", f"{SITE_URL}/breaking"]
    for article in rows:
        lastmod = (article.updated_at or article.received_at)
        urls.append(f"{SITE_URL}/article/{article.id}")
        _ = lastmod  # lastmod available if needed in extended sitemap
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
        + "\n</urlset>\n"
    )
    return Response(content=body, media_type="application/xml")
