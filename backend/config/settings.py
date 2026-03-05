"""
FuviAI Marketing Agent — Application Settings
Sử dụng Pydantic Settings để quản lý config từ .env
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ─── Core LLM ───────────────────────────────────────────
    anthropic_api_key: str = Field(..., description="Anthropic API Key")
    anthropic_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model ID"
    )

    # ─── Database ───────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://fuviai:password@localhost:5432/marketing_agent"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ─── Vector DB ──────────────────────────────────────────
    chroma_persist_dir: str = Field(default="./data/chroma")
    chroma_collection: str = Field(default="fuviai_knowledge")

    # ─── Social Platforms ───────────────────────────────────
    zalo_oa_access_token: str = Field(default="")
    zalo_oa_secret: str = Field(default="")
    facebook_access_token: str = Field(default="")
    facebook_page_id: str = Field(default="")
    tiktok_access_token: str = Field(default="")
    tiktok_app_id: str = Field(default="")
    shopee_partner_id: str = Field(default="")
    shopee_partner_key: str = Field(default="")
    google_ads_developer_token: str = Field(default="")

    # ─── App ────────────────────────────────────────────────
    app_env: str = Field(default="development")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")
    allowed_origins: str = Field(
        default="http://localhost:3000,https://marketing.fuviai.com"
    )
    secret_key: str = Field(default="change-this-in-production")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
