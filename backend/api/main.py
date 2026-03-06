"""
FuviAI Marketing Agent — FastAPI Application
Entry point cho backend API
"""

from contextlib import asynccontextmanager
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config.settings import get_settings
from backend.api.routes import agents, content, research, analytics, automation, commerce, customers, shopee, google_ads, facebook_ads, tiktok_ads, ads_unified, zalo_oa, notifications, reports
from backend.api.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from backend.monitoring import init_sentry, sentry_capture_exception

APP_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_sentry(settings)
    logger.info(f"FuviAI Marketing Agent starting | env={settings.app_env} | version=1.0.0")
    try:
        from backend.db.database import create_tables
        create_tables()
    except Exception as e:
        logger.warning(f"DB table creation skipped (no DB?): {e}")
    yield
    logger.info("FuviAI Marketing Agent shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="FuviAI Marketing Agent API",
        description=(
            "AI Marketing Agent cho doanh nghiệp Việt Nam — marketing.fuviai.com\n\n"
            "**12 AI Agents:** Content (M1), Research (M2), Campaign (M3), SEO (M4), "
            "Social (M5), Insight (M6), Listening (M7), Livestream (M8), AdBudget (M9), "
            "Competitor (M10), Personalize (M11), Compliance (M12) + LangGraph Orchestrator"
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ─── Middleware (order matters: outermost = last executed) ───────────────
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Routers ─────────────────────────────────────────────────────────────
    app.include_router(agents.router,     prefix="/api/agents",     tags=["Agents"])
    app.include_router(content.router,    prefix="/api/content",    tags=["Content"])
    app.include_router(research.router,   prefix="/api/research",   tags=["Research & SEO"])
    app.include_router(analytics.router,  prefix="/api/analytics",  tags=["Analytics"])
    app.include_router(automation.router, prefix="/api/automation", tags=["Automation"])
    app.include_router(commerce.router,   prefix="/api/commerce",   tags=["Commerce & AI Orchestrator"])
    app.include_router(customers.router,  prefix="/api/customers",  tags=["Customers & Email Logs"])
    app.include_router(shopee.router,     prefix="/api/shopee",     tags=["Shopee E-commerce"])
    app.include_router(google_ads.router,   prefix="/api/ads/google",   tags=["Google Ads"])
    app.include_router(facebook_ads.router, prefix="/api/ads/facebook", tags=["Facebook Ads"])
    app.include_router(tiktok_ads.router,   prefix="/api/ads/tiktok",   tags=["TikTok Ads"])
    app.include_router(ads_unified.router,  prefix="/api/ads/unified",  tags=["Unified Ads"])
    app.include_router(zalo_oa.router,        prefix="/api/zalo",          tags=["Zalo OA"])
    app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
    app.include_router(reports.router,       prefix="/api/reports",       tags=["Reports"])

    # ─── Health & Meta ────────────────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health():
        settings = get_settings()
        checks: dict[str, str] = {}

        # Ping Redis
        try:
            import redis as _redis
            r = _redis.from_url(settings.redis_url, socket_connect_timeout=2)
            r.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"

        # Ping PostgreSQL
        try:
            import psycopg2
            conn = psycopg2.connect(settings.database_url, connect_timeout=2)
            conn.close()
            checks["postgres"] = "ok"
        except Exception as e:
            checks["postgres"] = f"error: {e}"

        overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
        return {
            "status": overall,
            "service": "fuviai-marketing-agent",
            "version": "1.0.0",
            "agents": 12,
            "uptime_seconds": round(time.time() - APP_START_TIME),
            "checks": checks,
        }

    @app.get("/health/live", tags=["System"])
    async def liveness():
        """Kubernetes/Docker liveness probe — chỉ check process còn sống."""
        return {"status": "ok"}

    @app.get("/", tags=["System"])
    async def root():
        return {
            "name": "FuviAI Marketing Agent",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
