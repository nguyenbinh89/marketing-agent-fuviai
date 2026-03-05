"""
FuviAI Marketing Agent — /api/commerce/* routes
Livestream, Ad Budget, Personalization, Compliance, Orchestrator
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

# ─── Lazy singletons ─────────────────────────────────────────────────────────

_livestream_agent = None
_adbudget_agent = None
_personalize_agent = None
_compliance_agent = None
_orchestrator = None


def get_livestream_agent():
    global _livestream_agent
    if _livestream_agent is None:
        from backend.agents.livestream_agent import LivestreamAgent
        _livestream_agent = LivestreamAgent()
    return _livestream_agent


def get_adbudget_agent():
    global _adbudget_agent
    if _adbudget_agent is None:
        from backend.agents.adbudget_agent import AdBudgetAgent
        _adbudget_agent = AdBudgetAgent()
    return _adbudget_agent


def get_personalize_agent():
    global _personalize_agent
    if _personalize_agent is None:
        from backend.agents.personalize_agent import PersonalizeAgent
        _personalize_agent = PersonalizeAgent()
    return _personalize_agent


def get_compliance_agent():
    global _compliance_agent
    if _compliance_agent is None:
        from backend.agents.compliance_agent import ComplianceAgent
        _compliance_agent = ComplianceAgent()
    return _compliance_agent


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from backend.agents.orchestrator import MarketingOrchestrator
        _orchestrator = MarketingOrchestrator()
    return _orchestrator


# ─── Request Models ──────────────────────────────────────────────────────────

# Livestream
class StartSessionRequest(BaseModel):
    product: str
    platform: str = "tiktok"
    target_revenue: float = 0
    session_id: str = ""


class ScriptRequest(BaseModel):
    session_id: str
    current_viewers: int
    comments: list[str] = []
    revenue_this_segment: float = 0


class FlashDealRequest(BaseModel):
    session_id: str
    discount_percent: int
    slots: int
    duration_minutes: int = 10


class BatchReplyRequest(BaseModel):
    comments: list[str]
    product_info: str = ""
    brand_tone: str = "thân thiện, năng lượng cao"


class PrepareScriptRequest(BaseModel):
    product: str
    platform: str = "tiktok"
    duration_minutes: int = 60
    target_revenue: float = 0


# AdBudget
class QuarterlyForecastRequest(BaseModel):
    budget: float
    industry: str
    quarter: int
    year: int = 2027


class AnnualPlanRequest(BaseModel):
    annual_budget: float
    industry: str
    primary_goal: str = "cân bằng awareness và conversion"
    channels: list[str] = ["facebook", "tiktok", "zalo", "google"]


class SeasonBoostRequest(BaseModel):
    base_budget: float
    season_key: str
    industry: str


class ChannelAllocateRequest(BaseModel):
    budget: float
    goal: str = "conversion"
    industry: str = "general"
    current_month: int = 3


class ROASForecastRequest(BaseModel):
    spend: float
    platform: str
    industry: str
    campaign_type: str = "conversion"
    historical_roas: float | None = None


class EmergencyReallocRequest(BaseModel):
    current_allocation: dict[str, float]
    underperforming: str
    overperforming: str


# Personalize
class SegmentRequest(BaseModel):
    customers: list[dict[str, Any]]


class PersonalizedEmailRequest(BaseModel):
    customer: dict[str, Any]
    segment: str = "potential"
    product_context: str = "FuviAI Marketing Agent"
    trigger: str = ""


class ZaloPersonalRequest(BaseModel):
    customer: dict[str, Any]
    segment: str
    offer: str = ""


class SegmentVariantsRequest(BaseModel):
    base_message: str
    segments: list[str]
    channel: str = "email"


class TriggerFlowRequest(BaseModel):
    trigger_event: str
    product: str = "FuviAI"
    segment: str = "all"


class AbandonedCartRequest(BaseModel):
    cart_value: float
    products: list[str]
    customer_name: str = "bạn"
    segment: str = "potential"


class BirthdayRequest(BaseModel):
    customer_name: str
    tier: str = "loyal"
    birthday_offer: str = ""


class UpsellRequest(BaseModel):
    customer: dict[str, Any]
    current_product: str
    available_upgrades: list[str]


# Compliance
class ComplianceCheckRequest(BaseModel):
    content: str
    platform: str = "facebook"
    content_type: str = "social_post"
    industry: str = "general"


class BatchComplianceRequest(BaseModel):
    contents: list[str]
    platform: str = "facebook"


class FixContentRequest(BaseModel):
    content: str
    issues: list[dict] | None = None
    platform: str = "facebook"


# Orchestrator
class CampaignPlanRequest(BaseModel):
    task: str
    product: str
    industry: str = "marketing"
    budget: float = 100_000_000
    season: str = ""


# ═══════════════════════════════════════════════════════════════════════
# LIVESTREAM ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/livestream/start")
async def start_livestream_session(request: StartSessionRequest):
    """Bắt đầu session livestream mới."""
    if not request.product.strip():
        raise HTTPException(status_code=400, detail="product không được để trống")
    try:
        agent = get_livestream_agent()
        session = agent.start_session(
            request.product, request.platform,
            request.target_revenue, request.session_id,
        )
        return {"message": "Session đã bắt đầu", "session": session.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/livestream/script")
async def suggest_script(request: ScriptRequest):
    """Gợi ý script real-time cho host (< 2 giây)."""
    try:
        agent = get_livestream_agent()
        session = agent.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session không tồn tại: {request.session_id}")
        script = agent.suggest_next_script(
            session, request.current_viewers,
            request.comments, request.revenue_this_segment,
        )
        return {"script": script, "session": session.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/livestream/flash-deal")
async def trigger_flash_deal(request: FlashDealRequest):
    """Tung flash deal kèm script announcement."""
    try:
        agent = get_livestream_agent()
        session = agent.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session không tồn tại: {request.session_id}")
        result = agent.trigger_flash_deal(
            session, request.discount_percent,
            request.slots, request.duration_minutes,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/livestream/batch-reply")
async def batch_reply_comments(request: BatchReplyRequest):
    """Tạo reply cho nhiều comments livestream cùng lúc."""
    if not request.comments:
        raise HTTPException(status_code=400, detail="Comments không được để trống")
    try:
        agent = get_livestream_agent()
        replies = agent.batch_reply_comments(
            request.comments, request.product_info, request.brand_tone
        )
        return {"replies": replies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/livestream/prepare-script")
async def prepare_stream_script(request: PrepareScriptRequest):
    """Tạo script khung trước khi bắt đầu stream."""
    try:
        agent = get_livestream_agent()
        script = agent.prepare_stream_script(
            request.product, request.platform,
            request.duration_minutes, request.target_revenue,
        )
        return {"product": request.product, "platform": request.platform, "script": script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/livestream/{session_id}/next-script")
async def next_script_for_session(session_id: str, request: ScriptRequest):
    """Gợi ý script tiếp theo cho session (path param version)."""
    try:
        agent = get_livestream_agent()
        session = agent.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session không tồn tại: {session_id}")
        script = agent.suggest_next_script(
            session, request.current_viewers,
            request.comments, request.revenue_this_segment,
        )
        return {"script": script, "session": session.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/livestream/{session_id}/flash-deal")
async def flash_deal_for_session(session_id: str, request: FlashDealRequest):
    """Trigger flash deal cho session (path param version)."""
    try:
        agent = get_livestream_agent()
        session = agent.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session không tồn tại: {session_id}")
        result = agent.trigger_flash_deal(
            session,
            request.discount_percent if hasattr(request, "discount_percent") else 20,
            request.slots if hasattr(request, "slots") else 10,
            request.duration_minutes,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/livestream/{session_id}/end")
async def end_session(session_id: str):
    """Kết thúc livestream và lấy summary."""
    agent = get_livestream_agent()
    result = agent.end_session(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/livestream/sessions")
async def list_sessions():
    """Danh sách sessions đang active."""
    agent = get_livestream_agent()
    return {"sessions": agent.list_sessions()}


# ═══════════════════════════════════════════════════════════════════════
# AD BUDGET ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/budget/forecast/quarterly")
async def quarterly_forecast(request: QuarterlyForecastRequest):
    """Dự báo ngân sách cho 1 quý (±15% accuracy)."""
    if not 1 <= request.quarter <= 4:
        raise HTTPException(status_code=400, detail="quarter phải từ 1 đến 4")
    try:
        agent = get_adbudget_agent()
        result = agent.forecast_quarterly(
            request.budget, request.industry, request.quarter, request.year
        )
        return {"quarter": request.quarter, "year": request.year, "forecast": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/plan/annual")
async def annual_budget_plan(request: AnnualPlanRequest):
    """Lập kế hoạch ngân sách cả năm theo mùa vụ VN."""
    try:
        agent = get_adbudget_agent()
        result = agent.annual_budget_plan(
            request.annual_budget, request.industry,
            request.primary_goal, request.channels,
        )
        return {"annual_budget": request.annual_budget, "plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/season-boost")
async def season_budget_boost(request: SeasonBoostRequest):
    """Tính budget cần thiết cho mùa vụ cụ thể."""
    try:
        agent = get_adbudget_agent()
        result = agent.season_budget_boost(
            request.base_budget, request.season_key, request.industry
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/allocate")
async def allocate_by_channel(request: ChannelAllocateRequest):
    """Phân bổ budget tối ưu giữa các kênh."""
    try:
        agent = get_adbudget_agent()
        result = agent.allocate_by_channel(
            request.budget, request.goal, request.industry, request.current_month
        )
        return {"budget": request.budget, "allocation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/forecast/roas")
async def forecast_roas(request: ROASForecastRequest):
    """Dự báo ROAS cho campaign cụ thể."""
    try:
        agent = get_adbudget_agent()
        result = agent.forecast_roas(
            request.spend, request.platform, request.industry,
            request.campaign_type, request.historical_roas,
        )
        return {"platform": request.platform, "spend": request.spend, "forecast": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/budget/emergency-realloc")
async def emergency_reallocation(request: EmergencyReallocRequest):
    """Tái phân bổ ngân sách khẩn cấp khi 1 kênh underperform."""
    if not request.current_allocation:
        raise HTTPException(status_code=400, detail="current_allocation không được để trống")
    try:
        agent = get_adbudget_agent()
        result = agent.emergency_budget_reallocation(
            request.current_allocation, request.underperforming, request.overperforming
        )
        return {"recommendation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/budget/season-calendar")
async def get_season_calendar():
    """Lịch mùa vụ quảng cáo VN."""
    agent = get_adbudget_agent()
    return {"calendar": agent.get_season_calendar()}


# ═══════════════════════════════════════════════════════════════════════
# PERSONALIZATION ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/personalize/segment")
async def segment_customers(request: SegmentRequest):
    """Phân khúc khách hàng theo CLV tier."""
    if not request.customers:
        raise HTTPException(status_code=400, detail="customers không được để trống")
    if len(request.customers) > 1000:
        raise HTTPException(status_code=400, detail="Tối đa 1000 customers mỗi lần")
    try:
        agent = get_personalize_agent()
        result = agent.segment_customers(request.customers)
        # Build per-customer segments list for frontend
        segments = [
            {
                "customer_id": c.get("customer_id", str(i)),
                "name": c.get("name", f"Customer {i}"),
                "tier": agent.calculate_clv_tier(
                    c.get("total_spent", 0),
                    c.get("days_since_last_purchase", 999),
                    c.get("purchase_count", 0),
                ),
                "strategy": result.get("ai_strategy", "")[:200],
            }
            for i, c in enumerate(request.customers)
        ]
        return {
            "total": result["total"],
            "summary": result["summary"],
            "ai_strategy": result["ai_strategy"],
            "segments": segments,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalize/email")
async def personalized_email(request: PersonalizedEmailRequest):
    """Tạo email cá nhân hoá theo CLV segment và trigger."""
    try:
        agent = get_personalize_agent()
        result = agent.personalized_email(
            request.customer, request.segment,
            request.product_context, request.trigger,
        )
        return {"segment": request.segment, "trigger": request.trigger, "email": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalize/zalo")
async def personalized_zalo(request: ZaloPersonalRequest):
    """Tạo Zalo message cá nhân hoá."""
    try:
        agent = get_personalize_agent()
        result = agent.personalized_zalo_message(
            request.customer, request.segment, request.offer
        )
        return {"segment": request.segment, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalize/segment-variants")
async def segment_variants(request: SegmentVariantsRequest):
    """Tạo biến thể content cho nhiều segments."""
    if not request.base_message.strip():
        raise HTTPException(status_code=400, detail="base_message không được để trống")
    if not request.segments:
        raise HTTPException(status_code=400, detail="segments không được để trống")
    try:
        agent = get_personalize_agent()
        variants = agent.create_segment_variants(
            request.base_message, request.segments, request.channel
        )
        return {"channel": request.channel, "variants": variants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalize/trigger-flow")
async def design_trigger_flow(request: TriggerFlowRequest):
    """Thiết kế automation flow cho trigger event."""
    try:
        agent = get_personalize_agent()
        result = agent.design_trigger_flow(
            request.trigger_event, request.product, request.segment
        )
        return {"trigger": request.trigger_event, "flow": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalize/abandoned-cart")
async def abandoned_cart_sequence(request: AbandonedCartRequest):
    """Tạo 3-email sequence cho abandoned cart."""
    if not request.products:
        raise HTTPException(status_code=400, detail="products không được để trống")
    try:
        agent = get_personalize_agent()
        result = agent.abandoned_cart_sequence(
            request.cart_value, request.products,
            request.customer_name, request.segment,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalize/birthday")
async def birthday_campaign(request: BirthdayRequest):
    """Tạo birthday campaign (Zalo + Email)."""
    try:
        agent = get_personalize_agent()
        result = agent.birthday_campaign(
            request.customer_name, request.tier, request.birthday_offer
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personalize/upsell")
async def upsell_recommendation(request: UpsellRequest):
    """Tạo upsell message cá nhân hoá."""
    if not request.available_upgrades:
        raise HTTPException(status_code=400, detail="available_upgrades không được để trống")
    try:
        agent = get_personalize_agent()
        result = agent.upsell_recommendation(
            request.customer, request.current_product, request.available_upgrades
        )
        return {"upsell_message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# COMPLIANCE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/compliance/check")
async def check_compliance(request: ComplianceCheckRequest):
    """Kiểm tra compliance content trước khi đăng."""
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="content không được để trống")
    try:
        agent = get_compliance_agent()
        result = agent.check_content(
            request.content, request.platform,
            request.content_type, request.industry,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/batch-check")
async def batch_compliance_check(request: BatchComplianceRequest):
    """Kiểm tra compliance cho nhiều content cùng lúc."""
    if not request.contents:
        raise HTTPException(status_code=400, detail="contents không được để trống")
    if len(request.contents) > 20:
        raise HTTPException(status_code=400, detail="Tối đa 20 contents mỗi lần")
    try:
        agent = get_compliance_agent()
        results = agent.batch_check(request.contents, request.platform)
        failed = sum(1 for r in results if r["verdict"] == "FAIL")
        warnings = sum(1 for r in results if r["verdict"] == "WARNING")
        return {
            "total": len(results),
            "failed": failed,
            "warnings": warnings,
            "passed": len(results) - failed - warnings,
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/fix")
async def fix_content(request: FixContentRequest):
    """Tự động sửa content vi phạm để compliant."""
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="content không được để trống")
    try:
        agent = get_compliance_agent()
        result = agent.fix_content(request.content, request.issues, request.platform)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/policies/{platform}")
async def get_platform_policy(platform: str):
    """Tóm tắt policy quảng cáo của platform."""
    agent = get_compliance_agent()
    policy = agent.get_platform_policies(platform)
    return {"platform": platform, "policy": policy}


@router.post("/compliance/checklist")
async def pre_publish_checklist(content: str, platform: str = "facebook", industry: str = "general"):
    """Tạo checklist kiểm tra trước khi đăng."""
    if not content.strip():
        raise HTTPException(status_code=400, detail="content không được để trống")
    try:
        agent = get_compliance_agent()
        result = agent.pre_publish_checklist(content, platform, industry)
        return {"platform": platform, "checklist": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════
# ORCHESTRATOR ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════

@router.post("/orchestrate/campaign-plan")
async def orchestrate_campaign_plan(request: CampaignPlanRequest):
    """
    Full multi-agent workflow: Research → Competitor → SEO → Content → Budget → Compliance → Report.
    Trả về kế hoạch campaign hoàn chỉnh (~2-3 phút).
    """
    if not request.task.strip() or not request.product.strip():
        raise HTTPException(status_code=400, detail="task và product không được để trống")
    try:
        orch = get_orchestrator()
        state = await orch.run_campaign_plan_async(
            task=request.task,
            product=request.product,
            industry=request.industry,
            budget=request.budget,
            season=request.season,
        )
        return {
            "task": request.task,
            "completed_nodes": state.get("completed_nodes", []),
            "errors": state.get("errors", []),
            "final_report": state.get("final_report", ""),
            "sections": {
                "market_data": state.get("market_data", "")[:500],
                "competitor_data": state.get("competitor_data", "")[:500],
                "content_plan": state.get("content_plan", "")[:500],
                "budget_allocation": state.get("budget_allocation", "")[:500],
            },
        }
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrate/campaign-plan/stream")
async def stream_campaign_plan(request: CampaignPlanRequest):
    """
    Stream kế hoạch campaign — nhìn thấy progress real-time theo từng agent.
    """
    if not request.task.strip() or not request.product.strip():
        raise HTTPException(status_code=400, detail="task và product không được để trống")

    async def _generate():
        try:
            orch = get_orchestrator()
            async for chunk in orch.stream_campaign_plan(
                task=request.task,
                product=request.product,
                industry=request.industry,
                budget=request.budget,
            ):
                yield chunk
        except Exception as e:
            yield f"\n\n[ERROR] {str(e)}"

    return StreamingResponse(_generate(), media_type="text/plain")
