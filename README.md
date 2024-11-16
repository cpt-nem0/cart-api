# E-commerce API Documentation

A FastAPI-based e-commerce backend API that handles products, shopping carts, orders, and discount codes.

## Table of Contents
- [Setup](#setup)
- [Data Models](#data-models)
- [API Endpoints](#api-endpoints)
- [Examples](#examples)
- [Error Handling](#error-handling)

## Setup

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ecommerce-api
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install fastapi uvicorn
```

4. Run the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8123`, and the interactive documentation (Swagger UI) at `http://localhost:8123/docs`.

## Data Models

### Product
```python
{
    "id": int,
    "name": str,
    "price": float
}
```

### CartItem
```python
{
    "product_id": int,
    "quantity": int  # Must be greater than 0
}
```

### Order
```python
{
    "id": UUID,
    "user_id": str,
    "items": List[CartItem],
    "total_amount": float,
    "discount_code": str | None,
    "final_amount": float,
    "created_at": datetime
}
```

### AdminStats
```python
{
    "total_items_sold": int,
    "total_purchase_amount": float,
    "discount_codes": List[str],
    "total_discount_amount": float
}
```

## API Endpoints

### Products

#### GET `/products`
Returns a list of all available products.

**Response**: `List[Product]`
```json
[
    {
        "id": 1,
        "name": "Laptop",
        "price": 999.99
    },
    ...
]
```

### Cart Operations

#### POST `/cart/{user_id}/add`
Add an item to user's shopping cart.

**Parameters**:
- `user_id`: string (path parameter)
- Request body: CartItem

**Example Request**:
```json
{
    "product_id": 1,
    "quantity": 2
}
```

**Response**:
```json
{
    "message": "Item added to cart"
}
```

#### GET `/cart/{user_id}`
Retrieve the contents and total amount of a user's cart.

**Parameters**:
- `user_id`: string (path parameter)

**Response**:
```json
{
    "items": [
        {
            "product_id": 1,
            "quantity": 2
        }
    ],
    "total": 1999.98
}
```

### Checkout

#### POST `/checkout/{user_id}`
Process checkout for a user's cart.

**Parameters**:
- `user_id`: string (path parameter)
- `discount_code`: string (optional query parameter)

**Response**: Order object
```json
{
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "user123",
    "items": [...],
    "total_amount": 1999.98,
    "discount_code": "DISCOUNT1234",
    "final_amount": 1799.98,
    "created_at": "2024-11-16T10:30:00"
}
```

### Admin Endpoints

> :warning: Admin endpoints are protected with Bearer token authentication, use `Bearer super-secret-token` for accessing them

#### GET `/admin/stats`
Retrieve administrative statistics.

**Response**: AdminStats object
```json
{
    "total_items_sold": 10,
    "total_purchase_amount": 5999.94,
    "discount_codes": ["DISCOUNT1234", "DISCOUNT5678"],
    "total_discount_amount": 599.99
}
```

#### GET `/admin/discount-codes`
List all valid discount codes.

**Response**: List of strings
```json
["DISCOUNT1234", "DISCOUNT5678"]
```

## Examples

### Complete Purchase Flow

1. View available products:
```bash
curl http://localhost:8123/products
```

2. Add item to cart:
```bash
curl -X POST http://localhost:8123/cart/user123/add \
    -H "Content-Type: application/json" \
    -d '{"product_id": 1, "quantity": 2}'
```

3. View cart:
```bash
curl http://localhost:8123/cart/user123
```

4. Checkout with discount:
```bash
curl -X POST "http://localhost:8123/cart/user123/checkout?discount_code=DISCOUNT1234"
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Successful operation
- `400`: Bad request (e.g., invalid input, empty cart)
- `404`: Resource not found (e.g., invalid product ID)
- `422`: Validation error (e.g., invalid data format)
- `401`: Unauthorized access for admin endpoints

Error responses include a detail message:
```json
{
    "detail": "Product not found"
}
```

## Business Rules

1. Discount Code Generation:
   - A new discount code is automatically generated every nth order (default: 3)
   - All discount codes provide a 10% discount
   - Discount codes can be used only once

2. Cart Management:
   - If adding an existing product to cart, quantity is updated
   - Cart is cleared after successful checkout
   - Products must exist in the store to be added to cart

3. Order Processing:
   - Orders are stored with unique UUIDs
   - Discount codes are validated before applying
   - Final amount is calculated after applying valid discounts

## Testing

Access the interactive API documentation at `http://localhost:8123/docs` to test all endpoints directly in your browser.

For automated testing, we recommend using pytest. Example test cases will be provided in the `tests/` directory.

## Security Considerations

This is a basic implementation focusing on functionality. In a production environment, you should add:

1. Authentication and authorization
2. Input validation and sanitization
3. Rate limiting
4. HTTPS encryption
5. Proper session management
6. Error logging
7. Database persistence

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE.md file for details