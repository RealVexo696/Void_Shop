#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛍️ VOID_SHOP v1.0 – ALL-IN-ONE
RealVexo696 / Void_Shop
Companion to VOID-TOOLS v2.6 by V0id-v2

ALL 7 FEATURES IN ONE FILE:
1. 🛍️ Auto-Delivery      (!checkbuy → <5s DM)
2. 🔐 Bio-Code-Auth      (!verify → void-8392)
3. 🚨 AntiScam Shield    (Link-Filter <200ms)
4. 📈 FOMO Live Ticker   (#live-käufe)
5. 🪙 Void-Coins Economy (!coins !shop !redeem)
6. 👑 Web Dashboard      (http://localhost:5000)
7. 📜 LOGSYSTEM 2.0      (12 dedizierte Kanäle)

Python 3.11+ · discord.py 2.3.2 · Flask 3.0.3 · aiosqlite
AGPL-3.0

Run:
  pip install discord.py aiohttp aiosqlite Flask python-dotenv
  python void_shop_all_in_one.py
"""
import discord
from discord.ext import commands
import aiohttp
import aiosqlite
import asyncio
import sqlite3
import json
import os
import sys
import random
import re
import datetime
import time
import threading
from urllib.parse import urlparse

# =====================================================================
#  🛠️  CONFIG – HIER BEARBEITEN
# =====================================================================

TOKEN = os.getenv("DISCORD_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")
GUILD_ID = int(os.getenv("GUILD_ID", "0") or 0)
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)
PREFIX = "!"

# --- 12 LOG KANÄLE ---
LOG_JOIN      = int(os.getenv("LOG_JOIN", "0") or 0)      # 📥 join-leave
LOG_VOICE     = int(os.getenv("LOG_VOICE", "0") or 0)     # 🎙️ voice
LOG_MESSAGE   = int(os.getenv("LOG_MESSAGE", "0") or 0)   # 💬 message
LOG_SHOP      = int(os.getenv("LOG_SHOP", "0") or 0)      # 🛍️ shop
LOG_VERIFY    = int(os.getenv("LOG_VERIFY", "0") or 0)    # 🔐 verify
LOG_ANTISCAM  = int(os.getenv("LOG_ANTISCAM", "0") or 0)  # 🚨 antiscam
LOG_TICKET    = int(os.getenv("LOG_TICKET", "0") or 0)    # 🎫 ticket
LOG_COINS     = int(os.getenv("LOG_COINS", "0") or 0)     # 🪙 coins
LOG_MOD       = int(os.getenv("LOG_MOD", "0") or 0)       # ⚙️ mod
LOG_TICKER    = int(os.getenv("LOG_TICKER", "0") or 0)    # 📈 ticker / live-käufe
LOG_BOT       = int(os.getenv("LOG_BOT", "0") or 0)       # 🔧 bot
LOG_OWNER     = int(os.getenv("LOG_OWNER", "0") or 0)     # 👑 owner

LOG_CHANNELS = {
    "join": LOG_JOIN, "voice": LOG_VOICE, "message": LOG_MESSAGE,
    "shop": LOG_SHOP, "verify": LOG_VERIFY, "antiscam": LOG_ANTISCAM,
    "ticket": LOG_TICKET, "coins": LOG_COINS, "mod": LOG_MOD,
    "ticker": LOG_TICKER, "bot": LOG_BOT, "owner": LOG_OWNER,
}

TICKER_CHANNEL_ID = LOG_TICKER  # FOMO Kanal = ticker log

# Rollen (optional)
ROLE_VERIFIED  = 0
ROLE_CUSTOMER  = 0
ROLE_STAFF     = 0
ROLE_VIP       = 0

# Roblox
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE", "")  # optional .ROBLOSECURITY

# Dashboard
DASHBOARD_ENABLED = True
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 5000
DASHBOARD_SECRET = "voidshop-secret-change-me"
DASHBOARD_LOGIN_CODE = "voidshop"  # oder str(OWNER_ID)

# Datenbank
DATABASE_PATH = "void_shop.db"

# =====================================================================
#  🛍️  PRODUKTE – AUTO-DELIVERY
# =====================================================================
PRODUCTS = {
    "fastflags_premium": {
        "name": "Premium FastFlags Paket",
        "gamepass_id": 12345678,
        "robux_price": 250,
        "deliver": {
            "title": "🎉 Danke für deinen Kauf – Premium FastFlags",
            "message": "Hier ist dein **Premium FastFlags Paket** – sofortige Lieferung!\n\n📎 Download:\n• FastFlags JSON\n• Anleitung PDF\n• T-Shirt Vorlage\n\nSupport: https://discord.gg/voidv2\nDanke, dass du Void_Shop vertraust! <3",
            "files": [
                "https://cdn.void-shop.local/fastflags/premium.json",
                "https://cdn.void-shop.local/fastflags/README.pdf"
            ]
        },
        "coins_reward": 50,
        "role_give": "CUSTOMER"
    },
    "tshirt_template_pro": {
        "name": "T-Shirt Template Pro",
        "gamepass_id": 12345679,
        "robux_price": 120,
        "deliver": {
            "title": "👕 T-Shirt Template Pro",
            "message": "Dein **T-Shirt Template Pro** Paket!\n\nEnthalten:\n• 12x PSD Vorlagen\n• 30x PNG Overlays\n• Roblox Upload Guide\n\nViel Spaß beim Designen!",
            "files": ["https://cdn.void-shop.local/tshirt/pro_pack.zip"]
        },
        "coins_reward": 50,
        "role_give": "CUSTOMER"
    },
    "fastflags_ultra": {
        "name": "FastFlags Ultra",
        "gamepass_id": 12345680,
        "robux_price": 499,
        "deliver": {
            "title": "⚡ FastFlags Ultra – Danke!",
            "message": "Ultra Paket freigeschaltet!\n\n• Ultra FastFlags\n• FPS Booster\n• Private Discord VIP Zugang\n\nLink läuft 72h.",
            "files": ["https://cdn.void-shop.local/fastflags/ultra.zip"]
        },
        "coins_reward": 50,
        "role_give": "VIP"
    },
    "starter_bundle": {
        "name": "Starter Bundle",
        "gamepass_id": 12345681,
        "robux_price": 75,
        "deliver": {
            "title": "📦 Starter Bundle",
            "message": "Danke für deinen ersten Kauf!\n\nDein Download: https://cdn.void-shop.local/starter/bundle.zip\n\n+50 Void-Coins wurden gutgeschrieben!"
        },
        "coins_reward": 50,
        "role_give": "CUSTOMER"
    }
}

# =====================================================================
#  🪙  COIN ECONOMY
# =====================================================================
COIN_REWARDS = {
    "verify": 10,
    "invite": 25,
    "purchase": 50,
    "vouch_5star": 30,
    "daily": 5,
}
SHOP_REWARDS = {
    150: {"name": "15% Rabatt-Code", "type": "discount"},
    300: {"name": "Gratis T-Shirt Template", "type": "product"},
    500: {"name": "VIP Role 30 Tage", "type": "role"},
    800: {"name": "Premium FastFlags Paket", "type": "product"},
}

# =====================================================================
#  🚨  ANTISCAM WHITELIST
# =====================================================================
SAFE_DOMAINS = [
    "roblox.com", "www.roblox.com", "web.roblox.com",
    "discord.com", "discord.gg", "discordapp.com", "cdn.discordapp.com",
    "youtube.com", "youtu.be", "www.youtube.com",
    "github.com", "t.me", "voidtool", "voidv2",
    "twitter.com", "x.com", "twitch.tv", "tiktok.com",
    "paypal.com", "stripe.com",
]
SUSPICIOUS_KEYWORDS = [
    "roblóx", "rob1ox", "r0blox", "roblox-free", "free-robux",
    "dlscord", "discorde", "disord", "discord-nitro",
    "steamcommunity-n", "steancommunity", "free-nitro", "nitro-free"
]

# =====================================================================
#  🗄️  DATABASE
# =====================================================================
DB_SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(
  discord_id INTEGER PRIMARY KEY,
  roblox_id INTEGER,
  roblox_name TEXT,
  verified INTEGER DEFAULT 0,
  coins INTEGER DEFAULT 0,
  total_spent_robux INTEGER DEFAULT 0,
  purchases INTEGER DEFAULT 0,
  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  verified_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS verify_codes(
  discord_id INTEGER PRIMARY KEY,
  roblox_id INTEGER,
  roblox_name TEXT,
  code TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS purchases(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  discord_id INTEGER,
  roblox_id INTEGER,
  product_key TEXT,
  gamepass_id INTEGER,
  robux_price INTEGER,
  delivered INTEGER DEFAULT 0,
  delivery_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS deliveries(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  purchase_id INTEGER,
  discord_id INTEGER,
  product_key TEXT,
  delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  dm_message_id TEXT,
  success INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS coins_ledger(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  discord_id INTEGER,
  amount INTEGER,
  reason TEXT,
  meta TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS invites(
  inviter_id INTEGER,
  invited_id INTEGER PRIMARY KEY,
  joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  rewarded INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS staff_stats(
  staff_id INTEGER PRIMARY KEY,
  tickets_claimed INTEGER DEFAULT 0,
  tickets_closed INTEGER DEFAULT 0,
  avg_response_sec INTEGER DEFAULT 0,
  rating_sum INTEGER DEFAULT 0,
  rating_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS antiscam_hits(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  discord_id INTEGER,
  channel_id INTEGER,
  url TEXT,
  reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS logs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  log_type TEXT,
  discord_id INTEGER,
  channel_id INTEGER,
  content TEXT,
  meta TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS vouches(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  discord_id INTEGER,
  stars INTEGER,
  message TEXT,
  coins_awarded INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS revenue_daily(
  day TEXT PRIMARY KEY,
  robux INTEGER DEFAULT 0,
  purchases INTEGER DEFAULT 0,
  customers INTEGER DEFAULT 0
);
"""

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript(DB_SCHEMA)
        await db.commit()

# =====================================================================
#  🌐  ROBLOX API
# =====================================================================
_session: aiohttp.ClientSession | None = None
async def get_session():
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
    return _session

async def roblox_username_to_id(username: str):
    s = await get_session()
    try:
        async with s.post("https://users.roblox.com/v1/usernames/users",
            json={"usernames":[username],"excludeBannedUsers":True}) as r:
            j = await r.json()
            data = j.get("data", [])
            if data:
                u = data[0]
                return u["id"], u.get("displayName", u["name"])
    except Exception: pass
    return None

async def roblox_get_description(user_id: int) -> str:
    s = await get_session()
    try:
        async with s.get(f"https://users.roblox.com/v1/users/{user_id}") as r:
            if r.status == 200:
                j = await r.json()
                return j.get("description","") or ""
    except Exception: pass
    return ""

async def roblox_owns_gamepass(roblox_id: int, gamepass_id: int) -> bool:
    s = await get_session()
    try:
        url = f"https://inventory.roblox.com/v1/users/{roblox_id}/items/GamePass/{gamepass_id}"
        headers = {}
        if ROBLOX_COOKIE:
            headers["Cookie"] = f".ROBLOSECURITY={ROBLOX_COOKIE}"
        async with s.get(url, headers=headers) as r:
            if r.status == 200:
                j = await r.json()
                return len(j.get("data", [])) > 0
    except Exception: pass
    return False

# --- Bio verify ---
def generate_bio_code() -> str:
    return f"void-{random.randint(1000,9999)}"

async def check_bio_code(roblox_id: int, code: str) -> bool:
    desc = await roblox_get_description(roblox_id)
    return code.lower() in desc.lower()

# =====================================================================
#  🛍️  AUTO-DELIVERY SERVICE
# =====================================================================
async def find_owned_product(roblox_id: int):
    for key, p in PRODUCTS.items():
        gp = p.get("gamepass_id")
        if gp and await roblox_owns_gamepass(roblox_id, gp):
            async with aiosqlite.connect(DATABASE_PATH) as db:
                cur = await db.execute(
                    "SELECT id FROM purchases WHERE roblox_id=? AND product_key=? AND delivered=1",
                    (roblox_id, key))
                if await cur.fetchone():
                    continue
            return key, p
    return None, None

async def record_purchase(discord_id:int, roblox_id:int, product_key:str, product:dict):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO purchases(discord_id,roblox_id,product_key,gamepass_id,robux_price,delivered,delivery_at) VALUES(?,?,?,?,?,1,CURRENT_TIMESTAMP)",
            (discord_id, roblox_id, product_key, product.get("gamepass_id"), product.get("robux_price",0))
        )
        await db.execute(
            "UPDATE users SET purchases=purchases+1, total_spent_robux=total_spent_robux+? WHERE discord_id=?",
            (product.get("robux_price",0), discord_id)
        )
        today = datetime.date.today().isoformat()
        await db.execute(
            "INSERT INTO revenue_daily(day,robux,purchases,customers) VALUES(?,?,1,1) ON CONFLICT(day) DO UPDATE SET robux=robux+excluded.robux, purchases=purchases+1",
            (today, product.get("robux_price",0))
        )
        await db.commit()
        cur = await db.execute("SELECT last_insert_rowid()")
        row = await cur.fetchone()
        return row[0] if row else None

# =====================================================================
#  🪙  COINS
# =====================================================================
async def add_coins(discord_id:int, amount:int, reason:str, meta:str=""):
    if amount==0: return
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO users(discord_id,coins) VALUES(?,0)", (discord_id,))
        await db.execute("UPDATE users SET coins=coins+? WHERE discord_id=?", (amount, discord_id))
        await db.execute("INSERT INTO coins_ledger(discord_id,amount,reason,meta) VALUES(?,?,?,?)",
                         (discord_id, amount, reason, meta))
        await db.commit()

async def get_coins(discord_id:int)->int:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT coins FROM users WHERE discord_id=?", (discord_id,))
        row = await cur.fetchone()
        return row[0] if row else 0

async def spend_coins(discord_id:int, amount:int, reason:str)->bool:
    bal = await get_coins(discord_id)
    if bal < amount: return False
    await add_coins(discord_id, -amount, reason)
    return True

# =====================================================================
#  🚨  ANTISCAM ENGINE
# =====================================================================
URL_RE = re.compile(r'https?://[^\s<]+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s<]*)?', re.I)

def extract_urls(text:str): return URL_RE.findall(text or "")
def normalize_domain(url:str)->str:
    if not url.startswith("http"): url="http://"+url
    try:
        p=urlparse(url)
        return (p.hostname or "").lower().lstrip("www.")
    except: return ""

def levenshtein(a:str,b:str)->int:
    if a==b: return 0
    la,lb=len(a),len(b)
    if la==0: return lb
    if lb==0: return la
    prev=list(range(lb+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1):
            cost=0 if ca==cb else 1
            cur.append(min(cur[-1]+1, prev[j]+1, prev[j-1]+cost))
        prev=cur
    return prev[-1]

def is_safe_domain(host:str)->bool:
    if not host: return False
    for safe in SAFE_DOMAINS:
        if host==safe or host.endswith("."+safe): return True
    for target in ["roblox.com","discord.com","discord.gg","youtube.com"]:
        if levenshtein(host,target)<=2 and host!=target: return False
        if target.replace(".","") in host.replace(".","") and host!=target and not host.endswith("."+target):
            return False
    return True

def scan_message_antiscam(content:str)->list:
    bad=[]
    for url in extract_urls(content):
        host=normalize_domain(url)
        if not host: continue
        low=(url+" "+host).lower()
        if any(s in low for s in SUSPICIOUS_KEYWORDS):
            bad.append({"url":url,"host":host,"reason":"typosquatting / scam keyword"})
            continue
        if not is_safe_domain(host):
            bad.append({"url":url,"host":host,"reason":"domain not whitelisted"})
    return bad

# =====================================================================
#  📜  LOGGER SERVICE – 12 KANÄLE
# =====================================================================
LOG_COLORS = {
    "join":0x2ecc71, "voice":0x3498db, "message":0xe67e22, "shop":0xf1c40f,
    "verify":0x9b59b6, "antiscam":0xe74c3c, "ticket":0x1abc9c,
    "coins":0xFFD700, "mod":0xe74c3c, "ticker":0xFFD700,
    "bot":0x95a5a6, "owner":0x2c3e50,
}
async def send_log(bot, log_type:str, embed:discord.Embed=None, content:str=None,
                   discord_id:int=None, channel_id:int=None, meta:str=""):
    chan_id = LOG_CHANNELS.get(log_type,0)
    if not chan_id: return
    ch = bot.get_channel(chan_id)
    if ch is None:
        try: ch = await bot.fetch_channel(chan_id)
        except: return
    try:
        if embed:
            if not embed.timestamp: embed.timestamp = datetime.datetime.utcnow()
            if not embed.color: embed.color = LOG_COLORS.get(log_type,0x7d7d7d)
        await ch.send(content=content, embed=embed)
    except: pass
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT INTO logs(log_type,discord_id,channel_id,content,meta) VALUES(?,?,?,?,?)",
                (log_type, discord_id, channel_id, content or (embed.title if embed else ""), meta)
            )
            await db.commit()
    except: pass

def make_embed(title, description, color=None, user:discord.Member=None):
    e = discord.Embed(title=title, description=description, timestamp=datetime.datetime.utcnow())
    if color: e.color=color
    if user:
        try:
            e.set_thumbnail(url=user.display_avatar.url)
            e.set_footer(text=f"{user} • {user.id}", icon_url=user.display_avatar.url)
        except: pass
    return e

# =====================================================================
#  📈  TICKER + REVENUE
# =====================================================================
async def send_purchase_ticker(bot, channel_id:int, buyer:discord.Member, product_name:str, robux:int):
    ch = bot.get_channel(channel_id) or (await bot.fetch_channel(channel_id) if channel_id else None)
    if not ch: return
    embed = discord.Embed(
        title="🎉 Neuer Kauf!",
        description=f"**{buyer.mention}** hat soeben **{product_name}** erworben!\nVielen Dank! ❤️",
        color=0xFFD700, timestamp=datetime.datetime.utcnow()
    )
    try: embed.set_thumbnail(url=buyer.display_avatar.url)
    except: pass
    embed.add_field(name="Produkt", value=product_name, inline=True)
    embed.add_field(name="Preis", value=f"{robux} Robux", inline=True)
    embed.set_footer(text="Void_Shop • Live Käufe")
    try: await ch.send(embed=embed)
    except: pass

async def get_revenue_summary():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT COALESCE(SUM(robux_price),0), COUNT(*) FROM purchases WHERE delivered=1")
        total_robux, total_purchases = await cur.fetchone()
        cur = await db.execute("SELECT COALESCE(SUM(robux_price),0), COUNT(*) FROM purchases WHERE delivered=1 AND created_at >= date('now','start of month')")
        month_robux, month_purchases = await cur.fetchone()
        cur = await db.execute("SELECT COALESCE(SUM(robux_price),0), COUNT(*) FROM purchases WHERE delivered=1 AND date(created_at)=date('now')")
        today_robux, today_purchases = await cur.fetchone()
        cur = await db.execute("SELECT product_key, COUNT(*), SUM(robux_price) FROM purchases WHERE delivered=1 GROUP BY product_key ORDER BY SUM(robux_price) DESC LIMIT 5")
        top = await cur.fetchall()
        cur = await db.execute("SELECT day, robux, purchases FROM revenue_daily ORDER BY day DESC LIMIT 30")
        daily = await cur.fetchall()
    return {
        "total_robux": total_robux or 0, "total_purchases": total_purchases or 0,
        "month_robux": month_robux or 0, "month_purchases": month_purchases or 0,
        "today_robux": today_robux or 0, "today_purchases": today_purchases or 0,
        "top_products": top, "daily": list(reversed(daily))
    }

# =====================================================================
#  🤖  DISCORD BOT
# =====================================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None, case_insensitive=True)

# ---------- VERIFY VIEW ----------
class VerifyView(discord.ui.View):
    def __init__(self, discord_id, roblox_id, roblox_name, code):
        super().__init__(timeout=300)
        self.discord_id=discord_id; self.roblox_id=roblox_id
        self.roblox_name=roblox_name; self.code=code

    @discord.ui.button(label="✅ Bestätigen", style=discord.ButtonStyle.green)
    async def confirm(self, interaction:discord.Interaction, button:discord.ui.Button):
        if interaction.user.id != self.discord_id:
            return await interaction.response.send_message("Nicht dein Verify!", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        ok = await check_bio_code(self.roblox_id, self.code)
        if not ok:
            emb = discord.Embed(title="❌ Code nicht gefunden",
                description=f"Ich sehe `{self.code}` **nicht** in deiner Roblox Bio.\n\n1. https://www.roblox.com/users/{self.roblox_id}/profile\n2. Bearbeiten → Beschreibung → `{self.code}` einfügen\n3. Speichern → hier nochmal Bestätigen",
                color=0xe74c3c)
            return await interaction.followup.send(embed=emb, ephemeral=True)
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "INSERT INTO users(discord_id,roblox_id,roblox_name,verified,verified_at,coins) VALUES(?,?,?,?,CURRENT_TIMESTAMP,COALESCE((SELECT coins FROM users WHERE discord_id=?),0)) ON CONFLICT(discord_id) DO UPDATE SET roblox_id=excluded.roblox_id, roblox_name=excluded.roblox_name, verified=1, verified_at=CURRENT_TIMESTAMP",
                (self.discord_id, self.roblox_id, self.roblox_name, self.discord_id))
            await db.execute("DELETE FROM verify_codes WHERE discord_id=?", (self.discord_id,))
            await db.commit()
        if ROLE_VERIFIED:
            try:
                role = interaction.guild.get_role(ROLE_VERIFIED)
                if role: await interaction.user.add_roles(role, reason="Roblox Bio Verify")
            except: pass
        await add_coins(self.discord_id, COIN_REWARDS["verify"], "verify")
        emb = discord.Embed(title="✅ Verifiziert!",
            description=f"Willkommen **{self.roblox_name}**!\nRoblox ID: `{self.roblox_id}`\n\n+{COIN_REWARDS['verify']} Void-Coins gutgeschrieben!",
            color=0x2ecc71)
        await interaction.followup.send(embed=emb, ephemeral=True)
        log_emb = make_embed("🔐 Verify Erfolg", f"{interaction.user.mention} → **{self.roblox_name}** (`{self.roblox_id}`)\nCode: `{self.code}`", 0x2ecc71, interaction.user)
        await send_log(bot, "verify", log_emb, discord_id=self.discord_id)
        self.stop()

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction:discord.Interaction, button:discord.ui.Button):
        if interaction.user.id != self.discord_id:
            return await interaction.response.send_message("Nicht dein Verify!", ephemeral=True)
        await interaction.response.send_message("Abgebrochen.", ephemeral=True)
        self.stop()

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f"""
 \033[91m
 ██╗   ██╗ ██████╗ ██╗██████╗     ███████╗██╗  ██╗ ██████╗ ██████╗ 
 ██║   ██║██╔═══██╗██║██╔══██╗    ██╔════╝██║  ██║██╔═══██╗██╔══██╗
 ██║   ██║██║   ██║██║██║  ██║    ███████╗███████║██║   ██║██████╔╝
 ╚██╗ ██╔╝██║   ██║██║██║  ██║    ╚════██║██╔══██║██║   ██║██╔═══╝ 
  ╚████╔╝ ╚██████╔╝██║██████╔╝    ███████║██║  ██║╚██████╔╝██║     
   ╚═══╝   ╚═════╝ ╚═╝╚═════╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     
 \033[0m
  Void_Shop v1.0 ALL-IN-ONE
  Bot: {bot.user} ({bot.user.id})
  Guilds: {len(bot.guilds)}
  Latency: {round(bot.latency*1000)}ms

  Features:
   🛍️ Auto-Delivery   🔐 Bio-Code-Auth   🚨 AntiScam
   📈 FOMO Ticker      🪙 Void-Coins      👑 Web Dashboard
   📜 12-Channel Logs

  Dashboard: http://localhost:{DASHBOARD_PORT}
""")
    await send_log(bot, "bot", make_embed("🤖 Bot Online",
        f"**{bot.user}** gestartet\nGuilds: {len(bot.guilds)}\nLatenz: {round(bot.latency*1000)}ms", 0x2ecc71))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound): return
    if isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(f"⏳ Cooldown: {error.retry_after:.0f}s", delete_after=5)
    if isinstance(error, commands.CheckFailure):
        return await ctx.send("❌ Keine Berechtigung.", delete_after=5)
    print(f"[ERR] {error}")
    try: await ctx.send(f"⚠️ {error}", delete_after=15)
    except: pass

