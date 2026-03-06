"""
FuviAI Marketing Agent — /api/customers/* routes
Customer CRUD, abandoned cart management, email log
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from loguru import logger

router = APIRouter()


# ─── Request Models ───────────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    customer_id: str
    name: str
    email: str
    phone: str = ""
    total_spent: float = 0.0
    purchase_count: int = 0
    days_since_last_purchase: int = 0
    clv_tier: str = "new"
    birthday: str = ""          # MM-DD format, VD: "03-06"
    email_opted_in: bool = True
    industry: str = ""


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_spent: float | None = None
    purchase_count: int | None = None
    days_since_last_purchase: int | None = None
    clv_tier: str | None = None
    birthday: str | None = None
    email_opted_in: bool | None = None


class CartCreate(BaseModel):
    cart_id: str
    email: str
    name: str = ""
    segment: str = "potential"
    cart_value: float
    products: list[str]


class CartRecover(BaseModel):
    cart_id: str


# ─── Customer endpoints ───────────────────────────────────────────────────────

@router.post("/", status_code=201)
async def create_customer(request: CustomerCreate):
    """Tạo mới hoặc cập nhật customer (upsert theo customer_id)."""
    if not request.customer_id.strip():
        raise HTTPException(status_code=400, detail="customer_id không được để trống")
    if not request.email.strip():
        raise HTTPException(status_code=400, detail="email không được để trống")
    if request.birthday and len(request.birthday) != 5:
        raise HTTPException(status_code=400, detail="birthday phải có format MM-DD, VD: '03-06'")
    try:
        from backend.db.database import get_db
        from backend.db.repository import upsert_customer
        with get_db() as db:
            customer = upsert_customer(db, request.model_dump())
            return customer.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}")
async def get_customer(customer_id: str):
    """Lấy thông tin customer theo customer_id."""
    try:
        from backend.db.database import get_db
        from backend.db.models import Customer
        with get_db() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                raise HTTPException(status_code=404, detail="Không tìm thấy customer")
            return customer.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{customer_id}")
async def update_customer(customer_id: str, request: CustomerUpdate):
    """Cập nhật 1 số trường của customer."""
    try:
        from backend.db.database import get_db
        from backend.db.models import Customer
        with get_db() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                raise HTTPException(status_code=404, detail="Không tìm thấy customer")
            updates = request.model_dump(exclude_none=True)
            for field, value in updates.items():
                setattr(customer, field, value)
            return customer.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(customer_id: str):
    """Xoá customer."""
    try:
        from backend.db.database import get_db
        from backend.db.models import Customer
        with get_db() as db:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                raise HTTPException(status_code=404, detail="Không tìm thấy customer")
            db.delete(customer)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_customers(
    clv_tier: str | None = Query(None, description="Lọc theo tier: champion/loyal/potential/at_risk/lost/new"),
    email_opted_in: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Danh sách customers với filter và pagination."""
    try:
        from backend.db.database import get_db
        from backend.db.models import Customer
        with get_db() as db:
            q = db.query(Customer)
            if clv_tier:
                q = q.filter(Customer.clv_tier == clv_tier)
            if email_opted_in is not None:
                q = q.filter(Customer.email_opted_in == email_opted_in)
            total = q.count()
            customers = q.order_by(Customer.total_spent.desc()).offset(offset).limit(limit).all()
            return {
                "total": total,
                "offset": offset,
                "limit": limit,
                "customers": [c.to_dict() for c in customers],
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", status_code=201)
async def batch_upsert_customers(customers: list[CustomerCreate]):
    """Tạo/cập nhật nhiều customers cùng lúc (tối đa 500)."""
    if not customers:
        raise HTTPException(status_code=400, detail="customers không được để trống")
    if len(customers) > 500:
        raise HTTPException(status_code=400, detail="Tối đa 500 customers mỗi lần")
    try:
        from backend.db.database import get_db
        from backend.db.repository import upsert_customer
        with get_db() as db:
            upserted = 0
            for c in customers:
                upsert_customer(db, c.model_dump())
                upserted += 1
            return {"upserted": upserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Abandoned Cart endpoints ─────────────────────────────────────────────────

@router.post("/carts/", status_code=201)
async def create_abandoned_cart(request: CartCreate):
    """Tạo abandoned cart record (trigger từ frontend/webhook khi user bỏ giỏ)."""
    if not request.products:
        raise HTTPException(status_code=400, detail="products không được để trống")
    if request.cart_value <= 0:
        raise HTTPException(status_code=400, detail="cart_value phải > 0")
    try:
        from backend.db.database import get_db
        from backend.db.repository import create_cart
        with get_db() as db:
            cart = create_cart(db, request.model_dump())
            return cart.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/carts/{cart_id}/recover")
async def recover_cart(cart_id: str):
    """Đánh dấu giỏ hàng đã được mua (dừng email sequence)."""
    try:
        from backend.db.database import get_db
        from backend.db.repository import mark_cart_recovered
        from backend.db.models import AbandonedCart
        with get_db() as db:
            cart = db.query(AbandonedCart).filter(AbandonedCart.cart_id == cart_id).first()
            if not cart:
                raise HTTPException(status_code=404, detail="Không tìm thấy cart")
            mark_cart_recovered(db, cart_id)
            return {"cart_id": cart_id, "recovered": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/carts/")
async def list_carts(
    is_recovered: bool | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Danh sách abandoned carts."""
    try:
        from backend.db.database import get_db
        from backend.db.models import AbandonedCart
        with get_db() as db:
            q = db.query(AbandonedCart)
            if is_recovered is not None:
                q = q.filter(AbandonedCart.is_recovered == is_recovered)
            carts = q.order_by(AbandonedCart.abandoned_at.desc()).limit(limit).all()
            return {"total": len(carts), "carts": [c.to_dict() for c in carts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Email Log endpoints ──────────────────────────────────────────────────────

@router.get("/email-logs/")
async def get_email_logs(
    email_type: str | None = Query(None, description="birthday/winback/abandoned_cart/personalized/bulk"),
    days_back: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
):
    """Lấy email logs gần đây."""
    try:
        from backend.db.database import get_db
        from backend.db.repository import get_email_logs
        with get_db() as db:
            logs = get_email_logs(db, email_type=email_type, days_back=days_back, limit=limit)
            return {"total": len(logs), "logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/email-logs/summary")
async def get_email_summary(days_back: int = Query(7, ge=1, le=90)):
    """Tổng hợp email stats theo type."""
    try:
        from backend.db.database import get_db
        from backend.db.repository import get_email_summary
        with get_db() as db:
            return get_email_summary(db, days_back=days_back)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
