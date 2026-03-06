"""
FuviAI Marketing Agent — /api/ads/tiktok/* routes
TikTok Ads Manager API v1.3: campaigns, ad groups, ads, reports, audience breakdown, benchmark
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from backend.tools.tiktok_ads_tool import TikTokAdsTool

router = APIRouter()

_tads = None


def get_tads() -> TikTokAdsTool:
    global _tads
    if _tads is None:
        _tads = TikTokAdsTool()
    return _tads


# ─── Request Models ───────────────────────────────────────────────────────────

class CampaignStatusRequest(BaseModel):
    campaign_id: str
    status: str = Field(..., pattern="^(ENABLE|DISABLE)$")


class CampaignBudgetRequest(BaseModel):
    campaign_id: str
    budget_vnd: float = Field(..., gt=0, description="Ngân sách (VNĐ)")


# ─── Campaigns ────────────────────────────────────────────────────────────────

@router.get("/campaigns")
async def get_campaigns(status: str = Query(default="CAMPAIGN_STATUS_ENABLE")):
    """
    Danh sách TikTok Ads campaigns.
    status: CAMPAIGN_STATUS_ENABLE | CAMPAIGN_STATUS_DISABLE | CAMPAIGN_STATUS_ALL
    """
    valid = ("CAMPAIGN_STATUS_ENABLE", "CAMPAIGN_STATUS_DISABLE", "CAMPAIGN_STATUS_ALL", "CAMPAIGN_STATUS_DELETE")
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"status phải là: {', '.join(valid)}")
    try:
        campaigns = get_tads().get_campaigns(status=status)
        return {"status": status, "count": len(campaigns), "campaigns": campaigns}
    except Exception as e:
        logger.error(f"TikTok Ads campaigns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/campaigns/status")
async def update_campaign_status(request: CampaignStatusRequest):
    """Bật/tắt campaign (ENABLE / DISABLE)."""
    try:
        result = get_tads().update_campaign_status(request.campaign_id, request.status)
        return {"campaign_id": request.campaign_id, "new_status": request.status, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/campaigns/budget")
async def update_campaign_budget(request: CampaignBudgetRequest):
    """Cập nhật ngân sách campaign (VNĐ)."""
    try:
        result = get_tads().update_campaign_budget(request.campaign_id, request.budget_vnd)
        return {"campaign_id": request.campaign_id, "budget_vnd": request.budget_vnd, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Ad Groups ────────────────────────────────────────────────────────────────

@router.get("/adgroups")
async def get_adgroups(campaign_id: str | None = Query(default=None)):
    """Danh sách Ad Groups (targeting, placements, budget)."""
    try:
        adgroups = get_tads().get_adgroups(campaign_id=campaign_id)
        return {"count": len(adgroups), "adgroups": adgroups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Ads ──────────────────────────────────────────────────────────────────────

@router.get("/ads")
async def get_ads(campaign_id: str | None = Query(default=None)):
    """Danh sách Ads (creative, video, CTA)."""
    try:
        ads = get_tads().get_ads(campaign_id=campaign_id)
        return {"count": len(ads), "ads": ads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Reports ──────────────────────────────────────────────────────────────────

@router.get("/insights/account")
async def get_account_insights(days: int = Query(default=30, ge=1, le=90)):
    """Tóm tắt toàn account: spend, CTR, CPC, CPM, conversions, video plays."""
    try:
        return get_tads().get_account_insights(days_back=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/campaigns")
async def get_campaign_report(days: int = Query(default=7, ge=1, le=90)):
    """Performance theo campaign."""
    try:
        rows = get_tads().get_campaign_report(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/adgroups")
async def get_adgroup_report(days: int = Query(default=7, ge=1, le=90)):
    """Performance theo Ad Group."""
    try:
        rows = get_tads().get_adgroup_report(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/ads")
async def get_ad_report(days: int = Query(default=7, ge=1, le=90)):
    """Performance theo Ad: VTR, play rate, avg play time."""
    try:
        rows = get_tads().get_ad_report(days_back=days)
        return {"days": days, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights/audience")
async def get_audience_report(
    days: int = Query(default=30, ge=1, le=90),
    breakdown: str = Query(default="age"),
):
    """
    Audience breakdown.
    breakdown: age | gender | country | platform | device
    """
    allowed = {"age", "gender", "country", "platform", "device"}
    if breakdown not in allowed:
        raise HTTPException(status_code=400, detail=f"breakdown phải là: {', '.join(sorted(allowed))}")
    try:
        rows = get_tads().get_audience_report(days_back=days, breakdown=breakdown)
        return {"days": days, "breakdown": breakdown, "count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Benchmark ────────────────────────────────────────────────────────────────

@router.get("/benchmark")
async def get_benchmark(industry: str = Query(default="saas")):
    """
    Benchmark TikTok Ads ngành VN 2026 (offline).
    industry: fmcg | fb | realestate | ecommerce | saas | education
    """
    try:
        return get_tads().get_industry_benchmark(industry=industry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