# --- LOGSYSTEM: JOIN/LEAVE ---
@bot.event
async def on_member_join(member):
    emb = make_embed("📥 Mitglied beigetreten",
        f"{member.mention} **{member}**\nAccount erstellt: <t:{int(member.created_at.timestamp())}:R>\nID: `{member.id}`",
        0x2ecc71, member)
    await send_log(bot, "join", emb, discord_id=member.id)

@bot.event
async def on_member_remove(member):
    emb = make_embed("📤 Mitglied verlassen", f"**{member}**\n`{member.id}`", 0xe74c3c, member)
    await send_log(bot, "join", emb, discord_id=member.id)

# --- VOICE LOGS ---
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel == after.channel:
        changes=[]
        if before.self_mute != after.self_mute: changes.append(f"Mute {before.self_mute}→{after.self_mute}")
        if before.self_deaf != after.self_deaf: changes.append(f"Deaf {before.self_deaf}→{after.self_deaf}")
        if before.self_stream != after.self_stream: changes.append(f"Stream {before.self_stream}→{after.self_stream}")
        if changes:
            emb = make_embed("🎙️ Voice Update", f"{member.mention}\n"+"\n".join(changes), 0x3498db, member)
            await send_log(bot,"voice",emb,discord_id=member.id,channel_id=(after.channel.id if after.channel else None))
        return
    if after.channel and not before.channel:
        desc=f"{member.mention} → 🔊 **{after.channel.name}**"; color=0x2ecc71
    elif before.channel and not after.channel:
        desc=f"{member.mention} ← 🔊 **{before.channel.name}**"; color=0xe74c3c
    else:
        desc=f"{member.mention} 🔀 **{before.channel.name}** → **{after.channel.name}**"; color=0xf39c12
    emb = make_embed("🎙️ Voice", desc, color, member)
    await send_log(bot,"voice",emb,discord_id=member.id,
        channel_id=(after.channel.id if after.channel else before.channel.id if before.channel else None))

