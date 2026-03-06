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


# ═══════════════════════════════════════════════════════════════════════
# SEARCH TOOL
# ═══════════════════════════════════════════════════════════════════════

class TestSearchTool:
    def test_search_response_success_true(self):
        from backend.tools.search_tool import SearchResponse, SearchResult
        resp = SearchResponse(query="test")
        resp.results = [SearchResult(title="T", url="https://example.com", snippet="S")]
        resp.total = 1
        assert resp.success is True

    def test_search_response_success_false_no_results(self):
        from backend.tools.search_tool import SearchResponse
        resp = SearchResponse(query="test")
        assert resp.success is False

    def test_search_response_success_false_has_error(self):
        from backend.tools.search_tool import SearchResponse, SearchResult
        resp = SearchResponse(query="test", error="timeout")
        resp.results = [SearchResult(title="T", url="https://x.com", snippet="S")]
        assert resp.success is False

    def test_format_results_for_llm_no_results(self):
        from backend.tools.search_tool import SearchResponse, SearchTool
        tool = SearchTool()
        resp = SearchResponse(query="test", error="lỗi kết nối")
        text = tool.format_results_for_llm(resp)
        assert "Không tìm thấy" in text

    def test_format_results_for_llm_with_results(self):
        from backend.tools.search_tool import SearchResponse, SearchResult, SearchTool
        tool = SearchTool()
        resp = SearchResponse(query="AI marketing")
        resp.results = [
            SearchResult(title="FuviAI ra mắt", url="https://fuviai.com", snippet="Tin tức mới nhất về AI", source="fuviai.com"),
        ]
        resp.total = 1
        text = tool.format_results_for_llm(resp)
        assert "FuviAI ra mắt" in text
        assert "AI marketing" in text

    def test_format_results_respects_max_chars(self):
        from backend.tools.search_tool import SearchResponse, SearchResult, SearchTool
        tool = SearchTool()
        resp = SearchResponse(query="test")
        resp.results = [
            SearchResult(title=f"Title {i}", url=f"https://ex.com/{i}", snippet="A" * 500)
            for i in range(20)
        ]
        resp.total = 20
        text = tool.format_results_for_llm(resp, max_chars=500)
        assert len(text) <= 600  # chút tolerance cho header

    @patch("backend.tools.search_tool.httpx.post")
    def test_duckduckgo_timeout(self, mock_post):
        import httpx
        from backend.tools.search_tool import DuckDuckGoSearch
        mock_post.side_effect = httpx.TimeoutException("timeout")
        ddg = DuckDuckGoSearch()
        result = ddg.search("test query")
        assert result.success is False
        assert "Timeout" in result.error

    @patch("backend.tools.search_tool.httpx.post")
    def test_duckduckgo_returns_results(self, mock_post):
        from backend.tools.search_tool import DuckDuckGoSearch
        mock_resp = MagicMock()
        mock_resp.text = """
        <html><body>
          <div class="result">
            <a class="result__a" href="https://example.com">Tiêu đề bài viết</a>
            <a class="result__snippet">Mô tả ngắn về bài viết</a>
            <a class="result__url">example.com</a>
          </div>
        </body></html>
        """
        mock_post.return_value = mock_resp
        ddg = DuckDuckGoSearch()
        result = ddg.search("AI marketing Việt Nam")
        assert result.engine == "duckduckgo"
        assert isinstance(result.results, list)

    def test_google_not_configured(self):
        from backend.tools.search_tool import GoogleCustomSearch
        with patch("backend.tools.search_tool.get_settings") as mock_settings:
            mock_settings.return_value.google_cse_api_key = ""
            mock_settings.return_value.google_cse_id = ""
            g = GoogleCustomSearch()
            assert g.is_configured is False
            resp = g.search("test")
            assert resp.success is False
            assert "chưa được cấu hình" in resp.error

    def test_search_tool_fallback_to_ddg(self):
        """Nếu Google không cấu hình, SearchTool phải dùng DuckDuckGo."""
        from backend.tools.search_tool import SearchTool, SearchResponse, SearchResult
        tool = SearchTool()
        # Google không configured
        tool._google._api_key = ""
        tool._google._cse_id = ""

        mock_resp = SearchResponse(query="test")
        mock_resp.results = [SearchResult(title="DDG Result", url="https://ddg.com", snippet="snippet")]
        mock_resp.total = 1

        with patch.object(tool._ddg, "search", return_value=mock_resp):
            result = tool.search("test query", prefer_google=True)
        assert result.engine == "duckduckgo"
        assert len(result.results) == 1

    def test_batch_search_returns_dict(self):
        from backend.tools.search_tool import SearchTool, SearchResponse
        tool = SearchTool()
        empty = SearchResponse(query="q")
        with patch.object(tool, "search", return_value=empty):
            results = tool.batch_search(["kw1", "kw2"], delay=0)
        assert isinstance(results, dict)
        assert "kw1" in results
        assert "kw2" in results


