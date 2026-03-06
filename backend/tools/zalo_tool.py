"""
FuviAI Marketing Agent — Zalo OA Tool
Zalo Official Account API wrapper
Docs: https://developers.zalo.me/docs/api/official-account-api
"""

from __future__ import annotations

from typing import Any
from loguru import logger

import requests

from backend.config.settings import get_settings


ZALO_API_BASE = "https://openapi.zalo.me/v2.0/oa"


class ZaloOATool:
    """
    Wrapper cho Zalo Official Account API.

    Usage:
        tool = ZaloOATool()
        tool.send_message(user_id="xxx", message="Chào anh Minh!")
        tool.broadcast(message="Thông báo khuyến mãi!")
    """

    def __init__(self):
        self.settings = get_settings()
        self._session = requests.Session()
        self._session.headers.update({
            "access_token": self.settings.zalo_oa_access_token,
            "Content-Type": "application/json",
        })

    def _post(self, endpoint: str, payload: dict) -> dict[str, Any]:
        if not self.settings.zalo_oa_access_token:
            logger.warning("Zalo OA token chưa được cấu hình")
            return {"error": "ZALO_OA_ACCESS_TOKEN chưa được set trong .env"}

        url = f"{ZALO_API_BASE}/{endpoint}"
        try:
            resp = self._session.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("error") and data["error"] != 0:
                logger.error(f"Zalo API error: {data}")
            return data
        except requests.RequestException as e:
            logger.error(f"Zalo request failed: {e}")
            return {"error": str(e)}

    # ─── Messaging ───────────────────────────────────────────────────────────

    def send_text_message(self, user_id: str, message: str) -> dict:
        """Gửi text message cho 1 user."""
        payload = {
            "recipient": {"user_id": user_id},
            "message": {"text": message},
        }
        result = self._post("message", payload)
        logger.info(f"Zalo message sent | user={user_id} | chars={len(message)}")
        return result

    def send_image_message(self, user_id: str, image_url: str, caption: str = "") -> dict:
        """Gửi ảnh kèm caption."""
        payload = {
            "recipient": {"user_id": user_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "media",
                        "elements": [{"media_type": "image", "url": image_url}],
                    },
                },
                "text": caption,
            },
        }
        return self._post("message", payload)

    def send_button_message(
        self,
        user_id: str,
        text: str,
        buttons: list[dict],
    ) -> dict:
        """
        Gửi message có nút bấm.

        Args:
            buttons: [{"title": "Mua ngay", "payload": "BUY_NOW"}, ...]
        """
        payload = {
            "recipient": {"user_id": user_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": text,
                        "buttons": [
                            {"type": "oa.query.hide", "title": b["title"], "payload": b.get("payload", b["title"])}
                            for b in buttons
                        ],
                    },
                }
            },
        }
        return self._post("message", payload)

    # ─── Broadcast ───────────────────────────────────────────────────────────

    def broadcast(
        self,
        message: str,
        tag_names: list[str] | None = None,
    ) -> dict:
        """
        Gửi broadcast đến toàn bộ followers hoặc theo tag.

        Args:
            tag_names: Lọc theo tag (None = gửi tất cả)
        """
        payload: dict[str, Any] = {
            "recipient": {"user_id": "all"},
            "message": {"text": message},
        }
        if tag_names:
            payload["recipient"] = {"tag_names": tag_names}

        result = self._post("message", payload)
        logger.info(f"Zalo broadcast sent | tags={tag_names} | chars={len(message)}")
        return result

    # ─── Follower Info ────────────────────────────────────────────────────────

    def get_follower_info(self, user_id: str) -> dict:
        """Lấy thông tin follower."""
        if not self.settings.zalo_oa_access_token:
            return {"error": "Token chưa được cấu hình"}
        url = f"{ZALO_API_BASE}/getprofile"
        try:
            resp = self._session.get(url, params={"user_id": user_id}, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_followers(self, offset: int = 0, count: int = 50) -> dict:
        """Lấy danh sách followers."""
        if not self.settings.zalo_oa_access_token:
            return {"error": "Token chưa được cấu hình"}
        url = f"{ZALO_API_BASE}/getfollowers"
        try:
            resp = self._session.get(url, params={"offset": offset, "count": count}, timeout=10)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    # ─── OA Info & Stats ─────────────────────────────────────────────────────

    def get_oa_info(self) -> dict[str, Any]:
        """Lấy thông tin OA: tên, avatar, follower count, description."""
        if not self.settings.zalo_oa_access_token:
            return {"error": "ZALO_OA_ACCESS_TOKEN chưa được set trong .env"}
        url = f"{ZALO_API_BASE}/getoa"
        try:
            resp = self._session.get(url, timeout=10)
            data = resp.json()
            oa = data.get("data", data)
            logger.debug("Zalo OA info fetched")
            return {
                "name": oa.get("name", ""),
                "oa_id": oa.get("oa_id", ""),
                "avatar": oa.get("avatar", ""),
                "cover": oa.get("cover", ""),
                "description": oa.get("description", ""),
                "num_follower": oa.get("num_follower", 0),
                "is_verified": oa.get("is_verified", False),
                "oa_type": oa.get("oa_type", 0),
            }
        except Exception as e:
            logger.error(f"Zalo OA info error: {e}")
            return {"error": str(e)}

    def get_tags(self) -> list[dict[str, Any]]:
        """Lấy danh sách tags của OA."""
        if not self.settings.zalo_oa_access_token:
            return []
        url = f"{ZALO_API_BASE}/tag/getallbyoa"
        try:
            resp = self._session.get(url, timeout=10)
            data = resp.json()
            tags = data.get("data", [])
            logger.debug(f"Zalo OA tags fetched | count={len(tags)}")
            return [{"name": t.get("tagName", ""), "total": t.get("totalFollower", 0)} for t in tags]
        except Exception as e:
            logger.error(f"Zalo OA tags error: {e}")
            return []

    def send_broadcast_by_tag(self, tag_name: str, message: str) -> dict[str, Any]:
        """Broadcast tin nhắn đến followers có tag cụ thể."""
        payload = {
            "recipient": {"tag_name": tag_name},
            "message": {"text": message},
        }
        result = self._post("message", payload)
        logger.info(f"Zalo broadcast by tag | tag={tag_name} | chars={len(message)}")
        return result

    def get_recent_chats(self, count: int = 10, offset: int = 0) -> list[dict[str, Any]]:
        """Lấy danh sách hội thoại gần đây."""
        if not self.settings.zalo_oa_access_token:
            return []
        url = f"{ZALO_API_BASE}/listrecentchat"
        try:
            resp = self._session.get(url, params={"count": min(count, 50), "offset": offset}, timeout=10)
            data = resp.json()
            chats = data.get("data", {}).get("conversations", [])
            return [
                {
                    "user_id": c.get("user_id", ""),
                    "display_name": c.get("display_name", ""),
                    "avatar": c.get("avatar", ""),
                    "last_message": c.get("last_message", ""),
                    "time": c.get("time", 0),
                }
                for c in chats
            ]
        except Exception as e:
            logger.error(f"Zalo recent chats error: {e}")
            return []

    # ─── Webhook Helper ───────────────────────────────────────────────────────

    @staticmethod
    def verify_webhook(data: str, mac: str, secret: str) -> bool:
        """Verify webhook signature từ Zalo."""
        import hmac
        import hashlib
        expected = hmac.new(
            secret.encode(), data.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, mac)
