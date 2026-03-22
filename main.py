from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# -------------------------------
# Fashion Products Data
# -------------------------------
products = [
    {"id": 1, "name": "T-Shirt", "price": 499, "category": "Men", "in_stock": True},
    {"id": 2, "name": "Jeans", "price": 1299, "category": "Men", "in_stock": True},
    {"id": 3, "name": "Dress", "price": 1999, "category": "Women", "in_stock": True},
    {"id": 4, "name": "Jacket", "price": 2499, "category": "Women", "in_stock": True}
]

cart = []
orders = []
order_counter = 1

# -------------------------------
# Models
# -------------------------------
class Product(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool

class Checkout(BaseModel):
    customer_name: str
    delivery_address: str

# -------------------------------
# Helper Functions
# -------------------------------
def find_product(product_id):
    return next((p for p in products if p["id"] == product_id), None)

def calculate_total(price, quantity):
    return price * quantity

# -------------------------------
# Basic APIs
# -------------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Fashion Store API"}

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

# -------------------------------
# Extra APIs (MUST COME BEFORE dynamic)
# -------------------------------
@app.get("/products/category/{category}")
def get_by_category(category: str):
    result = [p for p in products if p["category"].lower() == category.lower()]
    return {"products": result}

@app.get("/products/instock")
def get_instock():
    result = [p for p in products if p["in_stock"]]
    return {"products": result}

@app.get("/products/summary")
def product_summary():
    total = len(products)
    in_stock = len([p for p in products if p["in_stock"]])
    out_stock = total - in_stock

    return {
        "total_products": total,
        "in_stock": in_stock,
        "out_of_stock": out_stock
    }

# -------------------------------
# Search / Filter / Sort / Pagination
# -------------------------------
@app.get("/products/search")
def search_products(keyword: str):
    result = [p for p in products if keyword.lower() in p["name"].lower()]
    return {"results": result}

@app.get("/products/filter")
def filter_products(min_price: int = None, max_price: int = None):
    result = products
    if min_price:
        result = [p for p in result if p["price"] >= min_price]
    if max_price:
        result = [p for p in result if p["price"] <= max_price]
    return result

@app.get("/products/sort")
def sort_products(sort_by: str = "price", order: str = "asc"):
    reverse = True if order == "desc" else False
    return sorted(products, key=lambda x: x[sort_by], reverse=reverse)

@app.get("/products/page")
def paginate_products(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    end = start + limit
    return {"page": page, "products": products[start:end]}

@app.get("/products/browse")
def browse_products(keyword: Optional[str] = None, page: int = 1, limit: int = 2):
    result = products

    if keyword:
        result = [p for p in result if keyword.lower() in p["name"].lower()]

    start = (page - 1) * limit
    end = start + limit

    return {
        "total": len(result),
        "products": result[start:end]
    }

# -------------------------------
# Product by ID (KEEP THIS LAST among product routes)
# -------------------------------
@app.get("/products/{product_id}")
def get_product(product_id: int):
    product = find_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# -------------------------------
# CRUD Operations
# -------------------------------
@app.post("/products")
def add_product(product: Product):
    new_product = product.dict()
    new_product["id"] = len(products) + 1
    products.append(new_product)
    return new_product

@app.put("/products/{product_id}")
def update_product(product_id: int, price: int = None, in_stock: bool = None):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if price is not None:
        product["price"] = price
    if in_stock is not None:
        product["in_stock"] = in_stock

    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    products.remove(product)
    return {"message": "Product deleted"}

# -------------------------------
# Cart APIs
# -------------------------------
@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int = 1):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail="Product out of stock")

    subtotal = calculate_total(product["price"], quantity)

    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "subtotal": subtotal
    }

    cart.append(cart_item)
    return {"message": "Added to cart", "item": cart_item}

@app.get("/cart")
def view_cart():
    total = sum(item["subtotal"] for item in cart)
    return {"cart": cart, "total_amount": total}

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):
    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": "Item removed"}

    raise HTTPException(status_code=404, detail="Item not found in cart")

@app.post("/cart/checkout")
def checkout(data: Checkout):
    global order_counter

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    placed_orders = []

    for item in cart:
        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total": item["subtotal"],
            "address": data.delivery_address
        }
        orders.append(order)
        placed_orders.append(order)
        order_counter += 1

    cart.clear()

    return {
        "message": "Order placed successfully",
        "orders": placed_orders
    }

# -------------------------------
# Orders APIs
# -------------------------------
@app.get("/orders")
def get_orders():
    return {"orders": orders}

@app.get("/orders/search")
def search_orders(customer_name: str):
    result = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    return {"results": result}
