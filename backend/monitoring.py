"""
FuviAI Marketing Agent — Monitoring
Sentry error tracking + performance monitoring integration
Docs: https://docs.sentry.io/platforms/python/integrations/fastapi/

Tắt Sentry: để SENTRY_DSN trống trong .env
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from backend.config.settings import Settings


def init_sentry(settings: "Settings") -> None:
    """
    Khởi tạo Sentry SDK khi app start.
    Tự động tắt nếu SENTRY_DSN trống (dev mode).

    Tích hợp:
    - FastAPIIntegration: capture HTTP request context
    - LoguruIntegration: forward ERROR+ logs lên Sentry
    - SqlalchemyIntegration: track DB queries (performance)
    """
    if not settings.sentry_dsn:
        logger.info("Sentry disabled (SENTRY_DSN not set)")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        import logging

        sentry_logging = LoggingIntegration(
            level=logging.WARNING,       # Capture WARNING trở lên làm breadcrumbs
            event_level=logging.ERROR,   # Gửi ERROR trở lên thành Sentry events
        )

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            release="fuviai-marketing-agent@1.0.0",
            traces_sample_rate=settings.sentry_traces_sample_rate,
            profiles_sample_rate=0.1,
            integrations=[
                StarletteIntegration(transaction_style="url"),
                FastApiIntegration(transaction_style="url"),
                sentry_logging,
            ],
            # Không gửi PII (email, IP)
            send_default_pii=False,
            # Ignore các errors không cần track
            ignore_errors=[KeyboardInterrupt],
        )

        # Tag chung cho mọi event
        sentry_sdk.set_tag("service", "fuviai-marketing-agent")
        sentry_sdk.set_tag("agents", "12")

        logger.info(
            f"Sentry initialized | env={settings.app_env} "
            f"| traces={settings.sentry_traces_sample_rate}"
        )

    except ImportError:
        logger.warning("sentry-sdk không được cài. Chạy: pip install sentry-sdk[fastapi]")
    except Exception as e:
        logger.error(f"Sentry init failed: {e}")


def sentry_capture_exception(exc: Exception) -> None:
    """
    Capture exception thủ công lên Sentry.
    Dùng trong middleware và các background tasks.
    Safe to call khi Sentry chưa được init.
    """
    try:
        import sentry_sdk
        sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def sentry_capture_message(message: str, level: str = "warning") -> None:
    """
    Gửi message/alert lên Sentry (không phải exception).
    Dùng để alert các sự kiện quan trọng (crisis detected, budget limit...).

    Args:
        level: "debug" | "info" | "warning" | "error" | "fatal"
    """
    try:
        import sentry_sdk
        sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass


def sentry_set_user(user_id: str, email: str = "", username: str = "") -> None:
    """
    Gán user context cho Sentry events trong request hiện tại.
    Gọi sau khi xác thực user.
    """
    try:
        import sentry_sdk
        sentry_sdk.set_user({
            "id": user_id,
            **({"email": email} if email else {}),
            **({"username": username} if username else {}),
        })
    except Exception:
        pass
