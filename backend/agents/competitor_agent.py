"""
FuviAI Marketing Agent — Competitor Agent (M10)
Competitor Intelligence: crawl website + fanpage đối thủ, diff detection,
engagement comparison, auto counter-strategy
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.tools.scraper_tool import ScraperTool


COMPETITOR_SYSTEM = """Bạn là Competitive Intelligence Analyst của FuviAI, theo dõi và phân tích \
đối thủ cạnh tranh để giúp FuviAI luôn đi trước một bước.

## Phương pháp phân tích
- **Pricing Intelligence**: Theo dõi thay đổi giá, phát hiện discount > 15% ngay lập tức
- **Content Intelligence**: Phân tích loại content đối thủ đang đẩy mạnh
- **Campaign Detection**: Nhận diện khi đối thủ launch big campaign
- **Weakness Spotting**: Tìm điểm yếu trong strategy của đối thủ để exploit

## Output
Mỗi phân tích phải kết thúc bằng **Counter-Strategy** — hành động cụ thể FuviAI nên làm ngay.
Không phân tích chung chung, phải có số liệu và timeline cụ thể."""


class CompetitorProfile:
    """Profile của 1 đối thủ cạnh tranh."""

    def __init__(
        self,
        name: str,
        website: str,
        facebook_page: str = "",
        industry: str = "",
    ):
        self.name = name
        self.website = website
        self.facebook_page = facebook_page
        self.industry = industry
        self.snapshots: list[dict[str, Any]] = []
        self.last_checked: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "website": self.website,
            "facebook_page": self.facebook_page,
            "industry": self.industry,
            "snapshots_count": len(self.snapshots),
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
        }


class CompetitorAgent(BaseAgent):
    """
    Agent theo dõi đối thủ cạnh tranh tự động.

    Usage:
        agent = CompetitorAgent()

        # Thêm đối thủ cần theo dõi
        agent.add_competitor("Đối thủ A", "https://doithua.com")

        # Chạy scan hàng ngày
        report = agent.daily_scan()

        # Phân tích sâu 1 đối thủ
        analysis = agent.analyze_competitor("Đối thủ A")

        # Counter-strategy khi đối thủ launch campaign lớn
        strategy = agent.generate_counter_strategy("Đối thủ A", "Vừa giảm giá 30%")
    """

    def __init__(self):
        super().__init__(
            system_prompt=COMPETITOR_SYSTEM,
            max_tokens=8096,
            temperature=0.3,
        )
        self._scraper = ScraperTool()
        self._competitors: dict[str, CompetitorProfile] = {}

    # ─── Competitor Management ────────────────────────────────────────────────

    def add_competitor(
        self,
        name: str,
        website: str,
        facebook_page: str = "",
        industry: str = "general",
    ) -> CompetitorProfile:
        """Thêm đối thủ vào danh sách theo dõi."""
        profile = CompetitorProfile(name, website, facebook_page, industry)
        self._competitors[name] = profile
        logger.info(f"Competitor added: {name} | {website}")
        return profile

    def remove_competitor(self, name: str) -> bool:
        """Xóa đối thủ khỏi danh sách theo dõi."""
        if name in self._competitors:
            del self._competitors[name]
            logger.info(f"Competitor removed: {name}")
            return True
        return False

    def list_competitors(self) -> list[dict[str, Any]]:
        """Danh sách đối thủ đang theo dõi."""
        return [p.to_dict() for p in self._competitors.values()]

    # ─── Website Monitoring ───────────────────────────────────────────────────

    def snapshot_competitor(self, name: str) -> dict[str, Any]:
        """
        Lấy snapshot hiện tại của website đối thủ.
        Lưu vào history để so sánh sau.
        """
        profile = self._competitors.get(name)
        if not profile:
            return {"error": f"Đối thủ '{name}' chưa được thêm vào danh sách"}

        snapshot = self._scraper.get_page_snapshot(profile.website)
        snapshot["competitor_name"] = name
        profile.snapshots.append(snapshot)
        profile.last_checked = datetime.now()

        logger.info(f"Snapshot taken | competitor={name} | prices={len(snapshot.get('price_mentions', []))}")
        return snapshot

    def check_for_changes(self, name: str) -> dict[str, Any]:
        """
        So sánh snapshot mới nhất vs snapshot trước đó.
        Trả về dict changes + AI analysis nếu có thay đổi lớn.
        """
        profile = self._competitors.get(name)
        if not profile:
            return {"error": f"Đối thủ '{name}' chưa được thêm"}

        if len(profile.snapshots) < 2:
            # Chụp snapshot mới để có data
            self.snapshot_competitor(name)
            if len(profile.snapshots) < 2:
                return {"message": "Cần ít nhất 2 snapshots để so sánh. Chạy lại sau 24h."}

        old = profile.snapshots[-2]
        new = profile.snapshots[-1]
        changes = self._scraper.detect_changes(old, new)

        result = {
            "competitor": name,
            **changes,
        }

        if changes["has_changes"]:
            logger.warning(f"Changes detected | competitor={name} | changes={len(changes['changes'])}")
            result["ai_analysis"] = self._analyze_changes_with_ai(name, changes["changes"])

        return result

    def _analyze_changes_with_ai(self, name: str, changes: list[dict]) -> str:
        """Dùng Claude phân tích ý nghĩa các thay đổi phát hiện được."""
        changes_str = json.dumps(changes, ensure_ascii=False, indent=2)

        prompt = f"""Phân tích các thay đổi vừa phát hiện trên website đối thủ "{name}":

