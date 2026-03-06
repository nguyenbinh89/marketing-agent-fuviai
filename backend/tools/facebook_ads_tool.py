"""
FuviAI Marketing Agent — Facebook Ads Tool
Facebook Marketing API v21.0 — campaign management, performance reporting, audience insights
Docs: https://developers.facebook.com/docs/marketing-apis

Auth: User/System Access Token (dùng chung FACEBOOK_ACCESS_TOKEN)
Ad Account: act_{FACEBOOK_AD_ACCOUNT_ID}
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import httpx
from loguru import logger

from backend.config.settings import get_settings


GRAPH_API_BASE = "https://graph.facebook.com/v21.0"

# Benchmark ngành VN 2026
INDUSTRY_BENCHMARKS: dict[str, dict[str, float]] = {
    "fmcg":       {"cpc": 2200,  "cpm": 40000, "ctr": 1.9, "roas": 3.5, "frequency": 2.5},
    "fb":         {"cpc": 2800,  "cpm": 50000, "ctr": 2.4, "roas": 4.0, "frequency": 3.0},
    "realestate": {"cpc": 12000, "cpm": 75000, "ctr": 0.9, "roas": 7.5, "frequency": 2.0},
    "ecommerce":  {"cpc": 1600,  "cpm": 30000, "ctr": 3.2, "roas": 5.5, "frequency": 3.5},
    "saas":       {"cpc": 7000,  "cpm": 65000, "ctr": 1.3, "roas": 4.0, "frequency": 2.2},
    "education":  {"cpc": 4000,  "cpm": 45000, "ctr": 1.6, "roas": 3.2, "frequency": 2.8},
}


class FacebookAdsTool:
    """
    Wrapper cho Facebook Marketing API v21.0.

    Cần trong .env:
        FACEBOOK_ACCESS_TOKEN   — User/System Access Token có quyền ads_read, ads_management
        FACEBOOK_AD_ACCOUNT_ID  — Ad Account ID (dạng act_XXXXXXXXX hoặc chỉ số)

    Usage:
        tool = FacebookAdsTool()
        campaigns = tool.get_campaigns()
        insights  = tool.get_account_insights(days_back=30)
        keywords  = tool.get_campaign_insights(campaign_id="123", days_back=7)
    """

    def __init__(self):
        settings = get_settings()
        self._token = settings.facebook_access_token
        raw_id = settings.facebook_ad_account_id.strip()
        self._account_id = raw_id if raw_id.startswith("act_") else f"act_{raw_id}" if raw_id else ""
        self._client = httpx.Client(timeout=30)

    @property
    def is_configured(self) -> bool:
        return bool(self._token and self._account_id and self._account_id != "act_")

    def _not_configured(self) -> dict[str, Any]:
        return {
            "error": "Facebook Ads chưa được cấu hình. "
                     "Kiểm tra FACEBOOK_ACCESS_TOKEN và FACEBOOK_AD_ACCOUNT_ID trong .env"
        }

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.is_configured:
            return self._not_configured()
        url = f"{GRAPH_API_BASE}/{endpoint}"
        p = {"access_token": self._token, **(params or {})}
        try:
            resp = self._client.get(url, params=p)
            data = resp.json()
            if "error" in data:
                logger.error(f"Facebook Ads API error: {data['error'].get('message', data['error'])}")
            return data
        except Exception as e:
            logger.error(f"Facebook Ads GET exception: {e}")
            return {"error": str(e)}

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.is_configured:
            return self._not_configured()
        url = f"{GRAPH_API_BASE}/{endpoint}"
        try:
            resp = self._client.post(
                url,
                data={**payload, "access_token": self._token},
            )
            data = resp.json()
            if "error" in data:
                logger.error(f"Facebook Ads POST error: {data['error'].get('message', data['error'])}")
            return data
        except Exception as e:
            logger.error(f"Facebook Ads POST exception: {e}")
            return {"error": str(e)}

    def _date_range(self, days_back: int) -> dict[str, str]:
        today = date.today()
        since = today - timedelta(days=days_back)
        return {"since": since.isoformat(), "until": today.isoformat()}

    # ─── Campaigns ───────────────────────────────────────────────────────────

    def get_campaigns(
        self,
        status: str = "ACTIVE",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách campaigns.

        Args:
            status: ACTIVE | PAUSED | ARCHIVED | DELETED
        """
        result = self._get(
            f"{self._account_id}/campaigns",
            {
                "fields": "id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time,created_time",
                "effective_status": f'["{status}"]',
                "limit": limit,
            },
        )
        campaigns = []
        for c in result.get("data", []):
            daily_budget = int(c.get("daily_budget", 0))
            lifetime_budget = int(c.get("lifetime_budget", 0))
            campaigns.append({
                "id": c.get("id", ""),
                "name": c.get("name", ""),
                "status": c.get("status", ""),
                "objective": c.get("objective", ""),
                "daily_budget_vnd": daily_budget / 100 if daily_budget else 0,
                "lifetime_budget_vnd": lifetime_budget / 100 if lifetime_budget else 0,
                "start_time": c.get("start_time", ""),
                "stop_time": c.get("stop_time", ""),
                "created_time": c.get("created_time", ""),
            })
        logger.debug(f"Facebook Ads campaigns | status={status} | count={len(campaigns)}")
        return campaigns

    def update_campaign_status(self, campaign_id: str, status: str) -> dict[str, Any]:
        """Bật/tắt campaign (ACTIVE / PAUSED)."""
        result = self._post(campaign_id, {"status": status})
        logger.info(f"Facebook Ads campaign status updated | id={campaign_id} | status={status}")
        return result

    def update_campaign_budget(
        self,
        campaign_id: str,
        daily_budget_vnd: float | None = None,
        lifetime_budget_vnd: float | None = None,
    ) -> dict[str, Any]:
        """
        Cập nhật ngân sách campaign.
        Facebook dùng đơn vị cents (1 VNĐ = 100 units trong API).
        """
        payload: dict[str, Any] = {}
        if daily_budget_vnd is not None:
            payload["daily_budget"] = str(int(daily_budget_vnd * 100))
        if lifetime_budget_vnd is not None:
            payload["lifetime_budget"] = str(int(lifetime_budget_vnd * 100))
        if not payload:
            return {"error": "Cần truyền daily_budget_vnd hoặc lifetime_budget_vnd"}
        result = self._post(campaign_id, payload)
        logger.info(f"Facebook Ads budget updated | id={campaign_id}")
        return result

    # ─── Ad Sets ─────────────────────────────────────────────────────────────

    def get_adsets(self, campaign_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Lấy danh sách Ad Sets (của account hoặc campaign cụ thể)."""
        endpoint = f"{campaign_id}/adsets" if campaign_id else f"{self._account_id}/adsets"
        result = self._get(
            endpoint,
            {
                "fields": "id,name,status,daily_budget,lifetime_budget,targeting,optimization_goal,billing_event,bid_amount",
                "limit": limit,
            },
        )
        adsets = []
        for s in result.get("data", []):
            daily = int(s.get("daily_budget", 0))
            adsets.append({
                "id": s.get("id", ""),
                "name": s.get("name", ""),
                "status": s.get("status", ""),
                "daily_budget_vnd": daily / 100 if daily else 0,
                "optimization_goal": s.get("optimization_goal", ""),
                "billing_event": s.get("billing_event", ""),
            })
        logger.debug(f"Facebook Ads adsets | count={len(adsets)}")
        return adsets

    # ─── Insights / Performance ───────────────────────────────────────────────

    def get_account_insights(self, days_back: int = 30) -> dict[str, Any]:
        """
        Tóm tắt toàn account: spend, impressions, clicks, CTR, CPC, ROAS.
        """
        result = self._get(
            f"{self._account_id}/insights",
            {
                "fields": "spend,impressions,clicks,ctr,cpc,cpm,reach,frequency,actions,action_values",
                "time_range": str(self._date_range(days_back)).replace("'", '"'),
                "level": "account",
            },
        )
        data = result.get("data", [{}])
        if not data:
            return {"error": "Không có dữ liệu insights"}
        d = data[0]

        spend = float(d.get("spend", 0))
        actions = {a["action_type"]: float(a["value"]) for a in d.get("actions", [])}
        action_values = {a["action_type"]: float(a["value"]) for a in d.get("action_values", [])}
        purchases = actions.get("purchase", actions.get("offsite_conversion.fb_pixel_purchase", 0))
        purchase_value = action_values.get("purchase", action_values.get("offsite_conversion.fb_pixel_purchase", 0))

        summary = {
            "days": days_back,
            "spend_vnd": round(spend, 0),
            "impressions": int(d.get("impressions", 0)),
            "clicks": int(d.get("clicks", 0)),
            "reach": int(d.get("reach", 0)),
            "frequency": round(float(d.get("frequency", 0)), 2),
            "ctr": round(float(d.get("ctr", 0)), 2),
            "cpc_vnd": round(float(d.get("cpc", 0)), 0),
            "cpm_vnd": round(float(d.get("cpm", 0)), 0),
            "purchases": round(purchases, 0),
            "purchase_value_vnd": round(purchase_value, 0),
            "roas": round(purchase_value / spend, 2) if spend > 0 else 0,
        }
        logger.info(f"Facebook Ads account insights | days={days_back} | spend={spend:,.0f}đ")
        return summary

    def get_campaign_insights(
        self,
        days_back: int = 7,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Performance theo campaign: spend, CTR, CPC, CPM, ROAS."""
        result = self._get(
            f"{self._account_id}/insights",
            {
                "fields": "campaign_id,campaign_name,spend,impressions,clicks,ctr,cpc,cpm,reach,actions,action_values",
                "time_range": str(self._date_range(days_back)).replace("'", '"'),
                "level": "campaign",
                "limit": limit,
            },
        )
        rows = []
        for d in result.get("data", []):
            spend = float(d.get("spend", 0))
            actions = {a["action_type"]: float(a["value"]) for a in d.get("actions", [])}
            action_values = {a["action_type"]: float(a["value"]) for a in d.get("action_values", [])}
            purchase_value = action_values.get("purchase", action_values.get("offsite_conversion.fb_pixel_purchase", 0))
            rows.append({
                "campaign_id": d.get("campaign_id", ""),
                "campaign": d.get("campaign_name", ""),
                "spend_vnd": round(spend, 0),
                "impressions": int(d.get("impressions", 0)),
                "clicks": int(d.get("clicks", 0)),
                "reach": int(d.get("reach", 0)),
                "ctr": round(float(d.get("ctr", 0)), 2),
                "cpc_vnd": round(float(d.get("cpc", 0)), 0),
                "cpm_vnd": round(float(d.get("cpm", 0)), 0),
                "purchases": round(actions.get("purchase", 0), 0),
                "roas": round(purchase_value / spend, 2) if spend > 0 else 0,
            })
        rows.sort(key=lambda x: x["spend_vnd"], reverse=True)
        logger.debug(f"Facebook Ads campaign insights | days={days_back} | rows={len(rows)}")
        return rows

    def get_adset_insights(self, days_back: int = 7) -> list[dict[str, Any]]:
        """Performance theo Ad Set."""
        result = self._get(
            f"{self._account_id}/insights",
            {
                "fields": "adset_id,adset_name,campaign_name,spend,impressions,clicks,ctr,cpc,reach,actions",
                "time_range": str(self._date_range(days_back)).replace("'", '"'),
                "level": "adset",
                "limit": 50,
            },
        )
        rows = []
        for d in result.get("data", []):
            spend = float(d.get("spend", 0))
            actions = {a["action_type"]: float(a["value"]) for a in d.get("actions", [])}
            rows.append({
                "adset_id": d.get("adset_id", ""),
                "adset": d.get("adset_name", ""),
                "campaign": d.get("campaign_name", ""),
                "spend_vnd": round(spend, 0),
                "impressions": int(d.get("impressions", 0)),
                "clicks": int(d.get("clicks", 0)),
                "ctr": round(float(d.get("ctr", 0)), 2),
                "cpc_vnd": round(float(d.get("cpc", 0)), 0),
                "link_clicks": round(actions.get("link_click", 0), 0),
            })
        rows.sort(key=lambda x: x["spend_vnd"], reverse=True)
        logger.debug(f"Facebook Ads adset insights | days={days_back} | rows={len(rows)}")
        return rows

    def get_ad_insights(self, days_back: int = 7) -> list[dict[str, Any]]:
        """Performance theo từng Ad (creative level)."""
        result = self._get(
            f"{self._account_id}/insights",
            {
                "fields": "ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,ctr,cpc,reach,actions",
                "time_range": str(self._date_range(days_back)).replace("'", '"'),
                "level": "ad",
                "limit": 50,
            },
        )
        rows = []
        for d in result.get("data", []):
            spend = float(d.get("spend", 0))
            actions = {a["action_type"]: float(a["value"]) for a in d.get("actions", [])}
            rows.append({
                "ad_id": d.get("ad_id", ""),
                "ad": d.get("ad_name", ""),
                "adset": d.get("adset_name", ""),
                "campaign": d.get("campaign_name", ""),
                "spend_vnd": round(spend, 0),
                "impressions": int(d.get("impressions", 0)),
                "clicks": int(d.get("clicks", 0)),
                "ctr": round(float(d.get("ctr", 0)), 2),
                "cpc_vnd": round(float(d.get("cpc", 0)), 0),
                "link_clicks": round(actions.get("link_click", 0), 0),
            })
        rows.sort(key=lambda x: x["spend_vnd"], reverse=True)
        logger.debug(f"Facebook Ads ad insights | days={days_back} | rows={len(rows)}")
        return rows

    # ─── Audience / Delivery ──────────────────────────────────────────────────

    def get_delivery_insights(
        self,
        days_back: int = 30,
        breakdown: str = "age,gender",
    ) -> list[dict[str, Any]]:
        """
        Breakdown performance theo demographic.

        Args:
            breakdown: age,gender | country | publisher_platform | device_platform
        """
        result = self._get(
            f"{self._account_id}/insights",
            {
                "fields": "spend,impressions,clicks,ctr,reach,actions",
                "time_range": str(self._date_range(days_back)).replace("'", '"'),
                "breakdowns": breakdown,
                "level": "account",
                "limit": 100,
            },
        )
        rows = []
        for d in result.get("data", []):
            row = {
                "spend_vnd": round(float(d.get("spend", 0)), 0),
                "impressions": int(d.get("impressions", 0)),
                "clicks": int(d.get("clicks", 0)),
                "ctr": round(float(d.get("ctr", 0)), 2),
                "reach": int(d.get("reach", 0)),
            }
            # Add breakdown dimensions
            for dim in breakdown.split(","):
                row[dim.strip()] = d.get(dim.strip(), "")
            rows.append(row)
        rows.sort(key=lambda x: x["impressions"], reverse=True)
        logger.debug(f"Facebook Ads delivery breakdown | breakdown={breakdown} | rows={len(rows)}")
        return rows

    # ─── Ad Library (competitor research) ─────────────────────────────────────

    def search_ads_library(
        self,
        search_terms: str,
        country: str = "VN",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Tìm kiếm ads trong Facebook Ad Library — nghiên cứu đối thủ.
        Không cần Ad Account, chỉ cần access token.
        """
        if not self._token:
            return []
        result = self._get(
            "ads_archive",
            {
                "ad_reached_countries": country,
                "search_terms": search_terms,
                "ad_type": "ALL",
                "fields": "id,ad_creative_body,ad_creative_link_title,page_name,page_id,ad_snapshot_url,impressions",
                "limit": limit,
            },
        )
        ads = []
        for a in result.get("data", []):
            ads.append({
                "id": a.get("id", ""),
                "page_name": a.get("page_name", ""),
                "body": a.get("ad_creative_body", "")[:200] if a.get("ad_creative_body") else "",
                "link_title": a.get("ad_creative_link_title", ""),
                "snapshot_url": a.get("ad_snapshot_url", ""),
                "impressions": a.get("impressions", {}).get("lower_bound", "N/A"),
            })
        logger.info(f"Facebook Ad Library | query={search_terms} | found={len(ads)}")
        return ads

    # ─── Benchmark (offline) ─────────────────────────────────────────────────

    def get_industry_benchmark(self, industry: str = "saas") -> dict[str, Any]:
        """Benchmark Facebook Ads ngành VN 2026 (không cần API)."""
        benchmark = INDUSTRY_BENCHMARKS.get(industry.lower(), INDUSTRY_BENCHMARKS["saas"])
        return {
            "industry": industry,
            "source": "FuviAI benchmark Facebook Ads VN 2026",
            **benchmark,
            "note": "Dùng get_account_insights() để so sánh với data thực của account",
        }
