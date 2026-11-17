import sqlite3

from app import DATABASE

DATABASE.parent.mkdir(parents=True, exist_ok=True)

categories = ["electronics", "books", "clothing", "home"]

products = [
    (
        i,
        f"Product {i:04d}",
        categories[(i - 1) % len(categories)],
        1000 + i * 25,
    )
    for i in range(1, 1001)
]

connection = sqlite3.connect(DATABASE)

try:
    with connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price_cents INTEGER NOT NULL CHECK (price_cents >= 0)
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_category_id
            ON products(category, id)
        """)

        connection.executemany(
            """
            INSERT OR IGNORE INTO products
                (id, name, category, price_cents)
            VALUES (?, ?, ?, ?)
            """,
            products,
        )

    print("Database ready: 1,000 sample product IDs seeded.")
finally:
    connection.close()