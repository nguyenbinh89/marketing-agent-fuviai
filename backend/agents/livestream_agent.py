"""
FuviAI Marketing Agent — Livestream Agent (M8)
Real-time AI Coach cho buổi livestream: script gợi ý, auto-reply, flash deal timing
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.agents.insight_agent import InsightAgent


LIVESTREAM_SYSTEM = """Bạn là Livestream AI Coach của FuviAI, hỗ trợ host bán hàng livestream \
trên TikTok Shop, Facebook Live, Shopee Live.

## Vai trò real-time
- **Script Coach**: Gợi ý lời thoại tiếp theo dựa trên phản hồi viewer
- **Deal Timing**: Xác định thời điểm tốt nhất để tung flash deal / voucher
- **Momentum Manager**: Phát hiện khi engagement drop và đề xuất cách kéo lại
- **Comment Handler**: Trả lời hàng loạt comment theo tone brand

## Nguyên tắc Livestream VN
- Hook mạnh trong 30 giây đầu: "Ai đang xem tới đây để lại tim cho mình"
- Tạo FOMO: "Chỉ còn X suất", "Deal này tắt sau 10 phút"
- Kêu gọi tương tác liên tục: "Share cho bạn bè", "Tag người cần cái này"
- Xử lý comment tiêu cực nhanh, chuyển sang positive ngay
- Peak time TikTok: 20:00-22:30 — đây là golden hour

## Response format
Luôn ngắn gọn, actionable, có thể đọc ngay trong 5 giây."""


# ─── Livestream Session State ─────────────────────────────────────────────────

class LivestreamSession:
    """Trạng thái của 1 buổi livestream đang diễn ra."""

    def __init__(self, product: str, platform: str, target_revenue: float = 0):
        self.product = product
        self.platform = platform
        self.target_revenue = target_revenue
        self.start_time = datetime.now()
        self.peak_viewers = 0
        self.current_viewers = 0
        self.revenue_achieved = 0.0
        self.flash_deals_used: list[dict] = []
        self.script_history: list[str] = []
        self.alerts: list[dict] = []

    def elapsed_minutes(self) -> int:
        return int((datetime.now() - self.start_time).total_seconds() / 60)

    def viewer_drop_percent(self, previous: int) -> float:
        if previous <= 0:
            return 0.0
        return (previous - self.current_viewers) / previous * 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "product": self.product,
            "platform": self.platform,
            "elapsed_minutes": self.elapsed_minutes(),
            "current_viewers": self.current_viewers,
            "peak_viewers": self.peak_viewers,
            "revenue_achieved": self.revenue_achieved,
            "target_revenue": self.target_revenue,
            "flash_deals_used": len(self.flash_deals_used),
            "start_time": self.start_time.isoformat(),
        }


class LivestreamAgent(BaseAgent):
    """
    Agent AI Coach hỗ trợ livestream bán hàng real-time.

    Usage:
        agent = LivestreamAgent()
        session = agent.start_session("FuviAI Gói Pro", "tiktok", target_revenue=50_000_000)

        # Real-time gợi ý script
        script = agent.suggest_next_script(session, current_viewers=500, comments=["giá bao nhiêu?"])

        # Tung flash deal
        deal = agent.trigger_flash_deal(session, discount_percent=30, slots=50)
    """

    def __init__(self):
        super().__init__(
            system_prompt=LIVESTREAM_SYSTEM,
            max_tokens=2048,  # Nhỏ để response nhanh
            temperature=0.6,
        )
        self._insight_agent = InsightAgent()
        self._active_sessions: dict[str, LivestreamSession] = {}

    # ─── Session Management ──────────────────────────────────────────────────

    def start_session(
        self,
        product: str,
        platform: str = "tiktok",
        target_revenue: float = 0,
        session_id: str = "",
    ) -> LivestreamSession:
        """Bắt đầu buổi livestream mới."""
        sid = session_id or f"{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session = LivestreamSession(product, platform, target_revenue)
        self._active_sessions[sid] = session
        logger.info(f"Livestream session started | id={sid} | product={product} | platform={platform}")
        return session

    def get_session(self, session_id: str) -> LivestreamSession | None:
        return self._active_sessions.get(session_id)

    def end_session(self, session_id: str) -> dict[str, Any]:
        """Kết thúc livestream, tạo summary."""
        session = self._active_sessions.pop(session_id, None)
        if not session:
            return {"error": "Session không tồn tại"}
        summary = self.generate_session_summary(session)
        logger.info(f"Livestream session ended | id={session_id} | elapsed={session.elapsed_minutes()}min")
        return {"session": session.to_dict(), "summary": summary}

    # ─── Real-time Script Suggestions ────────────────────────────────────────

    def suggest_next_script(
        self,
        session: LivestreamSession,
        current_viewers: int,
        comments: list[str] | None = None,
        revenue_this_segment: float = 0,
    ) -> str:
        """
        Gợi ý lời thoại tiếp theo trong < 2 giây.
        Tự động điều chỉnh theo momentum hiện tại.

        Args:
            current_viewers: Số viewer đang xem
            comments: 5-10 comments gần nhất
            revenue_this_segment: Doanh thu 10 phút vừa qua
        """
        prev_viewers = session.current_viewers
        session.current_viewers = current_viewers
        session.peak_viewers = max(session.peak_viewers, current_viewers)

        drop = session.viewer_drop_percent(prev_viewers)
        elapsed = session.elapsed_minutes()

        # Phân tích comment sentiment
        sentiment_str = ""
        if comments:
            sentiment = self._insight_agent.analyze_sentiment(comments[:10])
            pos = sentiment["summary"]["positive"]
            neg = sentiment["summary"]["negative"]
            sentiment_str = f"Comment: {pos} tích cực / {neg} tiêu cực"
            top_questions = [c for c in comments if "?" in c][:3]
        else:
            top_questions = []

        phase = self._get_stream_phase(elapsed)

        prompt = f"""REAL-TIME SCRIPT — Gợi ý lời thoại NGAY BÂY cho host:

