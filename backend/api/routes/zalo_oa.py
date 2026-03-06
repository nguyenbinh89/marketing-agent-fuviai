"""
FuviAI Marketing Agent — /api/zalo/* routes
Zalo Official Account API: OA info, followers, messaging, broadcast, tags
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from backend.tools.zalo_tool import ZaloOATool

router = APIRouter()

_zalo: ZaloOATool | None = None


def get_zalo() -> ZaloOATool:
    global _zalo
    if _zalo is None:
        _zalo = ZaloOATool()
    return _zalo


# ─── Request Models ───────────────────────────────────────────────────────────

class TextMessageRequest(BaseModel):
    user_id: str
    message: str = Field(..., min_length=1, max_length=2000)


class ButtonMessageRequest(BaseModel):
    user_id: str
    text: str = Field(..., min_length=1, max_length=500)
    buttons: list[dict] = Field(..., min_length=1, max_length=5)


class BroadcastRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    tag_name: str | None = Field(default=None, description="Gửi theo tag (None = gửi tất cả)")


# ─── OA Info ──────────────────────────────────────────────────────────────────

@router.get("/info")
async def get_oa_info():
    """Thông tin OA: tên, follower count, avatar, description."""
    try:
        return get_zalo().get_oa_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Followers ────────────────────────────────────────────────────────────────

@router.get("/followers")
async def get_followers(
    offset: int = Query(default=0, ge=0),
    count: int = Query(default=50, ge=1, le=50),
):
    """Danh sách followers (phân trang, tối đa 50/lần)."""
    try:
        result = get_zalo().get_followers(offset=offset, count=count)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/followers/{user_id}")
async def get_follower_profile(user_id: str):
    """Thông tin chi tiết 1 follower."""
    try:
        return get_zalo().get_follower_info(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Messaging ────────────────────────────────────────────────────────────────

@router.post("/message/text")
async def send_text_message(request: TextMessageRequest):
    """Gửi text message cho 1 user."""
    try:
        result = get_zalo().send_text_message(
            user_id=request.user_id,
            message=request.message,
        )
        if result.get("error") and result["error"] != 0:
            raise HTTPException(status_code=400, detail=str(result))
        return {"sent": True, "user_id": request.user_id, **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message/button")
async def send_button_message(request: ButtonMessageRequest):
    """Gửi tin nhắn có nút bấm."""
    try:
        result = get_zalo().send_button_message(
            user_id=request.user_id,
            text=request.text,
            buttons=request.buttons,
        )
        return {"sent": True, "user_id": request.user_id, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Broadcast ────────────────────────────────────────────────────────────────

@router.post("/broadcast")
async def broadcast(request: BroadcastRequest):
    """
    Broadcast tin nhắn đến toàn bộ followers hoặc theo tag.
    tag_name=None → gửi tất cả.
    """
    try:
        if request.tag_name:
            result = get_zalo().send_broadcast_by_tag(
                tag_name=request.tag_name,
                message=request.message,
            )
        else:
            result = get_zalo().broadcast(message=request.message)
        return {
            "sent": True,
            "target": request.tag_name or "all",
            "chars": len(request.message),
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Tags ─────────────────────────────────────────────────────────────────────

@router.get("/tags")
async def get_tags():
    """Danh sách tags và số follower trong mỗi tag."""
    try:
        tags = get_zalo().get_tags()
        return {"count": len(tags), "tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Recent Chats ─────────────────────────────────────────────────────────────

@router.get("/chats")
async def get_recent_chats(
    count: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    """Danh sách hội thoại gần đây."""
    try:
        chats = get_zalo().get_recent_chats(count=count, offset=offset)
        return {"count": len(chats), "chats": chats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
