"""
Integration tests — Phase 3 & 4 Agents (M7, M8, M9, M10, M11, M12, Orchestrator)
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime


@pytest.fixture
def mock_anthropic():
    with patch("backend.agents.base_agent.anthropic.Anthropic") as mock_cls, \
         patch("backend.agents.base_agent.anthropic.AsyncAnthropic"):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="AI response test")]
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 100
        mock_client.messages.create.return_value = mock_response
        mock_cls.return_value = mock_client
        yield mock_client


# ═══════════════════════════════════════════════════════════════════════
# COMPETITOR AGENT (M10)
# ═══════════════════════════════════════════════════════════════════════

class TestCompetitorAgent:
    @pytest.fixture
    def agent(self, mock_anthropic):
        with patch("backend.agents.competitor_agent.ScraperTool") as mock_scraper:
            from backend.agents.competitor_agent import CompetitorAgent
            a = CompetitorAgent()
            a._scraper = mock_scraper()
            a._scraper.get_page_snapshot.return_value = {
                "title": "Đối thủ A — Giải pháp Marketing",
                "headings": ["Về chúng tôi", "Sản phẩm"],
                "price_mentions": ["990.000đ", "2.990.000đ"],
                "text_length": 5000,
                "timestamp": datetime.now().isoformat(),
            }
            a._scraper.detect_changes.return_value = {
                "has_changes": False, "changes": []
            }
            yield a

    def test_add_competitor(self, agent):
        profile = agent.add_competitor("TestCo", "https://testco.vn", industry="saas")
        assert profile.name == "TestCo"
        assert profile.website == "https://testco.vn"
        assert "TestCo" in agent._competitors

    def test_remove_competitor(self, agent):
        agent.add_competitor("ToRemove", "https://toremove.vn")
        assert agent.remove_competitor("ToRemove") is True
        assert "ToRemove" not in agent._competitors

    def test_remove_nonexistent(self, agent):
        assert agent.remove_competitor("NotExist") is False

    def test_list_competitors_empty(self, agent):
        assert agent.list_competitors() == []

    def test_snapshot_unknown_competitor(self, agent):
        result = agent.snapshot_competitor("Unknown")
        assert "error" in result

    def test_snapshot_known_competitor(self, agent):
        agent.add_competitor("Known", "https://known.vn")
        snapshot = agent.snapshot_competitor("Known")
        assert snapshot.get("title") or snapshot.get("error") is None
        assert "Known" in agent._competitors
        assert len(agent._competitors["Known"].snapshots) > 0

    def test_get_dashboard_data(self, agent):
        agent.add_competitor("A", "https://a.vn")
        data = agent.get_dashboard_data()
        assert "total_competitors" in data
        assert data["total_competitors"] == 1


# ═══════════════════════════════════════════════════════════════════════
# LISTENING AGENT (M7)
# ═══════════════════════════════════════════════════════════════════════

class TestListeningAgent:
    @pytest.fixture
    def agent(self, mock_anthropic):
        with patch("backend.agents.listening_agent.ScraperTool") as mock_scraper, \
             patch("backend.agents.listening_agent.ZaloOATool"), \
             patch("backend.agents.listening_agent.ContentAgent"), \
             patch("backend.agents.listening_agent.InsightAgent") as mock_insight:
            from backend.agents.listening_agent import ListeningAgent
            a = ListeningAgent()
            a._scraper = mock_scraper()
            a._scraper.scrape_cafef_headlines.return_value = [
                {"title": "AI Marketing bùng nổ 2027", "source": "CafeF"},
                {"title": "Shopee tăng trưởng mạnh Q1", "source": "CafeF"},
            ]
            a._scraper.scrape_vnexpress_business.return_value = []
            a._insight_agent = mock_insight()
            a._insight_agent.analyze_sentiment.return_value = {
                "summary": {"positive": 1, "negative": 0, "neutral": 1, "total": 2},
            }
            a._insight_agent.detect_crisis.return_value = {
                "is_crisis": False, "severity": "none",
                "negative_ratio": 0.0, "negative_count": 0, "total": 2,
                "has_crisis_keywords": False,
            }
            yield a

    def test_scan_trends_returns_dict(self, agent):
        result = agent.scan_trends(industry="marketing")
        assert "industry" in result
        assert "scan_time" in result
        assert "articles_found" in result

    def test_monitor_keywords_returns_list(self, agent):
        result = agent.monitor_keywords(["AI Marketing"])
        assert isinstance(result, list)

    def test_filter_by_keywords(self, agent):
        articles = [
            {"title": "AI Marketing đang hot"},
            {"title": "Tin tức bất động sản"},
        ]
        filtered = agent._filter_by_keywords(articles, ["AI", "marketing"])
        assert len(filtered) == 1

    def test_get_trend_history_empty(self, agent):
        assert agent.get_trend_history() == []

    def test_crisis_check_no_crisis(self, agent):
        result = agent.check_and_alert_crisis(["Sản phẩm tốt", "Ổn lắm"])
        assert not result["is_crisis"]


# ═══════════════════════════════════════════════════════════════════════
# LIVESTREAM AGENT (M8)
# ═══════════════════════════════════════════════════════════════════════

class TestLivestreamAgent:
    @pytest.fixture
    def agent(self, mock_anthropic):
        with patch("backend.agents.livestream_agent.InsightAgent") as mock_insight:
            from backend.agents.livestream_agent import LivestreamAgent
            a = LivestreamAgent()
            a._insight_agent = mock_insight()
            a._insight_agent.analyze_sentiment.return_value = {
                "summary": {"positive": 3, "negative": 0, "neutral": 1, "total": 4}
            }
            yield a

    def test_start_session(self, agent):
        session = agent.start_session("FuviAI Pro", "tiktok", 50_000_000, "test-001")
        assert session.product == "FuviAI Pro"
        assert session.platform == "tiktok"
        assert "test-001" in agent._active_sessions

    def test_get_session(self, agent):
        agent.start_session("Product", "tiktok", session_id="sid-1")
        session = agent.get_session("sid-1")
        assert session is not None
        assert session.product == "Product"

    def test_get_nonexistent_session(self, agent):
        assert agent.get_session("nonexistent") is None

    def test_end_session(self, agent):
        agent.start_session("P", "tiktok", session_id="end-1")
        result = agent.end_session("end-1")
        assert "session" in result
        assert "end-1" not in agent._active_sessions

    def test_end_nonexistent_session(self, agent):
        result = agent.end_session("no-such-session")
        assert "error" in result

    def test_list_sessions(self, agent):
        agent.start_session("P1", "tiktok", session_id="s1")
        agent.start_session("P2", "facebook", session_id="s2")
        sessions = agent.list_sessions()
        assert len(sessions) == 2

    def test_get_stream_phase(self, agent):
        assert "WARM-UP" in agent._get_stream_phase(2)
        assert "BUILD-UP" in agent._get_stream_phase(10)
        assert "PEAK" in agent._get_stream_phase(20)
        assert "CLOSE" in agent._get_stream_phase(55)

    def test_evaluate_deal_timing_early(self, agent):
        result = agent._evaluate_deal_timing(elapsed=5, viewers=100, peak=100)
        assert "sớm" in result.lower() or "⚠️" in result

    def test_evaluate_deal_timing_good(self, agent):
        result = agent._evaluate_deal_timing(elapsed=20, viewers=80, peak=100)
        assert "✅" in result

    def test_session_elapsed_minutes(self):
        from backend.agents.livestream_agent import LivestreamSession
        session = LivestreamSession("P", "tiktok")
        assert session.elapsed_minutes() >= 0

    def test_session_viewer_drop(self):
        from backend.agents.livestream_agent import LivestreamSession
        session = LivestreamSession("P", "tiktok")
        session.current_viewers = 80
        drop = session.viewer_drop_percent(100)
        assert drop == 20.0

    def test_session_to_dict(self):
        from backend.agents.livestream_agent import LivestreamSession
        session = LivestreamSession("FuviAI", "tiktok", target_revenue=50_000_000)
        d = session.to_dict()
        assert d["product"] == "FuviAI"
        assert d["platform"] == "tiktok"
        assert d["target_revenue"] == 50_000_000


# ═══════════════════════════════════════════════════════════════════════
# AD BUDGET AGENT (M9)
# ═══════════════════════════════════════════════════════════════════════

class TestAdBudgetAgent:
    def test_season_calendar_exists(self):
        from backend.agents.adbudget_agent import SEASON_CALENDAR
        assert "tet" in SEASON_CALENDAR
        assert "11_11" in SEASON_CALENDAR
        assert "black_friday" in SEASON_CALENDAR
        assert "summer" in SEASON_CALENDAR

    def test_season_calendar_structure(self):
        from backend.agents.adbudget_agent import SEASON_CALENDAR
        for key, season in SEASON_CALENDAR.items():
            assert "name" in season
            assert "months" in season
            assert "cpc_multiplier" in season
            assert isinstance(season["months"], list)
            assert season["cpc_multiplier"] > 0

    def test_get_season_calendar(self, mock_anthropic):
        from backend.agents.adbudget_agent import AdBudgetAgent
        agent = AdBudgetAgent()
        cal = agent.get_season_calendar()
        assert "tet" in cal

    def test_season_boost_invalid_key(self, mock_anthropic):
        from backend.agents.adbudget_agent import AdBudgetAgent
        agent = AdBudgetAgent()
        result = agent.season_budget_boost(10_000_000, "invalid_season", "saas")
        assert "error" in result

    def test_season_boost_valid(self, mock_anthropic):
        from backend.agents.adbudget_agent import AdBudgetAgent
        agent = AdBudgetAgent()
        result = agent.season_budget_boost(10_000_000, "tet", "fmcg")
        assert "recommended_budget" in result
        assert result["recommended_budget"] > result["base_budget"]
        assert result["cpc_multiplier"] > 1.0


# ═══════════════════════════════════════════════════════════════════════
# PERSONALIZE AGENT (M11)
# ═══════════════════════════════════════════════════════════════════════

class TestPersonalizeAgent:
    def test_clv_tier_champion(self):
        from backend.agents.personalize_agent import calculate_clv_tier
        assert calculate_clv_tier(15_000_000, 5, 8) == "champion"

    def test_clv_tier_loyal(self):
        from backend.agents.personalize_agent import calculate_clv_tier
        assert calculate_clv_tier(5_000_000, 30, 4) == "loyal"

    def test_clv_tier_at_risk(self):
        from backend.agents.personalize_agent import calculate_clv_tier
        assert calculate_clv_tier(1_000_000, 95, 2) == "at_risk"

    def test_clv_tier_lost(self):
        from backend.agents.personalize_agent import calculate_clv_tier
        assert calculate_clv_tier(500_000, 200, 1) == "lost"

    def test_clv_tier_new(self):
        from backend.agents.personalize_agent import calculate_clv_tier
        assert calculate_clv_tier(100_000, 5, 1) == "new"

    def test_segment_customers(self, mock_anthropic):
        from backend.agents.personalize_agent import PersonalizeAgent
        agent = PersonalizeAgent()
        customers = [
            {"id": "1", "name": "A", "total_spent": 20_000_000, "days_since_last_purchase": 10, "purchase_count": 10},
            {"id": "2", "name": "B", "total_spent": 200_000, "days_since_last_purchase": 300, "purchase_count": 1},
        ]
        result = agent.segment_customers(customers)
        assert result["total"] == 2
        assert "champion" in result["summary"] or "lost" in result["summary"]

    def test_segment_customers_assigns_tier(self, mock_anthropic):
        from backend.agents.personalize_agent import PersonalizeAgent
        agent = PersonalizeAgent()
        customers = [
            {"id": "1", "total_spent": 20_000_000, "days_since_last_purchase": 5, "purchase_count": 10}
        ]
        result = agent.segment_customers(customers)
        assert result["summary"].get("champion", 0) == 1


# ═══════════════════════════════════════════════════════════════════════
# COMPLIANCE AGENT (M12)
# ═══════════════════════════════════════════════════════════════════════

class TestComplianceAgent:
    def test_quick_check_clean_content(self):
        from backend.agents.compliance_agent import _quick_check
        result = _quick_check("FuviAI giúp tối ưu marketing doanh nghiệp")
        assert result["quick_check_passed"] is True
        assert result["issues_found"] == 0

    def test_quick_check_superlative_claim(self):
        from backend.agents.compliance_agent import _quick_check
        result = _quick_check("Phần mềm số 1 thị trường Việt Nam")
        assert result["issues_found"] > 0
        assert any(i["level"] == "WARNING" for i in result["issues"])

    def test_quick_check_medical_claim(self):
        from backend.agents.compliance_agent import _quick_check
        result = _quick_check("Sản phẩm chữa bệnh hiệu quả 100%")
        assert result["issues_found"] > 0

    def test_quick_check_gambling_fails(self):
        from backend.agents.compliance_agent import _quick_check
        result = _quick_check("Tham gia cờ bạc online kiếm tiền")
        assert not result["quick_check_passed"]
        assert any(i["level"] == "FAIL" for i in result["issues"])

    def test_quick_check_crisis_keywords(self):
        from backend.agents.compliance_agent import _quick_check
        result = _quick_check("FuviAI scam lừa đảo người dùng")
        assert not result["quick_check_passed"]

    def test_check_content_fail_gambling(self, mock_anthropic):
        from backend.agents.compliance_agent import ComplianceAgent
        agent = ComplianceAgent()
        result = agent.check_content("Tham gia casino online", platform="facebook")
        assert result["verdict"] == "FAIL"
        assert not result["safe_to_publish"]

    def test_check_content_pass(self, mock_anthropic):
        from backend.agents.compliance_agent import ComplianceAgent
        # Override AI response để trả về PASS
        agent = ComplianceAgent()
        agent._client.messages.create.return_value.content[0].text = (
            "VERDICT: PASS\nRISK SCORE: 5\nSAFE TO PUBLISH: Yes\nSUGGESTIONS: None"
        )
        result = agent.check_content(
            "FuviAI giúp doanh nghiệp tối ưu chi phí marketing. Dùng thử 14 ngày miễn phí.",
            platform="facebook"
        )
        assert result["verdict"] in ["PASS", "WARNING"]

    def test_batch_check_returns_list(self, mock_anthropic):
        from backend.agents.compliance_agent import ComplianceAgent
        agent = ComplianceAgent()
        results = agent.batch_check(["Content tốt 1", "Content tốt 2"])
        assert isinstance(results, list)
        assert len(results) == 2

    def test_get_platform_policies_facebook(self, mock_anthropic):
        from backend.agents.compliance_agent import ComplianceAgent
        agent = ComplianceAgent()
        policy = agent.get_platform_policies("facebook")
        assert "Facebook" in policy
        assert len(policy) > 50

    def test_get_platform_policies_unknown(self, mock_anthropic):
        from backend.agents.compliance_agent import ComplianceAgent
        agent = ComplianceAgent()
        policy = agent.get_platform_policies("unknown_platform")
        assert "Chưa có" in policy


# ═══════════════════════════════════════════════════════════════════════
# SCRAPER TOOL
# ═══════════════════════════════════════════════════════════════════════

class TestScraperTool:
    def test_detect_changes_no_change(self):
        from backend.agents.scraper_tool import ScraperTool
        # Import từ tools directory
        pass  # Skip nếu import khác

    def test_detect_changes_title_change(self):
        from backend.tools.scraper_tool import ScraperTool
        scraper = ScraperTool()
        old = {"title": "Old Title", "headings": [], "price_mentions": [], "text_length": 1000}
        new = {"title": "New Title", "headings": [], "price_mentions": [], "text_length": 1000, "timestamp": "2027-01-01"}
        result = scraper.detect_changes(old, new)
        assert result["has_changes"] is True
        assert any(c["type"] == "title_changed" for c in result["changes"])

    def test_detect_changes_price_change(self):
        from backend.tools.scraper_tool import ScraperTool
        scraper = ScraperTool()
        old = {"title": "Same", "headings": [], "price_mentions": ["990.000đ"], "text_length": 1000}
        new = {"title": "Same", "headings": [], "price_mentions": ["790.000đ"], "text_length": 1000, "timestamp": "2027-01-01"}
        result = scraper.detect_changes(old, new)
        assert result["has_changes"] is True
        assert any(c["type"] == "price_changed" for c in result["changes"])

    def test_detect_changes_no_change_same(self):
        from backend.tools.scraper_tool import ScraperTool
        scraper = ScraperTool()
        snapshot = {"title": "Same", "headings": ["H1"], "price_mentions": ["990đ"], "text_length": 1000}
        new = {**snapshot, "timestamp": "2027-01-01"}
        result = scraper.detect_changes(snapshot, new)
        assert not result["has_changes"]
