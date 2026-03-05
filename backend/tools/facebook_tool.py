"""
FuviAI Marketing Agent — Facebook Tool
Facebook Graph API wrapper cho Page management và posting
Docs: https://developers.facebook.com/docs/graph-api
"""

from __future__ import annotations

from typing import Any
from loguru import logger

import requests

from backend.config.settings import get_settings


GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class FacebookTool:
    """
    Wrapper cho Facebook Graph API.

    Usage:
        tool = FacebookTool()
        tool.post_to_page("Caption hay cho post mới!")
        tool.schedule_post("Content...", publish_time=1234567890)
    """

    def __init__(self):
        self.settings = get_settings()
        self._session = requests.Session()

    def _get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        if not self.settings.facebook_access_token:
            return {"error": "FACEBOOK_ACCESS_TOKEN chưa được set trong .env"}
        url = f"{GRAPH_API_BASE}/{endpoint}"
        p = {"access_token": self.settings.facebook_access_token, **(params or {})}
        try:
            resp = self._session.get(url, params=p, timeout=10)
            return resp.json()
        except Exception as e:
            logger.error(f"Facebook GET error: {e}")
            return {"error": str(e)}

    def _post(self, endpoint: str, payload: dict) -> dict[str, Any]:
        if not self.settings.facebook_access_token:
            return {"error": "FACEBOOK_ACCESS_TOKEN chưa được set trong .env"}
        url = f"{GRAPH_API_BASE}/{endpoint}"
        try:
            resp = self._session.post(
                url,
                data={**payload, "access_token": self.settings.facebook_access_token},
                timeout=10,
            )
            data = resp.json()
            if "error" in data:
                logger.error(f"Facebook API error: {data['error']}")
            return data
        except Exception as e:
            logger.error(f"Facebook POST error: {e}")
            return {"error": str(e)}

    # ─── Page Posts ──────────────────────────────────────────────────────────

    def post_to_page(self, message: str, link: str = "") -> dict:
        """Đăng bài lên Facebook Page ngay lập tức."""
        page_id = self.settings.facebook_page_id
        if not page_id:
            return {"error": "FACEBOOK_PAGE_ID chưa được set trong .env"}

        payload = {"message": message}
        if link:
            payload["link"] = link

        result = self._post(f"{page_id}/feed", payload)
        logger.info(f"Facebook post published | page={page_id} | chars={len(message)}")
        return result

    def schedule_post(
        self,
        message: str,
        publish_time: int,
        link: str = "",
    ) -> dict:
        """
        Lên lịch đăng bài Facebook.

        Args:
            publish_time: Unix timestamp (phải ít nhất 10 phút từ bây giờ)
        """
        page_id = self.settings.facebook_page_id
        if not page_id:
            return {"error": "FACEBOOK_PAGE_ID chưa được set trong .env"}

        payload = {
            "message": message,
            "published": "false",
            "scheduled_publish_time": str(publish_time),
        }
        if link:
            payload["link"] = link

        result = self._post(f"{page_id}/feed", payload)
        logger.info(f"Facebook post scheduled | page={page_id} | time={publish_time}")
        return result

    def post_with_image(self, message: str, image_url: str) -> dict:
        """Đăng bài kèm ảnh từ URL."""
        page_id = self.settings.facebook_page_id
        if not page_id:
            return {"error": "FACEBOOK_PAGE_ID chưa được set trong .env"}

        # Upload photo trước
        photo_result = self._post(
            f"{page_id}/photos",
            {"url": image_url, "published": "false"},
        )

        if "id" not in photo_result:
            return photo_result

        # Đăng bài kèm photo
        return self._post(
            f"{page_id}/feed",
            {"message": message, "attached_media": f"[{{'media_fbid': '{photo_result['id']}'}}]"},
        )

    # ─── Page Analytics ──────────────────────────────────────────────────────

    def get_page_insights(
        self,
        metrics: list[str] | None = None,
        period: str = "week",
    ) -> dict:
        """Lấy analytics của Page."""
        page_id = self.settings.facebook_page_id
        if not page_id:
            return {"error": "FACEBOOK_PAGE_ID chưa được set trong .env"}

        default_metrics = [
            "page_impressions", "page_reach", "page_engaged_users",
            "page_fans", "page_views_total",
        ]
        metrics = metrics or default_metrics

        return self._get(
            f"{page_id}/insights",
            {"metric": ",".join(metrics), "period": period},
        )

    def get_post_insights(self, post_id: str) -> dict:
        """Lấy analytics của 1 post cụ thể."""
        metrics = "post_impressions,post_reach,post_engaged_users,post_reactions_by_type_total,post_clicks"
        return self._get(f"{post_id}/insights", {"metric": metrics})

    def get_recent_posts(self, limit: int = 10) -> dict:
        """Lấy danh sách bài viết gần đây."""
        page_id = self.settings.facebook_page_id
        if not page_id:
            return {"error": "FACEBOOK_PAGE_ID chưa được set trong .env"}
        return self._get(
            f"{page_id}/posts",
            {"fields": "id,message,created_time,likes.summary(true),comments.summary(true)", "limit": limit},
        )

    # ─── Ad Library ──────────────────────────────────────────────────────────

    def search_ads_library(
        self,
        search_terms: str,
        country: str = "VN",
        limit: int = 20,
    ) -> dict:
        """
        Tìm kiếm ads trong Facebook Ad Library (để research đối thủ).
        Cần app review để dùng đầy đủ.
        """
        return self._get(
            "ads_archive",
            {
                "ad_reached_countries": country,
                "search_terms": search_terms,
                "ad_type": "ALL",
                "fields": "id,ad_creative_body,page_name,ad_snapshot_url",
                "limit": limit,
            },
        )

    # ─── Comments ────────────────────────────────────────────────────────────

    def get_post_comments(self, post_id: str, limit: int = 100) -> list[str]:
        """Lấy comments của 1 post để phân tích sentiment."""
        result = self._get(
            f"{post_id}/comments",
            {"fields": "message,created_time", "limit": limit},
        )
        comments = result.get("data", [])
        return [c.get("message", "") for c in comments if c.get("message")]

    def reply_to_comment(self, comment_id: str, message: str) -> dict:
        """Reply comment tự động."""
        return self._post(f"{comment_id}/comments", {"message": message})
