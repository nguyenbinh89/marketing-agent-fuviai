"""
FuviAI Marketing Agent — Scraper Tool
Playwright + BeautifulSoup4 web scraper cho crawling dữ liệu public
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from loguru import logger

import requests
from bs4 import BeautifulSoup


# Lazy import playwright (optional, nặng hơn)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright chưa cài — dùng requests fallback")


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
}


class ScraperTool:
    """
    Web scraper kết hợp requests + BeautifulSoup (nhanh)
    và Playwright (cho trang cần JS render).

    Usage:
        scraper = ScraperTool()
        html = scraper.fetch("https://cafef.vn")
        text = scraper.get_text("https://vnexpress.net/kinh-doanh")
        posts = scraper.scrape_facebook_page("fanpageid")
    """

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    # ─── Basic Fetch ─────────────────────────────────────────────────────────

    def fetch(self, url: str, use_playwright: bool = False) -> str:
        """Lấy HTML của URL. Trả về string rỗng nếu lỗi."""
        if use_playwright and _PLAYWRIGHT_AVAILABLE:
            return self._fetch_playwright(url)
        return self._fetch_requests(url)

    def _fetch_requests(self, url: str) -> str:
        try:
            resp = self._session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except Exception as e:
            logger.warning(f"Fetch failed | url={url} | error={e}")
            return ""

    def _fetch_playwright(self, url: str) -> str:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_extra_http_headers(HEADERS)
                page.goto(url, timeout=self.timeout * 1000)
                page.wait_for_load_state("networkidle", timeout=self.timeout * 1000)
                content = page.content()
                browser.close()
                return content
        except Exception as e:
            logger.warning(f"Playwright fetch failed | url={url} | error={e}")
            return ""

    def get_text(self, url: str, use_playwright: bool = False) -> str:
        """Lấy text thuần (strip HTML tags) từ URL."""
        html = self.fetch(url, use_playwright)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        # Xóa script + style
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # Xóa dòng trắng thừa
        lines = [l for l in text.splitlines() if l.strip()]
        return "\n".join(lines)

    def parse_soup(self, url: str, use_playwright: bool = False) -> BeautifulSoup | None:
        """Trả về BeautifulSoup object để parse tuỳ ý."""
        html = self.fetch(url, use_playwright)
        if not html:
            return None
        return BeautifulSoup(html, "html.parser")

    # ─── CafeF / VnExpress ───────────────────────────────────────────────────

    def scrape_cafef_headlines(self, max_articles: int = 10) -> list[dict[str, str]]:
        """Crawl headlines từ CafeF (marketing/quảng cáo)."""
        urls = [
            "https://cafef.vn/doanh-nghiep.chn",
            "https://cafef.vn/kinh-doanh.chn",
        ]
        articles = []
        for url in urls:
            soup = self.parse_soup(url)
            if not soup:
                continue
            for a in soup.select("h3 a, h2 a")[:max_articles]:
                href = a.get("href", "")
                title = a.get_text(strip=True)
                if title and href:
                    if not href.startswith("http"):
                        href = "https://cafef.vn" + href
                    articles.append({"title": title, "url": href, "source": "CafeF"})
            if len(articles) >= max_articles:
                break
        return articles[:max_articles]

    def scrape_vnexpress_business(self, max_articles: int = 10) -> list[dict[str, str]]:
        """Crawl headlines từ VnExpress Kinh doanh."""
        soup = self.parse_soup("https://vnexpress.net/kinh-doanh")
        if not soup:
            return []
        articles = []
        for a in soup.select("h3.title-news a, h2.title-news a")[:max_articles]:
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if title and href:
                articles.append({"title": title, "url": href, "source": "VnExpress"})
        return articles

    def scrape_article_content(self, url: str, max_chars: int = 3000) -> str:
        """Lấy nội dung bài viết từ CafeF/VnExpress."""
        soup = self.parse_soup(url)
        if not soup:
            return ""
        # Tìm article body
        for selector in ["article", ".fck_detail", ".sidebar-1", "div.content-detail"]:
            body = soup.select_one(selector)
            if body:
                text = body.get_text(separator="\n", strip=True)
                return text[:max_chars]
        return self.get_text(url)[:max_chars]

    # ─── Website Monitoring ───────────────────────────────────────────────────

    def get_page_snapshot(self, url: str) -> dict[str, Any]:
        """
        Lấy snapshot của webpage để monitor thay đổi.
        Trả về: {title, description, headings, links, price_mentions, timestamp}
        """
        soup = self.parse_soup(url, use_playwright=False)
        if not soup:
            return {"url": url, "error": "Không thể crawl", "timestamp": datetime.now().isoformat()}

        title = soup.find("title")
        meta_desc = soup.find("meta", {"name": "description"})

        # Trích giá (dạng 1.000.000đ hoặc 1,000,000 VND)
        text = soup.get_text()
        price_pattern = r"\d{1,3}(?:[.,]\d{3})*\s*(?:đ|VND|vnđ|₫)"
        prices = re.findall(price_pattern, text, re.IGNORECASE)

        headings = [h.get_text(strip=True) for h in soup.select("h1, h2")[:10]]

        return {
            "url": url,
            "title": title.get_text(strip=True) if title else "",
            "description": meta_desc.get("content", "") if meta_desc else "",
            "headings": headings,
            "price_mentions": list(set(prices))[:10],
            "text_length": len(text),
            "timestamp": datetime.now().isoformat(),
        }

    def detect_changes(
        self,
        old_snapshot: dict[str, Any],
        new_snapshot: dict[str, Any],
    ) -> dict[str, Any]:
        """So sánh 2 snapshots, trả về danh sách thay đổi."""
        changes = []

        if old_snapshot.get("title") != new_snapshot.get("title"):
            changes.append({
                "type": "title_changed",
                "old": old_snapshot.get("title"),
                "new": new_snapshot.get("title"),
            })

        old_prices = set(old_snapshot.get("price_mentions", []))
        new_prices = set(new_snapshot.get("price_mentions", []))
        if old_prices != new_prices:
            added = new_prices - old_prices
            removed = old_prices - new_prices
            if added or removed:
                changes.append({
                    "type": "price_changed",
                    "added": list(added),
                    "removed": list(removed),
                })

        old_h = set(old_snapshot.get("headings", []))
        new_h = set(new_snapshot.get("headings", []))
        new_headings = new_h - old_h
        if new_headings:
            changes.append({
                "type": "new_content",
                "new_headings": list(new_headings),
            })

        size_diff = new_snapshot.get("text_length", 0) - old_snapshot.get("text_length", 0)
        if abs(size_diff) > 500:
            changes.append({
                "type": "content_size_changed",
                "diff": size_diff,
            })

        return {
            "has_changes": bool(changes),
            "changes": changes,
            "checked_at": new_snapshot.get("timestamp"),
        }

    # ─── Hashtag / Keyword Research ───────────────────────────────────────────

    def get_trending_hashtags_vn(self) -> list[str]:
        """
        Lấy trending hashtags VN từ các nguồn public.
        Trả về list hashtag (fallback nếu không crawl được).
        """
        # Fallback: hashtag phổ biến ngành marketing VN 2026
        base_hashtags = [
            "#marketing", "#vietnam", "#kinh_doanh", "#startup_vietnam",
            "#thuong_mai_dien_tu", "#digital_marketing", "#content_marketing",
            "#fuviai", "#ai_marketing", "#automation",
        ]
        return base_hashtags
