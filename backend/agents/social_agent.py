"""
FuviAI Marketing Agent — Social Agent (M5)
Scheduler tự động đăng bài Zalo OA, Facebook, TikTok
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.agents.content_agent import ContentAgent, Platform, Tone
from backend.tools.zalo_tool import ZaloOATool
from backend.tools.facebook_tool import FacebookTool
from backend.config.settings import get_settings


SOCIAL_SYSTEM = """Bạn là Social Media Manager của FuviAI, chuyên lập lịch và tối ưu \
thời gian đăng bài để đạt engagement cao nhất.

## Khung giờ vàng đăng bài tại Việt Nam

### Facebook
- Sáng: 7:00-9:00 (trước giờ làm)
- Trưa: 11:30-13:30 (giờ nghỉ)
- Tối: 19:00-22:00 (sau giờ làm)
- Tốt nhất: Thứ 3, 4, 5 lúc 19:00-21:00

### TikTok
- 7:00-9:00 (sáng)
- 15:00-17:00 (chiều)
- 20:00-23:00 (tối — peak nhất)

### Zalo OA
- 7:30-9:00 (sáng — đọc tin nhắn sáng)
- 11:00-12:00 (trước ăn trưa)
- 20:00-21:30 (buổi tối)

## Nguyên tắc
- Không đăng quá 2 lần/ngày trên Facebook
- Zalo: không spam, tối đa 1 broadcast/ngày
- TikTok: 1-3 video/ngày, cách nhau ít nhất 3 giờ"""


class PostSchedule:
    """Đại diện cho 1 bài đăng đã lên lịch."""

    def __init__(
        self,
        platform: str,
        content: str,
        scheduled_time: datetime,
        status: str = "pending",
    ):
        self.platform = platform
        self.content = content
        self.scheduled_time = scheduled_time
        self.status = status  # pending / published / failed
        self.post_id: str | None = None
        self.created_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "scheduled_time": self.scheduled_time.isoformat(),
            "status": self.status,
            "post_id": self.post_id,
            "created_at": self.created_at.isoformat(),
        }


class SocialAgent(BaseAgent):
    """
    Agent quản lý lịch đăng bài cross-platform.

    Usage:
        agent = SocialAgent()

        # Lên lịch 1 tuần content
        schedule = agent.create_weekly_schedule(
            product="FuviAI",
            platforms=[Platform.FACEBOOK, Platform.ZALO]
        )

        # Đăng ngay
        agent.post_now("Caption nội dung...", platform=Platform.FACEBOOK)
    """

    def __init__(self):
        super().__init__(
            system_prompt=SOCIAL_SYSTEM,
            max_tokens=6000,
            temperature=0.5,
        )
        self._content_agent = ContentAgent()
        self._zalo = ZaloOATool()
        self._facebook = FacebookTool()
        self._schedule: list[PostSchedule] = []

    # ─── Schedule Tạo Lịch ──────────────────────────────────────────────────

    def suggest_posting_times(
        self,
        platforms: list[str],
        days: int = 7,
        posts_per_day: int = 1,
    ) -> str:
        """Claude đề xuất lịch đăng tối ưu cho tuần tới."""
        today = datetime.now().strftime("%A, %d/%m/%Y")

        prompt = f"""Lên lịch đăng bài cho {days} ngày tới (bắt đầu từ {today}):

**Platforms:** {', '.join(platforms)}
**Số bài/ngày:** {posts_per_day}

Tạo lịch chi tiết dạng bảng:
| Ngày | Giờ | Platform | Loại content | Ghi chú |
|------|-----|----------|-------------|---------|

Giải thích lý do chọn các khung giờ này.
Lưu ý các ngày đặc biệt trong tuần (cuối tuần, ngày lễ)."""

        return self.chat(prompt, reset_history=True)

    def create_weekly_schedule(
        self,
        product: str,
        platforms: list[Platform] | None = None,
        campaign_theme: str = "",
    ) -> str:
        """Tạo content plan 1 tuần đầy đủ với AI."""
        if platforms is None:
            platforms = [Platform.FACEBOOK, Platform.ZALO]

        platform_names = [p.value for p in platforms]

        prompt = f"""Tạo content plan 7 ngày cho sản phẩm/dịch vụ:

**Sản phẩm:** {product}
**Platforms:** {', '.join(platform_names)}
**Theme chiến dịch:** {campaign_theme or 'awareness + conversion'}

