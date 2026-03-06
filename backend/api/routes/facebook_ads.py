"""
FuviAI Marketing Agent — /api/ads/facebook/* routes
Facebook Marketing API v21.0: campaigns, insights, ad sets, ads, audience breakdown, Ad Library
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from backend.tools.facebook_ads_tool import FacebookAdsTool

router = APIRouter()

_fads = None


def get_fads() -> FacebookAdsTool:
    global _fads
    if _fads is None:
        _fads = FacebookAdsTool()
    return _fads


# ─── Request Models ───────────────────────────────────────────────────────────

class CampaignStatusRequest(BaseModel):
    campaign_id: str
    status: str = Field(..., pattern="^(ACTIVE|PAUSED)$")


class CampaignBudgetRequest(BaseModel):
    campaign_id: str
    daily_budget_vnd: float | None = Field(default=None, gt=0)
    lifetime_budget_vnd: float | None = Field(default=None, gt=0)


# ─── Campaigns ────────────────────────────────────────────────────────────────

@router.get("/campaigns")
async def get_campaigns(status: str = Query(default="ACTIVE")):
    """
    Danh sách Facebook Ads campaigns.
    status: ACTIVE | PAUSED | ARCHIVED | DELETED
    """
    valid = ("ACTIVE", "PAUSED", "ARCHIVED", "DELETED")
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"status phải là: {', '.join(valid)}")
    try:
        campaigns = get_fads().get_campaigns(status=status)
        return {"status": status, "count": len(campaigns), "campaigns": campaigns}
    except Exception as e:
        logger.error(f"Facebook Ads campaigns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/campaigns/status")
async def update_campaign_status(request: CampaignStatusRequest):
    """Bật/tắt campaign (ACTIVE / PAUSED)."""
    try:
        result = get_fads().update_campaign_status(request.campaign_id, request.status)
        return {"campaign_id": request.campaign_id, "new_status": request.status, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/campaigns/budget")
async def update_campaign_budget(request: CampaignBudgetRequest):
    """Cập nhật ngân sách campaign (ngày hoặc lifetime, VNĐ)."""
    if request.daily_budget_vnd is None and request.lifetime_budget_vnd is None:
        raise HTTPException(status_code=400, detail="Cần truyền daily_budget_vnd hoặc lifetime_budget_vnd")
    try:
        result = get_fads().update_campaign_budget(
            campaign_id=request.campaign_id,
            daily_budget_vnd=request.daily_budget_vnd,
            lifetime_budget_vnd=request.lifetime_budget_vnd,
        )
        return {"updated": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Ad Sets ──────────────────────────────────────────────────────────────────

@router.get("/adsets")
async def get_adsets(campaign_id: str | None = Query(default=None)):
    """Danh sách Ad Sets (của toàn account hoặc campaign cụ thể)."""
    try:
        adsets = get_fads().get_adsets(campaign_id=campaign_id)
        return {"count": len(adsets), "adsets": adsets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Insights / Performance ───────────────────────────────────────────────────

@router.get("/insights/account")
async def get_account_insights(days: int = Query(default=30, ge=1, le=90)):
    """
    Tóm tắt toàn account: spend, impressions, clicks, CTR, CPC, CPM, ROAS.
    """
    try:
        return get_fads().get_account_insights(days_back=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/campaigns")
async def get_campaign_insights(days: int = Query(default=7, ge=1, le=90)):
    """Performance theo campaign — spend, CTR, CPC, ROAS."""
    try:
        rows = get_fads().get_campaign_insights(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/adsets")
async def get_adset_insights(days: int = Query(default=7, ge=1, le=90)):
    """Performance theo Ad Set."""
    try:
        rows = get_fads().get_adset_insights(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/ads")
async def get_ad_insights(days: int = Query(default=7, ge=1, le=90)):
    """Performance theo từng Ad (creative level)."""
    try:
        rows = get_fads().get_ad_insights(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/delivery")
async def get_delivery_insights(
    days: int = Query(default=30, ge=1, le=90),
    breakdown: str = Query(default="age,gender"),
):
    """
    Breakdown audience: age,gender | country | publisher_platform | device_platform
    """
    allowed_breakdowns = {"age,gender", "country", "publisher_platform", "device_platform"}
    if breakdown not in allowed_breakdowns:
        raise HTTPException(
            status_code=400,
            detail=f"breakdown phải là: {', '.join(sorted(allowed_breakdowns))}"
        )
    try:
        rows = get_fads().get_delivery_insights(days_back=days, breakdown=breakdown)
        return {"days": days, "breakdown": breakdown, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Ad Library ───────────────────────────────────────────────────────────────

@router.get("/ad-library")
async def search_ad_library(
    q: str = Query(..., min_length=2, description="Từ khoá tìm ads đối thủ"),
    country: str = Query(default="VN"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Facebook Ad Library — research ads đối thủ (không cần Ad Account)."""
    try:
        ads = get_fads().search_ads_library(search_terms=q, country=country, limit=limit)
        return {"query": q, "country": country, "count": len(ads), "ads": ads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Benchmark ────────────────────────────────────────────────────────────────

@router.get("/benchmark")
async def get_benchmark(industry: str = Query(default="saas")):
    """
    Benchmark Facebook Ads ngành VN 2026 (offline — không cần token).
    industry: fmcg | fb | realestate | ecommerce | saas | education
    """
    try:
        return get_fads().get_industry_benchmark(industry=industry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
