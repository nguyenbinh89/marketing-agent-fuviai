"""
FuviAI Marketing Agent — /api/ads/unified/* routes
Unified Ads Dashboard — tổng hợp dữ liệu từ Google Ads, Facebook Ads, TikTok Ads
"""

from __future__ import annotations

import concurrent.futures
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from backend.tools.google_ads_tool import GoogleAdsTool
from backend.tools.facebook_ads_tool import FacebookAdsTool
from backend.tools.tiktok_ads_tool import TikTokAdsTool

router = APIRouter()

_gads: GoogleAdsTool | None = None
_fads: FacebookAdsTool | None = None
_tads: TikTokAdsTool | None = None


def get_tools() -> tuple[GoogleAdsTool, FacebookAdsTool, TikTokAdsTool]:
    global _gads, _fads, _tads
    if _gads is None:
        _gads = GoogleAdsTool()
    if _fads is None:
        _fads = FacebookAdsTool()
    if _tads is None:
        _tads = TikTokAdsTool()
    return _gads, _fads, _tads


def _safe(fn, *args, **kwargs) -> dict[str, Any]:
    """Gọi tool method, trả về error dict nếu thất bại."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Unified ads tool error: {e}")
        return {"error": str(e)}


@router.get("/summary")
async def get_unified_summary(days: int = Query(default=30, ge=1, le=90)):
    """
    Tóm tắt tổng hợp 3 platform: Google Ads, Facebook Ads, TikTok Ads.
    Gọi song song (concurrent.futures), tổng hợp thành 1 response.
    """
    gads, fads, tads = get_tools()

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_google   = ex.submit(_safe, gads.get_account_summary, days)
        f_facebook = ex.submit(_safe, fads.get_account_insights, days)
        f_tiktok   = ex.submit(_safe, tads.get_account_insights, days)

    g = f_google.result()
    f = f_facebook.result()
    t = f_tiktok.result()

    platforms = []

    # Google Ads
    if "error" not in g and "total_cost_vnd" in g:
        platforms.append({
            "platform": "Google Ads",
            "key": "google",
            "configured": True,
            "spend_vnd": float(g.get("total_cost_vnd", 0)),
            "clicks": int(g.get("total_clicks", 0)),
            "impressions": int(g.get("total_impressions", 0)),
            "conversions": float(g.get("total_conversions", 0)),
            "ctr": float(g.get("avg_ctr", 0)),
            "cpc_vnd": float(g.get("avg_cpc_vnd", 0)),
            "roas": float(g.get("overall_roas", 0)),
            "color": "#4285F4",
        })
    else:
        platforms.append({"platform": "Google Ads", "key": "google", "configured": False, "error": g.get("error", "")})

    # Facebook Ads
    if "error" not in f and "spend_vnd" in f:
        platforms.append({
            "platform": "Facebook Ads",
            "key": "facebook",
            "configured": True,
            "spend_vnd": float(f.get("spend_vnd", 0)),
            "clicks": int(f.get("clicks", 0)),
            "impressions": int(f.get("impressions", 0)),
            "conversions": float(f.get("purchases", 0)),
            "ctr": float(f.get("ctr", 0)),
            "cpc_vnd": float(f.get("cpc_vnd", 0)),
            "roas": float(f.get("roas", 0)),
            "color": "#1877F2",
        })
    else:
        platforms.append({"platform": "Facebook Ads", "key": "facebook", "configured": False, "error": f.get("error", "")})

    # TikTok Ads
    if "error" not in t and "spend_vnd" in t:
        platforms.append({
            "platform": "TikTok Ads",
            "key": "tiktok",
            "configured": True,
            "spend_vnd": float(t.get("spend_vnd", 0)),
            "clicks": int(t.get("clicks", 0)),
            "impressions": int(t.get("impressions", 0)),
            "conversions": float(t.get("conversions", 0)),
            "ctr": float(t.get("ctr", 0)),
            "cpc_vnd": float(t.get("cpc_vnd", 0)),
            "roas": 0.0,  # TikTok needs separate conversion value tracking
            "color": "#010101",
        })
    else:
        platforms.append({"platform": "TikTok Ads", "key": "tiktok", "configured": False, "error": t.get("error", "")})

    # Totals (configured only)
    active = [p for p in platforms if p.get("configured")]
    total_spend = sum(p["spend_vnd"] for p in active)
    total_clicks = sum(p["clicks"] for p in active)
    total_impressions = sum(p["impressions"] for p in active)
    total_conversions = sum(p["conversions"] for p in active)
    blended_roas = round(
        sum(p["roas"] * p["spend_vnd"] for p in active if p["roas"] > 0) / total_spend, 2
    ) if total_spend > 0 else 0

    # Spend allocation %
    for p in platforms:
        if p.get("configured") and total_spend > 0:
            p["spend_pct"] = round(p["spend_vnd"] / total_spend * 100, 1)
        else:
            p["spend_pct"] = 0.0

    logger.info(f"Unified ads summary | days={days} | platforms={len(active)} | total_spend={total_spend:,.0f}đ")

    return {
        "days": days,
        "platforms": platforms,
        "totals": {
            "spend_vnd": round(total_spend, 0),
            "clicks": total_clicks,
            "impressions": total_impressions,
            "conversions": round(total_conversions, 1),
            "blended_roas": blended_roas,
            "avg_ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0,
            "avg_cpc_vnd": round(total_spend / total_clicks, 0) if total_clicks > 0 else 0,
        },
        "configured_count": len(active),
    }


@router.get("/benchmarks")
async def get_all_benchmarks(industry: str = Query(default="saas")):
    """
    Benchmark tất cả 3 platform theo ngành (offline).
    industry: fmcg | fb | realestate | ecommerce | saas | education
    """
    gads, fads, tads = get_tools()
    return {
        "industry": industry,
        "google":   gads.get_industry_benchmark(industry),
        "facebook": fads.get_industry_benchmark(industry),
        "tiktok":   tads.get_industry_benchmark(industry),
    }
