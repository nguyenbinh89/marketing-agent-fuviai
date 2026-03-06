"""
FuviAI Marketing Agent — /api/reports/* routes
AI-powered marketing report generator — tổng hợp dữ liệu + viết báo cáo tiếng Việt
"""

from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

router = APIRouter()

ReportType = Literal["weekly", "monthly", "campaign_summary", "platform_comparison"]

# Lazy singletons
_base_agent = None
_gads = None
_fads = None
_tads = None


def _get_agent():
    global _base_agent
    if _base_agent is None:
        from backend.agents.base_agent import BaseAgent
        _base_agent = BaseAgent()
    return _base_agent


def _get_ad_tools():
    global _gads, _fads, _tads
    if _gads is None:
        from backend.tools.google_ads_tool import GoogleAdsTool
        _gads = GoogleAdsTool()
    if _fads is None:
        from backend.tools.facebook_ads_tool import FacebookAdsTool
        _fads = FacebookAdsTool()
    if _tads is None:
        from backend.tools.tiktok_ads_tool import TikTokAdsTool
        _tads = TikTokAdsTool()
    return _gads, _fads, _tads


def _safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Report data fetch error: {e}")
        return {"error": str(e)}


# ─── Request / Response models ────────────────────────────────────────────────

class ReportRequest(BaseModel):
    report_type: ReportType = "weekly"
    days: int = 30
    brand_name: str = "Thương hiệu"
    industry: str = "ecommerce"
    include_google: bool = True
    include_facebook: bool = True
    include_tiktok: bool = True
    extra_notes: str = ""        # Ghi chú thêm từ marketer


class ReportResponse(BaseModel):
    report_type: str
    days: int
    brand_name: str
    generated_at: str
    platforms_included: list[str]
    report_markdown: str
    word_count: int


# ─── Data collection ──────────────────────────────────────────────────────────

def _collect_platform_data(req: ReportRequest) -> dict:
    gads, fads, tads = _get_ad_tools()
    data: dict = {}

    tasks = []
    if req.include_google and gads.is_configured:
        tasks.append(("google", gads.get_account_summary, req.days))
    if req.include_facebook and fads.is_configured:
        tasks.append(("facebook", fads.get_account_insights, req.days))
    if req.include_tiktok and tads.is_configured:
        tasks.append(("tiktok", tads.get_account_insights, req.days))

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(_safe, fn, days): key for key, fn, days in tasks}
        for future, key in futures.items():
            data[key] = future.result()

    # Config status
    data["_config"] = {
        "google":   gads.is_configured,
        "facebook": fads.is_configured,
        "tiktok":   tads.is_configured,
    }
    return data


def _format_data_for_prompt(data: dict, req: ReportRequest) -> str:
    lines = []

    if "google" in data and "error" not in data["google"]:
        g = data["google"]
        lines.append(
            f"GOOGLE ADS ({req.days} ngày):\n"
            f"  Chi tiêu: {float(g.get('total_cost_vnd', 0)):,.0f}đ\n"
            f"  Clicks: {int(g.get('total_clicks', 0)):,}\n"
            f"  Impressions: {int(g.get('total_impressions', 0)):,}\n"
            f"  CTR: {g.get('avg_ctr', 0)}%\n"
            f"  CPC: {float(g.get('avg_cpc_vnd', 0)):,.0f}đ\n"
            f"  Conversions: {g.get('total_conversions', 0)}\n"
            f"  ROAS: {g.get('overall_roas', 0)}×\n"
            f"  Campaigns đang chạy: {g.get('active_campaigns', 0)}"
        )
    elif req.include_google and not data.get("_config", {}).get("google"):
        lines.append("GOOGLE ADS: Chưa kết nối API")

    if "facebook" in data and "error" not in data["facebook"]:
        f = data["facebook"]
        lines.append(
            f"FACEBOOK ADS ({req.days} ngày):\n"
            f"  Chi tiêu: {float(f.get('spend_vnd', 0)):,.0f}đ\n"
            f"  Clicks: {int(f.get('clicks', 0)):,}\n"
            f"  Impressions: {int(f.get('impressions', 0)):,}\n"
            f"  CTR: {f.get('ctr', 0)}%\n"
            f"  CPC: {float(f.get('cpc_vnd', 0)):,.0f}đ\n"
            f"  Purchases: {f.get('purchases', 0)}\n"
            f"  ROAS: {f.get('roas', 0)}×\n"
            f"  Frequency: {f.get('frequency', 0)}×\n"
            f"  Reach: {int(f.get('reach', 0)):,}"
        )
    elif req.include_facebook and not data.get("_config", {}).get("facebook"):
        lines.append("FACEBOOK ADS: Chưa kết nối API")

    if "tiktok" in data and "error" not in data["tiktok"]:
        t = data["tiktok"]
        lines.append(
            f"TIKTOK ADS ({req.days} ngày):\n"
            f"  Chi tiêu: {float(t.get('spend_vnd', 0)):,.0f}đ\n"
            f"  Clicks: {int(t.get('clicks', 0)):,}\n"
            f"  Impressions: {int(t.get('impressions', 0)):,}\n"
            f"  CTR: {t.get('ctr', 0)}%\n"
            f"  CPC: {float(t.get('cpc_vnd', 0)):,.0f}đ\n"
            f"  VTR 6s: {t.get('vtr_6s', 0)}%\n"
            f"  CPM: {float(t.get('cpm_vnd', 0)):,.0f}đ"
        )
    elif req.include_tiktok and not data.get("_config", {}).get("tiktok"):
        lines.append("TIKTOK ADS: Chưa kết nối API")

    return "\n\n".join(lines) if lines else "Không có dữ liệu platform nào được kết nối."


