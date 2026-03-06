"""
FuviAI Marketing Agent — Security Middleware
Rate limiting, API key auth, input sanitization, request logging
"""

from __future__ import annotations

import re
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

try:
    from backend.monitoring import sentry_capture_exception
except ImportError:
    def sentry_capture_exception(e: Exception) -> None:
        pass


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """
    In-memory rate limiter theo IP (sliding window).
    Production: thay bằng Redis-backed rate limiter.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Kiểm tra key (IP hoặc API key) có được phép request không.

        Returns:
            (allowed: bool, remaining: int)
        """
        now = time.time()
        window_start = now - self.window

        # Xóa requests cũ ngoài window
        self._requests[key] = [t for t in self._requests[key] if t > window_start]

        current_count = len(self._requests[key])
        if current_count >= self.max_requests:
            return False, 0

        self._requests[key].append(now)
        return True, self.max_requests - current_count - 1

    def reset(self, key: str) -> None:
        self._requests.pop(key, None)


# Global rate limiters
_api_limiter = RateLimiter(max_requests=60, window_seconds=60)      # 60 req/min per IP
_heavy_limiter = RateLimiter(max_requests=10, window_seconds=60)    # 10 req/min cho heavy endpoints
_auth_limiter = RateLimiter(max_requests=5, window_seconds=60)      # 5 req/min cho auth endpoints

# Heavy endpoints (gọi nhiều Claude tokens)
HEAVY_ENDPOINTS = {
    "/api/commerce/orchestrate/campaign-plan",
    "/api/commerce/orchestrate/campaign-plan/stream",
    "/api/research/market-report",
    "/api/automation/campaign/analyze",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware — áp dụng cho tất cả API routes."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        client_ip = _get_client_ip(request)
        path = request.url.path

        # Heavy endpoints: stricter limit
        if path in HEAVY_ENDPOINTS:
            allowed, remaining = _heavy_limiter.is_allowed(f"heavy:{client_ip}")
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "message": "Endpoint này giới hạn 10 requests/phút. Vui lòng thử lại sau.",
                        "retry_after": 60,
                    },
                    headers={"Retry-After": "60"},
                )

        # General rate limit
        allowed, remaining = _api_limiter.is_allowed(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Quá nhiều requests. Giới hạn 60 requests/phút.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


# ─── Request Logging ──────────────────────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log tất cả API requests với timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/") and request.url.path != "/health":
            return await call_next(request)

        start = time.time()
        client_ip = _get_client_ip(request)

        try:
            response = await call_next(request)
            elapsed_ms = round((time.time() - start) * 1000)

            log_fn = logger.warning if response.status_code >= 400 else logger.info
            log_fn(
                f"{request.method} {request.url.path} "
                f"| status={response.status_code} | {elapsed_ms}ms | ip={client_ip}"
            )
            response.headers["X-Response-Time"] = f"{elapsed_ms}ms"
            return response

        except Exception as e:
            elapsed_ms = round((time.time() - start) * 1000)
            logger.error(
                f"{request.method} {request.url.path} "
                f"| EXCEPTION | {elapsed_ms}ms | ip={client_ip} | error={e}"
            )
            sentry_capture_exception(e)
            raise


# ─── Input Sanitizer ─────────────────────────────────────────────────────────

# Patterns nguy hiểm cần sanitize
_SCRIPT_PATTERN = re.compile(r"<script[\s\S]*?>[\s\S]*?</script>", re.IGNORECASE)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_SQL_INJECTION_PATTERN = re.compile(
    r"\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b",
    re.IGNORECASE
)
_PROMPT_INJECTION_PATTERN = re.compile(
    r"(ignore\s+previous\s+instructions|forget\s+your\s+instructions|"
    r"you\s+are\s+now|act\s+as\s+a\s+different|DAN\s+mode|jailbreak)",
    re.IGNORECASE
)


def sanitize_string(value: str, max_length: int = 10000) -> str:
    """
    Sanitize string input:
    - Xóa script tags (XSS)
    - Truncate nếu quá dài
    - Flag prompt injection
    """
    if not isinstance(value, str):
        return value

    # Truncate
    if len(value) > max_length:
        value = value[:max_length]
        logger.warning(f"Input truncated to {max_length} chars")

    # Xóa script tags
    value = _SCRIPT_PATTERN.sub("", value)
    value = _HTML_TAG_PATTERN.sub("", value)

    # Log cảnh báo nếu phát hiện injection
    if _SQL_INJECTION_PATTERN.search(value):
        logger.warning(f"Potential SQL injection in input: {value[:100]}")

    if _PROMPT_INJECTION_PATTERN.search(value):
        logger.warning(f"Potential prompt injection in input: {value[:100]}")

    return value.strip()


def sanitize_dict(data: dict, max_depth: int = 5) -> dict:
    """Đệ quy sanitize tất cả string values trong dict."""
    if max_depth <= 0:
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_string(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            result[key] = [
                sanitize_string(v) if isinstance(v, str)
                else sanitize_dict(v, max_depth - 1) if isinstance(v, dict)
                else v
                for v in value
            ]
        else:
            result[key] = value
    return result


# ─── API Key Auth (Optional) ─────────────────────────────────────────────────

class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Optional API key authentication.
    Enable bằng cách set REQUIRE_API_KEY=true trong .env.
    """

    def __init__(self, app, valid_keys: set[str], enabled: bool = False):
        super().__init__(app)
        self._valid_keys = valid_keys
        self._enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._enabled:
            return await call_next(request)

        # Cho phép health check và docs không cần auth
        excluded = {"/health", "/docs", "/redoc", "/openapi.json"}
        if request.url.path in excluded:
            return await call_next(request)

        api_key = (
            request.headers.get("X-API-Key")
            or request.headers.get("Authorization", "").removeprefix("Bearer ")
        )

        if not api_key or api_key not in self._valid_keys:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Unauthorized",
                    "message": "API key không hợp lệ. Thêm header: X-API-Key: <your-key>",
                },
            )

        return await call_next(request)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_client_ip(request: Request) -> str:
    """Lấy IP thực của client (xử lý proxy/load balancer)."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"