**Sản phẩm:** {session.product} | **Platform:** {session.platform}
**Thời điểm:** phút {elapsed} | **Phase:** {phase}
**Viewers:** {current_viewers} ({f'giảm {drop:.0f}%' if drop > 10 else 'ổn định'})
**Doanh thu đoạn này:** {revenue_this_segment:,.0f} VNĐ
{sentiment_str}
{f'Câu hỏi đang được hỏi nhiều: {chr(10).join(top_questions)}' if top_questions else ''}

Gợi ý script ngắn (50-80 chữ, đọc được ngay):
1. **Câu mở** (nếu viewer vừa vào)
2. **Core message** phù hợp với phase hiện tại
3. **CTA ngay** — 1 hành động cụ thể
{f'4. **Xử lý câu hỏi**: {top_questions[0]}' if top_questions else ''}

⚡ Tối ưu cho {session.platform.upper()} — ngắn, năng lượng cao."""

        script = self.chat(prompt, reset_history=True)
        session.script_history.append(script)
        return script

    def _get_stream_phase(self, elapsed_minutes: int) -> str:
        if elapsed_minutes < 5:
            return "WARM-UP (thu hút viewer)"
        elif elapsed_minutes < 15:
            return "BUILD-UP (giới thiệu sản phẩm)"
        elif elapsed_minutes < 30:
            return "PEAK (đẩy doanh số)"
        elif elapsed_minutes < 50:
            return "SUSTAIN (giữ momentum)"
        else:
            return "CLOSE (tạo urgency cuối stream)"

    def handle_viewer_drop(
        self,
        session: LivestreamSession,
        drop_percent: float,
    ) -> str:
        """
        Chiến thuật khẩn cấp khi viewer drop > 20%.
        Trả về script kéo lại viewer NGAY.
        """
        prompt = f"""🚨 EMERGENCY: Viewer đang drop {drop_percent:.0f}%!

