# 🚀 FuviAI Marketing Agent — ROADMAP
> **marketing.fuviai.com** | VS Code + Claude Code | Full Custom Build 2026

---

## 🏆 TRẠNG THÁI TỔNG QUAN (cập nhật 05/03/2026)

| Phase | Nội dung | Status |
|-------|----------|--------|
| Phase 1 | Core Agent (12 agents, FastAPI, ChromaDB) | ✅ HOÀN THÀNH |
| Phase 2 | Automation (Campaign, Insight, Social, Zalo/FB tools) | ✅ HOÀN THÀNH |
| Phase 3 | Intelligence (Listening, Competitor, Celery scheduler) | ✅ HOÀN THÀNH |
| Phase 4 | Commerce (Livestream, AdBudget, Personalize, Compliance, Orchestrator) | ✅ HOÀN THÀNH |
| Phase 5 | Launch (Tests, Middleware, CI/CD, Frontend, Deploy) | ✅ HOÀN THÀNH |

### ✅ Đã deploy
- **Backend API** — Vercel (github.com/nguyenbinh89/marketing-agent-fuviai)
- **Frontend** — Next.js 14, 10 pages

### 🔄 Còn lại (Post-Launch)
- [x] `backend/tools/search_tool.py` — Web search cho research/listening agents
- [x] `backend/tools/tiktok_tool.py` — TikTok for Business API
- [x] `backend/tools/shopee_tool.py` — Shopee Open Platform API
- [ ] `backend/tools/google_ads_tool.py` — Google Ads API
- [ ] Monitoring — Sentry error tracking + uptime alert
- [ ] Onboard 3 beta users từ 500+ khách hàng FuviAI

---

## 📋 MỤC LỤC

