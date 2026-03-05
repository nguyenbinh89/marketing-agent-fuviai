"""
FuviAI Marketing Agent — Listening Agent (M7)
Social Listening real-time: trend detection + crisis alert + auto content draft
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.agents.content_agent import ContentAgent, Platform, Tone
from backend.agents.insight_agent import InsightAgent
from backend.tools.scraper_tool import ScraperTool
from backend.tools.zalo_tool import ZaloOATool


LISTENING_SYSTEM = """Bạn là Social Listening Analyst của FuviAI, theo dõi xu hướng mạng xã hội \
Việt Nam 24/7 để phát hiện trend sớm hơn đối thủ.

## Nhiệm vụ
1. **Trend Detection**: Phát hiện chủ đề đang nổi trong 6-24h — trước khi viral
2. **Crisis Monitoring**: Cảnh báo sớm khủng hoảng truyền thông
3. **Content Opportunity**: Đề xuất content ăn theo trend đang lên

## Nguyên tắc phân tích
- Phân biệt trend thật (tăng bền vững) vs spike nhất thời (noise)
- Hiểu context văn hoá VN: mùa vụ, sự kiện, ngày lễ ảnh hưởng organic trend
- Ưu tiên trend liên quan đến ngành của client (FMCG, F&B, BĐS, TMĐT)
- Sentiment tiêu cực tăng nhanh = nguy cơ khủng hoảng, cần alert ngay

