"""
FuviAI Marketing Agent — Personalize Agent (M11)
Hyper-Personalization: CLV segmentation, dynamic content, trigger automation
"""

from __future__ import annotations

import json
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.tools.email_tool import EmailTool, EmailResult, BatchEmailResult


PERSONALIZE_SYSTEM = """Bạn là Personalization Specialist của FuviAI, chuyên tạo trải nghiệm \
cá nhân hoá cho từng khách hàng dựa trên data hành vi.

## Triết lý cá nhân hoá
- **Right Message** + **Right Person** + **Right Time** + **Right Channel**
- Personalization không chỉ là "[Tên]" — phải hiểu stage trong customer journey
- Đừng cá nhân hoá những gì khách hàng không muốn biết bạn đang theo dõi

## CLV Segments (Customer Lifetime Value)

### Tier 1 — Champions (CLV > 10 triệu)
- Ưu đãi exclusive, early access, VIP treatment
- Channel: Zalo cá nhân + email personalized

### Tier 2 — Loyals (CLV 3-10 triệu)
- Loyalty rewards, upsell nhẹ nhàng
- Channel: Email + Zalo broadcast theo tag

### Tier 3 — Potentials (CLV 500K-3 triệu)
- Nurture, education, cross-sell
- Channel: Email sequence + Facebook retargeting

### Tier 4 — At Risk (mua rồi không quay lại > 90 ngày)
- Win-back campaign, last chance offer
- Channel: Email + Zalo aggressive

### Tier 5 — Lost (> 180 ngày không tương tác)
- Re-engagement hoặc sunset
- Channel: Email cuối, không spam Zalo

## Trigger Events
Các sự kiện kích hoạt automation: abandoned_cart, first_purchase, repeat_purchase,
birthday, anniversary, inactive_30d, inactive_90d, high_value_browse, price_drop"""


# ─── CLV Calculation ──────────────────────────────────────────────────────────

def calculate_clv_tier(
    total_spent: float,
    days_since_last_purchase: int,
    purchase_count: int,
) -> str:
    """Phân loại CLV tier dựa trên hành vi mua hàng."""
    if days_since_last_purchase > 180:
        return "lost"
    if days_since_last_purchase > 90 and purchase_count < 3:
        return "at_risk"
    if total_spent > 10_000_000:
        return "champion"
    if total_spent > 3_000_000 or purchase_count >= 5:
        return "loyal"
    if total_spent > 500_000:
        return "potential"
    return "new"


