"""
FuviAI Marketing Agent — Insight Agent (M6)
Customer Insights + Sentiment Analysis tiếng Việt (Bắc/Trung/Nam)
"""

from __future__ import annotations

import re
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.config.prompts_vn import FUVIAI_SYSTEM_PROMPT

# Lazy import underthesea (optional)
try:
    from underthesea import sentiment, word_tokenize
    _UNDERTHESEA_AVAILABLE = True
except ImportError:
    _UNDERTHESEA_AVAILABLE = False
    logger.warning("underthesea chưa cài — dùng rule-based sentiment fallback")


INSIGHT_SYSTEM = """Bạn là Customer Insight Analyst của FuviAI, chuyên phân tích \
hành vi khách hàng và sentiment tiếng Việt.

## Chuyên môn
- Phân tích sentiment tiếng Việt: hiểu ngữ cảnh, phương ngữ, slang
- Customer segmentation theo RFM (Recency, Frequency, Monetary)
- Voice of Customer: tổng hợp feedback thành insight hành động được

## Phương ngữ hiểu được
- **Miền Nam**: "thiệt ra", "ngu quá", "đỉnh của chóp", "chanh sả", "chất lừ", "bắt trend"
- **Miền Bắc**: "quá xịn", "đỉnh thật", "tuyệt vời", "chuẩn bài"
- **Gen Z**: "hết hồn", "xịn sò", "ib inbox", "dm", "thả tim", "đỉnh nóc"
- Hiểu irony và sarcasm trong tiếng Việt

## Output
Luôn kết thúc bằng "Insight hành động" — ít nhất 2 việc cụ thể có thể làm ngay."""


# ─── Rule-based Sentiment (fallback) ────────────────────────────────────────

POSITIVE_WORDS = {
    "tốt", "hay", "đỉnh", "xịn", "tuyệt", "ổn", "ok", "được", "thích",
    "yêu", "xuất sắc", "hoàn hảo", "chất", "ngon", "recommend", "gợi ý",
    "đỉnh của chóp", "chanh sả", "chất lừ", "xịn sò", "hết hồn tích cực",
    "chuẩn", "ưng", "hài lòng", "satisfied", "amazing", "great",
}

NEGATIVE_WORDS = {
    "tệ", "kém", "dở", "chán", "xấu", "fail", "lỗi", "bug", "hỏng",
    "tệ quá", "thất vọng", "disappointed", "sad", "buồn", "mệt",
    "chậm", "lag", "crash", "không được", "không ổn", "bóc phốt",
    "scam", "lừa đảo", "thất bại", "phàn nàn",
}


def _rule_based_sentiment(text: str) -> str:
    text_lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    if pos > neg:
        return "positive"
    elif neg > pos:
        return "negative"
    return "neutral"


