"""
FuviAI Marketing Agent — Google Ads Tool
Google Ads API v18 REST wrapper cho campaign management và performance reporting
Docs: https://developers.google.com/google-ads/api/docs/start

Auth: OAuth2 (refresh_token → access_token) + developer-token header
Query language: Google Ads Query Language (GAQL) cho reporting
"""

from __future__ import annotations

from typing import Any
from loguru import logger

import httpx

from backend.config.settings import get_settings


GOOGLE_ADS_API_BASE = "https://googleads.googleapis.com/v18"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Benchmark ngành VN 2026 — dùng khi không có data thực
INDUSTRY_BENCHMARKS: dict[str, dict[str, float]] = {
    "fmcg":       {"cpc": 2500,  "cpm": 45000, "ctr": 1.8, "roas": 3.5, "conversion_rate": 2.1},
    "fb":         {"cpc": 3000,  "cpm": 55000, "ctr": 2.2, "roas": 3.8, "conversion_rate": 2.5},
    "realestate": {"cpc": 15000, "cpm": 80000, "ctr": 0.8, "roas": 8.0, "conversion_rate": 0.5},
    "ecommerce":  {"cpc": 1800,  "cpm": 35000, "ctr": 3.0, "roas": 5.0, "conversion_rate": 3.5},
    "saas":       {"cpc": 8000,  "cpm": 70000, "ctr": 1.2, "roas": 4.2, "conversion_rate": 1.8},
    "education":  {"cpc": 4500,  "cpm": 50000, "ctr": 1.5, "roas": 3.0, "conversion_rate": 2.0},
}