# --- MESSAGE LOGS + ANTISCAM + VOUCH ---
@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message); return
    if message.guild:
        # --- AntiScam ---
        bad = scan_message_antiscam(message.content)
        if bad:
            try: await message.delete()
            except: pass
            try:
                emb_warn = discord.Embed(title="🚨 Link blockiert – Anti-Scam",
                    description="Dein Link wurde entfernt (nicht gewhitelistet).\n\n**Erlaubt:** `roblox.com`, `discord.com`, `discord.gg`, `youtube.com`, `github.com`",
                    color=0xe74c3c)
                await message.channel.send(f"{message.author.mention}", embed=emb_warn, delete_after=20)
            except: pass
            details = "\n".join([f"• `{b['url']}` → {b['reason']}" for b in bad])
            log_emb = make_embed("🚨 AntiScam – Link gelöscht",
                f"**User:** {message.author.mention}\n**Channel:** {message.channel.mention}\n\n{details}\n\n```{message.content[:800]}```",
                0xe74c3c, message.author)
            await send_log(bot,"antiscam",log_emb,discord_id=message.author.id,channel_id=message.channel.id,meta=str(bad))
            async with aiosqlite.connect(DATABASE_PATH) as db:
                for b in bad:
                    await db.execute("INSERT INTO antiscam_hits(discord_id,channel_id,url,reason) VALUES(?,?,?,?)",
                        (message.author.id, message.channel.id, b["url"], b["reason"]))
                await db.commit()
            return  # block further processing
        # --- Vouch 5★ Coins ---
        if "vouch" in message.channel.name.lower():
            c = message.content.lower()
            if message.content.count("⭐")>=5 or "5/5" in c or "5★" in c or "5 sterne" in c:
                await add_coins(message.author.id, COIN_REWARDS["vouch_5star"], "vouch_5star")
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    await db.execute("INSERT INTO vouches(discord_id,stars,message,coins_awarded) VALUES(?,?,?,?)",
                        (message.author.id,5,message.content[:500],COIN_REWARDS["vouch_5star"]))
                    await db.commit()
                try:
                    await message.add_reaction("✅")
                    await message.reply(f"Danke für dein 5⭐ Vouch! +{COIN_REWARDS['vouch_5star']} Coins!", delete_after=15)
                except: pass
                log_emb = make_embed("🪙 Vouch belohnt",
                    f"{message.author.mention} 5★ → +{COIN_REWARDS['vouch_5star']} Coins",0xFFD700,message.author)
                await send_log(bot,"coins",log_emb,discord_id=message.author.id,channel_id=message.channel.id)
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild: return
    content = (message.content[:1000]+"…") if len(message.content)>1000 else message.content
    emb = make_embed("🗑️ Nachricht gelöscht",
        f"**Channel:** {message.channel.mention}\n**Author:** {message.author.mention}\n\n```{content or '[Embed/Attachment]'}```",
        0xe74c3c, message.author)
    await send_log(bot,"message",emb,discord_id=message.author.id,channel_id=message.channel.id,meta=message.content)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild: return
    if before.content == after.content: return
    emb = discord.Embed(title="✏️ Nachricht bearbeitet", color=0xf39c12, timestamp=datetime.datetime.utcnow())
    emb.add_field(name="Vorher", value=(before.content[:1000] or "…"), inline=False)
    emb.add_field(name="Nachher", value=(after.content[:1000] or "…"), inline=False)
    emb.add_field(name="User / Channel", value=f"{after.author.mention} • {after.channel.mention} • [Jump]({after.jump_url})", inline=False)
    await send_log(bot,"message",emb,discord_id=after.author.id,channel_id=after.channel.id)

