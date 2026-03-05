"""
Integration tests — Phase 2 Agents (M3, M5, M6)
CampaignAgent, InsightAgent, SocialAgent
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# ─── Shared mock fixture ─────────────────────────────────────────────────────

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client dùng chung cho tất cả agents."""
    with patch("backend.agents.base_agent.anthropic.Anthropic") as mock_cls, \
         patch("backend.agents.base_agent.anthropic.AsyncAnthropic"):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="AI response test từ Claude")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 200
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        yield mock_client


# ═══════════════════════════════════════════════════════════════════════
# CAMPAIGN AGENT (M3)
# ═══════════════════════════════════════════════════════════════════════

class TestCampaignAgent:
    def test_init(self, mock_anthropic):
        from backend.agents.campaign_agent import CampaignAgent
        agent = CampaignAgent()
        assert agent.temperature == 0.2
        assert agent.max_tokens == 8096

    def test_analyze_csv(self, mock_anthropic):
        from backend.agents.campaign_agent import CampaignAgent
        agent = CampaignAgent()
        csv = "ad_name,impressions,clicks,spend\nAd A,10000,200,5000000"
        result = agent.analyze_csv(csv, platform="facebook")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_optimize_budget_returns_string(self, mock_anthropic):
        from backend.agents.campaign_agent import CampaignAgent
        agent = CampaignAgent()
        result = agent.optimize_budget(
            {"facebook": 10_000_000, "tiktok": 5_000_000},
            goal="tối đa ROAS",
            season="11_11",
        )
        assert isinstance(result, str)

    def test_design_ab_test(self, mock_anthropic):
        from backend.agents.campaign_agent import CampaignAgent
        agent = CampaignAgent()
        result = agent.design_ab_test("Tăng CTR", "Ảnh sản phẩm", budget=5_000_000)
        assert isinstance(result, str)

    def test_weekly_report_with_comparison(self, mock_anthropic):
        from backend.agents.campaign_agent import CampaignAgent
        agent = CampaignAgent()
        current = {"spend": 10_000_000, "roas": 3.5}
        previous = {"spend": 8_000_000, "roas": 3.0}
        result = agent.weekly_report(current, previous)
        assert isinstance(result, str)

    def test_vn_benchmarks_exist(self):
        from backend.agents.campaign_agent import VN_BENCHMARKS
        assert "facebook" in VN_BENCHMARKS
        assert "tiktok" in VN_BENCHMARKS
        assert "roas" in VN_BENCHMARKS["facebook"]

    def test_dict_to_csv(self):
        from backend.agents.campaign_agent import CampaignAgent
        data = [{"name": "Ad A", "spend": 1000}, {"name": "Ad B", "spend": 2000}]
        csv = CampaignAgent._dict_to_csv(data)
        assert "name" in csv
        assert "Ad A" in csv

    def test_dict_to_csv_empty(self):
        from backend.agents.campaign_agent import CampaignAgent
        assert CampaignAgent._dict_to_csv([]) == ""


# ═══════════════════════════════════════════════════════════════════════
# INSIGHT AGENT (M6)
# ═══════════════════════════════════════════════════════════════════════

