"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Core ---
    app_name: str = "KASSEM NEWS"
    app_slogan_ar: str = "العالم في الصورة الكاملة"
    app_slogan_en: str = "The World in Full Perspective"
    site_url: str = Field(default="https://kassem.news")
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    # --- Database ---
    # SQLite by default for zero-dependency local dev. Point to PostgreSQL in prod.
    database_url: str = Field(default="sqlite:///./kassem_news.db")

    @field_validator("database_url", mode="before")
    @classmethod
    def use_installed_postgres_driver(cls, value: str) -> str:
        # Render hands us postgresql:// URLs; SQLAlchemy would pick psycopg2 there,
        # but this image installs psycopg 3 only.
        if isinstance(value, str) and value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    # --- Security ---
    secret_key: str = Field(default="change-me-in-production")
    access_token_expire_minutes: int = Field(default=60 * 12)
    algorithm: str = "HS256"

    # --- Bootstrap admin (used only by the seed script) ---
    admin_email: str = Field(default="admin@kassem.news")
    admin_password: str = Field(default="ChangeMe123!")
    admin_name: str = Field(default="مدير التحرير")

    # --- CORS ---
    cors_origins: str = Field(default="http://localhost:3000")

    # --- Ingestion ---
    ingestion_enabled: bool = Field(default=True)
    ingestion_interval_minutes: int = Field(default=15)
    ingestion_timeout_seconds: int = Field(default=20)
    ingestion_max_retries: int = Field(default=3)
    ingestion_user_agent: str = Field(
        default="KassemNewsBot/1.0 (+https://kassem.news/bot)"
    )
    # Comma-separated keywords/phrases whose presence in a candidate item causes
    # it to be skipped (not ingested/published). Used to avoid transferring
    # news framed as hostile to the resistance axis.
    ingestion_blocked_keywords: str = Field(
        default=(
            "إرهابي,إرهاب,متطرف,الميليشيات,مليشيا"
        )
    )

    # --- Media uploads ---
    uploads_dir: str = Field(default="./uploads")
    max_video_mb: int = Field(default=200)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    # --- AI (OpenRouter / OpenAI-compatible) ---
    # The API key lives ONLY on the server. Never expose it to the frontend.
    ai_enabled: bool = Field(default=True)
    openrouter_api_key: str = Field(default="")
    ai_base_url: str = Field(default="https://openrouter.ai/api/v1")
    ai_model: str = Field(default="google/gemma-4-31b-it:free")
    ai_fallback_models: str = Field(
        default=(
            "nvidia/nemotron-3-ultra-550b-a55b:free,"
            "xingchen-agi/xing4.0-29b-a4b:free"
        )
    )
    ai_site_url: str = Field(default="https://kassem.news")
    ai_app_name: str = Field(default="Kassem News")
    ai_timeout_seconds: int = Field(default=90)
    ai_max_tokens: int = Field(default=1600)
    ai_temperature: float = Field(default=0.4)
    # Enrich new ingests (translate Arabic summary when the source is not Arabic).
    # Off by default: free models are slow and rate-limited, so this is opt-in.
    ai_summarize_on_ingest: bool = Field(default=False)
    ai_ingest_max_per_run: int = Field(default=20)

    @property
    def ai_configured(self) -> bool:
        return bool(self.ai_enabled and self.openrouter_api_key.strip())

    @property
    def ai_model_chain(self) -> list[str]:
        chain = [self.ai_model.strip()]
        for item in self.ai_fallback_models.split(","):
            name = item.strip()
            if name and name not in chain:
                chain.append(name)
        return [name for name in chain if name]

    # --- kairosAI (تحليل آلي) ---
    kairos_enabled: bool = Field(default=True)
    kairos_interval_hours: int = Field(default=5)
    kairos_author: str = Field(default="kairosAI — قاسم نيوز")
    kairos_stance: str = Field(
        default=(
            "كاييروس إيه آي هو المحلل الآلي لمنصة قاسم نيوز، وموقفه معلن وثابت: "
            "مؤيد لمحور المقاومة في ساحاته — المقاومة اللبنانية، وأنصار الله في "
            "اليمن، والمقاومة الإيرانية، والمقاومة العراقية — وينظر إلى تطورات "
            "المنطقة من هذه الزاوية دائماً. التحليلات آراء منصبية لا تُتّخذ كخبر، "
            "ولا تسقط حق القارئ في التثبّت من الوقائع."
        )
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
