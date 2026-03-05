"""
Tests cho Content Agent (M1)
Chạy: pytest tests/ -v
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.agents.content_agent import ContentAgent, Platform, Tone


@pytest.fixture
def mock_agent():
    """ContentAgent với Claude API được mock."""
    with patch("backend.agents.base_agent.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Nội dung test từ Claude")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 200
        mock_client.messages.create.return_value = mock_response

        with patch("backend.agents.base_agent.anthropic.AsyncAnthropic"):
            agent = ContentAgent()
            agent._client = mock_client
            yield agent


def test_agent_initializes(mock_agent):
    """ContentAgent khởi tạo thành công."""
    assert mock_agent is not None
    assert mock_agent.max_tokens == 8096


def test_generate_facebook_caption(mock_agent):
    """Tạo Facebook caption trả về string."""
    result = mock_agent.generate_facebook_caption(
        product="Phần mềm FuviAI",
        tone=Tone.FRIENDLY,
    )
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_tiktok_script(mock_agent):
    """Tạo TikTok script với duration hợp lệ."""
    result = mock_agent.generate_tiktok_script(
        product="Phần mềm FuviAI",
        duration=60,
    )
    assert isinstance(result, str)


def test_generate_zalo_message(mock_agent):
    """Tạo Zalo message với tên khách hàng."""
    result = mock_agent.generate_zalo_message(
        product="Phần mềm FuviAI",
        customer_name="Anh Minh",
        offer="Giảm 30% tháng 3",
    )
    assert isinstance(result, str)


def test_generate_email(mock_agent):
    """Tạo email marketing AIDA."""
    result = mock_agent.generate_email(
        product="Phần mềm FuviAI",
        target_segment="chủ shop online",
    )
    assert isinstance(result, str)


def test_conversation_history_maintained(mock_agent):
    """History được giữ qua nhiều turns."""
    mock_agent.chat("Câu hỏi 1")
    mock_agent.chat("Câu hỏi 2")
    assert len(mock_agent.conversation_history) == 4  # 2 user + 2 assistant


def test_clear_history(mock_agent):
    """Clear history hoạt động đúng."""
    mock_agent.chat("Test message")
    mock_agent.clear_history()
    assert len(mock_agent.conversation_history) == 0


def test_generate_campaign_content(mock_agent):
    """Campaign content tạo cho nhiều platform."""
    results = mock_agent.generate_campaign_content(
        product="FuviAI Software",
        campaign_name="Tết 2027",
        platforms=[Platform.FACEBOOK, Platform.ZALO],
    )
    assert "facebook" in results
    assert "zalo" in results
