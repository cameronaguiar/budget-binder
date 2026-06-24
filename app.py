from flask import Flask, render_template, request, redirect
import os
from dotenv import load_dotenv
from supabase import create_client

app = Flask(__name__)

# -----------------------------
# Supabase Setup
# -----------------------------
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)


# -----------------------------
# Dashboard (Accounts list)
# -----------------------------
@app.route("/")
def dashboard():

    accounts = supabase.table("accounts") \
        .select("*") \
        .execute().data

    return render_template(
        "dashboard.html",
        accounts=accounts
    )


# -----------------------------
# Create Account
# -----------------------------
@app.route("/create-account", methods=["POST"])
def create_account():

    name = request.form["name"]
    currency = request.form["currency"]

    supabase.table("accounts").insert({
        "name": name,
        "currency": currency
    }).execute()

    return redirect("/")


# -----------------------------
# Account Page (categories + total)
# -----------------------------
@app.route("/account/<int:id>")
def account(id):

    account = supabase.table("accounts") \
        .select("*") \
        .eq("id", id) \
        .single() \
        .execute().data

    categories = supabase.table("categories") \
        .select("*") \
        .eq("account_id", id) \
        .execute().data

    transactions = supabase.table("transactions") \
        .select("*") \
        .eq("account_id", id) \
        .execute().data

    total = sum(t["amount"] for t in transactions)

    return render_template(
        "account.html",
        account=account,
        categories=categories,
        transactions=transactions,
        total=total
    )


# -----------------------------
# Add Category
# -----------------------------
@app.route("/add-category/<int:account_id>", methods=["POST"])
def add_category(account_id):

    name = request.form["name"]

    supabase.table("categories").insert({
        "account_id": account_id,
        "name": name
    }).execute()

    return redirect(f"/account/{account_id}")


# -----------------------------
# Category Page
# -----------------------------
@app.route("/category/<int:id>")
def category(id):

    category = supabase.table("categories") \
        .select("*") \
        .eq("id", id) \
        .single() \
        .execute().data

    transactions = supabase.table("transactions") \
        .select("*") \
        .eq("category_id", id) \
        .order("id", desc=True) \
        .execute().data

    return render_template(
        "category.html",
        category=category,
        transactions=transactions,
        account_id=category["account_id"]
    )


# -----------------------------
# Add Transaction
# -----------------------------
@app.route("/add-transaction/<int:category_id>", methods=["POST"])
def add_transaction(category_id):

    amount = float(request.form["amount"])
    description = request.form["description"]
    date = request.form["date"]

    category = supabase.table("categories") \
        .select("*") \
        .eq("id", category_id) \
        .single() \
        .execute().data

    supabase.table("transactions").insert({
        "category_id": category_id,
        "account_id": category["account_id"],
        "date": date,
        "description": description,
        "amount": amount
    }).execute()

    return redirect(f"/category/{category_id}")


# -----------------------------
# Rename Category
# -----------------------------
@app.route("/rename-category/<int:id>", methods=["POST"])
def rename_category(id):

    new_name = request.form["name"]

    supabase.table("categories") \
        .update({"name": new_name}) \
        .eq("id", id) \
        .execute()

    return redirect(f"/category/{id}")


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)