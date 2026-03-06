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
    instagram_access_token: str = Field(default="")
    instagram_business_id: str = Field(default="")
    shopee_partner_id: str = Field(default="")
    shopee_partner_key: str = Field(default="")
    shopee_access_token: str = Field(default="")
    shopee_shop_id: str = Field(default="")
    google_ads_developer_token: str = Field(default="")
    google_ads_client_id: str = Field(default="")
    google_ads_client_secret: str = Field(default="")
    google_ads_refresh_token: str = Field(default="")
    google_ads_customer_id: str = Field(default="")
    google_ads_login_customer_id: str = Field(default="")
    google_cse_api_key: str = Field(default="", description="Google Custom Search API Key")
    google_cse_id: str = Field(default="", description="Google Custom Search Engine ID")

    # ─── Email (SendGrid) ───────────────────────────────────
    sendgrid_api_key: str = Field(default="", description="SendGrid API Key")
    sendgrid_from_email: str = Field(default="noreply@fuviai.com", description="Sender email (phải verify domain)")
    sendgrid_from_name: str = Field(default="FuviAI Marketing", description="Sender display name")

    # ─── Monitoring ─────────────────────────────────────────
    sentry_dsn: str = Field(default="", description="Sentry DSN — để trống để tắt")
    sentry_traces_sample_rate: float = Field(default=0.1, description="0.0-1.0 — tỷ lệ trace performance")

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
