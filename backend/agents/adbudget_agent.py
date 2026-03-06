"""
FuviAI Marketing Agent — Ad Budget Agent (M9)
Dự báo ngân sách quảng cáo theo mùa vụ VN, tối ưu phân bổ theo mục tiêu
"""

from __future__ import annotations

import json
from typing import Any
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.tools.google_ads_tool import GoogleAdsTool


ADBUDGET_SYSTEM = """Bạn là Ad Budget Intelligence Specialist của FuviAI, chuyên dự báo và \
tối ưu ngân sách quảng cáo cho SME Việt Nam.

## Chuyên môn
- Dự báo CPC/CPM theo mùa vụ VN với độ chính xác ±15%
- Phân bổ ngân sách tối ưu giữa các kênh theo mục tiêu (awareness/conversion/retention)
- Nhận diện thời điểm "vàng" và "đắt đỏ" trong năm để điều chỉnh spend
- Mô hình ROAS forecast theo ngành và budget size

## Lịch mùa vụ quảng cáo VN (quan trọng nhất)

### Q1 (CPC tăng 40-80%)
- Tết Nguyên Đán: Giá đắt nhất năm, nhưng ROAS cao nếu plan đúng
- Valentine 14/2: tăng ~30% ngành thời trang, quà tặng

### Q2 (CPC tương đối ổn)
- 8/3 Quốc tế Phụ nữ: tăng ngành làm đẹp, thời trang nữ
- 30/4-1/5: tăng ngành du lịch, F&B

### Q3 (CPC thấp — cơ hội tốt)
- Mùa hè: CPC thấp, test campaign mới
- 20/10 Phụ nữ VN: tăng ngành quà tặng, hoa

### Q4 (CPC cao nhất sau Tết)
- 11/11 Shopee: ROAS cao nhất năm, cần budget lớn
- Black Friday: tăng 50-100%
- 12/12: tăng mạnh TMĐT
- Chuẩn bị Tết: tháng 12 bắt đầu tăng

## Output
Luôn kèm con số cụ thể (VNĐ), % tăng/giảm, và timeline rõ ràng."""


# ─── Season Calendar ─────────────────────────────────────────────────────────

SEASON_CALENDAR = {
    "tet": {
        "name": "Tết Nguyên Đán",
        "months": [1, 2],
        "cpc_multiplier": 1.6,
        "best_channels": ["facebook", "zalo"],
        "industries": ["all"],
        "strategy": "Tăng budget sớm (từ 20/12), creative Tết, focus Zalo OA",
    },
    "8_3": {
        "name": "8/3 Quốc tế Phụ nữ",
        "months": [3],
        "cpc_multiplier": 1.3,
        "best_channels": ["facebook", "tiktok"],
        "industries": ["fashion", "beauty", "gifts"],
        "strategy": "Emotional content, gift guide, influencer collab",
    },
    "summer": {
        "name": "Mùa hè (Tháng 6-8)",
        "months": [6, 7, 8],
        "cpc_multiplier": 0.8,
        "best_channels": ["tiktok", "google"],
        "industries": ["travel", "fb", "fashion"],
        "strategy": "CPC thấp — thời điểm tốt để test creative mới, build audience",
    },
    "20_10": {
        "name": "20/10 Phụ nữ Việt Nam",
        "months": [10],
        "cpc_multiplier": 1.25,
        "best_channels": ["zalo", "facebook"],
        "industries": ["gifts", "beauty", "fashion"],
        "strategy": "Zalo OA broadcast, Facebook emotional video",
    },
    "11_11": {
        "name": "11/11 Shopee Double Day",
        "months": [11],
        "cpc_multiplier": 1.5,
        "best_channels": ["shopee", "tiktok", "facebook"],
        "industries": ["ecommerce", "all"],
        "strategy": "Performance ads max budget, retargeting mạnh, flash deals",
    },
    "black_friday": {
        "name": "Black Friday",
        "months": [11],
        "cpc_multiplier": 1.7,
        "best_channels": ["facebook", "google", "email"],
        "industries": ["all"],
        "strategy": "Email marketing + retargeting, audience đã warm up từ 11/11",
    },
    "12_12": {
        "name": "12/12 Double Day",
        "months": [12],
        "cpc_multiplier": 1.4,
        "best_channels": ["shopee", "tiktok"],
        "industries": ["ecommerce"],
        "strategy": "Kéo dài momentum từ Black Friday, focus mobile",
    },
}


