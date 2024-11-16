from typing import Dict, List

from server.models import CartItem, Order, Product


class Store:
    def __init__(self):
        self.products: Dict[int, Product] = {
            1: Product(id=1, name="Product 1", price=999.99),
            2: Product(id=2, name="Product 2", price=499.99),
            3: Product(id=3, name="Product 3", price=99.99),
        }
        self.carts: Dict[str, List[CartItem]] = {}  # user_id -> cart_items
        self.orders: List[Order] = []
        self.discount_codes: Dict[str, float] = {}  # code -> discount_percentage
        self.order_count = 0
        self.nth_order = 10


store = Store()
