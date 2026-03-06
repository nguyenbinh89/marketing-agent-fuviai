"""
FuviAI Marketing Agent — Database Repository
Query helpers dùng trong Celery tasks và API routes
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session
from loguru import logger

from backend.db.models import Customer, AbandonedCart, EmailLog


# ─── Customer Queries ─────────────────────────────────────────────────────────

def get_birthday_customers(db: Session, today: str | None = None) -> list[dict[str, Any]]:
    """
    Lấy danh sách KH có sinh nhật hôm nay, chưa nhận birthday email năm nay,
    và đang opted-in.

    Args:
        today: MM-DD format (default: hôm nay)
    """
    if not today:
        today = date.today().strftime("%m-%d")
    current_year = date.today().year

    customers = (
        db.query(Customer)
        .filter(
            Customer.birthday == today,
            Customer.email_opted_in == True,
            (Customer.last_birthday_sent_year != current_year)
            | (Customer.last_birthday_sent_year == None),
        )
        .all()
    )

    logger.info(f"Birthday customers today ({today}): {len(customers)}")
    return [c.to_dict() for c in customers]


def get_inactive_customers(
    db: Session,
    threshold_days: int = 90,
    winback_cooldown_days: int = 30,
) -> list[dict[str, Any]]:
    """
    Lấy KH không hoạt động > threshold_days và chưa nhận win-back trong cooldown_days.
    """
    cooldown_cutoff = datetime.utcnow() - timedelta(days=winback_cooldown_days)

    customers = (
        db.query(Customer)
        .filter(
            Customer.days_since_last_purchase >= threshold_days,
            Customer.email_opted_in == True,
            (Customer.last_winback_sent_at < cooldown_cutoff)
            | (Customer.last_winback_sent_at == None),
        )
        .limit(500)
        .all()
    )

    logger.info(f"Inactive customers (>{threshold_days}d): {len(customers)}")
    return [c.to_dict() for c in customers]


def get_pending_carts(db: Session) -> list[dict[str, Any]]:
    """
    Lấy giỏ hàng bị bỏ chưa recovered, cần gửi step tiếp theo.
    Chỉ lấy carts chưa hoàn thành cả 3 bước.
    """
    carts = (
        db.query(AbandonedCart)
        .filter(
            AbandonedCart.is_recovered == False,
            AbandonedCart.step_3_sent == False,
        )
        .order_by(AbandonedCart.abandoned_at)
        .limit(200)
        .all()
    )

    logger.info(f"Pending abandoned carts: {len(carts)}")
    return [c.to_dict() for c in carts]


def upsert_customer(db: Session, data: dict[str, Any]) -> Customer:
    """
    Tạo mới hoặc cập nhật customer theo customer_id.
    """
    customer_id = data.get("customer_id", "")
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()

    if customer is None:
        customer = Customer(customer_id=customer_id)
        db.add(customer)

    for field in [
        "name", "email", "phone", "total_spent", "purchase_count",
        "days_since_last_purchase", "clv_tier", "birthday",
        "email_opted_in", "industry",
    ]:
        if field in data:
            setattr(customer, field, data[field])

    db.flush()
    return customer


def mark_birthday_sent(db: Session, customer_id: str) -> None:
    """Đánh dấu đã gửi birthday email năm nay."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if customer:
        customer.last_birthday_sent_year = date.today().year
        db.flush()


def mark_winback_sent(db: Session, customer_email: str) -> None:
    """Cập nhật last_winback_sent_at."""
    customer = db.query(Customer).filter(Customer.email == customer_email).first()
    if customer:
        customer.last_winback_sent_at = datetime.utcnow()
        db.flush()


# ─── Cart Queries ─────────────────────────────────────────────────────────────

def create_cart(db: Session, data: dict[str, Any]) -> AbandonedCart:
    """Tạo mới abandoned cart record."""
    cart = AbandonedCart(
        cart_id=data["cart_id"],
        customer_email=data["email"],
        customer_name=data.get("name", ""),
        clv_segment=data.get("segment", "potential"),
        cart_value=float(data.get("cart_value", 0)),
        products=data.get("products", []),
        abandoned_at=datetime.utcnow(),
    )
    db.add(cart)
    db.flush()
    return cart


def mark_cart_step_sent(db: Session, cart_id: str, step: int) -> None:
    """Đánh dấu đã gửi email bước X cho cart."""
    cart = db.query(AbandonedCart).filter(AbandonedCart.cart_id == cart_id).first()
    if cart:
        if step == 1:
            cart.step_1_sent = True
            cart.step_1_sent_at = datetime.utcnow()
        elif step == 2:
            cart.step_2_sent = True
            cart.step_2_sent_at = datetime.utcnow()
        elif step == 3:
            cart.step_3_sent = True
            cart.step_3_sent_at = datetime.utcnow()
        db.flush()


def mark_cart_recovered(db: Session, cart_id: str) -> None:
    """Đánh dấu giỏ hàng đã được mua (recovered)."""
    cart = db.query(AbandonedCart).filter(AbandonedCart.cart_id == cart_id).first()
    if cart:
        cart.is_recovered = True
        cart.recovered_at = datetime.utcnow()
        db.flush()


# ─── Email Log ────────────────────────────────────────────────────────────────

def log_email(
    db: Session,
    to_email: str,
    to_name: str,
    subject: str,
    email_type: str,
    success: bool,
    segment: str = "",
    trigger: str = "",
    message_id: str = "",
    error: str = "",
    customer_id: str = "",
) -> EmailLog:
    """Ghi log một email đã gửi."""
    log = EmailLog(
        to_email=to_email,
        to_name=to_name,
        subject=subject,
        email_type=email_type,
        segment=segment,
        trigger=trigger,
        success=success,
        sendgrid_message_id=message_id,
        error_message=error,
        customer_id=customer_id,
    )
    db.add(log)
    db.flush()
    return log


def get_email_logs(
    db: Session,
    email_type: str | None = None,
    days_back: int = 7,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Lấy email logs gần đây."""
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    q = db.query(EmailLog).filter(EmailLog.sent_at >= cutoff)
    if email_type:
        q = q.filter(EmailLog.email_type == email_type)
    logs = q.order_by(EmailLog.sent_at.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]


def get_email_summary(db: Session, days_back: int = 7) -> dict[str, Any]:
    """Tổng hợp stats email theo type trong N ngày."""
    from sqlalchemy import func as sqlfunc
    cutoff = datetime.utcnow() - timedelta(days=days_back)

    rows = (
        db.query(
            EmailLog.email_type,
            sqlfunc.count(EmailLog.id).label("total"),
            sqlfunc.sum(
                sqlfunc.cast(EmailLog.success, Integer)
                if hasattr(EmailLog.success.type, "impl") else EmailLog.success
            ).label("sent"),
        )
        .filter(EmailLog.sent_at >= cutoff)
        .group_by(EmailLog.email_type)
        .all()
    )

    from sqlalchemy import Integer as SAInteger
    rows = (
        db.query(
            EmailLog.email_type,
            sqlfunc.count(EmailLog.id).label("total"),
        )
        .filter(EmailLog.sent_at >= cutoff)
        .group_by(EmailLog.email_type)
        .all()
    )

    return {
        "period_days": days_back,
        "by_type": {row.email_type: {"total": row.total} for row in rows},
    }
