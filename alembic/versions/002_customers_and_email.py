"""Add customers, abandoned_carts, email_logs tables

Revision ID: 002
Revises: 001
Create Date: 2026-03-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── Customers ───────────────────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.String(64), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), server_default=""),
        sa.Column("total_spent", sa.Float, server_default="0"),
        sa.Column("purchase_count", sa.Integer, server_default="0"),
        sa.Column("days_since_last_purchase", sa.Integer, server_default="0"),
        sa.Column("clv_tier", sa.String(20), server_default="new"),
        sa.Column("birthday", sa.String(5), server_default=""),
        sa.Column("last_winback_sent_at", sa.DateTime, nullable=True),
        sa.Column("last_birthday_sent_year", sa.Integer, nullable=True),
        sa.Column("email_opted_in", sa.Boolean, server_default="true"),
        sa.Column("industry", sa.String(50), server_default=""),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_customers_customer_id", "customers", ["customer_id"], unique=True)
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_clv_tier", "customers", ["clv_tier"])
    op.create_index("ix_customers_birthday", "customers", ["birthday"])
    op.create_index("ix_customers_email_opted", "customers", ["email_opted_in"])

    # ─── Abandoned Carts ─────────────────────────────────────────────────────
    op.create_table(
        "abandoned_carts",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("cart_id", sa.String(64), unique=True, nullable=False),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("customer_name", sa.String(255), server_default=""),
        sa.Column("clv_segment", sa.String(20), server_default="potential"),
        sa.Column("cart_value", sa.Float, nullable=False),
        sa.Column("products", sa.JSON, nullable=True),
        sa.Column("abandoned_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("recovered_at", sa.DateTime, nullable=True),
        sa.Column("is_recovered", sa.Boolean, server_default="false"),
        sa.Column("step_1_sent", sa.Boolean, server_default="false"),
        sa.Column("step_1_sent_at", sa.DateTime, nullable=True),
        sa.Column("step_2_sent", sa.Boolean, server_default="false"),
        sa.Column("step_2_sent_at", sa.DateTime, nullable=True),
        sa.Column("step_3_sent", sa.Boolean, server_default="false"),
        sa.Column("step_3_sent_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_carts_cart_id", "abandoned_carts", ["cart_id"], unique=True)
    op.create_index("ix_carts_customer_email", "abandoned_carts", ["customer_email"])
    op.create_index("ix_carts_abandoned_at", "abandoned_carts", ["abandoned_at"])
    op.create_index("ix_carts_recovered", "abandoned_carts", ["is_recovered"])

    # ─── Email Logs ──────────────────────────────────────────────────────────
    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("to_email", sa.String(255), nullable=False),
        sa.Column("to_name", sa.String(255), server_default=""),
        sa.Column("subject", sa.String(500), server_default=""),
        sa.Column("email_type", sa.String(50), nullable=False),
        sa.Column("segment", sa.String(20), server_default=""),
        sa.Column("trigger", sa.String(50), server_default=""),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("sendgrid_message_id", sa.String(255), server_default=""),
        sa.Column("error_message", sa.Text, server_default=""),
        sa.Column("customer_id", sa.String(64), server_default=""),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_email_logs_to_email", "email_logs", ["to_email"])
    op.create_index("ix_email_logs_sent_at", "email_logs", ["sent_at"])
    op.create_index("ix_email_logs_type_sent", "email_logs", ["email_type", "sent_at"])
    op.create_index("ix_email_logs_customer", "email_logs", ["customer_id"])


def downgrade() -> None:
    op.drop_table("email_logs")
    op.drop_table("abandoned_carts")
    op.drop_table("customers")
