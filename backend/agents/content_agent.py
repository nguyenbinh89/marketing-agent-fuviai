"""
FuviAI Marketing Agent — Content Agent (M1)
Viết caption Facebook, TikTok script, Zalo message, Email marketing
"""

from __future__ import annotations

from enum import Enum
from typing import Literal
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.config.prompts_vn import CONTENT_AGENT_SYSTEM


class Platform(str, Enum):
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    ZALO = "zalo"
    EMAIL = "email"


class Tone(str, Enum):
    PROFESSIONAL = "chuyen_nghiep"
    FRIENDLY = "than_thien"
    GEN_Z = "gen_z"


class ContentAgent(BaseAgent):
    """
    Agent chuyên tạo marketing content tiếng Việt.

    Usage:
        agent = ContentAgent()
        result = agent.generate_facebook_caption(
            product="Phần mềm quản lý bán hàng FuviAI",
            tone=Tone.FRIENDLY
        )
    """

    def __init__(self):
        super().__init__(
            system_prompt=CONTENT_AGENT_SYSTEM,
            max_tokens=8096,
            temperature=0.8,
        )

    # ─── Facebook ───────────────────────────────────────────────────────────

    def generate_facebook_caption(
        self,
        product: str,
        tone: Tone = Tone.FRIENDLY,
        target_audience: str = "chủ doanh nghiệp SME Việt Nam",
        key_benefit: str = "",
        cta: str = "Nhắn tin tư vấn ngay",
    ) -> str:
        tone_desc = {
            Tone.PROFESSIONAL: "chuyên nghiệp, dùng ngôn ngữ B2B",
            Tone.FRIENDLY: "thân thiện, gần gũi, dùng 'bạn/mình'",
            Tone.GEN_Z: "Gen Z, trendy, dùng từ ngữ viral TikTok VN",
        }

        prompt = f"""Viết caption Facebook cho sản phẩm/dịch vụ sau:

**Sản phẩm:** {product}
**Tone:** {tone_desc[tone]}
**Đối tượng:** {target_audience}
**Lợi ích chính:** {key_benefit or "tự xác định từ sản phẩm"}
**CTA:** {cta}

Yêu cầu:
- 300-500 chữ
- Hook mạnh câu đầu
- 3-4 đoạn ngắn
- Emoji phù hợp
- 3-5 hashtag cuối bài
- Kèm theo 1 phiên bản A/B test thay thế
- Gợi ý thời điểm đăng tốt nhất"""

        logger.info(f"Generating Facebook caption | product={product[:50]}")
        return self.chat(prompt)

    # ─── TikTok ─────────────────────────────────────────────────────────────

    def generate_tiktok_script(
        self,
        product: str,
        duration: Literal[60, 90] = 60,
        hook_style: str = "câu hỏi gây tò mò",
    ) -> str:
        prompt = f"""Viết TikTok script cho sản phẩm/dịch vụ sau:

**Sản phẩm:** {product}
**Thời lượng:** {duration} giây
**Kiểu hook:** {hook_style}

Cấu trúc bắt buộc:
[00:00-00:03] HOOK - Câu hook cực mạnh, dừng scroll ngay
[00:03-00:15] PROBLEM - Đánh vào nỗi đau của khách hàng
[00:15-00:{duration-10}] SOLUTION - Giới thiệu sản phẩm giải quyết
[00:{duration-10}:00-00:{duration}] CTA - Kêu gọi hành động + urgency

Ghi chú thêm:
- [TRANSITION] cho các cảnh chuyển
- [TEXT ON SCREEN] cho text overlay
- [SOUND CUE] cho nhạc/sound effect gợi ý
- Dùng ngôn ngữ TikTok VN tự nhiên"""

        logger.info(f"Generating TikTok script | product={product[:50]}")
        return self.chat(prompt)

    # ─── Zalo ───────────────────────────────────────────────────────────────

    def generate_zalo_message(
        self,
        product: str,
        customer_name: str = "",
        offer: str = "",
        urgency: str = "",
    ) -> str:
        name_part = f"cho khách hàng tên: {customer_name}" if customer_name else ""
        offer_part = f"Ưu đãi: {offer}" if offer else ""
        urgency_part = f"Urgency: {urgency}" if urgency else ""

        prompt = f"""Viết Zalo OA broadcast message {name_part}:

**Sản phẩm:** {product}
{offer_part}
{urgency_part}

Yêu cầu:
- Tối đa 200 chữ
- Cá nhân hoá nếu có tên khách hàng
- CTA rõ ràng (link/số điện thoại/nút)
- Không spam, tone thân thiện
- Kèm 1 bản thay thế ngắn hơn (< 100 chữ)"""

        logger.info(f"Generating Zalo message | product={product[:50]}")
        return self.chat(prompt)

    # ─── Email ──────────────────────────────────────────────────────────────

    def generate_email(
        self,
        product: str,
        target_segment: str = "khách hàng tiềm năng",
        subject_style: str = "tạo tò mò",
    ) -> str:
        prompt = f"""Viết email marketing theo cấu trúc AIDA:

**Sản phẩm/Dịch vụ:** {product}
**Đối tượng:** {target_segment}
**Subject style:** {subject_style}

Yêu cầu:
- Subject line (< 50 ký tự, không spam words)
- Preheader text (< 100 ký tự)
- Body email đầy đủ 4 phần AIDA:
  * Attention: Mở đầu gây chú ý
  * Interest: Kết nối pain point
  * Desire: Lợi ích + số liệu + social proof
  * Action: CTA button text + deadline/urgency
- Kèm 2 subject line thay thế để A/B test
- Gợi ý giờ gửi email tối ưu"""

        logger.info(f"Generating email | product={product[:50]}")
        return self.chat(prompt)

    # ─── Multi-platform ─────────────────────────────────────────────────────

    def generate_campaign_content(
        self,
        product: str,
        campaign_name: str,
        platforms: list[Platform] = None,
    ) -> dict[str, str]:
        """Tạo content cho nhiều platform cùng lúc."""
        if platforms is None:
            platforms = [Platform.FACEBOOK, Platform.ZALO]

        results = {}
        for platform in platforms:
            if platform == Platform.FACEBOOK:
                results["facebook"] = self.generate_facebook_caption(product)
            elif platform == Platform.TIKTOK:
                results["tiktok"] = self.generate_tiktok_script(product)
            elif platform == Platform.ZALO:
                results["zalo"] = self.generate_zalo_message(product)
            elif platform == Platform.EMAIL:
                results["email"] = self.generate_email(product)

        logger.info(
            f"Campaign content generated | campaign={campaign_name} | "
            f"platforms={[p.value for p in platforms]}"
        )
        return results
