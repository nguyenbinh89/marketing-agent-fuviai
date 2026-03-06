"""
FuviAI Marketing Agent — Celery Tasks: Email Automation
Birthday auto-send, win-back campaign, abandoned cart reminder
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from loguru import logger

from backend.tasks.celery_app import app


# ─── Birthday Auto-Send ───────────────────────────────────────────────────────

@app.task(
    name="backend.tasks.email_tasks.send_birthday_emails",
    bind=True,
    max_retries=2,
    time_limit=300,
)
def send_birthday_emails(self, customers: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Gửi birthday email cho tất cả khách hàng có sinh nhật hôm nay.

    Được gọi bởi beat_schedule lúc 9:00 sáng mỗi ngày.

    Args:
        customers: [{"email", "name", "clv_tier", "birthday": "MM-DD"}, ...]
                   Dữ liệu nên được lấy từ database trước khi gọi task này.
                   Demo: dùng danh sách cứng — trong production tích hợp DB query.
    """
    today = date.today().strftime("%m-%d")
    sent = 0
    failed = 0
    skipped = 0

    try:
        from backend.agents.personalize_agent import PersonalizeAgent
        agent = PersonalizeAgent()

        for c in customers:
            birthday = c.get("birthday", "")
            if not birthday:
                skipped += 1
                continue

            # So sánh MM-DD
            if birthday[:5] != today:
                skipped += 1
                continue

            email = c.get("email", "")
            name = c.get("name", "")
            tier = c.get("clv_tier", "loyal")

            if not email:
                failed += 1
                continue

            try:
                result = agent.send_birthday_campaign(
                    customer_email=email,
                    customer_name=name,
                    tier=tier,
                    birthday_offer=c.get("birthday_offer", ""),
                )
                if result.success:
                    sent += 1
                    logger.info(f"Birthday email sent | to={email} | tier={tier}")
                else:
                    failed += 1
                    logger.warning(f"Birthday email failed | to={email} | error={result.error}")
            except Exception as e:
                failed += 1
                logger.error(f"Birthday email exception | to={email} | error={e}")

        summary = {
            "date": today,
            "total_customers": len(customers),
            "birthday_today": sent + failed,
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
        }
        logger.info(f"Birthday task done | {summary}")
        return summary

    except Exception as exc:
        logger.error(f"Birthday email task failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


# ─── Win-Back Campaign ────────────────────────────────────────────────────────

@app.task(
    name="backend.tasks.email_tasks.send_winback_emails",
    bind=True,
    max_retries=2,
    time_limit=600,
)
def send_winback_emails(
    self,
    customers: list[dict[str, Any]],
    inactive_threshold_days: int = 90,
) -> dict[str, Any]:
    """
    Gửi win-back email cho khách hàng không hoạt động.

    Được gọi bởi beat_schedule mỗi thứ Hai lúc 10:00 sáng.

    Args:
        customers: [{"email", "name", "clv_tier", "days_since_last_purchase", "total_spent"}, ...]
        inactive_threshold_days: Gửi cho khách không mua > X ngày (default 90)
    """
    sent = 0
    failed = 0
    skipped = 0

    try:
        from backend.agents.personalize_agent import PersonalizeAgent
        from backend.tools.email_tool import EmailTool
        agent = PersonalizeAgent()
        email_tool = EmailTool()

        for c in customers:
            days_inactive = c.get("days_since_last_purchase", 0)
            if days_inactive < inactive_threshold_days:
                skipped += 1
                continue

            # Đã gửi win-back trong 30 ngày qua → skip
            last_winback = c.get("last_winback_sent_days_ago", 999)
            if last_winback < 30:
                skipped += 1
                continue

            email = c.get("email", "")
            name = c.get("name", "")
            tier = c.get("clv_tier", "at_risk")

            if not email or not email_tool.validate_email(email):
                failed += 1
                continue

            try:
                # Tạo win-back content bằng PersonalizeAgent
                content = agent.personalized_email(
                    customer=c,
                    segment=tier,
                    product_context="FuviAI Marketing Agent",
                    trigger="inactive_90d" if days_inactive >= 90 else "inactive_30d",
                )
                result = email_tool.send_win_back(
                    to_email=email,
                    to_name=name,
                    email_content=content,
                    days_inactive=days_inactive,
                )
                if result.success:
                    sent += 1
                    logger.info(f"Win-back email sent | to={email} | days_inactive={days_inactive}")
                else:
                    failed += 1
                    logger.warning(f"Win-back failed | to={email} | error={result.error}")
            except Exception as e:
                failed += 1
                logger.error(f"Win-back exception | to={email} | error={e}")

        summary = {
            "threshold_days": inactive_threshold_days,
            "total_customers": len(customers),
            "eligible": sent + failed,
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
        }
        logger.info(f"Win-back task done | {summary}")
        return summary

    except Exception as exc:
        logger.error(f"Win-back task failed: {exc}")
        raise self.retry(exc=exc, countdown=180)


# ─── Abandoned Cart Reminder ──────────────────────────────────────────────────

@app.task(
    name="backend.tasks.email_tasks.send_abandoned_cart_reminders",
    bind=True,
    max_retries=2,
    time_limit=600,
)
def send_abandoned_cart_reminders(
    self,
    carts: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Gửi abandoned cart emails theo đúng timing:
    - Step 1: 1h sau khi bỏ giỏ
    - Step 2: 24h sau (nếu chưa mua)
    - Step 3: 72h sau (nếu chưa mua)

    Được gọi bởi beat_schedule mỗi 1 giờ.

    Args:
        carts: [{
            "email", "name", "cart_value", "products",
            "segment", "abandoned_at": ISO datetime string,
            "step_1_sent": bool, "step_2_sent": bool, "step_3_sent": bool
        }, ...]
    """
    sent = 0
    failed = 0
    skipped = 0

    try:
        from backend.agents.personalize_agent import PersonalizeAgent
        agent = PersonalizeAgent()
        now = datetime.utcnow()

        for cart in carts:
            email = cart.get("email", "")
            name = cart.get("name", "")
            cart_value = float(cart.get("cart_value", 0))
            products = cart.get("products", [])
            segment = cart.get("segment", "potential")

            if not email or not products:
                skipped += 1
                continue

            # Parse abandoned_at
            try:
                abandoned_at = datetime.fromisoformat(cart.get("abandoned_at", ""))
            except (ValueError, TypeError):
                skipped += 1
                continue

            hours_elapsed = (now - abandoned_at).total_seconds() / 3600

            # Determine which step to send
            step_to_send: int | None = None
            if hours_elapsed >= 1 and not cart.get("step_1_sent"):
                step_to_send = 1
            elif hours_elapsed >= 24 and not cart.get("step_2_sent"):
                step_to_send = 2
            elif hours_elapsed >= 72 and not cart.get("step_3_sent"):
                step_to_send = 3

            if step_to_send is None:
                skipped += 1
                continue

            try:
                results = agent.send_abandoned_cart_sequence(
                    customer_email=email,
                    customer_name=name,
                    cart_value=cart_value,
                    products=products,
                    segment=segment,
                    steps=[step_to_send],
                )
                step_key = f"step_{step_to_send}"
                if results.get(step_key) and results[step_key].success:
                    sent += 1
                    logger.info(f"Cart email sent | step={step_to_send} | to={email} | value={cart_value:,.0f}")
                else:
                    error = results.get(step_key, {})
                    failed += 1
                    logger.warning(f"Cart email failed | step={step_to_send} | to={email} | error={getattr(error, 'error', 'unknown')}")
            except Exception as e:
                failed += 1
                logger.error(f"Cart email exception | to={email} | step={step_to_send} | error={e}")

        summary = {
            "total_carts": len(carts),
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
            "run_at": now.isoformat(),
        }
        logger.info(f"Abandoned cart task done | {summary}")
        return summary

    except Exception as exc:
        logger.error(f"Abandoned cart task failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


# ─── Email Stats Report ───────────────────────────────────────────────────────

@app.task(
    name="backend.tasks.email_tasks.send_email_stats_report",
    bind=True,
)
def send_email_stats_report(self) -> dict[str, Any]:
    """
    Lấy stats email 7 ngày qua từ SendGrid và ghi log.
    Chạy mỗi thứ Hai lúc 8am.
    """
    try:
        from backend.tools.email_tool import EmailTool
        from datetime import timedelta
        tool = EmailTool()

        end = date.today()
        start = end - timedelta(days=7)
        stats = tool.get_stats(start.isoformat(), end.isoformat())

        totals = stats.get("totals", {})
        logger.info(
            f"Weekly email stats | "
            f"delivered={totals.get('delivered', 0)} | "
            f"opens={totals.get('opens', 0)} | "
            f"clicks={totals.get('clicks', 0)} | "
            f"bounces={totals.get('bounces', 0)} | "
            f"unsubscribes={totals.get('unsubscribes', 0)}"
        )
        return stats
    except Exception as exc:
        logger.error(f"Email stats task failed: {exc}")
        return {"error": str(exc)}
