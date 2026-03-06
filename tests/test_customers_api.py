"""
Tests — /api/customers/* CRUD + Cart + Email Log endpoints
Dùng SQLite in-memory DB để không cần PostgreSQL
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client_with_db():
    """TestClient với SQLite in-memory DB."""
    with patch("backend.config.settings.Settings.anthropic_api_key", new="sk-ant-test"), \
         patch("backend.db.database.get_engine") as mock_engine:

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from backend.db.database import Base, get_session_factory
        import backend.db.models  # noqa

        # SQLite in-memory
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

        mock_engine.return_value = engine
        with patch("backend.db.database.get_session_factory", return_value=SessionLocal):
            with patch("backend.agents.base_agent.anthropic.Anthropic"), \
                 patch("backend.agents.base_agent.anthropic.AsyncAnthropic"):
                from backend.api.main import app
                with TestClient(app) as c:
                    yield c, engine


@pytest.fixture(scope="module")
def client(client_with_db):
    c, _ = client_with_db
    return c


# ─── Customer CRUD ────────────────────────────────────────────────────────────

class TestCustomerCRUD:
    def test_create_customer(self, client):
        r = client.post("/api/customers/", json={
            "customer_id": "TEST-C001",
            "name": "Nguyễn Văn An",
            "email": "an@example.com",
            "total_spent": 12000000,
            "purchase_count": 8,
            "days_since_last_purchase": 5,
            "clv_tier": "champion",
            "birthday": "03-06",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["customer_id"] == "TEST-C001"
        assert data["clv_tier"] == "champion"
        assert data["birthday"] == "03-06"

    def test_upsert_customer_updates_existing(self, client):
        # Tạo lần đầu
        client.post("/api/customers/", json={
            "customer_id": "TEST-C002",
            "name": "Trần Bích",
            "email": "bich@example.com",
            "total_spent": 1000000,
        })
        # Upsert lại với data mới
        r = client.post("/api/customers/", json={
            "customer_id": "TEST-C002",
            "name": "Trần Thị Bích",
            "email": "bich@example.com",
            "total_spent": 5000000,
            "clv_tier": "loyal",
        })
        assert r.status_code == 201
        assert r.json()["total_spent"] == 5000000
        assert r.json()["clv_tier"] == "loyal"

    def test_create_customer_missing_customer_id(self, client):
        r = client.post("/api/customers/", json={
            "customer_id": "",
            "name": "Test",
            "email": "test@example.com",
        })
        assert r.status_code == 400

    def test_create_customer_invalid_birthday_format(self, client):
        r = client.post("/api/customers/", json={
            "customer_id": "TEST-BAD",
            "name": "Test",
            "email": "bad@example.com",
            "birthday": "2026-03-06",  # sai format — phải là MM-DD
        })
        assert r.status_code == 400

    def test_get_customer(self, client):
        r = client.get("/api/customers/TEST-C001")
        assert r.status_code == 200
        assert r.json()["name"] == "Nguyễn Văn An"

    def test_get_customer_not_found(self, client):
        r = client.get("/api/customers/NONEXISTENT")
        assert r.status_code == 404

    def test_patch_customer(self, client):
        r = client.patch("/api/customers/TEST-C001", json={
            "total_spent": 20000000,
            "days_since_last_purchase": 1,
        })
        assert r.status_code == 200
        assert r.json()["total_spent"] == 20000000

    def test_patch_customer_not_found(self, client):
        r = client.patch("/api/customers/GHOST", json={"total_spent": 100})
        assert r.status_code == 404

    def test_list_customers(self, client):
        r = client.get("/api/customers/?limit=10")
        assert r.status_code == 200
        data = r.json()
        assert "customers" in data
        assert "total" in data
        assert isinstance(data["customers"], list)

    def test_list_customers_filter_tier(self, client):
        r = client.get("/api/customers/?clv_tier=champion&limit=10")
        assert r.status_code == 200
        for c in r.json()["customers"]:
            assert c["clv_tier"] == "champion"

    def test_batch_upsert(self, client):
        r = client.post("/api/customers/batch", json=[
            {"customer_id": "BATCH-01", "name": "A", "email": "a@b.com", "total_spent": 100000},
            {"customer_id": "BATCH-02", "name": "B", "email": "b@b.com", "total_spent": 200000},
        ])
        assert r.status_code == 201
        assert r.json()["upserted"] == 2

    def test_batch_too_many(self, client):
        r = client.post("/api/customers/batch", json=[
            {"customer_id": f"X{i}", "name": "T", "email": f"x{i}@b.com"} for i in range(501)
        ])
        assert r.status_code == 400

    def test_delete_customer(self, client):
        client.post("/api/customers/", json={
            "customer_id": "TO-DELETE",
            "name": "Del",
            "email": "del@b.com",
        })
        r = client.delete("/api/customers/TO-DELETE")
        assert r.status_code == 204
        # Confirm đã xoá
        r2 = client.get("/api/customers/TO-DELETE")
        assert r2.status_code == 404


# ─── Abandoned Cart ───────────────────────────────────────────────────────────

class TestAbandonedCart:
    def test_create_cart(self, client):
        r = client.post("/api/customers/carts/", json={
            "cart_id": "CART-TEST-001",
            "email": "khach@example.com",
            "name": "Khách Test",
            "cart_value": 1500000,
            "products": ["FuviAI Pro", "Training"],
        })
        assert r.status_code == 201
        data = r.json()
        assert data["cart_id"] == "CART-TEST-001"
        assert data["cart_value"] == 1500000
        assert data["is_recovered"] is False

    def test_create_cart_empty_products(self, client):
        r = client.post("/api/customers/carts/", json={
            "cart_id": "CART-BAD",
            "email": "bad@b.com",
            "cart_value": 100000,
            "products": [],
        })
        assert r.status_code == 400

    def test_create_cart_zero_value(self, client):
        r = client.post("/api/customers/carts/", json={
            "cart_id": "CART-ZERO",
            "email": "zero@b.com",
            "cart_value": 0,
            "products": ["Item"],
        })
        assert r.status_code == 400

    def test_recover_cart(self, client):
        r = client.post("/api/customers/carts/CART-TEST-001/recover")
        assert r.status_code == 200
        assert r.json()["recovered"] is True

    def test_recover_cart_not_found(self, client):
        r = client.post("/api/customers/carts/GHOST-CART/recover")
        assert r.status_code == 404

    def test_list_carts(self, client):
        r = client.get("/api/customers/carts/?is_recovered=false")
        assert r.status_code == 200
        assert "carts" in r.json()

    def test_list_recovered_carts(self, client):
        r = client.get("/api/customers/carts/?is_recovered=true")
        assert r.status_code == 200
        # CART-TEST-001 đã recovered
        cart_ids = [c["cart_id"] for c in r.json()["carts"]]
        assert "CART-TEST-001" in cart_ids


# ─── Email Logs ───────────────────────────────────────────────────────────────

class TestEmailLogs:
    def test_email_logs_empty(self, client):
        r = client.get("/api/customers/email-logs/")
        assert r.status_code == 200
        assert "logs" in r.json()
        assert isinstance(r.json()["logs"], list)

    def test_email_logs_filter_type(self, client):
        r = client.get("/api/customers/email-logs/?email_type=birthday")
        assert r.status_code == 200

    def test_email_logs_days_back_limit(self, client):
        r = client.get("/api/customers/email-logs/?days_back=91")
        assert r.status_code == 422  # FastAPI validation error

    def test_email_summary(self, client):
        r = client.get("/api/customers/email-logs/summary?days_back=7")
        assert r.status_code == 200
        data = r.json()
        assert "period_days" in data
        assert "by_type" in data
