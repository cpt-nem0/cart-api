import random
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from server.models import AdminStats, CartItem, Order, Product
from server.store import store

app = FastAPI(title="E-commerce API")
security = HTTPBearer()

SUPER_SECRET_TOKEN = "super-secret-token"


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.scheme != "Bearer" or credentials.credentials != SUPER_SECRET_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


@app.get("/products", response_model=List[Product])
async def get_products():
    """Get all available products"""
    return list(store.products.values())


@app.post("/cart/{user_id}/add")
async def add_to_cart(user_id: str, item: CartItem):
    """Add an item to user's cart"""
    if item.product_id not in store.products:
        raise HTTPException(status_code=404, detail="Product not found")

    if user_id not in store.carts:
        store.carts[user_id] = []

    # Check if product already in cart
    for cart_item in store.carts[user_id]:
        if cart_item.product_id == item.product_id:
            cart_item.quantity += item.quantity
            break
    else:
        store.carts[user_id].append(item)

    return {"message": "Item added to cart"}


@app.get("/cart/{user_id}")
async def get_cart(user_id: str):
    """Get user's cart with total amount"""
    if user_id not in store.carts:
        return {"items": [], "total": 0}

    items = store.carts[user_id]
    total = sum(store.products[item.product_id].price * item.quantity for item in items)

    return {"items": items, "total": total}


@app.post("/checkout/{user_id}")
async def checkout(user_id: str, discount_code: Optional[str] = None):
    """Process checkout and create order"""
    if user_id not in store.carts or not store.carts[user_id]:
        raise HTTPException(status_code=400, detail="Cart is empty")

    cart_items = store.carts[user_id]
    total_amount = sum(
        store.products[item.product_id].price * item.quantity for item in cart_items
    )

    # Apply discount if valid
    discount_amount = 0
    if discount_code and discount_code in store.discount_codes:
        discount_amount = total_amount * (store.discount_codes[discount_code] / 100)
        final_amount = total_amount - discount_amount
    else:
        final_amount = total_amount

    # Create order
    order = Order(
        id=uuid4(),
        user_id=user_id,
        items=cart_items,
        total_amount=total_amount,
        discount_code=discount_code if discount_code in store.discount_codes else None,
        final_amount=final_amount,
        created_at=datetime.now(),
    )

    store.orders.append(order)
    store.order_count += 1

    # Clear cart
    store.carts[user_id] = []

    # Generate new discount code if nth order
    if store.order_count % store.nth_order == 0:
        new_code = f"DISCOUNT{random.randint(1000, 9999)}-{int(store.order_count//store.nth_order) if store.nth_order else 0}"
        store.discount_codes[new_code] = 10.0

    return order


@app.get(
    "/admin/stats",
    response_model=AdminStats,
    dependencies=[Depends(verify_admin_token)],
)
async def get_admin_stats():
    """Get administrative statistics"""
    total_items = sum(
        sum(item.quantity for item in order.items) for order in store.orders
    )

    total_purchase = sum(order.total_amount for order in store.orders)

    total_discount = sum(
        order.total_amount - order.final_amount
        for order in store.orders
        if order.discount_code
    )

    return AdminStats(
        total_items_sold=total_items,
        total_purchase_amount=total_purchase,
        discount_codes=list(store.discount_codes.keys()),
        total_discount_amount=total_discount,
    )


@app.get("/admin/discount-codes", dependencies=[Depends(verify_admin_token)])
async def get_discount_codes():
    """Get all valid discount codes"""
    return list(store.discount_codes.keys())
