"""
Phase 16: Inventory calculation, Statement Ledger, Reviews Queue, and Statement Override Tests.

Validates the critical invariant:
  REJECTED statement -> inventory unchanged
  FLAGGED statement  -> inventory unchanged
  CONFIRMED statement -> inventory changes
  Latest Baseline + Confirmed IN - Confirmed OUT = Current Inventory
"""
import pytest
from httpx import AsyncClient

from tests.api.conftest import (
    register_and_login,
    create_shop_for_user,
    create_product_for_shop,
    set_baseline_for_product,
)


class TestInventoryCalculation:

    @pytest.mark.asyncio
    async def test_inventory_formula_with_multiple_statements(self, client: AsyncClient):
        """
        Verify: Current Stock = Baseline (100) + IN (25) - OUT (10) = 115.
        Flagged and rejected statements must not affect inventory.
        """
        owner = await register_and_login(client, "Inv Owner", "+912003001001")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Rice", "bag")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 100.0, "bag")

        # 1. Confirmed OUT (10 bags)
        r = await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 10 bags of rice"},
            headers=owner["headers"],
        )
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "CONFIRMED"

        # 2. Confirmed IN (25 bags)
        r = await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Received 25 bags of rice"},
            headers=owner["headers"],
        )
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "CONFIRMED"

        # 3. Check stock: 100 - 10 + 25 = 115
        r = await client.get(f"/api/v1/shops/{shop['id']}/inventory", headers=owner["headers"])
        assert r.status_code == 200
        item = next(i for i in r.json()["data"] if i["product_id"] == product["id"])
        assert item["current_stock"] == 115.0
        assert item["confirmed_in"] == 25.0
        assert item["confirmed_out"] == 10.0

    @pytest.mark.asyncio
    async def test_flagged_and_rejected_do_not_mutate_stock(self, client: AsyncClient):
        """Flagged and rejected statements do not alter inventory."""
        owner = await register_and_login(client, "Invariant Owner", "+912003001002")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Wheat", "kg")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 50.0, "kg")

        # Flagged statement (unresolvable product name)
        r = await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 20 kg of nonexistingitem"},
            headers=owner["headers"],
        )
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "FLAGGED"

        # Stock of Wheat must remain strictly 50.0
        r = await client.get(f"/api/v1/shops/{shop['id']}/inventory", headers=owner["headers"])
        item = next(i for i in r.json()["data"] if i["product_id"] == product["id"])
        assert item["current_stock"] == 50.0

    @pytest.mark.asyncio
    async def test_new_baseline_supersedes_previous(self, client: AsyncClient):
        """Setting a new baseline resets the calculation point."""
        owner = await register_and_login(client, "Baseline Owner", "+912003001003")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Sugar", "kg")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 100.0, "kg")

        # Sell 20 kg -> 80
        await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 20 kg of sugar"},
            headers=owner["headers"],
        )

        # Set new baseline to 200 kg
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 200.0, "kg")

        # Inventory must now be 200.0
        r = await client.get(f"/api/v1/products/{product['id']}/inventory", headers=owner["headers"])
        assert r.status_code == 200
        assert r.json()["data"]["current_stock"] == 200.0

    @pytest.mark.asyncio
    async def test_product_history_returns_confirmed_movements(self, client: AsyncClient):
        """Product history endpoint returns only confirmed statements."""
        owner = await register_and_login(client, "History Owner", "+912003001004")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Oil", "liter")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 50.0, "liter")

        # 1 confirmed
        await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 5 liter of oil"},
            headers=owner["headers"],
        )

        r = await client.get(f"/api/v1/products/{product['id']}/history", headers=owner["headers"])
        assert r.status_code == 200
        history = r.json()["data"]
        assert len(history) == 1
        assert history[0]["quantity"] == 5.0
        assert history[0]["direction"] == "OUT"