# ═══════════════════════════════════════════════════════════════════════
# RESEARCH AGENT — search_market
# ═══════════════════════════════════════════════════════════════════════

class TestResearchAgentSearchMarket:
    @pytest.fixture
    def agent(self, mock_anthropic):
        with patch("backend.agents.research_agent.VectorStore"), \
             patch("backend.agents.research_agent.SearchTool") as mock_search_cls:
            from backend.agents.research_agent import ResearchAgent
            a = ResearchAgent()
            a._search = mock_search_cls()
            yield a

    def test_search_market_no_results(self, agent):
        from backend.tools.search_tool import SearchResponse
        agent._search.search_news.return_value = SearchResponse(query="test", error="lỗi")
        result = agent.search_market("AI marketing")
        assert "Không tìm thấy" in result

    def test_search_market_with_results(self, agent):
        from backend.tools.search_tool import SearchResponse, SearchResult
        resp = SearchResponse(query="AI marketing")
        resp.results = [
            SearchResult(title="AI marketing VN 2026", url="https://ex.com", snippet="Xu hướng mới")
        ]
        resp.total = 1
        agent._search.search_news.return_value = resp
        agent._search.format_results_for_llm.return_value = "Kết quả tìm kiếm cho: 'AI marketing'"
        with patch.object(agent.vector_store, "add_documents", return_value=1):
            result = agent.search_market("AI marketing", days=7)
        assert isinstance(result, str)
        assert len(result) > 0


# ═══════════════════════════════════════════════════════════════════════
# COMPETITOR AGENT — search_competitor_news
# ═══════════════════════════════════════════════════════════════════════

class TestCompetitorAgentNews:
    @pytest.fixture
    def agent(self, mock_anthropic):
        with patch("backend.agents.competitor_agent.ScraperTool"), \
             patch("backend.agents.competitor_agent.SearchTool") as mock_search_cls:
            from backend.agents.competitor_agent import CompetitorAgent
            a = CompetitorAgent()
            a._search = mock_search_cls()
            yield a

    def test_search_competitor_news_returns_list(self, agent):
        from backend.tools.search_tool import SearchResponse, SearchResult
        resp = SearchResponse(query="Haravan")
        resp.results = [
            SearchResult(title="Haravan ra mắt tính năng mới", url="https://haravan.com/news", snippet="Chi tiết...", source="haravan.com"),
        ]
        resp.total = 1
        agent._search.search_news.return_value = resp
        news = agent.search_competitor_news("Haravan", days=30)
        assert isinstance(news, list)
        assert len(news) == 1
        assert news[0]["title"] == "Haravan ra mắt tính năng mới"

    def test_search_competitor_news_empty(self, agent):
        from backend.tools.search_tool import SearchResponse
        agent._search.search_news.return_value = SearchResponse(query="Unknown")
        news = agent.search_competitor_news("Unknown Corp")
        assert news == []


# ═══════════════════════════════════════════════════════════════════════
# EMAIL TOOL (SendGrid)
# ═══════════════════════════════════════════════════════════════════════

