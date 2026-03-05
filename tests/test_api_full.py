"""
Full API integration tests — tất cả routes Phase 1-4
Chạy: pytest tests/test_api_full.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def mock_claude():
    """Auto-mock Claude API cho tất cả tests."""
    with patch("backend.agents.base_agent.anthropic.Anthropic") as mock_cls, \
         patch("backend.agents.base_agent.anthropic.AsyncAnthropic"):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Mock AI response cho test")]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 100
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        yield


# ═══════════════════════════════════════════════════════════════════════
# HEALTH & DOCS
# ═══════════════════════════════════════════════════════════════════════

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "fuviai-marketing-agent"


def test_swagger_docs(client):
    r = client.get("/docs")
    assert r.status_code == 200


def test_openapi_schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert "paths" in schema
    # Kiểm tra tất cả routers đã mount
    paths = schema["paths"]
    assert any("/api/agents" in p for p in paths)
    assert any("/api/content" in p for p in paths)
    assert any("/api/research" in p for p in paths)
    assert any("/api/analytics" in p for p in paths)
    assert any("/api/automation" in p for p in paths)
    assert any("/api/commerce" in p for p in paths)


# ═══════════════════════════════════════════════════════════════════════
# CONTENT ROUTES
# ═══════════════════════════════════════════════════════════════════════

class TestContentRoutes:
    def test_facebook_missing_product(self, client):
        r = client.post("/api/content/generate/facebook", json={"product": ""})
        assert r.status_code == 400

    def test_tiktok_missing_product(self, client):
        r = client.post("/api/content/generate/tiktok", json={"product": ""})
        assert r.status_code == 400

    @patch("backend.api.routes.content.get_content_agent")
    def test_facebook_success(self, mock_get, client):
        mock_agent = MagicMock()
        mock_agent.generate_facebook_caption.return_value = "Caption test"
        mock_get.return_value = mock_agent
        r = client.post("/api/content/generate/facebook", json={
            "product": "FuviAI", "tone": "than_thien"
        })
        assert r.status_code == 200
        assert r.json()["platform"] == "facebook"

    @patch("backend.api.routes.content.get_content_agent")
    def test_zalo_success(self, mock_get, client):
        mock_agent = MagicMock()
        mock_agent.generate_zalo_message.return_value = "Zalo message test"
        mock_get.return_value = mock_agent
        r = client.post("/api/content/generate/zalo", json={
            "product": "FuviAI", "offer": "Giảm 30%"
        })
        assert r.status_code == 200

    @patch("backend.api.routes.content.get_content_agent")
    def test_campaign_multi_platform(self, mock_get, client):
        mock_agent = MagicMock()
        mock_agent.campaign_content.return_value = {"facebook": "...", "zalo": "..."}
        mock_get.return_value = mock_agent
        r = client.post("/api/content/generate/campaign", json={
            "product": "FuviAI",
            "campaign_name": "Tết 2027",
            "platforms": ["facebook", "zalo"],
        })
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# AUTOMATION ROUTES
# ═══════════════════════════════════════════════════════════════════════

class TestAutomationRoutes:
    def test_sentiment_empty(self, client):
        r = client.post("/api/automation/insight/sentiment", json={"texts": []})
        assert r.status_code == 400

    def test_sentiment_too_many(self, client):
        r = client.post("/api/automation/insight/sentiment", json={
            "texts": ["text"] * 501
        })
        assert r.status_code == 400

    @patch("backend.api.routes.automation.get_insight_agent")
    def test_sentiment_success(self, mock_get, client):
        mock_agent = MagicMock()
        mock_agent.analyze_sentiment.return_value = {
            "summary": {"positive": 1, "negative": 0, "neutral": 0, "total": 1},
            "details": [{"text": "Tốt", "sentiment": "positive"}],
            "top_positive": ["Tốt"],
            "top_negative": [],
            "ai_insight": "test insight",
        }
        mock_get.return_value = mock_agent
        r = client.post("/api/automation/insight/sentiment", json={"texts": ["Sản phẩm tốt!"]})
        assert r.status_code == 200
        assert "summary" in r.json()

    def test_campaign_analyze_empty_csv(self, client):
        r = client.post("/api/automation/campaign/analyze", json={
            "csv_content": "   ", "platform": "facebook"
        })
        assert r.status_code == 400

    @patch("backend.api.routes.automation.get_campaign_agent")
    def test_campaign_analyze_success(self, mock_get, client):
        mock_agent = MagicMock()
        mock_agent.analyze_csv.return_value = "5 đề xuất cải thiện"
        mock_get.return_value = mock_agent
        r = client.post("/api/automation/campaign/analyze", json={
            "csv_content": "ad_name,spend\nAd A,1000000",
            "platform": "facebook",
        })
        assert r.status_code == 200

    @patch("backend.api.routes.automation.get_social_agent")
    def test_social_schedule(self, mock_get, client):
        from backend.agents.social_agent import PostSchedule
        from datetime import datetime
        mock_agent = MagicMock()
        mock_post = PostSchedule("facebook", "Test", datetime(2027, 3, 15, 19, 0))
        mock_agent.schedule_post.return_value = mock_post
        mock_get.return_value = mock_agent
        r = client.post("/api/automation/social/schedule", json={
            "content": "Nội dung test",
            "platform": "facebook",
            "scheduled_time": "2027-03-15T19:00:00",
        })
        assert r.status_code == 200

    def test_social_schedule_invalid_time(self, client):
        r = client.post("/api/automation/social/schedule", json={
            "content": "Test",
            "platform": "facebook",
            "scheduled_time": "not-a-date",
        })
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════════
# ANALYTICS ROUTES (Phase 3)
# ═══════════════════════════════════════════════════════════════════════

class TestAnalyticsRoutes:
    @patch("backend.api.routes.analytics.get_competitor_agent")
    def test_get_competitors_dashboard(self, mock_get, client):
        mock_agent = MagicMock()
        mock_agent.get_dashboard_data.return_value = {"total_competitors": 0, "competitors": []}
        mock_get.return_value = mock_agent
        r = client.get("/api/analytics/competitors")
        assert r.status_code == 200

    def test_add_competitor_missing_fields(self, client):
        r = client.post("/api/analytics/competitors/add", json={"name": "", "website": ""})
        assert r.status_code == 400

    def test_listing_trends_history(self, client):
        with patch("backend.api.routes.analytics.get_listening_agent") as mock_get:
            mock_agent = MagicMock()
            mock_agent.get_trend_history.return_value = []
            mock_get.return_value = mock_agent
            r = client.get("/api/analytics/listening/trend-history")
            assert r.status_code == 200

    def test_listening_scan_invalid_industry(self, client):
        r = client.post("/api/analytics/listening/scan", json={
            "industry": "invalid_industry_xyz"
        })
        assert r.status_code == 400

    def test_keywords_monitor_empty(self, client):
        r = client.post("/api/analytics/listening/keywords", json={"keywords": []})
        assert r.status_code == 400

    def test_keywords_monitor_too_many(self, client):
        r = client.post("/api/analytics/listening/keywords", json={
            "keywords": [f"kw{i}" for i in range(21)]
        })
        assert r.status_code == 400

    def test_crisis_check_empty(self, client):
        r = client.post("/api/analytics/listening/crisis-check", json={"texts": []})
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════════
# COMMERCE ROUTES (Phase 4)
# ═══════════════════════════════════════════════════════════════════════

class TestCommerceRoutes:
    # Livestream
    def test_start_session_empty_product(self, client):
        r = client.post("/api/commerce/livestream/start", json={"product": ""})
        assert r.status_code == 400

    @patch("backend.api.routes.commerce.get_livestream_agent")
    def test_start_session_success(self, mock_get, client):
        from backend.agents.livestream_agent import LivestreamSession
        mock_agent = MagicMock()
        session = LivestreamSession("FuviAI", "tiktok")
        mock_agent.start_session.return_value = session
        mock_get.return_value = mock_agent
        r = client.post("/api/commerce/livestream/start", json={
            "product": "FuviAI", "platform": "tiktok"
        })
        assert r.status_code == 200

    def test_script_session_not_found(self, client):
        with patch("backend.api.routes.commerce.get_livestream_agent") as mock_get:
            mock_agent = MagicMock()
            mock_agent.get_session.return_value = None
            mock_get.return_value = mock_agent
            r = client.post("/api/commerce/livestream/script", json={
                "session_id": "nonexistent", "current_viewers": 100
            })
            assert r.status_code == 404

    # Budget
    def test_quarterly_forecast_invalid_quarter(self, client):
        r = client.post("/api/commerce/budget/forecast/quarterly", json={
            "budget": 100_000_000, "industry": "saas", "quarter": 5
        })
        assert r.status_code == 400

    @patch("backend.api.routes.commerce.get_adbudget_agent")
    def test_season_calendar(self, mock_get, client):
        from backend.agents.adbudget_agent import SEASON_CALENDAR
        mock_agent = MagicMock()
        mock_agent.get_season_calendar.return_value = SEASON_CALENDAR
        mock_get.return_value = mock_agent
        r = client.get("/api/commerce/budget/season-calendar")
        assert r.status_code == 200
        data = r.json()
        assert "tet" in data["calendar"]

    def test_season_boost_invalid(self, client):
        with patch("backend.api.routes.commerce.get_adbudget_agent") as mock_get:
            mock_agent = MagicMock()
            mock_agent.season_budget_boost.return_value = {"error": "Season không hợp lệ"}
            mock_get.return_value = mock_agent
            r = client.post("/api/commerce/budget/season-boost", json={
                "base_budget": 10_000_000, "season_key": "invalid", "industry": "saas"
            })
            assert r.status_code == 400

    # Personalize
    def test_segment_empty_customers(self, client):
        r = client.post("/api/commerce/personalize/segment", json={"customers": []})
        assert r.status_code == 400

    def test_segment_too_many_customers(self, client):
        r = client.post("/api/commerce/personalize/segment", json={
            "customers": [{"id": str(i)} for i in range(1001)]
        })
        assert r.status_code == 400

    # Compliance
    def test_compliance_check_empty(self, client):
        r = client.post("/api/commerce/compliance/check", json={"content": ""})
        assert r.status_code == 400

    @patch("backend.api.routes.commerce.get_compliance_agent")
    def test_compliance_check_success(self, mock_get, client):
        mock_agent = MagicMock()
        mock_agent.check_content.return_value = {
            "verdict": "PASS", "risk_score": 5, "safe_to_publish": True,
            "quick_check_issues": [], "content_length": 50, "platform": "facebook",
        }
        mock_get.return_value = mock_agent
        r = client.post("/api/commerce/compliance/check", json={
            "content": "FuviAI giúp tối ưu marketing doanh nghiệp.",
            "platform": "facebook",
        })
        assert r.status_code == 200
        assert r.json()["verdict"] == "PASS"

    def test_batch_compliance_too_many(self, client):
        r = client.post("/api/commerce/compliance/batch-check", json={
            "contents": ["content"] * 21
        })
        assert r.status_code == 400

    @patch("backend.api.routes.commerce.get_compliance_agent")
    def test_platform_policy(self, mock_get, client):
        mock_agent = MagicMock()
        mock_agent.get_platform_policies.return_value = "Facebook Ads Policy..."
        mock_get.return_value = mock_agent
        r = client.get("/api/commerce/compliance/policies/facebook")
        assert r.status_code == 200

    # Orchestrator
    def test_orchestrate_missing_fields(self, client):
        r = client.post("/api/commerce/orchestrate/campaign-plan", json={
            "task": "", "product": ""
        })
        assert r.status_code == 400
