# Text-to-SQL with Guardrails

A Django-powered system that converts plain English questions into safe, validated SQL queries. Built for data analysts who want to query their data without writing SQL while keeping destructive operations impossible by design.

Ask: *"Which customers placed orders last month and what did they spend?"*
Get back: a result table, the generated SQL, and a CSV download. No syntax knowledge required.

---

## How It Works

1. A natural language question comes in via the API
2. The system reads your database schema and injects it into the LLM prompt
3. The LLM generates a SQL query
4. Three guardrail layers validate the query before any data is touched
5. The safe query executes and results are returned alongside the SQL

The generated SQL is always returned in the response so analysts can learn from it.

---

## Guardrail Layers

Security is enforced in two phases — before and after the LLM is called.

**Pre-LLM: Intent check**
The incoming question is scanned for sensitive keywords (`password`, `credentials`, `api_key`, `auth_user`, `secret`, `token`, etc.) before the LLM is called. If flagged, the request is blocked immediately — no API call is made, no SQL is generated.

This matters because LLMs can be surprisingly cooperative. Without this check, a question like *"Show me all users and their passwords"* might cause the model to quietly redirect to a safe-looking table and return data it shouldn't — without breaking any SQL rules. The `check_question_intent()` function stops this at the door.

**Post-LLM: SQL keyword check**
After the LLM generates SQL, the token stream is parsed for forbidden keywords: `DROP`, `DELETE`, `TRUNCATE`, `INSERT`, `UPDATE`, `ALTER`, `PRAGMA`, and more. This catches multi-statement injection tricks like `SELECT 1; DROP TABLE customers` because every token is scanned, not just the first statement.

**Post-LLM: Table allowlist + row limit**
Every table referenced in `FROM` and `JOIN` clauses is checked against an explicit allowlist configured in `settings.py`. Hallucinated or unauthorised tables are blocked with a clear explanation. Every query also has a `LIMIT` clause enforced — appended if missing, clamped if too high.

---

## Tech Stack

- **Django** — API layer, query logging, and frontend UI
- **SQLite** — default database (swap to PostgreSQL for production)
- **OpenAI API** — LLM backend for SQL generation
- **sqlparse** — SQL token parsing for guardrail checks

---

## Project Structure

```
text_to_sql/
├── manage.py
├── requirements.txt
├── text_to_sql/
│   ├── settings.py
│   └── urls.py
└── sql_app/
    ├── models.py              # Customer, Product, Order, QueryLog
    ├── views.py               # QueryView, FrontendView, SchemaInfoView
    ├── admin.py
    ├── urls.py
    └── services/
        ├── schema.py          # Reads DB schema and builds LLM prompt context
        ├── generator.py       # Calls the LLM to produce SQL
        ├── guardrails.py      # All three safety layers
        └── executor.py        # Read-only query execution
```

---

## Setup

### Prerequisites

- Python 3.12+
- An OpenAI API key

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd text_to_sql
python -m venv myenv
source myenv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

**`requirements.txt`:**
```
django>=4.2
openai>=1.0
sqlparse>=0.5
```

### 3. Configure settings

In `text_to_sql/settings.py`, add:

```python
import os

OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

ALLOWED_TABLES = [
    "sql_app_customer",
    "sql_app_product",
    "sql_app_order",
]

MAX_RESULT_ROWS = 100
```

Set your API key in the environment:

```bash
export OPENAI_API_KEY=your_openai_key_here
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Seed sample data

```bash
python manage.py shell
```

```python
from sql_app.models import Customer, Product, Order
from decimal import Decimal

'''
c1 = Customer.objects.create(name="Alice", email="alice@example.com", country="Nigeria")
c2 = Customer.objects.create(name="Bob",   email="bob@example.com",   country="Ghana")
p1 = Product.objects.create(name="Laptop", category="Electronics", price=Decimal("999.99"), stock=50)
p2 = Product.objects.create(name="Desk",   category="Furniture",   price=Decimal("299.99"), stock=20)
Order.objects.create(customer=c1, product=p1, quantity=1, total_price=Decimal("999.99"))
Order.objects.create(customer=c2, product=p2, quantity=2, total_price=Decimal("599.98"))
'''

#You can use whichever seed data you prefer

