"""
FuviAI Marketing Agent — Search Tool
Web search wrapper: DuckDuckGo (free) + Google Custom Search (optional)
Dùng bởi: ResearchAgent (M2), ListeningAgent (M7), CompetitorAgent (M10)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus, urlencode

import httpx
from bs4 import BeautifulSoup
from loguru import logger

from backend.config.settings import get_settings


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = ""
    published_at: str = ""


@dataclass
class SearchResponse:
    query: str
    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    engine: str = "duckduckgo"
    error: str = ""

    @property
    def success(self) -> bool:
        return not self.error and len(self.results) > 0


# ─── DuckDuckGo Search ────────────────────────────────────────────────────────

class DuckDuckGoSearch:
    """
    DuckDuckGo HTML search — miễn phí, không cần API key.
    Dùng cho môi trường dev hoặc khi Google CSE chưa được cấu hình.
    """

    BASE_URL = "https://html.duckduckgo.com/html/"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    }

    def search(self, query: str, max_results: int = 10, region: str = "vn-vi") -> SearchResponse:
        """
        Tìm kiếm với DuckDuckGo HTML endpoint.

        Args:
            query: Từ khoá tìm kiếm
            max_results: Số kết quả tối đa (1-30)
            region: Vùng tìm kiếm (vn-vi cho Việt Nam)
        """
        response = SearchResponse(query=query, engine="duckduckgo")
        try:
            payload = {
                "q": query,
                "kl": region,  # kl = region/language
                "kp": "-2",    # safe search off
            }
            resp = httpx.post(
                self.BASE_URL,
                data=payload,
                headers=self.HEADERS,
                timeout=15,
                follow_redirects=True,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            for result_div in soup.select("div.result")[:max_results]:
                title_tag = result_div.select_one("a.result__a")
                snippet_tag = result_div.select_one("a.result__snippet")
                url_tag = result_div.select_one("a.result__url")

                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                url = title_tag.get("href", "")
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                source = url_tag.get_text(strip=True) if url_tag else ""

                if title and url:
                    response.results.append(SearchResult(
                        title=title,
                        url=url,
                        snippet=snippet,
                        source=source,
                    ))

            response.total = len(response.results)
            logger.debug(f"DuckDuckGo '{query}' → {response.total} kết quả")

        except httpx.TimeoutException:
            response.error = "Timeout khi kết nối DuckDuckGo"
            logger.warning(f"DuckDuckGo timeout: {query}")
        except Exception as e:
            response.error = str(e)
            logger.error(f"DuckDuckGo error: {e}")

        return response


# ─── Google Custom Search ─────────────────────────────────────────────────────

class GoogleCustomSearch:
    """
    Google Custom Search JSON API.
    Cần: GOOGLE_CSE_API_KEY + GOOGLE_CSE_ID trong .env
    Free tier: 100 queries/ngày
    """

    BASE_URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.google_cse_api_key
        self.cse_id = settings.google_cse_id

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.cse_id)

    def search(
        self,
        query: str,
        max_results: int = 10,
        lang: str = "lang_vi",
        country: str = "countryVN",
        date_restrict: str = "",
    ) -> SearchResponse:
        """
        Tìm kiếm với Google Custom Search API.

        Args:
            query: Từ khoá tìm kiếm
            max_results: Tối đa 10 mỗi request (giới hạn của Google)
            lang: Ngôn ngữ kết quả (lang_vi cho tiếng Việt)
            country: Quốc gia (countryVN)
            date_restrict: Giới hạn thời gian (d7=7 ngày, m1=1 tháng)
        """
        response = SearchResponse(query=query, engine="google")

        if not self.is_configured:
            response.error = "Google CSE chưa được cấu hình (thiếu GOOGLE_CSE_API_KEY hoặc GOOGLE_CSE_ID)"
            logger.warning(response.error)
            return response

        try:
            params: dict[str, Any] = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "lr": lang,
                "gl": "vn",
                "num": min(max_results, 10),
            }
            if date_restrict:
                params["dateRestrict"] = date_restrict

            resp = httpx.get(self.BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("items", []):
                pagemap = item.get("pagemap", {})
                metatags = pagemap.get("metatags", [{}])[0] if pagemap.get("metatags") else {}
                published = (
                    metatags.get("article:published_time", "")
                    or metatags.get("og:updated_time", "")
                )
                response.results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", "").replace("\n", " ").strip(),
                    source=item.get("displayLink", ""),
                    published_at=published,
                ))

            response.total = int(data.get("searchInformation", {}).get("totalResults", 0))
            logger.debug(f"Google CSE '{query}' → {len(response.results)} kết quả (total: {response.total})")

        except httpx.HTTPStatusError as e:
            response.error = f"Google API HTTP {e.response.status_code}: {e.response.text[:200]}"
            logger.error(response.error)
        except Exception as e:
            response.error = str(e)
            logger.error(f"Google CSE error: {e}")

        return response


# ─── Unified SearchTool ───────────────────────────────────────────────────────

class SearchTool:
    """
    Unified search tool — tự động dùng Google CSE nếu có cấu hình,
    fallback về DuckDuckGo.

    Usage:
        tool = SearchTool()

        # Tìm kiếm cơ bản
        results = tool.search("AI marketing Việt Nam 2026")

        # Tìm kiếm tin tức mới nhất (7 ngày)
        results = tool.search_news("xu hướng FMCG", days=7)

        # Tìm kiếm theo domain cụ thể
        results = tool.search_site("automation", site="cafef.vn")

        # Batch search nhiều từ khoá
        all_results = tool.batch_search(["keyword1", "keyword2"], delay=1.0)
    """

    def __init__(self):
        self._ddg = DuckDuckGoSearch()
        self._google = GoogleCustomSearch()

    def search(
        self,
        query: str,
        max_results: int = 10,
        prefer_google: bool = True,
    ) -> SearchResponse:
        """Tìm kiếm — ưu tiên Google CSE, fallback DuckDuckGo."""
        if prefer_google and self._google.is_configured:
            result = self._google.search(query, max_results=max_results)
            if result.success:
                return result
            logger.warning(f"Google CSE thất bại, fallback DuckDuckGo: {result.error}")

        return self._ddg.search(query, max_results=max_results)

    def search_news(
        self,
        query: str,
        days: int = 7,
        max_results: int = 10,
    ) -> SearchResponse:
        """Tìm kiếm tin tức trong N ngày gần nhất."""
        date_restrict = f"d{days}"

        if self._google.is_configured:
            result = self._google.search(
                query,
                max_results=max_results,
                date_restrict=date_restrict,
            )
            if result.success:
                return result

        # DuckDuckGo: thêm time filter vào query
        time_query = f"{query} site:vnexpress.net OR site:cafef.vn OR site:baodautu.vn OR site:tuoitre.vn"
        return self._ddg.search(time_query, max_results=max_results)

    def search_site(
        self,
        query: str,
        site: str,
        max_results: int = 10,
    ) -> SearchResponse:
        """Tìm kiếm trong một website cụ thể."""
        site_query = f"site:{site} {query}"
        return self.search(site_query, max_results=max_results)

    def search_vn_news(
        self,
        query: str,
        max_results: int = 10,
    ) -> SearchResponse:
        """Tìm kiếm tin tức Việt Nam từ các nguồn uy tín."""
        vn_query = (
            f"{query} "
            "(site:vnexpress.net OR site:cafef.vn OR site:baodautu.vn "
            "OR site:tuoitre.vn OR site:thanhnien.vn OR site:nhandan.vn)"
        )
        return self.search(vn_query, max_results=max_results)

    def batch_search(
        self,
        queries: list[str],
        max_results: int = 5,
        delay: float = 1.0,
    ) -> dict[str, SearchResponse]:
        """
        Tìm kiếm nhiều từ khoá cùng lúc (tuần tự để tránh rate limit).

        Args:
            queries: Danh sách từ khoá
            max_results: Số kết quả mỗi từ khoá
            delay: Thời gian chờ giữa các request (giây)
        """
        results: dict[str, SearchResponse] = {}
        for i, query in enumerate(queries):
            results[query] = self.search(query, max_results=max_results)
            if i < len(queries) - 1:
                time.sleep(delay)
        return results

    def format_results_for_llm(self, response: SearchResponse, max_chars: int = 3000) -> str:
        """Chuyển kết quả search thành text cho LLM context."""
        if not response.success:
            return f"Không tìm thấy kết quả cho: {response.query}"

        lines = [f"Kết quả tìm kiếm cho: '{response.query}'\n"]
        total_chars = 0

        for i, r in enumerate(response.results, 1):
            block = (
                f"{i}. **{r.title}**\n"
                f"   URL: {r.url}\n"
                f"   {r.snippet}\n"
            )
            if r.published_at:
                block += f"   Ngày đăng: {r.published_at}\n"
            block += "\n"

            if total_chars + len(block) > max_chars:
                break
            lines.append(block)
            total_chars += len(block)

        return "".join(lines)
