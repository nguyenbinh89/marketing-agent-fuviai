"""
Integration tests cho FastAPI endpoints
Chạy: pytest tests/test_api.py -v
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    """Health endpoint trả về ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_available(client):
    """Swagger docs có thể truy cập."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_chat_empty_message(client):
    """Chat với message rỗng trả về 400."""
    response = client.post("/api/agents/chat", json={
        "session_id": "test",
        "message": "   ",
    })
    assert response.status_code == 400


def test_generate_facebook_empty_product(client):
    """Generate Facebook với product rỗng trả về 400."""
    response = client.post("/api/content/generate/facebook", json={
        "product": "",
    })
    assert response.status_code == 400


@patch("backend.api.routes.content.get_content_agent")
def test_generate_facebook_success(mock_get_agent, client):
    """Generate Facebook caption thành công."""
    mock_agent = MagicMock()
    mock_agent.generate_facebook_caption.return_value = "Caption test tiếng Việt hay"
    mock_get_agent.return_value = mock_agent

    response = client.post("/api/content/generate/facebook", json={
        "product": "Phần mềm quản lý FuviAI",
        "tone": "than_thien",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "facebook"
    assert len(data["content"]) > 0


def test_clear_nonexistent_session(client):
    """Clear session không tồn tại trả về message phù hợp."""
    response = client.delete("/api/agents/sessions/nonexistent_session_xyz")
    assert response.status_code == 200
    assert "not found" in response.json()["message"].lower()
