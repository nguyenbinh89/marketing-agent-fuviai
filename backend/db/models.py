"""
FuviAI Marketing Agent — SQLAlchemy Models
Customer, AbandonedCart, EmailLog
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Date, Float,
    Integer, String, Text, JSON, Index,
    func,
)

from backend.db.database import Base


class Customer(Base):
    """Khách hàng với CLV data và email automation info."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), default="")

    # CLV data
    total_spent = Column(Float, default=0.0)
    purchase_count = Column(Integer, default=0)
    days_since_last_purchase = Column(Integer, default=0)
    clv_tier = Column(String(20), default="new")  # champion/loyal/potential/at_risk/lost/new

    # Birthday (MM-DD format cho annual trigger)
    birthday = Column(String(5), default="")  # "03-06"

    # Email automation flags
    last_winback_sent_at = Column(DateTime, nullable=True)
    last_birthday_sent_year = Column(Integer, nullable=True)  # năm gửi gần nhất
    email_opted_in = Column(Boolean, default=True)

    # Metadata
    industry = Column(String(50), default="")
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_customers_clv_tier", "clv_tier"),
        Index("ix_customers_birthday", "birthday"),
        Index("ix_customers_email_opted", "email_opted_in"),
    )

    @property
    def days_since_winback(self) -> int:
        """Số ngày kể từ lần win-back email cuối."""
        if not self.last_winback_sent_at:
            return 9999
        return (datetime.utcnow() - self.last_winback_sent_at).days

    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "total_spent": self.total_spent,
            "purchase_count": self.purchase_count,
            "days_since_last_purchase": self.days_since_last_purchase,
            "clv_tier": self.clv_tier,
            "birthday": self.birthday,
            "email_opted_in": self.email_opted_in,
            "industry": self.industry,
        }


class AbandonedCart(Base):
    """Giỏ hàng bị bỏ — tracking để gửi 3-step email sequence."""
    __tablename__ = "abandoned_carts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(String(64), unique=True, nullable=False, index=True)
    customer_email = Column(String(255), nullable=False, index=True)
    customer_name = Column(String(255), default="")
    clv_segment = Column(String(20), default="potential")

    cart_value = Column(Float, nullable=False)
    products = Column(JSON, default=list)  # ["FuviAI Pro", "FuviAI Training"]

    abandoned_at = Column(DateTime, nullable=False, default=func.now())
    recovered_at = Column(DateTime, nullable=True)
    is_recovered = Column(Boolean, default=False)

    # Email step tracking
    step_1_sent = Column(Boolean, default=False)
    step_1_sent_at = Column(DateTime, nullable=True)
    step_2_sent = Column(Boolean, default=False)
    step_2_sent_at = Column(DateTime, nullable=True)
    step_3_sent = Column(Boolean, default=False)
    step_3_sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_carts_abandoned_at", "abandoned_at"),
        Index("ix_carts_recovered", "is_recovered"),
    )

    def to_dict(self) -> dict:
        return {
            "cart_id": self.cart_id,
            "email": self.customer_email,
            "name": self.customer_name,
            "segment": self.clv_segment,
            "cart_value": self.cart_value,
            "products": self.products or [],
            "abandoned_at": self.abandoned_at.isoformat() if self.abandoned_at else "",
            "step_1_sent": self.step_1_sent,
            "step_2_sent": self.step_2_sent,
            "step_3_sent": self.step_3_sent,
        }


class EmailLog(Base):
    """Log mỗi email đã gửi — audit trail và dedup."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    to_email = Column(String(255), nullable=False, index=True)
    to_name = Column(String(255), default="")
    subject = Column(String(500), default="")

    email_type = Column(String(50), nullable=False)  # personalized/birthday/winback/abandoned_cart/bulk
    segment = Column(String(20), default="")
    trigger = Column(String(50), default="")

    success = Column(Boolean, nullable=False)
    sendgrid_message_id = Column(String(255), default="")
    error_message = Column(Text, default="")

    sent_at = Column(DateTime, default=func.now(), index=True)
    customer_id = Column(String(64), default="")

    __table_args__ = (
        Index("ix_email_logs_type_sent", "email_type", "sent_at"),
        Index("ix_email_logs_customer", "customer_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "to_email": self.to_email,
            "subject": self.subject,
            "email_type": self.email_type,
            "segment": self.segment,
            "success": self.success,
            "sent_at": self.sent_at.isoformat() if self.sent_at else "",
        }