@bot.event
async def on_member_ban(guild, user):
    emb = make_embed("🔨 Ban", f"{user.mention} **{user}**\n`{user.id}`",0xe74c3c)
    await send_log(bot,"mod",emb,discord_id=user.id)

@bot.event
async def on_member_unban(guild, user):
    emb = make_embed("🔓 Unban", f"{user} `{user.id}`",0x2ecc71)
    await send_log(bot,"mod",emb,discord_id=user.id)

@bot.event
async def on_guild_channel_create(channel):
    if "ticket" in channel.name.lower():
        emb = make_embed("🎫 Ticket geöffnet", f"{channel.mention} erstellt",0x1abc9c)
        await send_log(bot,"ticket",emb,channel_id=channel.id)

@bot.event
async def on_guild_channel_delete(channel):
    if "ticket" in channel.name.lower():
        emb = make_embed("🎫 Ticket geschlossen", f"#{channel.name} gelöscht",0x95a5a6)
        await send_log(bot,"ticket",emb,channel_id=channel.id)

# ---------- COMMANDS ----------
@bot.command(name="help")
async def help_cmd(ctx):
    e = discord.Embed(title="🛍️ Void_Shop – Befehle", color=0xFF2020)
    e.add_field(name="🔐 Verify", value="`!verify Name` – Bio-Code Auth", inline=False)
    e.add_field(name="🛍️ Shop", value="`!checkbuy` – Auto-Delivery\n`!products`", inline=False)
    e.add_field(name="🪙 Coins", value="`!coins` `!shop` `!redeem <Coins>` `!daily` `!coinlb`", inline=False)
    e.add_field(name="📈", value="Käufe → automatisch #live-käufe", inline=False)
    e.add_field(name="👑 Owner", value="`!revenue` `!stafflb`", inline=False)
    e.set_footer(text="Void_Shop v1.0 ALL-IN-ONE • Web: http://localhost:5000")
    await ctx.send(embed=e)

