from flask import Flask, render_template, request, redirect, session
import os
from dotenv import load_dotenv
from supabase import create_client

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

# -----------------------------
# Supabase Setup
# -----------------------------
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# -----------------------------
# Login Page
# -----------------------------
@app.route("/login")
def login_page():
    return render_template("login.html")


# -----------------------------
# Signup Page
# -----------------------------
@app.route("/signup")
def signup_page():
    return render_template("signup.html")


# -----------------------------
# Create Account (Signup)
# -----------------------------
@app.route("/signup", methods=["POST"])
def signup():

    email = request.form["email"]
    password = request.form["password"]

    try:
        supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        return redirect("/login")

    except Exception as e:
        return str(e)


# -----------------------------
# Login User
# -----------------------------
@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        session["user_id"] = result.user.id

        return redirect("/")

    except Exception as e:
        return str(e)


# -----------------------------
# Logout
# -----------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# -----------------------------
# Dashboard (Accounts List)
# -----------------------------
@app.route("/")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    accounts = supabase.table("accounts") \
        .select("*") \
        .eq("user_id", user_id) \
        .execute().data

    for account in accounts:

        categories = supabase.table("categories") \
            .select("*") \
            .eq("account_id", account["id"]) \
            .execute().data

        transactions = supabase.table("transactions") \
            .select("*") \
            .eq("account_id", account["id"]) \
            .execute().data

        account_total = 0

        for category in categories:

            category_total = float(
                category.get("starting_balance", 0)
            )

            for t in transactions:
                if t["category_id"] == category["id"]:
                    category_total += float(t["amount"])

            account_total += category_total

        account["total"] = account_total

    return render_template(
        "dashboard.html",
        accounts=accounts
    )


# -----------------------------
# Create Account
# -----------------------------
@app.route("/create-account", methods=["POST"])
def create_account():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    name = request.form["name"]
    currency = request.form["currency"]

    supabase.table("accounts").insert({
        "user_id": user_id,
        "name": name,
        "currency": currency
    }).execute()

    return redirect("/")


# -----------------------------
# Account Page
# -----------------------------
@app.route("/account/<int:id>")
def account(id):

    if "user_id" not in session:
        return redirect("/login")

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

    account_total = 0

    for category in categories:

        category_total = float(
            category.get("starting_balance", 0)
        )

        for t in transactions:
            if t["category_id"] == category["id"]:
                category_total += float(t["amount"])

        category["total"] = category_total
        account_total += category_total

    return render_template(
        "account.html",
        account=account,
        categories=categories,
        total=account_total
    )


# -----------------------------
# Add Category
# -----------------------------
@app.route("/add-category/<int:account_id>", methods=["POST"])
def add_category(account_id):

    name = request.form["name"]
    starting_balance = float(request.form["balance"])

    supabase.table("categories").insert({
        "account_id": account_id,
        "name": name,
        "starting_balance": starting_balance
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
        .order("date", desc=True) \
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
# Delete Transaction
# -----------------------------
@app.route("/delete-transaction/<int:id>", methods=["POST"])
def delete_transaction(id):

    transaction = supabase.table("transactions") \
        .select("*") \
        .eq("id", id) \
        .single() \
        .execute().data

    category_id = transaction["category_id"]

    supabase.table("transactions") \
        .delete() \
        .eq("id", id) \
        .execute()

    return redirect(f"/category/{category_id}")


# -----------------------------
# Edit Transaction
# -----------------------------
@app.route("/edit-transaction/<int:id>", methods=["POST"])
def edit_transaction(id):

    transaction = supabase.table("transactions") \
        .select("*") \
        .eq("id", id) \
        .single() \
        .execute().data

    category_id = transaction["category_id"]

    supabase.table("transactions") \
        .update({
            "date": request.form["date"],
            "description": request.form["description"],
            "amount": float(request.form["amount"])
        }) \
        .eq("id", id) \
        .execute()

    return redirect(f"/category/{category_id}")

# -----------------------------
# Rename Category
# -----------------------------
@app.route("/rename-category/<int:id>", methods=["POST"])
def rename_category(id):

    new_name = request.form["name"]

    supabase.table("categories") \
        .update({
            "name": new_name
        }) \
        .eq("id", id) \
        .execute()

    return redirect(f"/category/{id}")


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)