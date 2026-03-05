"""
FuviAI Marketing Agent — Campaign Agent (M3)
Phân tích hiệu suất campaign, đề xuất tối ưu ngân sách và creative
"""

from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.config.prompts_vn import CAMPAIGN_AGENT_SYSTEM


# Benchmark ngành VN 2025-2026
VN_BENCHMARKS = {
    "facebook": {"ctr": 1.8, "cpc": 2500, "cpm": 45000, "roas": 3.5, "cpa": 85000},
    "google": {"ctr": 4.5, "cpc": 3500, "cpm": 35000, "roas": 4.2, "cpa": 75000},
    "tiktok": {"ctr": 2.5, "cpc": 1800, "cpm": 30000, "roas": 2.8, "cpa": 95000},
    "shopee": {"ctr": 4.0, "cpc": 1200, "cpm": 25000, "roas": 5.0, "cpa": 55000},
    "email": {"open_rate": 21, "ctr": 3.5, "conversion_rate": 2.1},
}


class CampaignAgent(BaseAgent):
    """
    Agent phân tích campaign marketing.

    Usage:
        agent = CampaignAgent()
        report = agent.analyze_csv("path/to/campaign.csv")
        budget = agent.optimize_budget({"facebook": 5000000, "tiktok": 3000000})
    """

    def __init__(self):
        super().__init__(
            system_prompt=CAMPAIGN_AGENT_SYSTEM,
            max_tokens=8096,
            temperature=0.2,
        )

    # ─── Phân tích CSV ───────────────────────────────────────────────────────

    def analyze_csv(self, csv_content: str, platform: str = "facebook") -> str:
        """
        Phân tích dữ liệu campaign từ CSV string.
        Trả về 5 đề xuất cải thiện cụ thể.
        """
        benchmark = VN_BENCHMARKS.get(platform, VN_BENCHMARKS["facebook"])

        prompt = f"""Phân tích dữ liệu campaign {platform.upper()} sau và đưa ra 5 đề xuất cải thiện:

**Benchmark ngành VN hiện tại:**
- CTR trung bình: {benchmark.get('ctr', 'N/A')}%
- CPC trung bình: {benchmark.get('cpc', 'N/A'):,} VNĐ
- ROAS trung bình: {benchmark.get('roas', 'N/A')}×
- CPA trung bình: {benchmark.get('cpa', 'N/A'):,} VNĐ

**Dữ liệu campaign:**
```
{csv_content[:3000]}
```

Phân tích và đề xuất theo format:
1. Tóm tắt hiệu suất (so với benchmark)
2. Top 3 ad set/creative đang hoạt động tốt nhất
3. Bottom 3 cần dừng/tối ưu ngay
4. 5 đề xuất cải thiện (xếp theo impact/effort)
5. Phân bổ ngân sách đề xuất cho tuần tới"""

        logger.info(f"Analyzing campaign CSV | platform={platform} | rows={csv_content.count(chr(10))}")
        return self.chat(prompt, reset_history=True)

    def analyze_dict(self, data: list[dict[str, Any]], platform: str = "facebook") -> str:
        """Phân tích campaign data từ list of dicts."""
        csv_content = self._dict_to_csv(data)
        return self.analyze_csv(csv_content, platform)

    # ─── Budget Optimization ─────────────────────────────────────────────────

    def optimize_budget(
        self,
        current_budget: dict[str, float],
        goal: str = "tối đa ROAS",
        season: str = "",
    ) -> str:
        """
        Đề xuất phân bổ lại ngân sách giữa các platform.

        Args:
            current_budget: {"facebook": 10000000, "tiktok": 5000000, ...} (VNĐ)
            goal: mục tiêu campaign
            season: mùa vụ đặc biệt ("tet", "11.11", "black_friday", "")
        """
        total = sum(current_budget.values())
        breakdown = "\n".join(
            f"  - {p.title()}: {b:,.0f} VNĐ ({b/total*100:.1f}%)"
            for p, b in current_budget.items()
        )

        season_context = ""
        if season:
            season_map = {
                "tet": "Tết Nguyên Đán — tăng mạnh Zalo OA + Facebook, CPC tăng 40-80%",
                "11.11": "11/11 Shopee/Lazada — tập trung performance ads, ROAS cao nhất năm",
                "black_friday": "Black Friday — email + retargeting, audience đã warm up",
                "8.3": "8/3 Quốc tế Phụ nữ — Facebook/Instagram, emotional content",
                "20.10": "20/10 Phụ nữ Việt Nam — Zalo OA + TikTok, gift/voucher",
            }
            season_context = f"\n**Mùa vụ:** {season_map.get(season, season)}"

        prompt = f"""Tối ưu ngân sách marketing cho mục tiêu: **{goal}**
{season_context}

**Ngân sách hiện tại (tổng: {total:,.0f} VNĐ):**
{breakdown}

**Benchmark ROAS từng platform (VN 2026):**
{json.dumps({k: v for k, v in VN_BENCHMARKS.items() if 'roas' in v}, ensure_ascii=False, indent=2)}

Đề xuất:
1. Phân bổ ngân sách tối ưu (% và số tiền cụ thể)
2. Lý do dịch chuyển ngân sách
3. KPI kỳ vọng sau tối ưu
4. Cảnh báo rủi ro nếu có"""

        return self.chat(prompt, reset_history=True)

    # ─── A/B Test ────────────────────────────────────────────────────────────

    def design_ab_test(
        self,
        objective: str,
        current_approach: str,
        budget: float = 5_000_000,
    ) -> str:
        """Thiết kế A/B test cho campaign."""
        prompt = f"""Thiết kế A/B test chi tiết cho campaign marketing:

**Mục tiêu:** {objective}
**Approach hiện tại:** {current_approach}
**Budget test:** {budget:,.0f} VNĐ

Thiết kế:
1. Hypothesis (giả thuyết cần kiểm chứng)
2. Variant A (control) vs Variant B (challenger) — mô tả cụ thể
3. Phân bổ ngân sách A/B (thường 50/50 hoặc 70/30)
4. Thời gian chạy tối thiểu để có statistical significance
5. KPI chính để đánh giá winner
6. Cách đọc kết quả: khi nào thì dừng sớm / kéo dài"""

        return self.chat(prompt, reset_history=True)

    # ─── Campaign Report ─────────────────────────────────────────────────────

    def weekly_report(
        self,
        metrics: dict[str, Any],
        previous_metrics: dict[str, Any] | None = None,
    ) -> str:
        """Tạo báo cáo campaign tuần."""
        prev_str = ""
        if previous_metrics:
            prev_str = f"\n**Tuần trước:**\n{json.dumps(previous_metrics, ensure_ascii=False, indent=2)}"

        prompt = f"""Tạo báo cáo campaign tuần theo format chuẩn FuviAI:

**Dữ liệu tuần này:**
{json.dumps(metrics, ensure_ascii=False, indent=2)}
{prev_str}

Format báo cáo:
📊 **CAMPAIGN REPORT TUẦN [N]**

**Tổng quan:**
- Tổng spend / ROAS / CPA vs tuần trước

**Highlights:**
- ✅ Điểm tốt (3 điểm)
- ⚠️ Cần cải thiện (3 điểm)

**Top performing:**
- Creative / Audience / Placement tốt nhất

**Action items tuần tới:**
- 3 action cụ thể, có deadline"""

        return self.chat(prompt, reset_history=True)

    # ─── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _dict_to_csv(data: list[dict]) -> str:
        if not data:
            return ""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()