#  🔐 VERIFY
@bot.command(name="verify")
async def verify_cmd(ctx, *, roblox_name: str = None):
    """!verify [RobloxName] – Bulletproof Bio-Code-Auth"""
    if not roblox_name:
        return await ctx.send("Usage: `!verify DeinRobloxName`")
    try: await ctx.message.delete()
    except: pass
    res = await roblox_username_to_id(roblox_name)
    if not res:
        return await ctx.send(f"❌ Roblox-User **{roblox_name}** nicht gefunden.", delete_after=15)
    roblox_id, display = res
    code = generate_bio_code()
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO verify_codes(discord_id,roblox_id,roblox_name,code,created_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
            (ctx.author.id, roblox_id, roblox_name, code))
        await db.commit()
    emb = discord.Embed(
        title="🔐 Roblox Verifizierung – Bio-Code-Auth",
        description=f"**Gefunden:** {display} (@{roblox_name})\nRoblox ID: `{roblox_id}`\n\n**Dein Sicherheitscode:**\n```\n{code}\n```\n\n**So geht's:**\n1️⃣ Kopiere den Code\n2️⃣ Profil: https://www.roblox.com/users/{roblox_id}/profile\n3️⃣ Bearbeiten → **Beschreibung** → Code einfügen → Speichern\n4️⃣ Unten **Bestätigen** klicken\n\n⏱️ 5 Minuten gültig.",
        color=0x9b59b6)
    emb.set_footer(text="Void_Shop • Bulletproof Verify")
    view = VerifyView(ctx.author.id, roblox_id, roblox_name, code)
    try:
        await ctx.author.send(embed=emb, view=view)
        await ctx.send(f"{ctx.author.mention} 📩 Check deine DMs!", delete_after=20)
    except discord.Forbidden:
        await ctx.send(embed=emb, view=view, delete_after=300)
    log_emb = make_embed("🔐 Verify gestartet",
        f"{ctx.author.mention} → **{roblox_name}** (`{roblox_id}`)\nCode: `{code}`",0x9b59b6,ctx.author)
    await send_log(bot,"verify",log_emb,discord_id=ctx.author.id)

