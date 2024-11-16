import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class Product(BaseModel):
    id: int
    name: str
    price: float


class Order(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID
    user_id: str
    items: List[CartItem]
    total_amount: float
    discount_code: Optional[str] = None
    final_amount: float
    created_at: datetime


class AdminStats(BaseModel):
    total_items_sold: int
    total_purchase_amount: float
    discount_codes: List[str]
    total_discount_amount: float
