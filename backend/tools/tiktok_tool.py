"""
FuviAI Marketing Agent — TikTok Tool
TikTok for Business Content Posting API v2 wrapper
Docs: https://developers.tiktok.com/doc/content-posting-api-get-started

Flows:
  - Direct Post (video URL): init → upload → publish
  - Scheduled Post: init với scheduled_publish_time
  - Analytics: video list + stats
  - Comments: list + reply
"""

from __future__ import annotations

from typing import Any
from loguru import logger

import httpx

from backend.config.settings import get_settings


TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"

# Privacy levels theo TikTok API
PRIVACY_LEVEL = {
    "public": "PUBLIC_TO_EVERYONE",
    "friends": "MUTUAL_FOLLOW_FRIENDS",
    "private": "SELF_ONLY",
}


class TikTokTool:
    """
    Wrapper cho TikTok for Business Content Posting API v2.

    Cần trong .env:
        TIKTOK_ACCESS_TOKEN — User access token (scope: video.upload, video.publish)
        TIKTOK_APP_ID       — App ID từ TikTok Developer Portal

    Usage:
        tool = TikTokTool()

        # Đăng video từ URL công khai
        result = tool.publish_video_from_url(
            video_url="https://cdn.example.com/video.mp4",
            title="FuviAI — AI Marketing tự động #marketing #ai",
        )

        # Lên lịch đăng sau 2 giờ
        import time
        result = tool.schedule_video(
            video_url="https://cdn.example.com/video.mp4",
            title="Flash Sale 11/11 #sale",
            scheduled_time=int(time.time()) + 7200,
        )

        # Lấy analytics
        stats = tool.get_video_analytics(["video_id_1", "video_id_2"])
    """

    def __init__(self):
        settings = get_settings()
        self._access_token = settings.tiktok_access_token
        self._app_id = settings.tiktok_app_id
        self._client = httpx.Client(timeout=30)

    @property
    def is_configured(self) -> bool:
        return bool(self._access_token and self._app_id)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def _not_configured(self) -> dict[str, Any]:
        return {"error": "TIKTOK_ACCESS_TOKEN hoặc TIKTOK_APP_ID chưa được set trong .env"}

    def _get(self, endpoint: str, params: dict | None = None) -> dict[str, Any]:
        if not self.is_configured:
            return self._not_configured()
        try:
            resp = self._client.get(
                f"{TIKTOK_API_BASE}/{endpoint}",
                headers=self._headers(),
                params=params or {},
            )
            data = resp.json()
            if data.get("error", {}).get("code") not in (None, "ok"):
                logger.error(f"TikTok GET error: {data['error']}")
            return data
        except Exception as e:
            logger.error(f"TikTok GET exception: {e}")
            return {"error": str(e)}

    def _post(self, endpoint: str, payload: dict) -> dict[str, Any]:
        if not self.is_configured:
            return self._not_configured()
        try:
            resp = self._client.post(
                f"{TIKTOK_API_BASE}/{endpoint}",
                headers=self._headers(),
                json=payload,
            )
            data = resp.json()
            if data.get("error", {}).get("code") not in (None, "ok"):
                logger.error(f"TikTok POST error: {data['error']}")
            return data
        except Exception as e:
            logger.error(f"TikTok POST exception: {e}")
            return {"error": str(e)}

    # ─── Account ─────────────────────────────────────────────────────────────

    def get_creator_info(self) -> dict[str, Any]:
        """
        Lấy thông tin creator account (tên, avatar, follower count...).
        Scope cần: user.info.basic
        """
        result = self._post(
            "user/info/",
            {"fields": ["display_name", "avatar_url", "follower_count", "video_count"]},
        )
        logger.debug("TikTok creator info fetched")
        return result.get("data", result)

    # ─── Video Publish ────────────────────────────────────────────────────────

    def publish_video_from_url(
        self,
        video_url: str,
        title: str,
        privacy: str = "public",
        disable_comment: bool = False,
        disable_duet: bool = False,
        disable_stitch: bool = False,
    ) -> dict[str, Any]:
        """
        Đăng video lên TikTok từ URL công khai (Pull từ URL).
        Cách nhanh nhất — TikTok tự download video.

        Args:
            video_url: URL công khai của file video (.mp4, .mov, .webm)
            title: Caption/description tối đa 2200 ký tự, hỗ trợ #hashtag @mention
            privacy: "public" | "friends" | "private"
            disable_comment: Tắt bình luận
            disable_duet: Tắt duet
            disable_stitch: Tắt stitch
        """
        if len(title) > 2200:
            title = title[:2197] + "..."

        payload = {
            "post_info": {
                "title": title,
                "privacy_level": PRIVACY_LEVEL.get(privacy, "PUBLIC_TO_EVERYONE"),
                "disable_comment": disable_comment,
                "disable_duet": disable_duet,
                "disable_stitch": disable_stitch,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
        }

        result = self._post("post/publish/video/init/", payload)
        publish_id = result.get("data", {}).get("publish_id", "")
        logger.info(f"TikTok video published | title={title[:50]} | publish_id={publish_id}")
        return {
            "publish_id": publish_id,
            "status": "published" if publish_id else "failed",
            "raw": result,
        }

    def schedule_video(
        self,
        video_url: str,
        title: str,
        scheduled_time: int,
        privacy: str = "public",
    ) -> dict[str, Any]:
        """
        Lên lịch đăng video TikTok.

        Args:
            scheduled_time: Unix timestamp (phải ít nhất 15 phút từ bây giờ,
                            tối đa 10 ngày sau)
        """
        if len(title) > 2200:
            title = title[:2197] + "..."

        payload = {
            "post_info": {
                "title": title,
                "privacy_level": PRIVACY_LEVEL.get(privacy, "PUBLIC_TO_EVERYONE"),
                "scheduled_publish_time": scheduled_time,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "video_url": video_url,
            },
        }

        result = self._post("post/publish/video/init/", payload)
        publish_id = result.get("data", {}).get("publish_id", "")
        logger.info(f"TikTok video scheduled | title={title[:50]} | time={scheduled_time}")
        return {
            "publish_id": publish_id,
            "scheduled_time": scheduled_time,
            "status": "scheduled" if publish_id else "failed",
            "raw": result,
        }

    def get_publish_status(self, publish_id: str) -> dict[str, Any]:
        """
        Kiểm tra trạng thái upload/publish của video.
        Status: PROCESSING_UPLOAD | PUBLISH_COMPLETE | FAILED
        """
        result = self._post(
            "post/publish/status/fetch/",
            {"publish_id": publish_id},
        )
        status = result.get("data", {}).get("status", "UNKNOWN")
        logger.debug(f"TikTok publish status | id={publish_id} | status={status}")
        return result.get("data", result)

    # ─── Video Analytics ─────────────────────────────────────────────────────

    def get_video_list(self, max_count: int = 20) -> list[dict[str, Any]]:
        """
        Lấy danh sách video đã đăng của account.
        Trả về list gồm id, title, create_time, share_url.
        """
        result = self._post(
            "video/list/",
            {
                "fields": ["id", "title", "create_time", "share_url", "view_count", "like_count"],
                "max_count": min(max_count, 20),
            },
        )
        videos = result.get("data", {}).get("videos", [])
        logger.debug(f"TikTok video list fetched | count={len(videos)}")
        return videos

    def get_video_analytics(self, video_ids: list[str]) -> dict[str, Any]:
        """
        Lấy analytics chi tiết của nhiều video.

        Returns:
            {video_id: {view_count, like_count, comment_count, share_count, ...}}
        """
        if not video_ids:
            return {}

        result = self._post(
            "video/query/",
            {
                "filters": {"video_ids": video_ids[:20]},
                "fields": [
                    "id", "title", "create_time",
                    "view_count", "like_count", "comment_count",
                    "share_count", "reach", "video_duration",
                    "average_time_watched", "full_video_watched_rate",
                ],
            },
        )

        videos = result.get("data", {}).get("videos", [])
        analytics = {v["id"]: v for v in videos if "id" in v}
        logger.debug(f"TikTok analytics fetched | videos={len(analytics)}")
        return analytics

    def get_account_analytics(
        self,
        date_range_start: str,
        date_range_end: str,
    ) -> dict[str, Any]:
        """
        Lấy analytics tổng hợp của account theo khoảng thời gian.

        Args:
            date_range_start: "20260101"
            date_range_end: "20260131"
        """
        result = self._get(
            "research/adlib/ad/query/",
            {
                "start_date": date_range_start,
                "end_date": date_range_end,
                "fields": "view_count,like_count,comment_count,share_count,follower_count",
            },
        )
        return result.get("data", result)

    # ─── Comments ────────────────────────────────────────────────────────────

    def get_video_comments(
        self,
        video_id: str,
        max_count: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách comments của video.
        Scope cần: comment.list
        """
        result = self._post(
            "comment/list/",
            {
                "video_id": video_id,
                "fields": ["id", "text", "create_time", "like_count", "username"],
                "max_count": min(max_count, 100),
            },
        )
        comments = result.get("data", {}).get("comments", [])
        logger.debug(f"TikTok comments fetched | video={video_id} | count={len(comments)}")
        return comments

    def reply_to_comment(
        self,
        video_id: str,
        comment_id: str,
        text: str,
    ) -> dict[str, Any]:
        """
        Reply comment trên TikTok video.
        Scope cần: comment.write

        Args:
            video_id: ID của video chứa comment
            comment_id: ID của comment cần reply
            text: Nội dung reply
        """
        if len(text) > 150:
            text = text[:147] + "..."

        result = self._post(
            "comment/publish/",
            {
                "video_id": video_id,
                "parent_comment_id": comment_id,
                "text": text,
            },
        )
        comment_id_new = result.get("data", {}).get("comment_id", "")
        logger.info(f"TikTok comment replied | video={video_id} | parent={comment_id}")
        return {
            "comment_id": comment_id_new,
            "status": "published" if comment_id_new else "failed",
            "raw": result,
        }

    def batch_reply_comments(
        self,
        video_id: str,
        replies: list[dict[str, str]],
    ) -> list[dict[str, Any]]:
        """
        Reply nhiều comments cùng lúc (dùng cho livestream agent).

        Args:
            replies: [{"comment_id": "...", "text": "Cảm ơn bạn!"}]
        """
        results = []
        for item in replies:
            result = self.reply_to_comment(
                video_id=video_id,
                comment_id=item["comment_id"],
                text=item["text"],
            )
            results.append(result)
        logger.info(f"TikTok batch reply | video={video_id} | count={len(results)}")
        return results

    # ─── Hashtag Research ────────────────────────────────────────────────────

    def search_hashtag(self, hashtag: str) -> dict[str, Any]:
        """
        Tìm kiếm thông tin về một hashtag (view count, video count).
        Dùng cho ListeningAgent để theo dõi trend.
        """
        result = self._get(
            "research/hashtag/query/",
            {"hashtag_name": hashtag.lstrip("#")},
        )
        logger.debug(f"TikTok hashtag search | #{hashtag}")
        return result.get("data", result)