Cho mỗi ngày, cung cấp:
1. **Ngày/Thứ + Giờ đăng lý tưởng**
2. **Platform**
3. **Loại content** (educational / promotional / entertaining / engagement)
4. **Hook/Idea chính** (1-2 câu)
5. **CTA** cụ thể

Format bảng markdown đẹp, dễ copy vào lịch làm việc."""

        return self.chat(prompt, reset_history=True)

    # ─── Auto-posting ────────────────────────────────────────────────────────

    def post_now(
        self,
        content: str,
        platform: Platform,
        user_id: str = "",
    ) -> dict[str, Any]:
        """Đăng ngay lên platform được chỉ định."""
        result = {"platform": platform.value, "status": "failed", "data": {}}

        if platform == Platform.FACEBOOK:
            data = self._facebook.post_to_page(content)
            result["status"] = "published" if "id" in data else "failed"
            result["data"] = data

        elif platform == Platform.ZALO:
            if user_id:
                data = self._zalo.send_text_message(user_id, content)
            else:
                data = self._zalo.broadcast(content)
            result["status"] = "published" if not data.get("error") else "failed"
            result["data"] = data

        else:
            result["data"] = {"message": f"Platform {platform.value} chưa tích hợp auto-post"}

        logger.info(f"Post {result['status']} | platform={platform.value}")
        return result

    def schedule_post(
        self,
        content: str,
        platform: Platform,
        scheduled_time: datetime,
    ) -> PostSchedule:
        """Thêm bài vào hàng đợi lịch đăng."""
        post = PostSchedule(
            platform=platform.value,
            content=content,
            scheduled_time=scheduled_time,
        )
        self._schedule.append(post)
        logger.info(
            f"Post scheduled | platform={platform.value} | time={scheduled_time.isoformat()}"
        )
        return post

    def get_schedule(self, status: str | None = None) -> list[dict]:
        """Lấy danh sách lịch đăng."""
        posts = self._schedule
        if status:
            posts = [p for p in posts if p.status == status]
        return [p.to_dict() for p in posts]

    # ─── Auto-reply ──────────────────────────────────────────────────────────

    def generate_comment_reply(
        self,
        comment: str,
        brand_tone: str = "thân thiện",
        context: str = "",
    ) -> str:
        """Tạo reply comment tự động theo tone brand FuviAI."""
        prompt = f"""Viết reply comment cho FuviAI theo tone: {brand_tone}

**Comment của khách:**
"{comment}"

**Context thêm:** {context or "không có"}

Yêu cầu:
- Tự nhiên, không cứng nhắc
- Trả lời đúng trọng tâm
- Kết thúc bằng CTA nhẹ nhàng nếu phù hợp
- Dưới 100 chữ
- Đừng dùng template cứng nhắc"""

        return self.chat(prompt, reset_history=True)

    def bulk_reply_strategy(self, comments: list[str], sentiment_data: dict) -> str:
        """Strategy trả lời hàng loạt comments theo sentiment."""
        pos = sentiment_data.get("positive", 0)
        neg = sentiment_data.get("negative", 0)

        sample_neg = [c for c in comments if len(c) > 10][:5]

        prompt = f"""Tạo strategy reply comments cho FuviAI:

**Tổng quan:** {pos} tích cực / {neg} tiêu cực / {sentiment_data.get('neutral', 0)} trung tính

**Sample comments tiêu cực cần reply khéo:**
{chr(10).join(f"- {c}" for c in sample_neg)}

Cung cấp:
1. Template reply cho từng loại comment (tích cực / tiêu cực / hỏi thông tin)
2. Cách handle comment tiêu cực mà không làm escalate
3. Danh sách 5 comments cần ưu tiên reply ngay
4. Tone guide phù hợp với FuviAI brand"""

        return self.chat(prompt, reset_history=True)

    # ─── Content Repurposing ─────────────────────────────────────────────────

    def repurpose_content(
        self,
        original_content: str,
        original_platform: str,
        target_platforms: list[str],
    ) -> str:
        """Adapt content từ 1 platform sang các platform khác."""
        prompt = f"""Adapt content này từ {original_platform} sang {', '.join(target_platforms)}:

**Content gốc ({original_platform}):**
{original_content[:1500]}

Cho mỗi platform target, viết lại phù hợp với:
- Format và độ dài chuẩn của platform đó
- Tone phù hợp với audience platform đó
- CTA phù hợp
- Giữ nguyên core message nhưng adapt style"""

        return self.chat(prompt, reset_history=True)