class InsightAgent(BaseAgent):
    """
    Agent phân tích customer insights và sentiment tiếng Việt.

    Usage:
        agent = InsightAgent()
        result = agent.analyze_sentiment(["Sản phẩm quá tốt!", "Giao hàng chậm quá"])
        rfm = agent.rfm_segmentation(customer_data)
    """

    def __init__(self):
        super().__init__(
            system_prompt=INSIGHT_SYSTEM,
            max_tokens=6000,
            temperature=0.2,
        )

    # ─── Sentiment Analysis ──────────────────────────────────────────────────

    def analyze_sentiment(self, texts: list[str]) -> dict[str, Any]:
        """
        Phân tích sentiment cho list comments/reviews.

        Returns:
            {
                "summary": {"positive": N, "negative": N, "neutral": N},
                "details": [{"text": ..., "sentiment": ..., "score": ...}],
                "top_positive": [...],
                "top_negative": [...],
                "ai_insight": "..."
            }
        """
        results = []
        for text in texts:
            if _UNDERTHESEA_AVAILABLE:
                try:
                    label = sentiment(text)
                    sent = "positive" if "pos" in label.lower() else (
                        "negative" if "neg" in label.lower() else "neutral"
                    )
                except Exception:
                    sent = _rule_based_sentiment(text)
            else:
                sent = _rule_based_sentiment(text)

            results.append({"text": text, "sentiment": sent})

        summary = {
            "positive": sum(1 for r in results if r["sentiment"] == "positive"),
            "negative": sum(1 for r in results if r["sentiment"] == "negative"),
            "neutral": sum(1 for r in results if r["sentiment"] == "neutral"),
            "total": len(results),
        }

        top_pos = [r["text"] for r in results if r["sentiment"] == "positive"][:3]
        top_neg = [r["text"] for r in results if r["sentiment"] == "negative"][:3]

        # Dùng Claude để phân tích sâu hơn
        sample = results[:20]  # Giới hạn để không tốn quá nhiều token
        ai_insight = self._get_ai_insight(sample, summary)

        logger.info(f"Sentiment analysis | total={len(texts)} | pos={summary['positive']} neg={summary['negative']}")

        return {
            "summary": summary,
            "details": results,
            "top_positive": top_pos,
            "top_negative": top_neg,
            "ai_insight": ai_insight,
        }

    def _get_ai_insight(self, sample: list[dict], summary: dict) -> str:
        prompt = f"""Phân tích sentiment feedback từ khách hàng Việt Nam:

**Tổng quan:** {summary['positive']} tích cực / {summary['negative']} tiêu cực / {summary['neutral']} trung tính

**Mẫu feedback:**
{chr(10).join(f"- [{r['sentiment'].upper()}] {r['text']}" for r in sample)}

Cung cấp:
1. Chủ đề chính được đề cập (top 3)
2. Pain points lặp lại nhiều nhất
3. Điểm khách hàng đánh giá cao nhất
4. Insight hành động: 2 việc cần làm ngay trong tuần này"""

        return self.chat(prompt, reset_history=True)

    def analyze_single(self, text: str) -> dict[str, str]:
        """Phân tích sentiment 1 comment nhanh."""
        if _UNDERTHESEA_AVAILABLE:
            try:
                label = sentiment(text)
                sent = "positive" if "pos" in label.lower() else (
                    "negative" if "neg" in label.lower() else "neutral"
                )
            except Exception:
                sent = _rule_based_sentiment(text)
        else:
            sent = _rule_based_sentiment(text)
        return {"text": text, "sentiment": sent}

    # ─── Customer Segmentation ───────────────────────────────────────────────

    def rfm_segmentation(self, customer_data: list[dict[str, Any]]) -> str:
        """
        Phân khúc khách hàng theo RFM.

        Args:
            customer_data: list of {"customer_id", "last_purchase_days", "frequency", "total_spent"}
        """
        import json as _json

        prompt = f"""Phân tích RFM segmentation cho {len(customer_data)} khách hàng FuviAI:

**Dữ liệu mẫu (top 10):**
{_json.dumps(customer_data[:10], ensure_ascii=False, indent=2)}

Thực hiện:
1. Phân loại thành 5 segment: Champions / Loyal / At Risk / Need Attention / Lost
2. Số lượng và % khách trong mỗi segment
3. Strategy cụ thể cho từng segment (message, offer, channel)
4. Priority action: segment nào cần xử lý ngay nhất và tại sao"""

        logger.info(f"RFM segmentation | customers={len(customer_data)}")
        return self.chat(prompt, reset_history=True)

    # ─── Voice of Customer ───────────────────────────────────────────────────

    def voice_of_customer(
        self,
        feedbacks: list[str],
        source: str = "tổng hợp",
    ) -> str:
        """Tổng hợp Voice of Customer từ nhiều nguồn."""
        combined = "\n".join(f"- {f}" for f in feedbacks[:50])

        prompt = f"""Tổng hợp Voice of Customer từ {len(feedbacks)} feedback ({source}):

{combined}

Báo cáo VOC:
1. **Jobs to be done**: Khách đang cố làm gì?
2. **Pain points** (xếp theo tần suất xuất hiện)
3. **Delighters**: Điều gì khiến họ vui bất ngờ?
4. **Unmet needs**: Nhu cầu chưa được đáp ứng
5. **Exact words**: Trích dẫn nguyên văn 5 câu có thể dùng trong marketing copy
6. **Insight hành động**: 3 việc cụ thể"""

        return self.chat(prompt, reset_history=True)

    # ─── Crisis Detection ─────────────────────────────────────────────────────

    def detect_crisis(self, texts: list[str], threshold: float = 0.3) -> dict[str, Any]:
        """
        Phát hiện khủng hoảng truyền thông từ batch comments.
        Trả về {"is_crisis": bool, "severity": "high/medium/low", "reason": str}
        """
        if not texts:
            return {"is_crisis": False, "severity": "none", "reason": "Không có dữ liệu"}

        neg_count = sum(
            1 for t in texts
            if _rule_based_sentiment(t) == "negative"
        )
        neg_ratio = neg_count / len(texts)

        crisis_keywords = ["scam", "lừa đảo", "bóc phốt", "tẩy chay", "báo", "kiện", "hoàn tiền"]
        has_crisis_kw = any(
            kw in t.lower() for t in texts for kw in crisis_keywords
        )

        is_crisis = neg_ratio > threshold or has_crisis_kw
        severity = "high" if neg_ratio > 0.5 or has_crisis_kw else (
            "medium" if neg_ratio > threshold else "low"
        )

        logger.warning(f"Crisis check | neg_ratio={neg_ratio:.1%} | is_crisis={is_crisis}")

        return {
            "is_crisis": is_crisis,
            "severity": severity,
            "negative_ratio": round(neg_ratio, 3),
            "negative_count": neg_count,
            "total": len(texts),
            "has_crisis_keywords": has_crisis_kw,
        }