class PersonalizeAgent(BaseAgent):
    """
    Agent tạo nội dung và automation cá nhân hoá theo từng segment khách hàng.

    Usage:
        agent = PersonalizeAgent()

        # Tạo email cá nhân hoá
        email = agent.personalized_email(customer, segment="champion")

        # Thiết kế automation trigger
        flow = agent.design_trigger_flow("abandoned_cart")

        # Dynamic content cho nhiều segment
        variants = agent.create_segment_variants(base_content, segments=["champion", "at_risk"])
    """

    def __init__(self):
        super().__init__(
            system_prompt=PERSONALIZE_SYSTEM,
            max_tokens=6000,
            temperature=0.5,
        )
        self._email = EmailTool()

    # ─── Customer Segmentation ────────────────────────────────────────────────

    def segment_customers(
        self,
        customers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Phân khúc danh sách khách hàng theo CLV tier.

        Args:
            customers: [{"id", "total_spent", "days_since_last_purchase", "purchase_count", "name"}, ...]

        Returns:
            {"segments": {tier: [customers]}, "ai_strategy": "..."}
        """
        segments: dict[str, list] = {
            "champion": [], "loyal": [], "potential": [],
            "at_risk": [], "lost": [], "new": [],
        }

        for c in customers:
            tier = calculate_clv_tier(
                c.get("total_spent", 0),
                c.get("days_since_last_purchase", 999),
                c.get("purchase_count", 0),
            )
            c["clv_tier"] = tier
            segments[tier].append(c)

        # Summary
        summary = {tier: len(lst) for tier, lst in segments.items()}
        logger.info(f"Customer segmentation | total={len(customers)} | segments={summary}")

        # AI strategy cho từng segment
        ai_strategy = self._segment_strategy(summary, len(customers))

        return {
            "total": len(customers),
            "segments": {tier: lst for tier, lst in segments.items() if lst},
            "summary": summary,
            "ai_strategy": ai_strategy,
        }

    def _segment_strategy(self, summary: dict[str, int], total: int) -> str:
        summary_str = "\n".join(
            f"  - {tier}: {count} KH ({count/total*100:.1f}%)"
            for tier, count in summary.items() if count > 0
        )

        prompt = f"""Đề xuất strategy cho từng segment khách hàng FuviAI:

**Phân bổ ({total} khách hàng):**
{summary_str}

Cho mỗi segment có khách hàng, đề xuất:
1. **Ưu tiên action** ngay tuần này
2. **Message chủ đạo** (1 câu)
3. **Channel + frequency** liên lạc
4. **Offer/incentive** phù hợp

Kết luận: Segment nào cần đầu tư ngay nhất để ROI tốt nhất?"""

        return self.chat(prompt, reset_history=True)

    # ─── Personalized Content ─────────────────────────────────────────────────

    def personalized_email(
        self,
        customer: dict[str, Any],
        segment: str = "potential",
        product_context: str = "FuviAI Marketing Agent",
        trigger: str = "",
    ) -> str:
        """
        Tạo email cá nhân hoá cho 1 khách hàng cụ thể.

        Args:
            customer: {"name", "total_spent", "last_product", "days_since_purchase", ...}
            segment: CLV tier
            trigger: "birthday", "abandoned_cart", "inactive_90d", "first_purchase", ...
        """
        customer_context = json.dumps(customer, ensure_ascii=False, indent=2)

        trigger_context = {
            "birthday": "Hôm nay là sinh nhật khách hàng — cơ hội tặng quà đặc biệt",
            "abandoned_cart": "Khách bỏ giỏ hàng 24h trước — nhắc nhở nhẹ nhàng",
            "inactive_90d": "Khách không mua 90 ngày — win-back campaign",
            "first_purchase": "Vừa mua lần đầu — onboarding + upsell nhẹ",
            "repeat_purchase": "Vừa mua lần 2+ — loyalty reward",
            "price_drop": "Sản phẩm họ đã xem vừa giảm giá",
            "high_value_browse": "Vừa xem sản phẩm premium nhiều lần",
        }.get(trigger, trigger)

        prompt = f"""Viết email marketing cá nhân hoá:

**Thông tin khách hàng:**
{customer_context}

**Segment:** {segment}
**Sản phẩm/Context:** {product_context}
**Trigger:** {trigger_context or 'Nurture thông thường'}

Viết email theo cấu trúc:
📌 **Subject line** (A/B: 2 options — 1 curiosity, 1 benefit-driven)
📌 **Preview text** (50 chars)

**[BODY]**
- Mở đầu cá nhân hoá (dùng tên, reference hành vi/lịch sử)
- Core message phù hợp segment ({segment})
- Social proof hoặc data point thuyết phục
- CTA rõ ràng + urgency phù hợp

**Tone:** phù hợp với segment {segment} — không quá formal, không spam-y
**Độ dài:** 150-250 chữ"""

        return self.chat(prompt, reset_history=True)

    def personalized_zalo_message(
        self,
        customer: dict[str, Any],
        segment: str,
        offer: str = "",
    ) -> str:
        """Tạo Zalo message cá nhân hoá (tối đa 200 chữ)."""
        name = customer.get("name", "bạn")
        spent = customer.get("total_spent", 0)

        prompt = f"""Viết Zalo message cá nhân hoá cho {name} (segment: {segment}):

**Dữ liệu khách:** đã chi {spent:,.0f} VNĐ | {customer.get('days_since_last_purchase', 0)} ngày chưa mua
**Offer:** {offer or 'Thông tin mới nhất về FuviAI'}

Yêu cầu:
- Tối đa 150 chữ
- Xưng tên {name} tự nhiên (không quá 1 lần)
- Phù hợp segment {segment}
- CTA có link hoặc "Nhắn tin tư vấn"
- Không bắt đầu bằng "Xin chào" hay template cứng"""

        return self.chat(prompt, reset_history=True)

    def create_segment_variants(
        self,
        base_message: str,
        segments: list[str],
        channel: str = "email",
    ) -> dict[str, str]:
        """
        Tạo nhiều biến thể content cho các segments khác nhau.
        Giữ core message nhưng adapt tone/offer/urgency theo segment.
        """
        segments_str = ", ".join(segments)

        prompt = f"""Tạo {len(segments)} biến thể của message này cho từng segment:

**Base message:**
{base_message}

**Channel:** {channel}
**Segments cần tạo:** {segments_str}

Cho mỗi segment, viết biến thể riêng (thay đổi tone, urgency, offer nếu cần):

{'---'.join([f'{chr(10)}### Variant cho segment: {s}{chr(10)}[Viết ở đây]' for s in segments])}"""

        raw = self.chat(prompt, reset_history=True)

        # Parse các variant từ response
        variants: dict[str, str] = {}
        for seg in segments:
            # Tìm section cho segment này
            marker = f"### Variant cho segment: {seg}"
            if marker in raw:
                start = raw.index(marker) + len(marker)
                # Tìm segment tiếp theo hoặc end
                next_markers = [
                    raw.index(f"### Variant cho segment: {s}")
                    for s in segments
                    if s != seg and f"### Variant cho segment: {s}" in raw
                    and raw.index(f"### Variant cho segment: {s}") > start
                ]
                end = min(next_markers) if next_markers else len(raw)
                variants[seg] = raw[start:end].strip()
            else:
                variants[seg] = raw  # Fallback

        return variants

    # ─── Trigger Automation ───────────────────────────────────────────────────

    def design_trigger_flow(
        self,
        trigger_event: str,
        product: str = "FuviAI",
        segment: str = "all",
    ) -> str:
        """
        Thiết kế automation flow cho trigger event.

        Args:
            trigger_event: "abandoned_cart" / "first_purchase" / "inactive_30d" / ...
        """
        prompt = f"""Thiết kế automation flow cho trigger: **{trigger_event}**

**Sản phẩm:** {product}
**Target segment:** {segment}

Flow chi tiết:

**⚡ TRIGGER:** {trigger_event}

**Step 1 — Immediate (0-1h):**
- Channel: ?
- Message tone: ?
- Content: (viết sample)
- Goal: ?

**Step 2 — Follow-up (24h nếu chưa convert):**
- Channel: ?
- Message: (viết sample)

**Step 3 — Last attempt (72h):**
- Channel: ?
- Message + offer cuối: (viết sample)

**Exit condition:** Convert / Unsubscribe / Timeout

**A/B test gợi ý:** Test element nào trong flow này?
**Success metric:** Đo lường bằng gì?"""

        logger.info(f"Trigger flow designed | trigger={trigger_event} | segment={segment}")
        return self.chat(prompt, reset_history=True)

    def abandoned_cart_sequence(
        self,
        cart_value: float,
        products: list[str],
        customer_name: str = "bạn",
        segment: str = "potential",
    ) -> dict[str, str]:
        """
        Tạo 3-email sequence cho abandoned cart.
        """
        products_str = ", ".join(products[:3])

        prompt = f"""Tạo abandoned cart email sequence (3 emails) cho:

**Sản phẩm bỏ giỏ:** {products_str}
**Giá trị giỏ hàng:** {cart_value:,.0f} VNĐ
**Tên khách:** {customer_name}
**Segment:** {segment}

**Email 1 — Gửi sau 1h** (gentle reminder):
Subject: ...
Body: ...

---

**Email 2 — Gửi sau 24h** (social proof + FAQ):
Subject: ...
Body: ...

---

**Email 3 — Gửi sau 72h** (last chance + offer):
Subject: ...
Body: ... [Thêm offer nhỏ nếu cart > 500K]

Tone: Natural, không spam-y, đừng làm khách cảm thấy bị "stalk"."""

        raw = self.chat(prompt, reset_history=True)

        # Split thành 3 emails
        parts = raw.split("---")
        return {
            "email_1_1h": parts[0].strip() if len(parts) > 0 else raw,
            "email_2_24h": parts[1].strip() if len(parts) > 1 else "",
            "email_3_72h": parts[2].strip() if len(parts) > 2 else "",
        }

    def birthday_campaign(
        self,
        customer_name: str,
        tier: str = "loyal",
        birthday_offer: str = "",
    ) -> dict[str, str]:
        """Tạo birthday campaign (Zalo + Email)."""
        offer = birthday_offer or "Voucher sinh nhật đặc biệt"

        prompt = f"""Tạo birthday campaign cho {customer_name} (tier: {tier}):

**Offer:** {offer}

Tạo 2 messages:

**Zalo Message (< 150 chữ):**
[Viết message Zalo ấm áp, cá nhân]

---

**Email (đầy đủ hơn):**
Subject: ...
Body: [150-200 chữ, emotional, có offer rõ ràng]

Tone: Ấm áp, chân thành — đây là ngày đặc biệt của họ, không phải dịp để hard sell."""

        raw = self.chat(prompt, reset_history=True)
        parts = raw.split("---")
        return {
            "zalo": parts[0].strip() if len(parts) > 0 else raw,
            "email": parts[1].strip() if len(parts) > 1 else "",
        }

    def upsell_recommendation(
        self,
        customer: dict[str, Any],
        current_product: str,
        available_upgrades: list[str],
    ) -> str:
        """Tạo upsell message phù hợp với lịch sử mua hàng."""
        upgrades_str = "\n".join(f"- {u}" for u in available_upgrades)

        prompt = f"""Tạo upsell recommendation tự nhiên cho khách hàng:

**Sản phẩm đang dùng:** {current_product}
**Lịch sử:** đã chi {customer.get('total_spent', 0):,.0f} VNĐ | mua {customer.get('purchase_count', 0)} lần
**Tier:** {customer.get('clv_tier', 'potential')}

**Sản phẩm upgrade có thể đề xuất:**
{upgrades_str}

Viết upsell message:
- Acknowledge giá trị hiện tại (đừng khiến họ thấy mình đang "bán thêm")
- Đặt câu hỏi hoặc nêu pain point mà upgrade sẽ giải quyết
- Đề xuất upgrade cụ thể nhất phù hợp với tier này
- CTA nhẹ nhàng: "Muốn xem thêm?" thay vì "Mua ngay"

Kênh: Email (150 chữ) — tone consultative."""

        return self.chat(prompt, reset_history=True)

    # ─── Email Sending (SendGrid) ──────────────────────────────────────────────

    def send_personalized_email(
        self,
        customer: dict[str, Any],
        segment: str = "potential",
        product_context: str = "FuviAI Marketing Agent",
        trigger: str = "",
    ) -> EmailResult:
        """
        Tạo nội dung bằng AI rồi gửi email cá nhân hoá ngay.

        Args:
            customer: {"name", "email", "total_spent", ...}
            segment: CLV tier
            trigger: "birthday" / "abandoned_cart" / "inactive_90d" / ...
        """
        to_email = customer.get("email", "")
        if not to_email or not self._email.validate_email(to_email):
            logger.warning(f"Invalid email | customer={customer.get('id', '?')}")
            return EmailResult(success=False, error="Invalid or missing email address")

        content = self.personalized_email(customer, segment, product_context, trigger)
        to_name = customer.get("name", "")

        # Extract subject line từ nội dung AI (dòng đầu có "Subject:")
        subject = f"Tin tức từ FuviAI dành cho {to_name}"
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.lower().startswith("subject:"):
                subject = stripped.split(":", 1)[1].strip().strip("*")
                # Dùng option A nếu có A/B (lấy trước dấu /)
                if "/" in subject:
                    subject = subject.split("/")[0].strip()
                break

        logger.info(f"Sending personalized email | to={to_email} | trigger={trigger or 'nurture'}")
        return self._email.send_email(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            html_content=content,
            categories=["personalized", segment, trigger or "nurture"],
            custom_args={"trigger": trigger, "segment": segment},
        )

    def send_abandoned_cart_sequence(
        self,
        customer_email: str,
        customer_name: str,
        cart_value: float,
        products: list[str],
        segment: str = "potential",
        steps: list[int] | None = None,
    ) -> dict[str, EmailResult]:
        """
        Tạo nội dung AI rồi gửi sequence abandoned cart (1, 2 hoặc 3 bước).

        Args:
            steps: Danh sách bước cần gửi — [1], [2], [3] hoặc [1,2,3]
                   Mặc định gửi bước 1 (gọi lại sau 24h để gửi bước 2, 3)
        """
        if steps is None:
            steps = [1]

        sequence = self.abandoned_cart_sequence(cart_value, products, customer_name, segment)
        step_map = {
            1: sequence.get("email_1_1h", ""),
            2: sequence.get("email_2_24h", ""),
            3: sequence.get("email_3_72h", ""),
        }

        results: dict[str, EmailResult] = {}
        for step in steps:
            content = step_map.get(step, "")
            if not content:
                results[f"step_{step}"] = EmailResult(success=False, error="Empty content")
                continue
            results[f"step_{step}"] = self._email.send_abandoned_cart(
                to_email=customer_email,
                to_name=customer_name,
                email_content=content,
                cart_value=cart_value,
                step=step,
            )
        return results

    def send_birthday_campaign(
        self,
        customer_email: str,
        customer_name: str,
        tier: str = "loyal",
        birthday_offer: str = "",
    ) -> EmailResult:
        """Tạo nội dung AI rồi gửi birthday email."""
        if not self._email.validate_email(customer_email):
            return EmailResult(success=False, error="Invalid email address")

        campaign = self.birthday_campaign(customer_name, tier, birthday_offer)
        email_content = campaign.get("email", "")
        if not email_content:
            return EmailResult(success=False, error="AI returned empty email content")

        return self._email.send_birthday(
            to_email=customer_email,
            to_name=customer_name,
            email_content=email_content,
        )

    def send_bulk_segment_email(
        self,
        customers: list[dict[str, Any]],
        base_message: str,
        subject: str,
        segments: list[str] | None = None,
    ) -> BatchEmailResult:
        """
        Tạo content variants cho từng segment rồi gửi hàng loạt.

        Args:
            customers: [{"email", "name", "clv_tier", ...}, ...]
            base_message: Nội dung gốc để AI tạo variants
            subject: Tiêu đề email
            segments: Segments cần tạo variant (mặc định: champion, loyal, potential, at_risk)
        """
        if segments is None:
            segments = ["champion", "loyal", "potential", "at_risk"]

        variants = self.create_segment_variants(base_message, segments, channel="email")

        result = BatchEmailResult()
        for c in customers:
            email = c.get("email", "")
            if not email or not self._email.validate_email(email):
                result.failed += 1
                result.errors.append(f"Invalid email: {email or 'missing'}")
                continue

            tier = c.get("clv_tier", "potential")
            content = variants.get(tier, variants.get("potential", base_message))
            res = self._email.send_email(
                to_email=email,
                to_name=c.get("name", ""),
                subject=subject,
                html_content=content,
                categories=["bulk", tier],
                custom_args={"segment": tier},
            )
            if res.success:
                result.sent += 1
            else:
                result.failed += 1
                result.errors.append(f"{email}: {res.error}")

        logger.info(f"Bulk segment email | sent={result.sent} | failed={result.failed}")
        return result
