# FuviAI Marketing Agent — Makefile
# Dùng: make <target>

.PHONY: help setup dev test lint docker-dev docker-prod frontend clean

## ── Hiển thị help ──────────────────────────────────────────────────────────

help:
	@echo "FuviAI Marketing Agent — Available commands:"
	@echo ""
	@echo "  setup        Tạo venv + cài dependencies"
	@echo "  dev          Chạy API backend (dev mode, port 8000)"
	@echo "  frontend     Chạy Next.js frontend (dev mode, port 3000)"
	@echo "  test         Chạy toàn bộ tests"
	@echo "  test-cov     Chạy tests + coverage report"
	@echo "  lint         Ruff lint + format check"
	@echo "  docker-dev   Docker Compose (postgres + redis + app)"
	@echo "  docker-prod  Docker Compose production (+ nginx)"
	@echo "  clean        Xoá __pycache__, .pytest_cache, .coverage"

## ── Setup ───────────────────────────────────────────────────────────────────

setup:
	python -m venv venv
	venv/Scripts/activate && pip install --upgrade pip && pip install -r requirements.txt
	cp .env.example .env
	@echo "\n✅ Done. Edit .env và thêm ANTHROPIC_API_KEY rồi chạy: make dev"

## ── Development ─────────────────────────────────────────────────────────────

dev:
	python run.py

frontend:
	cd frontend && npm install && npm run dev

## ── Testing ─────────────────────────────────────────────────────────────────

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=backend --cov-report=term-missing --cov-report=html

## ── Linting ─────────────────────────────────────────────────────────────────

lint:
	ruff check backend/ tests/
	ruff format --check backend/ tests/

lint-fix:
	ruff check --fix backend/ tests/
	ruff format backend/ tests/

## ── Docker ──────────────────────────────────────────────────────────────────

docker-dev:
	docker-compose up -d

docker-prod:
	docker-compose --profile production up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

docker-build:
	docker-compose build --no-cache

## ── Cleanup ─────────────────────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f .coverage
	rm -rf htmlcov/
	@echo "✅ Cleaned"
