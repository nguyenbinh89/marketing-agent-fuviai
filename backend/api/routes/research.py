"""
FuviAI Marketing Agent — /api/research/* routes
Market research, keyword research, content summarization
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from backend.agents.research_agent import ResearchAgent
from backend.agents.seo_agent import SEOAgent

router = APIRouter()

_research_agent = None
_seo_agent = None


def get_research_agent() -> ResearchAgent:
    global _research_agent
    if _research_agent is None:
        _research_agent = ResearchAgent()
    return _research_agent


def get_seo_agent() -> SEOAgent:
    global _seo_agent
    if _seo_agent is None:
        _seo_agent = SEOAgent()
    return _seo_agent


# ─── Request Models ─────────────────────────────────────────────────────────

class MarketReportRequest(BaseModel):
    industry: str = "tổng quan"


class IndustryResearchRequest(BaseModel):
    industry: str
    aspects: list[str] | None = None


class KeywordRequest(BaseModel):
    topic: str
    industry: str = ""
    target_location: str = "Việt Nam"


class SearchMarketRequest(BaseModel):
    query: str
    days: int = 7
    max_results: int = 8


class SummarizeRequest(BaseModel):
    url: str


class MetaTagRequest(BaseModel):
    page_title: str
    page_description: str
    keywords: list[str] | None = None
    page_type: str = "article"


class ContentOutlineRequest(BaseModel):
    keyword: str
    word_count: int = 1500
    content_type: str = "blog"


class AEORequest(BaseModel):
    content: str
    target_question: str


class ContentAuditRequest(BaseModel):
    content: str
    target_keyword: str


class LandingPageRequest(BaseModel):
    product: str
    target_keyword: str
    usp: str = ""


# ─── Research Endpoints ──────────────────────────────────────────────────────

@router.post("/market-report")
async def market_report(request: MarketReportRequest):
    """Tạo báo cáo thị trường hàng ngày (crawl + tóm tắt bằng AI)."""
    try:
        agent = get_research_agent()
        report = agent.daily_market_report(industry=request.industry)
        return {"industry": request.industry, "report": report}
    except Exception as e:
        logger.error(f"Market report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/industry")
async def research_industry(request: IndustryResearchRequest):
    """Nghiên cứu sâu về một ngành cụ thể."""
    if not request.industry.strip():
        raise HTTPException(status_code=400, detail="Industry không được để trống")
    try:
        agent = get_research_agent()
        result = agent.research_industry(
            industry=request.industry,
            aspects=request.aspects,
        )
        return {"industry": request.industry, "analysis": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords")
async def research_keywords(request: KeywordRequest):
    """Nghiên cứu từ khoá SEO cho topic."""
    if not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic không được để trống")
    try:
        agent = get_seo_agent()
        result = agent.research_keywords(
            topic=request.topic,
            industry=request.industry,
            target_location=request.target_location,
        )
        return {"topic": request.topic, "keywords": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_market(request: SearchMarketRequest):
    """Tìm kiếm thông tin thị trường theo từ khoá — DuckDuckGo/Google + AI tóm tắt."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query không được để trống")
    if not 1 <= request.days <= 90:
        raise HTTPException(status_code=400, detail="days phải trong khoảng 1-90")
    if not 1 <= request.max_results <= 20:
        raise HTTPException(status_code=400, detail="max_results phải trong khoảng 1-20")
    try:
        agent = get_research_agent()
        summary = agent.search_market(
            query=request.query,
            days=request.days,
            max_results=request.max_results,
        )
        return {"query": request.query, "days": request.days, "summary": summary}
    except Exception as e:
        logger.error(f"Search market error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize-url")
async def summarize_url(request: SummarizeRequest):
    """Tóm tắt nội dung 1 URL bất kỳ."""
    if not request.url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL không hợp lệ")
    try:
        agent = get_research_agent()
        summary = agent.summarize_url(request.url)
        return {"url": request.url, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── SEO Endpoints ──────────────────────────────────────────────────────────

@router.post("/seo/meta-tags")
async def generate_meta_tags(request: MetaTagRequest):
    """Tạo meta tags SEO đầy đủ (title, description, OG, schema)."""
    try:
        agent = get_seo_agent()
        result = agent.generate_meta_tags(
            page_title=request.page_title,
            page_description=request.page_description,
            keywords=request.keywords,
            page_type=request.page_type,
        )
        return {"meta_tags": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seo/content-outline")
async def generate_content_outline(request: ContentOutlineRequest):
    """Tạo content outline chuẩn SEO."""
    try:
        agent = get_seo_agent()
        result = agent.generate_content_outline(
            keyword=request.keyword,
            word_count=request.word_count,
            content_type=request.content_type,
        )
        return {"keyword": request.keyword, "outline": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seo/aeo-optimize")
async def optimize_for_ai_search(request: AEORequest):
    """Tối ưu content cho AI Search (ChatGPT, Perplexity, Claude)."""
    try:
        agent = get_seo_agent()
        result = agent.optimize_for_ai_search(
            content=request.content,
            target_question=request.target_question,
        )
        return {"optimized_content": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seo/audit")
async def audit_content(request: ContentAuditRequest):
    """Audit SEO cho content."""
    try:
        agent = get_seo_agent()
        result = agent.audit_content(
            content=request.content,
            target_keyword=request.target_keyword,
        )
        return {"keyword": request.target_keyword, "audit": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seo/landing-page")
async def generate_landing_page_seo(request: LandingPageRequest):
    """Tạo full SEO copy cho landing page."""
    try:
        agent = get_seo_agent()
        result = agent.generate_landing_page_seo(
            product=request.product,
            target_keyword=request.target_keyword,
            usp=request.usp,
        )
        return {"product": request.product, "seo_copy": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