class TestEmailTool:
    """Unit tests cho EmailTool — mock httpx và SendGrid settings."""

    @pytest.fixture
    def tool_disabled(self):
        """EmailTool khi chưa cấu hình API key."""
        with patch("backend.tools.email_tool.EmailTool.__init__", lambda self: None):
            from backend.tools.email_tool import EmailTool
            t = EmailTool.__new__(EmailTool)
            t._api_key = ""
            t._from_email = "noreply@fuviai.com"
            t._from_name = "FuviAI Marketing"
            t._enabled = False
            return t

    @pytest.fixture
    def tool_enabled(self):
        """EmailTool đã cấu hình API key."""
        with patch("backend.tools.email_tool.EmailTool.__init__", lambda self: None):
            from backend.tools.email_tool import EmailTool
            t = EmailTool.__new__(EmailTool)
            t._api_key = "SG.test_key"
            t._from_email = "noreply@fuviai.com"
            t._from_name = "FuviAI Marketing"
            t._enabled = True
            return t

    def test_validate_email_valid(self, tool_disabled):
        assert tool_disabled.validate_email("test@example.com") is True
        assert tool_disabled.validate_email("nguyen.van.a@company.vn") is True

    def test_validate_email_invalid(self, tool_disabled):
        assert tool_disabled.validate_email("not-an-email") is False
        assert tool_disabled.validate_email("@nodomain.com") is False
        assert tool_disabled.validate_email("") is False

    def test_send_disabled_returns_error(self, tool_disabled):
        from backend.tools.email_tool import EmailResult
        result = tool_disabled.send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="Hello",
        )
        assert result.success is False
        assert "not configured" in result.error.lower()

    def test_send_bulk_disabled_returns_batch_error(self, tool_disabled):
        result = tool_disabled.send_bulk(
            recipients=[{"email": "a@b.com", "name": "Test"}],
            subject="Test",
            html_content="Hello",
        )
        assert result.sent == 0
        assert result.failed == 1

    def test_wrap_html_plain_text(self, tool_disabled):
        html = tool_disabled._wrap_html("Xin chào\n\nNội dung", "Subject")
        assert "<p>" in html
        assert "Xin chào" in html

    def test_wrap_html_preserves_existing_html(self, tool_disabled):
        raw = "<p>Already HTML</p>"
        result = tool_disabled._wrap_html(raw, "Subject")
        assert result == raw

    def test_plain_from_html(self, tool_disabled):
        html = "<p>Xin <b>chào</b></p>"
        plain = tool_disabled._plain_from_html(html)
        assert "<" not in plain
        assert "Xin" in plain and "chào" in plain

    def test_send_email_success(self, tool_enabled):
        import httpx
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 202
        mock_resp.content = b""
        with patch("backend.tools.email_tool.httpx.post", return_value=mock_resp):
            result = tool_enabled.send_email(
                to_email="khach@example.com",
                to_name="Khách Hàng",
                subject="Ưu đãi đặc biệt",
                html_content="<p>Nội dung email</p>",
                categories=["test"],
            )
        assert result.success is True
        assert result.status_code == 202

    def test_send_email_failure(self, tool_enabled):
        import httpx
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 401
        mock_resp.content = b'{"errors": [{"message": "Unauthorized"}]}'
        mock_resp.json.return_value = {"errors": [{"message": "Unauthorized"}]}
        with patch("backend.tools.email_tool.httpx.post", return_value=mock_resp):
            result = tool_enabled.send_email(
                to_email="test@example.com",
                subject="Test",
                html_content="Hello",
            )
        assert result.success is False
        assert result.status_code == 401

    def test_send_bulk_partial_success(self, tool_enabled):
        import httpx
        mock_ok = MagicMock(spec=httpx.Response)
        mock_ok.status_code = 202
        mock_ok.content = b""
        mock_fail = MagicMock(spec=httpx.Response)
        mock_fail.status_code = 400
        mock_fail.content = b'{"errors": []}'
        mock_fail.json.return_value = {"errors": []}

        responses = iter([mock_ok, mock_fail])
        with patch("backend.tools.email_tool.httpx.post", side_effect=lambda *a, **kw: next(responses)):
            result = tool_enabled.send_bulk(
                recipients=[
                    {"email": "ok@example.com", "name": "OK"},
                    {"email": "fail@example.com", "name": "Fail"},
                ],
                subject="Bulk Test",
                html_content="<p>Nội dung</p>",
            )
        assert result.sent == 1
        assert result.failed == 1

    def test_send_birthday(self, tool_enabled):
        import httpx
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 202
        mock_resp.content = b""
        with patch("backend.tools.email_tool.httpx.post", return_value=mock_resp):
            result = tool_enabled.send_birthday(
                to_email="khach@example.com",
                to_name="Nguyễn Văn A",
                email_content="Chúc mừng sinh nhật!",
            )
        assert result.success is True

    def test_send_abandoned_cart_step1(self, tool_enabled):
        import httpx
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 202
        mock_resp.content = b""
        with patch("backend.tools.email_tool.httpx.post", return_value=mock_resp):
            result = tool_enabled.send_abandoned_cart(
                to_email="khach@example.com",
                to_name="Test",
                email_content="Bạn còn quên gì?",
                cart_value=500_000,
                step=1,
            )
        assert result.success is True

    def test_timeout_returns_error(self, tool_enabled):
        import httpx
        with patch("backend.tools.email_tool.httpx.post", side_effect=httpx.TimeoutException("timeout")):
            result = tool_enabled.send_email(
                to_email="test@example.com",
                subject="Test",
                html_content="Hello",
            )
        assert result.success is False
        assert result.status_code == 408


