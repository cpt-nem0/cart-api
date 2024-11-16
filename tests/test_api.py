from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from server.api import app
from server.store import store

client = TestClient(app)


@pytest.fixture
def reset_store():
    """Reset store to initial state before each test"""
    store.__init__()
    yield store


def test_get_products(reset_store):
    """Test listing all products"""
    response = client.get("/products")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 3
    assert products[0]["name"] == "Product 1"
    assert products[0]["price"] == 999.99


def test_add_to_cart(reset_store):
    """Test adding items to cart"""
    # Add new item
    response = client.post("/cart/user1/add", json={"product_id": 1, "quantity": 2})
    assert response.status_code == 200
    assert response.json()["message"] == "Item added to cart"

    # Check cart
    response = client.get("/cart/user1")
    assert response.status_code == 200
    cart = response.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2
    assert cart["total"] == 999.99 * 2


def test_add_invalid_product_to_cart(reset_store):
    """Test adding non-existent product to cart"""
    response = client.post("/cart/user1/add", json={"product_id": 999, "quantity": 1})
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_add_existing_product_to_cart(reset_store):
    """Test adding same product multiple times"""
    # Add product first time
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 2})

    # Add same product second time
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 3})

    response = client.get("/cart/user1")
    assert response.status_code == 200
    cart = response.json()
    assert cart["items"][0]["quantity"] == 5
    assert cart["total"] == 999.99 * 5


def test_empty_cart(reset_store):
    """Test getting empty cart"""
    response = client.get("/cart/newuser")
    assert response.status_code == 200
    cart = response.json()
    assert cart["items"] == []
    assert cart["total"] == 0


def test_checkout_empty_cart(reset_store):
    """Test checkout with empty cart"""
    response = client.post("/checkout/newuser")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"


def test_successful_checkout(reset_store):
    """Test successful checkout process"""
    # Add items to cart
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 2})

    # Checkout
    response = client.post("/checkout/user1")
    assert response.status_code == 200
    order = response.json()
    assert order["user_id"] == "user1"
    assert order["total_amount"] == 999.99 * 2
    assert order["final_amount"] == 999.99 * 2
    assert UUID(order["id"])  # Validates UUID format

    # Verify cart is empty after checkout
    cart_response = client.get("/cart/user1")
    assert cart_response.json()["items"] == []


def test_discount_code_generation(reset_store):
    """Test discount code generation every nth order"""
    # Complete n-1 orders
    for _ in range(store.nth_order - 1):
        client.post("/cart/user1/add", json={"product_id": 1, "quantity": 1})
        client.post("/checkout/user1")

    # Get current discount codes
    response = client.get("/admin/discount-codes")
    initial_codes = response.json()

    # Complete nth order
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 1})
    client.post("/checkout/user1")

    # Check new discount code was generated
    response = client.get("/admin/discount-codes")
    new_codes = response.json()
    assert len(new_codes) == len(initial_codes) + 1


def test_checkout_with_discount(reset_store):
    """Test checkout process with valid discount code"""
    # Generate a discount code
    store.discount_codes["TEST10"] = 10.0

    # Add items to cart
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 1})

    # Checkout with discount
    response = client.post("/checkout/user1?discount_code=TEST10")
    assert response.status_code == 200
    order = response.json()
    assert order["discount_code"] == "TEST10"
    assert order["total_amount"] == 999.99
    assert order["final_amount"] == 899.991  # 10% off


def test_checkout_with_invalid_discount(reset_store):
    """Test checkout process with invalid discount code"""
    # Add items to cart
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 1})

    # Checkout with invalid discount
    response = client.post("/checkout/user1?discount_code=INVALID")
    assert response.status_code == 200
    order = response.json()
    assert order["discount_code"] is None
    assert order["total_amount"] == order["final_amount"]


def test_admin_stats(reset_store):
    """Test administrative statistics"""
    # Complete some orders
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 2})
    client.post("/checkout/user1")

    store.discount_codes["TEST10"] = 10.0
    client.post("/cart/user2/add", json={"product_id": 2, "quantity": 1})
    client.post("/checkout/user2?discount_code=TEST10")

    response = client.get("/admin/stats")
    assert response.status_code == 200
    stats = response.json()

    assert stats["total_items_sold"] == 3
    assert stats["total_purchase_amount"] == (999.99 * 2) + 499.99
    assert len(stats["discount_codes"]) == 1
    assert stats["total_discount_amount"] == pytest.approx(49.999, rel=1e-3)


def test_multiple_products_in_cart(reset_store):
    """Test cart with multiple different products"""
    # Add multiple products
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 1})
    client.post("/cart/user1/add", json={"product_id": 2, "quantity": 2})
    client.post("/cart/user1/add", json={"product_id": 3, "quantity": 3})

    response = client.get("/cart/user1")
    cart = response.json()

    assert len(cart["items"]) == 3
    assert cart["total"] == 999.99 + (499.99 * 2) + (99.99 * 3)


# Integration Tests


def test_complete_shopping_flow(reset_store):
    """Test complete shopping flow from browsing to checkout"""
    # 1. Browse products
    products_response = client.get("/products")
    assert products_response.status_code == 200
    products = products_response.json()

    # 2. Add items to cart
    for product in products[:2]:  # Add first two products
        client.post(
            "/cart/user1/add", json={"product_id": product["id"], "quantity": 1}
        )

    # 3. View cart
    cart_response = client.get("/cart/user1")
    assert cart_response.status_code == 200
    cart = cart_response.json()
    assert len(cart["items"]) == 2

    # 4. Checkout
    checkout_response = client.post("/checkout/user1")
    assert checkout_response.status_code == 200
    order = checkout_response.json()

    # 5. Verify order details
    assert len(order["items"]) == 2
    assert order["total_amount"] == 999.99 + 499.99

    # 6. Check admin stats
    stats_response = client.get("/admin/stats")
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["total_items_sold"] == 2
    assert stats["total_purchase_amount"] == 999.99 + 499.99


def test_concurrent_carts(reset_store):
    """Test multiple users with active carts"""
    # User 1 adds items
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 1})

    # User 2 adds items
    client.post("/cart/user2/add", json={"product_id": 2, "quantity": 1})

    # Check User 1's cart
    response1 = client.get("/cart/user1")
    cart1 = response1.json()
    assert len(cart1["items"]) == 1
    assert cart1["items"][0]["product_id"] == 1

    # Check User 2's cart
    response2 = client.get("/cart/user2")
    cart2 = response2.json()
    assert len(cart2["items"]) == 1
    assert cart2["items"][0]["product_id"] == 2


# Negative Test Cases


def test_invalid_quantity(reset_store):
    """Test adding item with invalid quantity"""
    response = client.post("/cart/user1/add", json={"product_id": 1, "quantity": 0})
    assert response.status_code == 422  # Validation Error


def test_checkout_after_cart_modification(reset_store):
    """Test checkout process after cart modifications"""
    # Add item
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 2})

    # Modify quantity
    client.post("/cart/user1/add", json={"product_id": 1, "quantity": 1})

    # Checkout
    response = client.post("/checkout/user1")
    assert response.status_code == 200
    order = response.json()
    assert order["items"][0]["quantity"] == 3
