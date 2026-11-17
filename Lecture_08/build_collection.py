import json
from pathlib import Path

folder = Path("postman")
folder.mkdir(exist_ok=True)

cases = [
    (
        "Default listing",
        "",
        200,
        [
            "pm.expect(body.total).to.eql(1000);",
            "pm.expect(body.items).to.have.lengthOf(10);",
            "pm.expect(body.page).to.eql(1);",
            "pm.expect(body.per_page).to.eql(10);",
            "pm.expect(body.items[0]).to.have.all.keys("
            "'id', 'name', 'category', 'price_cents');",
            "pm.expect(body.items[0].price_cents).to.be.a('number');",
        ],
    ),
    (
        "Filter electronics",
        "?category=electronics&per_page=5",
        200,
        [
            "pm.expect(body.total).to.eql(250);",
            "pm.expect(body.items).to.have.lengthOf(5);",
            "body.items.forEach(p => "
            "pm.expect(p.category).to.eql('electronics'));",
        ],
    ),
    (
        "Second page",
        "?page=2&per_page=10",
        200,
        [
            "pm.expect(body.page).to.eql(2);",
            "pm.expect(body.items).to.have.lengthOf(10);",
            "pm.expect(body.items[0].id).to.eql(11);",
            "pm.expect(body.items[9].id).to.eql(20);",
        ],
    ),
    (
        "Unknown category",
        "?category=nonexistent",
        200,
        [
            "pm.expect(body.total).to.eql(0);",
            "pm.expect(body.items).to.eql([]);",
        ],
    ),
    (
        "Reject page zero",
        "?page=0",
        400,
        [
            "pm.expect(body.code).to.eql('VALIDATION_ERROR');",
            "pm.expect(body.message).to.include('page');",
        ],
    ),
    (
        "Reject non-integer page",
        "?page=abc",
        400,
        [
            "pm.expect(body.code).to.eql('VALIDATION_ERROR');",
            "pm.expect(body.message).to.include('integers');",
        ],
    ),
    (
        "Reject excessive page size",
        "?per_page=101",
        400,
        [
            "pm.expect(body.code).to.eql('VALIDATION_ERROR');",
            "pm.expect(body.message).to.include('100');",
        ],
    ),
]

items = []

for name, query, status, assertions in cases:
    items.append({
        "name": name,
        "request": {
            "method": "GET",
            "header": [],
            "url": "{{base_url}}/api/v1/products" + query,
        },
        "event": [{
            "listen": "test",
            "script": {
                "type": "text/javascript",
                "exec": [
                    f"pm.test('HTTP {status}', () => "
                    f"pm.response.to.have.status({status}));",
                    "pm.test('Response content is correct', () => {",
                    "  const body = pm.response.json();",
                    *["  " + line for line in assertions],
                    "});",
                ],
            },
        }],
    })

collection = {
    "info": {
        "name": "Product Catalog API",
        "schema": (
            "https://schema.getpostman.com/json/"
            "collection/v2.1.0/collection.json"
        ),
    },
    "item": items,
}

environment = {
    "name": "Product Catalog Local",
    "values": [{
        "key": "base_url",
        "value": "http://127.0.0.1:5000",
        "enabled": True,
    }],
    "_postman_variable_scope": "environment",
}

for filename, content in [
    ("products.postman_collection.json", collection),
    ("local.postman_environment.json", environment),
]:
    (folder / filename).write_text(
        json.dumps(content, indent=2),
        encoding="utf-8",
    )

print("Collection and environment created in postman/")