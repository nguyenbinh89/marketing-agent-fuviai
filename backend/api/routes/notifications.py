"""
FuviAI Marketing Agent — /api/notifications/* routes
Smart alert system — tự động phát hiện bất thường trong ad campaigns
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Query
from loguru import logger
from pydantic import BaseModel

from backend.tools.google_ads_tool import GoogleAdsTool
from backend.tools.facebook_ads_tool import FacebookAdsTool
from backend.tools.tiktok_ads_tool import TikTokAdsTool

router = APIRouter()

AlertSeverity = Literal["critical", "warning", "info"]
AlertType = Literal["performance", "budget", "config", "crisis", "system"]

# Lazy singletons
_gads: GoogleAdsTool | None = None
_fads: FacebookAdsTool | None = None
_tads: TikTokAdsTool | None = None


class Alert(BaseModel):
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    platform: str | None = None
    timestamp: str
    action_url: str | None = None


def _get_tools() -> tuple[GoogleAdsTool, FacebookAdsTool, TikTokAdsTool]:
    global _gads, _fads, _tads
    if _gads is None:
        _gads = GoogleAdsTool()
    if _fads is None:
        _fads = FacebookAdsTool()
    if _tads is None:
        _tads = TikTokAdsTool()
    return _gads, _fads, _tads


def _uid() -> str:
    return str(uuid.uuid4())[:8]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Benchmark thresholds (ecommerce ngành rộng)
_CTR_BENCH  = {"Google Ads": 2.0,   "Facebook Ads": 1.5,   "TikTok Ads": 1.0}
_CPC_BENCH  = {"Google Ads": 5_000, "Facebook Ads": 3_000, "TikTok Ads": 2_000}   # VNĐ
_ROAS_BENCH = {"Google Ads": 4.0,   "Facebook Ads": 3.5,   "TikTok Ads": 2.5}


def _generate_alerts(days: int = 30) -> list[Alert]:
    gads, fads, tads = _get_tools()
    alerts: list[Alert] = []
    now = _now()

    # ── Google Ads ────────────────────────────────────────────────────────────
    if not gads.is_configured:
        alerts.append(Alert(
            id=_uid(), type="config", severity="warning",
            title="Google Ads chưa cấu hình",
            message=(
                "Thêm GOOGLE_ADS_DEVELOPER_TOKEN, GOOGLE_ADS_CLIENT_ID, "
                "GOOGLE_ADS_CUSTOMER_ID vào .env để kết nối Google Ads API."
            ),
            platform="Google Ads", timestamp=now, action_url="/google-ads",
        ))
    else:
        try:
            g = gads.get_account_summary(days)
            if "error" not in g:
                ctr   = float(g.get("avg_ctr", 0))
                cpc   = float(g.get("avg_cpc_vnd", 0))
                roas  = float(g.get("overall_roas", 0))
                spend = float(g.get("total_cost_vnd", 0))

                if ctr > 0 and ctr < _CTR_BENCH["Google Ads"] * 0.6:
                    alerts.append(Alert(
                        id=_uid(), type="performance", severity="warning",
                        title=f"Google Ads CTR thấp ({ctr:.2f}%)",
                        message=(
                            f"CTR {ctr:.2f}% thấp hơn 60% benchmark ngành "
                            f"({_CTR_BENCH['Google Ads']}%). "
                            "Kiểm tra ad copy, match type và Quality Score."
                        ),
                        platform="Google Ads", timestamp=now, action_url="/google-ads",
                    ))
                if cpc > _CPC_BENCH["Google Ads"] * 1.5:
                    alerts.append(Alert(
                        id=_uid(), type="performance", severity="warning",
                        title=f"Google Ads CPC cao ({cpc:,.0f}đ)",
                        message=(
                            f"CPC {cpc:,.0f}đ vượt 1.5× benchmark ({_CPC_BENCH['Google Ads']:,}đ). "
                            "Xem xét điều chỉnh bid strategy hoặc cải thiện Quality Score."
                        ),
                        platform="Google Ads", timestamp=now, action_url="/google-ads",
                    ))
                if roas > 0 and roas < _ROAS_BENCH["Google Ads"] * 0.7:
                    alerts.append(Alert(
                        id=_uid(), type="performance", severity="critical",
                        title=f"Google Ads ROAS nguy hiểm ({roas:.1f}×)",
                        message=(
                            f"ROAS {roas:.1f}× dưới ngưỡng an toàn "
                            f"({_ROAS_BENCH['Google Ads'] * 0.7:.1f}×). "
                            "Cân nhắc tạm dừng campaign tệ và tập trung ngân sách vào top performer."
                        ),
                        platform="Google Ads", timestamp=now, action_url="/google-ads",
                    ))
                if spend > 0:
                    alerts.append(Alert(
                        id=_uid(), type="system", severity="info",
                        title="Google Ads đang hoạt động",
                        message=(
                            f"Chi {spend:,.0f}đ trong {days} ngày | "
                            f"{g.get('active_campaigns', 0)} campaigns | "
                            f"CTR {ctr:.2f}% | ROAS {roas:.1f}×"
                        ),
                        platform="Google Ads", timestamp=now, action_url="/google-ads",
                    ))
        except Exception as e:
            logger.warning(f"Notification Google Ads error: {e}")
            alerts.append(Alert(
                id=_uid(), type="system", severity="warning",
                title="Google Ads API lỗi",
                message=str(e)[:120],
                platform="Google Ads", timestamp=now, action_url="/google-ads",
            ))

    # ── Facebook Ads ──────────────────────────────────────────────────────────
    if not fads.is_configured:
        alerts.append(Alert(
            id=_uid(), type="config", severity="warning",
            title="Facebook Ads chưa cấu hình",
            message=(
                "Thêm FACEBOOK_ACCESS_TOKEN và FACEBOOK_AD_ACCOUNT_ID vào .env "
                "để kết nối Facebook Marketing API v21.0."
            ),
            platform="Facebook Ads", timestamp=now, action_url="/facebook-ads",
        ))
    else:
        try:
            f = fads.get_account_insights(days)
            if "error" not in f:
                ctr  = float(f.get("ctr", 0))
                cpc  = float(f.get("cpc_vnd", 0))
                roas = float(f.get("roas", 0))
                freq = float(f.get("frequency", 0))

                if ctr > 0 and ctr < _CTR_BENCH["Facebook Ads"] * 0.6:
                    alerts.append(Alert(
                        id=_uid(), type="performance", severity="warning",
                        title=f"Facebook Ads CTR thấp ({ctr:.2f}%)",
                        message=(
                            f"CTR {ctr:.2f}% thấp hơn benchmark ({_CTR_BENCH['Facebook Ads']}%). "
                            "Thay đổi creative, headline hoặc thu hẹp audience targeting."
                        ),
                        platform="Facebook Ads", timestamp=now, action_url="/facebook-ads",
                    ))
                if freq > 4.5:
                    alerts.append(Alert(
                        id=_uid(), type="performance", severity="warning",
                        title=f"Facebook Ads Frequency quá cao ({freq:.1f}×)",
                        message=(
                            f"Frequency {freq:.1f}× vượt ngưỡng 4.5× — ad fatigue nguy cơ cao. "
                            "Refresh creative hoặc mở rộng audience."
                        ),
                        platform="Facebook Ads", timestamp=now, action_url="/facebook-ads",
                    ))
                if roas > 0 and roas < _ROAS_BENCH["Facebook Ads"] * 0.7:
                    alerts.append(Alert(
                        id=_uid(), type="performance", severity="critical",
                        title=f"Facebook Ads ROAS nguy hiểm ({roas:.1f}×)",
                        message=(
                            f"ROAS {roas:.1f}× dưới ngưỡng. "
                            "Xem xét tối ưu landing page, offer và retargeting funnel."
                        ),
                        platform="Facebook Ads", timestamp=now, action_url="/facebook-ads",
                    ))
        except Exception as e:
            logger.warning(f"Notification Facebook Ads error: {e}")
            alerts.append(Alert(
                id=_uid(), type="system", severity="warning",
                title="Facebook Ads API lỗi",
                message=str(e)[:120],
                platform="Facebook Ads", timestamp=now, action_url="/facebook-ads",
            ))

    # ── TikTok Ads ────────────────────────────────────────────────────────────
    if not tads.is_configured:
        alerts.append(Alert(
            id=_uid(), type="config", severity="warning",
            title="TikTok Ads chưa cấu hình",
            message=(
                "Thêm TIKTOK_ADS_ACCESS_TOKEN và TIKTOK_ADS_ADVERTISER_ID vào .env "
                "để kết nối TikTok Ads Manager API v1.3."
            ),
            platform="TikTok Ads", timestamp=now, action_url="/tiktok-ads",
        ))
    else:
        try:
            t = tads.get_account_insights(days)
            if "error" not in t:
                ctr   = float(t.get("ctr", 0))
                vtr   = float(t.get("vtr_6s", 0))
                spend = float(t.get("spend_vnd", 0))

                if ctr > 0 and ctr < _CTR_BENCH["TikTok Ads"] * 0.6:
                    alerts.append(Alert(
                        id=_uid(), type="performance", severity="warning",
                        title=f"TikTok Ads CTR thấp ({ctr:.2f}%)",
                        message=(
                            f"CTR {ctr:.2f}% thấp hơn benchmark ({_CTR_BENCH['TikTok Ads']}%). "
                            "Thử hook mạnh hơn trong 3 giây đầu, dùng trending sound."
                        ),
                        platform="TikTok Ads", timestamp=now, action_url="/tiktok-ads",
                    ))
                if vtr > 0 and vtr < 10.0:
                    alerts.append(Alert(
                        id=_uid(), type="performance", severity="info",
                        title=f"TikTok VTR 6s thấp ({vtr:.1f}%)",
                        message=(
                            f"View-through rate 6s = {vtr:.1f}% — người xem rời sớm. "
                            "Tối ưu phần mở đầu video (hook, text overlay, CTA sớm)."
                        ),
                        platform="TikTok Ads", timestamp=now, action_url="/tiktok-ads",
                    ))
                if spend > 0:
                    alerts.append(Alert(
                        id=_uid(), type="system", severity="info",
                        title="TikTok Ads đang hoạt động",
                        message=f"Chi {spend:,.0f}đ trong {days} ngày | CTR {ctr:.2f}% | VTR 6s {vtr:.1f}%",
                        platform="TikTok Ads", timestamp=now, action_url="/tiktok-ads",
                    ))
        except Exception as e:
            logger.warning(f"Notification TikTok Ads error: {e}")
            alerts.append(Alert(
                id=_uid(), type="system", severity="warning",
                title="TikTok Ads API lỗi",
                message=str(e)[:120],
                platform="TikTok Ads", timestamp=now, action_url="/tiktok-ads",
            ))

    # ── System tips ───────────────────────────────────────────────────────────
    n_configured = sum([gads.is_configured, fads.is_configured, tads.is_configured])
    if n_configured == 0:
        alerts.append(Alert(
            id=_uid(), type="system", severity="info",
            title="Chưa có platform nào được kết nối",
            message="Kết nối ít nhất 1 platform quảng cáo để nhận performance alerts tự động.",
            platform=None, timestamp=now, action_url="/ads",
        ))
    elif n_configured < 3:
        missing = [
            p for p, tool in [
                ("Google Ads", gads), ("Facebook Ads", fads), ("TikTok Ads", tads)
            ]
            if not tool.is_configured
        ]
        alerts.append(Alert(
            id=_uid(), type="system", severity="info",
            title=f"Còn {len(missing)} platform chưa kết nối",
            message=f"{', '.join(missing)} chưa cấu hình. Kết nối để có cái nhìn toàn diện.",
            platform=None, timestamp=now, action_url="/ads",
        ))

    # Sort: critical → warning → info
    _order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: _order.get(a.severity, 3))

    logger.info(
        f"Alerts generated: {len(alerts)} total | "
        f"critical={sum(1 for a in alerts if a.severity == 'critical')} | "
        f"warning={sum(1 for a in alerts if a.severity == 'warning')} | "
        f"info={sum(1 for a in alerts if a.severity == 'info')}"
    )
    return alerts


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[Alert])
async def list_notifications(days: int = Query(default=30, ge=1, le=90)):
    """
    Lấy danh sách notifications/alerts tự động từ tất cả ad platforms.
    Kiểm tra: performance thấp, CTR/CPC bất thường, platform chưa cấu hình.
    """
    return _generate_alerts(days)


@router.get("/count")
async def get_notification_count():
    """Đếm alerts (dùng cho badge header — kiểm tra 7 ngày gần nhất)."""
    alerts = _generate_alerts(7)
    return {
        "total":    len(alerts),
        "critical": sum(1 for a in alerts if a.severity == "critical"),
        "warning":  sum(1 for a in alerts if a.severity == "warning"),
        "info":     sum(1 for a in alerts if a.severity == "info"),
    }


@router.post("/check")
async def trigger_check(days: int = Query(default=30, ge=1, le=90)):
    """Refresh toàn bộ notification check (POST = explicit user action)."""
    return _generate_alerts(days)
