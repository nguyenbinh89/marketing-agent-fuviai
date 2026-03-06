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
def send_birthday_emails(self, customers: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """
    Gửi birthday email cho tất cả khách hàng có sinh nhật hôm nay.
    Được gọi bởi beat_schedule lúc 9:00 sáng mỗi ngày.

    Args:
        customers: Nếu None → tự query từ DB. Nếu có → dùng list truyền vào (manual trigger).
    """
    today = date.today().strftime("%m-%d")
    sent = 0
    failed = 0

    try:
        from backend.agents.personalize_agent import PersonalizeAgent
        from backend.db.database import get_db
        from backend.db.repository import get_birthday_customers, mark_birthday_sent, log_email

        agent = PersonalizeAgent()

        # Lấy customers từ DB nếu không được inject
        if customers is None:
            with get_db() as db:
                customers = get_birthday_customers(db)

        for c in customers:
            email = c.get("email", "")
            name = c.get("name", "")
            tier = c.get("clv_tier", "loyal")
            customer_id = c.get("customer_id", "")

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
                with get_db() as db:
                    if result.success:
                        if customer_id:
                            mark_birthday_sent(db, customer_id)
                        sent += 1
                        logger.info(f"Birthday email sent | to={email} | tier={tier}")
                    else:
                        failed += 1
                        logger.warning(f"Birthday email failed | to={email} | error={result.error}")
                    log_email(
                        db, to_email=email, to_name=name,
                        subject=f"Chúc mừng sinh nhật {name}",
                        email_type="birthday", segment=tier,
                        success=result.success, error=result.error,
                        customer_id=customer_id,
                    )
            except Exception as e:
                failed += 1
                logger.error(f"Birthday email exception | to={email} | error={e}")

        summary = {
            "date": today,
            "total_customers": len(customers),
            "sent": sent,
            "failed": failed,
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
    customers: list[dict[str, Any]] | None = None,
    inactive_threshold_days: int = 90,
) -> dict[str, Any]:
    """
    Gửi win-back email cho khách hàng không hoạt động.
    Được gọi bởi beat_schedule mỗi thứ Hai lúc 10:00 sáng.

    Args:
        customers: Nếu None → tự query từ DB.
        inactive_threshold_days: Gửi cho khách không mua > X ngày (default 90)
    """
    sent = 0
    failed = 0

    try:
        from backend.agents.personalize_agent import PersonalizeAgent
        from backend.tools.email_tool import EmailTool
        from backend.db.database import get_db
        from backend.db.repository import get_inactive_customers, mark_winback_sent, log_email

        agent = PersonalizeAgent()
        email_tool = EmailTool()

        if customers is None:
            with get_db() as db:
                customers = get_inactive_customers(db, inactive_threshold_days)

        for c in customers:
            email = c.get("email", "")
            name = c.get("name", "")
            tier = c.get("clv_tier", "at_risk")
            days_inactive = c.get("days_since_last_purchase", 0)

            if not email or not email_tool.validate_email(email):
                failed += 1
                continue

            try:
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
                with get_db() as db:
                    if result.success:
                        mark_winback_sent(db, email)
                        sent += 1
                        logger.info(f"Win-back sent | to={email} | days={days_inactive}")
                    else:
                        failed += 1
                        logger.warning(f"Win-back failed | to={email} | error={result.error}")
                    log_email(
                        db, to_email=email, to_name=name,
                        subject=f"Chúng tôi nhớ bạn, {name}",
                        email_type="winback", segment=tier,
                        trigger="inactive_90d" if days_inactive >= 90 else "inactive_30d",
                        success=result.success, error=result.error,
                    )
            except Exception as e:
                failed += 1
                logger.error(f"Win-back exception | to={email} | error={e}")

        summary = {
            "threshold_days": inactive_threshold_days,
            "total": len(customers),
            "sent": sent,
            "failed": failed,
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
    carts: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Gửi abandoned cart emails theo đúng timing (step 1/2/3).
    Được gọi bởi beat_schedule mỗi 1 giờ.

    Args:
        carts: Nếu None → tự query từ DB. Nếu có → dùng list truyền vào.
    """
    sent = 0
    failed = 0
    skipped = 0

    try:
        from backend.agents.personalize_agent import PersonalizeAgent
        from backend.db.database import get_db
        from backend.db.repository import get_pending_carts, mark_cart_step_sent, log_email

        agent = PersonalizeAgent()
        now = datetime.utcnow()

        if carts is None:
            with get_db() as db:
                carts = get_pending_carts(db)

        for cart in carts:
            email = cart.get("email", "")
            name = cart.get("name", "")
            cart_value = float(cart.get("cart_value", 0))
            products = cart.get("products", [])
            segment = cart.get("segment", "potential")
            cart_id = cart.get("cart_id", "")

            if not email or not products:
                skipped += 1
                continue

            try:
                abandoned_at = datetime.fromisoformat(cart.get("abandoned_at", ""))
            except (ValueError, TypeError):
                skipped += 1
                continue

            hours_elapsed = (now - abandoned_at).total_seconds() / 3600

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
                result = results.get(step_key)
                success = bool(result and result.success)
                with get_db() as db:
                    if success:
                        if cart_id:
                            mark_cart_step_sent(db, cart_id, step_to_send)
                        sent += 1
                        logger.info(f"Cart email sent | step={step_to_send} | to={email}")
                    else:
                        failed += 1
                        logger.warning(f"Cart email failed | step={step_to_send} | to={email}")
                    log_email(
                        db, to_email=email, to_name=name,
                        subject=f"Giỏ hàng {cart_value:,.0f}đ của bạn",
                        email_type="abandoned_cart", segment=segment,
                        trigger=f"step_{step_to_send}", success=success,
                    )
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