# ═══════════════════════════════════════════════════════════════════════
# PERSONALIZE AGENT — send_* methods
# ═══════════════════════════════════════════════════════════════════════

class TestPersonalizeAgentEmailSend:
    @pytest.fixture
    def agent(self, mock_anthropic):
        with patch("backend.agents.personalize_agent.EmailTool") as mock_email_cls:
            from backend.agents.personalize_agent import PersonalizeAgent
            a = PersonalizeAgent()
            mock_email = mock_email_cls.return_value
            mock_email.validate_email.return_value = True
            a._email = mock_email
            yield a

    def test_send_personalized_email_invalid_email(self, agent):
        agent._email.validate_email.return_value = False
        result = agent.send_personalized_email(
            {"name": "Test", "email": "bad-email"},
            segment="potential",
        )
        assert result.success is False
        assert "Invalid" in result.error

    def test_send_personalized_email_missing_email(self, agent):
        result = agent.send_personalized_email(
            {"name": "Test"},  # không có "email"
            segment="potential",
        )
        assert result.success is False

    def test_send_personalized_email_success(self, agent):
        from backend.tools.email_tool import EmailResult
        agent._email.send_email.return_value = EmailResult(success=True, status_code=202)
        result = agent.send_personalized_email(
            {"name": "Nguyễn Văn A", "email": "a@example.com", "total_spent": 5_000_000},
            segment="loyal",
            trigger="inactive_90d",
        )
        assert result.success is True
        agent._email.send_email.assert_called_once()

    def test_send_birthday_invalid_email(self, agent):
        agent._email.validate_email.return_value = False
        result = agent.send_birthday_campaign("bad@", "Test")
        assert result.success is False

    def test_send_birthday_success(self, agent):
        from backend.tools.email_tool import EmailResult
        agent._email.send_birthday.return_value = EmailResult(success=True, status_code=202)
        result = agent.send_birthday_campaign(
            "khach@example.com", "Nguyễn Văn A", tier="champion"
        )
        assert result.success is True

    def test_send_abandoned_cart_sequence_step1(self, agent):
        from backend.tools.email_tool import EmailResult
        agent._email.send_abandoned_cart.return_value = EmailResult(success=True)
        results = agent.send_abandoned_cart_sequence(
            "khach@example.com", "Test", 1_000_000,
            ["FuviAI Pro", "FuviAI Business"], steps=[1],
        )
        assert "step_1" in results
        assert results["step_1"].success is True

    def test_send_bulk_skips_invalid_emails(self, agent):
        agent._email.validate_email.side_effect = lambda e: "@" in e and "." in e.split("@")[1]
        agent._email.send_email.return_value = MagicMock(success=True)
        result = agent.send_bulk_segment_email(
            customers=[
                {"email": "ok@example.com", "name": "OK", "clv_tier": "loyal"},
                {"email": "bad-email", "name": "Bad"},
            ],
            base_message="Tin tức mới từ FuviAI",
            subject="Cập nhật tháng 3",
        )
        assert result.failed >= 1