**Thay đổi:**
{changes_str}

Đánh giá:
1. Đây là loại thay đổi gì? (pricing, product launch, campaign, rebranding...)
2. Mức độ ảnh hưởng đến FuviAI: Cao / Trung bình / Thấp
3. Họ đang thực hiện chiến lược gì?
4. **Counter-strategy của FuviAI**: Cần làm gì trong 48h tới?

Trả lời súc tích, hành động được ngay."""

        return self.chat(prompt, reset_history=True)

    # ─── Daily Scan ───────────────────────────────────────────────────────────

    def daily_scan(self) -> dict[str, Any]:
        """
        Scan toàn bộ đối thủ — chạy 1 lần/ngày qua Celery.
        Trả về báo cáo tổng hợp.
        """
        if not self._competitors:
            return {"message": "Chưa có đối thủ nào trong danh sách. Dùng add_competitor() trước."}

        logger.info(f"Daily competitor scan | count={len(self._competitors)}")

        scan_results = []
        alerts = []

        for name in self._competitors:
            # Lấy snapshot mới
            snapshot = self.snapshot_competitor(name)

            # Check changes
            changes = self.check_for_changes(name)

            result = {
                "competitor": name,
                "snapshot": {
                    "title": snapshot.get("title", ""),
                    "prices": snapshot.get("price_mentions", []),
                    "headings": snapshot.get("headings", [])[:3],
                },
                "changes": changes,
            }

            # Flag nếu có thay đổi giá
            has_price_change = any(
                c.get("type") == "price_changed"
                for c in changes.get("changes", [])
            )
            if has_price_change:
                alerts.append(f"⚠️ {name}: Phát hiện thay đổi giá!")
                result["alert"] = "PRICE_CHANGE"

            scan_results.append(result)

        return {
            "scan_date": datetime.now().isoformat(),
            "competitors_scanned": len(scan_results),
            "alerts": alerts,
            "results": scan_results,
        }

    # ─── Competitor Analysis ─────────────────────────────────────────────────

    def analyze_competitor(
        self,
        name: str,
        additional_context: str = "",
    ) -> str:
        """
        Phân tích sâu 1 đối thủ dựa trên dữ liệu đã thu thập.
        """
        profile = self._competitors.get(name)
        if not profile:
            return f"Đối thủ '{name}' chưa được thêm vào danh sách."

        latest = profile.snapshots[-1] if profile.snapshots else {}
        history_count = len(profile.snapshots)

        prompt = f"""Phân tích toàn diện đối thủ cạnh tranh: **{name}**

**Thông tin cơ bản:**
- Website: {profile.website}
- Facebook: {profile.facebook_page or "Chưa có"}
- Ngành: {profile.industry}
- Số lần đã theo dõi: {history_count} lần

**Dữ liệu website mới nhất:**
- Title: {latest.get('title', 'N/A')}
- Headings: {', '.join(latest.get('headings', [])[:5])}
- Mentions giá: {', '.join(latest.get('price_mentions', [])[:5]) or 'Không có'}

**Context thêm:** {additional_context or "Không có"}

Phân tích:
1. **Định vị thị trường**: Họ đang target ai? Giá trị đề xuất là gì?
2. **Điểm mạnh** vs **Điểm yếu** (so với FuviAI)
3. **Chiến lược pricing**: Premium / Mid-range / Budget?
4. **Content & Marketing strategy** (dựa trên headings và context)
5. **Khoảng trống thị trường** FuviAI có thể khai thác
6. **Counter-strategy cụ thể**: 3 action FuviAI nên làm trong 30 ngày tới"""

        logger.info(f"Competitor analysis | name={name}")
        return self.chat(prompt, reset_history=True)

    def compare_competitors(self, names: list[str] | None = None) -> str:
        """So sánh nhiều đối thủ cùng lúc."""
        if names is None:
            names = list(self._competitors.keys())

        if not names:
            return "Chưa có đối thủ nào để so sánh."

        competitors_data = []
        for name in names:
            profile = self._competitors.get(name)
            if profile:
                latest = profile.snapshots[-1] if profile.snapshots else {}
                competitors_data.append({
                    "name": name,
                    "website": profile.website,
                    "title": latest.get("title", ""),
                    "headings": latest.get("headings", [])[:3],
                    "prices": latest.get("price_mentions", [])[:3],
                })

        prompt = f"""So sánh {len(competitors_data)} đối thủ cạnh tranh của FuviAI:

**Dữ liệu:**
{json.dumps(competitors_data, ensure_ascii=False, indent=2)}

Tạo bảng so sánh:
1. **Bảng so sánh** (markdown): Tên | Định vị | Pricing | Điểm mạnh | Điểm yếu
2. **Ai đang dẫn đầu** và tại sao
3. **FuviAI nên học gì** từ mỗi đối thủ
4. **Cơ hội phân biệt hóa** — FuviAI có thể làm gì mà cả 3 chưa làm?"""

        return self.chat(prompt, reset_history=True)

    # ─── Counter-Strategy ─────────────────────────────────────────────────────

    def generate_counter_strategy(
        self,
        competitor_name: str,
        trigger_event: str,
        budget_available: float = 50_000_000,
        timeline_days: int = 7,
    ) -> str:
        """
        Tạo counter-strategy ngay khi đối thủ có động thái lớn.
        Target < 30 giây response.

        Args:
            trigger_event: "Vừa giảm giá 30%", "Launch sản phẩm mới", "Chạy TVC"
            budget_available: Ngân sách FuviAI có thể deploy ngay (VNĐ)
            timeline_days: Số ngày để phản ứng
        """
        prompt = f"""URGENT: Cần counter-strategy ngay!

**Đối thủ:** {competitor_name}
**Sự kiện:** {trigger_event}
**Budget khả dụng:** {budget_available:,.0f} VNĐ
**Timeline:** {timeline_days} ngày

Tạo ngay counter-strategy cho FuviAI:

**[NGAY LẬP TỨC — Trong 24h]**
- Action 1: ...
- Action 2: ...

**[NGẮN HẠN — Ngày 2-{timeline_days}]**
- Action 1: ...
- Action 2: ...

**Phân bổ budget {budget_available:,.0f} VNĐ:**
- Channel A: X% = ... VNĐ
- Channel B: Y% = ... VNĐ

**KPI kỳ vọng:** ...
**Rủi ro cần tránh:** ..."""

        logger.info(f"Counter-strategy generated | competitor={competitor_name} | event={trigger_event}")
        return self.chat(prompt, reset_history=True)

    def benchmark_engagement(
        self,
        fuviai_metrics: dict[str, Any],
        competitor_metrics: dict[str, dict[str, Any]],
    ) -> str:
        """
        So sánh engagement rate FuviAI vs đối thủ.

        Args:
            fuviai_metrics: {"reach": 10000, "engagement": 500, "posts": 20}
            competitor_metrics: {"Đối thủ A": {"reach": ..., ...}, ...}
        """
        all_data = {"FuviAI": fuviai_metrics, **competitor_metrics}

        # Tính engagement rate
        for brand, m in all_data.items():
            reach = m.get("reach", 1)
            engagement = m.get("engagement", 0)
            m["engagement_rate"] = round(engagement / reach * 100, 2) if reach > 0 else 0

        prompt = f"""Phân tích engagement rate FuviAI vs đối thủ:

**Dữ liệu (tuần này):**
{json.dumps(all_data, ensure_ascii=False, indent=2)}

Benchmark ngành VN 2026: Facebook ER trung bình 1.5-3%, TikTok 3-8%

Báo cáo:
1. Bảng xếp hạng engagement rate
2. FuviAI đang ở vị trí nào và tại sao
3. Top performer đang làm gì khác biệt
4. 3 action cụ thể để tăng ER của FuviAI lên top 2 trong 30 ngày"""

        return self.chat(prompt, reset_history=True)

    # ─── Dashboard Data ───────────────────────────────────────────────────────

    def get_dashboard_data(self) -> dict[str, Any]:
        """
        Trả về data JSON cho /api/analytics/competitors dashboard.
        """
        competitors_summary = []
        for name, profile in self._competitors.items():
            latest = profile.snapshots[-1] if profile.snapshots else {}
            competitors_summary.append({
                "name": name,
                "website": profile.website,
                "industry": profile.industry,
                "last_checked": profile.last_checked.isoformat() if profile.last_checked else None,
                "snapshot": {
                    "title": latest.get("title", ""),
                    "price_mentions": latest.get("price_mentions", []),
                },
                "snapshots_count": len(profile.snapshots),
            })

        return {
            "total_competitors": len(self._competitors),
            "competitors": competitors_summary,
            "last_scan": datetime.now().isoformat(),
        }
