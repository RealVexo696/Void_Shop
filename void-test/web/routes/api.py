"""
VOID Shop Web-App
- schlanke Flask-Routen
- HTML liegt in web/pages.py
- APIs für Status, Admin-Dashboard und Produktverwaltung
"""

import os
import threading
import csv
import io

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
    overrides = db.get_product_overrides()
    sales = db.sales_stats().get("per_product", {})
    best = None
    if sales:
        best_name = max(sales.items(), key=lambda x: x[1])[0]
        for k, base in PRODUCTS.items():
            if base.get("name") == best_name:
                best = k
                break
    out = {}
    for idx, key in enumerate(PRODUCT_ORDER):
        p = dict(PRODUCTS[key])
        p.update(overrides.get(key, {}))
        try:
            p["robux"] = int(p.get("robux", 0))
        except Exception:
            p["robux"] = PRODUCTS[key].get("robux", 0)
        p["active"] = db.is_product_active(key)
        p["stock"] = db.stock_count(key)
        unlimited = db.is_unlimited(key)
        if unlimited:
            p["stock_label"] = "∞ unlimited"
            p["stock_badge"] = "Unlimited"
        elif p["stock"] <= 0:
            p["stock_label"] = "🔴 ausverkauft"
            p["stock_badge"] = "Ausverkauft"
        elif p["stock"] < 3:
            p["stock_label"] = f"🟡 {p['stock']} übrig"
            p["stock_badge"] = "Wenig Bestand"
        else:
            p["stock_label"] = f"🟢 {p['stock']} auf Lager"
            p["stock_badge"] = "Auf Lager"
        badges = []
        if key == best:
            badges.append("Bestseller")
        if idx >= 3:
            badges.append("Neu")
        if sales.get(p.get("name"), 0) >= 3:
            badges.append("Beliebt")
        if unlimited:
            badges.append("Unlimited")
        if p["stock_badge"] in ("Ausverkauft", "Wenig Bestand"):
            badges.append(p["stock_badge"])
        p["badges"] = badges or [p["stock_badge"]]
        p["key_needed"] = "Nein" if unlimited else "Ja"
        p["euro"] = p.get("price", "").split("/")[-1].strip() if "/" in p.get("price", "") else f"{p['robux']*0.01:.2f} €"
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
        "api_online": True,
        "delivery_active": True,
        "ticket_system_active": True,
        "guilds": guild_count,
        "open_tickets": open_tickets,
        "products_available": available,
        "avg_response": avg,
        "recent_sales": db.recent_sales_public(5),
        "last_updates": [x[1] for x in pages.CHANGELOG[:3]],
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

@app.route("/api/products")
def api_products_public():
    return jsonify({"products": products_for_web()})


@app.route("/roadmap")
def roadmap_page():
    return Response(pages.render_roadmap(), mimetype="text/html")


@app.route("/status")
def status_page():
    return Response(pages.render_status_page(site_status()), mimetype="text/html")



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
            "stock": p["stock"], "stock_label": p["stock_label"], "unlimited": db.is_unlimited(k), "active": db.is_product_active(k),
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


@app.route("/api/admin/products/<product_key>", methods=["PATCH"])
def api_admin_product_update(product_key):
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    if product_key not in products_for_web():
        return jsonify({"error": "unknown product"}), 404
    data = request.json or {}
    if "name" in data: db.set_product_override(product_key, "name", str(data["name"]))
    if "desc" in data: db.set_product_override(product_key, "desc", str(data["desc"]))
    if "robux" in data:
        robux = int(data["robux"])
        db.set_product_override(product_key, "robux", robux)
        db.set_product_override(product_key, "price", f"{robux} R$ / {robux*0.01:.2f} €")
    if "active" in data: db.set_product_active(product_key, bool(data["active"]))
    return jsonify({"status": "ok", "product": products_for_web()[product_key]})


@app.route("/api/admin/products/<product_key>/keys")
def api_admin_product_key_list(product_key):
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    if product_key not in products_for_web():
        return jsonify({"error": "unknown product"}), 404
    return jsonify({"keys": db.keys_for_product(product_key)})


@app.route("/api/admin/tickets")
def api_admin_tickets():
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    data = db.get_dashboard_data(bot_instance).get("live_discord", {}).get("tickets_list", [])
    metas = db.data.get("ticket_meta", {})
    return jsonify({"tickets": data, "meta": metas})


@app.route("/api/admin/export/<kind>")
def api_admin_export(kind):
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    output = io.StringIO()
    writer = csv.writer(output)
    if kind == "sales":
        rows = db.data.get("sales_log", [])
        writer.writerow(["order_id", "product", "buyer_id", "buyer_name", "robux", "time"])
        for r in rows: writer.writerow([r.get("order_id"), r.get("product_name"), r.get("buyer_id"), r.get("buyer_name"), r.get("robux"), r.get("time")])
    elif kind == "keys":
        writer.writerow(["product", "key", "used", "used_by", "used_at"])
        for prod, keys in db.data.get("license_keys", {}).items():
            for k in keys: writer.writerow([prod, k.get("key"), k.get("used"), k.get("used_by"), k.get("used_at")])
    elif kind == "tickets":
        writer.writerow(["channel_id", "opened", "claimed", "supporter", "closed"])
        for cid, m in db.data.get("ticket_meta", {}).items(): writer.writerow([cid, m.get("opened"), m.get("claimed"), m.get("supporter"), m.get("closed")])
    elif kind == "reviews":
        writer.writerow(["supporter", "claims", "reviews", "stars"])
        for name, v in db.data.get("supporter_leaderboard", {}).items(): writer.writerow([name, v.get("claims"), v.get("reviews"), v.get("stars")])
    else:
        return jsonify({"error": "unknown export"}), 404
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename={kind}.csv"})


@app.route("/api/admin/sales")
def api_admin_sales():
    if not is_logged_in():
        return jsonify({"error": "unauthorized"}), 401
    product = request.args.get("product")
    period = request.args.get("period")
    supporter = request.args.get("supporter")
    log = list(db.data.get("sales_log", []))
    import datetime
    now_dt = datetime.datetime.utcnow()
    today_str = now_dt.strftime("%Y-%m-%d")
    if period == "today":
        log = [s for s in log if str(s.get("time", "")).startswith(today_str)]
    elif period == "7d":
        d7 = (now_dt - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        log = [s for s in log if str(s.get("time", "")) >= d7]
    elif period == "30d":
        d30 = (now_dt - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        log = [s for s in log if str(s.get("time", "")) >= d30]

    if product:
        log = [s for s in log if s.get("product") == product or s.get("product_name") == product]
    if supporter:
        log = [s for s in log if s.get("supporter") == supporter or s.get("buyer_name") == supporter]
    supporters = list(db.data.get("supporter_leaderboard", {}).keys())
    return jsonify({"sales": log[:100], "supporters": supporters})


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()
