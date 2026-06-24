from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB = "budget.db"

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS accounts(
        id INTEGER PRIMARY KEY,
        name TEXT,
        currency TEXT
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS categories(
        id INTEGER PRIMARY KEY,
        account_id INTEGER,
        name TEXT,
        balance REAL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY,
        category_id INTEGER,
        date TEXT,
        description TEXT,
        amount REAL,
        balance_after REAL
    )
    """)

    conn.commit()

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

@app.route("/")
def dashboard():

    conn = db()

    accounts = conn.execute("""
SELECT
    a.*,
    COALESCE(SUM(c.balance),0) as total_balance
FROM accounts a
LEFT JOIN categories c
ON a.id = c.account_id
GROUP BY a.id
""").fetchall()

    return render_template(
        "dashboard.html",
        accounts=accounts
    )


@app.route("/create-account", methods=["POST"])
def create_account():

    name = request.form["name"]
    currency = request.form["currency"]

    conn = db()

    conn.execute(
        "INSERT INTO accounts(name,currency) VALUES(?,?)",
        (name,currency)
    )

    conn.commit()

    return redirect("/")


@app.route("/account/<int:id>")
def account(id):

    conn = db()

    account = conn.execute(
        "SELECT * FROM accounts WHERE id=?",
        (id,)
    ).fetchone()

    categories = conn.execute(
        "SELECT * FROM categories WHERE account_id=?",
        (id,)
    ).fetchall()

    total = sum(c["balance"] for c in categories)

    return render_template(
        "account.html",
        account=account,
        categories=categories,
        total=total
    )


@app.route("/add-category/<int:account_id>", methods=["POST"])
def add_category(account_id):

    name = request.form["name"]
    balance = float(request.form["balance"])

    conn = db()

    conn.execute(
        """
        INSERT INTO categories(
            account_id,
            name,
            balance
        )
        VALUES(?,?,?)
        """,
        (account_id,name,balance)
    )

    conn.commit()

    return redirect(f"/account/{account_id}")


@app.route("/category/<int:id>")
def category(id):

    conn = db()

    category = conn.execute(
        "SELECT * FROM categories WHERE id=?",
        (id,)
    ).fetchone()

    transactions = conn.execute(
        """
        SELECT *
        FROM transactions
        WHERE category_id=?
        ORDER BY date DESC,id DESC
        """,
        (id,)
    ).fetchall()

    account_id = conn.execute(
    """
    SELECT account_id
    FROM categories
    WHERE id=?
    """,
    (id,)
).fetchone()["account_id"]

    return render_template(
        "category.html",
        category=category,
        transactions=transactions,
        account_id=account_id
    )


@app.route("/add-transaction/<int:category_id>", methods=["POST"])
def add_transaction(category_id):

    amount = float(request.form["amount"])
    description = request.form["description"]
    date = request.form["date"]

    conn = db()

    category = conn.execute(
        "SELECT * FROM categories WHERE id=?",
        (category_id,)
    ).fetchone()

    new_balance = category["balance"] + amount

    conn.execute(
        """
        UPDATE categories
        SET balance=?
        WHERE id=?
        """,
        (new_balance,category_id)
    )

    conn.execute(
        """
        INSERT INTO transactions(
            category_id,
            date,
            description,
            amount,
            balance_after
        )
        VALUES(?,?,?,?,?)
        """,
        (
            category_id,
            date,
            description,
            amount,
            new_balance
        )
    )

    conn.commit()

    return redirect(f"/category/{category_id}")

@app.route("/rename-category/<int:id>", methods=["POST"])
def rename_category(id):

    new_name = request.form["name"]

    conn = db()

    conn.execute(
        """
        UPDATE categories
        SET name=?
        WHERE id=?
        """,
        (new_name,id)
    )

    conn.commit()

    return redirect(f"/category/{id}")

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
