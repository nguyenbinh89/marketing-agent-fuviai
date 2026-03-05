# FuviAI Marketing Agent — Claude Code Context

> AI Marketing Agent cho marketing.fuviai.com | Python 3.12 + FastAPI + LangGraph

## Project Overview

- **FuviAI** (Future Vision AI) — Top 3 AI Automation Việt Nam, 500+ doanh nghiệp, ROI 4.2x
- **Stack:** Python 3.12, FastAPI, Anthropic Claude Sonnet 4, LangGraph, ChromaDB, PostgreSQL, Redis
- **Target:** SME Việt Nam — FMCG, F&B, bất động sản, thương mại điện tử

## Cấu trúc thư mục

```
backend/
  agents/          # 12 AI agents (M1-M12)
    base_agent.py  # Base class — Anthropic API connection
    content_agent.py  # M1 — Facebook/TikTok/Zalo/Email content
    [Phase 2+]     # research, campaign, seo, social, insight, listening,
                   # livestream, adbudget, competitor, personalize, compliance
    orchestrator.py  # LangGraph multi-agent workflow
  tools/           # Platform API wrappers (Zalo, Facebook, TikTok, Shopee...)
  memory/          # ChromaDB vector store + conversation history
  api/             # FastAPI routes
    main.py        # App entry point
    routes/        # /agents, /content, /analytics
  config/
    settings.py    # Pydantic Settings từ .env
    prompts_vn.py  # System prompts tiếng Việt
data/              # Knowledge base + ChromaDB
tests/             # pytest
```

## Phase Status

- **Phase 1 (Tuần 1-2):** IN PROGRESS
  - [x] base_agent.py
  - [x] content_agent.py (M1)
  - [x] config/settings.py + prompts_vn.py
  - [x] FastAPI /api/agents/chat + /api/content/generate/*
  - [ ] research_agent.py (M2)
  - [ ] memory/vector_store.py (ChromaDB)
  - [ ] seo_agent.py (M4)
- **Phase 2-5:** Planned

## Key Commands

```bash
# Activate venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Run API
uvicorn backend.api.main:app --reload --port 8000

# Run tests
pytest tests/ -v

# Docker
docker-compose up -d postgres redis
```

## Coding conventions

- Python 3.12, type hints everywhere
- Loguru for logging (not print/logging)
- Pydantic v2 for data models
- All prompts in Vietnamese (prompts_vn.py)
- Async FastAPI endpoints
- BaseAgent as parent class for all agents