Platform: {session.platform} | Phút {session.elapsed_minutes()}
Viewers hiện tại: {session.current_viewers} / Peak: {session.peak_viewers}

Viết script khẩn cấp để kéo lại viewer (max 60 chữ):
- Tạo pattern interrupt ngay lập tức
- Hook mạnh cho người đang scroll qua
- Tease deal/surprise sắp tới
- Kêu gọi share ngay

Chỉ viết script, không giải thích."""

        logger.warning(f"Viewer drop alert | session={session.product} | drop={drop_percent:.0f}%")
        return self.chat(prompt, reset_history=True)

    # ─── Flash Deal Management ────────────────────────────────────────────────

    def trigger_flash_deal(
        self,
        session: LivestreamSession,
        discount_percent: int,
        slots: int,
        duration_minutes: int = 10,
    ) -> dict[str, Any]:
        """
        Tạo script tung flash deal + tracking.

        Returns:
            {"script": "...", "deal_info": {...}, "timing_advice": "..."}
        """
        elapsed = session.elapsed_minutes()
        viewers = session.current_viewers

        # Kiểm tra timing có hợp lý không
        timing_score = self._evaluate_deal_timing(elapsed, viewers, session.peak_viewers)

        prompt = f"""Tung FLASH DEAL ngay bây giờ:

🔥 **Deal:** Giảm {discount_percent}% | Chỉ {slots} suất | Hết sau {duration_minutes} phút
📍 **Sản phẩm:** {session.product}
👥 **Viewers:** {viewers} người đang xem

Viết script tung deal (80-100 chữ):
1. Câu shock announcement
2. Nhấn mạnh giới hạn (slots + thời gian)
3. Hướng dẫn mua ngay (pinned comment / link)
4. Countdown energy: "3... 2... 1... OPEN!"

Tone: cực kỳ hứng khởi, năng lượng max."""

        script = self.chat(prompt, reset_history=True)

        deal_record = {
            "discount_percent": discount_percent,
            "slots": slots,
            "duration_minutes": duration_minutes,
            "triggered_at": datetime.now().isoformat(),
            "viewers_at_trigger": viewers,
            "elapsed_minutes": elapsed,
        }
        session.flash_deals_used.append(deal_record)

        return {
            "script": script,
            "deal_info": deal_record,
            "timing_advice": timing_score,
        }

    def _evaluate_deal_timing(
        self, elapsed: int, viewers: int, peak: int
    ) -> str:
        """Đánh giá timing tung deal có tốt không."""
        ratio = viewers / peak if peak > 0 else 1.0
        if elapsed < 10:
            return "⚠️ Hơi sớm — viewer chưa warm up đủ. Đợi thêm 5-10 phút."
        elif ratio < 0.5:
            return "⚠️ Viewer đang thấp. Deal có thể không hiệu quả — cân nhắc kéo viewer trước."
        elif 15 <= elapsed <= 40 and ratio >= 0.7:
            return "✅ Timing tốt! Đây là thời điểm vàng để tung deal."
        else:
            return "✅ OK để tung deal."

    def suggest_deal_schedule(
        self,
        session: LivestreamSession,
        total_deals: int = 3,
        stream_duration: int = 60,
    ) -> str:
        """Lên lịch tung deals tối ưu cho cả buổi stream."""
        prompt = f"""Lên kế hoạch tung flash deals cho buổi livestream {stream_duration} phút:

**Sản phẩm:** {session.product} | **Platform:** {session.platform}
**Số deals:** {total_deals}

Tạo lịch tối ưu:
| Phút | Deal | Discount | Slots | Lý do chọn thời điểm này |
|------|------|----------|-------|--------------------------|

