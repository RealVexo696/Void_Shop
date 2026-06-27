"""
Database - Persistente Datenspeicherung (shop_db.json)
Inklusive automatischem Ticket-Archiv, Vouch-Leveling, Auto-Gamepass Tracker,
Web-Store Orders und Analytics-Historie.
"""

import json
import os
import threading

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
                    if "analytics_history" not in self.data:
                        self.data["analytics_history"] = [
                            {"date": "Woche 1", "members": 50, "vouches": 12, "robux": 2500},
                            {"date": "Woche 2", "members": 120, "vouches": 34, "robux": 6200},
                            {"date": "Woche 3", "members": 240, "vouches": 68, "robux": 10800},
                            {"date": "Woche 4", "members": 380, "vouches": 95, "robux": 14500},
                        ]
            except Exception:
                pass

    def save(self):
        with self.lock:
            try:
                with open(self.filename, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

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
        ping = round(bot_client.latency * 1000) if bot_client and bot_client.latency else 18

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
