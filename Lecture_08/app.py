import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "instance" / "products.db"


def connect_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


@app.get("/api/v1/products")
def list_products():
    # Validate pagination before querying the database.
    try:
        page = int(request.args.get("page", "1"))
        per_page = int(request.args.get("per_page", "10"))
    except ValueError:
        return jsonify(
            code="VALIDATION_ERROR",
            message="page and per_page must be integers",
        ), 400

    if page < 1 or not 1 <= per_page <= 100:
        return jsonify(
            code="VALIDATION_ERROR",
            message="page must be >= 1; per_page must be between 1 and 100",
        ), 400

    category = request.args.get("category")
    where = ""
    parameters = []

    if category is not None:
        where = " WHERE category = ?"
        parameters.append(category)

    connection = connect_db()

    try:
        total = connection.execute(
            "SELECT COUNT(*) FROM products" + where,
            parameters,
        ).fetchone()[0]

        rows = connection.execute(
            "SELECT id, name, category, price_cents FROM products"
            + where
            + " ORDER BY id LIMIT ? OFFSET ?",
            parameters + [per_page, (page - 1) * per_page],
        ).fetchall()

        return jsonify(
            items=[dict(row) for row in rows],
            page=page,
            per_page=per_page,
            total=total,
        )
    finally:
        connection.close()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)