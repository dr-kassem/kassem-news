import os
import tempfile

import pytest

_tmp = tempfile.mkdtemp(prefix="kassem-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_tmp, 'test.db')}"
os.environ["INGESTION_ENABLED"] = "false"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key"
# Tests must stay offline and deterministic: never call the real AI provider.
os.environ["AI_ENABLED"] = "false"
os.environ["OPENROUTER_API_KEY"] = ""

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import (  # noqa: E402
    Category,
    Country,
    Region,
    Role,
    Source,
    SourceType,
    User,
)
from app.security import hash_password  # noqa: E402


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db(db_engine):
    # Fresh schema for every test to guarantee isolation.
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def seed_data(db):
    def get_or_add(model, **kwargs):
        existing = db.query(model).filter_by(**kwargs).first()
        if existing is not None:
            return existing
        obj = model(**kwargs)
        db.add(obj)
        db.flush()
        return obj

    regions = {}
    for data in [
        {"slug": "lebanon", "name_ar": "لبنان", "name_en": "Lebanon"},
        {"slug": "middle-east", "name_ar": "الشرق الأوسط", "name_en": "Middle East"},
    ]:
        regions[data["slug"]] = get_or_add(Region, **data)
    categories = {}
    for data in [
        {"slug": "politics", "name_ar": "سياسة", "name_en": "Politics"},
        {"slug": "economy", "name_ar": "اقتصاد", "name_en": "Economy"},
        {"slug": "world", "name_ar": "العالم", "name_en": "World"},
    ]:
        categories[data["slug"]] = get_or_add(Category, **data)
    get_or_add(
        Country, iso_code="LB", name_ar="لبنان", name_en="Lebanon",
        region_id=regions["lebanon"].id,
    )
    source = get_or_add(
        Source,
        slug="test-source",
        name_ar="مصدر اختبار",
        name_en="Test Source",
        feed_url="https://example.test/feed",
    )
    source.type = SourceType.rss
    source.trust_tier = 1
    source.requires_review = False
    source.is_active = True
    source.language = "ar"
    user = get_or_add(
        User,
        email="editor@test.news",
        full_name="محرر",
        hashed_password=hash_password("password123"),
        role=Role.editor,
        is_active=True,
    )
    db.commit()
    yield {
        "category": {slug: cat.id for slug, cat in categories.items()},
        "region": regions,
        "source": source,
        "user": user,
    }