class GoogleAdsTool:
    """
    Wrapper cho Google Ads API v18.

    Cần trong .env:
        GOOGLE_ADS_DEVELOPER_TOKEN   — Developer token từ Google Ads Manager
        GOOGLE_ADS_CLIENT_ID         — OAuth2 Client ID (Google Cloud Console)
        GOOGLE_ADS_CLIENT_SECRET     — OAuth2 Client Secret
        GOOGLE_ADS_REFRESH_TOKEN     — Refresh token (lấy qua OAuth2 flow)
        GOOGLE_ADS_CUSTOMER_ID       — Google Ads Customer ID (không có dấu gạch)
        GOOGLE_ADS_LOGIN_CUSTOMER_ID — Manager Account ID (nếu dùng MCC, để trống nếu không)

    Usage:
        tool = GoogleAdsTool()

        # Danh sách campaigns
        campaigns = tool.get_campaigns()

        # Báo cáo performance 7 ngày
        report = tool.get_campaign_performance(days_back=7)

        # Báo cáo từ khoá
        keywords = tool.get_keyword_performance(days_back=30)

        # Cập nhật ngân sách campaign
        tool.update_campaign_budget(campaign_id="123456789", daily_budget_micros=500_000_000)

        # Đề xuất từ khoá mới
        ideas = tool.get_keyword_ideas(seed_keywords=["marketing automation", "AI marketing"])
    """

    def __init__(self):
        settings = get_settings()
        self._developer_token = settings.google_ads_developer_token
        self._client_id = settings.google_ads_client_id
        self._client_secret = settings.google_ads_client_secret
        self._refresh_token = settings.google_ads_refresh_token
        self._customer_id = settings.google_ads_customer_id.replace("-", "")
        self._login_customer_id = settings.google_ads_login_customer_id.replace("-", "")
        self._access_token: str = ""
        self._client = httpx.Client(timeout=30)

    @property
    def is_configured(self) -> bool:
        return bool(
            self._developer_token
            and self._client_id
            and self._client_secret
            and self._refresh_token
            and self._customer_id
        )

    def _not_configured(self) -> dict[str, Any]:
        return {"error": "Google Ads chưa được cấu hình đầy đủ. Kiểm tra GOOGLE_ADS_* trong .env"}

    def _refresh_access_token(self) -> bool:
        """Lấy access token mới từ refresh token."""
        try:
            resp = self._client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": self._refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            data = resp.json()
            if "access_token" in data:
                self._access_token = data["access_token"]
                logger.debug("Google Ads access token refreshed")
                return True
            logger.error(f"Google Ads token refresh failed: {data}")
            return False
        except Exception as e:
            logger.error(f"Google Ads token refresh exception: {e}")
            return False

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "developer-token": self._developer_token,
            "Content-Type": "application/json",
        }
        if self._login_customer_id:
            headers["login-customer-id"] = self._login_customer_id
        return headers

    def _search(self, query: str) -> list[dict[str, Any]]:
        """
        Thực thi GAQL query qua googleAds:search endpoint.
        Auto-refresh token nếu 401.
        """
        if not self.is_configured:
            return []

        if not self._access_token:
            if not self._refresh_access_token():
                return []

        url = f"{GOOGLE_ADS_API_BASE}/customers/{self._customer_id}/googleAds:search"
        payload = {"query": query}

        try:
            resp = self._client.post(url, headers=self._headers(), json=payload)

            # Auto-refresh on 401
            if resp.status_code == 401:
                if self._refresh_access_token():
                    resp = self._client.post(url, headers=self._headers(), json=payload)

            data = resp.json()
            if "error" in data:
                logger.error(f"Google Ads GAQL error: {data['error'].get('message', data['error'])}")
                return []

            return data.get("results", [])

        except Exception as e:
            logger.error(f"Google Ads search exception: {e}")
            return []

    def _mutate(self, resource: str, operations: list[dict]) -> dict[str, Any]:
        """Thực thi mutate operations (create/update/delete)."""
        if not self.is_configured:
            return self._not_configured()

        if not self._access_token:
            if not self._refresh_access_token():
                return {"error": "Không thể lấy access token"}

        url = f"{GOOGLE_ADS_API_BASE}/customers/{self._customer_id}/{resource}:mutate"
        payload = {"operations": operations}

        try:
            resp = self._client.post(url, headers=self._headers(), json=payload)
            if resp.status_code == 401:
                if self._refresh_access_token():
                    resp = self._client.post(url, headers=self._headers(), json=payload)

            data = resp.json()
            if "error" in data:
                logger.error(f"Google Ads mutate error: {data['error']}")
            return data
        except Exception as e:
            logger.error(f"Google Ads mutate exception: {e}")
            return {"error": str(e)}

    # ─── Campaigns ───────────────────────────────────────────────────────────

    def get_campaigns(self, status: str = "ENABLED") -> list[dict[str, Any]]:
        """
        Lấy danh sách campaigns đang chạy.

        Args:
            status: "ENABLED" | "PAUSED" | "REMOVED"
        """
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign_budget.amount_micros,
                campaign.start_date,
                campaign.end_date
            FROM campaign
            WHERE campaign.status = '{status}'
            ORDER BY campaign.name
        """
        results = self._search(query)
        campaigns = [
            {
                "id": r["campaign"]["id"],
                "name": r["campaign"]["name"],
                "status": r["campaign"]["status"],
                "channel": r["campaign"].get("advertisingChannelType", ""),
                "daily_budget": int(r.get("campaignBudget", {}).get("amountMicros", 0)) / 1_000_000,
                "start_date": r["campaign"].get("startDate", ""),
                "end_date": r["campaign"].get("endDate", ""),
            }
            for r in results
        ]
        logger.debug(f"Google Ads campaigns fetched | count={len(campaigns)}")
        return campaigns

    def update_campaign_budget(
        self,
        campaign_budget_id: str,
        daily_budget_vnd: float,
    ) -> dict[str, Any]:
        """
        Cập nhật ngân sách hàng ngày của campaign.
        Google Ads dùng đơn vị micros (1 VNĐ = 1,000,000 micros).

        Args:
            campaign_budget_id: Resource name hoặc ID của budget
            daily_budget_vnd: Ngân sách ngày (VNĐ)
        """
        budget_micros = int(daily_budget_vnd * 1_000_000)
        resource_name = (
            campaign_budget_id
            if campaign_budget_id.startswith("customers/")
            else f"customers/{self._customer_id}/campaignBudgets/{campaign_budget_id}"
        )
        result = self._mutate(
            "campaignBudgets",
            [{
                "updateMask": "amount_micros",
                "update": {
                    "resourceName": resource_name,
                    "amountMicros": str(budget_micros),
                },
            }],
        )
        logger.info(f"Google Ads budget updated | budget_id={campaign_budget_id} | budget={daily_budget_vnd:,.0f}đ")
        return result

    def pause_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Tạm dừng campaign."""
        resource_name = f"customers/{self._customer_id}/campaigns/{campaign_id}"
        result = self._mutate(
            "campaigns",
            [{"updateMask": "status", "update": {"resourceName": resource_name, "status": "PAUSED"}}],
        )
        logger.info(f"Google Ads campaign paused | id={campaign_id}")
        return result

    def enable_campaign(self, campaign_id: str) -> dict[str, Any]:
        """Kích hoạt lại campaign đang tạm dừng."""
        resource_name = f"customers/{self._customer_id}/campaigns/{campaign_id}"
        result = self._mutate(
            "campaigns",
            [{"updateMask": "status", "update": {"resourceName": resource_name, "status": "ENABLED"}}],
        )
        logger.info(f"Google Ads campaign enabled | id={campaign_id}")
        return result

    # ─── Performance Reports ─────────────────────────────────────────────────

    def get_campaign_performance(self, days_back: int = 7) -> list[dict[str, Any]]:
        """
        Báo cáo performance tổng hợp theo campaign trong N ngày qua.

        Returns:
            [{campaign_name, impressions, clicks, ctr, avg_cpc, cost, conversions, roas}]
        """
        query = f"""
            SELECT
                campaign.name,
                campaign.id,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value
            FROM campaign
            WHERE segments.date DURING LAST_{days_back}_DAYS
              AND campaign.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
        """
        results = self._search(query)
        rows = []
        for r in results:
            m = r.get("metrics", {})
            cost = int(m.get("costMicros", 0)) / 1_000_000
            conv_value = float(m.get("conversionsValue", 0))
            rows.append({
                "campaign": r["campaign"]["name"],
                "campaign_id": r["campaign"]["id"],
                "impressions": int(m.get("impressions", 0)),
                "clicks": int(m.get("clicks", 0)),
                "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                "avg_cpc": round(int(m.get("averageCpc", 0)) / 1_000_000, 0),
                "cost_vnd": round(cost, 0),
                "conversions": round(float(m.get("conversions", 0)), 1),
                "roas": round(conv_value / cost, 2) if cost > 0 else 0,
            })
        logger.debug(f"Google Ads campaign performance | days={days_back} | rows={len(rows)}")
        return rows

    def get_keyword_performance(
        self,
        days_back: int = 30,
        min_clicks: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Báo cáo performance theo từ khoá — dùng cho SEOAgent và ResearchAgent.

        Returns:
            [{keyword, match_type, impressions, clicks, avg_cpc, quality_score, cost}]
        """
        query = f"""
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.keyword.match_type,
                ad_group_criterion.quality_info.quality_score,
                metrics.impressions,
                metrics.clicks,
                metrics.average_cpc,
                metrics.cost_micros,
                metrics.conversions
            FROM keyword_view
            WHERE segments.date DURING LAST_{days_back}_DAYS
              AND metrics.clicks >= {min_clicks}
            ORDER BY metrics.clicks DESC
            LIMIT 100
        """
        results = self._search(query)
        rows = []
        for r in results:
            m = r.get("metrics", {})
            kw = r.get("adGroupCriterion", {}).get("keyword", {})
            qi = r.get("adGroupCriterion", {}).get("qualityInfo", {})
            rows.append({
                "keyword": kw.get("text", ""),
                "match_type": kw.get("matchType", ""),
                "quality_score": qi.get("qualityScore", 0),
                "impressions": int(m.get("impressions", 0)),
                "clicks": int(m.get("clicks", 0)),
                "avg_cpc": round(int(m.get("averageCpc", 0)) / 1_000_000, 0),
                "cost_vnd": round(int(m.get("costMicros", 0)) / 1_000_000, 0),
                "conversions": round(float(m.get("conversions", 0)), 1),
            })
        logger.debug(f"Google Ads keyword performance | days={days_back} | rows={len(rows)}")
        return rows

    def get_search_terms_report(self, days_back: int = 30) -> list[dict[str, Any]]:
        """
        Search terms report — từ khoá thực tế người dùng tìm kiếm.
        Dùng cho SEOAgent phát hiện từ khoá mới tiềm năng.
        """
        query = f"""
            SELECT
                search_term_view.search_term,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions
            FROM search_term_view
            WHERE segments.date DURING LAST_{days_back}_DAYS
            ORDER BY metrics.clicks DESC
            LIMIT 50
        """
        results = self._search(query)
        rows = []
        for r in results:
            m = r.get("metrics", {})
            rows.append({
                "search_term": r.get("searchTermView", {}).get("searchTerm", ""),
                "impressions": int(m.get("impressions", 0)),
                "clicks": int(m.get("clicks", 0)),
                "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                "avg_cpc": round(int(m.get("averageCpc", 0)) / 1_000_000, 0),
                "conversions": round(float(m.get("conversions", 0)), 1),
            })
        logger.debug(f"Google Ads search terms | days={days_back} | rows={len(rows)}")
        return rows

    def get_ad_performance(self, days_back: int = 7) -> list[dict[str, Any]]:
        """Báo cáo performance theo từng ad (headline, description, CTR)."""
        query = f"""
            SELECT
                ad_group_ad.ad.responsive_search_ad.headlines,
                ad_group_ad.ad.id,
                ad_group_ad.status,
                metrics.impressions,
                metrics.clicks,
                metrics.ctr,
                metrics.conversions
            FROM ad_group_ad
            WHERE segments.date DURING LAST_{days_back}_DAYS
              AND ad_group_ad.status = 'ENABLED'
            ORDER BY metrics.clicks DESC
            LIMIT 50
        """
        results = self._search(query)
        rows = []
        for r in results:
            m = r.get("metrics", {})
            ad = r.get("adGroupAd", {}).get("ad", {})
            rsa = ad.get("responsiveSearchAd", {})
            headlines = [h.get("text", "") for h in rsa.get("headlines", [])[:3]]
            rows.append({
                "ad_id": ad.get("id", ""),
                "headlines": headlines,
                "impressions": int(m.get("impressions", 0)),
                "clicks": int(m.get("clicks", 0)),
                "ctr": round(float(m.get("ctr", 0)) * 100, 2),
                "conversions": round(float(m.get("conversions", 0)), 1),
            })
        logger.debug(f"Google Ads ad performance | days={days_back} | rows={len(rows)}")
        return rows

    # ─── Keyword Ideas ────────────────────────────────────────────────────────

    def get_keyword_ideas(
        self,
        seed_keywords: list[str],
        language_id: str = "1040",  # Vietnamese
        location_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Lấy ý tưởng từ khoá từ Keyword Planner.
        Dùng cho SEOAgent + ContentAgent nghiên cứu từ khoá.

        Args:
            seed_keywords: Danh sách từ khoá gốc
            language_id: "1040" = Tiếng Việt, "1000" = Tiếng Anh
            location_ids: ["2704"] = Việt Nam
        """
        if not self.is_configured:
            return []
        if not self._access_token:
            self._refresh_access_token()

        if location_ids is None:
            location_ids = ["2704"]  # Vietnam

        url = f"{GOOGLE_ADS_API_BASE}/customers/{self._customer_id}:generateKeywordIdeas"
        payload = {
            "language": f"languageConstants/{language_id}",
            "geoTargetConstants": [f"geoTargetConstants/{lid}" for lid in location_ids],
            "includeAdultKeywords": False,
            "keywordSeed": {"keywords": seed_keywords},
        }

        try:
            resp = self._client.post(url, headers=self._headers(), json=payload)
            if resp.status_code == 401:
                if self._refresh_access_token():
                    resp = self._client.post(url, headers=self._headers(), json=payload)

            data = resp.json()
            ideas = []
            for item in data.get("results", []):
                kw_idea = item.get("keywordIdeaMetrics", {})
                ideas.append({
                    "keyword": item.get("text", ""),
                    "avg_monthly_searches": int(kw_idea.get("avgMonthlySearches", 0)),
                    "competition": kw_idea.get("competition", "UNSPECIFIED"),
                    "low_top_of_page_bid": round(
                        int(kw_idea.get("lowTopOfPageBidMicros", 0)) / 1_000_000, 0
                    ),
                    "high_top_of_page_bid": round(
                        int(kw_idea.get("highTopOfPageBidMicros", 0)) / 1_000_000, 0
                    ),
                })
            ideas.sort(key=lambda x: x["avg_monthly_searches"], reverse=True)
            logger.info(f"Google Ads keyword ideas | seeds={seed_keywords} | ideas={len(ideas)}")
            return ideas

        except Exception as e:
            logger.error(f"Google Ads keyword ideas exception: {e}")
            return []

    # ─── Budget Recommendations ────────────────────────────────────────────────

    def get_budget_recommendation(self, campaign_id: str) -> dict[str, Any]:
        """
        Lấy đề xuất ngân sách từ Google Ads cho campaign cụ thể.
        Dùng cho AdBudgetAgent tối ưu phân bổ.
        """
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                recommendation.campaign_budget_recommendation.budget_options
            FROM recommendation
            WHERE recommendation.type = 'CAMPAIGN_BUDGET'
              AND campaign.id = {campaign_id}
        """
        results = self._search(query)
        if not results:
            return {"message": f"Không có đề xuất ngân sách cho campaign {campaign_id}"}

        rec = results[0].get("recommendation", {})
        budget_rec = rec.get("campaignBudgetRecommendation", {})
        options = [
            {
                "budget_vnd": round(int(o.get("budgetAmountMicros", 0)) / 1_000_000, 0),
                "impact_impressions": o.get("impact", {}).get("baseMetrics", {}).get("impressions", 0),
            }
            for o in budget_rec.get("budgetOptions", [])
        ]
        logger.debug(f"Google Ads budget recommendation | campaign={campaign_id}")
        return {"campaign_id": campaign_id, "budget_options": options}

    # ─── Industry Benchmark (offline) ────────────────────────────────────────

    def get_industry_benchmark(self, industry: str = "saas") -> dict[str, Any]:
        """
        Trả về benchmark ngành VN 2026 (không cần API call).
        Dùng khi chưa có data thực hoặc account chưa cấu hình.
        """
        benchmark = INDUSTRY_BENCHMARKS.get(industry.lower(), INDUSTRY_BENCHMARKS["saas"])
        return {
            "industry": industry,
            "source": "FuviAI benchmark VN 2026",
            **benchmark,
            "note": "Dùng data thực từ get_campaign_performance() khi có đủ lịch sử",
        }

    # ─── Summary cho Agents ───────────────────────────────────────────────────

    def get_account_summary(self, days_back: int = 30) -> dict[str, Any]:
        """
        Tóm tắt toàn bộ account — dùng cho CampaignAgent báo cáo tháng.

        Returns:
            {total_cost, total_clicks, total_impressions, total_conversions,
             avg_ctr, avg_cpc, overall_roas, top_campaigns}
        """
        rows = self.get_campaign_performance(days_back=days_back)
        if not rows:
            return {"error": "Không có dữ liệu hoặc chưa cấu hình Google Ads"}

        total_cost = sum(r["cost_vnd"] for r in rows)
        total_clicks = sum(r["clicks"] for r in rows)
        total_impressions = sum(r["impressions"] for r in rows)
        total_conversions = sum(r["conversions"] for r in rows)
        conv_value = sum(r["roas"] * r["cost_vnd"] for r in rows)

        summary = {
            "days": days_back,
            "total_cost_vnd": round(total_cost, 0),
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "total_conversions": round(total_conversions, 1),
            "avg_ctr": round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0,
            "avg_cpc_vnd": round(total_cost / total_clicks, 0) if total_clicks > 0 else 0,
            "overall_roas": round(conv_value / total_cost, 2) if total_cost > 0 else 0,
            "top_campaigns": sorted(rows, key=lambda x: x["cost_vnd"], reverse=True)[:5],
        }
        logger.info(f"Google Ads account summary | days={days_back} | cost={total_cost:,.0f}đ")
        return summary