#  🛍️ CHECKBUY – AUTO-DELIVERY
@bot.command(name="checkbuy")
async def checkbuy_cmd(ctx):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT roblox_id, roblox_name FROM users WHERE discord_id=? AND verified=1",
            (ctx.author.id,))
        row = await cur.fetchone()
    if not row:
        return await ctx.send(f"{ctx.author.mention} ❌ Nicht verifiziert! `!verify DeinName`", delete_after=20)
    roblox_id, roblox_name = row
    msg = await ctx.send(f"🔍 Prüfe Käufe für **{roblox_name}** (`{roblox_id}`) …")
    product_key, product = await find_owned_product(roblox_id)
    if not product:
        await msg.edit(content=f"❌ Kein neuer Gamepass-Kauf gefunden für **{roblox_name}**.\nKaufe zuerst im Roblox-Shop → dann `!checkbuy` erneut.")
        log_emb = make_embed("🛍️ checkbuy – nichts gefunden",
            f"{ctx.author.mention} • {roblox_name} (`{roblox_id}`)",0xe67e22,ctx.author)
        await send_log(bot,"shop",log_emb,discord_id=ctx.author.id)
        return
    purchase_id = await record_purchase(ctx.author.id, roblox_id, product_key, product)
    await msg.edit(content=f"✅ Kauf erkannt: **{product['name']}** – bereite Auto-Delivery vor …")
    # DM
    deliver = product.get("deliver",{})
    embed = discord.Embed(
        title=deliver.get("title", f"Danke – {product['name']}"),
        description=deliver.get("message","Hier ist dein Produkt!"),
        color=0x00ff88)
    embed.add_field(name="Produkt", value=product["name"], inline=True)
    embed.add_field(name="Preis", value=f"{product.get('robux_price','?')} Robux", inline=True)
    embed.add_field(name="Lieferung", value="< 5 Sekunden • Auto-Delivery", inline=False)
    files = deliver.get("files",[])
    if files:
        embed.add_field(name="Download Links", value="\n".join(f"• <{u}>" for u in files), inline=False)
    embed.set_footer(text="Void_Shop • Auto-Delivery • danke ❤️")
    dm_ok=True; dm_msg_id=""
    try:
        dm = await ctx.author.create_dm()
        dm_msg = await dm.send(embed=embed)
        dm_msg_id=str(dm_msg.id)
    except Exception:
        dm_ok=False
        await ctx.send(f"⚠️ Konnte keine DM senden! Öffne deine DMs.\n\n**Manuell:**\n"+"\n".join(files), delete_after=60)
    # role
    try:
        role_key = product.get("role_give","CUSTOMER")
        role_id = ROLE_VIP if role_key=="VIP" else ROLE_CUSTOMER
        if role_id:
            r = ctx.guild.get_role(role_id)
            if r: await ctx.author.add_roles(r, reason="Void_Shop Auto-Delivery")
    except: pass
    # coins
    coins_reward = product.get("coins_reward", COIN_REWARDS["purchase"])
    await add_coins(ctx.author.id, coins_reward, "purchase", product_key)
    await msg.edit(content=f"🎉 **{product['name']}** erfolgreich geliefert! Check deine DMs {ctx.author.mention}\n+{coins_reward} Void-Coins!")
    # ticker
    if TICKER_CHANNEL_ID:
        await send_purchase_ticker(bot, TICKER_CHANNEL_ID, ctx.author, product["name"], product.get("robux_price",0))
    # shop log
    log_emb = make_embed("✅ Auto-Delivery Erfolg",
        f"{ctx.author.mention} → **{product['name']}**\n{product.get('robux_price')} Robux • DM {'OK' if dm_ok else 'FAIL'}\nRoblox: {roblox_name} (`{roblox_id}`)",
        0x2ecc71, ctx.author)
    await send_log(bot,"shop",log_emb,discord_id=ctx.author.id)

@bot.command(name="products")
async def products_cmd(ctx):
    emb = discord.Embed(title="🛍️ Void_Shop Produkte", color=0xFFD700)
    for k,p in PRODUCTS.items():
        emb.add_field(name=f"{p['name']} – {p['robux_price']} R$",
                      value=f"Gamepass: `{p['gamepass_id']}`\n`!checkbuy` nach Kauf", inline=False)
    await ctx.send(embed=emb)

#  🪙 COINS
@bot.command(name="coins")
async def coins_cmd(ctx, member: discord.Member=None):
    target = member or ctx.author
    bal = await get_coins(target.id)
    emb = discord.Embed(title="🪙 Void-Coins", description=f"{target.mention} hat **{bal} Coins**", color=0xFFD700)
    await ctx.send(embed=emb)

@bot.command(name="shop")
async def coinshop_cmd(ctx):
    bal = await get_coins(ctx.author.id)
    emb = discord.Embed(title="🛍️ Coin-Shop", description=f"Dein Guthaben: **{bal} Coins**", color=0xFFD700)
    for price, reward in sorted(SHOP_REWARDS.items()):
        emb.add_field(name=f"{price} Coins → {reward['name']}", value=f"`!redeem {price}`", inline=False)
    emb.set_footer(text="Verdiene: verify +10, invite +25, kauf +50, vouch +30, daily +5")
    await ctx.send(embed=emb)

@bot.command(name="redeem")
async def redeem_cmd(ctx, amount:int=None):
    if not amount or amount not in SHOP_REWARDS:
        return await ctx.send("Verfügbar: "+", ".join(f"`!redeem {k}`" for k in SHOP_REWARDS))
    reward = SHOP_REWARDS[amount]
    ok = await spend_coins(ctx.author.id, amount, f"redeem_{reward['type']}")
    if not ok:
        bal = await get_coins(ctx.author.id)
        return await ctx.send(f"❌ Nicht genug Coins! Du hast {bal}, brauchst {amount}.")
    emb = discord.Embed(title="✅ Eingelöst!",
        description=f"**{reward['name']}**\n\nEin Staff meldet sich, oder du erhältst es per DM.",
        color=0x2ecc71)
    await ctx.send(embed=emb)
    log_emb = make_embed("🪙 Coin Redeem",
        f"{ctx.author.mention} hat **{reward['name']}** für {amount} Coins eingelöst.",0xFFD700,ctx.author)
    await send_log(bot,"coins",log_emb,discord_id=ctx.author.id)

@bot.command(name="coinlb", aliases=["coinslb"])
async def coinlb_cmd(ctx):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT discord_id, coins, purchases FROM users ORDER BY coins DESC LIMIT 10")
        rows = await cur.fetchall()
    desc = ""
    for i,(did,coins,pur) in enumerate(rows,1):
        desc += f"**#{i}** <@{did}> — **{coins}** 🪙 · {pur} Käufe\n"
    emb = discord.Embed(title="🏆 Void-Coin Leaderboard", description=desc or "Noch niemand.", color=0xFFD700)
    await ctx.send(embed=emb)

@bot.command(name="daily")
@commands.cooldown(1,86400,commands.BucketType.user)
async def daily_cmd(ctx):
    await add_coins(ctx.author.id, COIN_REWARDS["daily"], "daily")
    await ctx.send(f"✅ Daily abgeholt! +{COIN_REWARDS['daily']} Coins")