## Output format
Luôn trả về JSON-compatible structure hoặc markdown có đánh số rõ ràng."""


# ─── Keyword Sets theo ngành ─────────────────────────────────────────────────

INDUSTRY_KEYWORDS: dict[str, list[str]] = {
    "fmcg": ["tiêu dùng", "siêu thị", "hàng tiêu dùng", "fmcg", "bán lẻ", "khuyến mãi"],
    "fb": ["quán ăn", "nhà hàng", "cafe", "đồ ăn", "ẩm thực", "giao đồ ăn", "food"],
    "realestate": ["bất động sản", "căn hộ", "chung cư", "đất nền", "mua nhà", "cho thuê"],
    "ecommerce": ["shopee", "tiki", "lazada", "mua online", "deal", "voucher", "flash sale"],
    "marketing": ["marketing", "quảng cáo", "digital", "ai", "automation", "content"],
}


class TrendData:
    """Dữ liệu 1 trend được phát hiện."""

    def __init__(
        self,
        keyword: str,
        source: str,
        volume: int,
        sentiment_ratio: float,
        sample_texts: list[str],
        detected_at: datetime | None = None,
    ):
        self.keyword = keyword
        self.source = source
        self.volume = volume
        self.sentiment_ratio = sentiment_ratio  # tỷ lệ positive (0-1)
        self.sample_texts = sample_texts[:5]
        self.detected_at = detected_at or datetime.now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "keyword": self.keyword,
            "source": self.source,
            "volume": self.volume,
            "sentiment_ratio": round(self.sentiment_ratio, 2),
            "sample_texts": self.sample_texts,
            "detected_at": self.detected_at.isoformat(),
        }


class ListeningAgent(BaseAgent):
    """
    Agent Social Listening — theo dõi xu hướng mạng xã hội VN.

    Usage:
        agent = ListeningAgent()

        # Chạy scan tổng hợp
        report = agent.scan_trends(industry="fmcg")

        # Monitor keywords cụ thể
        trends = agent.monitor_keywords(["#tết2027", "khuyến mãi cuối năm"])

        # Auto-tạo content ăn theo trend
        content = agent.draft_trend_content(trend_data)
    """

    def __init__(self):
        super().__init__(
            system_prompt=LISTENING_SYSTEM,
            max_tokens=6000,
            temperature=0.4,
        )
        self._scraper = ScraperTool()
        self._content_agent = ContentAgent()
        self._insight_agent = InsightAgent()
        self._zalo = ZaloOATool()
        self._trend_history: list[TrendData] = []

    # ─── Trend Detection ─────────────────────────────────────────────────────

    def scan_trends(
        self,
        industry: str = "marketing",
        hours_back: int = 24,
    ) -> dict[str, Any]:
        """
        Quét xu hướng từ nhiều nguồn trong N giờ qua.

        Returns:
            {
                "trends": [...],
                "crisis_risk": {...},
                "top_opportunity": "...",
                "scan_time": "..."
            }
        """
        logger.info(f"Scanning trends | industry={industry} | hours={hours_back}")

        keywords = INDUSTRY_KEYWORDS.get(industry, INDUSTRY_KEYWORDS["marketing"])

        # Thu thập tin tức
        raw_articles = self._collect_news_articles()

        # Lọc theo keyword ngành
        relevant = self._filter_by_keywords(raw_articles, keywords)

        # Phân tích sentiment
        texts = [a.get("title", "") for a in relevant]
        sentiment_data = {}
        if texts:
            result = self._insight_agent.analyze_sentiment(texts)
            sentiment_data = result.get("summary", {})

        # Phát hiện topics nổi bật bằng Claude
        trend_analysis = self._analyze_trends_with_ai(relevant, industry, sentiment_data)

        # Crisis check
        crisis = self._insight_agent.detect_crisis(texts)

        return {
            "industry": industry,
            "articles_found": len(relevant),
            "sentiment": sentiment_data,
            "crisis_risk": crisis,
            "trend_analysis": trend_analysis,
            "scan_time": datetime.now().isoformat(),
        }

    def monitor_keywords(
        self,
        keywords: list[str],
        sources: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Monitor danh sách keywords cụ thể.
        Trả về list trends theo thứ tự volume giảm dần.
        """
        if sources is None:
            sources = ["cafef", "vnexpress"]

        all_articles = self._collect_news_articles()
        results = []

        for kw in keywords:
            kw_lower = kw.lower().lstrip("#")
            matching = [
                a for a in all_articles
                if kw_lower in a.get("title", "").lower()
            ]

            if matching:
                texts = [a["title"] for a in matching]
                sentiment_result = self._insight_agent.analyze_sentiment(texts)
                pos = sentiment_result["summary"]["positive"]
                total = sentiment_result["summary"]["total"]
                ratio = pos / total if total > 0 else 0.5

                trend = TrendData(
                    keyword=kw,
                    source=", ".join(sources),
                    volume=len(matching),
                    sentiment_ratio=ratio,
                    sample_texts=texts[:5],
                )
                self._trend_history.append(trend)
                results.append(trend.to_dict())

        results.sort(key=lambda x: x["volume"], reverse=True)
        logger.info(f"Keywords monitored: {len(keywords)} | trends found: {len(results)}")
        return results

    def _collect_news_articles(self) -> list[dict[str, str]]:
        """Thu thập bài viết từ CafeF và VnExpress."""
        articles = []
        try:
            articles.extend(self._scraper.scrape_cafef_headlines(max_articles=15))
        except Exception as e:
            logger.warning(f"CafeF scrape failed: {e}")
        try:
            articles.extend(self._scraper.scrape_vnexpress_business(max_articles=15))
        except Exception as e:
            logger.warning(f"VnExpress scrape failed: {e}")
        return articles

    def _filter_by_keywords(
        self,
        articles: list[dict],
        keywords: list[str],
    ) -> list[dict]:
        """Lọc bài viết có chứa ít nhất 1 keyword."""
        result = []
        for article in articles:
            title_lower = article.get("title", "").lower()
            if any(kw.lower() in title_lower for kw in keywords):
                result.append(article)
        return result

    def _analyze_trends_with_ai(
        self,
        articles: list[dict],
        industry: str,
        sentiment: dict,
    ) -> str:
        """Dùng Claude phân tích trend từ danh sách bài viết."""
        if not articles:
            return "Không đủ dữ liệu để phân tích trend."

        titles = "\n".join(f"- {a['title']} ({a.get('source', '')})" for a in articles[:20])
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)

        prompt = f"""Phân tích xu hướng ngành {industry.upper()} từ {len(articles)} bài báo VN gần đây:

**Sentiment:** {pos} tích cực / {neg} tiêu cực / {sentiment.get('neutral', 0)} trung tính

**Tin tức:**
{titles}

Phân tích:
1. **Top 3 xu hướng đang nổi** (xếp theo momentum — tăng nhanh nhất)
2. **Chủ đề nào có thể viral trong 48h tới** và lý do
3. **Cơ hội content** — 2 ý tưởng cụ thể có thể tạo ngay hôm nay
4. **Rủi ro** — có chủ đề nào nhạy cảm cần tránh không?"""

        return self.chat(prompt, reset_history=True)

    # ─── Content Draft from Trend ─────────────────────────────────────────────

    def draft_trend_content(
        self,
        trend: dict[str, Any],
        platform: Platform = Platform.FACEBOOK,
        tone: Tone = Tone.FRIENDLY,
    ) -> str:
        """
        Tự động tạo content ăn theo trend vừa phát hiện.

        Args:
            trend: TrendData.to_dict() hoặc dict có "keyword" + "sample_texts"
        """
        keyword = trend.get("keyword", "")
        samples = trend.get("sample_texts", [])
        samples_str = "\n".join(f"- {t}" for t in samples[:3])

        prompt = f"""Tạo content ăn theo trend đang hot:

**Trend:** {keyword}
**Nguồn tin tức liên quan:**
{samples_str}

Yêu cầu:
- Platform: {platform.value}
- Tone: {tone.value}
- Content phải liên quan đến FuviAI (AI Marketing Automation)
- Ăn theo trend nhưng không copy, tạo góc nhìn độc đáo của FuviAI
- Thêm CTA phù hợp

Chỉ viết content, không giải thích thêm."""

        content = self._content_agent.chat(prompt, reset_history=True)
        logger.info(f"Trend content drafted | keyword={keyword} | platform={platform.value}")
        return content

    def draft_multi_platform(
        self,
        trend: dict[str, Any],
    ) -> dict[str, str]:
        """Tạo content ăn theo trend cho nhiều platform cùng lúc."""
        return {
            "facebook": self.draft_trend_content(trend, Platform.FACEBOOK, Tone.FRIENDLY),
            "tiktok": self.draft_trend_content(trend, Platform.TIKTOK, Tone.GENZ),
            "zalo": self.draft_trend_content(trend, Platform.ZALO, Tone.PROFESSIONAL),
        }

    # ─── Crisis Alert ─────────────────────────────────────────────────────────

    def check_and_alert_crisis(
        self,
        texts: list[str],
        alert_zalo_user: str = "",
    ) -> dict[str, Any]:
        """
        Kiểm tra khủng hoảng và gửi alert Zalo OA nếu cần.

        Args:
            texts: Danh sách comments/posts cần check
            alert_zalo_user: User ID Zalo để nhận alert (để trống = không gửi)
        """
        crisis = self._insight_agent.detect_crisis(texts)

        if crisis["is_crisis"]:
            severity = crisis["severity"]
            emoji = "🚨" if severity == "high" else "⚠️"
            alert_msg = (
                f"{emoji} FUVIAI CRISIS ALERT\n"
                f"Mức độ: {severity.upper()}\n"
                f"Tỷ lệ tiêu cực: {crisis['negative_ratio']:.0%} "
                f"({crisis['negative_count']}/{crisis['total']} comments)\n"
                f"Thời gian: {datetime.now().strftime('%H:%M %d/%m/%Y')}\n"
                f"Hành động: Kiểm tra ngay và có phản hồi trong 30 phút."
            )

            logger.warning(f"CRISIS ALERT | severity={severity} | neg_ratio={crisis['negative_ratio']:.1%}")

            if alert_zalo_user:
                zalo_result = self._zalo.send_text_message(alert_zalo_user, alert_msg)
                crisis["zalo_alert_sent"] = not zalo_result.get("error")
                crisis["alert_message"] = alert_msg
            else:
                crisis["alert_message"] = alert_msg

        return crisis

    def generate_crisis_response(
        self,
        crisis_context: str,
        brand: str = "FuviAI",
    ) -> str:
        """Tạo statement phản hồi khủng hoảng truyền thông."""
        prompt = f"""Viết statement phản hồi khủng hoảng truyền thông cho {brand}:

**Tình huống:**
{crisis_context}

Viết:
1. **Immediate statement** (đăng ngay trong 30 phút — thừa nhận, không biện minh)
2. **Follow-up post** (sau 2-4 giờ — giải thích + action plan)
3. **Private reply template** (cho từng người comment tiêu cực)

Tone: Chân thành, không defensive, thể hiện trách nhiệm."""

        return self.chat(prompt, reset_history=True)

    # ─── Scheduled Job Helper ─────────────────────────────────────────────────

    def run_scheduled_scan(
        self,
        industry: str = "marketing",
        crisis_alert_zalo: str = "",
    ) -> dict[str, Any]:
        """
        Entry point cho Celery task — chạy mỗi 30 phút.
        Trả về kết quả đầy đủ để lưu DB.
        """
        result = self.scan_trends(industry=industry, hours_back=1)

        # Lấy texts từ articles để crisis check
        articles = self._collect_news_articles()
        texts = [a.get("title", "") for a in articles if a.get("title")]

        if texts and crisis_alert_zalo:
            crisis = self.check_and_alert_crisis(texts, alert_zalo_user=crisis_alert_zalo)
            result["crisis_check"] = crisis

        result["job_type"] = "scheduled_scan"
        result["interval_minutes"] = 30
        return result

    def get_trend_history(self, limit: int = 20) -> list[dict]:
        """Lấy lịch sử trends đã phát hiện."""
        return [t.to_dict() for t in self._trend_history[-limit:]]