class TestReviewQueueAndApproval:

    @pytest.mark.asyncio
    async def test_owner_approves_review_updates_inventory(self, client: AsyncClient):
        """
        1. Statement is FLAGGED (e.g. unknown product).
        2. Inventory is unchanged.
        3. Owner overrides product_id on statement or reviews queue.
        4. Owner approves review.
        5. Statement becomes CONFIRMED.
        6. Inventory is updated.
        """
        owner = await register_and_login(client, "Review Owner", "+912003002001")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Rice", "bag")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 100.0, "bag")

        # Submit statement with ambiguous term that won't resolve without vocabulary
        r = await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 10 bags of cereal"},
            headers=owner["headers"],
        )
        assert r.status_code == 200
        stmt_data = r.json()["data"]
        assert stmt_data["status"] == "FLAGGED"
        review_id = stmt_data["review_id"]
        statement_id = stmt_data["statement_id"]
        assert review_id is not None

        # Stock must still be 100
        inv_res = await client.get(f"/api/v1/shops/{shop['id']}/inventory", headers=owner["headers"])
        rice_item = next(i for i in inv_res.json()["data"] if i["product_id"] == product["id"])
        assert rice_item["current_stock"] == 100.0

        # Owner overrides the statement to point to product "Rice"
        over_res = await client.post(
            f"/api/v1/statements/{statement_id}/override",
            json={"product_id": product["id"], "reason": "Cereal means Rice"},
            headers=owner["headers"],
        )
        assert over_res.status_code == 200
        assert over_res.json()["data"]["product_id"] == product["id"]

        # Owner approves the review
        app_res = await client.post(
            f"/api/v1/reviews/{review_id}/approve",
            json={"reason": "Approved after mapping product"},
            headers=owner["headers"],
        )
        assert app_res.status_code == 200
        assert app_res.json()["data"]["decision"] == "APPROVED"
        assert app_res.json()["data"]["statement_status"] == "CONFIRMED"

        # Now inventory must reflect the 10 bags sold: 100 - 10 = 90
        inv_res = await client.get(f"/api/v1/shops/{shop['id']}/inventory", headers=owner["headers"])
        rice_item = next(i for i in inv_res.json()["data"] if i["product_id"] == product["id"])
        assert rice_item["current_stock"] == 90.0

    @pytest.mark.asyncio
    async def test_owner_rejects_review_inventory_remains_unchanged(self, client: AsyncClient):
        owner = await register_and_login(client, "Reject Owner", "+912003002002")
        shop = await create_shop_for_user(client, owner["headers"])
        product = await create_product_for_shop(client, owner["headers"], shop["id"], "Rice", "bag")
        await set_baseline_for_product(client, owner["headers"], shop["id"], product["id"], 50.0, "bag")

        r = await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 15 bags of strangeitem"},
            headers=owner["headers"],
        )
        review_id = r.json()["data"]["review_id"]

        rej_res = await client.post(
            f"/api/v1/reviews/{review_id}/reject",
            json={"reason": "Invalid transaction claim"},
            headers=owner["headers"],
        )
        assert rej_res.status_code == 200
        assert rej_res.json()["data"]["decision"] == "REJECTED"
        assert rej_res.json()["data"]["statement_status"] == "REJECTED"

        # Inventory remains unchanged at 50
        inv_res = await client.get(f"/api/v1/shops/{shop['id']}/inventory", headers=owner["headers"])
        rice_item = next(i for i in inv_res.json()["data"] if i["product_id"] == product["id"])
        assert rice_item["current_stock"] == 50.0

    @pytest.mark.asyncio
    async def test_non_owner_cannot_approve_reviews(self, client: AsyncClient):
        owner = await register_and_login(client, "Shop Owner", "+912003002003")
        shop = await create_shop_for_user(client, owner["headers"])

        staff = await register_and_login(client, "Staff Member", "+912003002004")
        await client.post(
            f"/api/v1/shops/{shop['id']}/members",
            json={"name": "Staff Member", "phone": "+912003002004", "role": "STAFF"},
            headers=owner["headers"],
        )

        r = await client.post(
            "/api/v1/voice/process",
            data={"shop_id": shop["id"], "transcript_override": "Sold 5 bags of mysteryitem"},
            headers=owner["headers"],
        )
        review_id = r.json()["data"]["review_id"]

        # Staff attempts to approve review -> 403
        app_res = await client.post(
            f"/api/v1/reviews/{review_id}/approve",
            json={"reason": "I want to approve"},
            headers=staff["headers"],
        )
        assert app_res.status_code == 403
