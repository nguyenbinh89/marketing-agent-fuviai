"""
FuviAI Marketing Agent — Research Agent (M2)
Crawl và tóm tắt tin tức thị trường VN, lưu vào ChromaDB
"""

from __future__ import annotations

import re
from datetime import datetime, date
from typing import Any
from loguru import logger

import requests
from bs4 import BeautifulSoup

from backend.agents.base_agent import BaseAgent
from backend.config.prompts_vn import RESEARCH_AGENT_SYSTEM
from backend.memory.vector_store import VectorStore
from backend.tools.search_tool import SearchTool


# ─── News Sources cấu hình ─────────────────────────────────────────────────

NEWS_SOURCES = {
    "cafef": {
        "name": "CafeF",
        "url": "https://cafef.vn/thi-truong-chung-khoan.chn",
        "article_selector": "h3.title a, h2.title a",
        "content_selector": "div.detail-content p",
        "base_url": "https://cafef.vn",
    },
    "vnexpress_kinhdoanh": {
        "name": "VnExpress Kinh Doanh",
        "url": "https://vnexpress.net/kinh-doanh",
        "article_selector": "h3.title-news a, h2.title-news a",
        "content_selector": "article p",
        "base_url": "https://vnexpress.net",
    },
    "baodautu": {
        "name": "Báo Đầu Tư",
        "url": "https://baodautu.vn/kinh-doanh",
        "article_selector": "h3.article-title a, h2.article-title a",
        "content_selector": "div.article-content p",
        "base_url": "https://baodautu.vn",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}


class ResearchAgent(BaseAgent):
    """
    Agent nghiên cứu thị trường VN.
    Crawl tin tức → tóm tắt → lưu vào ChromaDB → RAG.

    Usage:
        agent = ResearchAgent()
        report = agent.daily_market_report()
        keywords = agent.research_keywords("FMCG Việt Nam")
    """

    def __init__(self):
        super().__init__(
            system_prompt=RESEARCH_AGENT_SYSTEM,
            max_tokens=8096,
            temperature=0.3,  # Thấp hơn để phân tích chính xác hơn
        )
        self.vector_store = VectorStore()
        self._session = requests.Session()
        self._session.headers.update(HEADERS)
        self._search = SearchTool()

    # ─── Crawling ───────────────────────────────────────────────────────────

    def crawl_article_links(self, source_key: str, max_articles: int = 10) -> list[str]:
        """Lấy danh sách link bài viết từ trang chủ của source."""
        source = NEWS_SOURCES.get(source_key)
        if not source:
            return []

        try:
            resp = self._session.get(source["url"], timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            links = []
            for tag in soup.select(source["article_selector"]):
                href = tag.get("href", "")
                if href.startswith("http"):
                    links.append(href)
                elif href.startswith("/"):
                    links.append(source["base_url"] + href)

            links = list(dict.fromkeys(links))[:max_articles]  # dedupe
            logger.info(f"Found {len(links)} articles from {source['name']}")
            return links

        except Exception as e:
            logger.warning(f"Crawl failed for {source_key}: {e}")
            return []

    def crawl_article_content(self, url: str, source_key: str) -> dict[str, str] | None:
        """Crawl nội dung 1 bài viết."""
        source = NEWS_SOURCES.get(source_key, {})
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Lấy title
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Lấy nội dung
            selector = source.get("content_selector", "article p, div.content p")
            paragraphs = soup.select(selector)
            text = " ".join(p.get_text(strip=True) for p in paragraphs[:20])
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) < 100:
                return None

            return {
                "title": title,
                "text": f"{title}. {text}",
                "source": source.get("name", source_key),
                "url": url,
                "date": date.today().isoformat(),
                "category": "market_news",
            }

        except Exception as e:
            logger.warning(f"Article crawl failed {url}: {e}")
            return None

    def crawl_all_sources(self, max_per_source: int = 5) -> list[dict]:
        """Crawl tất cả news sources và trả về list articles."""
        all_articles = []

        for source_key in NEWS_SOURCES:
            links = self.crawl_article_links(source_key, max_articles=max_per_source)
            for url in links:
                article = self.crawl_article_content(url, source_key)
                if article:
                    all_articles.append(article)

        logger.info(f"Crawled {len(all_articles)} articles total")
        return all_articles

    # ─── Analysis ───────────────────────────────────────────────────────────

    def daily_market_report(self, industry: str = "tổng quan") -> str:
        """
        Tạo báo cáo thị trường hàng ngày.
        Crawl tin tức → lưu ChromaDB → dùng Claude tổng hợp.
        """
        logger.info(f"Generating daily market report | industry={industry}")

        # Crawl tin tức
        articles = self.crawl_all_sources(max_per_source=3)

        # Lưu vào vector store
        if articles:
            added = self.vector_store.add_documents(articles)
            logger.info(f"Saved {added} articles to knowledge base")

        # Lấy context từ vector store
        context = self.vector_store.format_context_for_prompt(
            query=f"thị trường {industry} Việt Nam hôm nay",
            n_results=8,
        )

        # Tổng hợp bằng Claude
        today = datetime.now().strftime("%d/%m/%Y")
        prompt = f"""Dựa trên dữ liệu sau, tạo báo cáo thị trường ngày {today}:

{context}

Tổng hợp báo cáo theo format chuẩn của FuviAI, tập trung vào ngành: {industry}"""

        return self.chat(prompt, reset_history=True)

    def research_industry(
        self,
        industry: str,
        aspects: list[str] | None = None,
    ) -> str:
        """
        Nghiên cứu sâu về một ngành cụ thể.
        Kết hợp knowledge base + Claude analysis.
        """
        if aspects is None:
            aspects = ["xu hướng", "cơ hội", "thách thức", "đối thủ chính"]

        context = self.vector_store.format_context_for_prompt(
            query=f"{industry} Việt Nam 2025 2026",
            n_results=6,
        )

        aspects_str = ", ".join(aspects)
        prompt = f"""Phân tích ngành {industry} tại Việt Nam, tập trung vào: {aspects_str}

Dữ liệu tham khảo:
{context}

Cung cấp insight cụ thể, có số liệu, relevant với doanh nghiệp SME Việt Nam."""

        return self.chat(prompt, reset_history=True)

    def research_keywords(self, topic: str) -> str:
        """
        Nghiên cứu từ khoá cho topic.
        Kết hợp với SEO Agent ở Phase 1 cuối.
        """
        context = self.vector_store.format_context_for_prompt(
            query=topic, n_results=5
        )

        prompt = f"""Gợi ý 15 từ khoá SEO tiếng Việt cho chủ đề: "{topic}"

Context market data:
{context}

Phân loại thành:
1. Short-tail keywords (1-2 từ) — 5 từ khoá
2. Long-tail keywords (3-5 từ) — 7 từ khoá
3. Question keywords (câu hỏi) — 3 từ khoá

Ước tính search intent và mức độ cạnh tranh (cao/trung bình/thấp)."""

        return self.chat(prompt, reset_history=True)

    def search_market(self, query: str, days: int = 7, max_results: int = 8) -> str:
        """
        Tìm kiếm thông tin thị trường theo từ khoá + thời gian.
        Lưu kết quả vào ChromaDB và trả về tóm tắt AI.

        Args:
            query: Từ khoá tìm kiếm (VD: "AI marketing Việt Nam 2026")
            days: Giới hạn kết quả trong N ngày gần nhất (chỉ có tác dụng với Google CSE)
            max_results: Số kết quả tối đa
        """
        logger.info(f"Search market | query='{query}' | days={days}")

        response = self._search.search_news(query, days=days, max_results=max_results)

        if not response.success:
            return f"Không tìm thấy kết quả cho: '{query}'. Lỗi: {response.error}"

        # Lưu vào vector store
        articles = [
            {
                "title": r.title,
                "text": f"{r.title}. {r.snippet}",
                "source": r.source,
                "url": r.url,
                "date": r.published_at or date.today().isoformat(),
                "category": "search_result",
            }
            for r in response.results
            if r.title and r.snippet
        ]
        if articles:
            self.vector_store.add_documents(articles)

        # Tổng hợp bằng Claude
        context = self._search.format_results_for_llm(response)
        prompt = f"""Tóm tắt và phân tích các kết quả tìm kiếm sau về chủ đề: "{query}"

{context}

Cung cấp:
1. **Tóm tắt chính** (3-5 điểm quan trọng nhất)
2. **Xu hướng nổi bật** từ các nguồn này
3. **Insight cho marketing** — doanh nghiệp SME Việt Nam nên lưu ý gì?"""

        return self.chat(prompt, reset_history=True)

    def summarize_url(self, url: str) -> str:
        """Tóm tắt nội dung 1 URL bất kỳ."""
        try:
            resp = self._session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Remove scripts/styles
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()

            text = soup.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)[:3000]  # Giới hạn 3000 ký tự

        except Exception as e:
            return f"Không thể crawl URL: {e}"

        prompt = f"""Tóm tắt nội dung bài viết sau trong 200 chữ tiếng Việt,
tập trung vào insight marketing và kinh doanh:

{text}"""

        return self.chat(prompt, reset_history=True)
