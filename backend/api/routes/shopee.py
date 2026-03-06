"""
FuviAI Marketing Agent — /api/shopee/* routes
Shopee Open Platform: shop management, products, orders, vouchers, ads, insight
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from loguru import logger

from backend.tools.shopee_tool import ShopeeTool

router = APIRouter()

_shopee = None


def get_shopee() -> ShopeeTool:
    global _shopee
    if _shopee is None:
        _shopee = ShopeeTool()
    return _shopee


# ─── Request Models ──────────────────────────────────────────────────────────

class UpdatePriceRequest(BaseModel):
    item_id: int
    price: float = Field(..., gt=0, description="Giá mới (VNĐ)")
    model_id: int = 0


class UpdateStockRequest(BaseModel):
    item_id: int
    stock: int = Field(..., ge=0)
    model_id: int = 0


class CreateVoucherRequest(BaseModel):
    discount_pct: int = Field(..., ge=1, le=90, description="Phần trăm giảm giá")
    min_spend: float = Field(default=0, ge=0, description="Giá trị đơn tối thiểu (VNĐ)")
    usage_limit: int = Field(default=100, ge=1)
    voucher_name: str = ""
    start_time: int = 0
    end_time: int = 0


class UpdateAdsBudgetRequest(BaseModel):
    campaign_id: int
    daily_budget: float = Field(..., gt=0, description="Ngân sách ngày (VNĐ)")


# ─── Shop Endpoints ──────────────────────────────────────────────────────────

@router.get("/shop")
async def get_shop_info():
    """Thông tin cơ bản shop: tên, rating, follower, response rate."""
    try:
        return get_shopee().get_shop_info()
    except Exception as e:
        logger.error(f"Shopee shop info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance")
async def get_shop_performance():
    """KPI hiệu suất shop: doanh thu, đơn hàng, conversion rate, rating."""
    try:
        return get_shopee().get_shop_performance()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/revenue")
async def get_revenue_summary(days: int = Query(default=30, ge=1, le=90)):
    """Tóm tắt doanh thu N ngày: total_orders, cancellation_rate."""
    try:
        return get_shopee().get_revenue_summary(days_back=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insight")
async def get_shop_insight(date_from: str, date_to: str):
    """
    Insight tổng hợp theo ngày: page_view, unique_visitors, orders, revenue.

    date_from / date_to format: YYYY-MM-DD
    """
    try:
        return get_shopee().get_shop_insight(date_from=date_from, date_to=date_to)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Product Endpoints ───────────────────────────────────────────────────────

@router.get("/products")
async def get_products(
    page_size: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str = Query(default="NORMAL"),
):
    """Danh sách sản phẩm trong shop."""
    valid_statuses = ("NORMAL", "BANNED", "DELETED", "UNLIST")
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status phải là: {', '.join(valid_statuses)}")
    try:
        return get_shopee().get_product_list(page_size=page_size, offset=offset, item_status=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/top")
async def get_top_products(limit: int = Query(default=10, ge=1, le=50)):
    """Top sản phẩm bán chạy (sort theo sold count)."""
    try:
        return get_shopee().get_top_products(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{item_id}")
async def get_product_detail(item_id: int):
    """Chi tiết 1 sản phẩm: giá, stock, mô tả, ảnh."""
    try:
        return get_shopee().get_product_detail(item_id=item_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/products/price")
async def update_price(request: UpdatePriceRequest):
    """Cập nhật giá sản phẩm."""
    try:
        result = get_shopee().update_price(
            item_id=request.item_id,
            price=request.price,
            model_id=request.model_id,
        )
        return {"updated": True, "item_id": request.item_id, "new_price": request.price, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/products/stock")
async def update_stock(request: UpdateStockRequest):
    """Cập nhật tồn kho sản phẩm."""
    try:
        result = get_shopee().update_stock(
            item_id=request.item_id,
            stock=request.stock,
            model_id=request.model_id,
        )
        return {"updated": True, "item_id": request.item_id, "new_stock": request.stock, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Order Endpoints ─────────────────────────────────────────────────────────

@router.get("/orders")
async def get_orders(
    days: int = Query(default=7, ge=1, le=90),
    status: str = Query(default="READY_TO_SHIP"),
    page_size: int = Query(default=50, ge=1, le=100),
):
    """
    Danh sách đơn hàng.
    status: UNPAID | READY_TO_SHIP | SHIPPED | COMPLETED | CANCELLED
    """
    valid = ("UNPAID", "READY_TO_SHIP", "SHIPPED", "COMPLETED", "CANCELLED")
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"status phải là: {', '.join(valid)}")
    try:
        orders = get_shopee().get_order_list(days_back=days, order_status=status, page_size=page_size)
        return {"days": days, "status": status, "count": len(orders), "orders": orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Voucher Endpoints ───────────────────────────────────────────────────────

@router.post("/vouchers")
async def create_voucher(request: CreateVoucherRequest):
    """Tạo voucher giảm giá (percentage discount)."""
    try:
        result = get_shopee().create_voucher(
            discount_pct=request.discount_pct,
            min_spend=request.min_spend,
            usage_limit=request.usage_limit,
            voucher_name=request.voucher_name,
            start_time=request.start_time,
            end_time=request.end_time,
        )
        return {"created": True, "discount_pct": request.discount_pct, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vouchers")
async def get_vouchers(status: str = Query(default="ongoing")):
    """
    Danh sách voucher.
    status: upcoming | ongoing | expired
    """
    if status not in ("upcoming", "ongoing", "expired"):
        raise HTTPException(status_code=400, detail="status phải là: upcoming, ongoing, expired")
    try:
        vouchers = get_shopee().get_voucher_list(status=status)
        return {"status": status, "count": len(vouchers), "vouchers": vouchers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Ads Endpoints ───────────────────────────────────────────────────────────

@router.get("/ads")
async def get_ads_campaigns():
    """Danh sách campaign Shopee Ads đang chạy."""
    try:
        campaigns = get_shopee().get_ads_campaigns()
        return {"count": len(campaigns), "campaigns": campaigns}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ads/{campaign_id}/performance")
async def get_ads_performance(campaign_id: int, date_from: str, date_to: str):
    """Performance data của 1 Shopee Ads campaign (date format: YYYY-MM-DD)."""
    try:
        return get_shopee().get_ads_performance(
            campaign_id=campaign_id,
            date_from=date_from,
            date_to=date_to,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/ads/budget")
async def update_ads_budget(request: UpdateAdsBudgetRequest):
    """Cập nhật ngân sách ngày của Shopee Ads campaign."""
    try:
        result = get_shopee().update_ads_budget(
            campaign_id=request.campaign_id,
            daily_budget=request.daily_budget,
        )
        return {"updated": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