def _build_prompt(data_text: str, req: ReportRequest) -> str:
    report_labels = {
        "weekly":              "Báo cáo tuần",
        "monthly":             "Báo cáo tháng",
        "campaign_summary":    "Tóm tắt Campaign",
        "platform_comparison": "So sánh Platform",
    }
    label = report_labels.get(req.report_type, "Báo cáo Marketing")
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    extra = f"\n\nGhi chú từ marketer: {req.extra_notes}" if req.extra_notes.strip() else ""

    return f"""Bạn là chuyên gia marketing cấp cao tại FuviAI — nền tảng AI Marketing hàng đầu Việt Nam.
Hãy viết **{label}** cho thương hiệu **{req.brand_name}** (ngành: {req.industry}) bằng tiếng Việt chuyên nghiệp.

Ngày báo cáo: {today}
Kỳ phân tích: {req.days} ngày vừa qua

=== DỮ LIỆU THỰC TẾ ===
{data_text}{extra}

=== YÊU CẦU BÁO CÁO ===
Viết báo cáo markdown đầy đủ bao gồm:

1. **Tóm tắt điều hành** (Executive Summary — 3-5 điểm bullet)
2. **Hiệu suất theo Platform** — phân tích từng platform được kết nối:
   - Kết quả đạt được (chi tiêu, clicks, CTR, ROAS)
   - So sánh với benchmark ngành {req.industry}
   - Điểm mạnh và hạn chế
3. **Phân bổ ngân sách** — nhận xét về hiệu quả chi tiêu
4. **Top 3 Insights quan trọng nhất**
5. **Đề xuất hành động ưu tiên** (Action Items — {req.days // 7} tuần tới):
   - Ưu tiên cao (thực hiện ngay)
   - Ưu tiên trung bình
   - Ưu tiên thấp
6. **Dự báo & Cơ hội** — xu hướng cần chú ý cho kỳ tới

Viết chuyên nghiệp, cụ thể với con số thực tế, tránh chung chung.
Sử dụng markdown (## headings, **bold**, bullet points, bảng nếu cần).
Độ dài: 600-900 từ."""


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=ReportResponse)
async def generate_report(req: ReportRequest):
    """
    Tạo báo cáo marketing AI tiếng Việt — tổng hợp dữ liệu thực từ tất cả platform đã kết nối.
    """
    if req.days < 1 or req.days > 180:
        raise HTTPException(status_code=422, detail="days phải từ 1-180")

    # 1. Thu thập dữ liệu từ các platform
    logger.info(f"Generating {req.report_type} report | brand={req.brand_name} | days={req.days}")
    platform_data = _collect_platform_data(req)
    data_text = _format_data_for_prompt(platform_data, req)

    # 2. Gọi Claude AI để viết báo cáo
    agent = _get_agent()
    prompt = _build_prompt(data_text, req)
    try:
        report_md = await agent.chat(prompt)
    except Exception as e:
        logger.error(f"Report AI generation failed: {e}")
        raise HTTPException(status_code=503, detail=f"AI generation failed: {e}")

    # 3. Danh sách platform đã có dữ liệu
    included = []
    cfg = platform_data.get("_config", {})
    if req.include_google and cfg.get("google"):
        included.append("Google Ads")
    if req.include_facebook and cfg.get("facebook"):
        included.append("Facebook Ads")
    if req.include_tiktok and cfg.get("tiktok"):
        included.append("TikTok Ads")

    logger.info(f"Report generated | {len(included)} platforms | ~{len(report_md.split()):,} words")

    return ReportResponse(
        report_type=req.report_type,
        days=req.days,
        brand_name=req.brand_name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        platforms_included=included,
        report_markdown=report_md,
        word_count=len(report_md.split()),
    )


@router.get("/templates")
async def get_templates():
    """Danh sách loại báo cáo có thể tạo."""
    return {
        "templates": [
            {
                "type": "weekly",
                "label": "Báo cáo Tuần",
                "description": "Tóm tắt hiệu suất 7 ngày, so sánh tuần trước",
                "recommended_days": 7,
            },
            {
                "type": "monthly",
                "label": "Báo cáo Tháng",
                "description": "Phân tích toàn diện 30 ngày, ROAS, budget efficiency",
                "recommended_days": 30,
            },
            {
                "type": "campaign_summary",
                "label": "Tóm tắt Campaign",
                "description": "Đánh giá campaign cụ thể, A/B test, insights",
                "recommended_days": 14,
            },
            {
                "type": "platform_comparison",
                "label": "So sánh Platform",
                "description": "Google vs Facebook vs TikTok — phân tích chi tiết",
                "recommended_days": 30,
            },
        ]
    }
