"""
FuviAI Marketing Agent — Shopee Tool
Shopee Open Platform API wrapper cho shop management, ads, và analytics
Docs: https://open.shopee.com/documents

Auth: HMAC-SHA256 signature với partner_id + partner_key + access_token
Endpoints dùng: Shop, Product, Order, Ads, Insight (Analytics)
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from loguru import logger

import httpx

from backend.config.settings import get_settings


SHOPEE_API_BASE = "https://partner.shopeemobile.com/api/v2"
SHOPEE_API_BASE_TEST = "https://partner.test-stable.shopeemobile.com/api/v2"


class ShopeeTool:
    """
    Wrapper cho Shopee Open Platform API v2.

    Cần trong .env:
        SHOPEE_PARTNER_ID  — Partner ID từ Shopee Partner Portal
        SHOPEE_PARTNER_KEY — Partner Key (secret) để ký request
        SHOPEE_ACCESS_TOKEN — Access token của shop (lấy qua OAuth)
        SHOPEE_SHOP_ID     — Shop ID của store cần quản lý

    Usage:
        tool = ShopeeTool()

        # Lấy thông tin shop
        info = tool.get_shop_info()

        # Lấy danh sách sản phẩm
        products = tool.get_product_list(page_size=20)

        # Cập nhật giá sản phẩm
        tool.update_price(item_id=123456, price=99000)

        # Lấy analytics doanh thu
        revenue = tool.get_shop_performance()

        # Tạo voucher flash sale
        tool.create_voucher(discount_pct=20, min_spend=200000)
    """

    def __init__(self, test_mode: bool = False):
        settings = get_settings()
        self._partner_id = int(settings.shopee_partner_id) if settings.shopee_partner_id else 0
        self._partner_key = settings.shopee_partner_key
        self._access_token = getattr(settings, "shopee_access_token", "")
        self._shop_id = int(getattr(settings, "shopee_shop_id", 0) or 0)
        self._base = SHOPEE_API_BASE_TEST if test_mode else SHOPEE_API_BASE
        self._client = httpx.Client(timeout=30)

    @property
    def is_configured(self) -> bool:
        return bool(self._partner_id and self._partner_key)

    def _not_configured(self) -> dict[str, Any]:
        return {"error": "SHOPEE_PARTNER_ID hoặc SHOPEE_PARTNER_KEY chưa được set trong .env"}

    def _sign(self, path: str, timestamp: int) -> str:
        """
        Tạo HMAC-SHA256 signature theo Shopee spec:
        base_string = partner_id + path + timestamp + access_token + shop_id
        """
        base = (
            f"{self._partner_id}{path}{timestamp}"
            f"{self._access_token}{self._shop_id}"
        )
        return hmac.new(
            self._partner_key.encode("utf-8"),
            base.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _params(self, path: str) -> dict[str, Any]:
        """Tạo common params (sign, timestamp, partner_id, access_token, shop_id)."""
        ts = int(time.time())
        return {
            "partner_id": self._partner_id,
            "timestamp": ts,
            "access_token": self._access_token,
            "shop_id": self._shop_id,
            "sign": self._sign(path, ts),
        }

    def _get(self, path: str, extra_params: dict | None = None) -> dict[str, Any]:
        if not self.is_configured:
            return self._not_configured()
        params = {**self._params(path), **(extra_params or {})}
        try:
            resp = self._client.get(f"{self._base}{path}", params=params)
            data = resp.json()
            if data.get("error"):
                logger.error(f"Shopee GET error | path={path} | error={data['error']}")
            return data
        except Exception as e:
            logger.error(f"Shopee GET exception: {e}")
            return {"error": str(e)}

    def _post(self, path: str, payload: dict) -> dict[str, Any]:
        if not self.is_configured:
            return self._not_configured()
        params = self._params(path)
        try:
            resp = self._client.post(
                f"{self._base}{path}",
                params=params,
                json=payload,
            )
            data = resp.json()
            if data.get("error"):
                logger.error(f"Shopee POST error | path={path} | error={data['error']}")
            return data
        except Exception as e:
            logger.error(f"Shopee POST exception: {e}")
            return {"error": str(e)}

    # ─── Shop ────────────────────────────────────────────────────────────────

    def get_shop_info(self) -> dict[str, Any]:
        """Lấy thông tin cơ bản của shop (tên, rating, follower, response rate)."""
        result = self._get("/shop/get_shop_info")
        logger.debug(f"Shopee shop info fetched | shop_id={self._shop_id}")
        return result.get("response", result)

    def get_shop_performance(self) -> dict[str, Any]:
        """
        Lấy KPI hiệu suất shop: doanh thu, đơn hàng, conversion rate, rating.
        Dùng cho CampaignAgent báo cáo weekly.
        """
        result = self._get("/shop/get_shop_performance")
        logger.debug("Shopee shop performance fetched")
        return result.get("response", result)

    # ─── Products ────────────────────────────────────────────────────────────

    def get_product_list(
        self,
        page_size: int = 20,
        offset: int = 0,
        item_status: str = "NORMAL",
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách sản phẩm trong shop.

        Args:
            item_status: "NORMAL" | "BANNED" | "DELETED" | "UNLIST"
        """
        result = self._get(
            "/product/get_item_list",
            {"page_size": min(page_size, 100), "offset": offset, "item_status": item_status},
        )
        items = result.get("response", {}).get("item", [])
        logger.debug(f"Shopee product list | count={len(items)}")
        return items

    def get_product_detail(self, item_id: int) -> dict[str, Any]:
        """Lấy thông tin chi tiết 1 sản phẩm (giá, stock, mô tả, ảnh)."""
        result = self._get("/product/get_item_base_info", {"item_id_list": item_id})
        items = result.get("response", {}).get("item_list", [])
        return items[0] if items else result

    def update_price(self, item_id: int, price: float, model_id: int = 0) -> dict[str, Any]:
        """
        Cập nhật giá sản phẩm.

        Args:
            price: Giá mới (VNĐ)
            model_id: ID variation nếu có, 0 = sản phẩm đơn
        """
        price_list = [{"model_id": model_id, "original_price": price}]
        result = self._post(
            "/product/update_price",
            {"item_id": item_id, "price_list": price_list},
        )
        logger.info(f"Shopee price updated | item={item_id} | price={price:,.0f}đ")
        return result.get("response", result)

    def update_stock(self, item_id: int, stock: int, model_id: int = 0) -> dict[str, Any]:
        """Cập nhật tồn kho sản phẩm."""
        stock_list = [{"model_id": model_id, "normal_stock": stock}]
        result = self._post(
            "/product/update_stock",
            {"item_id": item_id, "stock_list": stock_list},
        )
        logger.info(f"Shopee stock updated | item={item_id} | stock={stock}")
        return result.get("response", result)

    # ─── Orders ──────────────────────────────────────────────────────────────

    def get_order_list(
        self,
        days_back: int = 7,
        order_status: str = "READY_TO_SHIP",
        page_size: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Lấy danh sách đơn hàng trong N ngày qua.

        Args:
            order_status: "UNPAID" | "READY_TO_SHIP" | "SHIPPED" | "COMPLETED" | "CANCELLED"
        """
        now = int(time.time())
        result = self._get(
            "/order/get_order_list",
            {
                "time_range_field": "create_time",
                "time_from": now - days_back * 86400,
                "time_to": now,
                "page_size": min(page_size, 100),
                "order_status": order_status,
            },
        )
        orders = result.get("response", {}).get("order_list", [])
        logger.debug(f"Shopee orders fetched | days={days_back} | count={len(orders)}")
        return orders

    def get_order_detail(self, order_sn_list: list[str]) -> list[dict[str, Any]]:
        """Lấy chi tiết nhiều đơn hàng cùng lúc (tối đa 50)."""
        result = self._post(
            "/order/get_order_detail",
            {
                "order_sn_list": order_sn_list[:50],
                "response_optional_fields": "buyer_user_id,buyer_username,item_list,total_amount",
            },
        )
        return result.get("response", {}).get("order_list", [])

    # ─── Vouchers / Flash Sale ────────────────────────────────────────────────

    def create_voucher(
        self,
        discount_pct: int,
        min_spend: float = 0,
        usage_limit: int = 100,
        start_time: int = 0,
        end_time: int = 0,
        voucher_name: str = "",
    ) -> dict[str, Any]:
        """
        Tạo voucher giảm giá cho shop.

        Args:
            discount_pct: Phần trăm giảm (1-90)
            min_spend: Giá trị đơn tối thiểu (VNĐ), 0 = không giới hạn
            usage_limit: Số lượt dùng tối đa
            start_time: Unix timestamp bắt đầu (0 = ngay bây giờ)
            end_time: Unix timestamp kết thúc (0 = 7 ngày sau)
        """
        now = int(time.time())
        payload = {
            "voucher_name": voucher_name or f"FuviAI Sale {discount_pct}%",
            "voucher_code": f"FUVIAI{discount_pct}",
            "start_time": start_time or now,
            "end_time": end_time or now + 7 * 86400,
            "discount_type": 1,        # 1 = percentage, 2 = fixed amount
            "discount_amount": discount_pct,
            "min_basket_price": min_spend,
            "max_price": 0,            # 0 = không giới hạn max discount
            "display_start_time": start_time or now,
            "voucher_type": 1,         # 1 = shop voucher
            "usage_quantity": usage_limit,
        }
        result = self._post("/voucher/add_voucher", payload)
        logger.info(f"Shopee voucher created | discount={discount_pct}% | limit={usage_limit}")
        return result.get("response", result)

    def get_voucher_list(self, status: str = "ongoing") -> list[dict[str, Any]]:
        """
        Lấy danh sách voucher.

        Args:
            status: "upcoming" | "ongoing" | "expired"
        """
        result = self._get(
            "/voucher/get_voucher_list",
            {"status": status, "page_size": 20, "page_no": 0},
        )
        return result.get("response", {}).get("voucher_list", [])

    # ─── Shopee Ads ──────────────────────────────────────────────────────────

    def get_ads_campaigns(self) -> list[dict[str, Any]]:
        """Lấy danh sách campaign quảng cáo đang chạy trên Shopee Ads."""
        result = self._get("/ads/get_all_campaign")
        campaigns = result.get("response", {}).get("campaign_info_list", [])
        logger.debug(f"Shopee ads campaigns fetched | count={len(campaigns)}")
        return campaigns

    def get_ads_performance(
        self,
        campaign_id: int,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        """
        Lấy performance data của 1 campaign Shopee Ads.

        Args:
            date_from: "2026-01-01"
            date_to: "2026-01-31"
        """
        result = self._get(
            "/ads/get_campaign_report",
            {
                "campaign_id": campaign_id,
                "date_from": date_from,
                "date_to": date_to,
            },
        )
        logger.debug(f"Shopee ads performance | campaign={campaign_id}")
        return result.get("response", result)

    def update_ads_budget(self, campaign_id: int, daily_budget: float) -> dict[str, Any]:
        """
        Cập nhật ngân sách ngày của campaign Shopee Ads.
        Dùng cho AdBudgetAgent tự động điều chỉnh budget.
        """
        result = self._post(
            "/ads/update_campaign",
            {"campaign_id": campaign_id, "daily_budget": daily_budget},
        )
        logger.info(f"Shopee ads budget updated | campaign={campaign_id} | budget={daily_budget:,.0f}đ")
        return result.get("response", result)

    # ─── Shop Insight (Analytics) ─────────────────────────────────────────────

    def get_shop_insight(
        self,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        """
        Lấy insight tổng hợp: traffic, conversion, doanh thu theo ngày.

        Args:
            date_from: "2026-01-01"
            date_to: "2026-01-31"

        Returns:
            {
              "page_view": [...],
              "unique_visitors": [...],
              "orders": [...],
              "revenue": [...],
            }
        """
        result = self._get(
            "/insight/get_shop_insight_info",
            {"date_from": date_from, "date_to": date_to},
        )
        logger.debug(f"Shopee insight fetched | {date_from} → {date_to}")
        return result.get("response", result)

    def get_product_insight(
        self,
        item_id: int,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        """Lấy insight của 1 sản phẩm cụ thể (views, add-to-cart, orders)."""
        result = self._get(
            "/insight/get_item_insight_info",
            {"item_id": item_id, "date_from": date_from, "date_to": date_to},
        )
        return result.get("response", result)

    # ─── Helpers cho Agents ───────────────────────────────────────────────────

    def get_top_products(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Lấy top sản phẩm bán chạy (dùng cho PersonalizeAgent + ContentAgent).
        Tổng hợp từ product list + order data.
        """
        products = self.get_product_list(page_size=50)
        # Sort theo sold count nếu có
        products_sorted = sorted(
            products,
            key=lambda p: p.get("sold", 0),
            reverse=True,
        )
        logger.debug(f"Shopee top products | limit={limit}")
        return products_sorted[:limit]

    def get_revenue_summary(self, days_back: int = 30) -> dict[str, Any]:
        """
        Tóm tắt doanh thu N ngày qua — dùng cho CampaignAgent báo cáo.
        Trả về: total_orders, total_revenue, avg_order_value, cancellation_rate.
        """
        orders = self.get_order_list(days_back=days_back, order_status="COMPLETED")
        cancelled = self.get_order_list(days_back=days_back, order_status="CANCELLED")

        total = len(orders)
        cancel = len(cancelled)
        # Shopee order không có total_amount trực tiếp trong list — cần get_order_detail
        summary = {
            "days": days_back,
            "total_completed_orders": total,
            "total_cancelled_orders": cancel,
            "cancellation_rate": round(cancel / (total + cancel) * 100, 1) if (total + cancel) > 0 else 0,
            "note": "Để lấy doanh thu chi tiết, dùng get_order_detail() với order_sn_list",
        }
        logger.info(f"Shopee revenue summary | days={days_back} | orders={total} | cancelled={cancel}")
        return summary