class TestInsightAgent:
    def test_rule_based_sentiment_positive(self):
        from backend.agents.insight_agent import _rule_based_sentiment
        assert _rule_based_sentiment("Sản phẩm quá tốt, tuyệt vời") == "positive"

    def test_rule_based_sentiment_negative(self):
        from backend.agents.insight_agent import _rule_based_sentiment
        assert _rule_based_sentiment("Hàng tệ quá, thất vọng") == "negative"

    def test_rule_based_sentiment_neutral(self):
        from backend.agents.insight_agent import _rule_based_sentiment
        assert _rule_based_sentiment("Tôi đã mua sản phẩm này") == "neutral"

    def test_analyze_sentiment_returns_dict(self, mock_anthropic):
        from backend.agents.insight_agent import InsightAgent
        agent = InsightAgent()
        result = agent.analyze_sentiment(["Sản phẩm tốt!", "Giao hàng chậm"])
        assert "summary" in result
        assert "details" in result
        assert "top_positive" in result
        assert "top_negative" in result
        assert result["summary"]["total"] == 2

    def test_analyze_single(self, mock_anthropic):
        from backend.agents.insight_agent import InsightAgent
        agent = InsightAgent()
        result = agent.analyze_single("Xịn sò lắm!")
        assert "text" in result
        assert "sentiment" in result
        assert result["sentiment"] in ["positive", "negative", "neutral"]

    def test_detect_crisis_low_negative(self, mock_anthropic):
        from backend.agents.insight_agent import InsightAgent
        agent = InsightAgent()
        texts = ["Tốt", "Hay", "OK", "Được", "Tệ"]
        result = agent.detect_crisis(texts, threshold=0.5)
        assert result["negative_ratio"] == 0.2
        assert not result["is_crisis"]

    def test_detect_crisis_high_negative(self, mock_anthropic):
        from backend.agents.insight_agent import InsightAgent
        agent = InsightAgent()
        texts = ["tệ", "thất vọng", "kém", "lừa đảo", "bóc phốt"]
        result = agent.detect_crisis(texts, threshold=0.3)
        assert result["is_crisis"] is True
        assert result["severity"] in ["high", "medium"]

    def test_detect_crisis_keyword_trigger(self, mock_anthropic):
        from backend.agents.insight_agent import InsightAgent
        agent = InsightAgent()
        texts = ["Sản phẩm ok", "scam hoàn toàn"]
        result = agent.detect_crisis(texts)
        assert result["is_crisis"] is True
        assert result["has_crisis_keywords"] is True

    def test_detect_crisis_empty(self, mock_anthropic):
        from backend.agents.insight_agent import InsightAgent
        agent = InsightAgent()
        result = agent.detect_crisis([])
        assert not result["is_crisis"]


# ═══════════════════════════════════════════════════════════════════════
# SOCIAL AGENT (M5)
# ═══════════════════════════════════════════════════════════════════════

class TestSocialAgent:
    @pytest.fixture
    def mock_social_agent(self, mock_anthropic):
        with patch("backend.agents.social_agent.ZaloOATool") as mock_zalo, \
             patch("backend.agents.social_agent.FacebookTool") as mock_fb, \
             patch("backend.agents.social_agent.ContentAgent"):
            agent_module = __import__("backend.agents.social_agent", fromlist=["SocialAgent"])
            agent = agent_module.SocialAgent()
            agent._zalo = mock_zalo()
            agent._facebook = mock_fb()
            yield agent

    def test_schedule_post(self, mock_social_agent):
        from backend.agents.content_agent import Platform
        post = mock_social_agent.schedule_post(
            "Content test", Platform.FACEBOOK,
            datetime(2027, 3, 10, 19, 0, 0),
        )
        assert post.status == "pending"
        assert post.platform == "facebook"

    def test_get_schedule_empty(self, mock_social_agent):
        result = mock_social_agent.get_schedule()
        assert isinstance(result, list)

    def test_get_schedule_filter(self, mock_social_agent):
        from backend.agents.content_agent import Platform
        mock_social_agent.schedule_post("Post 1", Platform.FACEBOOK, datetime(2027, 3, 10, 19, 0))
        pending = mock_social_agent.get_schedule(status="pending")
        assert all(p["status"] == "pending" for p in pending)

    def test_post_schedule_to_dict(self):
        from backend.agents.social_agent import PostSchedule
        post = PostSchedule("facebook", "Test content", datetime.now())
        d = post.to_dict()
        assert d["platform"] == "facebook"
        assert d["status"] == "pending"
        assert "scheduled_time" in d

    def test_post_now_facebook(self, mock_social_agent):
        from backend.agents.content_agent import Platform
        mock_social_agent._facebook.post_to_page.return_value = {"id": "12345"}
        result = mock_social_agent.post_now("Content test", Platform.FACEBOOK)
        assert result["status"] == "published"
        assert result["platform"] == "facebook"

    def test_post_now_unsupported_platform(self, mock_social_agent):
        from backend.agents.content_agent import Platform
        result = mock_social_agent.post_now("Content", Platform.TIKTOK)
        assert "chưa tích hợp" in result["data"]["message"]
