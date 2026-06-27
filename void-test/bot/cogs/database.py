"""
Database - Persistente Datenspeicherung (shop_db.json)
Inklusive automatischem Ticket-Archiv, Vouch-Leveling, Auto-Gamepass Tracker,
Web-Store Orders und Analytics-Historie.
"""

import json
import os
import threading
import math

import discord


class Database:
    def __init__(self, filename="shop_db.json"):
        self.filename = filename
        self.lock = threading.Lock()
        self.data = {
            "coins": {"12345678": 250, "87654321": 450},
            "revenue_robux": 14500,
            "revenue_euro": 145.0,
            "supporter_leaderboard": {
                "Vexo_Admin": {"claims": 18, "reviews": 12, "stars": 58},
                "Lukas_Support": {"claims": 14, "reviews": 9, "stars": 44},
            },
            "recent_purchases": [
                {"user": "Maximilian", "product": "Prestige FastFlags v2", "time": "12:45"},
                {"user": "Sven_Roblox", "product": "T-Shirt Template Pack", "time": "11:20"},
            ],
            "scam_blocked": 23,
            "live_logs": {
                "voice": ["[12:30:15] Voice System Online"],
                "ban_kick": ["[12:30:15] Ban & Kick Monitor Aktiv"],
                "message": ["[12:30:15] Message Tracker Online"],
                "invite": ["[12:30:15] Invite Tracker Geladen"],
                "join_leave": ["[12:30:15] Join/Leave Scanner Online"],
                "ticket": ["[12:30:15] Ticket Engine Aktiv"],
                "system": ["[12:30:15] System Logger Bereit"],
                "security": ["[12:30:15] Anti-Scam Phishing Schild Bereit"],
                "verify": ["[12:30:15] Bio-Code Auth Engine Aktiv"],
                "custom": ["[12:30:15] Prestige Bot Modules Geladen"],
            },
            "transcripts": {
                "kauf-beispiel": {
                    "closed_by": "Vexo_Admin",
                    "closed_by_id": "123456789",
                    "closed_by_avatar": "https://cdn.discordapp.com/embed/avatars/0.png",
                    "time": "2026-06-27 12:30:00",
                    "messages": [
                        {
                            "author": "Kunde",
                            "avatar": "https://cdn.discordapp.com/embed/avatars/1.png",
                            "timestamp": "2026-06-27 12:25:10",
                            "content": "Hallo, ich würde gerne das FastFlags Premium Paket kaufen!",
                            "bot": False
                        },
                        {
                            "author": "Vexo_Admin",
                            "avatar": "https://cdn.discordapp.com/embed/avatars/0.png",
                            "timestamp": "2026-06-27 12:26:00",
                            "content": "Gerne! Hier ist deine Datei. Vielen Dank für deinen Einkauf!",
                            "bot": False
                        },
                        {
                            "author": "𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 Bot",
                            "avatar": "https://cdn.discordapp.com/embed/avatars/4.png",
                            "timestamp": "2026-06-27 12:26:05",
                            "content": "🎉 Kauf bestätigt! Rollen und +50 Coins wurden zugewiesen.",
                            "bot": True
                        }
                    ]
                }
            },
            "user_vouches": {},
            "verified_users": {},
            "vip_serials": {},
            "web_orders": [],
            # Lizenz-Keys pro Produkt: {"infinityxeh": [{"key": "...", "used": False, "used_by": None, "used_at": None}], ...}
            "license_keys": {},
            # Verkaufs-Log für Statistik: [{"product": "...", "buyer_id": "...", "buyer_name": "...", "robux": 750, "time": "ISO"}]
            "sales_log": [],
            # Warenkörbe pro Ticket-Kanal: {channel_id: [product_key, ...]}
            "carts": {},
            # Ticket-Timing für Ø-Antwortzeit & Supporter-Statistik
            # {channel_id: {"opened": ISO, "claimed": ISO, "supporter": name, "closed": ISO}}
            "ticket_meta": {},
            # FAQ-Einträge: {"keyword": "Antwort", ...}
            "faq": {
                "preis": "💰 Unsere Preise: ♾️ INFINITYxEH 750 R$ · 💉 FFlags Injector 300 R$ · 🛡️ Anti-Ban 1.000 R$.",
                "zahlung": "💳 Wir akzeptieren PayPal, Robux (Gamepass), Paysafecard und Krypto.",
                "lieferung": "📦 Nach bestätigter Zahlung erhältst du deinen Key sofort automatisch per DM.",
                "key": "🔑 Löse deinen Key mit dem Befehl /redeem <key> ein, um deine Rolle zu erhalten.",
                "anti-ban": "🛡️ Anti-Ban schützt dich zuverlässig vor Bans. Preis: 1.000 R$ / 10,00 €.",
            },
            # Sprach-Einstellung pro User: {user_id: "de"|"en"}
            "user_lang": {},
            # Supporter des Monats (Cache): {"month": "2026-06", "winner": name}
            "supporter_of_month": {},
            "analytics_history": [
                {"date": "Woche 1", "members": 50, "vouches": 12, "robux": 2500},
                {"date": "Woche 2", "members": 120, "vouches": 34, "robux": 6200},
                {"date": "Woche 3", "members": 240, "vouches": 68, "robux": 10800},
                {"date": "Woche 4", "members": 380, "vouches": 95, "robux": 14500},
            ]
        }
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.data.update(saved)
                    if "live_logs" not in self.data:
                        self.data["live_logs"] = {
                            k: [f"[Sys] Monitor {k} bereit"]
                            for k in [
                                "voice", "ban_kick", "message", "invite",
                                "join_leave", "ticket", "system", "security",
                                "verify", "custom",
                            ]
                        }
                    if "transcripts" not in self.data: self.data["transcripts"] = {}
                    if "user_vouches" not in self.data: self.data["user_vouches"] = {}
                    if "verified_users" not in self.data: self.data["verified_users"] = {}
                    if "vip_serials" not in self.data: self.data["vip_serials"] = {}
                    if "web_orders" not in self.data: self.data["web_orders"] = []
                    if "license_keys" not in self.data: self.data["license_keys"] = {}
                    if "sales_log" not in self.data: self.data["sales_log"] = []
                    if "carts" not in self.data: self.data["carts"] = {}
                    if "ticket_meta" not in self.data: self.data["ticket_meta"] = {}
                    if "faq" not in self.data: self.data["faq"] = {}
                    if "user_lang" not in self.data: self.data["user_lang"] = {}
                    if "supporter_of_month" not in self.data: self.data["supporter_of_month"] = {}
                    if "analytics_history" not in self.data:
                        self.data["analytics_history"] = [
                            {"date": "Woche 1", "members": 50, "vouches": 12, "robux": 2500},
                            {"date": "Woche 2", "members": 120, "vouches": 34, "robux": 6200},
                            {"date": "Woche 3", "members": 240, "vouches": 68, "robux": 10800},
                            {"date": "Woche 4", "members": 380, "vouches": 95, "robux": 14500},
                        ]
            except Exception:
                pass

    def _save_unlocked(self):
        """Schreibt die Daten OHNE den Lock zu nehmen.
        Nur aufrufen, wenn self.lock bereits gehalten wird (verhindert Deadlock)."""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def save(self):
        with self.lock:
            self._save_unlocked()

    def add_log(self, cat, text):
        t_str = discord.utils.utcnow().strftime("%H:%M:%S")
        entry = f"[{t_str}] {text}"
        with self.lock:
            if "live_logs" not in self.data:
                self.data["live_logs"] = {}
            if cat not in self.data["live_logs"]:
                self.data["live_logs"][cat] = []
            self.data["live_logs"][cat].insert(0, entry)
            self.data["live_logs"][cat] = self.data["live_logs"][cat][:50]

    def get_coins(self, user_id):
        return self.data["coins"].get(str(user_id), 0)

    def add_coins(self, user_id, amount):
        uid = str(user_id)
        self.data["coins"][uid] = self.data["coins"].get(uid, 0) + amount
        self.save()

    def add_purchase(self, username, product, robux_price):
        self.data["revenue_robux"] += robux_price
        self.data["revenue_euro"] += round(robux_price * 0.01, 2)
        time_str = discord.utils.utcnow().strftime("%H:%M")
        self.data["recent_purchases"].insert(
            0, {"user": username, "product": product, "time": time_str}
        )
        self.data["recent_purchases"] = self.data["recent_purchases"][:15]
        self.add_log("custom", f"Kauf absolviert: {username} kaufte {product} ({robux_price} R$)")
        self.save()

    def add_supporter_claim(self, username):
        if username not in self.data["supporter_leaderboard"]:
            self.data["supporter_leaderboard"][username] = {
                "claims": 0, "reviews": 0, "stars": 0,
            }
        self.data["supporter_leaderboard"][username]["claims"] += 1
        self.add_log("ticket", f"Supporter {username} übernahm ein Ticket")
        self.save()

    def add_supporter_review(self, username, stars_count):
        if username not in self.data["supporter_leaderboard"]:
            self.data["supporter_leaderboard"][username] = {
                "claims": 0, "reviews": 0, "stars": 0,
            }
        self.data["supporter_leaderboard"][username]["reviews"] += 1
        self.data["supporter_leaderboard"][username]["stars"] += stars_count
        self.add_log("custom", f"Kunden-Rezension: ⭐{stars_count} Sterne hinterlassen")
        self.save()

    def add_scam_block(self):
        self.data["scam_blocked"] += 1
        self.save()

    def next_ticket_number(self):
        """Fortlaufende Ticket-Nummer (z. B. ticket-0001)."""
        with self.lock:
            if "ticket_counter" not in self.data:
                self.data["ticket_counter"] = 0
            self.data["ticket_counter"] += 1
            num = self.data["ticket_counter"]
        self.save()
        return num

    # ==================== LIZENZ-KEYS & AUTO-DELIVERY ====================
    def add_keys(self, product_key, keys_list):
        """Fügt eine Liste von Keys zum Vorrat eines Produkts hinzu. Gibt Anzahl neuer Keys zurück."""
        added = 0
        with self.lock:
            if "license_keys" not in self.data:
                self.data["license_keys"] = {}
            if product_key not in self.data["license_keys"]:
                self.data["license_keys"][product_key] = []
            existing = {k["key"] for k in self.data["license_keys"][product_key]}
            for k in keys_list:
                k = k.strip()
                if k and k not in existing:
                    self.data["license_keys"][product_key].append(
                        {"key": k, "used": False, "used_by": None, "used_at": None}
                    )
                    existing.add(k)
                    added += 1
        self.save()
        return added

    def stock_count(self, product_key):
        """Anzahl freier (unbenutzter) Keys für ein Produkt."""
        with self.lock:
            keys = self.data.get("license_keys", {}).get(product_key, [])
            return sum(1 for k in keys if not k["used"])

    def all_stock(self):
        """Dict {product_key: freie_keys} über alle Produkte."""
        with self.lock:
            return {
                p: sum(1 for k in keys if not k["used"])
                for p, keys in self.data.get("license_keys", {}).items()
            }

    def claim_key(self, product_key, user_id, user_name):
        """Nimmt einen freien Key aus dem Vorrat, markiert ihn als benutzt und gibt ihn zurück.
        Gibt None zurück, wenn kein Key mehr verfügbar ist."""
        with self.lock:
            keys = self.data.get("license_keys", {}).get(product_key, [])
            for k in keys:
                if not k["used"]:
                    k["used"] = True
                    k["used_by"] = f"{user_name} ({user_id})"
                    k["used_at"] = discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    self._save_unlocked()
                    return k["key"]
        return None

    def redeem_key(self, key_str):
        """Sucht einen Key über ALLE Produkte. Markiert ihn als eingelöst.
        Gibt (product_key) zurück wenn gültig & frei, sonst None bei ungültig,
        oder 'used' wenn bereits benutzt."""
        with self.lock:
            for product_key, keys in self.data.get("license_keys", {}).items():
                for k in keys:
                    if k["key"] == key_str.strip():
                        if k["used"]:
                            return ("used", product_key)
                        return ("ok", product_key)
        return (None, None)

    def mark_key_redeemed(self, key_str, user_id, user_name):
        with self.lock:
            for product_key, keys in self.data.get("license_keys", {}).items():
                for k in keys:
                    if k["key"] == key_str.strip() and not k["used"]:
                        k["used"] = True
                        k["used_by"] = f"{user_name} ({user_id})"
                        k["used_at"] = discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        self._save_unlocked()
                        return True
        return False

    def log_sale(self, product_key, product_name, buyer_id, buyer_name, robux):
        """Protokolliert einen Verkauf für die Statistik."""
        with self.lock:
            if "sales_log" not in self.data:
                self.data["sales_log"] = []
            self.data["sales_log"].insert(0, {
                "product": product_key,
                "product_name": product_name,
                "buyer_id": str(buyer_id),
                "buyer_name": buyer_name,
                "robux": robux,
                "time": discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            })
            self.data["sales_log"] = self.data["sales_log"][:500]
        self.save()

    def sales_stats(self):
        """Aggregierte Verkaufsstatistik: Gesamt, heute, pro Produkt."""
        import datetime
        with self.lock:
            log = list(self.data.get("sales_log", []))
        today = discord.utils.utcnow().strftime("%Y-%m-%d")
        total_robux = sum(s["robux"] for s in log)
        today_robux = sum(s["robux"] for s in log if s["time"].startswith(today))
        per_product = {}
        for s in log:
            per_product[s["product_name"]] = per_product.get(s["product_name"], 0) + 1
        best = max(per_product.items(), key=lambda x: x[1])[0] if per_product else "—"
        return {
            "total_sales": len(log),
            "total_robux": total_robux,
            "today_sales": sum(1 for s in log if s["time"].startswith(today)),
            "today_robux": today_robux,
            "per_product": per_product,
            "best_product": best,
        }

    def sales_timeseries(self, days=7):
        """Tagesumsatz der letzten N Tage (für Diagramm). Liste von (label, robux)."""
        import datetime
        with self.lock:
            log = list(self.data.get("sales_log", []))
        out = []
        today = discord.utils.utcnow().date()
        for i in range(days - 1, -1, -1):
            day = today - datetime.timedelta(days=i)
            ds = day.strftime("%Y-%m-%d")
            robux = sum(s["robux"] for s in log if s["time"].startswith(ds))
            out.append((day.strftime("%d.%m"), robux))
        return out

    # ==================== WARENKORB ====================
    def get_cart(self, channel_id):
        with self.lock:
            return list(self.data.get("carts", {}).get(str(channel_id), []))

    def cart_add(self, channel_id, product_key):
        cid = str(channel_id)
        with self.lock:
            self.data.setdefault("carts", {}).setdefault(cid, []).append(product_key)
            cart = list(self.data["carts"][cid])
        self.save()
        return cart

    def cart_clear(self, channel_id):
        cid = str(channel_id)
        with self.lock:
            self.data.setdefault("carts", {})[cid] = []
        self.save()

    def cart_remove_one(self, channel_id, product_key):
        cid = str(channel_id)
        with self.lock:
            cart = self.data.setdefault("carts", {}).setdefault(cid, [])
            if product_key in cart:
                cart.remove(product_key)
            result = list(cart)
        self.save()
        return result

    # ==================== TICKET-TIMING / SUPPORTER-STATS ====================
    def ticket_open(self, channel_id):
        with self.lock:
            self.data.setdefault("ticket_meta", {})[str(channel_id)] = {
                "opened": discord.utils.utcnow().isoformat(),
                "claimed": None, "supporter": None, "closed": None,
            }
        self.save()

    def ticket_claim(self, channel_id, supporter_name):
        cid = str(channel_id)
        with self.lock:
            meta = self.data.setdefault("ticket_meta", {}).get(cid)
            if meta and not meta.get("claimed"):
                meta["claimed"] = discord.utils.utcnow().isoformat()
                meta["supporter"] = supporter_name
        self.save()

    def ticket_close(self, channel_id):
        cid = str(channel_id)
        with self.lock:
            meta = self.data.setdefault("ticket_meta", {}).get(cid)
            if meta:
                meta["closed"] = discord.utils.utcnow().isoformat()
        self.save()

    def ticket_stats(self):
        """Ø-Antwortzeit + Tickets pro Supporter + Zufriedenheit."""
        import datetime
        with self.lock:
            metas = list(self.data.get("ticket_meta", {}).values())
            board = dict(self.data.get("supporter_leaderboard", {}))
        response_secs = []
        per_supporter = {}
        for m in metas:
            if m.get("opened") and m.get("claimed"):
                try:
                    o = datetime.datetime.fromisoformat(m["opened"])
                    c = datetime.datetime.fromisoformat(m["claimed"])
                    response_secs.append((c - o).total_seconds())
                except Exception:
                    pass
            if m.get("supporter"):
                per_supporter[m["supporter"]] = per_supporter.get(m["supporter"], 0) + 1
        avg = sum(response_secs) / len(response_secs) if response_secs else 0
        # Zufriedenheit aus Leaderboard (stars / reviews)
        total_stars = sum(v.get("stars", 0) for v in board.values())
        total_reviews = sum(v.get("reviews", 0) for v in board.values())
        satisfaction = (total_stars / total_reviews) if total_reviews else 0
        return {
            "avg_response_secs": round(avg),
            "per_supporter": per_supporter,
            "total_tickets": len(metas),
            "satisfaction": round(satisfaction, 2),
            "leaderboard": board,
        }

    def supporter_of_month(self):
        """Berechnet den Supporter des Monats anhand der meisten Sterne im Leaderboard."""
        month = discord.utils.utcnow().strftime("%Y-%m")
        with self.lock:
            board = dict(self.data.get("supporter_leaderboard", {}))
        if not board:
            return None
        winner = max(board.items(), key=lambda x: x[1].get("stars", 0))
        with self.lock:
            self.data["supporter_of_month"] = {"month": month, "winner": winner[0]}
        self.save()
        return {"name": winner[0], **winner[1]}

    # ==================== FAQ ====================
    def faq_lookup(self, text):
        """Sucht ein FAQ-Keyword im Text. Gibt Antwort oder None."""
        low = text.lower()
        with self.lock:
            faq = dict(self.data.get("faq", {}))
        for keyword, answer in faq.items():
            if keyword.lower() in low:
                return answer
        return None

    def faq_set(self, keyword, answer):
        with self.lock:
            self.data.setdefault("faq", {})[keyword.lower()] = answer
        self.save()

    def faq_all(self):
        with self.lock:
            return dict(self.data.get("faq", {}))

    # ==================== SPRACHE ====================
    def get_lang(self, user_id):
        with self.lock:
            return self.data.get("user_lang", {}).get(str(user_id), "de")

    def set_lang(self, user_id, lang):
        with self.lock:
            self.data.setdefault("user_lang", {})[str(user_id)] = lang
        self.save()

    def add_ticket_transcript(self, channel_name, closed_by_user, messages):
        with self.lock:
            if "transcripts" not in self.data:
                self.data["transcripts"] = {}
            self.data["transcripts"][channel_name] = {
                "closed_by": closed_by_user.name,
                "closed_by_id": str(closed_by_user.id),
                "closed_by_avatar": closed_by_user.display_avatar.url if closed_by_user.display_avatar else "https://cdn.discordapp.com/embed/avatars/0.png",
                "time": discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "messages": messages
            }
        self.save()

    def get_transcripts_list(self):
        with self.lock:
            if "transcripts" not in self.data:
                return {}
            return dict(self.data["transcripts"])

    def add_user_vouch(self, user_id):
        uid = str(user_id)
        with self.lock:
            if "user_vouches" not in self.data: self.data["user_vouches"] = {}
            self.data["user_vouches"][uid] = self.data["user_vouches"].get(uid, 0) + 1
            count = self.data["user_vouches"][uid]
        self.save()
        return count

    def set_user_verified(self, user_id, roblox_id, roblox_name):
        uid = str(user_id)
        with self.lock:
            if "verified_users" not in self.data: self.data["verified_users"] = {}
            self.data["verified_users"][uid] = {
                "roblox_id": roblox_id,
                "roblox_name": roblox_name,
                "claimed_gamepass": False
            }
        self.save()

    def get_verified_users(self):
        with self.lock:
            return dict(self.data.get("verified_users", {}))

    def mark_gamepass_claimed(self, user_id):
        uid = str(user_id)
        with self.lock:
            if uid in self.data.get("verified_users", {}):
                self.data["verified_users"][uid]["claimed_gamepass"] = True
        self.save()

    def get_vip_serial(self, user_id):
        uid = str(user_id)
        with self.lock:
            if "vip_serials" not in self.data: self.data["vip_serials"] = {}
            if uid not in self.data["vip_serials"]:
                num = len(self.data["vip_serials"]) + 1
                self.data["vip_serials"][uid] = f"VIP-#{num:04d}"
            serial = self.data["vip_serials"][uid]
        self.save()
        return serial

    def add_web_order(self, user_identifier, product_name, payment_mode):
        with self.lock:
            if "web_orders" not in self.data: self.data["web_orders"] = []
            self.data["web_orders"].append({
                "user": user_identifier,
                "product": product_name,
                "mode": payment_mode,
                "status": "pending"
            })
        self.save()

    def pop_pending_web_orders(self):
        with self.lock:
            if "web_orders" not in self.data: return []
            pending = [o for o in self.data["web_orders"] if o["status"] == "pending"]
            for o in pending:
                o["status"] = "processed"
            return pending

    def get_dashboard_data(self, bot_client):
        tot_m = 0
        on_m = 0
        bst = 0
        op_tix = 0
        v_cnt = 0
        tix_list = []
        ping = round(bot_client.latency * 1000) if bot_client and bot_client.latency and not math.isnan(bot_client.latency) else 18

        if bot_client:
            for g in bot_client.guilds:
                tot_m += len(g.members)
                bst += g.premium_subscription_count
                for m in g.members:
                    if m.status != discord.Status.offline:
                        on_m += 1
                    if any(
                        "Verified" in r.name or "𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱" in r.name
                        for r in m.roles
                    ):
                        v_cnt += 1
                for c in g.text_channels:
                    if any(
                        x in c.name.lower()
                        for x in ["kauf-", "support-", "partner-"]
                    ) or (c.topic and "von" in c.topic):
                        op_tix += 1
                        tix_list.append({"name": c.name, "topic": c.topic or "Support"})

        with self.lock:
            dc = dict(self.data)
            dc["live_discord"] = {
                "total_members": tot_m,
                "online_members": on_m,
                "boosters": bst,
                "open_tickets": op_tix,
                "verified_members": v_cnt,
                "ping_ms": ping,
                "tickets_list": tix_list,
            }
            return dc


db = Database()