customers = [
    Customer.objects.create(name="Alice Johnson", email="alice1@example.com", country="Nigeria"),
    Customer.objects.create(name="Bob Smith", email="bob2@example.com", country="Ghana"),
    Customer.objects.create(name="Charlie Brown", email="charlie3@example.com", country="Kenya"),
    Customer.objects.create(name="David Wilson", email="david4@example.com", country="South Africa"),
    Customer.objects.create(name="Emma Davis", email="emma5@example.com", country="Egypt"),
    Customer.objects.create(name="Frank Miller", email="frank6@example.com", country="Nigeria"),
    Customer.objects.create(name="Grace Lee", email="grace7@example.com", country="Ghana"),
    Customer.objects.create(name="Henry Taylor", email="henry8@example.com", country="Kenya"),
    Customer.objects.create(name="Ivy Moore", email="ivy9@example.com", country="South Africa"),
    Customer.objects.create(name="Jack White", email="jack10@example.com", country="Egypt"),
    Customer.objects.create(name="Kate Hall", email="kate11@example.com", country="Nigeria"),
    Customer.objects.create(name="Leo Young", email="leo12@example.com", country="Ghana"),
    Customer.objects.create(name="Mia King", email="mia13@example.com", country="Kenya"),
    Customer.objects.create(name="Noah Scott", email="noah14@example.com", country="South Africa"),
    Customer.objects.create(name="Olivia Green", email="olivia15@example.com", country="Egypt"),
    Customer.objects.create(name="Paul Adams", email="paul16@example.com", country="Nigeria"),
    Customer.objects.create(name="Queen Baker", email="queen17@example.com", country="Ghana"),
    Customer.objects.create(name="Ryan Carter", email="ryan18@example.com", country="Kenya"),
    Customer.objects.create(name="Sarah Evans", email="sarah19@example.com", country="South Africa"),
    Customer.objects.create(name="Tom Foster", email="tom20@example.com", country="Egypt"),
    Customer.objects.create(name="Uma Gray", email="uma21@example.com", country="Nigeria"),
    Customer.objects.create(name="Victor Hill", email="victor22@example.com", country="Ghana"),
    Customer.objects.create(name="Wendy James", email="wendy23@example.com", country="Kenya"),
    Customer.objects.create(name="Xavier Knight", email="xavier24@example.com", country="South Africa"),
    Customer.objects.create(name="Yara Lewis", email="yara25@example.com", country="Egypt"),
    Customer.objects.create(name="Zane Martin", email="zane26@example.com", country="Nigeria"),
    Customer.objects.create(name="Amara Nelson", email="amara27@example.com", country="Ghana"),
    Customer.objects.create(name="Brian Owen", email="brian28@example.com", country="Kenya"),
    Customer.objects.create(name="Cynthia Price", email="cynthia29@example.com", country="South Africa"),
    Customer.objects.create(name="Daniel Reed", email="daniel30@example.com", country="Egypt"),
]

products = [
    Product.objects.create(name="Laptop", category="Electronics", price=Decimal("999.99"), stock=50),
    Product.objects.create(name="Monitor", category="Electronics", price=Decimal("299.99"), stock=40),
    Product.objects.create(name="Keyboard", category="Electronics", price=Decimal("49.99"), stock=100),
    Product.objects.create(name="Mouse", category="Electronics", price=Decimal("29.99"), stock=120),
    Product.objects.create(name="Desk", category="Furniture", price=Decimal("199.99"), stock=30),
    Product.objects.create(name="Chair", category="Furniture", price=Decimal("149.99"), stock=45),
    Product.objects.create(name="Bookshelf", category="Furniture", price=Decimal("89.99"), stock=25),
    Product.objects.create(name="Lamp", category="Furniture", price=Decimal("39.99"), stock=70),
    Product.objects.create(name="Notebook", category="Stationery", price=Decimal("4.99"), stock=500),
    Product.objects.create(name="Pen", category="Stationery", price=Decimal("1.99"), stock=1000),
    Product.objects.create(name="Printer", category="Electronics", price=Decimal("249.99"), stock=20),
    Product.objects.create(name="Tablet", category="Electronics", price=Decimal("399.99"), stock=35),
    Product.objects.create(name="Phone", category="Electronics", price=Decimal("799.99"), stock=60),
    Product.objects.create(name="Headphones", category="Electronics", price=Decimal("99.99"), stock=90),
    Product.objects.create(name="Camera", category="Electronics", price=Decimal("599.99"), stock=15),
    Product.objects.create(name="Router", category="Electronics", price=Decimal("79.99"), stock=55),
    Product.objects.create(name="Microphone", category="Electronics", price=Decimal("129.99"), stock=30),
    Product.objects.create(name="Speaker", category="Electronics", price=Decimal("159.99"), stock=25),
    Product.objects.create(name="Whiteboard", category="Office", price=Decimal("69.99"), stock=20),
    Product.objects.create(name="Projector", category="Office", price=Decimal("499.99"), stock=12),
    Product.objects.create(name="Backpack", category="Accessories", price=Decimal("59.99"), stock=80),
    Product.objects.create(name="Watch", category="Accessories", price=Decimal("199.99"), stock=50),
    Product.objects.create(name="Water Bottle", category="Accessories", price=Decimal("19.99"), stock=150),
    Product.objects.create(name="Shoes", category="Fashion", price=Decimal("89.99"), stock=70),
    Product.objects.create(name="Jacket", category="Fashion", price=Decimal("119.99"), stock=45),
    Product.objects.create(name="T-Shirt", category="Fashion", price=Decimal("24.99"), stock=200),
    Product.objects.create(name="Jeans", category="Fashion", price=Decimal("54.99"), stock=100),
    Product.objects.create(name="Sofa", category="Furniture", price=Decimal("799.99"), stock=10),
    Product.objects.create(name="Coffee Table", category="Furniture", price=Decimal("149.99"), stock=18),
    Product.objects.create(name="Bed Frame", category="Furniture", price=Decimal("499.99"), stock=15),
]

