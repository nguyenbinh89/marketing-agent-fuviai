"""
FuviAI Marketing Agent — TikTok Ads Tool
TikTok for Business / Ads Manager API v1.3
Docs: https://business-api.tiktok.com/portal/docs

Auth: Access-Token header (lấy từ TikTok for Business → Assets → App Management)
Advertiser: advertiser_id (tìm trong TikTok Ads Manager URL)
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx
from loguru import logger

from backend.config.settings import get_settings


TIKTOK_ADS_BASE = "https://business-api.tiktok.com/open_api/v1.3"

# Benchmark ngành VN 2026
INDUSTRY_BENCHMARKS: dict[str, dict[str, float]] = {
    "fmcg":       {"cpc": 1800, "cpm": 35000, "ctr": 2.0, "roas": 3.2, "vtr": 15.0},
    "fb":         {"cpc": 2200, "cpm": 42000, "ctr": 2.5, "roas": 3.8, "vtr": 18.0},
    "realestate": {"cpc": 9000, "cpm": 65000, "ctr": 1.0, "roas": 7.0, "vtr": 10.0},
    "ecommerce":  {"cpc": 1400, "cpm": 28000, "ctr": 3.5, "roas": 5.0, "vtr": 20.0},
    "saas":       {"cpc": 6000, "cpm": 55000, "ctr": 1.4, "roas": 3.8, "vtr": 12.0},
    "education":  {"cpc": 3500, "cpm": 40000, "ctr": 1.8, "roas": 3.0, "vtr": 16.0},
}

# TikTok campaign objective codes
OBJECTIVES = {
    "REACH": "Tiếp cận",
    "VIDEO_VIEWS": "Lượt xem video",
    "TRAFFIC": "Lưu lượng truy cập",
    "APP_PROMOTION": "Quảng bá ứng dụng",
    "LEAD_GENERATION": "Thu thập khách hàng tiềm năng",
    "CONVERSIONS": "Chuyển đổi",
    "CATALOG_SALES": "Bán hàng qua catalog",
    "SHOP_PURCHASES": "Mua hàng TikTok Shop",
}


class TikTokAdsTool:
    """
    Wrapper cho TikTok Ads Manager API v1.3.

    Cần trong .env:
        TIKTOK_ADS_ACCESS_TOKEN  — Access token từ TikTok for Business App
        TIKTOK_ADS_ADVERTISER_ID — Advertiser ID (số trong URL Ads Manager)

    Usage:
        tool = TikTokAdsTool()
        campaigns = tool.get_campaigns()
        insights  = tool.get_account_insights(days_back=30)
        report    = tool.get_campaign_report(days_back=7)
    """

    def __init__(self):
        settings = get_settings()
        self._token = settings.tiktok_ads_access_token
        self._advertiser_id = settings.tiktok_ads_advertiser_id
        self._client = httpx.Client(timeout=30)

    @property
    def is_configured(self) -> bool:
        return bool(self._token and self._advertiser_id)

    def _not_configured(self) -> dict[str, Any]:
        return {
            "error": "TikTok Ads chưa được cấu hình. "
                     "Kiểm tra TIKTOK_ADS_ACCESS_TOKEN và TIKTOK_ADS_ADVERTISER_ID trong .env"
        }

    def _headers(self) -> dict[str, str]:
        return {
            "Access-Token": self._token,
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.is_configured:
            return self._not_configured()
        try:
            resp = self._client.get(
                f"{TIKTOK_ADS_BASE}/{path}",
                headers=self._headers(),
                params={"advertiser_id": self._advertiser_id, **(params or {})},
            )
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error(f"TikTok Ads GET error: {data.get('message', data)}")
            return data
        except Exception as e:
            logger.error(f"TikTok Ads GET exception: {e}")
            return {"error": str(e)}

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured:
            return self._not_configured()
        try:
            resp = self._client.post(
                f"{TIKTOK_ADS_BASE}/{path}",
                headers=self._headers(),
                json={"advertiser_id": self._advertiser_id, **payload},
            )
            data = resp.json()
            if data.get("code", 0) != 0:
                logger.error(f"TikTok Ads POST error: {data.get('message', data)}")
            return data
        except Exception as e:
            logger.error(f"TikTok Ads POST exception: {e}")
            return {"error": str(e)}

    def _date_range(self, days_back: int) -> tuple[str, str]:
        today = date.today()
        since = today - timedelta(days=days_back)
        return since.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    # ─── Campaigns ───────────────────────────────────────────────────────────

    def get_campaigns(
        self,
        status: str = "CAMPAIGN_STATUS_ENABLE",
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách campaigns.

        status:
            CAMPAIGN_STATUS_ENABLE   — đang chạy
            CAMPAIGN_STATUS_DISABLE  — tạm dừng
            CAMPAIGN_STATUS_DELETE   — đã xoá
            CAMPAIGN_STATUS_ALL      — tất cả
        """
        result = self._get(
            "campaign/get/",
            {
                "primary_status": status,
                "fields": '["campaign_id","campaign_name","status","objective_type","budget","budget_mode","create_time","modify_time"]',
                "page_size": page_size,
            },
        )
        campaigns = []
        for c in result.get("data", {}).get("list", []):
            budget = float(c.get("budget", 0))
            campaigns.append({
                "id": c.get("campaign_id", ""),
                "name": c.get("campaign_name", ""),
                "status": c.get("status", ""),
                "objective": c.get("objective_type", ""),
                "objective_label": OBJECTIVES.get(c.get("objective_type", ""), c.get("objective_type", "")),
                "budget_vnd": budget,
                "budget_mode": c.get("budget_mode", ""),
                "create_time": c.get("create_time", ""),
            })
        logger.debug(f"TikTok Ads campaigns | status={status} | count={len(campaigns)}")
        return campaigns

    def update_campaign_status(self, campaign_id: str, status: str) -> dict[str, Any]:
        """
        Bật/tắt campaign.
        status: ENABLE | DISABLE
        """
        result = self._post(
            "campaign/update/",
            {
                "campaign_id": campaign_id,
                "operation_status": status,
            },
        )
        logger.info(f"TikTok Ads campaign status updated | id={campaign_id} | status={status}")
        return result

    def update_campaign_budget(self, campaign_id: str, budget: float) -> dict[str, Any]:
        """Cập nhật ngân sách campaign (VNĐ)."""
        result = self._post(
            "campaign/update/",
            {
                "campaign_id": campaign_id,
                "budget": budget,
            },
        )
        logger.info(f"TikTok Ads campaign budget updated | id={campaign_id} | budget={budget:,.0f}đ")
        return result

    # ─── Ad Groups ───────────────────────────────────────────────────────────

    def get_adgroups(
        self,
        campaign_id: str | None = None,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        """Lấy danh sách Ad Groups (targeting, placements, budget)."""
        params: dict[str, Any] = {
            "fields": '["adgroup_id","adgroup_name","campaign_id","status","budget","bid_price","placement_type","age_groups","gender","location_ids"]',
            "page_size": page_size,
        }
        if campaign_id:
            params["campaign_ids"] = f'["{campaign_id}"]'

        result = self._get("adgroup/get/", params)
        adgroups = []
        for g in result.get("data", {}).get("list", []):
            adgroups.append({
                "id": g.get("adgroup_id", ""),
                "name": g.get("adgroup_name", ""),
                "campaign_id": g.get("campaign_id", ""),
                "status": g.get("status", ""),
                "budget_vnd": float(g.get("budget", 0)),
                "bid_price_vnd": float(g.get("bid_price", 0)),
                "placement_type": g.get("placement_type", ""),
                "age_groups": g.get("age_groups", []),
                "gender": g.get("gender", ""),
            })
        logger.debug(f"TikTok Ads adgroups | count={len(adgroups)}")
        return adgroups

    # ─── Ads ─────────────────────────────────────────────────────────────────

    def get_ads(
        self,
        campaign_id: str | None = None,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        """Lấy danh sách Ads (creative, video, status)."""
        params: dict[str, Any] = {
            "fields": '["ad_id","ad_name","adgroup_id","campaign_id","status","ad_text","call_to_action","video_id","create_time"]',
            "page_size": page_size,
        }
        if campaign_id:
            params["campaign_ids"] = f'["{campaign_id}"]'

        result = self._get("ad/get/", params)
        ads = []
        for a in result.get("data", {}).get("list", []):
            ads.append({
                "id": a.get("ad_id", ""),
                "name": a.get("ad_name", ""),
                "adgroup_id": a.get("adgroup_id", ""),
                "campaign_id": a.get("campaign_id", ""),
                "status": a.get("status", ""),
                "ad_text": a.get("ad_text", "")[:150],
                "cta": a.get("call_to_action", ""),
                "video_id": a.get("video_id", ""),
            })
        logger.debug(f"TikTok Ads ads | count={len(ads)}")
        return ads

    # ─── Integrated Report ───────────────────────────────────────────────────

    def _report(
        self,
        data_level: str,
        dimensions: list[str],
        metrics: list[str],
        days_back: int,
        filters: list[dict] | None = None,
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        """Wrapper cho /report/integrated/get/ endpoint."""
        start_date, end_date = self._date_range(days_back)
        payload: dict[str, Any] = {
            "report_type": "BASIC",
            "data_level": data_level,
            "dimensions": dimensions,
            "metrics": metrics,
            "start_date": start_date,
            "end_date": end_date,
            "page_size": page_size,
        }
        if filters:
            payload["filters"] = filters

        result = self._post("report/integrated/get/", payload)
        return result.get("data", {}).get("list", [])

    def get_account_insights(self, days_back: int = 30) -> dict[str, Any]:
        """
        Tóm tắt toàn account: spend, impressions, clicks, CTR, CPM, conversions, ROAS.
        """
        rows = self._report(
            data_level="AUCTION_ADVERTISER",
            dimensions=["stat_time_day"],
            metrics=[
                "spend", "impressions", "clicks", "ctr", "cpm", "cpc",
                "reach", "frequency", "conversion", "real_time_conversion",
                "video_play_actions", "video_watched_2s", "video_watched_6s",
                "average_video_play", "video_views_p100",
            ],
            days_back=days_back,
        )

        totals: dict[str, float] = {}
        for row in rows:
            m = row.get("metrics", {})
            for key in ["spend", "impressions", "clicks", "reach", "conversion", "video_play_actions"]:
                totals[key] = totals.get(key, 0) + float(m.get(key, 0))

        spend = totals.get("spend", 0)
        impressions = totals.get("impressions", 0)
        clicks = totals.get("clicks", 0)

        summary = {
            "days": days_back,
            "spend_vnd": round(spend, 0),
            "impressions": int(impressions),
            "clicks": int(clicks),
            "reach": int(totals.get("reach", 0)),
            "ctr": round(clicks / impressions * 100, 2) if impressions > 0 else 0,
            "cpc_vnd": round(spend / clicks, 0) if clicks > 0 else 0,
            "cpm_vnd": round(spend / impressions * 1000, 0) if impressions > 0 else 0,
            "conversions": round(totals.get("conversion", 0), 0),
            "video_plays": int(totals.get("video_play_actions", 0)),
        }
        logger.info(f"TikTok Ads account insights | days={days_back} | spend={spend:,.0f}đ")
        return summary

    def get_campaign_report(self, days_back: int = 7) -> list[dict[str, Any]]:
        """Performance theo campaign: spend, CTR, CPC, CPM, conversions."""
        rows = self._report(
            data_level="AUCTION_CAMPAIGN",
            dimensions=["campaign_id"],
            metrics=["spend", "impressions", "clicks", "ctr", "cpc", "cpm", "conversion", "video_play_actions"],
            days_back=days_back,
        )
        result = []
        for row in rows:
            m = row.get("metrics", {})
            d = row.get("dimensions", {})
            spend = float(m.get("spend", 0))
            result.append({
                "campaign_id": d.get("campaign_id", ""),
                "spend_vnd": round(spend, 0),
                "impressions": int(m.get("impressions", 0)),
                "clicks": int(m.get("clicks", 0)),
                "ctr": round(float(m.get("ctr", 0)), 2),
                "cpc_vnd": round(float(m.get("cpc", 0)), 0),
                "cpm_vnd": round(float(m.get("cpm", 0)), 0),
                "conversions": round(float(m.get("conversion", 0)), 0),
                "video_plays": int(m.get("video_play_actions", 0)),
            })
        result.sort(key=lambda x: x["spend_vnd"], reverse=True)
        logger.debug(f"TikTok Ads campaign report | days={days_back} | rows={len(result)}")
        return result

    def get_adgroup_report(self, days_back: int = 7) -> list[dict[str, Any]]:
        """Performance theo Ad Group."""
        rows = self._report(
            data_level="AUCTION_ADGROUP",
            dimensions=["adgroup_id"],
            metrics=["spend", "impressions", "clicks", "ctr", "cpc", "cpm", "conversion"],
            days_back=days_back,
        )
        result = []
        for row in rows:
            m = row.get("metrics", {})
            d = row.get("dimensions", {})
            result.append({
                "adgroup_id": d.get("adgroup_id", ""),
                "spend_vnd": round(float(m.get("spend", 0)), 0),
                "impressions": int(m.get("impressions", 0)),
                "clicks": int(m.get("clicks", 0)),
                "ctr": round(float(m.get("ctr", 0)), 2),
                "cpc_vnd": round(float(m.get("cpc", 0)), 0),
                "conversions": round(float(m.get("conversion", 0)), 0),
            })
        result.sort(key=lambda x: x["spend_vnd"], reverse=True)
        return result

    def get_ad_report(self, days_back: int = 7) -> list[dict[str, Any]]:
        """Performance theo Ad (video creative level): play rate, VTR, CTR."""
        rows = self._report(
            data_level="AUCTION_AD",
            dimensions=["ad_id"],
            metrics=[
                "spend", "impressions", "clicks", "ctr", "cpc",
                "video_play_actions", "video_watched_2s", "video_watched_6s",
                "video_views_p100", "average_video_play_per_user",
            ],
            days_back=days_back,
        )
        result = []
        for row in rows:
            m = row.get("metrics", {})
            d = row.get("dimensions", {})
            impressions = int(m.get("impressions", 0))
            plays = int(m.get("video_play_actions", 0))
            watched_6s = int(m.get("video_watched_6s", 0))
            result.append({
                "ad_id": d.get("ad_id", ""),
                "spend_vnd": round(float(m.get("spend", 0)), 0),
                "impressions": impressions,
                "clicks": int(m.get("clicks", 0)),
                "ctr": round(float(m.get("ctr", 0)), 2),
                "cpc_vnd": round(float(m.get("cpc", 0)), 0),
                "video_plays": plays,
                "watched_6s": watched_6s,
                "watched_p100": int(m.get("video_views_p100", 0)),
                "vtr_6s": round(watched_6s / plays * 100, 1) if plays > 0 else 0,
                "avg_play_time": round(float(m.get("average_video_play_per_user", 0)), 1),
            })
        result.sort(key=lambda x: x["spend_vnd"], reverse=True)
        logger.debug(f"TikTok Ads ad report | days={days_back} | rows={len(result)}")
        return result

    def get_audience_report(
        self,
        days_back: int = 30,
        breakdown: str = "age",
    ) -> list[dict[str, Any]]:
        """
        Audience breakdown report.

        breakdown: age | gender | country_code | platform | device
        """
        dim_map = {
            "age": "age",
            "gender": "gender",
            "country": "country_code",
            "platform": "platform",
            "device": "device",
        }
        dim = dim_map.get(breakdown, "age")
        rows = self._report(
            data_level="AUCTION_ADVERTISER",
            dimensions=[dim],
            metrics=["spend", "impressions", "clicks", "ctr", "reach"],
            days_back=days_back,
        )
        result = []
        for row in rows:
            m = row.get("metrics", {})
            d = row.get("dimensions", {})
            result.append({
                breakdown: d.get(dim, "—"),
                "spend_vnd": round(float(m.get("spend", 0)), 0),
                "impressions": int(m.get("impressions", 0)),
                "clicks": int(m.get("clicks", 0)),
                "ctr": round(float(m.get("ctr", 0)), 2),
                "reach": int(m.get("reach", 0)),
            })
        result.sort(key=lambda x: x["impressions"], reverse=True)
        logger.debug(f"TikTok Ads audience | breakdown={breakdown} | rows={len(result)}")
        return result

    # ─── Benchmark (offline) ─────────────────────────────────────────────────

    def get_industry_benchmark(self, industry: str = "saas") -> dict[str, Any]:
        """Benchmark TikTok Ads ngành VN 2026 (không cần API call)."""
        benchmark = INDUSTRY_BENCHMARKS.get(industry.lower(), INDUSTRY_BENCHMARKS["saas"])
        return {
            "industry": industry,
            "source": "FuviAI benchmark TikTok Ads VN 2026",
            **benchmark,
            "note": "VTR = Video Through Rate (% xem hết 6s). Dùng get_account_insights() để so sánh.",
        }