Nguyên tắc:
- Deal 1: phút 15-20 (warm up xong)
- Deal peak: phút 25-35 (viewer cao nhất)
- Deal cuối: 10 phút trước khi kết thúc (urgency)
- Khoảng cách tối thiểu 10 phút giữa các deals"""

        return self.chat(prompt, reset_history=True)

    # ─── Comment Auto-reply ───────────────────────────────────────────────────

    def batch_reply_comments(
        self,
        comments: list[str],
        product_info: str = "",
        brand_tone: str = "thân thiện, năng lượng cao",
    ) -> list[dict[str, str]]:
        """
        Tạo reply cho nhiều comments cùng lúc.
        Phân loại: câu hỏi về giá, ship, sản phẩm, khiếu nại.
        """
        if not comments:
            return []

        comments_str = "\n".join(f"{i+1}. {c}" for i, c in enumerate(comments[:15]))

        prompt = f"""Tạo reply nhanh cho {len(comments[:15])} comments livestream:

**Context sản phẩm:** {product_info or session if hasattr(self, '_session') else 'Sản phẩm FuviAI'}
**Tone:** {brand_tone}

**Comments:**
{comments_str}

Cho mỗi comment, reply ngắn (< 20 chữ), natural, có emoji phù hợp.
Format JSON:
[
  {{"comment_index": 1, "reply": "..."}},
  ...
]

Chỉ trả về JSON array, không giải thích."""

        raw = self.chat(prompt, reset_history=True)

        # Parse JSON từ response
        try:
            import re
            json_match = re.search(r'\[.*\]', raw, re.DOTALL)
            if json_match:
                replies = json.loads(json_match.group())
                return [
                    {"comment": comments[r["comment_index"] - 1], "reply": r["reply"]}
                    for r in replies
                    if 0 < r.get("comment_index", 0) <= len(comments)
                ]
        except Exception as e:
            logger.warning(f"JSON parse failed for replies: {e}")

        # Fallback: trả về raw text
        return [{"comment": c, "reply": raw} for c in comments[:3]]

    # ─── Session Summary ──────────────────────────────────────────────────────

    def generate_session_summary(self, session: LivestreamSession) -> str:
        """Tạo báo cáo tổng kết sau livestream."""
        deals_str = json.dumps(session.flash_deals_used, ensure_ascii=False, indent=2)

        prompt = f"""Tạo báo cáo tổng kết buổi livestream:

**Sản phẩm:** {session.product} | **Platform:** {session.platform}
**Thời lượng:** {session.elapsed_minutes()} phút
**Peak viewers:** {session.peak_viewers}
**Doanh thu đạt được:** {session.revenue_achieved:,.0f} / {session.target_revenue:,.0f} VNĐ
**Flash deals đã dùng:** {len(session.flash_deals_used)}
{f'**Chi tiết deals:**{chr(10)}{deals_str}' if session.flash_deals_used else ''}

Báo cáo:
📊 **LIVESTREAM SUMMARY**
- KPI đạt được vs mục tiêu
- Top 3 điểm mạnh buổi stream
- Top 3 điểm cần cải thiện
- Thời điểm engagement cao nhất và lý do
- Gợi ý cho buổi stream tiếp theo"""

        return self.chat(prompt, reset_history=True)

    def prepare_stream_script(
        self,
        product: str,
        platform: str = "tiktok",
        duration_minutes: int = 60,
        target_revenue: float = 0,
    ) -> str:
        """Tạo script khung cho buổi stream trước khi bắt đầu."""
        prompt = f"""Tạo script khung cho buổi livestream bán hàng:

**Sản phẩm:** {product}
**Platform:** {platform.upper()}
**Thời lượng:** {duration_minutes} phút
**Mục tiêu doanh thu:** {f'{target_revenue:,.0f} VNĐ' if target_revenue else 'Không giới hạn'}

Script theo timeline:
| Phút | Segment | Script mẫu | Notes |
|------|---------|-----------|-------|

Bao gồm:
- Opening hook (0-30 giây)
- Giới thiệu sản phẩm (demo key features)
- Social proof (review khách hàng cũ)
- Deal announcement timing
- Closing urgency
- Backup script nếu viewer drop"""

        return self.chat(prompt, reset_history=True)

    def list_sessions(self) -> list[dict]:
        return [
            {"session_id": sid, **s.to_dict()}
            for sid, s in self._active_sessions.items()
        ]
