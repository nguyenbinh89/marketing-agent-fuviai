# FuviAI Marketing Agent

AI Marketing Agent cho [marketing.fuviai.com](https://marketing.fuviai.com) — tự động hóa toàn bộ quy trình marketing cho SME Việt Nam.

**FuviAI** (Future Vision AI) — Top 3 AI Automation Việt Nam, phục vụ 500+ doanh nghiệp, ROI trung bình 4.2x.

---

## Tính năng

12 AI agents chuyên biệt, mỗi agent xử lý một mảng marketing cụ thể:

| Agent | Chức năng |
|-------|-----------|
| M1 ContentAgent | Tạo content Facebook, TikTok, Zalo, Email, Shopee |
| M2 ResearchAgent | Nghiên cứu thị trường, tìm kiếm web, báo cáo ngành |
| M3 CampaignAgent | Phân tích campaign CSV, tối ưu ngân sách, A/B test |
| M4 SEOAgent | Keyword research, meta tags, content outline, AEO |
| M5 SocialAgent | Lên lịch post, reply comment, repurpose content |
| M6 InsightAgent | Sentiment analysis tiếng Việt, RFM, VOC, crisis detect |
| M7 ListeningAgent | Social listening 24/7, trend detection, crisis alert |
| M8 LivestreamAgent | Kịch bản livestream, flash deal, batch reply |
| M9 AdBudgetAgent | Lập kế hoạch ngân sách quý/năm, ROAS forecast |
| M10 CompetitorAgent | Theo dõi đối thủ, diff detection, counter-strategy |
| M11 PersonalizeAgent | CLV segmentation, email/Zalo cá nhân hóa, trigger flows |
| M12 ComplianceAgent | Kiểm duyệt nội dung, auto-fix vi phạm chính sách |

**Orchestrator**: LangGraph StateGraph 7 nodes (research → competitor → seo → content → budget → compliance → report), hỗ trợ streaming.

---

## Stack

- **Backend**: Python 3.12, FastAPI, LangGraph
- **AI**: Anthropic Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- **Vector DB**: ChromaDB (RAG knowledge base)
- **Database**: PostgreSQL + Redis
- **Search**: DuckDuckGo (free) + Google Custom Search (optional)
- **Task Queue**: Celery + Celery Beat
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Infrastructure**: Docker, Nginx

---

## Cài đặt nhanh

### Yêu cầu

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (cho production)

### Development

```bash
# 1. Clone & setup Python env
git clone https://github.com/fuviai/marketing-agent-fuviai
cd marketing-agent-fuviai
python -m venv venv
source venv/bin/activate      # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Cấu hình môi trường
cp .env.example .env
# Mở .env, điền ANTHROPIC_API_KEY (bắt buộc)

# 4. Chạy database (Docker)
docker-compose up -d postgres redis

# 5. Khởi động backend
python run.py                          # http://localhost:8000

# 6. Khởi động frontend (terminal mới)
cd frontend
npm install
npm run dev                            # http://localhost:3000
```

### Production (Docker)

```bash
cp .env.example .env    # điền đầy đủ các biến môi trường

# Chạy full stack
docker-compose up -d

# Thêm Nginx HTTPS
docker-compose --profile production up -d
```

---

## Biến môi trường

Bắt buộc:

```env
ANTHROPIC_API_KEY=sk-ant-...
```

Tuỳ chọn (mở rộng tính năng):

```env
# Google Custom Search (tìm kiếm chính xác hơn DuckDuckGo)
GOOGLE_CSE_API_KEY=...
GOOGLE_CSE_ID=...

# Zalo OA
ZALO_OA_ACCESS_TOKEN=...
ZALO_OA_SECRET=...

# Facebook
FACEBOOK_ACCESS_TOKEN=...
FACEBOOK_PAGE_ID=...

# Database (mặc định dùng Docker)
DATABASE_URL=postgresql://fuviai:password@localhost:5432/marketing_agent
REDIS_URL=redis://localhost:6379/0
```

Xem `.env.example` để biết đầy đủ các biến.

---

## API

Sau khi chạy backend, truy cập:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Các nhóm endpoint chính:

```
POST /api/agents/chat                          # Chat với AI agent
POST /api/content/generate/{platform}          # Tạo content

POST /api/research/search                      # Tìm kiếm thị trường (web search + AI)
POST /api/research/market-report               # Báo cáo thị trường hàng ngày
POST /api/research/industry                    # Nghiên cứu ngành
POST /api/research/seo/*                       # SEO tools

POST /api/automation/campaign/*                # Phân tích campaign
POST /api/automation/insight/*                 # Sentiment & insight
POST /api/automation/social/*                  # Social scheduling

GET  /api/analytics/competitors                # Dashboard đối thủ
GET  /api/analytics/competitors/{name}/news    # Tin tức mới về đối thủ
POST /api/analytics/listening/scan             # Quét trend theo ngành

POST /api/commerce/orchestrate/plan            # Campaign plan đầy đủ (streaming)
POST /api/commerce/compliance/check            # Kiểm duyệt content
POST /api/commerce/personalize/segment         # Phân khúc khách hàng
```

Xem `test.http` để có sẵn các request mẫu cho tất cả endpoints.

---

## Cấu trúc thư mục

```
backend/
  agents/          # 12 AI agents (M1-M12) + orchestrator
  api/
    main.py        # FastAPI app entry point
    middleware.py  # Rate limit, logging, API key, XSS sanitize
    routes/        # agents, content, research, automation, analytics, commerce
  config/
    settings.py    # Pydantic Settings từ .env
    prompts_vn.py  # System prompts tiếng Việt
  memory/
    vector_store.py    # ChromaDB wrapper
    conversation.py    # Conversation history
  tasks/
    celery_app.py          # Celery + Beat schedule
    listening_tasks.py     # Scan trends mỗi 30 phút
    competitor_tasks.py    # Scan đối thủ mỗi ngày
  tools/
    search_tool.py     # DuckDuckGo + Google Custom Search
    scraper_tool.py    # Web scraper (requests + BeautifulSoup)
    zalo_tool.py       # Zalo OA API
    facebook_tool.py   # Facebook Graph API
frontend/
  src/app/           # 10 trang Next.js (dashboard, chat, content, campaigns...)
  src/lib/api.ts     # Typed API client
tests/               # pytest unit + integration tests
nginx/               # Nginx config cho production
```

---

## Chạy tests

```bash
pytest tests/ -v

# Với coverage report
pytest tests/ --cov=backend --cov-report=term-missing
```

---

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):

1. **Lint** — ruff
2. **Test** — pytest với coverage ≥ 60%
3. **Build** — Docker multi-stage build
4. **Deploy** — SSH deploy lên server production
