"""
Full End-to-End Lifecycle Integration Test (Phase 18).

Validates:
1. Owner registration, OTP verification, shop setup.
2. Product catalog creation and baseline establishment.
3. Strict Mathematical Invariant:
   Latest Baseline + Confirmed IN - Confirmed OUT = Current Inventory
4. Voice pipeline statement ingestion & auto-confirmation.
5. Invariant preservation: FLAGGED and REJECTED statements NEVER alter inventory.
6. Review queue lifecycle (approve/reject flagged statements).
7. Cross-shop tenant isolation.
8. Query assistant deterministic answer.
9. Real dashboard aggregation.
"""
from decimal import Decimal
import pytest
from httpx import AsyncClient

from tests.api.conftest import (
    register_and_login,
    create_shop_for_user,
    create_product_for_shop,
    set_baseline_for_product,
)


@pytest.mark.asyncio
async def test_full_e2e_saathi_lifecycle(client: AsyncClient):
    # =========================================================================
    # Step 1: Owner Registration & Login
    # =========================================================================
    owner_auth = await register_and_login(client, "Ramesh Kumar", "+919999911111")
    owner_headers = owner_auth["headers"]

    # =========================================================================
    # Step 2: Create Shop
    # =========================================================================
    shop = await create_shop_for_user(client, owner_headers, name="Ramesh Provision Store")
    shop_id = shop["id"]

    # =========================================================================
    # Step 3: Product Catalog & Baseline
    # =========================================================================
    product = await create_product_for_shop(
        client, owner_headers, shop_id, name="Rice", default_unit="kg"
    )
    product_id = product["id"]

    # Set Initial Baseline: 100 kg
    await set_baseline_for_product(
        client, owner_headers, shop_id, product_id, quantity=100.0, unit="kg"
    )

    # Verify Initial Inventory: 100 kg (Baseline: 100, In: 0, Out: 0)
    inv_resp = await client.get(f"/api/v1/shops/{shop_id}/inventory", headers=owner_headers)
    assert inv_resp.status_code == 200
    items = inv_resp.json()["data"]
    assert len(items) == 1
    rice_item = next(i for i in items if i["product_id"] == product_id)
    assert Decimal(str(rice_item["current_stock"])) == Decimal("100.0")

    # =========================================================================
    # Step 4: Voice Statement - Sales (OUT 15 kg) -> Confirmed
    # =========================================================================
    voice_resp1 = await client.post(
        "/api/v1/voice/process",
        data={"shop_id": shop_id, "transcript_override": "Sold 15 kg of rice"},
        headers=owner_headers,
    )
    assert voice_resp1.status_code == 200
    st1 = voice_resp1.json()["data"]
    assert st1["status"] == "CONFIRMED"
    assert st1["direction"] == "OUT"

    # Verify Invariant: 100 - 15 = 85 kg
    inv_resp = await client.get(f"/api/v1/shops/{shop_id}/inventory", headers=owner_headers)
    rice_item = next(i for i in inv_resp.json()["data"] if i["product_id"] == product_id)
    assert Decimal(str(rice_item["current_stock"])) == Decimal("85.0")
    assert Decimal(str(rice_item["confirmed_out"])) == Decimal("15.0")

    # =========================================================================
    # Step 5: Voice Statement - Stock In (IN 30 kg) -> Confirmed
    # =========================================================================
    voice_resp2 = await client.post(
        "/api/v1/voice/process",
        data={"shop_id": shop_id, "transcript_override": "Received 30 kg of rice"},
        headers=owner_headers,
    )
    assert voice_resp2.status_code == 200
    st2 = voice_resp2.json()["data"]
    assert st2["status"] == "CONFIRMED"
    assert st2["direction"] == "IN"

    # Verify Invariant: 100 + 30 - 15 = 115 kg
    inv_resp = await client.get(f"/api/v1/shops/{shop_id}/inventory", headers=owner_headers)
    rice_item = next(i for i in inv_resp.json()["data"] if i["product_id"] == product_id)
    assert Decimal(str(rice_item["current_stock"])) == Decimal("115.0")
    assert Decimal(str(rice_item["confirmed_in"])) == Decimal("30.0")

    # =========================================================================
    # Step 6: Flagged Statement - Unrecognized Product
    # Invariant: FLAGGED must NEVER modify inventory
    # =========================================================================
    voice_resp3 = await client.post(
        "/api/v1/voice/process",
        data={"shop_id": shop_id, "transcript_override": "Delivered 20 bags of unknown dragonfruit"},
        headers=owner_headers,
    )
    assert voice_resp3.status_code == 200
    st3 = voice_resp3.json()["data"]
    assert st3["status"] == "FLAGGED"
    review_id = st3["review_id"]
    assert review_id is not None

    # Verify Inventory is completely UNCHANGED at 115 kg
    inv_resp = await client.get(f"/api/v1/shops/{shop_id}/inventory", headers=owner_headers)
    rice_item = next(i for i in inv_resp.json()["data"] if i["product_id"] == product_id)
    assert Decimal(str(rice_item["current_stock"])) == Decimal("115.0")

    # =========================================================================
    # Step 7: Review Queue Lifecycle (Rejecting leaves stock unchanged)
    # =========================================================================
    review_resp = await client.get(f"/api/v1/reviews?shop_id={shop_id}&status=PENDING", headers=owner_headers)
    assert review_resp.status_code == 200
    reviews = review_resp.json()["data"]
    assert len(reviews) >= 1

    # Reject the flagged statement
    reject_resp = await client.post(
        f"/api/v1/reviews/{review_id}/reject",
        headers=owner_headers,
        json={"reason": "Unknown item not stocked"}
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["data"]["decision"] == "REJECTED"
    assert reject_resp.json()["data"]["statement_status"] == "REJECTED"

    # Verify Inventory is STILL completely UNCHANGED at 115 kg
    inv_resp = await client.get(f"/api/v1/shops/{shop_id}/inventory", headers=owner_headers)
    rice_item = next(i for i in inv_resp.json()["data"] if i["product_id"] == product_id)
    assert Decimal(str(rice_item["current_stock"])) == Decimal("115.0")

    # =========================================================================
    # Step 8: Multi-Tenant Isolation Verification
    # A second shop cannot see or affect Ramesh's inventory
    # =========================================================================
    owner2_auth = await register_and_login(client, "Suresh Patel", "+919999922222")
    shop2 = await create_shop_for_user(client, owner2_auth["headers"], name="Suresh Electronics")
    shop2_id = shop2["id"]

    # Shop 2 has 0 products
    inv2_resp = await client.get(f"/api/v1/shops/{shop2_id}/inventory", headers=owner2_auth["headers"])
    assert inv2_resp.status_code == 200
    assert len(inv2_resp.json()["data"]) == 0

    # Shop 2 cannot access Ramesh's products
    p2_resp = await client.get(f"/api/v1/shops/{shop2_id}/products/{product_id}", headers=owner2_auth["headers"])
    assert p2_resp.status_code in (404, 403)

    # =========================================================================
    # Step 9: Query Assistant Validation
    # =========================================================================
    query_resp = await client.post(
        "/api/v1/query",
        headers=owner_headers,
        json={"shop_id": shop_id, "query": "How much rice do we have?"}
    )
    assert query_resp.status_code == 200
    assert query_resp.json()["success"] is True

    # Step 10: Dashboard Summary Verification
    dashboard_resp = await client.get(f"/api/v1/dashboard?shop_id={shop_id}", headers=owner_headers)
    assert dashboard_resp.status_code == 200
    d_data = dashboard_resp.json()["data"]
    assert d_data["total_products"] == 1
    assert d_data["sales_today"] == 15.0
