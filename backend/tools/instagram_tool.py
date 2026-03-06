"""
FuviAI Marketing Agent — Instagram Tool
Instagram Graph API v21.0 — Business/Creator accounts
Docs: https://developers.facebook.com/docs/instagram-api
"""

from __future__ import annotations

from typing import Any

import requests
from loguru import logger


GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


class InstagramTool:
    """
    Wrapper cho Instagram Graph API.
    Instagram Business/Creator account phải được kết nối với Facebook Page.

    Env vars cần thiết (trong Settings):
        INSTAGRAM_ACCESS_TOKEN   — Page Access Token (long-lived, đã có page permission)
        INSTAGRAM_BUSINESS_ID    — Instagram Business Account ID

    Usage:
        tool = InstagramTool()

        # Đăng ảnh
        result = tool.publish_photo(
            image_url="https://...",
            caption="Caption hay #FuviAI #Marketing"
        )

        # Đăng carousel (nhiều ảnh)
        result = tool.publish_carousel(
            image_urls=["https://img1.jpg", "https://img2.jpg"],
            caption="Carousel post"
        )

        # Đăng Reel
        result = tool.publish_reel(
            video_url="https://video.mp4",
            caption="Reel caption",
            cover_url="https://thumb.jpg"
        )
    """

    def __init__(self):
        from backend.config.settings import get_settings
        settings = get_settings()
        self._token: str = settings.instagram_access_token
        self._ig_id: str = settings.instagram_business_id
        self._enabled: bool = bool(self._token and self._ig_id)

        if not self._enabled:
            logger.warning("Instagram API not configured — posting disabled")

    # ─── Internal helpers ────────────────────────────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        if params is None:
            params = {}
        params["access_token"] = self._token
        try:
            r = requests.get(f"{GRAPH_API_BASE}{path}", params=params, timeout=15)
            return r.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def _post(self, path: str, data: dict | None = None) -> dict[str, Any]:
        if data is None:
            data = {}
        data["access_token"] = self._token
        try:
            r = requests.post(f"{GRAPH_API_BASE}{path}", data=data, timeout=30)
            return r.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def _check_enabled(self) -> dict[str, Any] | None:
        if not self._enabled:
            return {"error": "Instagram API not configured", "success": False}
        return None

    # ─── Account Info ─────────────────────────────────────────────────────────

    def get_account_info(self) -> dict[str, Any]:
        """Thông tin Instagram Business Account."""
        err = self._check_enabled()
        if err:
            return err
        return self._get(
            f"/{self._ig_id}",
            {"fields": "id,name,username,followers_count,media_count,biography,website"}
        )

    def get_account_insights(
        self,
        metric: str = "impressions,reach,profile_views,follower_count",
        period: str = "day",
        since: str = "",
        until: str = "",
    ) -> dict[str, Any]:
        """
        Lấy insights tổng quan tài khoản.

        Args:
            metric: Comma-separated metrics
            period: day | week | month | lifetime
        """
        err = self._check_enabled()
        if err:
            return err
        params: dict[str, Any] = {"metric": metric, "period": period}
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        return self._get(f"/{self._ig_id}/insights", params)

    # ─── Media Publishing ─────────────────────────────────────────────────────

    def publish_photo(
        self,
        image_url: str,
        caption: str = "",
        location_id: str = "",
    ) -> dict[str, Any]:
        """
        Đăng ảnh đơn lên Instagram.

        Args:
            image_url: URL công khai của ảnh (JPEG/PNG, min 320x320px)
            caption: Caption kèm hashtags (tối đa 2200 ký tự)
            location_id: Facebook location page ID (tuỳ chọn)
        """
        err = self._check_enabled()
        if err:
            return err
        if not image_url:
            return {"error": "image_url là bắt buộc"}

        # Step 1: Tạo container
        container_data: dict[str, Any] = {
            "image_url": image_url,
            "caption": caption[:2200],
        }
        if location_id:
            container_data["location_id"] = location_id

        container = self._post(f"/{self._ig_id}/media", container_data)
        if "error" in container or "id" not in container:
            logger.error(f"Instagram container creation failed: {container}")
            return container

        container_id = container["id"]
        logger.info(f"Instagram container created | id={container_id}")

        # Step 2: Publish container
        result = self._post(f"/{self._ig_id}/media_publish", {"creation_id": container_id})
        if "id" in result:
            logger.info(f"Instagram photo published | media_id={result['id']}")
        return result

    def publish_carousel(
        self,
        image_urls: list[str],
        caption: str = "",
    ) -> dict[str, Any]:
        """
        Đăng carousel (2-10 ảnh/video).

        Args:
            image_urls: Danh sách URL ảnh (2-10 ảnh)
            caption: Caption cho cả carousel
        """
        err = self._check_enabled()
        if err:
            return err
        if not 2 <= len(image_urls) <= 10:
            return {"error": "Carousel cần từ 2 đến 10 ảnh"}

        # Step 1: Tạo item containers
        item_ids: list[str] = []
        for url in image_urls:
            item = self._post(f"/{self._ig_id}/media", {
                "image_url": url,
                "is_carousel_item": "true",
            })
            if "id" not in item:
                return {"error": f"Lỗi tạo carousel item: {item}"}
            item_ids.append(item["id"])

        # Step 2: Tạo carousel container
        carousel = self._post(f"/{self._ig_id}/media", {
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": caption[:2200],
        })
        if "id" not in carousel:
            return {"error": f"Lỗi tạo carousel container: {carousel}"}

        # Step 3: Publish
        result = self._post(f"/{self._ig_id}/media_publish", {"creation_id": carousel["id"]})
        if "id" in result:
            logger.info(f"Instagram carousel published | items={len(image_urls)} | id={result['id']}")
        return result

    def publish_reel(
        self,
        video_url: str,
        caption: str = "",
        cover_url: str = "",
        share_to_feed: bool = True,
    ) -> dict[str, Any]:
        """
        Đăng Instagram Reel.

        Args:
            video_url: URL công khai video (MP4, min 3s max 90s)
            caption: Caption kèm hashtags
            cover_url: URL thumbnail (tuỳ chọn)
            share_to_feed: Cũng hiển thị trên Feed không
        """
        err = self._check_enabled()
        if err:
            return err
        if not video_url:
            return {"error": "video_url là bắt buộc"}

        # Step 1: Tạo container
        container_data: dict[str, Any] = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": caption[:2200],
            "share_to_feed": "true" if share_to_feed else "false",
        }
        if cover_url:
            container_data["cover_url"] = cover_url

        container = self._post(f"/{self._ig_id}/media", container_data)
        if "id" not in container:
            logger.error(f"Instagram Reel container failed: {container}")
            return container

        # Step 2: Đợi video processing (status check)
        import time
        container_id = container["id"]
        for _ in range(10):
            status = self._get(f"/{container_id}", {"fields": "status_code"})
            if status.get("status_code") == "FINISHED":
                break
            if status.get("status_code") == "ERROR":
                return {"error": "Video processing failed", "details": status}
            time.sleep(5)

        # Step 3: Publish
        result = self._post(f"/{self._ig_id}/media_publish", {"creation_id": container_id})
        if "id" in result:
            logger.info(f"Instagram Reel published | id={result['id']}")
        return result

    def publish_story_photo(self, image_url: str) -> dict[str, Any]:
        """Đăng ảnh lên Instagram Stories (24h)."""
        err = self._check_enabled()
        if err:
            return err
        container = self._post(f"/{self._ig_id}/media", {
            "image_url": image_url,
            "media_type": "STORIES",
        })
        if "id" not in container:
            return container
        return self._post(f"/{self._ig_id}/media_publish", {"creation_id": container["id"]})

    # ─── Media Management ─────────────────────────────────────────────────────

    def get_media_list(
        self,
        limit: int = 20,
        fields: str = "id,caption,media_type,timestamp,like_count,comments_count,permalink",
    ) -> dict[str, Any]:
        """Lấy danh sách media gần đây."""
        err = self._check_enabled()
        if err:
            return err
        return self._get(f"/{self._ig_id}/media", {"fields": fields, "limit": min(limit, 100)})

    def get_media_insights(self, media_id: str) -> dict[str, Any]:
        """
        Lấy insights cho 1 post.
        Metrics: impressions, reach, likes, comments, shares, saved, total_interactions
        """
        err = self._check_enabled()
        if err:
            return err
        return self._get(
            f"/{media_id}/insights",
            {"metric": "impressions,reach,likes,comments,shares,saved,total_interactions"}
        )

    def get_post_performance(self, limit: int = 10) -> dict[str, Any]:
        """
        Tổng hợp hiệu suất N posts gần nhất — dùng cho Competitor/Insight agents.
        """
        err = self._check_enabled()
        if err:
            return {"posts": [], "error": err.get("error")}

        media = self.get_media_list(limit=limit)
        posts = media.get("data", [])

        enriched = []
        for post in posts:
            insights = self.get_media_insights(post["id"])
            metrics = {}
            for item in insights.get("data", []):
                metrics[item["name"]] = item.get("values", [{}])[-1].get("value", 0)
            enriched.append({
                "id": post["id"],
                "media_type": post.get("media_type", ""),
                "caption": (post.get("caption", "") or "")[:100],
                "timestamp": post.get("timestamp", ""),
                "permalink": post.get("permalink", ""),
                "like_count": post.get("like_count", 0),
                "comments_count": post.get("comments_count", 0),
                **metrics,
            })

        logger.info(f"Instagram post performance fetched | posts={len(enriched)}")
        return {"posts": enriched, "total": len(enriched)}

    # ─── Comments ─────────────────────────────────────────────────────────────

    def get_comments(self, media_id: str, limit: int = 50) -> dict[str, Any]:
        """Lấy comments của 1 post."""
        err = self._check_enabled()
        if err:
            return err
        return self._get(
            f"/{media_id}/comments",
            {"fields": "id,text,username,timestamp,like_count", "limit": min(limit, 100)}
        )

    def reply_to_comment(self, comment_id: str, message: str) -> dict[str, Any]:
        """Trả lời comment."""
        err = self._check_enabled()
        if err:
            return err
        return self._post(f"/{comment_id}/replies", {"message": message[:1000]})

    def batch_reply_comments(
        self,
        media_id: str,
        reply_template: str,
        max_replies: int = 20,
    ) -> dict[str, Any]:
        """
        Trả lời tất cả comments chưa có reply (dùng cho SocialAgent).

        Args:
            reply_template: Template reply — có thể dùng {{username}} để mention
        """
        err = self._check_enabled()
        if err:
            return err

        comments_data = self.get_comments(media_id, limit=max_replies)
        comments = comments_data.get("data", [])

        replied = 0
        failed = 0
        for comment in comments[:max_replies]:
            username = comment.get("username", "bạn")
            msg = reply_template.replace("{{username}}", f"@{username}")
            result = self.reply_to_comment(comment["id"], msg)
            if "id" in result:
                replied += 1
            else:
                failed += 1

        logger.info(f"Instagram batch reply | replied={replied} | failed={failed}")
        return {"replied": replied, "failed": failed, "total": len(comments)}

    # ─── Hashtag Research ────────────────────────────────────────────────────

    def search_hashtag(self, hashtag: str) -> dict[str, Any]:
        """
        Tìm top/recent media theo hashtag (dùng cho ListeningAgent).
        Giới hạn: 30 unique hashtags/7 ngày per IG account.
        """
        err = self._check_enabled()
        if err:
            return err
        if hashtag.startswith("#"):
            hashtag = hashtag[1:]

        # Step 1: Get hashtag ID
        search = self._get("/ig_hashtag_search", {
            "user_id": self._ig_id,
            "q": hashtag,
        })
        if "data" not in search or not search["data"]:
            return {"error": f"Hashtag #{hashtag} not found", "count": 0}

        ht_id = search["data"][0]["id"]

        # Step 2: Get top media
        top = self._get(f"/{ht_id}/top_media", {
            "user_id": self._ig_id,
            "fields": "id,caption,media_type,like_count,comments_count,timestamp",
        })
        recent = self._get(f"/{ht_id}/recent_media", {
            "user_id": self._ig_id,
            "fields": "id,caption,media_type,like_count,comments_count,timestamp",
        })

        return {
            "hashtag": hashtag,
            "hashtag_id": ht_id,
            "top_media": top.get("data", []),
            "recent_media": recent.get("data", [])[:10],
            "top_count": len(top.get("data", [])),
        }