@daily_cmd.error
async def daily_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        h = int(error.retry_after//3600); m = int((error.retry_after%3600)//60)
        await ctx.send(f"⏳ Schon abgeholt! Nächster Daily in {h}h {m}m")

#  👑 OWNER
def is_owner():
    async def predicate(ctx): return ctx.author.id == OWNER_ID or OWNER_ID==0
    return commands.check(predicate)

@bot.command(name="revenue")
@is_owner()
async def revenue_cmd(ctx):
    data = await get_revenue_summary()
    emb = discord.Embed(title="👑 Revenue Dashboard – Owner Only", color=0x2c3e50)
    emb.add_field(name="Heute", value=f"{data['today_robux']} R$\n{data['today_purchases']} Käufe", inline=True)
    emb.add_field(name="Monat", value=f"{data['month_robux']} R$\n{data['month_purchases']} Käufe", inline=True)
    emb.add_field(name="Gesamt", value=f"{data['total_robux']} R$\n{data['total_purchases']} Käufe", inline=True)
    top_text = "\n".join([f"• {p} – {c}x – {r} R$" for p,c,r in data["top_products"]]) or "–"
    emb.add_field(name="Top Produkte", value=top_text, inline=False)
    await ctx.send(embed=emb, delete_after=120)
    try: await ctx.message.delete()
    except: pass

@bot.command(name="stafflb")
@is_owner()
async def stafflb_cmd(ctx):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cur = await db.execute("SELECT staff_id,tickets_claimed,tickets_closed,rating_count, CASE WHEN rating_count>0 THEN rating_sum*1.0/rating_count ELSE 0 END as avg FROM staff_stats ORDER BY tickets_closed DESC LIMIT 10")
        rows = await cur.fetchall()
    desc=""
    for i,(sid,claimed,closed,rc,avg) in enumerate(rows,1):
        desc+=f"**#{i}** <@{sid}> – {closed} closed / {claimed} claimed · ⭐ {avg:.1f} ({rc})\n"
    emb = discord.Embed(title="👑 Staff Leaderboard", description=desc or "Keine Daten", color=0x2c3e50)
    await ctx.send(embed=emb, delete_after=120)

@bot.command(name="ticker")
@commands.has_permissions(manage_guild=True)
async def ticker_test(ctx):
    if TICKER_CHANNEL_ID:
        await send_purchase_ticker(bot, TICKER_CHANNEL_ID, ctx.author, "Premium FastFlags Paket", 250)
        await ctx.send("✅ Test-Ticker gesendet", delete_after=5)

# =====================================================================
#  👑  WEB DASHBOARD – FLASK (eingebaut)
# =====================================================================
def run_dashboard():
    if not DASHBOARD_ENABLED: return
    try:
        from flask import Flask, render_template_string, request, redirect, session, jsonify
    except ImportError:
        print("[Dashboard] Flask nicht installiert – pip install Flask")
        return

    app = Flask(__name__)
    app.secret_key = DASHBOARD_SECRET

    # --- Templates inline (keine externen Dateien nötig) ---
    BASE_HTML = """
<!doctype html><html lang=de><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Void_Shop Dashboard</title>
<style>
:root{--bg:#0b0b0f;--card:#141421;--red:#FF2020;--gold:#FFD700;--muted:#889}
*{box-sizing:border-box;font-family:Inter,Segoe UI,Arial,sans-serif}
body{margin:0;background:var(--bg);color:#eee}
a{color:var(--gold);text-decoration:none}
.nav{display:flex;gap:18px;padding:14px 24px;background:#11111a;border-bottom:2px solid #1f1f2e;position:sticky;top:0}
.nav b{color:var(--red)}
.wrap{max-width:1300px;margin:24px auto;padding:0 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.card{background:var(--card);border:1px solid #222235;border-radius:16px;padding:18px}
.big{font-size:30px;font-weight:800}
.gold{color:var(--gold)}.red{color:var(--red)}.green{color:#2ecc71}.blue{color:#3498db}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:8px 10px;border-bottom:1px solid #252538;text-align:left}
th{color:var(--muted)}
.badge{background:#222;padding:2px 8px;border-radius:999px;font-size:12px}
.footer{opacity:.5;text-align:center;padding:30px;font-size:12px}
input,textarea{width:100%;padding:10px;background:#0f0f18;border:1px solid #2a2a40;color:#eee;border-radius:10px}
textarea{min-height:340px;font-family:monospace}
.btn{background:var(--red);color:#fff;border:none;padding:10px 16px;border-radius:10px;font-weight:700;cursor:pointer}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.two{grid-template-columns:1fr}}
</style></head><body>
<div class=nav><b>🛍️ VOID_SHOP</b>
<a href="/">Dashboard</a><a href="/products">Produkte</a><a href="/coins">Coins</a><a href="/logs">Logs</a>
<span style="flex:1"></span><a href="/logout">Logout</a></div>
<div class=wrap>
{{ content|safe }}
<div class=footer>Void_Shop v1.0 ALL-IN-ONE • RealVexo696 • Companion to VOID-TOOLS v2.6</div>
</div></body></html>
"""
    def page(content): return render_template_string(BASE_HTML, content=content)
    def q(sql, args=(), one=False):
        con = sqlite3.connect(DATABASE_PATH); con.row_factory=sqlite3.Row
        cur = con.execute(sql, args); rv = cur.fetchall(); con.close()
        return (rv[0] if rv else None) if one else rv

    @app.route("/login", methods=["GET","POST"])
    def login():
        if request.method=="POST":
            if request.form.get("code") in (DASHBOARD_LOGIN_CODE, str(OWNER_ID), "voidshop"):
                session["owner"]=True
                return redirect("/")
            err="<p style=color:#ff6b6b>Falscher Code</p>"
        else: err=""
        return f"""<!doctype html><meta charset=utf-8><title>Login</title>
<style>body{{margin:0;background:#0b0b0f;color:#eee;font-family:Segoe UI,Arial;display:grid;place-items:center;height:100vh}}
.box{{background:#141421;padding:36px;border-radius:20px;max-width:380px;width:90%}}
input{{width:100%;padding:13px;background:#0f0f18;border:1px solid #2a2a40;color:#eee;border-radius:12px;margin:10px 0;font-size:16px}}
button{{width:100%;padding:13px;background:#FF2020;color:#fff;border:none;border-radius:12px;font-weight:700;font-size:16px;cursor:pointer}}
</style>
<div class=box><h1 style="margin:0;color:#FF2020">👑 Void_Shop</h1><p style="color:#889">Owner Dashboard Login</p>
{err}
<form method=post><input type=password name=code placeholder="Owner Code" autofocus>
<button>Einloggen</button></form>
<small style="color:#666">Standard: <b>voidshop</b></small></div>"""

    @app.route("/logout")
    def logout(): session.clear(); return redirect("/login")

    def owner_required(f):
        from functools import wraps
        @wraps(f)
        def w(*a, **kw):
            if not session.get("owner"): return redirect("/login")
            return f(*a, **kw)
        return w

    @app.route("/")
    @owner_required
    def index():
        # revenue sync
        import asyncio
        data = asyncio.run(get_revenue_summary())
        users = q("SELECT COUNT(*) c FROM users", one=True); users = users["c"] if users else 0
        verified = q("SELECT COUNT(*) c FROM users WHERE verified=1", one=True); verified = verified["c"] if verified else 0
        coins_total = q("SELECT COALESCE(SUM(coins),0) s FROM users", one=True)["s"]
        recent = q("SELECT p.*, u.roblox_name FROM purchases p LEFT JOIN users u ON u.discord_id=p.discord_id ORDER BY p.created_at DESC LIMIT 12")
        coin_lb = q("SELECT discord_id, coins, purchases FROM users ORDER BY coins DESC LIMIT 10")
        scams = q("SELECT * FROM antiscam_hits ORDER BY created_at DESC LIMIT 8")
        conv = round((data["total_purchases"]/verified*100) if verified else 0,1)
        # render
        html = f"""
<h2>👑 Management Dashboard <span class=badge>LIVE</span></h2>
<div class=grid>
 <div class=card><div style="color:#889;font-size:12px;text-transform:uppercase">Heute Umsatz</div><div class="big gold">{data['today_robux']} <span style="font-size:16px">R$</span></div>{data['today_purchases']} Käufe</div>
 <div class=card><div style="color:#889;font-size:12px;text-transform:uppercase">Monat Umsatz</div><div class="big red">{data['month_robux']} R$</div>{data['month_purchases']} Käufe</div>
 <div class=card><div style="color:#889;font-size:12px;text-transform:uppercase">Gesamt</div><div class=big>{data['total_robux']} R$</div>{data['total_purchases']} Käufe gesamt</div>
 <div class=card><div style="color:#889;font-size:12px;text-transform:uppercase">User</div><div class="big blue">{users}</div>{verified} verifiziert</div>
 <div class=card><div style="color:#889;font-size:12px;text-transform:uppercase">Coins im Umlauf</div><div class="big gold">🪙 {coins_total}</div>Economy aktiv</div>
 <div class=card><div style="color:#889;font-size:12px;text-transform:uppercase">Conversion</div><div class="big green">{conv}%</div>verified → kauf</div>
</div>
<div class=two style="margin-top:16px">
 <div class=card><h3>📈 Top Produkte</h3><table><tr><th>Produkt</th><th>Verkäufe</th><th>Umsatz</th></tr>"""
        for p,c,r in data["top_products"]:
            html += f"<tr><td>{p}</td><td>{c}</td><td class=gold>{r} R$</td></tr>"
        html += "</table></div><div class=card><h3>🪙 Coin Leaderboard</h3><table><tr><th>#</th><th>User</th><th>Coins</th></tr>"
        for i,row in enumerate(coin_lb,1):
            html += f"<tr><td>{i}</td><td>&lt;@{row['discord_id']}&gt;</td><td class=gold>{row['coins']}</td></tr>"
        html += "</table></div></div>"
        html += "<div class=card style='margin-top:16px'><h3>🛍️ Letzte Käufe – Live Ticker</h3><table><tr><th>Zeit</th><th>Käufer</th><th>Produkt</th><th>R$</th></tr>"
        for r in recent:
            rn = f" <small>({r['roblox_name']})</small>" if r["roblox_name"] else ""
            html += f"<tr><td>{r['created_at']}</td><td>&lt;@{r['discord_id']}&gt;{rn}</td><td>{r['product_key']}</td><td class=gold>{r['robux_price']}</td></tr>"
        html += "</table></div>"
        html += "<div class=card style='margin-top:16px'><h3>🚨 Letzte AntiScam Hits</h3><table><tr><th>Zeit</th><th>User</th><th>URL</th><th>Grund</th></tr>"
        for s in scams:
            html += f"<tr><td>{s['created_at']}</td><td>&lt;@{s['discord_id']}&gt;</td><td style='max-width:300px;overflow:hidden;text-overflow:ellipsis'>{s['url']}</td><td>{s['reason']}</td></tr>"
        if not scams: html += "<tr><td colspan=4 style=color:#666>Keine Scam-Versuche – Schild hält! 🛡️</td></tr>"
        html += "</table></div>"
        html += "<div class=card style='margin-top:16px'><h3>🛒 Produkte – Auto-Delivery aktiv</h3><table><tr><th>Key</th><th>Name</th><th>Gamepass</th><th>Preis</th></tr>"
        import json as _json
        for k,p in PRODUCTS.items():
            html += f"<tr><td><code>{k}</code></td><td>{p['name']}</td><td>{p['gamepass_id']}</td><td class=gold>{p['robux_price']} R$</td></tr>"
        html += "</table><p><a href='/products' class=btn>Produkte bearbeiten →</a></p></div>"
        return page(html)

    @app.route("/products", methods=["GET","POST"])
    @owner_required
    def products_page():
        import json
        if request.method=="POST":
            return "<p style=color:#ff6b6b>Read-only in All-In-One – editiere PRODUCTS dict oben in der .py Datei Zeile ~90</p><p><a href=/products>Zurück</a></p>", 400
        pretty = json.dumps(PRODUCTS, indent=2, ensure_ascii=False)
        html = f"""<h2>🛍️ Produkt-Manager – Auto-Delivery</h2>
<div class=card><p>Produkte sind in dieser ALL-IN-ONE Version direkt im Code (Zeile ~90 <code>PRODUCTS = {{...}}</code>).<br>
Dashboard-Editor ist read-only – editiere die .py Datei direkt.</p>
<textarea readonly>{pretty}</textarea>
<br><br><a href="/" class=btn>← Dashboard</a></div>"""
        return page(html)

    @app.route("/coins")
    @owner_required
    def coins_page():
        rows = q("SELECT discord_id, coins, purchases, total_spent_robux, roblox_name FROM users ORDER BY coins DESC LIMIT 100")
        ledger = q("SELECT * FROM coins_ledger ORDER BY created_at DESC LIMIT 150")
        html = "<h2>🪙 Void-Coins Economy</h2><div class=two>"
        html += "<div class=card><h3>Leaderboard</h3><table><tr><th>User</th><th>Coins</th><th>Käufe</th><th>R$</th></tr>"
        for r in rows:
            html += f"<tr><td>&lt;@{r['discord_id']}&gt; {r['roblox_name'] or ''}</td><td class=gold>{r['coins']}</td><td>{r['purchases']}</td><td>{r['total_spent_robux']}</td></tr>"
        html += "</table></div><div class=card><h3>Ledger</h3><table><tr><th>Zeit</th><th>User</th><th>±</th><th>Grund</th></tr>"
        for l in ledger:
            col = "green" if l["amount"]>0 else "red"
            html += f"<tr><td>{l['created_at']}</td><td>&lt;@{l['discord_id']}&gt;</td><td class={col}>{l['amount']:+d}</td><td>{l['reason']}</td></tr>"
        html += "</table></div></div>"
        return page(html)

    @app.route("/logs")
    @owner_required
    def logs_page():
        t = request.args.get("type","")
        if t:
            rows = q("SELECT * FROM logs WHERE log_type=? ORDER BY created_at DESC LIMIT 300", (t,))
        else:
            rows = q("SELECT * FROM logs ORDER BY created_at DESC LIMIT 300")
        types = [r["log_type"] for r in q("SELECT DISTINCT log_type FROM logs")]
        filt = " ".join([f"<a class=badge href=/logs?type={x}>{x}</a>" for x in types]) + " <a class=badge href=/logs>alle</a>"
        html = f"<h2>📜 LogSystem 2.0 – 12 Kanäle</h2><div class=card style='margin-bottom:12px'>{filt}</div>"
        html += "<div class=card><table><tr><th>Zeit</th><th>Typ</th><th>User</th><th>Channel</th><th>Content</th></tr>"
        for r in rows:
            uid = f"&lt;@{r['discord_id']}&gt;" if r["discord_id"] else ""
            ch = f"#{r['channel_id']}" if r["channel_id"] else ""
            cont = (r["content"] or "")[:150]
            html += f"<tr><td>{r['created_at']}</td><td><span class=badge>{r['log_type']}</span></td><td>{uid}</td><td>{ch}</td><td>{cont}</td></tr>"
        html += "</table></div>"
        return page(html)

    @app.route("/api/revenue")
    @owner_required
    def api_revenue():
        import asyncio
        return jsonify(asyncio.run(get_revenue_summary()))

    print(f"[*] Void_Shop Dashboard → http://{DASHBOARD_HOST}:{DASHBOARD_PORT}  – Login: {DASHBOARD_LOGIN_CODE}")
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False, use_reloader=False)

# =====================================================================
#  🚀  START
# =====================================================================
async def main():
    await init_db()
    if TOKEN == "PUT_YOUR_BOT_TOKEN_HERE" or not TOKEN:
        print("\n[!] DISCORD_TOKEN fehlt!\n  → Öffne void_shop_all_in_one.py\n  → Bearbeite CONFIG ganz oben: TOKEN, GUILD_ID, OWNER_ID\n  → Trage deine 12 LOG_CHANNEL IDs ein\n")
        return
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    # Dashboard in Thread
    if DASHBOARD_ENABLED:
        t = threading.Thread(target=run_dashboard, daemon=True)
        t.start()
        time.sleep(0.8)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[+] Shutdown.")
    finally:
        try:
            # close aiohttp
            if _session and not _session.closed:
                asyncio.run(_session.close())
        except: pass
