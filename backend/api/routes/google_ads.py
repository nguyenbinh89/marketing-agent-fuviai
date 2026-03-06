"""
FuviAI Marketing Agent — /api/ads/google/* routes
Google Ads API v18: campaigns, performance, keywords, keyword ideas, benchmarks
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from backend.tools.google_ads_tool import GoogleAdsTool

router = APIRouter()

_gads = None


def get_gads() -> GoogleAdsTool:
    global _gads
    if _gads is None:
        _gads = GoogleAdsTool()
    return _gads


# ─── Request Models ──────────────────────────────────────────────────────────

class UpdateBudgetRequest(BaseModel):
    campaign_budget_id: str
    daily_budget_vnd: float = Field(..., gt=0, description="Ngân sách ngày (VNĐ)")


class CampaignStatusRequest(BaseModel):
    campaign_id: str
    status: str = Field(..., pattern="^(ENABLED|PAUSED)$")


class KeywordIdeasRequest(BaseModel):
    seed_keywords: list[str] = Field(..., min_length=1, max_length=10)
    language_id: str = "1040"   # Vietnamese


# ─── Campaign Endpoints ───────────────────────────────────────────────────────

@router.get("/campaigns")
async def get_campaigns(status: str = Query(default="ENABLED")):
    """
    Danh sách Google Ads campaigns.
    status: ENABLED | PAUSED | REMOVED
    """
    valid = ("ENABLED", "PAUSED", "REMOVED")
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"status phải là: {', '.join(valid)}")
    try:
        campaigns = get_gads().get_campaigns(status=status)
        return {"status": status, "count": len(campaigns), "campaigns": campaigns}
    except Exception as e:
        logger.error(f"Google Ads campaigns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/campaigns/budget")
async def update_budget(request: UpdateBudgetRequest):
    """Cập nhật ngân sách ngày của campaign (VNĐ)."""
    try:
        result = get_gads().update_campaign_budget(
            campaign_budget_id=request.campaign_budget_id,
            daily_budget_vnd=request.daily_budget_vnd,
        )
        return {"updated": True, "daily_budget_vnd": request.daily_budget_vnd, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/campaigns/status")
async def update_campaign_status(request: CampaignStatusRequest):
    """Bật/tắt campaign (ENABLED / PAUSED)."""
    try:
        if request.status == "PAUSED":
            result = get_gads().pause_campaign(request.campaign_id)
        else:
            result = get_gads().enable_campaign(request.campaign_id)
        return {"campaign_id": request.campaign_id, "new_status": request.status, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Performance Reports ─────────────────────────────────────────────────────

@router.get("/performance/summary")
async def get_account_summary(days: int = Query(default=30, ge=1, le=90)):
    """
    Tóm tắt toàn account: total_cost, clicks, impressions, conversions, ROAS, top campaigns.
    """
    try:
        return get_gads().get_account_summary(days_back=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/campaigns")
async def get_campaign_performance(days: int = Query(default=7, ge=1, le=90)):
    """Performance theo campaign: impressions, clicks, CTR, CPC, cost, conversions, ROAS."""
    try:
        rows = get_gads().get_campaign_performance(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/keywords")
async def get_keyword_performance(
    days: int = Query(default=30, ge=1, le=90),
    min_clicks: int = Query(default=0, ge=0),
):
    """Performance theo từ khoá: quality score, CTR, CPC, conversions."""
    try:
        rows = get_gads().get_keyword_performance(days_back=days, min_clicks=min_clicks)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/search-terms")
async def get_search_terms(days: int = Query(default=30, ge=1, le=90)):
    """Search terms report — từ khoá thực tế người dùng tìm (top 50)."""
    try:
        rows = get_gads().get_search_terms_report(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/ads")
async def get_ad_performance(days: int = Query(default=7, ge=1, le=90)):
    """Performance theo từng ad: headlines, CTR, clicks, conversions."""
    try:
        rows = get_gads().get_ad_performance(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Keyword Ideas ────────────────────────────────────────────────────────────

@router.post("/keyword-ideas")
async def get_keyword_ideas(request: KeywordIdeasRequest):
    """
    Google Keyword Planner — gợi ý từ khoá mới, volume tìm kiếm, giá thầu.
    Cần Google Ads account được cấu hình.
    """
    if not request.seed_keywords:
        raise HTTPException(status_code=400, detail="Cần ít nhất 1 seed keyword")
    try:
        ideas = get_gads().get_keyword_ideas(
            seed_keywords=request.seed_keywords,
            language_id=request.language_id,
        )
        return {"seed_keywords": request.seed_keywords, "count": len(ideas), "ideas": ideas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Benchmark (always available — no API key needed) ─────────────────────────

@router.get("/benchmark")
async def get_industry_benchmark(industry: str = Query(default="saas")):
    """
    Benchmark ngành VN 2026 (offline — không cần Google Ads account).
    industry: fmcg | fb | realestate | ecommerce | saas | education
    """
    try:
        return get_gads().get_industry_benchmark(industry=industry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
