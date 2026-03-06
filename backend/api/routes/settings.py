"""
FuviAI Marketing Agent — /api/settings/* routes
Kiểm tra trạng thái tất cả integrations đã cấu hình
"""

from __future__ import annotations

from fastapi import APIRouter
from loguru import logger

from backend.config.settings import get_settings

router = APIRouter()


def _masked(value: str, show: int = 4) -> str:
    """Mask sensitive values — chỉ hiện ký tự đầu."""
    if not value:
        return ""
    if len(value) <= show:
        return "****"
    return value[:show] + "****"


def _ok(value: str) -> bool:
    return bool(value and value.strip())


@router.get("/integrations")
async def get_integrations():
    """
    Trả về trạng thái cấu hình của tất cả integrations.
    Không trả về giá trị thực của secret keys.
    """
    s = get_settings()

    # ─── Ping Redis & Postgres ─────────────────────────────────────────────
    redis_ok = False
    postgres_ok = False

    try:
        import redis as _redis
        r = _redis.from_url(s.redis_url, socket_connect_timeout=2)
        r.ping()
        redis_ok = True
    except Exception as e:
        logger.debug(f"Redis ping failed: {e}")

    try:
        import psycopg2
        conn = psycopg2.connect(s.database_url, connect_timeout=2)
        conn.close()
        postgres_ok = True
    except Exception as e:
        logger.debug(f"Postgres ping failed: {e}")

    groups = [
        {
            "group": "Core AI",
            "integrations": [
                {
                    "id": "anthropic",
                    "name": "Anthropic Claude",
                    "description": "LLM engine cho 12 AI Agents — bắt buộc",
                    "configured": _ok(s.anthropic_api_key),
                    "masked_value": _masked(s.anthropic_api_key, 7),
                    "env_vars": ["ANTHROPIC_API_KEY"],
                    "action_url": None,
                    "docs_url": "https://console.anthropic.com",
                    "required": True,
                },
            ],
        },
        {
            "group": "Infrastructure",
            "integrations": [
                {
                    "id": "postgres",
                    "name": "PostgreSQL",
                    "description": "Database chính — lưu customers, orders, email logs",
                    "configured": postgres_ok,
                    "masked_value": _masked(s.database_url, 10) if _ok(s.database_url) else "",
                    "env_vars": ["DATABASE_URL"],
                    "action_url": None,
                    "docs_url": None,
                    "required": True,
                },
                {
                    "id": "redis",
                    "name": "Redis",
                    "description": "Cache + Celery task queue cho background jobs",
                    "configured": redis_ok,
                    "masked_value": s.redis_url if _ok(s.redis_url) else "",
                    "env_vars": ["REDIS_URL"],
                    "action_url": None,
                    "docs_url": None,
                    "required": True,
                },
                {
                    "id": "sentry",
                    "name": "Sentry",
                    "description": "Error tracking + performance monitoring",
                    "configured": _ok(s.sentry_dsn),
                    "masked_value": _masked(s.sentry_dsn),
                    "env_vars": ["SENTRY_DSN"],
                    "action_url": None,
                    "docs_url": "https://sentry.io",
                    "required": False,
                },
            ],
        },
        {
            "group": "Quảng cáo",
            "integrations": [
                {
                    "id": "google_ads",
                    "name": "Google Ads",
                    "description": "Quản lý campaigns, keywords, performance Google Ads",
                    "configured": all([
                        _ok(s.google_ads_developer_token),
                        _ok(s.google_ads_client_id),
                        _ok(s.google_ads_customer_id),
                    ]),
                    "masked_value": _masked(s.google_ads_developer_token),
                    "env_vars": [
                        "GOOGLE_ADS_DEVELOPER_TOKEN",
                        "GOOGLE_ADS_CLIENT_ID",
                        "GOOGLE_ADS_CLIENT_SECRET",
                        "GOOGLE_ADS_REFRESH_TOKEN",
                        "GOOGLE_ADS_CUSTOMER_ID",
                    ],
                    "action_url": "/google-ads",
                    "docs_url": "https://developers.google.com/google-ads/api/docs/get-started/introduction",
                    "required": False,
                },
                {
                    "id": "facebook_ads",
                    "name": "Facebook Ads",
                    "description": "Facebook Marketing API — campaigns, insights, audience",
                    "configured": _ok(s.facebook_access_token) and _ok(s.facebook_ad_account_id),
                    "masked_value": _masked(s.facebook_access_token),
                    "env_vars": ["FACEBOOK_ACCESS_TOKEN", "FACEBOOK_AD_ACCOUNT_ID"],
                    "action_url": "/facebook-ads",
                    "docs_url": "https://developers.facebook.com/docs/marketing-apis",
                    "required": False,
                },
                {
                    "id": "tiktok_ads",
                    "name": "TikTok Ads",
                    "description": "TikTok Ads Manager API — campaigns, video metrics, VTR",
                    "configured": _ok(s.tiktok_ads_access_token) and _ok(s.tiktok_ads_advertiser_id),
                    "masked_value": _masked(s.tiktok_ads_access_token),
                    "env_vars": ["TIKTOK_ADS_ACCESS_TOKEN", "TIKTOK_ADS_ADVERTISER_ID"],
                    "action_url": "/tiktok-ads",
                    "docs_url": "https://business-api.tiktok.com/portal/docs",
                    "required": False,
                },
            ],
        },
        {
            "group": "Social & Messaging",
            "integrations": [
                {
                    "id": "zalo_oa",
                    "name": "Zalo Official Account",
                    "description": "Gửi tin nhắn, broadcast, quản lý followers Zalo OA",
                    "configured": _ok(s.zalo_oa_access_token),
                    "masked_value": _masked(s.zalo_oa_access_token),
                    "env_vars": ["ZALO_OA_ACCESS_TOKEN", "ZALO_OA_SECRET"],
                    "action_url": "/zalo-oa",
                    "docs_url": "https://developers.zalo.me/docs",
                    "required": False,
                },
                {
                    "id": "facebook_page",
                    "name": "Facebook Page",
                    "description": "Đăng bài, schedule, quản lý Facebook Page",
                    "configured": _ok(s.facebook_access_token) and _ok(s.facebook_page_id),
                    "masked_value": _masked(s.facebook_page_id, 6),
                    "env_vars": ["FACEBOOK_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"],
                    "action_url": "/social",
                    "docs_url": "https://developers.facebook.com/docs/pages",
                    "required": False,
                },
                {
                    "id": "instagram",
                    "name": "Instagram Business",
                    "description": "Đăng ảnh, reel, story — Instagram Graph API v21.0",
                    "configured": _ok(s.instagram_access_token) and _ok(s.instagram_business_id),
                    "masked_value": _masked(s.instagram_access_token),
                    "env_vars": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ID"],
                    "action_url": "/social",
                    "docs_url": "https://developers.facebook.com/docs/instagram-api",
                    "required": False,
                },
                {
                    "id": "tiktok_organic",
                    "name": "TikTok for Business (Organic)",
                    "description": "Đăng video TikTok — Content Posting API",
                    "configured": _ok(s.tiktok_access_token),
                    "masked_value": _masked(s.tiktok_access_token),
                    "env_vars": ["TIKTOK_ACCESS_TOKEN", "TIKTOK_APP_ID"],
                    "action_url": "/social",
                    "docs_url": "https://developers.tiktok.com",
                    "required": False,
                },
            ],
        },
        {
            "group": "Thương mại",
            "integrations": [
                {
                    "id": "shopee",
                    "name": "Shopee Open Platform",
                    "description": "Quản lý shop, sản phẩm, đơn hàng, voucher Shopee",
                    "configured": _ok(s.shopee_partner_id) and _ok(s.shopee_access_token),
                    "masked_value": _masked(s.shopee_access_token),
                    "env_vars": [
                        "SHOPEE_PARTNER_ID", "SHOPEE_PARTNER_KEY",
                        "SHOPEE_ACCESS_TOKEN", "SHOPEE_SHOP_ID",
                    ],
                    "action_url": "/shopee",
                    "docs_url": "https://open.shopee.com",
                    "required": False,
                },
                {
                    "id": "sendgrid",
                    "name": "SendGrid Email",
                    "description": "Email marketing, transactional, abandoned cart automation",
                    "configured": _ok(s.sendgrid_api_key),
                    "masked_value": _masked(s.sendgrid_api_key, 6),
                    "env_vars": ["SENDGRID_API_KEY", "SENDGRID_FROM_EMAIL"],
                    "action_url": "/customers",
                    "docs_url": "https://sendgrid.com/docs",
                    "required": False,
                },
            ],
        },
        {
            "group": "Search & Research",
            "integrations": [
                {
                    "id": "google_search",
                    "name": "Google Custom Search",
                    "description": "Research agent — tìm kiếm tin tức, thị trường VN",
                    "configured": _ok(s.google_cse_api_key) and _ok(s.google_cse_id),
                    "masked_value": _masked(s.google_cse_api_key),
                    "env_vars": ["GOOGLE_CSE_API_KEY", "GOOGLE_CSE_ID"],
                    "action_url": "/research",
                    "docs_url": "https://developers.google.com/custom-search",
                    "required": False,
                },
            ],
        },
    ]

    total = sum(len(g["integrations"]) for g in groups)
    configured = sum(
        1 for g in groups for i in g["integrations"] if i["configured"]
    )
    required_missing = sum(
        1 for g in groups for i in g["integrations"]
        if i["required"] and not i["configured"]
    )

    logger.info(f"Integration check: {configured}/{total} configured, {required_missing} required missing")

    return {
        "summary": {
            "total": total,
            "configured": configured,
            "not_configured": total - configured,
            "required_missing": required_missing,
        },
        "groups": groups,
        "model": s.anthropic_model,
        "env": s.app_env,
        "version": "1.0.0",
    }
