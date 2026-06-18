import csv
import json
import random
import os
from datetime import datetime, timedelta
from itertools import groupby
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

# ── Config ──────────────────────────────────────────────────────────────
NUM_USERS    = 500
NUM_PRODUCTS = 100
NUM_ORDERS   = 3000
NUM_EVENTS   = 10000
START_DATE   = datetime(2024, 1, 1)
END_DATE     = datetime(2024, 12, 31)

OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "..", "raw_data")

CATEGORIES     = ["Electronics", "Clothing", "Home & Kitchen", "Sports", "Books", "Beauty"]
ORDER_STATUSES = ["completed", "pending", "cancelled", "refunded"]
EVENT_TYPES    = ["page_view", "product_view", "add_to_cart", "remove_from_cart", "purchase"]
CITIES         = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune"]

STATUS_WEIGHTS = [0.70, 0.15, 0.10, 0.05]
EVENT_WEIGHTS  = [0.35, 0.30, 0.18, 0.07, 0.10]


# ── Helper ──────────────────────────────────────────────────────────────
def random_date(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


# ── 1. Products ─────────────────────────────────────────────────────────
def generate_products():
    products = []
    for i in range(1, NUM_PRODUCTS + 1):
        products.append({
            "product_id": f"PROD_{i:04d}",
            "name":       fake.bs().title()[:60],
            "category":   random.choice(CATEGORIES),
            "price":      round(random.uniform(5.0, 999.99), 2),
            "stock":      random.randint(0, 500),
            "is_active":  random.choice([True, True, True, False]),
            "created_at": START_DATE.strftime("%Y-%m-%d"),
        })

    path = os.path.join(OUTPUT_DIR, "products", "products.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=products[0].keys())
        writer.writeheader()
        writer.writerows(products)

    print(f"products.csv -> {NUM_PRODUCTS} rows")
    return {p["product_id"]: p for p in products}


# ── 2. Users ────────────────────────────────────────────────────────────
def generate_users():
    users = []
    for i in range(1, NUM_USERS + 1):
        users.append({
            "user_id":     f"USR_{i:05d}",
            "name":        fake.name(),
            "email":       fake.unique.email(),
            "city":        random.choice(CITIES),
            "signup_date": random_date(START_DATE, END_DATE).strftime("%Y-%m-%d"),
            "segment":     random.choice(["new", "returning", "vip", "churned"]),
            "is_verified": random.choice([True, False]),
            "age":         random.randint(18, 65),
        })

    path = os.path.join(OUTPUT_DIR, "users", "users.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(users, f, indent=2)

    print(f"users.json -> {NUM_USERS} rows")
    return {u["user_id"]: u for u in users}


# ── 3. Orders ───────────────────────────────────────────────────────────
def generate_orders(users, products):
    user_ids    = list(users.keys())
    product_ids = list(products.keys())
    orders      = []
    order_items = []

    for i in range(1, NUM_ORDERS + 1):
        order_date  = random_date(START_DATE, END_DATE)
        user_id     = random.choice(user_ids)
        status      = random.choices(ORDER_STATUSES, weights=STATUS_WEIGHTS)[0]
        num_items   = random.randint(1, 5)
        order_total = 0.0
        line_items  = []

        for _ in range(num_items):
            pid      = random.choice(product_ids)
            qty      = random.randint(1, 4)
            price    = products[pid]["price"]
            subtotal = round(qty * price, 2)
            order_total += subtotal
            line_items.append({
                "order_id":   f"ORD_{i:06d}",
                "product_id": pid,
                "quantity":   qty,
                "unit_price": price,
                "subtotal":   subtotal,
            })

        orders.append({
            "order_id":       f"ORD_{i:06d}",
            "user_id":        user_id,
            "status":         status,
            "order_total":    round(order_total, 2),
            "num_items":      num_items,
            "payment_method": random.choice(["credit_card", "upi", "net_banking", "wallet"]),
            "created_at":     order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at":     (order_date + timedelta(hours=random.randint(1, 48))).strftime("%Y-%m-%d %H:%M:%S"),
        })
        order_items.extend(line_items)

    # partition orders by month — mirrors real S3 layout
    orders_sorted = sorted(orders, key=lambda x: x["created_at"][:7])
    for month, grp in groupby(orders_sorted, key=lambda x: x["created_at"][:7]):
        rows   = list(grp)
        yr, mo = month.split("-")
        path   = os.path.join(OUTPUT_DIR, "orders", f"year={yr}", f"month={mo}", "orders.csv")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    # order_items saved as one flat file
    items_path = os.path.join(OUTPUT_DIR, "orders", "order_items.csv")
    with open(items_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=order_items[0].keys())
        writer.writeheader()
        writer.writerows(order_items)

    print(f"orders.csv -> {NUM_ORDERS} orders, {len(order_items)} line items")
    return {o["order_id"]: o for o in orders}


# ── 4. Events ───────────────────────────────────────────────────────────
def generate_events(users, products, orders):
    user_ids    = list(users.keys())
    product_ids = list(products.keys())
    order_ids   = list(orders.keys())
    events      = []

    for i in range(1, NUM_EVENTS + 1):
        evt_type = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS)[0]
        evt_time = random_date(START_DATE, END_DATE)

        events.append({
            "event_id":   f"EVT_{i:07d}",
            "user_id":    random.choice(user_ids),
            "event_type": evt_type,
            "product_id": random.choice(product_ids) if evt_type != "page_view" else None,
            "order_id":   random.choice(order_ids)   if evt_type == "purchase"  else None,
            "session_id": fake.uuid4()[:8],
            "device":     random.choice(["mobile", "desktop", "tablet"]),
            "timestamp":  evt_time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    path = os.path.join(OUTPUT_DIR, "events", "events.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(events, f, indent=2)

    print(f"events.json -> {NUM_EVENTS} rows")


# ── Main ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nGenerating e-commerce data...\n")
    products = generate_products()
    users    = generate_users()
    orders   = generate_orders(users, products)
    generate_events(users, products, orders)
