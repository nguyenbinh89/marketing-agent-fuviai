"""
FuviAI Marketing Agent — FastAPI Application
Entry point cho backend API
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config.settings import get_settings
from backend.api.routes import agents, content, research, analytics, automation, commerce
from backend.api.middleware import RateLimitMiddleware, RequestLoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(f"FuviAI Marketing Agent starting | env={settings.app_env} | version=1.0.0")
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

    # ─── Health & Meta ────────────────────────────────────────────────────────
    @app.get("/health", tags=["System"])
    async def health():
        return {
            "status": "ok",
            "service": "fuviai-marketing-agent",
            "version": "1.0.0",
            "agents": 12,
        }

    @app.get("/", tags=["System"])
    async def root():
        return {
            "name": "FuviAI Marketing Agent",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