class AdBudgetAgent(BaseAgent):
    """
    Agent dự báo và tối ưu ngân sách quảng cáo.

    Usage:
        agent = AdBudgetAgent()

        # Dự báo budget cho quý tới
        forecast = agent.forecast_quarterly(budget=100_000_000, industry="ecommerce", quarter=4)

        # Lên kế hoạch ngân sách cả năm
        plan = agent.annual_budget_plan(annual_budget=500_000_000, industry="fmcg")

        # Phân bổ ngân sách theo kênh
        allocation = agent.allocate_by_channel(budget=50_000_000, goal="conversion")
    """

    def __init__(self):
        super().__init__(
            system_prompt=ADBUDGET_SYSTEM,
            max_tokens=8096,
            temperature=0.2,
        )
        self._google_ads = GoogleAdsTool()

    # ─── Seasonal Forecast ────────────────────────────────────────────────────

    def forecast_quarterly(
        self,
        budget: float,
        industry: str,
        quarter: int,
        year: int = 2027,
    ) -> str:
        """
        Dự báo hiệu quả ngân sách cho 1 quý cụ thể.
        Target accuracy: ±15% theo roadmap.
        """
        # Xác định mùa vụ trong quý
        quarter_months = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}
        months = quarter_months.get(quarter, [1, 2, 3])

        active_seasons = [
            s for s in SEASON_CALENDAR.values()
            if any(m in months for m in s["months"])
        ]
        seasons_str = json.dumps(active_seasons, ensure_ascii=False, indent=2)

        prompt = f"""Dự báo ngân sách Q{quarter}/{year} cho ngành {industry}:

**Budget:** {budget:,.0f} VNĐ
**Ngành:** {industry}
**Quý:** Q{quarter}/{year} (tháng {', '.join(str(m) for m in months)})

**Mùa vụ trong quý:**
{seasons_str}

Dự báo chi tiết:
1. **Phân bổ theo tháng** (budget + lý do điều chỉnh)
2. **KPI kỳ vọng theo từng tháng:**
   - Impressions / Clicks / Conversions (ước tính)
   - CPC dự kiến (so với trung bình)
   - ROAS kỳ vọng
3. **Thời điểm tăng/giảm budget** + % điều chỉnh
4. **Risk factors**: khi nào có thể miss target và cách phòng ngừa
5. **Best week trong quý** để push budget tối đa

Sai số dự báo mục tiêu: ±15%"""

        logger.info(f"Quarterly forecast | Q{quarter}/{year} | budget={budget:,.0f} | industry={industry}")
        return self.chat(prompt, reset_history=True)

    def annual_budget_plan(
        self,
        annual_budget: float,
        industry: str,
        primary_goal: str = "cân bằng awareness và conversion",
        channels: list[str] | None = None,
    ) -> str:
        """
        Lên kế hoạch ngân sách cả năm với phân bổ theo mùa vụ.
        """
        if channels is None:
            channels = ["facebook", "tiktok", "zalo", "google"]

        seasons_summary = {
            name: {"name": s["name"], "months": s["months"], "cpc_multiplier": s["cpc_multiplier"]}
            for name, s in SEASON_CALENDAR.items()
        }

        prompt = f"""Lập kế hoạch ngân sách quảng cáo cả năm 2027:

**Annual budget:** {annual_budget:,.0f} VNĐ
**Ngành:** {industry}
**Mục tiêu chính:** {primary_goal}
**Channels:** {', '.join(channels)}

**Lịch mùa vụ VN:**
{json.dumps(seasons_summary, ensure_ascii=False, indent=2)}

Kế hoạch:
1. **Bảng phân bổ theo quý** (Q1/Q2/Q3/Q4) — % và số tiền tuyệt đối
2. **Top 3 tháng cần đầu tư mạnh nhất** + lý do ROI cao
3. **Top 2 tháng có thể giảm spend** + dùng thời gian để làm gì
4. **Phân bổ theo kênh** cho cả năm (% tổng budget)
5. **Emergency reserve** (% giữ lại cho cơ hội bất ngờ)
6. **KPI tổng năm**: Impressions / Leads / Revenue kỳ vọng"""

        logger.info(f"Annual budget plan | budget={annual_budget:,.0f} | industry={industry}")
        return self.chat(prompt, reset_history=True)

    def season_budget_boost(
        self,
        base_budget: float,
        season_key: str,
        industry: str,
    ) -> dict[str, Any]:
        """
        Tính toán budget cần boost cho mùa vụ cụ thể.

        Returns:
            {"recommended_budget": ..., "multiplier": ..., "ai_plan": "..."}
        """
        season = SEASON_CALENDAR.get(season_key)
        if not season:
            available = list(SEASON_CALENDAR.keys())
            return {"error": f"Season không hợp lệ. Các season: {available}"}

        multiplier = season["cpc_multiplier"]
        # CPC tăng → cần budget cao hơn để giữ nguyên reach
        recommended_budget = base_budget * multiplier
        extra = recommended_budget - base_budget

        prompt = f"""Kế hoạch ngân sách cho mùa vụ **{season['name']}** - ngành {industry}:

**Base budget:** {base_budget:,.0f} VNĐ
**Budget đề xuất:** {recommended_budget:,.0f} VNĐ (+{(multiplier-1)*100:.0f}%)
**Lý do tăng:** CPC tăng ~{(multiplier-1)*100:.0f}% trong mùa này
**Kênh tốt nhất:** {', '.join(season['best_channels'])}
**Strategy:** {season['strategy']}

Chi tiết kế hoạch:
1. **Phân bổ {recommended_budget:,.0f} VNĐ** theo kênh
2. **Timeline**: Khi nào bắt đầu tăng, peak, và giảm dần
3. **Creative strategy** cho mùa này
4. **Early bird advantage**: Tăng budget sớm trước peak để tích lũy data
5. **Exit strategy**: Khi nào rút về base budget"""

        ai_plan = self.chat(prompt, reset_history=True)

        return {
            "season": season["name"],
            "base_budget": base_budget,
            "recommended_budget": recommended_budget,
            "additional_budget": extra,
            "cpc_multiplier": multiplier,
            "best_channels": season["best_channels"],
            "ai_plan": ai_plan,
        }

    # ─── Channel Allocation ───────────────────────────────────────────────────

    def allocate_by_channel(
        self,
        budget: float,
        goal: str = "conversion",
        industry: str = "general",
        current_month: int = 3,
    ) -> str:
        """
        Phân bổ budget tối ưu giữa các kênh theo mục tiêu.

        Args:
            goal: "awareness" / "conversion" / "retention" / "cân bằng"
        """
        # Xác định mùa vụ tháng hiện tại
        active_season = next(
            (s for s in SEASON_CALENDAR.values() if current_month in s["months"]),
            None
        )
        season_note = f"\n**Mùa vụ tháng {current_month}:** {active_season['name']} — {active_season['strategy']}" \
            if active_season else ""

        prompt = f"""Phân bổ ngân sách {budget:,.0f} VNĐ theo kênh:

**Mục tiêu:** {goal}
**Ngành:** {industry}
**Tháng hiện tại:** tháng {current_month}{season_note}

Benchmark hiệu quả từng kênh (VN 2026-2027):
- **Facebook Ads**: ROAS 3.5×, CPC 2.500đ, mạnh về remarketing + lookalike
- **TikTok Ads**: ROAS 2.8×, CPC 1.800đ, viral potential, Gen Z + Millennial
- **Google Ads**: ROAS 4.2×, CPC 3.500đ, intent-based, conversion cao
- **Zalo OA**: CPC 800đ, reach mid-age VN, tin nhắn cá nhân hoá
- **Shopee Ads**: ROAS 5.0×, CPC 1.200đ, bottom-of-funnel cực mạnh
- **Email Marketing**: ROI 36×, chi phí thấp nhất, nurture lead

Phân bổ chi tiết:
| Kênh | % | Số tiền | Mục đích | KPI kỳ vọng |
|------|---|---------|---------|------------|

Kèm theo:
- Lý do ưu tiên / deprioritize từng kênh
- Cách theo dõi hiệu quả từng kênh
- Khi nào rebalance"""

        return self.chat(prompt, reset_history=True)

    # ─── ROAS Forecasting ─────────────────────────────────────────────────────

    def forecast_roas(
        self,
        spend: float,
        platform: str,
        industry: str,
        campaign_type: str = "conversion",
        historical_roas: float | None = None,
    ) -> str:
        """Dự báo ROAS cho campaign cụ thể."""
        from backend.agents.campaign_agent import VN_BENCHMARKS
        benchmark = VN_BENCHMARKS.get(platform, {})

        historical_str = f"\n**ROAS lịch sử của bạn:** {historical_roas}× (dùng làm baseline)" \
            if historical_roas else ""

        prompt = f"""Dự báo ROAS cho campaign:

**Platform:** {platform.upper()}
**Spend:** {spend:,.0f} VNĐ
**Ngành:** {industry}
**Loại campaign:** {campaign_type}
**Benchmark ngành:** ROAS {benchmark.get('roas', 'N/A')}×, CPC {benchmark.get('cpc', 0):,}đ{historical_str}

Dự báo:
1. **ROAS kỳ vọng** (base / optimistic / conservative)
2. **Revenue kỳ vọng** = spend × ROAS
3. **Break-even point**: ROAS tối thiểu để có lãi
4. **Variables ảnh hưởng** ROAS nhất: creative quality, audience, landing page...
5. **Cách tối ưu** để đạt ROAS target trong 2 tuần đầu"""

        return self.chat(prompt, reset_history=True)

    def emergency_budget_reallocation(
        self,
        current_allocation: dict[str, float],
        underperforming: str,
        overperforming: str,
    ) -> str:
        """
        Tái phân bổ ngân sách khẩn cấp khi 1 kênh underperform.
        """
        total = sum(current_allocation.values())
        allocation_str = "\n".join(
            f"  - {k}: {v:,.0f} VNĐ ({v/total*100:.1f}%)"
            for k, v in current_allocation.items()
        )

        prompt = f"""KHẨN: Tái phân bổ ngân sách ngay!

**Phân bổ hiện tại (tổng: {total:,.0f} VNĐ):**
{allocation_str}

**Vấn đề:** {underperforming} đang underperform
**Cơ hội:** {overperforming} đang outperform

Đề xuất:
1. **Giảm bao nhiêu** từ {underperforming} (% cụ thể)
2. **Tăng bao nhiêu** cho {overperforming}
3. **Phân bổ mới** (bảng)
4. **Timeline thực hiện**: Thay đổi ngay hôm nay hay chờ?
5. **Trigger để review lại** trong bao lâu"""

        return self.chat(prompt, reset_history=True)

    def get_season_calendar(self) -> dict[str, Any]:
        """Trả về lịch mùa vụ quảng cáo VN."""
        return SEASON_CALENDAR

    # ─── Google Ads Integration ───────────────────────────────────────────────

    def analyze_google_ads_performance(
        self,
        days_back: int = 30,
        industry: str = "saas",
    ) -> str:
        """
        Lấy dữ liệu Google Ads thực tế + Claude phân tích + đề xuất tối ưu.
        Fallback về benchmark ngành VN nếu chưa cấu hình.

        Args:
            days_back: Số ngày muốn phân tích
            industry: Ngành để so sánh benchmark
        """
        if self._google_ads.is_configured:
            summary = self._google_ads.get_account_summary(days_back=days_back)
            keywords = self._google_ads.get_keyword_performance(days_back=days_back, min_clicks=5)
            data_source = "Google Ads API (data thực)"
        else:
            summary = {"note": "Google Ads chưa cấu hình — dùng benchmark ngành"}
            keywords = []
            data_source = "benchmark ngành VN 2026"

        benchmark = self._google_ads.get_industry_benchmark(industry)

        kw_str = ""
        if keywords:
            top_kw = keywords[:10]
            kw_str = "\n**Top 10 từ khoá theo clicks:**\n" + "\n".join(
                f"- {k['keyword']} | clicks: {k['clicks']} | CPC: {k['avg_cpc']:,.0f}đ | QS: {k['quality_score']}"
                for k in top_kw
            )

        prompt = f"""Phân tích hiệu suất Google Ads và đề xuất tối ưu:

**Nguồn dữ liệu:** {data_source}
**Khoảng thời gian:** {days_back} ngày qua
**Ngành:** {industry}

**Dữ liệu account:**
{json.dumps(summary, ensure_ascii=False, indent=2)}
{kw_str}

**Benchmark ngành {industry} VN 2026:**
- CPC trung bình: {benchmark['cpc']:,}đ
- ROAS trung bình: {benchmark['roas']}×
- CTR trung bình: {benchmark['ctr']}%
- Conversion rate: {benchmark['conversion_rate']}%

Phân tích:
1. **So sánh với benchmark ngành** — đang tốt hay kém hơn ở đâu?
2. **Top 3 vấn đề cần cải thiện ngay** (quality score, bid strategy, từ khoá...)
3. **Cơ hội tăng trưởng** — budget allocation, từ khoá mới, ad copy...
4. **Action plan cụ thể** trong 30 ngày tới với budget hiện tại"""

        logger.info(f"Google Ads performance analysis | days={days_back} | industry={industry}")
        return self.chat(prompt, reset_history=True)

    def optimize_google_ads_budget(
        self,
        total_monthly_budget: float,
        campaign_ids: list[str] | None = None,
    ) -> str:
        """
        Phân tích ROAS từng campaign và đề xuất phân bổ ngân sách tối ưu.

        Args:
            total_monthly_budget: Tổng ngân sách tháng (VNĐ)
            campaign_ids: Danh sách campaign cần tối ưu (None = tất cả)
        """
        campaigns = self._google_ads.get_campaign_performance(days_back=30)
        if campaign_ids:
            campaigns = [c for c in campaigns if str(c["campaign_id"]) in campaign_ids]

        if not campaigns:
            campaigns_str = "Chưa có dữ liệu campaign (Google Ads chưa cấu hình hoặc chưa có lịch sử)"
        else:
            campaigns_str = json.dumps(campaigns, ensure_ascii=False, indent=2)

        prompt = f"""Tối ưu phân bổ ngân sách Google Ads:

**Tổng ngân sách tháng:** {total_monthly_budget:,.0f} VNĐ
**Ngân sách ngày:** {total_monthly_budget/30:,.0f} VNĐ

**Performance 30 ngày qua:**
{campaigns_str}

Đề xuất phân bổ ngân sách tối ưu:
1. **Phân bổ theo campaign** (VNĐ/ngày + % tổng):
   | Campaign | Budget/ngày | % | Lý do |
2. **Campaign nên scale up** (ROAS cao, còn room tăng) và tại sao
3. **Campaign nên cắt giảm hoặc dừng** và tại sao
4. **Dự báo KPI** với phân bổ mới: clicks, conversions, ROAS tổng

Chỉ đề xuất thay đổi có data support, không suy đoán."""

        logger.info(f"Google Ads budget optimization | total={total_monthly_budget:,.0f}đ")
        return self.chat(prompt, reset_history=True)
