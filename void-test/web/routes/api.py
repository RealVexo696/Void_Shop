"""
VOID Shop Web-App
- schlanke Flask-Routen
- HTML liegt in web/pages.py
- APIs für Status, Admin-Dashboard und Produktverwaltung
"""

import os
import threading

from flask import Flask, jsonify, request, session, redirect, Response

from bot.cogs.database import db
from bot import bot as bot_instance
from web import pages

app = Flask("web_dashboard")
app.secret_key = os.environ.get("SECRET_KEY", "void-shop-default-secret-change-me")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "voidadmin")


def is_logged_in():
    return session.get("admin_logged_in") is True


def _products_raw():
    from bot.cogs.tickets import PRODUCTS, PRODUCT_ORDER
    return PRODUCTS, PRODUCT_ORDER


def products_for_web():
    PRODUCTS, PRODUCT_ORDER = _products_raw()
    out = {}
    for key in PRODUCT_ORDER:
        p = dict(PRODUCTS[key])
        p["stock"] = db.stock_count(key)
        p["stock_label"] = "∞ unlimited" if db.is_unlimited(key) else f"{db.stock_count(key)} auf Lager"
        p["key_needed"] = "Nein" if db.is_unlimited(key) else "Ja"
        p["euro"] = p.get("price", "").split("/")[-1].strip() if "/" in p.get("price", "") else ""
        out[key] = p
    return out


def site_status():
    try:
        guild_count = len(bot_instance.guilds) if bot_instance and bot_instance.is_ready() else 0
        bot_online = bool(bot_instance and bot_instance.is_ready())
    except Exception:
        guild_count = 0
        bot_online = False
    try:
        stats = db.get_dashboard_data(bot_instance)
        open_tickets = stats.get("live_discord", {}).get("open_tickets", 0)
    except Exception:
        open_tickets = 0
    t = db.ticket_stats()
    secs = t.get("avg_response_secs", 0)
    avg = f"{secs//60}m {secs%60}s" if secs >= 60 else (f"{secs}s" if secs else "kurz")
    products = products_for_web()
    available = sum(1 for k, p in products.items() if db.is_unlimited(k) or p.get("stock", 0) > 0)
    return {
        "bot_online": bot_online,
        "guilds": guild_count,
        "open_tickets": open_tickets,
        "products_available": available,
        "avg_response": avg,
    }


def bestseller_key():
    s = db.sales_stats()
    best_name = s.get("best_product")
    if not best_name or best_name == "—":
        return None
    products = products_for_web()
    for key, p in products.items():
        if p["name"] == best_name:
            return key
    return None


@app.route("/")
def home():
    return Response(pages.render_landing(products_for_web(), site_status(), bestseller_key()), mimetype="text/html")


@app.route("/store")
def store_page():
    return Response(pages.render_store(products_for_web()), mimetype="text/html")


@app.route("/fittingroom")
def fitting_page():
    return Response(pages.render_fitting(), mimetype="text/html")


@app.route("/product/<product_key>")
def product_page(product_key):
    return Response(pages.render_product_detail(product_key, products_for_web().get(product_key), bestseller_key()), mimetype="text/html")


@app.route("/changelog")
def changelog_page():
    return Response(pages.render_changelog(), mimetype="text/html")


@app.route("/partner")
def partner_page():
    return Response(pages.render_partner(), mimetype="text/html")


@app.route("/api/site/status")
def api_site_status():
    return jsonify(site_status())


@app.route("/api/stats")
def api_stats():
    return db.get_dashboard_data(bot_instance)


@app.route("/api/transcripts")
def api_transcripts():
    return jsonify(db.get_transcripts_list())


@app.route("/api/buy", methods=["POST"])
def api_buy():
    data = request.json or {}
    user = data.get("user")
    product = data.get("product")
    mode = data.get("mode")
    if user and product:
        db.add_web_order(user, product, mode)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin")
        return Response(pages.render_login("Falsches Passwort!"), mimetype="text/html")
    if is_logged_in():
        return redirect("/admin")
    return Response(pages.render_login(), mimetype="text/html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")


@app.route("/admin")
def admin_dashboard():
    if not is_logged_in():
        return redirect("/admin/login")
    return Response(pages.render_admin(), mimetype="text/html")


@app.route("/api/admin/stats")
def api_admin_stats():
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    s = db.sales_stats()
    t = db.ticket_stats()
    secs = t["avg_response_secs"]
    avg_txt = f"{secs//60}m {secs%60}s" if secs >= 60 else f"{secs}s"
    products = []
    for k, p in products_for_web().items():
        products.append({"key": k, "name": f"{p['emoji']} {p['name']}", "stock": p["stock_label"], "sold": s["per_product"].get(p["name"], 0)})
    return jsonify({
        "total_robux": s["total_robux"], "today_robux": s["today_robux"],
        "total_sales": s["total_sales"], "best_product": s["best_product"],
        "total_tickets": t["total_tickets"], "avg_response": avg_txt,
        "satisfaction": t["satisfaction"], "timeseries": db.sales_timeseries(7),
        "per_supporter": t["per_supporter"], "products": products,
    })


@app.route("/api/admin/products")
def api_admin_products():
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    products = []
    for k, p in products_for_web().items():
        products.append({
            "key": k, "name": p["name"], "emoji": p["emoji"], "price": p["price"], "robux": p["robux"],
            "stock": p["stock"], "stock_label": p["stock_label"], "unlimited": db.is_unlimited(k),
        })
    return jsonify({"products": products})


@app.route("/api/admin/products/<product_key>/unlimited", methods=["POST"])
def api_admin_product_unlimited(product_key):
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    if product_key not in products_for_web():
        return jsonify({"error": "unknown product"}), 404
    data = request.json or {}
    enabled = bool(data.get("enabled"))
    db.set_unlimited(product_key, enabled)
    return jsonify({"status": "ok", "product": product_key, "unlimited": enabled})


@app.route("/api/admin/products/<product_key>/keys", methods=["POST"])
def api_admin_product_keys(product_key):
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    if product_key not in products_for_web():
        return jsonify({"error": "unknown product"}), 404
    raw = (request.json or {}).get("keys", "")
    keys = [k.strip() for chunk in raw.replace("\n", ",").split(",") for k in chunk.split() if k.strip()]
    added = db.add_keys(product_key, keys)
    return jsonify({"status": "ok", "added": added, "stock": db.stock_label(product_key)})


@app.route("/api/admin/sales")
def api_admin_sales():
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    product = request.args.get("product")
    log = list(db.data.get("sales_log", []))[:100]
    if product:
        log = [s for s in log if s.get("product") == product]
    return jsonify({"sales": log[:50]})


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()