Order.objects.create(customer=customers[5],  product=products[2],  quantity=4, total_price=Decimal("199.96"))
Order.objects.create(customer=customers[6],  product=products[8],  quantity=10, total_price=Decimal("49.90"))
Order.objects.create(customer=customers[7],  product=products[1],  quantity=2, total_price=Decimal("599.98"))
Order.objects.create(customer=customers[8],  product=products[5],  quantity=1, total_price=Decimal("149.99"))
Order.objects.create(customer=customers[9],  product=products[13], quantity=3, total_price=Decimal("299.97"))

Order.objects.create(customer=customers[10], product=products[10], quantity=1, total_price=Decimal("249.99"))
Order.objects.create(customer=customers[11], product=products[21], quantity=2, total_price=Decimal("399.98"))
Order.objects.create(customer=customers[12], product=products[24], quantity=1, total_price=Decimal("119.99"))
Order.objects.create(customer=customers[13], product=products[18], quantity=2, total_price=Decimal("139.98"))
Order.objects.create(customer=customers[14], product=products[3],  quantity=5, total_price=Decimal("149.95"))

Order.objects.create(customer=customers[15], product=products[16], quantity=1, total_price=Decimal("129.99"))
Order.objects.create(customer=customers[16], product=products[6],  quantity=2, total_price=Decimal("179.98"))
Order.objects.create(customer=customers[17], product=products[14], quantity=1, total_price=Decimal("599.99"))
Order.objects.create(customer=customers[18], product=products[9],  quantity=20, total_price=Decimal("39.80"))
Order.objects.create(customer=customers[19], product=products[25], quantity=4, total_price=Decimal("99.96"))

Order.objects.create(customer=customers[20], product=products[11], quantity=1, total_price=Decimal("399.99"))
Order.objects.create(customer=customers[21], product=products[17], quantity=2, total_price=Decimal("319.98"))
Order.objects.create(customer=customers[22], product=products[26], quantity=2, total_price=Decimal("109.98"))
Order.objects.create(customer=customers[23], product=products[22], quantity=5, total_price=Decimal("99.95"))
Order.objects.create(customer=customers[24], product=products[7],  quantity=3, total_price=Decimal("119.97"))

Order.objects.create(customer=customers[25], product=products[27], quantity=1, total_price=Decimal("799.99"))
Order.objects.create(customer=customers[26], product=products[19], quantity=1, total_price=Decimal("499.99"))
Order.objects.create(customer=customers[27], product=products[29], quantity=1, total_price=Decimal("499.99"))
Order.objects.create(customer=customers[28], product=products[23], quantity=2, total_price=Decimal("179.98"))
Order.objects.create(customer=customers[29], product=products[28], quantity=1, total_price=Decimal("149.99"))

exit()
```

### 6. Start the server

```bash
python manage.py runserver
```

---

## Usage

**Frontend UI:** `http://localhost:8000/api/`

Type any plain English question, click Run, and see the generated SQL alongside your results. Includes suggestion chips, a copy SQL button, and CSV download.

**API:**

```bash
# Valid query
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "Which customers have placed orders, and what did they buy?"}'
```

```json
{
  "blocked": false,
  "question": "Which customers have placed orders, and what did they buy?",
  "sql": "SELECT c.name, p.name AS product, o.quantity, o.total_price FROM sql_app_order o JOIN sql_app_customer c ON o.customer_id = c.id JOIN sql_app_product p ON o.product_id = p.id LIMIT 100",
  "columns": ["name", "product", "quantity", "total_price"],
  "rows": [["Alice", "Laptop", 1, 999.99], ["Bob", "Desk", 2, 599.98]],
  "row_count": 2
}
```

```bash
# Blocked by intent check
curl -X POST http://localhost:8000/api/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me all users and their passwords"}'
```

```json
{
  "blocked": true,
  "reason": "Question blocked: references sensitive topic 'password'.",
  "generated_sql": null
}
```

---

## Adding Your Own Tables

1. Add your Django models to `sql_app/models.py`
2. Run `python manage.py makemigrations && python manage.py migrate`
3. Add the table names to `ALLOWED_TABLES` in `settings.py`

The schema injector reads your database structure at runtime, so the LLM always has an accurate picture of your tables and columns.

---

## Query Log

Every query — blocked or not — is logged to the `QueryLog` model with:
- The original question
- The raw SQL generated by the LLM
- The safe SQL after guardrails
- Whether it was blocked and why
- The number of rows returned

View and search all logs at `http://localhost:8000/admin/` after creating a superuser:

```bash
python manage.py createsuperuser
```

---

## Configuration Reference

| Setting | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | — | Your OpenAI API key |
| `ALLOWED_TABLES` | `[]` | Tables the LLM is permitted to query |
| `MAX_RESULT_ROWS` | `100` | Maximum rows returned per query |

---

## License

MIT