- [⚡ Bước 0 — Setup môi trường](#-bước-0--setup-môi-trường)
- [📁 Cấu trúc thư mục](#-cấu-trúc-thư-mục)
- [🗓️ Phase 1 — Core Agent (Tuần 1–2)](#️-phase-1--core-agent-tuần-12)
- [🗓️ Phase 2 — Automation (Tuần 3–4)](#️-phase-2--automation-tuần-34)
- [🗓️ Phase 3 — Intelligence (Tuần 5–6)](#️-phase-3--intelligence-tuần-56)
- [🗓️ Phase 4 — Commerce (Tuần 7–8)](#️-phase-4--commerce-tuần-78)
- [🗓️ Phase 5 — Launch (Tuần 9–10)](#️-phase-5--launch-tuần-910)
- [💬 Claude Code Prompts](#-claude-code-prompts)
- [🔑 Biến môi trường](#-biến-môi-trường)
- [📦 Tech Stack](#-tech-stack)

---

## ⚡ Bước 0 — Setup môi trường

> Hoàn thành trong **30 phút** trước khi bắt đầu code

### 1. Cài VS Code Extensions

Mở VS Code → `Ctrl+Shift+X` → Tìm và cài:

| Extension | Mục đích |
|---|---|
| **Claude Code** (Anthropic) | AI coding assistant chính |
| **Python** (Microsoft) | Python language support |
| **Docker** (Microsoft) | Container management |
| **REST Client** | Test API endpoints |
| **GitLens** | Git history & blame |
| **Pylance** | Python type checking |

### 2. Lấy Claude API Key

1. Truy cập [console.anthropic.com](https://console.anthropic.com)
2. Đăng ký / đăng nhập tài khoản
3. Vào **API Keys** → **Create Key**
4. Copy key → lưu vào `.env` (xem bên dưới)

### 3. Tạo Project

```bash
# Tạo thư mục
mkdir marketing-agent-fuviai
cd marketing-agent-fuviai

# Khởi tạo git
git init

# Tạo môi trường Python
python -m venv venv

# Kích hoạt (Windows)
venv\Scripts\activate

# Kích hoạt (Mac/Linux)
source venv/bin/activate

# Cài dependencies
pip install anthropic langchain langchain-anthropic langgraph
pip install fastapi uvicorn chromadb psycopg2-binary redis
pip install python-dotenv requests playwright beautifulsoup4
pip install underthesea celery python-multipart

# Mở VS Code
code .
```

### 4. Tạo file `.env`

Tạo file `.env` ở thư mục gốc và điền vào:

```env
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
DATABASE_URL=postgresql://user:password@localhost:5432/fuviai_agent
REDIS_URL=redis://localhost:6379
ZALO_OA_ACCESS_TOKEN=
FACEBOOK_ACCESS_TOKEN=
TIKTOK_ACCESS_TOKEN=
```

### 5. Đăng nhập Claude Code

Mở Claude Code panel trong VS Code → Đăng nhập Anthropic account → **Bắt đầu!**

---

## 📁 Cấu trúc thư mục

```
marketing-agent-fuviai/
│
├── .claude/
│   └── CLAUDE.md                  # Context cho Claude Code — copy roadmap.md vào đây
│
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py          # Base class dùng chung cho tất cả agents
│   │   ├── content_agent.py       # M1  — Tạo content tiếng Việt
│   │   ├── research_agent.py      # M2  — Nghiên cứu thị trường VN
│   │   ├── campaign_agent.py      # M3  — Phân tích campaign
│   │   ├── seo_agent.py           # M4  — SEO + AEO Optimizer
│   │   ├── social_agent.py        # M5  — Social Media automation
│   │   ├── insight_agent.py       # M6  — Customer Insights
│   │   ├── listening_agent.py     # M7  — Social Listening & Trend
│   │   ├── livestream_agent.py    # M8  — Livestream AI Coach
│   │   ├── adbudget_agent.py      # M9  — Ad Budget Intelligence
│   │   ├── competitor_agent.py    # M10 — Competitor Intelligence
│   │   ├── personalize_agent.py   # M11 — Hyper-Personalization
│   │   ├── compliance_agent.py    # M12 — Compliance & Data Privacy
│   │   └── orchestrator.py        # LangGraph multi-agent workflow
│   │
│   ├── tools/
│   │   ├── zalo_tool.py           # Zalo OA API integration
│   │   ├── facebook_tool.py       # Facebook Graph API
│   │   ├── tiktok_tool.py         # TikTok for Business API
│   │   ├── shopee_tool.py         # Shopee Open Platform API
│   │   ├── google_ads_tool.py     # Google Ads API
│   │   ├── search_tool.py         # Web search tool
│   │   └── scraper_tool.py        # Playwright web scraper
│   │
│   ├── memory/
│   │   ├── vector_store.py        # ChromaDB / Qdrant
│   │   └── conversation.py        # Conversation history
│   │
│   ├── api/
│   │   ├── main.py                # FastAPI app entry point
│   │   └── routes/
│   │       ├── agents.py          # /api/agents/* endpoints
│   │       ├── content.py         # /api/content/* endpoints
│   │       └── analytics.py       # /api/analytics/* endpoints
│   │
│   └── config/
│       ├── settings.py            # Cấu hình toàn hệ thống
│       └── prompts_vn.py          # System prompts tiếng Việt
│
├── frontend/                      # Next.js Dashboard (Phase 5)
│
├── data/
│   ├── knowledge_base/            # Dữ liệu marketing VN để RAG
│   └── samples/                   # Sample content cho training
│
├── tests/
│   ├── test_content_agent.py
│   └── test_api.py
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── roadmap.md                     # File này
```

---

## 🗓️ Phase 1 — Core Agent (Tuần 1–2)

**Mục tiêu:** Có agent viết được content marketing tiếng Việt chuyên nghiệp

### ✅ Checklist Tuần 1

- [ ] Setup môi trường xong (Bước 0)
- [ ] Tạo `base_agent.py` — kết nối Claude API thành công
- [ ] Tạo `config/prompts_vn.py` — system prompt tiếng Việt cho FuviAI
- [ ] Test gọi Claude API với prompt tiếng Việt đơn giản
- [ ] Tạo `content_agent.py` — viết caption Facebook, TikTok script, email
- [ ] Tạo `memory/conversation.py` — agent nhớ context hội thoại
- [ ] Test với 10 use case content thực tế của FuviAI

### ✅ Checklist Tuần 2

- [ ] Tạo `research_agent.py` — crawl CafeF, VnExpress, Báo Đầu tư
- [ ] Tạo `memory/vector_store.py` — ChromaDB lưu knowledge base ngành
- [ ] Tạo `seo_agent.py` — từ khóa + meta tag + AEO cho AI Search
- [ ] Tạo `api/main.py` — FastAPI với endpoint `/chat` đầu tiên
- [ ] Test toàn bộ Phase 1 với REST Client

### 🧪 Phase 1 hoàn thành khi

```
✔ Agent viết được caption Facebook 300 chữ cho sản phẩm bất kỳ
✔ Agent gợi ý 10 từ khóa SEO cho landing page FuviAI
✔ Agent tóm tắt tin tức marketing VN trong 24h qua
✔ API /chat hoạt động, trả về JSON trong < 3 giây
```

---

## 🗓️ Phase 2 — Automation (Tuần 3–4)

**Mục tiêu:** Tự động hoá campaign analysis và social media posting

### ✅ Checklist Tuần 3

- [ ] Tạo `campaign_agent.py` — phân tích hiệu suất campaign, đề xuất tối ưu
- [ ] Tạo `insight_agent.py` — sentiment analysis theo phương ngữ VN
- [ ] Tích hợp underthesea cho NLP tiếng Việt (Bắc / Trung / Nam)
- [ ] Viết unit test cho M3, M6

### ✅ Checklist Tuần 4

- [ ] Tạo `social_agent.py` — scheduler đăng bài Zalo OA, Facebook, TikTok
- [ ] Tạo `tools/zalo_tool.py` — Zalo OA API wrapper
- [ ] Tạo `tools/facebook_tool.py` — Facebook Graph API wrapper
- [ ] Setup Celery + Redis cho background jobs
- [ ] Docker Compose với PostgreSQL + Redis + app

### 🧪 Phase 2 hoàn thành khi

```
✔ Agent phân tích file CSV campaign và đưa ra 5 đề xuất cải thiện
✔ Bài viết được tự động đăng lên Zalo OA theo lịch
✔ Sentiment "tệ quá" / "xuất sắc" / "ổn ổn" được phân loại đúng
✔ Docker Compose chạy toàn bộ stack thành công
```

---

## 🗓️ Phase 3 — Intelligence (Tuần 5–6)

**Mục tiêu:** Social Listening real-time + Competitor monitoring tự động

### ✅ Checklist Tuần 5 — Social Listening (M7)

- [ ] Tạo `listening_agent.py` với Playwright crawl Facebook/TikTok public
- [ ] Phát hiện trending topics trong 24h trước đối thủ
- [ ] Tự động tạo content draft ăn theo trend vừa phát hiện
- [ ] Alert webhook Zalo OA khi phát hiện khủng hoảng truyền thông
- [ ] Celery scheduler chạy mỗi 30 phút

### ✅ Checklist Tuần 6 — Competitor Intelligence (M10)

- [ ] Tạo `competitor_agent.py` — crawl website + fanpage đối thủ hàng ngày
- [ ] Diff detector: phát hiện thay đổi giá, promotion, nội dung mới
- [ ] So sánh engagement rate FuviAI vs đối thủ theo tuần
- [ ] Auto-suggest counter-strategy khi đối thủ launch campaign lớn
- [ ] Endpoint `/api/analytics/competitors`

### 🧪 Phase 3 hoàn thành khi

```
✔ Hệ thống phát hiện trend đang hot trên TikTok VN trong 24h
✔ Alert Zalo khi đối thủ giảm giá > 20%
✔ Báo cáo weekly FuviAI vs top 3 đối thủ được tạo tự động
✔ Agent đề xuất counter-campaign cụ thể trong < 30 giây
```

---

## 🗓️ Phase 4 — Commerce (Tuần 7–8)

**Mục tiêu:** Livestream Coach + Ad Budget AI + Hyper-Personalization

### ✅ Checklist Tuần 7

- [ ] Tạo `livestream_agent.py` — real-time gợi ý script theo viewer feedback
- [ ] Auto-reply comment theo tone brand FuviAI
- [ ] Tối ưu voucher / flash deal timing theo momentum livestream
- [ ] Tạo `adbudget_agent.py` — dự báo ngân sách theo mùa vụ VN (Tết, 11/11...)

### ✅ Checklist Tuần 8

- [ ] Tạo `personalize_agent.py` — phân khúc khách theo CLV, hành vi
- [ ] Dynamic content: email/Zalo cá nhân hoá từng segment
- [ ] Trigger automation: abandoned cart, re-engagement, upsell
- [ ] Tạo `compliance_agent.py` — kiểm tra content theo Nghị định 13/2023
- [ ] Tích hợp tất cả 12 agents vào `orchestrator.py` với LangGraph

### 🧪 Phase 4 hoàn thành khi

```
✔ Livestream agent gợi ý script trong < 2 giây khi viewer drop 20%
✔ Dự báo ngân sách Tết 2027 với sai số ± 15%
✔ Email cá nhân hoá đạt open rate > 35% trong A/B test
✔ Content vi phạm NĐ 13/2023 bị flag tự động trước khi đăng
```

---

## 🗓️ Phase 5 — Launch (Tuần 9–10)

**Mục tiêu:** MVP hoàn chỉnh, deploy lên marketing.fuviai.com

### ✅ Checklist Tuần 9

- [ ] Viết integration tests cho toàn bộ 12 modules
- [ ] Performance test: API chịu 100 concurrent requests
- [ ] Security: API key rotation, rate limiting, input sanitization
- [ ] Next.js dashboard UI (chat + analytics + content scheduler)
- [ ] CI/CD pipeline với GitHub Actions

### ✅ Checklist Tuần 10

- [ ] Build Docker images cho môi trường production
- [ ] Deploy VPS (Singapore hoặc datacenter Việt Nam)
- [ ] Nginx reverse proxy + SSL cho marketing.fuviai.com
- [ ] Monitoring: logs + uptime alert
- [ ] Swagger UI documentation
- [ ] Onboard 3 beta users từ 500+ khách hàng FuviAI hiện có

### 🧪 Launch hoàn thành khi

```
✔ Uptime > 99.5% trong 72h test liên tục
✔ Response time API < 2 giây (p95)
✔ Tất cả 12 module hoạt động end-to-end
✔ Dashboard load < 3 giây trên mobile 4G Việt Nam
✔ 3 beta users confirm ROI dương trong tuần đầu
```

---

## 💬 Claude Code Prompts

> Copy từng prompt vào Claude Code panel **theo đúng thứ tự**

### Prompt 1 — Khởi tạo toàn bộ project

```
Tôi đang xây dựng AI Agent Marketing cho website marketing.fuviai.com
của Future Vision AI (FuviAI) — Top 3 AI Automation Việt Nam,
đã có 500+ doanh nghiệp khách hàng, ROI trung bình 4.2×.

Hãy tạo cho tôi:
1. Toàn bộ cấu trúc thư mục theo file roadmap.md trong project
2. requirements.txt đầy đủ
3. backend/config/settings.py với Pydantic Settings
4. backend/config/prompts_vn.py — system prompt chuyên gia marketing VN,
   hiểu brand FuviAI, viết content cho Facebook/TikTok/Zalo/Email
5. backend/agents/base_agent.py — base class kết nối Claude API
6. .env.example với tất cả biến môi trường
7. docker-compose.yml với PostgreSQL + Redis + FastAPI app

Tech: Python 3.12 + FastAPI + LangGraph + ChromaDB + PostgreSQL + Redis
```

### Prompt 2 — Content Agent (M1)

```
Tạo backend/agents/content_agent.py cho FuviAI Marketing Agent.

Agent phải:
- Viết caption Facebook (300–500 chữ), tone: chuyên nghiệp / thân thiện / Gen Z
- Viết TikTok script (60–90 giây) với hook mạnh trong 3 giây đầu
- Viết Zalo broadcast message ngắn gọn có CTA rõ ràng
- Viết email marketing theo cấu trúc AIDA
- Dùng ngôn ngữ tự nhiên, hiểu văn hoá tiêu dùng Việt Nam
- Nhớ context để cải thiện output qua nhiều lần chỉnh sửa

Dùng LangChain ConversationBufferMemory + Claude claude-sonnet-4.
Thêm FastAPI endpoint POST /api/content/generate để test.
```

### Prompt 3 — Research Agent (M2)

```
Tạo backend/agents/research_agent.py để nghiên cứu thị trường VN.

Agent phải:
- Crawl và tóm tắt tin tức từ CafeF, VnExpress Kinh doanh,
  Báo Đầu tư, Nielsen Vietnam trong 24h qua
- Phân tích xu hướng ngành: FMCG, F&B, bất động sản, công nghệ VN
- Tạo báo cáo insight 1 trang từ nhiều nguồn
- Lưu kết quả vào ChromaDB để dùng cho RAG

Dùng requests + BeautifulSoup4 để crawl,
underthesea để tokenize tiếng Việt,
ChromaDB để store embeddings.
```

### Prompt 4 — Social Listening Agent (M7)

```
Tạo backend/agents/listening_agent.py cho Social Listening real-time.

Agent phải:
- Crawl public posts Facebook pages và TikTok theo keyword/hashtag
- Phân tích sentiment tiếng Việt: tích cực / tiêu cực / trung tính
  (xử lý đúng phương ngữ Nam: "thiệt ra", "ngu quá", "đỉnh của chóp")
- Phát hiện trending topics đang tăng nhanh trong 6h gần nhất
- Khi có trend → tự động gọi content_agent tạo draft content ăn theo
- Gửi webhook alert Zalo OA khi phát hiện khủng hoảng truyền thông

Dùng Playwright cho crawling, underthesea cho NLP,
Celery task chạy mỗi 30 phút, lưu kết quả PostgreSQL.
```

### Prompt 5 — Competitor Intelligence (M10)

```
Tạo backend/agents/competitor_agent.py để monitor đối thủ tự động.

Agent phải:
- Nhận list đối thủ từ config (URL + Facebook page ID)
- Crawl hàng ngày: giá, promotion, nội dung mới, ads đang chạy
- So sánh engagement rate FuviAI vs đối thủ theo tuần
- Phát hiện thay đổi đột ngột: giảm giá > 15%, ra sản phẩm mới
- Khi đối thủ launch big campaign → generate counter-strategy < 30s
- Endpoint GET /api/analytics/competitors trả về dashboard JSON

Dùng Playwright + Facebook Ad Library API + diff algorithm.
```

### Prompt 6 — Orchestrator LangGraph

```
Tạo backend/agents/orchestrator.py — LangGraph multi-agent workflow.

Workflow khi nhận task phức tạp (VD: "Lên kế hoạch campaign Tết 2027"):
1. research_agent → lấy market data ngành F&B dịp Tết
2. competitor_agent → phân tích đối thủ đang làm gì
3. content_agent → tạo content plan 30 ngày
4. seo_agent → keyword strategy cho chiến dịch
5. Tổng hợp → báo cáo hoàn chỉnh

Yêu cầu:
- LangGraph StateGraph với nodes + edges + state schema rõ ràng
- Nếu 1 agent fail → retry 2 lần rồi skip và ghi log
- Streaming response để user thấy progress real-time
- Timeout 60s mỗi agent node
```

---

## 🔑 Biến môi trường

Tạo file `.env.example` (commit lên git) và `.env` (KHÔNG commit):

```env
# ═══════════════════════════════
# CORE — BẮT BUỘC
# ═══════════════════════════════
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# ═══════════════════════════════
# DATABASE
# ═══════════════════════════════
DATABASE_URL=postgresql://fuviai:password@localhost:5432/marketing_agent
REDIS_URL=redis://localhost:6379/0

# ═══════════════════════════════
# VECTOR DB
# ═══════════════════════════════
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION=fuviai_knowledge

# ═══════════════════════════════
# SOCIAL PLATFORMS — Thêm dần theo phase
# ═══════════════════════════════
ZALO_OA_ACCESS_TOKEN=
ZALO_OA_SECRET=
FACEBOOK_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=
TIKTOK_ACCESS_TOKEN=
TIKTOK_APP_ID=
SHOPEE_PARTNER_ID=
SHOPEE_PARTNER_KEY=
GOOGLE_ADS_DEVELOPER_TOKEN=

# ═══════════════════════════════
# APP
# ═══════════════════════════════
APP_ENV=development
APP_PORT=8000
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,https://marketing.fuviai.com
```

---

## 📦 Tech Stack

| Layer | Công nghệ | Ghi chú |
|---|---|---|
| **LLM** | Claude Sonnet 4 (Anthropic) | Tốt nhất tiếng Việt |
| **Agent Framework** | LangChain + LangGraph | Multi-agent workflow |
| **Backend** | Python 3.12 + FastAPI | Async, nhanh |
| **Task Queue** | Celery + Redis | Background jobs |
| **Vector DB** | ChromaDB → Qdrant | RAG knowledge base |
| **Database** | PostgreSQL 16 | Persistent data |
| **NLP tiếng Việt** | underthesea | Sentiment, tokenize |
| **Crawling** | Playwright + BeautifulSoup4 | Web scraping |
| **Frontend** | Next.js 14 + shadcn/ui | Dashboard Phase 5 |
| **IDE** | VS Code + Claude Code | Dev tool chính |
| **Container** | Docker + Docker Compose | Mọi environment |
| **Deploy** | Nginx + VPS SG/VN | Latency thấp |

---

## 🏁 BẮT ĐẦU NGAY — 5 bước

```
Bước 1 (5 phút)   → Lấy API key tại console.anthropic.com
Bước 2 (10 phút)  → Cài VS Code + Claude Code extension + đăng nhập
Bước 3 (15 phút)  → Chạy lệnh setup ở Bước 0 phía trên
Bước 4 (2 phút)   → Copy roadmap.md này vào .claude/CLAUDE.md
Bước 5 (ngồi xem) → Mở Claude Code → Paste Prompt 1 → 🎉
```

> 💡 **Mẹo quan trọng:** Lưu file `roadmap.md` này vào `.claude/CLAUDE.md`
> để Claude Code **luôn có context đầy đủ** về project FuviAI khi bạn hỏi bất kỳ điều gì.
> Claude Code sẽ đọc file này mỗi khi bắt đầu session mới.

---

*FuviAI Marketing Agent v2.0 — marketing.fuviai.com*  
*Tài liệu nội bộ | 2026*
