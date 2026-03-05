"""
FuviAI Marketing Agent — SEO Agent (M4)
SEO + AEO (Answer Engine Optimization) cho Google Search & AI Search
"""

from __future__ import annotations

from loguru import logger

from backend.agents.base_agent import BaseAgent
from backend.config.prompts_vn import SEO_AGENT_SYSTEM
from backend.memory.vector_store import VectorStore


class SEOAgent(BaseAgent):
    """
    Agent tối ưu SEO & AEO cho thị trường Việt Nam.

    Usage:
        agent = SEOAgent()
        keywords = agent.research_keywords("phần mềm quản lý bán hàng")
        meta = agent.generate_meta_tags(page_title="...", description="...")
    """

    def __init__(self):
        super().__init__(
            system_prompt=SEO_AGENT_SYSTEM,
            max_tokens=4096,
            temperature=0.3,
        )
        self.vector_store = VectorStore()

    # ─── Keyword Research ────────────────────────────────────────────────────

    def research_keywords(
        self,
        topic: str,
        industry: str = "",
        target_location: str = "Việt Nam",
    ) -> str:
        """
        Nghiên cứu từ khoá SEO cho topic/ngành.
        Trả về 10 từ khoá với phân tích intent và cạnh tranh.
        """
        context = self.vector_store.format_context_for_prompt(
            query=f"SEO {topic} {industry}",
            n_results=3,
        )

        prompt = f"""Nghiên cứu từ khoá SEO tiếng Việt cho:
- Chủ đề: {topic}
- Ngành: {industry or "tổng quát"}
- Địa điểm target: {target_location}

{context if context else ""}

Cung cấp danh sách 10 từ khoá với:
1. Từ khoá chính (primary keyword)
2. Từ khoá phụ (LSI keywords)
3. Long-tail keywords
4. Question keywords (People Also Ask)
5. Search intent: Informational / Navigational / Commercial / Transactional
6. Mức độ cạnh tranh: Cao / Trung bình / Thấp
7. Gợi ý content format phù hợp"""

        logger.info(f"Keyword research | topic={topic}")
        return self.chat(prompt, reset_history=True)

    # ─── Meta Tags ───────────────────────────────────────────────────────────

    def generate_meta_tags(
        self,
        page_title: str,
        page_description: str,
        keywords: list[str] | None = None,
        page_type: str = "article",
    ) -> str:
        """
        Tạo meta tags tối ưu cho SEO.
        Bao gồm: title, description, OG tags, Twitter Card.
        """
        kw_str = ", ".join(keywords) if keywords else "tự xác định"

        prompt = f"""Tạo meta tags SEO đầy đủ cho trang web sau:

**Tiêu đề trang:** {page_title}
**Mô tả nội dung:** {page_description}
**Từ khoá target:** {kw_str}
**Loại trang:** {page_type}

Cung cấp:
1. `<title>` tag (< 60 ký tự, có từ khoá chính)
2. `<meta name="description">` (< 160 ký tự, có CTA)
3. Open Graph tags (og:title, og:description, og:type)
4. Twitter Card tags
5. Canonical URL structure gợi ý
6. Schema.org markup JSON-LD (phù hợp với {page_type})

Format output: HTML code blocks sẵn để copy-paste"""

        return self.chat(prompt, reset_history=True)

    # ─── Content Outline ─────────────────────────────────────────────────────

    def generate_content_outline(
        self,
        keyword: str,
        word_count: int = 1500,
        content_type: str = "blog",
    ) -> str:
        """
        Tạo content outline chuẩn SEO cho 1 từ khoá.
        """
        prompt = f"""Tạo content outline chuẩn SEO cho từ khoá: "{keyword}"

**Loại content:** {content_type}
**Số từ mục tiêu:** {word_count} chữ
**Thị trường:** Việt Nam

Cung cấp:
1. **SEO Title** (H1) — có từ khoá, < 60 ký tự
2. **Meta description** — < 160 ký tự
3. **Outline chi tiết:**
   - Intro paragraph (hook + keyword mention)
   - H2 sections (3-5 sections, mỗi section 2-3 H3)
   - FAQ section (5 câu hỏi từ People Also Ask)
   - Conclusion + CTA
4. **Internal linking** gợi ý (3 URL liên quan)
5. **Featured snippet** opportunity: có/không, dạng nào (paragraph/list/table)
6. **AEO optimization**: format câu trả lời trực tiếp cho AI Search"""

        return self.chat(prompt, reset_history=True)

    # ─── AEO (Answer Engine Optimization) ───────────────────────────────────

    def optimize_for_ai_search(
        self,
        content: str,
        target_question: str,
    ) -> str:
        """
        Tối ưu content để được AI Search (ChatGPT, Perplexity, Claude) trích dẫn.
        """
        prompt = f"""Tối ưu đoạn content sau để AI Search (ChatGPT, Perplexity, Google AI) \
trích dẫn khi người dùng hỏi: "{target_question}"

**Content gốc:**
{content[:2000]}

Cung cấp:
1. **Phiên bản tối ưu AEO**: Viết lại dạng Q&A trực tiếp, câu trả lời trong 40-60 chữ đầu
2. **Structured data** gợi ý: FAQ Schema, HowTo Schema, v.v.
3. **E-E-A-T signals** cần thêm: Experience, Expertise, Authoritativeness, Trustworthiness
4. **Checklist AEO**: các yếu tố đã đạt / chưa đạt"""

        return self.chat(prompt, reset_history=True)

    # ─── SEO Audit ───────────────────────────────────────────────────────────

    def audit_content(self, content: str, target_keyword: str) -> str:
        """
        Audit content sẵn có theo checklist SEO.
        """
        prompt = f"""Audit SEO cho content sau, target keyword: "{target_keyword}"

**Content:**
{content[:3000]}

Đánh giá theo checklist:
1. **Keyword density** (mục tiêu: 1-2%)
2. **Keyword trong**: H1, H2, đoạn đầu, meta description
3. **Readability**: câu ngắn, đoạn ngắn, có heading rõ ràng
4. **Internal/External links**: đủ không
5. **Image alt text**: gợi ý
6. **Content length**: đủ chưa so với intent

**Kết quả**: Điểm SEO /100 + 5 điểm cần cải thiện ngay (priority order)"""

        return self.chat(prompt, reset_history=True)

    def generate_landing_page_seo(
        self,
        product: str,
        target_keyword: str,
        usp: str = "",
    ) -> str:
        """
        Tạo full SEO copy cho landing page sản phẩm.
        """
        prompt = f"""Viết SEO copy đầy đủ cho landing page:

**Sản phẩm/Dịch vụ:** {product}
**Target keyword chính:** {target_keyword}
**USP (lợi thế độc đáo):** {usp or "tự xác định"}

Cung cấp:
1. **Hero section**: H1 + subheadline + CTA button text
2. **Benefits section**: 3 lợi ích chính (có từ khoá tự nhiên)
3. **Social proof section**: template testimonial + số liệu
4. **FAQ section**: 5 câu hỏi + trả lời (chuẩn AEO)
5. **CTA section**: Headline + description + button
6. **Footer text**: Địa chỉ, schema NAP

Tất cả text phải: tự nhiên tiếng Việt, có từ khoá hữu cơ, CTA rõ ràng"""

        return self.chat(prompt, reset_history=True)
