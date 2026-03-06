"""
FuviAI Marketing Agent — /api/content/* routes
Generate marketing content cho các platform
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from backend.agents.content_agent import ContentAgent, Platform, Tone

router = APIRouter()

# Shared content agent instance
_content_agent = None


def get_content_agent() -> ContentAgent:
    global _content_agent
    if _content_agent is None:
        _content_agent = ContentAgent()
    return _content_agent


# ─── Request / Response Models ──────────────────────────────────────────────

class GenerateRequest(BaseModel):
    product: str
    tone: Tone = Tone.FRIENDLY
    target_audience: str = "chủ doanh nghiệp SME Việt Nam"
    key_benefit: str = ""
    cta: str = "Nhắn tin tư vấn ngay"


class InstagramRequest(BaseModel):
    product: str
    content_type: str = "photo"   # photo | reel | carousel | story
    tone: Tone = Tone.FRIENDLY
    target_audience: str = "chủ doanh nghiệp SME Việt Nam"
    key_benefit: str = ""
    hashtags_count: int = 20


class TikTokRequest(BaseModel):
    product: str
    duration: int = 60
    hook_style: str = "câu hỏi gây tò mò"


class ZaloRequest(BaseModel):
    product: str
    customer_name: str = ""
    offer: str = ""
    urgency: str = ""


class EmailRequest(BaseModel):
    product: str
    target_segment: str = "khách hàng tiềm năng"
    subject_style: str = "tạo tò mò"


class CampaignRequest(BaseModel):
    product: str
    campaign_name: str
    platforms: list[Platform] = [Platform.FACEBOOK, Platform.ZALO]


class ContentResponse(BaseModel):
    platform: str
    content: str


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/generate/facebook", response_model=ContentResponse)
async def generate_facebook(request: GenerateRequest):
    """Tạo Facebook caption (300-500 chữ)."""
    if not request.product.strip():
        raise HTTPException(status_code=400, detail="Product không được để trống")
    try:
        agent = get_content_agent()
        content = agent.generate_facebook_caption(
            product=request.product,
            tone=request.tone,
            target_audience=request.target_audience,
            key_benefit=request.key_benefit,
            cta=request.cta,
        )
        return ContentResponse(platform="facebook", content=content)
    except Exception as e:
        logger.error(f"Facebook caption error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/instagram", response_model=ContentResponse)
async def generate_instagram(request: InstagramRequest):
    """Tạo Instagram caption tối ưu cho photo/reel/carousel/story."""
    if not request.product.strip():
        raise HTTPException(status_code=400, detail="Product không được để trống")
    valid_types = ("photo", "reel", "carousel", "story")
    if request.content_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"content_type phải là: {', '.join(valid_types)}")
    if not 1 <= request.hashtags_count <= 30:
        raise HTTPException(status_code=400, detail="hashtags_count phải từ 1 đến 30")
    try:
        agent = get_content_agent()
        content = agent.generate_instagram_caption(
            product=request.product,
            content_type=request.content_type,
            tone=request.tone,
            target_audience=request.target_audience,
            key_benefit=request.key_benefit,
            hashtags_count=request.hashtags_count,
        )
        return ContentResponse(platform="instagram", content=content)
    except Exception as e:
        logger.error(f"Instagram caption error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/tiktok", response_model=ContentResponse)
async def generate_tiktok(request: TikTokRequest):
    """Tạo TikTok script (60-90 giây)."""
    if not request.product.strip():
        raise HTTPException(status_code=400, detail="Product không được để trống")
    if request.duration not in (60, 90):
        raise HTTPException(status_code=400, detail="Duration phải là 60 hoặc 90 giây")
    try:
        agent = get_content_agent()
        content = agent.generate_tiktok_script(
            product=request.product,
            duration=request.duration,
            hook_style=request.hook_style,
        )
        return ContentResponse(platform="tiktok", content=content)
    except Exception as e:
        logger.error(f"TikTok script error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/zalo", response_model=ContentResponse)
async def generate_zalo(request: ZaloRequest):
    """Tạo Zalo OA broadcast message."""
    if not request.product.strip():
        raise HTTPException(status_code=400, detail="Product không được để trống")
    try:
        agent = get_content_agent()
        content = agent.generate_zalo_message(
            product=request.product,
            customer_name=request.customer_name,
            offer=request.offer,
            urgency=request.urgency,
        )
        return ContentResponse(platform="zalo", content=content)
    except Exception as e:
        logger.error(f"Zalo message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/email", response_model=ContentResponse)
async def generate_email(request: EmailRequest):
    """Tạo email marketing theo cấu trúc AIDA."""
    if not request.product.strip():
        raise HTTPException(status_code=400, detail="Product không được để trống")
    try:
        agent = get_content_agent()
        content = agent.generate_email(
            product=request.product,
            target_segment=request.target_segment,
            subject_style=request.subject_style,
        )
        return ContentResponse(platform="email", content=content)
    except Exception as e:
        logger.error(f"Email error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/campaign")
async def generate_campaign(request: CampaignRequest):
    """Tạo content cho nhiều platform cùng lúc."""
    if not request.product.strip():
        raise HTTPException(status_code=400, detail="Product không được để trống")
    try:
        agent = get_content_agent()
        results = agent.generate_campaign_content(
            product=request.product,
            campaign_name=request.campaign_name,
            platforms=request.platforms,
        )
        return {
            "campaign_name": request.campaign_name,
            "product": request.product,
            "content": results,
        }
    except Exception as e:
        logger.error(f"Campaign content error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
