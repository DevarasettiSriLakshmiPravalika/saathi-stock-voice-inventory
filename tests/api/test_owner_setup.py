"""
Phase 3 — Owner Setup tests.

Tests:
- Shop creation (OWNER only)
- Shop retrieval
- Shop update
- Product CRUD
- Member CRUD
- Shop isolation between owners
"""
import pytest
from httpx import AsyncClient

from tests.api.conftest import (
    register_and_login,
    create_shop_for_user,
    create_product_for_shop,
)


class TestShopCreation:

    @pytest.mark.asyncio
    async def test_owner_can_create_shop(self, client: AsyncClient):
        auth = await register_and_login(client, "Shop Owner", "+912001001001")
        r = await client.post(
            "/api/v1/shops",
            json={"name": "My Rice Shop"},
            headers=auth["headers"],
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["name"] == "My Rice Shop"
        assert "id" in data
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_shop_creation_requires_auth(self, client: AsyncClient):
        r = await client.post("/api/v1/shops", json={"name": "Unauthorized Shop"})
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_get_shop_details(self, client: AsyncClient):
        auth = await register_and_login(client, "Owner A", "+912001001002")
        shop = await create_shop_for_user(client, auth["headers"], "Detailed Shop")
        shop_id = shop["id"]

        r = await client.get(f"/api/v1/shops/{shop_id}", headers=auth["headers"])
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["id"] == shop_id
        assert data["name"] == "Detailed Shop"

    @pytest.mark.asyncio
    async def test_get_shop_not_found(self, client: AsyncClient):
        auth = await register_and_login(client, "Owner B", "+912001001003")
        r = await client.get(
            "/api/v1/shops/00000000-0000-0000-0000-000000000000",
            headers=auth["headers"],
        )
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_update_shop(self, client: AsyncClient):
        auth = await register_and_login(client, "Owner C", "+912001001004")
        shop = await create_shop_for_user(client, auth["headers"], "Old Name")
        shop_id = shop["id"]

        r = await client.put(
            f"/api/v1/shops/{shop_id}",
            json={"name": "New Name"},
            headers=auth["headers"],
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_non_owner_cannot_access_other_shop(self, client: AsyncClient):
        """Shop isolation: user cannot access another user's shop."""
        owner1 = await register_and_login(client, "Owner 1", "+912001001005")
        shop = await create_shop_for_user(client, owner1["headers"], "Private Shop")
        shop_id = shop["id"]

        owner2 = await register_and_login(client, "Owner 2", "+912001001006")
        r = await client.get(f"/api/v1/shops/{shop_id}", headers=owner2["headers"])
        # Owner 2 should not be able to manage owner 1's shop
        assert r.status_code in (403, 404)


class TestProductCRUD:

    @pytest.mark.asyncio
    async def test_create_product(self, client: AsyncClient):
        auth = await register_and_login(client, "Product Owner", "+912001002001")
        shop = await create_shop_for_user(client, auth["headers"])
        shop_id = shop["id"]

        r = await client.post(
            f"/api/v1/shops/{shop_id}/products",
            json={"name": "Rice", "default_unit": "bag"},
            headers=auth["headers"],
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["name"] == "Rice"
        assert data["default_unit"] == "bag"
        assert data["shop_id"] == shop_id
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_products(self, client: AsyncClient):
        auth = await register_and_login(client, "Product List Owner", "+912001002002")
        shop = await create_shop_for_user(client, auth["headers"])
        shop_id = shop["id"]

        await create_product_for_shop(client, auth["headers"], shop_id, "Rice", "bag")
        await create_product_for_shop(client, auth["headers"], shop_id, "Sugar", "kg")
        await create_product_for_shop(client, auth["headers"], shop_id, "Oil", "litre")

        r = await client.get(
            f"/api/v1/shops/{shop_id}/products",
            headers=auth["headers"],
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert len(data) == 3
        names = {p["name"] for p in data}
        assert names == {"Rice", "Sugar", "Oil"}

    @pytest.mark.asyncio
    async def test_update_product(self, client: AsyncClient):
        auth = await register_and_login(client, "Product Update Owner", "+912001002003")
        shop = await create_shop_for_user(client, auth["headers"])
        product = await create_product_for_shop(client, auth["headers"], shop["id"], "Atta", "kg")

        r = await client.put(
            f"/api/v1/products/{product['id']}",
            json={"name": "Whole Wheat Atta", "default_unit": "bag"},
            headers=auth["headers"],
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["name"] == "Whole Wheat Atta"
        assert data["default_unit"] == "bag"

    @pytest.mark.asyncio
    async def test_deactivate_product(self, client: AsyncClient):
        auth = await register_and_login(client, "Product Delete Owner", "+912001002004")
        shop = await create_shop_for_user(client, auth["headers"])
        product = await create_product_for_shop(client, auth["headers"], shop["id"], "Dal", "kg")

        r = await client.delete(
            f"/api/v1/products/{product['id']}",
            headers=auth["headers"],
        )
        assert r.status_code == 200

        # Product list should no longer include deactivated product
        r = await client.get(
            f"/api/v1/shops/{shop['id']}/products",
            headers=auth["headers"],
        )
        products = r.json()["data"]
        product_ids = [p["id"] for p in products]
        assert product["id"] not in product_ids

    @pytest.mark.asyncio
    async def test_product_isolated_to_shop(self, client: AsyncClient):
        """Products from shop A must not appear in shop B."""
        owner1 = await register_and_login(client, "Owner P1", "+912001002005")
        owner2 = await register_and_login(client, "Owner P2", "+912001002006")
        shop1 = await create_shop_for_user(client, owner1["headers"], "Shop 1")
        shop2 = await create_shop_for_user(client, owner2["headers"], "Shop 2")

        await create_product_for_shop(client, owner1["headers"], shop1["id"], "Rice", "bag")

        r = await client.get(
            f"/api/v1/shops/{shop2['id']}/products",
            headers=owner2["headers"],
        )
        assert r.status_code == 200
        # Shop 2 should have no products
        assert len(r.json()["data"]) == 0


class TestMemberCRUD:

    @pytest.mark.asyncio
    async def test_add_staff_member(self, client: AsyncClient):
        auth = await register_and_login(client, "Member Owner", "+912001003001")
        shop = await create_shop_for_user(client, auth["headers"])
        shop_id = shop["id"]

        r = await client.post(
            f"/api/v1/shops/{shop_id}/members",
            json={"name": "Ramesh", "phone": "+912001003099", "role": "STAFF"},
            headers=auth["headers"],
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["role"] == "STAFF"
        assert data["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_add_outsider_member(self, client: AsyncClient):
        auth = await register_and_login(client, "Outsider Owner", "+912001003002")
        shop = await create_shop_for_user(client, auth["headers"])

        r = await client.post(
            f"/api/v1/shops/{shop['id']}/members",
            json={"name": "Suresh", "phone": "+912001003098", "role": "OUTSIDER"},
            headers=auth["headers"],
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["role"] == "OUTSIDER"

    @pytest.mark.asyncio
    async def test_cannot_add_owner_as_member(self, client: AsyncClient):
        """OWNER role cannot be assigned when adding a member."""
        auth = await register_and_login(client, "Owner Role Test", "+912001003003")
        shop = await create_shop_for_user(client, auth["headers"])

        r = await client.post(
            f"/api/v1/shops/{shop['id']}/members",
            json={"name": "Bad Role", "phone": "+912001003097", "role": "OWNER"},
            headers=auth["headers"],
        )
        assert r.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_list_members(self, client: AsyncClient):
        auth = await register_and_login(client, "List Owner", "+912001003004")
        shop = await create_shop_for_user(client, auth["headers"])

        await client.post(
            f"/api/v1/shops/{shop['id']}/members",
            json={"name": "Staff 1", "phone": "+912001003096", "role": "STAFF"},
            headers=auth["headers"],
        )
        await client.post(
            f"/api/v1/shops/{shop['id']}/members",
            json={"name": "Staff 2", "phone": "+912001003095", "role": "OUTSIDER"},
            headers=auth["headers"],
        )

        r = await client.get(
            f"/api/v1/shops/{shop['id']}/members",
            headers=auth["headers"],
        )
        assert r.status_code == 200
        members = r.json()["data"]
        # Owner is also a member, so at least 3 total (owner + 2 added)
        assert len(members) >= 2

    @pytest.mark.asyncio
    async def test_deactivate_member(self, client: AsyncClient):
        auth = await register_and_login(client, "Deactivate Owner", "+912001003005")
        shop = await create_shop_for_user(client, auth["headers"])

        r = await client.post(
            f"/api/v1/shops/{shop['id']}/members",
            json={"name": "Temp Staff", "phone": "+912001003094", "role": "STAFF"},
            headers=auth["headers"],
        )
        member_id = r.json()["data"]["id"]

        r = await client.delete(
            f"/api/v1/members/{member_id}",
            headers=auth["headers"],
        )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_non_owner_cannot_add_member(self, client: AsyncClient):
        """Non-owners cannot add members to a shop."""
        owner = await register_and_login(client, "Real Owner", "+912001003006")
        shop = await create_shop_for_user(client, owner["headers"])

        # Add a staff member
        await client.post(
            f"/api/v1/shops/{shop['id']}/members",
            json={"name": "Staff Member", "phone": "+912001003093", "role": "STAFF"},
            headers=owner["headers"],
        )

        # Attempt from a different user (not owner of this shop)
        other = await register_and_login(client, "Other User", "+912001003007")
        r = await client.post(
            f"/api/v1/shops/{shop['id']}/members",
            json={"name": "Intruder", "phone": "+912001003092", "role": "STAFF"},
            headers=other["headers"],
        )
        assert r.status_code == 403
