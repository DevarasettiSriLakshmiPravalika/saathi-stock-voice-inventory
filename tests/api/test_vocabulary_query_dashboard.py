"""
Phases 11 & 16: Vocabulary, Natural Language Queries, and Shop Dashboard Tests.

Tests:
- Shop-specific vocabulary creation, resolution, and isolation
- Natural language query assistant (CURRENT_STOCK, SALES_TODAY, RECEIPTS_TODAY, LOW_STOCK, REVIEW_QUEUE)
- Dashboard aggregation with real values
"""
import pytest
from httpx import AsyncClient

from tests.api.conftest import (
    register_and_login,
    create_shop_for_user,
    create_product_for_shop,
    set_baseline_for_product,
)


class TestShopVocabulary:

    @pytest.mark.asyncio
    async def test_vocabulary_mapping_resolves_product_in_voice(self, client: AsyncClient):
        """Map alias 'chawal' to 'Rice' -> 'Sold 5 bags of chawal' resolves to Rice."""
        owner = await register_and_login(client, "Vocab Owner", "+912004001001")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Rice", "bag")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 100.0, "bag")

        # Create alias mapping: "chawal" -> Rice
        vocab_res = await client.post(
            f"/api/v1/vocabulary?shop_id={shop['id']}",
            json={
                "source_term": "chawal",
                "mapping_type": "PRODUCT_ALIAS",
                "target_product_id": product["id"],
            },
            headers=owner["headers"],
        )
        assert vocab_res.status_code == 200
        assert vocab_res.json()["data"]["source_term"] == "chawal"

        # Now submit voice with "chawal"
        r = await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 5 bags of chawal"},
            headers=owner["headers"],
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["product_id"] == product["id"]
        assert data["decision"] == "AUTO_CONFIRMED"

        # Inventory check: 100 - 5 = 95
        inv_res = await client.get(f"/api/v1/products/{product['id']}/inventory", headers=owner["headers"])
        assert inv_res.json()["data"]["current_stock"] == 95.0

    @pytest.mark.asyncio
    async def test_vocabulary_is_isolated_between_shops(self, client: AsyncClient):
        """Vocabulary in Shop A must not resolve terms in Shop B."""
        owner_a = await register_and_login(client, "Owner A", "+912004001002")
        shop_a = await create_shop_for_user(client, owner_a["headers"], "Shop A")
        prod_a = await create_product_for_shop(client, owner_a["headers"], shop_a["id"], "Rice", "bag")

        # Add alias in Shop A
        await client.post(
            f"/api/v1/vocabulary?shop_id={shop_a['id']}",
            json={
                "source_term": "tandul",
                "mapping_type": "PRODUCT_ALIAS",
                "target_product_id": prod_a["id"],
            },
            headers=owner_a["headers"],
        )

        # Shop B has a product named "Rice", but no vocabulary mapping for "tandul"
        owner_b = await register_and_login(client, "Owner B", "+912004001003")
        shop_b = await create_shop_for_user(client, owner_b["headers"], "Shop B")
        prod_b = await create_product_for_shop(client, owner_b["headers"], shop_b["id"], "Rice", "bag")

        r = await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop_b["id"], "transcript_override": "Sold 5 bags of tandul"},
            headers=owner_b["headers"],
        )
        assert r.status_code == 200
        # In Shop B, "tandul" cannot resolve to prod_b
        assert r.json()["data"]["status"] == "FLAGGED"

    @pytest.mark.asyncio
    async def test_owner_can_list_and_delete_vocabulary(self, client: AsyncClient):
        owner = await register_and_login(client, "Vocab CRUD Owner", "+912004001004")
        shop = await create_shop_for_user(client, owner["headers"])
        prod = await create_product_for_shop(client, owner["headers"], shop["id"], "Wheat", "kg")

        # Create
        cr = await client.post(
            f"/api/v1/vocabulary?shop_id={shop['id']}",
            json={
                "source_term": "gehu",
                "mapping_type": "PRODUCT_ALIAS",
                "target_product_id": prod["id"],
            },
            headers=owner["headers"],
        )
        entry_id = cr.json()["data"]["id"]

        # List
        lr = await client.get(f"/api/v1/vocabulary?shop_id={shop['id']}", headers=owner["headers"])
        assert lr.status_code == 200
        assert len(lr.json()["data"]) == 1

        # Delete
        dr = await client.delete(f"/api/v1/vocabulary/{entry_id}", headers=owner["headers"])
        assert dr.status_code == 200
        assert dr.json()["data"]["deleted"] is True

        # List again -> 0
        lr2 = await client.get(f"/api/v1/vocabulary?shop_id={shop['id']}", headers=owner["headers"])
        assert len(lr2.json()["data"]) == 0


class TestNaturalLanguageQuery:

    @pytest.mark.asyncio
    async def test_query_current_stock(self, client: AsyncClient):
        owner = await register_and_login(client, "Query Owner", "+912004002001")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Rice", "bag")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 75.0, "bag")

        r = await client.post(
            "/api/v1/query",
            json={"shop_id": shop["id"], "query": "How much rice is left?"},
            headers=owner["headers"],
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_query_sales_today(self, client: AsyncClient):
        owner = await register_and_login(client, "Sales Query Owner", "+912004002002")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Rice", "bag")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 100.0, "bag")

        # Sold 15 bags
        await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 15 bags of rice"},
            headers=owner["headers"],
        )

        r = await client.post(
            "/api/v1/query",
            json={"shop_id": shop["id"], "query": "How much rice did we sell today?"},
            headers=owner["headers"],
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "sales_today" in data["data"]["result"]


class TestShopDashboard:

    @pytest.mark.asyncio
    async def test_dashboard_aggregates_real_values(self, client: AsyncClient):
        owner = await register_and_login(client, "Dash Owner", "+912004003001")
        shop = await create_shop_for_user(client, owner["headers"])
        p1 = await create_product_for_shop(client, owner["headers"], shop["id"], "Rice", "bag")
        p2 = await create_product_for_shop(client, owner["headers"], shop["id"], "Wheat", "kg")
        await set_baseline_for_product(client, owner["headers"], shop["id"], p1["id"], 50.0, "bag")
        await set_baseline_for_product(client, owner["headers"], shop["id"], p2["id"], 2.0, "kg")  # Low stock

        # Confirmed sale
        await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 5 bags of rice"},
            headers=owner["headers"],
        )

        # Flagged statement -> pending review
        await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 10 units of strangebrand"},
            headers=owner["headers"],
        )

        r = await client.get(f"/api/v1/dashboard?shop_id={shop['id']}", headers=owner["headers"])
        assert r.status_code == 200
        dash = r.json()["data"]
        assert dash["total_products"] == 2
        assert dash["sales_today"] == 5.0
        assert dash["pending_reviews"] == 1
        assert dash["low_stock_count"] >= 1
        assert len(dash["recent_activity"]) >= 2
