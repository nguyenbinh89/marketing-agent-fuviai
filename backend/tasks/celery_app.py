"""
FuviAI Marketing Agent — Celery Application
Background tasks: social listening, competitor scan, scheduled posts
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab
from loguru import logger

from backend.config.settings import get_settings

settings = get_settings()

# ─── Celery App ──────────────────────────────────────────────────────────────

app = Celery(
    "fuviai_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "backend.tasks.listening_tasks",
        "backend.tasks.competitor_tasks",
        "backend.tasks.email_tasks",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ─── Beat Schedule ────────────────────────────────────────────────────────────

app.conf.beat_schedule = {
    # Social Listening: mỗi 30 phút từ 7am-11pm
    "social-listening-30min": {
        "task": "backend.tasks.listening_tasks.run_social_listening",
        "schedule": crontab(minute="*/30", hour="7-23"),
        "kwargs": {"industry": "marketing"},
    },
    # Competitor scan: 1 lần/ngày lúc 8am
    "competitor-daily-scan": {
        "task": "backend.tasks.competitor_tasks.run_daily_competitor_scan",
        "schedule": crontab(hour=8, minute=0),
    },
    # Process scheduled posts: mỗi 5 phút
    "process-scheduled-posts": {
        "task": "backend.tasks.listening_tasks.process_scheduled_posts",
        "schedule": crontab(minute="*/5"),
    },
    # Birthday emails: 9am mỗi ngày — tự query DB
    "birthday-emails-daily": {
        "task": "backend.tasks.email_tasks.send_birthday_emails",
        "schedule": crontab(hour=9, minute=0),
    },
    # Win-back campaign: mỗi thứ Hai 10am — tự query DB
    "winback-emails-weekly": {
        "task": "backend.tasks.email_tasks.send_winback_emails",
        "schedule": crontab(hour=10, minute=0, day_of_week=1),
        "kwargs": {"inactive_threshold_days": 90},
    },
    # Abandoned cart reminders: mỗi 1 giờ từ 8am-11pm — tự query DB
    "abandoned-cart-hourly": {
        "task": "backend.tasks.email_tasks.send_abandoned_cart_reminders",
        "schedule": crontab(minute=0, hour="8-23"),
    },
    # Weekly email stats report: thứ Hai 8am
    "email-stats-weekly": {
        "task": "backend.tasks.email_tasks.send_email_stats_report",
        "schedule": crontab(hour=8, minute=0, day_of_week=1),
    },
}
