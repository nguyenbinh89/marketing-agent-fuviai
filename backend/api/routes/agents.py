"""
FuviAI Marketing Agent — /api/agents/* routes
Chat với agents, streaming, history management
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.config.prompts_vn import FUVIAI_SYSTEM_PROMPT

router = APIRouter()

# Simple in-memory session store (Phase 2 sẽ dùng Redis)
_sessions: dict[str, BaseAgent] = {}


def _get_or_create_agent(session_id: str) -> BaseAgent:
    if session_id not in _sessions:
        _sessions[session_id] = BaseAgent()
        logger.info(f"New session created: {session_id}")
    return _sessions[session_id]


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str
    reset_history: bool = False


class ChatResponse(BaseModel):
    session_id: str
    response: str
    history_length: int


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat với FuviAI Marketing Agent."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message không được để trống")

    agent = _get_or_create_agent(request.session_id)
    try:
        response = await agent.achat(
            request.message,
            reset_history=request.reset_history
        )
        return ChatResponse(
            session_id=request.session_id,
            response=response,
            history_length=len(agent.conversation_history),
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat — trả về response từng chunk."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message không được để trống")

    agent = _get_or_create_agent(request.session_id)

    async def generate():
        async for chunk in agent.astream(request.message):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain")


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Xoá conversation history của session."""
    if session_id in _sessions:
        _sessions[session_id].clear_history()
        return {"message": f"Session {session_id} cleared"}
    return {"message": "Session not found"}


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str):
    """Lấy conversation history của session."""
    if session_id not in _sessions:
        return {"session_id": session_id, "history": []}
    agent = _sessions[session_id]
    return {
        "session_id": session_id,
        "history": agent.get_history(),
        "history_length": len(agent.conversation_history),
    }
