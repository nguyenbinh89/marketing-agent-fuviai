# FuviAI Marketing Agent — Production Dockerfile
# Multi-stage build: builder + runtime

# ═══════════════════════════════════════════
# Stage 1: Builder
# ═══════════════════════════════════════════
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# ═══════════════════════════════════════════
# Stage 2: Runtime
# ═══════════════════════════════════════════
FROM python:3.12-slim AS runtime

ARG BUILD_DATE
ARG GIT_SHA
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${GIT_SHA}"
LABEL org.opencontainers.image.title="FuviAI Marketing Agent"
LABEL org.opencontainers.image.vendor="FuviAI"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 fuviai

WORKDIR /app

COPY --from=builder /root/.local /home/fuviai/.local
COPY --chown=fuviai:fuviai backend/ ./backend/
COPY --chown=fuviai:fuviai run.py pytest.ini ./

RUN mkdir -p data/chroma && chown -R fuviai:fuviai data/

USER fuviai

ENV PATH="/home/fuviai/.local/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
