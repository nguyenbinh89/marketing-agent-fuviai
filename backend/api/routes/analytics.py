"""
FuviAI Marketing Agent — /api/analytics/* routes
Competitor Intelligence + Social Listening dashboard
"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

from backend.agents.competitor_agent import CompetitorAgent
from backend.agents.listening_agent import ListeningAgent

router = APIRouter()

_competitor_agent: CompetitorAgent | None = None
_listening_agent: ListeningAgent | None = None


def get_competitor_agent() -> CompetitorAgent:
    global _competitor_agent
    if _competitor_agent is None:
        _competitor_agent = CompetitorAgent()
    return _competitor_agent


def get_listening_agent() -> ListeningAgent:
    global _listening_agent
    if _listening_agent is None:
        _listening_agent = ListeningAgent()
    return _listening_agent


# ─── Request Models ──────────────────────────────────────────────────────────

class AddCompetitorRequest(BaseModel):
    name: str
    website: str
    facebook_page: str = ""
    industry: str = "general"


class CounterStrategyRequest(BaseModel):
    competitor_name: str
    trigger_event: str
    budget: float = 50_000_000
    timeline_days: int = 7


class BenchmarkRequest(BaseModel):
    fuviai_metrics: dict[str, Any]
    competitor_metrics: dict[str, dict[str, Any]]


class TrendScanRequest(BaseModel):
    industry: str = "marketing"
    hours_back: int = 24


class KeywordMonitorRequest(BaseModel):
    keywords: list[str]


class CrisisCheckRequest(BaseModel):
    texts: list[str]
    alert_zalo_user: str = ""


class TrendContentRequest(BaseModel):
    keyword: str
    sample_texts: list[str] = []
    platform: str = "facebook"


# ─── Competitor Endpoints ─────────────────────────────────────────────────────

@router.get("/competitors")
async def get_competitors_dashboard():
    """Dashboard tổng quan tất cả đối thủ đang theo dõi."""
    agent = get_competitor_agent()
    return agent.get_dashboard_data()


@router.post("/competitors/add")
async def add_competitor(request: AddCompetitorRequest):
    """Thêm đối thủ mới vào danh sách theo dõi."""
    if not request.name.strip() or not request.website.strip():
        raise HTTPException(status_code=400, detail="name và website không được để trống")
    try:
        agent = get_competitor_agent()
        profile = agent.add_competitor(
            request.name, request.website, request.facebook_page, request.industry
        )
        # Lấy snapshot ngay
        snapshot = agent.snapshot_competitor(request.name)
        return {
            "message": f"Đã thêm {request.name} vào danh sách theo dõi",
            "profile": profile.to_dict(),
            "initial_snapshot": {
                "title": snapshot.get("title", ""),
                "prices": snapshot.get("price_mentions", []),
            },
        }
    except Exception as e:
        logger.error(f"Add competitor error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/competitors/{name}")
async def remove_competitor(name: str):
    """Xóa đối thủ khỏi danh sách theo dõi."""
    agent = get_competitor_agent()
    success = agent.remove_competitor(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy đối thủ: {name}")
    return {"message": f"Đã xóa {name} khỏi danh sách"}


@router.post("/competitors/{name}/snapshot")
async def take_snapshot(name: str):
    """Chụp snapshot website đối thủ ngay lập tức."""
    try:
        agent = get_competitor_agent()
        snapshot = agent.snapshot_competitor(name)
        if "error" in snapshot:
            raise HTTPException(status_code=404, detail=snapshot["error"])
        return snapshot
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competitors/{name}/changes")
async def check_changes(name: str):
    """So sánh snapshot mới nhất vs trước đó, phát hiện thay đổi."""
    try:
        agent = get_competitor_agent()
        result = agent.check_for_changes(name)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/competitors/{name}/analyze")
async def analyze_competitor(name: str, context: str = ""):
    """Phân tích sâu 1 đối thủ với AI."""
    try:
        agent = get_competitor_agent()
        analysis = agent.analyze_competitor(name, context)
        return {"competitor": name, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/competitors/compare")
async def compare_competitors(names: list[str] | None = None):
    """So sánh nhiều đối thủ cùng lúc."""
    try:
        agent = get_competitor_agent()
        result = agent.compare_competitors(names)
        return {"comparison": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/competitors/counter-strategy")
async def generate_counter_strategy(request: CounterStrategyRequest):
    """Tạo counter-strategy khi đối thủ có động thái lớn (< 30 giây)."""
    if not request.trigger_event.strip():
        raise HTTPException(status_code=400, detail="trigger_event không được để trống")
    try:
        agent = get_competitor_agent()
        strategy = agent.generate_counter_strategy(
            request.competitor_name,
            request.trigger_event,
            request.budget,
            request.timeline_days,
        )
        return {
            "competitor": request.competitor_name,
            "trigger": request.trigger_event,
            "strategy": strategy,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/competitors/benchmark-engagement")
async def benchmark_engagement(request: BenchmarkRequest):
    """So sánh engagement rate FuviAI vs đối thủ theo tuần."""
    try:
        agent = get_competitor_agent()
        result = agent.benchmark_engagement(
            request.fuviai_metrics, request.competitor_metrics
        )
        return {"benchmark": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/competitors/daily-scan")
async def trigger_daily_scan(background_tasks: BackgroundTasks):
    """Trigger daily competitor scan thủ công (chạy background)."""
    def _scan():
        try:
            agent = get_competitor_agent()
            agent.daily_scan()
        except Exception as e:
            logger.error(f"Background competitor scan failed: {e}")

    background_tasks.add_task(_scan)
    return {"message": "Daily scan đang chạy background. Kết quả sẽ có sau vài phút."}


# ─── Social Listening Endpoints ───────────────────────────────────────────────

@router.post("/listening/scan")
async def scan_trends(request: TrendScanRequest):
    """Quét xu hướng theo ngành trong N giờ qua."""
    valid_industries = ["marketing", "fmcg", "fb", "realestate", "ecommerce"]
    if request.industry not in valid_industries:
        raise HTTPException(
            status_code=400,
            detail=f"industry phải là một trong: {valid_industries}"
        )
    try:
        agent = get_listening_agent()
        result = agent.scan_trends(request.industry, request.hours_back)
        return result
    except Exception as e:
        logger.error(f"Trend scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listening/keywords")
async def monitor_keywords(request: KeywordMonitorRequest):
    """Monitor danh sách keywords cụ thể."""
    if not request.keywords:
        raise HTTPException(status_code=400, detail="Keywords không được để trống")
    if len(request.keywords) > 20:
        raise HTTPException(status_code=400, detail="Tối đa 20 keywords mỗi lần")
    try:
        agent = get_listening_agent()
        results = agent.monitor_keywords(request.keywords)
        return {"keywords": request.keywords, "trends": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listening/crisis-check")
async def crisis_check(request: CrisisCheckRequest):
    """Kiểm tra và alert khủng hoảng truyền thông."""
    if not request.texts:
        raise HTTPException(status_code=400, detail="Texts không được để trống")
    try:
        agent = get_listening_agent()
        result = agent.check_and_alert_crisis(request.texts, request.alert_zalo_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listening/draft-content")
async def draft_trend_content(request: TrendContentRequest):
    """Tạo content ăn theo trend vừa phát hiện."""
    if not request.keyword.strip():
        raise HTTPException(status_code=400, detail="keyword không được để trống")
    try:
        from backend.agents.content_agent import Platform
        platform_map = {p.value: p for p in Platform}
        platform = platform_map.get(request.platform, Platform.FACEBOOK)

        agent = get_listening_agent()
        trend = {"keyword": request.keyword, "sample_texts": request.sample_texts}
        content = agent.draft_trend_content(trend, platform=platform)
        return {
            "keyword": request.keyword,
            "platform": request.platform,
            "content": content,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listening/crisis-response")
async def generate_crisis_response(crisis_context: str, brand: str = "FuviAI"):
    """Tạo statement phản hồi khủng hoảng."""
    if not crisis_context.strip():
        raise HTTPException(status_code=400, detail="crisis_context không được để trống")
    try:
        agent = get_listening_agent()
        response = agent.generate_crisis_response(crisis_context, brand)
        return {"brand": brand, "crisis_response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/listening/trend-history")
async def get_trend_history(limit: int = 20):
    """Lấy lịch sử trends đã phát hiện trong session."""
    agent = get_listening_agent()
    return {"trends": agent.get_trend_history(limit)}
