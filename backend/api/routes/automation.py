"""
FuviAI Marketing Agent — /api/automation/* routes
Campaign analysis, sentiment, social scheduling
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Any
from loguru import logger

from backend.agents.campaign_agent import CampaignAgent
from backend.agents.insight_agent import InsightAgent
from backend.agents.social_agent import SocialAgent
from backend.agents.content_agent import Platform

router = APIRouter()

_campaign_agent = None
_insight_agent = None
_social_agent = None


def get_campaign_agent() -> CampaignAgent:
    global _campaign_agent
    if _campaign_agent is None:
        _campaign_agent = CampaignAgent()
    return _campaign_agent


def get_insight_agent() -> InsightAgent:
    global _insight_agent
    if _insight_agent is None:
        _insight_agent = InsightAgent()
    return _insight_agent


def get_social_agent() -> SocialAgent:
    global _social_agent
    if _social_agent is None:
        _social_agent = SocialAgent()
    return _social_agent


# ─── Request Models ──────────────────────────────────────────────────────────

class CampaignAnalysisRequest(BaseModel):
    csv_content: str
    platform: str = "facebook"


class BudgetOptimizeRequest(BaseModel):
    current_budget: dict[str, float]
    goal: str = "tối đa ROAS"
    season: str = ""


class ABTestRequest(BaseModel):
    objective: str
    current_approach: str
    budget: float = 5_000_000


class WeeklyReportRequest(BaseModel):
    metrics: dict[str, Any]
    previous_metrics: dict[str, Any] | None = None


class SentimentRequest(BaseModel):
    texts: list[str]


class VOCRequest(BaseModel):
    feedbacks: list[str]
    source: str = "tổng hợp"


class RFMRequest(BaseModel):
    customer_data: list[dict[str, Any]]


class PostNowRequest(BaseModel):
    content: str
    platform: str = "facebook"
    user_id: str = ""


class ScheduleRequest(BaseModel):
    content: str
    platform: str = "facebook"
    scheduled_time: str  # ISO format: "2026-03-10T19:00:00"


class WeeklyScheduleRequest(BaseModel):
    product: str
    platforms: list[str] = ["facebook", "zalo"]
    campaign_theme: str = ""


class CommentReplyRequest(BaseModel):
    comment: str
    brand_tone: str = "thân thiện"
    context: str = ""


class RepurposeRequest(BaseModel):
    original_content: str
    original_platform: str
    target_platforms: list[str]


# ─── Campaign Endpoints ──────────────────────────────────────────────────────

@router.post("/campaign/analyze")
async def analyze_campaign(request: CampaignAnalysisRequest):
    """Phân tích campaign CSV và đưa ra 5 đề xuất cải thiện."""
    if not request.csv_content.strip():
        raise HTTPException(status_code=400, detail="CSV content không được để trống")
    try:
        agent = get_campaign_agent()
        result = agent.analyze_csv(request.csv_content, request.platform)
        return {"platform": request.platform, "analysis": result}
    except Exception as e:
        logger.error(f"Campaign analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign/optimize-budget")
async def optimize_budget(request: BudgetOptimizeRequest):
    """Tối ưu phân bổ ngân sách giữa các platform."""
    if not request.current_budget:
        raise HTTPException(status_code=400, detail="Budget không được để trống")
    try:
        agent = get_campaign_agent()
        result = agent.optimize_budget(
            request.current_budget, request.goal, request.season
        )
        return {"goal": request.goal, "recommendation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign/ab-test")
async def design_ab_test(request: ABTestRequest):
    """Thiết kế A/B test cho campaign."""
    try:
        agent = get_campaign_agent()
        result = agent.design_ab_test(
            request.objective, request.current_approach, request.budget
        )
        return {"ab_test_design": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/campaign/weekly-report")
async def weekly_report(request: WeeklyReportRequest):
    """Tạo báo cáo campaign tuần."""
    try:
        agent = get_campaign_agent()
        result = agent.weekly_report(request.metrics, request.previous_metrics)
        return {"report": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Insight Endpoints ───────────────────────────────────────────────────────

@router.post("/insight/sentiment")
async def analyze_sentiment(request: SentimentRequest):
    """Phân tích sentiment tiếng Việt (Bắc/Trung/Nam)."""
    if not request.texts:
        raise HTTPException(status_code=400, detail="Texts không được để trống")
    if len(request.texts) > 500:
        raise HTTPException(status_code=400, detail="Tối đa 500 texts mỗi lần")
    try:
        agent = get_insight_agent()
        result = agent.analyze_sentiment(request.texts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insight/voc")
async def voice_of_customer(request: VOCRequest):
    """Tổng hợp Voice of Customer từ feedbacks."""
    if not request.feedbacks:
        raise HTTPException(status_code=400, detail="Feedbacks không được để trống")
    try:
        agent = get_insight_agent()
        result = agent.voice_of_customer(request.feedbacks, request.source)
        return {"source": request.source, "voc_report": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insight/rfm")
async def rfm_segmentation(request: RFMRequest):
    """Phân khúc khách hàng theo RFM."""
    if not request.customer_data:
        raise HTTPException(status_code=400, detail="Customer data không được để trống")
    try:
        agent = get_insight_agent()
        result = agent.rfm_segmentation(request.customer_data)
        return {"customer_count": len(request.customer_data), "segmentation": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/insight/crisis-check")
async def detect_crisis(request: SentimentRequest):
    """Phát hiện khủng hoảng truyền thông từ comments."""
    if not request.texts:
        raise HTTPException(status_code=400, detail="Texts không được để trống")
    try:
        agent = get_insight_agent()
        result = agent.detect_crisis(request.texts)
        if result["is_crisis"]:
            logger.warning(f"CRISIS DETECTED | severity={result['severity']}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Social Scheduling Endpoints ─────────────────────────────────────────────

@router.post("/social/post-now")
async def post_now(request: PostNowRequest):
    """Đăng bài ngay lên platform."""
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="Content không được để trống")
    try:
        platform_map = {p.value: p for p in Platform}
        platform = platform_map.get(request.platform)
        if not platform:
            raise HTTPException(status_code=400, detail=f"Platform không hợp lệ: {request.platform}")
        agent = get_social_agent()
        result = agent.post_now(request.content, platform, request.user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/schedule")
async def schedule_post(request: ScheduleRequest):
    """Lên lịch đăng bài."""
    from datetime import datetime
    try:
        scheduled_time = datetime.fromisoformat(request.scheduled_time)
    except ValueError:
        raise HTTPException(status_code=400, detail="scheduled_time không đúng format ISO (VD: 2026-03-10T19:00:00)")

    try:
        platform_map = {p.value: p for p in Platform}
        platform = platform_map.get(request.platform)
        if not platform:
            raise HTTPException(status_code=400, detail=f"Platform không hợp lệ")
        agent = get_social_agent()
        post = agent.schedule_post(request.content, platform, scheduled_time)
        return post.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social/schedule")
async def get_schedule(status: str | None = None):
    """Lấy danh sách lịch đăng."""
    agent = get_social_agent()
    return {"schedule": agent.get_schedule(status)}


@router.post("/social/weekly-plan")
async def create_weekly_plan(request: WeeklyScheduleRequest):
    """Tạo content plan 7 ngày với AI."""
    if not request.product.strip():
        raise HTTPException(status_code=400, detail="Product không được để trống")
    try:
        agent = get_social_agent()
        result = agent.create_weekly_schedule(
            product=request.product,
            campaign_theme=request.campaign_theme,
        )
        return {"product": request.product, "content_plan": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/reply-comment")
async def generate_reply(request: CommentReplyRequest):
    """Tạo reply comment tự động."""
    if not request.comment.strip():
        raise HTTPException(status_code=400, detail="Comment không được để trống")
    try:
        agent = get_social_agent()
        reply = agent.generate_comment_reply(
            request.comment, request.brand_tone, request.context
        )
        return {"comment": request.comment, "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/social/repurpose")
async def repurpose_content(request: RepurposeRequest):
    """Adapt content từ 1 platform sang các platform khác."""
    try:
        agent = get_social_agent()
        result = agent.repurpose_content(
            request.original_content,
            request.original_platform,
            request.target_platforms,
        )
        return {
            "original_platform": request.original_platform,
            "target_platforms": request.target_platforms,
            "repurposed_content": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
