#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛍️ VOID_SHOP v2.0 ULTIMATE – ALL-IN-ONE
RealVexo696 / Void_Shop
Companion to VOID-TOOLS v2.6 by V0id-v2

v2.0 – 27.06.2026 ULTIMATE
- !start → erstellt automatisch ~30 Kanäle + erweitertes LogSystem + Shop-Struktur
- Ticket-System: 🛒 Produkt kaufen / 💬 Allgemeiner Support / 🤝 Partnerschaft
- Ticket-Close Survey: 3 Fragen
  Q1: Haben Sie etwas gekauft? Ja/Nein
  Q2: Was? → FastFlags / Sky / T-Shirt Template / Anti Alt Ban (Buttons)
  Q3: Sterne-Bewertung 1-5 (klickbare Buttons, kein Tippen)
- Welcome / Leave schöner Text in #🎉・willkommen / #👋・auf-wiedersehen
- Discord-Zugang per 1-Klick + sichere Roblox Bio-Code-Auth für Shop-Käufe
- Stats: Mitglieder / Booster / Kunden / offene Tickets (Live Voice-Channels)
- Standard-Kanäle: regeln, willkommen, auf-wiedersehen, verify, fastflags, how-to-buy, …
- LOGSYSTEM 2.0 Kommandozentrale – viele spezialisierte Log-Kanäle
- Web Dashboard: Revenue, Staff-Leaderboard, Coins, Logs
- Auto-Delivery, Bio-Code-Auth, AntiScam, Void-Coins

Python 3.11+ · discord.py 2.3+
pip install discord.py aiohttp aiosqlite Flask python-dotenv
python void_shop_v2_ultimate_full.py
AGPL-3.0
"""
# =====================================================================
#  🔧 BOOTSTRAP – AUTO INSTALL – CRASH LOOP FIX
# =====================================================================
import sys, subprocess, os
def _pip(n):
    try:
        print(f"[BOOT] pip install {n} ...", flush=True)
        subprocess.check_call([sys.executable,"-m","pip","install","--quiet","--no-input", n],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        return True
    except Exception as e:
        print(f"[BOOT] {n} failed: {e}", flush=True); return False

for imp,pip in [("discord","discord.py>=2.3.2"),("aiohttp","aiohttp>=3.9.0"),("flask","Flask>=3.0.0"),("dotenv","python-dotenv>=1.0.0")]:
    try: __import__(imp)
    except ModuleNotFoundError: _pip(pip)

try:
    import aiosqlite
    HAS_AIOSQLITE=True
except ModuleNotFoundError:
    HAS_AIOSQLITE=False
    print("[BOOT] aiosqlite missing – using sqlite3 fallback", flush=True)

try:
    import discord
    from discord.ext import commands, tasks
except Exception as e:
    print(f"[FATAL] discord.py missing: {e}"); sys.exit(1)

try:
    import aiohttp
except Exception as e:
    print(f"[FATAL] aiohttp missing: {e}"); sys.exit(1)

import asyncio, sqlite3, json, random, re, datetime, time, threading
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[BOOT] .env loaded")
except: pass

try:
    from flask import Flask, render_template_string, request, redirect, session, jsonify
    HAS_FLASK=True
except Exception:
    HAS_FLASK=False
    print("[BOOT] Flask not available – Dashboard disabled")

print(f"[BOOT] discord.py {discord.__version__} | aiosqlite={HAS_AIOSQLITE} | flask={HAS_FLASK}")

# =====================================================================
#  🛠️  CONFIG
# =====================================================================
TOKEN = os.getenv("DISCORD_TOKEN","PUT_YOUR_BOT_TOKEN_HERE")
GUILD_ID = int(os.getenv("GUILD_ID","0") or 0)
OWNER_ID = int(os.getenv("OWNER_ID","0") or 0)
PREFIX = os.getenv("PREFIX","!")

# Log IDs – werden von !start überschrieben, ENV ist Fallback
LOG_JOIN     = int(os.getenv("LOG_JOIN","0") or 0)
LOG_LEAVE    = int(os.getenv("LOG_LEAVE","0") or 0)
LOG_VOICE    = int(os.getenv("LOG_VOICE","0") or 0)
LOG_MESSAGE  = int(os.getenv("LOG_MESSAGE","0") or 0)
LOG_INVITE   = int(os.getenv("LOG_INVITE","0") or 0)
LOG_SHOP     = int(os.getenv("LOG_SHOP","0") or 0)
LOG_VERIFY   = int(os.getenv("LOG_VERIFY","0") or 0)
LOG_ANTISCAM = int(os.getenv("LOG_ANTISCAM","0") or 0)
LOG_TICKET   = int(os.getenv("LOG_TICKET","0") or 0)
LOG_COINS    = int(os.getenv("LOG_COINS","0") or 0)
LOG_MOD      = int(os.getenv("LOG_MOD","0") or 0)
LOG_SYSTEM   = int(os.getenv("LOG_SYSTEM","0") or 0)
LOG_TICKER   = int(os.getenv("LOG_TICKER","0") or 0)
LOG_BOT      = int(os.getenv("LOG_BOT","0") or 0)
LOG_OWNER    = int(os.getenv("LOG_OWNER","0") or 0)

# Runtime config – wird von !start gespeichert
RUNTIME = {
    "log_join": LOG_JOIN, "log_leave": LOG_LEAVE, "log_voice": LOG_VOICE,
    "log_message": LOG_MESSAGE, "log_invite": LOG_INVITE, "log_shop": LOG_SHOP,
    "log_verify": LOG_VERIFY, "log_antiscam": LOG_ANTISCAM, "log_ticket": LOG_TICKET,
    "log_coins": LOG_COINS, "log_mod": LOG_MOD, "log_system": LOG_SYSTEM,
    "log_ticker": LOG_TICKER, "log_bot": LOG_BOT, "log_owner": LOG_OWNER,
    # channels
    "welcome": int(os.getenv("WELCOME_CHANNEL_ID","0") or 0),
    "goodbye": 0, "rules":0, "announcements":0,
    "verify":0, "how_to_buy":0, "fastflags":0, "products":0,
    "vouches":0, "media":0, "general":0, "bot_commands":0,
    "ticket_create":0,
    # stats
    "stat_members":0, "stat_boosters":0, "stat_customers":0, "stat_tickets":0,
    # roles
    "role_unverified": int(os.getenv("UNVERIFIED_ROLE_ID","0") or 0),
    "role_verified": int(os.getenv("VERIFIED_ROLE_ID","0") or 0),
    "role_member": 0,
    "role_customer": int(os.getenv("CUSTOMER_ROLE_ID","0") or 0),
    "role_vip": int(os.getenv("VIP_ROLE_ID","0") or 0),
    "role_booster":0,
    "role_staff": int(os.getenv("STAFF_ROLE_ID","0") or 0),
    "role_head_staff":0, "role_moderator":0, "role_trial_supporter":0,
    "role_admin":0, "role_owner":0,
}
SERVER_CONFIG_FILE = "void_server_config.json"
def load_runtime():
    global RUNTIME
    if os.path.isfile(SERVER_CONFIG_FILE):
        try:
            with open(SERVER_CONFIG_FILE,"r",encoding="utf-8") as f:
                d=json.load(f); RUNTIME.update(d)
            print(f"[CONFIG] loaded {SERVER_CONFIG_FILE}")
        except Exception as e: print(f"[CONFIG] {e}")
def save_runtime():
    try:
        with open(SERVER_CONFIG_FILE,"w",encoding="utf-8") as f:
            json.dump(RUNTIME,f,indent=2)
    except Exception as e: print(f"[CONFIG save] {e}")
load_runtime()

def L(key:str)->int: return RUNTIME.get(f"log_{key}", RUNTIME.get(key,0)) or 0
def C(key:str)->int: return RUNTIME.get(key,0) or 0
def ROL(key:str)->int: return RUNTIME.get(f"role_{key}",0) or 0

def ticker_ch(): return L("ticker") or C("ticker_create") or 0

ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE","")
DASHBOARD_ENABLED = HAS_FLASK and os.getenv("DASHBOARD_DISABLE","0")!="1"
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST","0.0.0.0")
DASHBOARD_PORT = int(os.getenv("PORT", os.getenv("DASHBOARD_PORT","5000")))
DASHBOARD_SECRET = os.getenv("DASHBOARD_SECRET","voidshop-secret-change-me")
DASHBOARD_LOGIN_CODE = os.getenv("DASHBOARD_LOGIN") or (str(OWNER_ID) if OWNER_ID else "voidshop")
DATABASE_PATH = os.getenv("DATABASE_PATH","void_shop.db")

# =====================================================================
#  🛍️  PRODUKTE – inkl. Sky + Anti Alt Ban
# =====================================================================
PRODUCTS = {
    "fastflags_premium": {
        "name": "Premium FastFlags Paket", "gamepass_id": 12345678, "robux_price": 250,
        "deliver": {
            "title": "🎉 Danke für deinen Kauf – Premium FastFlags",
            "message": "Hier ist dein **Premium FastFlags Paket** – sofortige Lieferung!\n\n📎 Download:\n• FastFlags JSON\n• Anleitung PDF\n• T-Shirt Vorlage\n\nSupport: https://discord.gg/voidv2",
            "files": ["https://cdn.void-shop.local/fastflags/premium.json","https://cdn.void-shop.local/fastflags/README.pdf"]
        },
        "coins_reward": 50, "role_give": "customer", "survey_key": "fastflags"
    },
    "sky": {
        "name": "Sky", "gamepass_id": 12345682, "robux_price": 180,
        "deliver": {
            "title": "☁️ Sky – Danke!",
            "message": "Dein **Sky** Paket!\n\n• Sky-Shader\n• Install Guide\n• Support inklusive",
            "files": ["https://cdn.void-shop.local/sky/sky.zip"]
        },
        "coins_reward": 50, "role_give": "customer", "survey_key": "sky"
    },
    "tshirt_template": {
        "name": "T-Shirt Template", "gamepass_id": 12345679, "robux_price": 120,
        "deliver": {
            "title": "👕 T-Shirt Template Pro",
            "message": "Dein **T-Shirt Template Pro**!\n\n• 12x PSD Vorlagen\n• 30x PNG Overlays\n• Roblox Upload Guide",
            "files": ["https://cdn.void-shop.local/tshirt/pro_pack.zip"]
        },
        "coins_reward": 50, "role_give": "customer", "survey_key": "tshirt_template"
    },
    "anti_alt_ban": {
        "name": "Anti Alt Ban", "gamepass_id": 12345683, "robux_price": 399,
        "deliver": {
            "title": "🛡️ Anti Alt Ban",
            "message": "Anti Alt Ban aktiviert!\n\n• Bypass Files\n• Setup Video\n• 24/7 Support",
            "files": ["https://cdn.void-shop.local/anti_alt_ban/pack.zip"]
        },
        "coins_reward": 50, "role_give": "vip", "survey_key": "anti_alt_ban"
    },
    "fastflags_ultra": {
        "name": "FastFlags Ultra", "gamepass_id": 12345680, "robux_price": 499,
        "deliver": {
            "title": "⚡ FastFlags Ultra",
            "message": "Ultra Paket freigeschaltet!\n• Ultra FastFlags\n• FPS Booster\n• VIP Discord",
            "files": ["https://cdn.void-shop.local/fastflags/ultra.zip"]
        },
        "coins_reward": 50, "role_give": "vip", "survey_key": "fastflags"
    },
    "starter_bundle": {
        "name": "Starter Bundle", "gamepass_id": 12345681, "robux_price": 75,
        "deliver": {
            "title": "📦 Starter Bundle",
            "message": "Danke für deinen ersten Kauf!\nDownload: https://cdn.void-shop.local/starter/bundle.zip"
        },
        "coins_reward": 50, "role_give": "customer", "survey_key": "fastflags"
    },
}

# Survey Optionen – exakt gefordert
SURVEY_PRODUCTS = [
    ("fastflags", "⚡ FastFlags", "FastFlags / Ultra / Premium"),
    ("sky", "☁️ Sky", "Sky Shader"),
    ("tshirt_template", "👕 T-Shirt Template", "T-Shirt Template Pro"),
    ("anti_alt_ban", "🛡️ Anti Alt Ban", "Anti Alt Ban Protection"),
]

COIN_REWARDS = {"verify":10,"invite":25,"purchase":50,"vouch_5star":30,"daily":5}
SHOP_REWARDS = {
    150: {"name":"15% Rabatt-Code","type":"discount"},
    300: {"name":"Gratis T-Shirt Template","type":"product"},
    500: {"name":"VIP Role 30 Tage","type":"role"},
    800: {"name":"Premium FastFlags Paket","type":"product"},
}

SAFE_DOMAINS = [
    "roblox.com","www.roblox.com","web.roblox.com",
    "discord.com","discord.gg","discordapp.com","cdn.discordapp.com",
    "youtube.com","youtu.be","www.youtube.com",
    "github.com","t.me","voidtool","voidv2",
    "twitter.com","x.com","twitch.tv","tiktok.com",
    "paypal.com","stripe.com",
]
SUSPICIOUS_KEYWORDS = [
    "roblóx","rob1ox","r0blox","roblox-free","free-robux",
    "dlscord","discorde","disord","discord-nitro",
    "steamcommunity-n","steancommunity","free-nitro","nitro-free"
]

# =====================================================================
#  🗄️  DATABASE
# =====================================================================
DB_SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(discord_id INTEGER PRIMARY KEY, roblox_id INTEGER, roblox_name TEXT, verified INTEGER DEFAULT 0, coins INTEGER DEFAULT 0, total_spent_robux INTEGER DEFAULT 0, purchases INTEGER DEFAULT 0, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, verified_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS verify_codes(discord_id INTEGER PRIMARY KEY, roblox_id INTEGER, roblox_name TEXT, code TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS purchases(id INTEGER PRIMARY KEY AUTOINCREMENT, discord_id INTEGER, roblox_id INTEGER, product_key TEXT, gamepass_id INTEGER, robux_price INTEGER, delivered INTEGER DEFAULT 0, delivery_at TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS deliveries(id INTEGER PRIMARY KEY AUTOINCREMENT, purchase_id INTEGER, discord_id INTEGER, product_key TEXT, delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, dm_message_id TEXT, success INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS coins_ledger(id INTEGER PRIMARY KEY AUTOINCREMENT, discord_id INTEGER, amount INTEGER, reason TEXT, meta TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS invites(inviter_id INTEGER, invited_id INTEGER PRIMARY KEY, invite_code TEXT, joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, rewarded INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS staff_stats(staff_id INTEGER PRIMARY KEY, tickets_claimed INTEGER DEFAULT 0, tickets_closed INTEGER DEFAULT 0, avg_response_sec INTEGER DEFAULT 0, rating_sum INTEGER DEFAULT 0, rating_count INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS antiscam_hits(id INTEGER PRIMARY KEY AUTOINCREMENT, discord_id INTEGER, channel_id INTEGER, url TEXT, reason TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT, log_type TEXT, discord_id INTEGER, channel_id INTEGER, content TEXT, meta TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS vouches(id INTEGER PRIMARY KEY AUTOINCREMENT, discord_id INTEGER, stars INTEGER, message TEXT, coins_awarded INTEGER DEFAULT 0, product TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS revenue_daily(day TEXT PRIMARY KEY, robux INTEGER DEFAULT 0, purchases INTEGER DEFAULT 0, customers INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS tickets_open(channel_id INTEGER PRIMARY KEY, user_id INTEGER, type TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, closed INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS ticket_metrics(channel_id INTEGER PRIMARY KEY, claimed_by INTEGER, claimed_at TIMESTAMP, first_staff_response_at TIMESTAMP, closer_id INTEGER, closed_at TIMESTAMP, survey_product TEXT, survey_stars INTEGER);
CREATE TABLE IF NOT EXISTS server_config(k TEXT PRIMARY KEY, v TEXT);
"""

if HAS_AIOSQLITE:
    async def db_connect(): return await aiosqlite.connect(DATABASE_PATH)
    async def db_execute(db, sql, params=()):
        cur = await db.execute(sql, params); return cur
    async def db_commit(db): await db.commit()
    async def db_close(db): await db.close()
    class get_db:
        async def __aenter__(self): self.db = await db_connect(); return self.db
        async def __aexit__(self, *a):
            try: await db_close(self.db)
            except: pass
else:
    import concurrent.futures
    _db_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="void_sql")
    class _SyncCursor:
        def __init__(self, cur): self._cur=cur
        async def fetchone(self): return await asyncio.get_event_loop().run_in_executor(_db_executor, self._cur.fetchone)
        async def fetchall(self): return await asyncio.get_event_loop().run_in_executor(_db_executor, self._cur.fetchall)
    class _AsyncDB:
        def __init__(self, conn): self._c=conn
        async def execute(self, sql, params=()):
            def _do(): return self._c.execute(sql, params)
            cur = await asyncio.get_event_loop().run_in_executor(_db_executor, _do)
            return _SyncCursor(cur)
        async def executescript(self, script):
            await asyncio.get_event_loop().run_in_executor(_db_executor, lambda: self._c.executescript(script))
        async def commit(self):
            await asyncio.get_event_loop().run_in_executor(_db_executor, self._c.commit)
        async def close(self):
            await asyncio.get_event_loop().run_in_executor(_db_executor, self._c.close)
    async def db_connect():
        def _open():
            c = sqlite3.connect(DATABASE_PATH, check_same_thread=False, timeout=30.0)
            c.row_factory = sqlite3.Row
            return c
        conn = await asyncio.get_event_loop().run_in_executor(_db_executor, _open)
        return _AsyncDB(conn)
    async def db_execute(db, sql, params=()): return await db.execute(sql, params)
    async def db_commit(db): await db.commit()
    async def db_close(db): await db.close()
    class get_db:
        async def __aenter__(self): self.db = await db_connect(); return self.db
        async def __aexit__(self, *a):
            try: await db_close(self.db)
            except: pass

async def init_db():
    async with get_db() as db:
        await db.executescript(DB_SCHEMA)
        try:
            await db_execute(db, "ALTER TABLE invites ADD COLUMN invite_code TEXT")
        except Exception:
            pass
        await db_commit(db)
    print(f"[DB] ready → {DATABASE_PATH} (aiosqlite={HAS_AIOSQLITE})")

# =====================================================================
#  🌐 ROBLOX / SERVICES
# =====================================================================
_session: aiohttp.ClientSession | None = None
async def get_session():
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
    return _session

async def roblox_username_to_id(username:str):
    s = await get_session()
    try:
        async with s.post("https://users.roblox.com/v1/usernames/users",
            json={"usernames":[username],"excludeBannedUsers":True}) as r:
            j = await r.json(); d = j.get("data",[])
            if d: u=d[0]; return u["id"], u.get("displayName",u["name"])
    except: pass
    return None

async def roblox_get_description(user_id:int)->str:
    s = await get_session()
    try:
        async with s.get(f"https://users.roblox.com/v1/users/{user_id}") as r:
            if r.status==200: j=await r.json(); return j.get("description","") or ""
    except: pass
    return ""

async def roblox_owns_gamepass(roblox_id:int, gamepass_id:int)->bool:
    s = await get_session()
    try:
        url = f"https://inventory.roblox.com/v1/users/{roblox_id}/items/GamePass/{gamepass_id}"
        headers = {}
        if ROBLOX_COOKIE: headers["Cookie"] = f".ROBLOSECURITY={ROBLOX_COOKIE}"
        async with s.get(url, headers=headers) as r:
            if r.status==200:
                j = await r.json(); return len(j.get("data",[])) > 0
    except: pass
    return False

def generate_bio_code(): return f"void-{random.randint(1000,9999)}"
async def check_bio_code(roblox_id:int, code:str)->bool:
    return code.lower() in (await roblox_get_description(roblox_id)).lower()

async def find_owned_product(roblox_id:int):
    for key,p in PRODUCTS.items():
        gp = p.get("gamepass_id")
        if gp and await roblox_owns_gamepass(roblox_id, gp):
            async with get_db() as db:
                cur = await db_execute(db,
                    "SELECT id FROM purchases WHERE roblox_id=? AND product_key=? AND delivered=1",
                    (roblox_id, key))
                if await cur.fetchone(): continue
            return key,p
    return None,None

async def record_purchase(discord_id:int, roblox_id:int, product_key:str, product:dict):
    async with get_db() as db:
        await db_execute(db,
            "INSERT INTO purchases(discord_id,roblox_id,product_key,gamepass_id,robux_price,delivered,delivery_at) VALUES(?,?,?,?,?,1,CURRENT_TIMESTAMP)",
            (discord_id,roblox_id,product_key,product.get("gamepass_id"),product.get("robux_price",0)))
        await db_execute(db,
            "UPDATE users SET purchases=purchases+1, total_spent_robux=total_spent_robux+? WHERE discord_id=?",
            (product.get("robux_price",0), discord_id))
        today = datetime.date.today().isoformat()
        await db_execute(db,
            "INSERT INTO revenue_daily(day,robux,purchases,customers) VALUES(?,?,1,1) ON CONFLICT(day) DO UPDATE SET robux=robux+excluded.robux, purchases=purchases+1",
            (today, product.get("robux_price",0)))
        await db_commit(db)

async def add_coins(discord_id:int, amount:int, reason:str, meta:str=""):
    if amount==0: return
    async with get_db() as db:
        await db_execute(db, "INSERT OR IGNORE INTO users(discord_id,coins) VALUES(?,0)", (discord_id,))
        await db_execute(db, "UPDATE users SET coins=coins+? WHERE discord_id=?", (amount, discord_id))
        await db_execute(db, "INSERT INTO coins_ledger(discord_id,amount,reason,meta) VALUES(?,?,?,?)",
            (discord_id, amount, reason, meta))
        await db_commit(db)

async def get_coins(discord_id:int)->int:
    async with get_db() as db:
        cur = await db_execute(db, "SELECT coins FROM users WHERE discord_id=?", (discord_id,))
        row = await cur.fetchone()
        if not row: return 0
        try: return row[0]
        except: return row["coins"]

async def spend_coins(discord_id:int, amount:int, reason:str)->bool:
    bal = await get_coins(discord_id)
    if bal < amount: return False
    await add_coins(discord_id, -amount, reason)
    return True

# --- Antiscam ---
URL_RE = re.compile(r'https?://[^\s<]+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/[^\s<]*)?', re.I)
def extract_urls(t:str): return URL_RE.findall(t or "")
def normalize_domain(url:str)->str:
    if not url.startswith("http"): url="http://"+url
    try:
        p = urlparse(url)
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
        if target.replace(".","") in host.replace(".","") and host!=target and not host.endswith("."+target): return False
    return True
def scan_message_antiscam(content:str)->list:
    bad=[]
    for url in extract_urls(content):
        host=normalize_domain(url)
        if not host: continue
        low=(url+" "+host).lower()
        if any(s in low for s in SUSPICIOUS_KEYWORDS):
            bad.append({"url":url,"host":host,"reason":"typosquatting / scam keyword"}); continue
        if not is_safe_domain(host):
            bad.append({"url":url,"host":host,"reason":"domain not whitelisted"})
    return bad

# =====================================================================
#  📜 LOGGER
# =====================================================================
LOG_COLORS = {
    "join":0x2ecc71, "leave":0x95a5a6, "voice":0x3498db, "message":0xe67e22,
    "invite":0x5865F2, "shop":0xf1c40f, "verify":0x9b59b6, "antiscam":0xe74c3c,
    "ticket":0x1abc9c, "coins":0xFFD700, "mod":0xe74c3c, "system":0x7289DA,
    "ticker":0xFFD700, "bot":0x95a5a6, "owner":0x2c3e50,
}
async def send_log(bot_obj, log_type:str, embed:discord.Embed=None, content:str=None,
                   discord_id:int=None, channel_id:int=None, meta:str=""):
    chan_id = L(log_type)
    if chan_id:
        ch = bot_obj.get_channel(chan_id)
        if ch is None:
            try: ch = await bot_obj.fetch_channel(chan_id)
            except: ch=None
        if ch:
            try:
                if embed:
                    if not embed.timestamp: embed.timestamp = datetime.datetime.utcnow()
                    if not embed.color: embed.color = LOG_COLORS.get(log_type,0x7d7d7d)
                await ch.send(content=content, embed=embed)
            except Exception as e:
                print(f"[LOG {log_type}] {e}")
    try:
        async with get_db() as db:
            await db_execute(db,
                "INSERT INTO logs(log_type,discord_id,channel_id,content,meta) VALUES(?,?,?,?,?)",
                (log_type, discord_id, channel_id, content or (embed.title if embed else ""), meta))
            await db_commit(db)
    except Exception as e:
        print(f"[LOG DB] {e}")

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
#  📈 TICKER / REVENUE
# =====================================================================
async def send_purchase_ticker(bot_obj, channel_id:int, buyer:discord.Member, product_name:str, robux:int):
    if not channel_id: return
    ch = bot_obj.get_channel(channel_id)
    if ch is None:
        try: ch = await bot_obj.fetch_channel(channel_id)
        except: return
    embed = discord.Embed(title="🎉 Neuer Kauf!",
        description=f"**{buyer.mention}** hat soeben **{product_name}** erworben!\nVielen Dank! ❤️",
        color=0xFFD700, timestamp=datetime.datetime.utcnow())
    try: embed.set_thumbnail(url=buyer.display_avatar.url)
    except: pass
    embed.add_field(name="Produkt", value=product_name, inline=True)
    embed.add_field(name="Preis", value=f"{robux} Robux", inline=True)
    embed.set_footer(text="Void_Shop • Live Käufe • FOMO")
    try: await ch.send(embed=embed)
    except Exception as e: print(f"[TICKER] {e}")

async def get_revenue_summary():
    async with get_db() as db:
        cur = await db_execute(db, "SELECT COALESCE(SUM(robux_price),0), COUNT(*) FROM purchases WHERE delivered=1")
        r = await cur.fetchone(); total_robux = r[0] if r else 0; total_purchases = r[1] if r else 0
        cur = await db_execute(db, "SELECT COALESCE(SUM(robux_price),0), COUNT(*) FROM purchases WHERE delivered=1 AND created_at >= date('now','start of month')")
        r = await cur.fetchone(); month_robux = r[0] if r else 0; month_purchases = r[1] if r else 0
        cur = await db_execute(db, "SELECT COALESCE(SUM(robux_price),0), COUNT(*) FROM purchases WHERE delivered=1 AND date(created_at)=date('now')")
        r = await cur.fetchone(); today_robux = r[0] if r else 0; today_purchases = r[1] if r else 0
        cur = await db_execute(db, "SELECT product_key, COUNT(*), SUM(robux_price) FROM purchases WHERE delivered=1 GROUP BY product_key ORDER BY SUM(robux_price) DESC LIMIT 5")
        top = await cur.fetchall()
        cur = await db_execute(db, "SELECT day, robux, purchases FROM revenue_daily ORDER BY day DESC LIMIT 30")
        daily = await cur.fetchall()
    return {
        "total_robux": total_robux or 0, "total_purchases": total_purchases or 0,
        "month_robux": month_robux or 0, "month_purchases": month_purchases or 0,
        "today_robux": today_robux or 0, "today_purchases": today_purchases or 0,
        "top_products": top, "daily": list(reversed(daily))
    }

# Ticket DB helpers
async def ticket_open(channel_id:int, user_id:int, ttype:str):
    async with get_db() as db:
        await db_execute(db, "INSERT OR REPLACE INTO tickets_open(channel_id,user_id,type,created_at,closed) VALUES(?,?,?,CURRENT_TIMESTAMP,0)",
            (channel_id, user_id, ttype))
        await db_commit(db)

async def ticket_close_db(channel_id:int):
    async with get_db() as db:
        await db_execute(db, "UPDATE tickets_open SET closed=1 WHERE channel_id=?", (channel_id,))
        await db_commit(db)

async def count_open_tickets()->int:
    async with get_db() as db:
        cur = await db_execute(db, "SELECT COUNT(*) FROM tickets_open WHERE closed=0")
        r = await cur.fetchone()
        return r[0] if r else 0

def parse_db_ts(value):
    if not value:
        return None
    if isinstance(value, datetime.datetime):
        return value
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(str(value), fmt)
        except Exception:
            continue
    return None

def product_label(product_key:str)->str:
    return PRODUCTS.get(product_key, {}).get("name", str(product_key).replace("_", " ").title())

def staff_role_ids()->set[int]:
    return {rid for rid in {
        ROL("owner"), ROL("admin"), ROL("head_staff"), ROL("moderator"),
        ROL("staff"), ROL("trial_supporter")
    } if rid}

def is_staff_member(member:discord.Member)->bool:
    if getattr(member.guild_permissions, "administrator", False) or getattr(member.guild_permissions, "manage_guild", False):
        return True
    ids = staff_role_ids()
    return any(getattr(role, "id", 0) in ids for role in getattr(member, "roles", []))

async def get_ticket_row(channel_id:int):
    async with get_db() as db:
        cur = await db_execute(db, "SELECT channel_id, user_id, type, created_at, closed FROM tickets_open WHERE channel_id=?", (channel_id,))
        return await cur.fetchone()

async def get_ticket_metrics(channel_id:int):
    async with get_db() as db:
        cur = await db_execute(db, "SELECT * FROM ticket_metrics WHERE channel_id=?", (channel_id,))
        return await cur.fetchone()

async def ensure_ticket_metrics(channel_id:int):
    async with get_db() as db:
        await db_execute(db, "INSERT OR IGNORE INTO ticket_metrics(channel_id) VALUES(?)", (channel_id,))
        await db_commit(db)

async def claim_ticket(channel_id:int, staff_id:int):
    async with get_db() as db:
        cur = await db_execute(db, "SELECT closed FROM tickets_open WHERE channel_id=?", (channel_id,))
        row = await cur.fetchone()
        if not row:
            return False, "not_found"
        try:
            closed = row[0]
        except Exception:
            closed = row["closed"]
        if closed:
            return False, "closed"
        await db_execute(db, "INSERT OR IGNORE INTO ticket_metrics(channel_id) VALUES(?)", (channel_id,))
        cur = await db_execute(db, "SELECT claimed_by FROM ticket_metrics WHERE channel_id=?", (channel_id,))
        mrow = await cur.fetchone()
        claimed_by = None
        if mrow:
            try:
                claimed_by = mrow[0]
            except Exception:
                claimed_by = mrow["claimed_by"]
        if claimed_by:
            return False, claimed_by
        await db_execute(db, "UPDATE ticket_metrics SET claimed_by=?, claimed_at=CURRENT_TIMESTAMP WHERE channel_id=?", (staff_id, channel_id))
        await db_execute(db, "INSERT OR IGNORE INTO staff_stats(staff_id) VALUES(?)", (staff_id,))
        await db_execute(db, "UPDATE staff_stats SET tickets_claimed=tickets_claimed+1 WHERE staff_id=?", (staff_id,))
        await db_commit(db)
    return True, staff_id

async def note_ticket_staff_response(channel_id:int, staff_id:int):
    async with get_db() as db:
        cur = await db_execute(db, "SELECT user_id, created_at, closed FROM tickets_open WHERE channel_id=?", (channel_id,))
        row = await cur.fetchone()
        if not row:
            return
        try:
            created_at = row[1]; closed = row[2]
        except Exception:
            created_at = row["created_at"]; closed = row["closed"]
        if closed:
            return
        await db_execute(db, "INSERT OR IGNORE INTO ticket_metrics(channel_id) VALUES(?)", (channel_id,))
        cur = await db_execute(db, "SELECT claimed_by, first_staff_response_at FROM ticket_metrics WHERE channel_id=?", (channel_id,))
        mrow = await cur.fetchone()
        claimed_by = None
        first_response = None
        if mrow:
            try:
                claimed_by, first_response = mrow[0], mrow[1]
            except Exception:
                claimed_by, first_response = mrow["claimed_by"], mrow["first_staff_response_at"]
        if not claimed_by:
            await db_execute(db, "UPDATE ticket_metrics SET claimed_by=?, claimed_at=CURRENT_TIMESTAMP WHERE channel_id=?", (staff_id, channel_id))
            await db_execute(db, "INSERT OR IGNORE INTO staff_stats(staff_id) VALUES(?)", (staff_id,))
            await db_execute(db, "UPDATE staff_stats SET tickets_claimed=tickets_claimed+1 WHERE staff_id=?", (staff_id,))
            claimed_by = staff_id
        if not first_response:
            await db_execute(db, "UPDATE ticket_metrics SET first_staff_response_at=CURRENT_TIMESTAMP WHERE channel_id=?", (channel_id,))
            created_dt = parse_db_ts(created_at)
            response_sec = max(0, int((datetime.datetime.utcnow() - created_dt).total_seconds())) if created_dt else 0
            await db_execute(db, "INSERT OR IGNORE INTO staff_stats(staff_id) VALUES(?)", (claimed_by,))
            cur = await db_execute(db, "SELECT tickets_claimed, avg_response_sec FROM staff_stats WHERE staff_id=?", (claimed_by,))
            srow = await cur.fetchone()
            if srow:
                try:
                    tickets_claimed, avg_response_sec = srow[0], srow[1]
                except Exception:
                    tickets_claimed, avg_response_sec = srow["tickets_claimed"], srow["avg_response_sec"]
                tickets_claimed = max(1, int(tickets_claimed or 1))
                avg_response_sec = int(avg_response_sec or 0)
                new_avg = response_sec if tickets_claimed <= 1 or avg_response_sec <= 0 else int(((avg_response_sec * (tickets_claimed - 1)) + response_sec) / tickets_claimed)
                await db_execute(db, "UPDATE staff_stats SET avg_response_sec=? WHERE staff_id=?", (new_avg, claimed_by))
        await db_commit(db)

async def finalize_ticket_metrics(channel_id:int, closer_id:int, stars:int=None, product:str=None):
    async with get_db() as db:
        await db_execute(db, "INSERT OR IGNORE INTO ticket_metrics(channel_id) VALUES(?)", (channel_id,))
        cur = await db_execute(db, "SELECT claimed_by FROM ticket_metrics WHERE channel_id=?", (channel_id,))
        row = await cur.fetchone()
        claimed_by = None
        if row:
            try:
                claimed_by = row[0]
            except Exception:
                claimed_by = row["claimed_by"]
        await db_execute(db, "UPDATE ticket_metrics SET closer_id=?, closed_at=CURRENT_TIMESTAMP, survey_product=?, survey_stars=? WHERE channel_id=?",
            (closer_id, product, stars, channel_id))
        target_staff = claimed_by or closer_id
        if target_staff:
            await db_execute(db, "INSERT OR IGNORE INTO staff_stats(staff_id) VALUES(?)", (target_staff,))
            await db_execute(db, "UPDATE staff_stats SET tickets_closed=tickets_closed+1, rating_sum=rating_sum+?, rating_count=rating_count+? WHERE staff_id=?",
                (stars or 0, 1 if stars else 0, target_staff))
        await db_commit(db)

async def refresh_invite_cache(guild:discord.Guild):
    try:
        invites = await guild.invites()
    except Exception:
        return
    INVITE_CACHE[guild.id] = {
        inv.code: {
            "uses": inv.uses or 0,
            "inviter_id": inv.inviter.id if inv.inviter else 0,
            "url": getattr(inv, "url", "")
        } for inv in invites
    }

async def detect_used_invite(guild:discord.Guild):
    try:
        invites = await guild.invites()
    except Exception:
        return None
    before = INVITE_CACHE.get(guild.id, {})
    used = None
    for inv in invites:
        prev = before.get(inv.code, {}).get("uses", 0)
        if (inv.uses or 0) > prev:
            used = inv
            break
    INVITE_CACHE[guild.id] = {
        inv.code: {
            "uses": inv.uses or 0,
            "inviter_id": inv.inviter.id if inv.inviter else 0,
            "url": getattr(inv, "url", "")
        } for inv in invites
    }
    return used

async def reward_invite_if_needed(inviter_id:int, invited_id:int, invite_code:str=""):
    if not inviter_id or inviter_id == invited_id:
        return False
    async with get_db() as db:
        cur = await db_execute(db, "SELECT rewarded FROM invites WHERE invited_id=?", (invited_id,))
        row = await cur.fetchone()
        if row:
            try:
                rewarded = row[0]
            except Exception:
                rewarded = row["rewarded"]
            if rewarded:
                return False
        await db_execute(db, "INSERT OR REPLACE INTO invites(inviter_id, invited_id, invite_code, joined_at, rewarded) VALUES(?,?,?,CURRENT_TIMESTAMP,1)",
            (inviter_id, invited_id, invite_code))
        await db_commit(db)
    await add_coins(inviter_id, COIN_REWARDS["invite"], "invite_reward", f"invited:{invited_id}")
    return True

INVITE_CACHE = {}

# =====================================================================
#  🤖 BOT
# =====================================================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None, case_insensitive=True)

# ---------------- TICKET SYSTEM ----------------
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction:discord.Interaction, ttype:str, label:str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        cat = discord.utils.get(guild.categories, name="🎫 TICKETS")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, manage_messages=True, read_message_history=True)
        }
        for role in guild.roles:
            if role.id in staff_role_ids():
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
        cname = f"ticket-{interaction.user.name.lower()}"[:90].replace(" ", "-")
        try:
            ch = await guild.create_text_channel(
                cname,
                category=cat,
                overwrites=overwrites,
                reason=f"Void_Shop Ticket {ttype} by {interaction.user}",
                topic=f"User:{interaction.user.id}|Type:{ttype}"
            )
        except Exception as e:
            return await interaction.followup.send(f"❌ Konnte Ticket nicht erstellen: {e}", ephemeral=True)
        await ticket_open(ch.id, interaction.user.id, ttype)
        emb = discord.Embed(
            title=f"🎫 Ticket – {label}",
            description=(
                f"Hallo {interaction.user.mention}!\n\n"
                f"**Typ:** {label}\n"
                "Ein Supporter meldet sich in Kürze.\n\n"
                "• Supporter können das Ticket mit **🙋 Claimen** übernehmen\n"
                "• Danach wird die Antwortzeit für dein Dashboard getrackt\n"
                "• Beim Schließen erscheint automatisch die 3-Fragen-Umfrage"
            ),
            color=0x1abc9c
        )
        emb.set_footer(text="Void_Shop Ticket System • Claim + Survey + Staff Tracking")
        await ch.send(f"{interaction.user.mention}", embed=emb, view=TicketControlView())
        await interaction.followup.send(f"✅ Ticket erstellt: {ch.mention}", ephemeral=True)
        log_emb = make_embed("🎫 Ticket geöffnet", f"{interaction.user.mention} → {ch.mention}\nTyp: **{label}**", 0x1abc9c, interaction.user)
        await send_log(bot, "ticket", log_emb, discord_id=interaction.user.id, channel_id=ch.id, meta=f"type={ttype}")

    @discord.ui.button(label="🛒 Produkt kaufen", style=discord.ButtonStyle.green, custom_id="ticket_buy_v2u")
    async def btn_buy(self, interaction:discord.Interaction, button:discord.ui.Button):
        await self.create_ticket(interaction, "buy", "Produkt kaufen")

    @discord.ui.button(label="💬 Allgemeiner Support", style=discord.ButtonStyle.blurple, custom_id="ticket_support_v2u")
    async def btn_support(self, interaction:discord.Interaction, button:discord.ui.Button):
        await self.create_ticket(interaction, "support", "Allgemeiner Support")

    @discord.ui.button(label="🤝 Partnerschaft", style=discord.ButtonStyle.gray, custom_id="ticket_partner_v2u")
    async def btn_partner(self, interaction:discord.Interaction, button:discord.ui.Button):
        await self.create_ticket(interaction, "partner", "Partnerschaft")

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🙋 Ticket claimen", style=discord.ButtonStyle.green, custom_id="ticket_claim_v3")
    async def claim_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        if not is_staff_member(interaction.user):
            return await interaction.response.send_message("❌ Nur Staff/Admin kann Tickets claimen.", ephemeral=True)
        ok, info = await claim_ticket(interaction.channel.id, interaction.user.id)
        if ok:
            await interaction.response.send_message(f"✅ {interaction.user.mention} hat dieses Ticket übernommen.")
            log_emb = make_embed(
                "🙋 Ticket geclaimed",
                f"Supporter: {interaction.user.mention}\nKanal: {interaction.channel.mention}",
                0x2ecc71,
                interaction.user
            )
            await send_log(bot, "ticket", log_emb, discord_id=interaction.user.id, channel_id=interaction.channel.id, meta="claimed=yes")
        else:
            if info == "closed":
                txt = "❌ Dieses Ticket ist bereits geschlossen."
            elif info == "not_found":
                txt = "❌ Dieses Ticket ist nicht in der Datenbank registriert."
            else:
                txt = f"ℹ️ Dieses Ticket wurde bereits von <@{info}> übernommen."
            await interaction.response.send_message(txt, ephemeral=True)

    @discord.ui.button(label="🔒 Ticket schließen", style=discord.ButtonStyle.red, custom_id="ticket_close_v3")
    async def close_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        row = await get_ticket_row(interaction.channel.id)
        if not row:
            return await interaction.response.send_message("❌ Ticketdaten nicht gefunden.", ephemeral=True)
        try:
            ticket_owner_id = row[1]
        except Exception:
            ticket_owner_id = row["user_id"]
        if interaction.user.id != ticket_owner_id and not is_staff_member(interaction.user):
            return await interaction.response.send_message("❌ Nur der Ticket-Ersteller oder Staff kann schließen.", ephemeral=True)
        await interaction.response.send_message(
            "**Ticket schließen – kurze Umfrage (3 Fragen)**\n\n**Frage 1/3:**\nHaben Sie etwas gekauft?",
            view=SurveyQ1View(interaction.channel, ticket_owner_id, interaction.user.id),
            ephemeral=False
        )

class SurveyQ1View(discord.ui.View):
    def __init__(self, ticket_channel, ticket_owner_id:int, close_requested_by_id:int):
        super().__init__(timeout=180)
        self.ticket_channel = ticket_channel
        self.ticket_owner_id = ticket_owner_id
        self.close_requested_by_id = close_requested_by_id

    async def guard(self, interaction:discord.Interaction):
        if interaction.user.id != self.ticket_owner_id:
            await interaction.response.send_message("❌ Nur der Ticket-Ersteller kann diese Umfrage beantworten.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Ja", style=discord.ButtonStyle.green)
    async def yes_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        if not await self.guard(interaction):
            return
        await interaction.response.edit_message(
            content="**Frage 2/3:**\nWas haben Sie gekauft?\nBitte wählen:",
            view=SurveyQ2View(self.ticket_channel, self.ticket_owner_id, self.close_requested_by_id)
        )

    @discord.ui.button(label="❌ Nein", style=discord.ButtonStyle.red)
    async def no_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        if not await self.guard(interaction):
            return
        await interaction.response.edit_message(content="Danke fürs Feedback! Ticket wird geschlossen …", view=None)
        await close_ticket_final(
            self.ticket_channel,
            interaction.user,
            closed_by_id=self.close_requested_by_id,
            purchased=False
        )

class SurveyQ2View(discord.ui.View):
    def __init__(self, ticket_channel, ticket_owner_id:int, close_requested_by_id:int):
        super().__init__(timeout=180)
        self.ticket_channel = ticket_channel
        self.ticket_owner_id = ticket_owner_id
        self.close_requested_by_id = close_requested_by_id
        for key, label, desc in SURVEY_PRODUCTS:
            self.add_item(SurveyProductButton(key, label, self.ticket_channel, self.ticket_owner_id, self.close_requested_by_id))

class SurveyProductButton(discord.ui.Button):
    def __init__(self, product_key, label, ticket_channel, ticket_owner_id:int, close_requested_by_id:int):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.product_key = product_key
        self.ticket_channel = ticket_channel
        self.ticket_owner_id = ticket_owner_id
        self.close_requested_by_id = close_requested_by_id

    async def callback(self, interaction:discord.Interaction):
        if interaction.user.id != self.ticket_owner_id:
            return await interaction.response.send_message("❌ Nur der Ticket-Ersteller kann diese Umfrage beantworten.", ephemeral=True)
        await interaction.response.edit_message(
            content=(
                f"**Frage 3/3:**\nWie bewerten Sie Ihren Einkauf / Support?\n\n"
                f"Ausgewählt: **{self.label}**\n\nBitte Sterne anklicken:"
            ),
            view=SurveyQ3View(self.ticket_channel, self.product_key, self.ticket_owner_id, self.close_requested_by_id)
        )

class SurveyQ3View(discord.ui.View):
    def __init__(self, ticket_channel, product_key:str, ticket_owner_id:int, close_requested_by_id:int):
        super().__init__(timeout=180)
        self.ticket_channel = ticket_channel
        self.product_key = product_key
        self.ticket_owner_id = ticket_owner_id
        self.close_requested_by_id = close_requested_by_id
        labels = ["⭐","⭐⭐","⭐⭐⭐","⭐⭐⭐⭐","⭐⭐⭐⭐⭐"]
        for i in range(5):
            self.add_item(StarButton(i+1, labels[i], ticket_channel, product_key, ticket_owner_id, close_requested_by_id))

class StarButton(discord.ui.Button):
    def __init__(self, stars:int, label:str, ticket_channel, product_key:str, ticket_owner_id:int, close_requested_by_id:int):
        super().__init__(label=label, style=discord.ButtonStyle.green if stars >= 4 else discord.ButtonStyle.secondary if stars == 3 else discord.ButtonStyle.red)
        self.stars = stars
        self.ticket_channel = ticket_channel
        self.product_key = product_key
        self.ticket_owner_id = ticket_owner_id
        self.close_requested_by_id = close_requested_by_id

    async def callback(self, interaction:discord.Interaction):
        if interaction.user.id != self.ticket_owner_id:
            return await interaction.response.send_message("❌ Nur der Ticket-Ersteller kann diese Umfrage beantworten.", ephemeral=True)
        user = interaction.user
        try:
            async with get_db() as db:
                await db_execute(
                    db,
                    "INSERT INTO vouches(discord_id,stars,message,coins_awarded,product) VALUES(?,?,?,?,?)",
                    (user.id, self.stars, f"Ticket Survey – {self.product_key}", 0, self.product_key)
                )
                await db_commit(db)
            if self.stars == 5:
                await add_coins(user.id, COIN_REWARDS["vouch_5star"], "vouch_5star", self.product_key)
                coin_txt = f"\n\n+{COIN_REWARDS['vouch_5star']} Void-Coins als Dankeschön!"
            else:
                coin_txt = ""
        except Exception as e:
            print(f"[survey] {e}")
            coin_txt = ""
        await interaction.response.edit_message(
            content=(
                f"Vielen Dank für Ihre **{self.stars} ⭐ Bewertung** zu **{product_label(self.product_key)}**!"
                f"{coin_txt}\n\nTicket wird in 5 Sekunden geschlossen …"
            ),
            view=None
        )
        try:
            log_emb = make_embed(
                "⭐ Ticket Bewertung",
                f"{user.mention}\nProdukt: **{product_label(self.product_key)}**\nBewertung: **{'⭐' * self.stars} ({self.stars}/5)**\nKanal: {self.ticket_channel.mention}",
                0xFFD700,
                user
            )
            await send_log(
                bot,
                "ticket",
                log_emb,
                discord_id=user.id,
                channel_id=self.ticket_channel.id,
                meta=f"stars={self.stars};product={self.product_key}"
            )
        except Exception:
            pass
        await asyncio.sleep(5)
        await close_ticket_final(
            self.ticket_channel,
            user,
            closed_by_id=self.close_requested_by_id,
            purchased=True,
            product=self.product_key,
            stars=self.stars
        )

async def close_ticket_final(channel:discord.TextChannel, feedback_user:discord.Member, closed_by_id:int=None, purchased:bool=False, product:str=None, stars:int=None):
    try:
        row = await get_ticket_row(channel.id)
        owner_id = None
        if row:
            try:
                owner_id = row[1]
            except Exception:
                owner_id = row["user_id"]
        real_closer = channel.guild.get_member(closed_by_id) if closed_by_id else feedback_user
        if real_closer is None:
            real_closer = feedback_user
        await finalize_ticket_metrics(channel.id, real_closer.id, stars=stars, product=product)
        await ticket_close_db(channel.id)
        txt = f"Ticket {channel.mention} geschlossen von {real_closer.mention}\n"
        txt += f"Feedback von: {feedback_user.mention}\n"
        if purchased:
            txt += f"Gekauft: {product_label(product or 'ja')}\n"
            if stars:
                txt += f"Bewertung: {stars}⭐\n"
        else:
            txt += "Kein Kauf"
        emb = make_embed("🎫 Ticket geschlossen", txt, 0x95a5a6, real_closer)
        await send_log(bot, "ticket", emb, discord_id=real_closer.id, channel_id=channel.id, meta=f"purchased={purchased};product={product};stars={stars}")
        if purchased and owner_id and L("ticker"):
            buyer = channel.guild.get_member(owner_id)
            if buyer:
                ch = bot.get_channel(L("ticker"))
                if ch:
                    tick = discord.Embed(
                        title="🎉 Kauf-Ticket erfolgreich abgeschlossen!",
                        description=f"**{buyer.mention}** hat soeben **{product_label(product or 'Produkt')}** abgeschlossen. Vielen Dank! ❤️",
                        color=0xFFD700,
                        timestamp=datetime.datetime.utcnow()
                    )
                    try:
                        tick.set_thumbnail(url=buyer.display_avatar.url)
                    except Exception:
                        pass
                    tick.set_footer(text="Void_Shop • Live Käufe • FOMO")
                    try:
                        await ch.send(embed=tick)
                    except Exception as e:
                        print(f"[ticket ticker] {e}")
        try:
            await update_stats_channels(channel.guild)
        except Exception:
            pass
        await asyncio.sleep(3)
        await channel.delete(reason=f"Ticket closed by {real_closer} – survey completed")
    except Exception as e:
        print(f"[close_ticket] {e}")
        try:
            await channel.send(f"⚠️ Fehler beim Schließen: {e}")
        except Exception:
            pass

# ---------- VERIFY ----------
class OneClickVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="✅ Discord-Zugang freischalten", style=discord.ButtonStyle.green, custom_id="oneclick_verify_v2u", emoji="🔓")
    async def verify_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        guild = interaction.guild; user = interaction.user
        member_role_id = ROL("member") or ROL("verified")
        unverified_id = ROL("unverified")
        try:
            if member_role_id:
                mr = guild.get_role(member_role_id)
                if mr: await user.add_roles(mr, reason="Discord Access Verify")
            if unverified_id:
                ur = guild.get_role(unverified_id)
                if ur and ur in user.roles:
                    await user.remove_roles(ur, reason="Discord access granted")
            await add_coins(user.id, COIN_REWARDS["verify"], "verify_oneclick")
            await interaction.response.send_message(
                f"✅ Server-Zugang freigeschaltet, {user.mention}!\n+{COIN_REWARDS['verify']} Coins gutgeschrieben.\n\n🔐 **Für Roblox-Käufe und 100 % Identitätsprüfung nutze zusätzlich:** `!verify DeinRobloxName`",
                ephemeral=True
            )
            log_emb = make_embed("🔓 Discord-Zugang freigeschaltet", f"{user.mention} hat den Serverzugang per 1-Klick freigeschaltet.\nHinweis: Roblox-Shop-Verify bleibt `!verify Name`.", 0x2ecc71, user)
            await send_log(bot, "verify", log_emb, discord_id=user.id)
            # welcome embed in welcome channel
            wc_id = C("welcome")
            if wc_id:
                ch = guild.get_channel(wc_id)
                if ch:
                    w = discord.Embed(
                        title=f"Willkommen {user.display_name}!",
                        description=f"🎉 **Herzlich Willkommen bei Void Shop**, {user.mention}!\n\nSchön dass du da bist ❤️\n\n🛍️ Schau in <#{(C('products') or C('general') or ch.id)}> vorbei\n💬 Support: Ticket-System\n🪙 Sammle Void-Coins!\n🔐 Für Shop-Käufe: `!verify DeinRobloxName`\n\n**Viel Spaß!**",
                        color=0x2ecc71, timestamp=datetime.datetime.utcnow()
                    )
                    try:
                        w.set_thumbnail(url=user.display_avatar.url)
                        w.set_footer(text=f"Mitglied #{guild.member_count} • Void_Shop", icon_url=guild.icon.url if guild.icon else None)
                    except: pass
                    try: await ch.send(content=user.mention, embed=w)
                    except: pass
        except Exception as e:
            if interaction.response.is_done():
                await interaction.followup.send(f"⚠️ Fehler: {e}", ephemeral=True)
            else:
                await interaction.response.send_message(f"⚠️ Fehler: {e}", ephemeral=True)

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
        async with get_db() as db:
            await db_execute(db,
                "INSERT INTO users(discord_id,roblox_id,roblox_name,verified,verified_at,coins) VALUES(?,?,?,?,CURRENT_TIMESTAMP,COALESCE((SELECT coins FROM users WHERE discord_id=?),0)) ON CONFLICT(discord_id) DO UPDATE SET roblox_id=excluded.roblox_id, roblox_name=excluded.roblox_name, verified=1, verified_at=CURRENT_TIMESTAMP",
                (self.discord_id, self.roblox_id, self.roblox_name, self.discord_id))
            await db_execute(db, "DELETE FROM verify_codes WHERE discord_id=?", (self.discord_id,))
            await db_commit(db)
        try:
            guild = interaction.guild
            if guild:
                ur_id = ROL("unverified")
                if ur_id:
                    ur = guild.get_role(ur_id)
                    if ur:
                        try: await interaction.user.remove_roles(ur, reason="Roblox verified")
                        except: pass
                for rk in ["verified","member","customer"]:
                    rid = ROL(rk)
                    if rid:
                        r = guild.get_role(rid)
                        if r:
                            try: await interaction.user.add_roles(r, reason="Roblox Bio Verify")
                            except: pass
        except: pass
        await add_coins(self.discord_id, COIN_REWARDS["verify"], "verify_bio")
        emb = discord.Embed(title="✅ Verifiziert!",
            description=f"Willkommen **{self.roblox_name}**!\nRoblox ID: `{self.roblox_id}`\n\n+{COIN_REWARDS['verify']} Void-Coins gutgeschrieben!",
            color=0x2ecc71)
        await interaction.followup.send(embed=emb, ephemeral=True)
        log_emb = make_embed("🔐 Bio-Verify Erfolg", f"{interaction.user.mention} → **{self.roblox_name}** (`{self.roblox_id}`)\nCode: `{self.code}`", 0x2ecc71, interaction.user)
        await send_log(bot, "verify", log_emb, discord_id=self.discord_id)
        self.stop()
    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.red)
    async def cancel(self, interaction:discord.Interaction, button:discord.ui.Button):
        if interaction.user.id != self.discord_id:
            return await interaction.response.send_message("Nicht dein Verify!", ephemeral=True)
        await interaction.response.send_message("Abgebrochen.", ephemeral=True)
        self.stop()

# =====================================================================
#  🚀  !start – SERVER SETUP
# =====================================================================
ROLE_DEFS = [
    # Administration
    ("👑 Owner", (255, 0, 0), True, True),
    ("⚡ Admin", (255, 70, 70), True, True),
    ("🔧 Head-Staff", (255, 120, 0), True, False),
    ("🛡️ Moderator", (0, 170, 255), True, False),
    ("🎫 Supporter", (0, 220, 120), True, False),
    ("🧰 Trial-Supporter", (120, 220, 120), False, False),
    # Shop / Kunden
    ("💎 VIP Kunde", (255, 215, 0), False, False),
    ("🛒 Kunde", (0, 255, 136), False, False),
    ("⭐ Premium", (255, 105, 180), False, False),
    ("🎁 Booster", (255, 115, 250), False, False),
    # Verifizierung
    ("✅ Verifiziert", (46, 204, 113), False, False),
    ("👤 Member", (88, 180, 255), False, False),
    ("❌ Unverifiziert", (120, 120, 120), False, False),
    # Produkte
    ("⚡ FastFlags", (255, 200, 0), False, False),
    ("☁️ Sky", (135, 206, 250), False, False),
    ("👕 T-Shirt", (255, 150, 200), False, False),
    ("🛡️ Anti Alt Ban", (180, 0, 255), False, False),
    # Level / Aktivität
    ("🔥 Aktiv", (255, 69, 0), False, False),
    ("💬 Chatter", (0, 200, 255), False, False),
    ("🌟 Stammkunde", (255, 215, 0), False, False),
    ("🏆 Top Käufer", (255, 215, 0), False, False),
    ("🎖️ Veteran", (192, 192, 192), False, False),
    # Spezial
    ("🤝 Partner", (100, 255, 180), False, False),
    ("🎨 Designer", (255, 105, 180), False, False),
    ("🧪 Beta Tester", (0, 255, 200), False, False),
    ("📢 Event Ping", (255, 220, 0), False, False),
    ("🎉 Giveaway Ping", (255, 180, 0), False, False),
    ("🛍️ Shop Ping", (0, 255, 150), False, False),
    ("📣 News Ping", (0, 150, 255), False, False),
    # Farben
    ("❤️ Rot", (231, 76, 60), False, False),
    ("💙 Blau", (52, 152, 219), False, False),
    ("💚 Grün", (46, 204, 113), False, False),
    ("💛 Gelb", (241, 196, 15), False, False),
    ("💜 Lila", (155, 89, 182), False, False),
    ("🩷 Pink", (253, 121, 168), False, False),
    ("🧡 Orange", (230, 126, 34), False, False),
    ("🤍 Weiß", (236, 240, 241), False, False),
    ("🖤 Schwarz", (44, 62, 80), False, False),
    # Bot
    ("🤖 Bot", (88, 101, 242), True, False),
]

CHANNELS_SETUP = [
    ("📢 INFO", [
        ("📜・regeln", "text", "📜 Server Regeln – bitte lesen!"),
        ("📢・ankündigungen", "text", "📢 Offizielle Ankündigungen"),
        ("🎉・willkommen", "text", "Herzlich Willkommen bei Void Shop!"),
        ("👋・auf-wiedersehen", "text", "Auf Wiedersehen Nachrichten"),
        ("✅・verify", "text", "Ein-Klick Verifizierung"),
        ("🛒・how-to-buy", "text", "So kaufst du bei uns"),
        ("❓・faq", "text", "Häufige Fragen"),
        ("🔗・links", "text", "Wichtige Links"),
    ]),
    ("🛍️ SHOP", [
        ("🛒・produkte", "text", "Unsere Produkte Übersicht"),
        ("⚡・fastflags", "text", "FastFlags Info & Downloads"),
        ("☁️・sky", "text", "Sky Produkt"),
        ("👕・tshirt-template", "text", "T-Shirt Templates"),
        ("🛡️・anti-alt-ban", "text", "Anti Alt Ban Info"),
        ("💰・preise", "text", "Preisliste"),
        ("🎁・angebote", "text", "Aktuelle Angebote"),
    ]),
    ("💬 COMMUNITY", [
        ("💬・allgemein", "text", "Allgemeiner Chat"),
        ("🤖・bot-commands", "text", "Bot Befehle hier: !help !verify !checkbuy"),
        ("📸・media", "text", "Teile deine Screenshots / Designs"),
        ("🎮・roblox", "text", "Roblox Talk"),
        ("💡・vorschläge", "text", "Vorschläge für den Shop"),
        ("🐛・bug-reports", "text", "Fehler melden"),
        ("🌍・international", "text", "English / International Chat"),
    ]),
    ("⭐ BEWERTUNGEN", [
        ("⭐・vouches", "text", "Kundenbewertungen – 5⭐ hier posten = +30 Coins!"),
        ("🏆・top-kunden", "text", "Top Kunden des Monats"),
    ]),
    ("🎫 TICKETS", [
        ("🎫・ticket-erstellen", "text", "Erstelle hier dein Ticket – 3 Optionen: Produkt kaufen / Support / Partnerschaft"),
    ]),
    ("🎙️ VOICE", [
        ("💬・Lobby", "voice", ""),
        ("🎮・Gaming", "voice", ""),
        ("🎵・Musik", "voice", ""),
        ("🔒・Support Warteraum", "voice", ""),
        ("👑・Staff Only", "voice", ""),
    ]),
]

LOG_CHANNEL_DEFS = [
    ("📥・join-logs","join"),
    ("📤・leave-logs","leave"),
    ("🎙️・voice-logs","voice"),
    ("💬・message-logs","message"),
    ("🔗・invite-logs","invite"),
    ("🛍️・shop-logs","shop"),
    ("🔐・verify-logs","verify"),
    ("🚨・antiscam-logs","antiscam"),
    ("🎫・ticket-logs","ticket"),
    ("🪙・coin-logs","coins"),
    ("⚙️・mod-logs","mod"),
    ("🏗️・system-logs","system"),
    ("📈・live-käufe","ticker"),
    ("🔧・bot-logs","bot"),
    ("👑・owner-logs","owner"),
]

def reset_runtime_state():
    for key in list(RUNTIME.keys()):
        if key.startswith("log_") or key.startswith("role_") or key.startswith("stat_") or key in {
            "welcome", "goodbye", "rules", "announcements", "verify", "how_to_buy", "fastflags",
            "products", "vouches", "media", "general", "bot_commands", "ticket_create", "ticker"
        }:
            RUNTIME[key] = 0

async def wipe_managed_server(guild:discord.Guild, status_message=None):
    deleted = {"roles":0, "channels":0, "categories":0}
    managed_category_names = {name for name, _ in CHANNELS_SETUP} | {"📊 LOGS", "📊 STATS"}
    managed_channel_names = {name for _, channels in CHANNELS_SETUP for name, _, _ in channels}
    managed_channel_names.update({name for name, _ in LOG_CHANNEL_DEFS})
    managed_role_names = {name for name, *_ in ROLE_DEFS}
    runtime_ids = {value for value in RUNTIME.values() if isinstance(value, int) and value}
    if status_message:
        try:
            await status_message.edit(content="♻️ **Reset-Modus aktiv** – lösche vorhandene VOID-Struktur …")
        except Exception:
            pass
    channels = sorted(list(guild.channels), key=lambda c: getattr(c, "position", 0), reverse=True)
    for ch in channels:
        cat_name = ch.category.name if getattr(ch, "category", None) else ""
        should_delete = ch.id in runtime_ids or ch.name in managed_channel_names or cat_name in {"📊 LOGS", "📊 STATS"}
        if should_delete:
            try:
                await ch.delete(reason="Void_Shop Komplett neu aufsetzen")
                deleted["channels"] += 1
                await asyncio.sleep(0.35)
            except Exception as e:
                print(f"[RESET channel] {ch} {e}")
    for cat in list(guild.categories):
        if cat.name in managed_category_names:
            try:
                await cat.delete(reason="Void_Shop Komplett neu aufsetzen")
                deleted["categories"] += 1
                await asyncio.sleep(0.35)
            except Exception as e:
                print(f"[RESET category] {cat} {e}")
    for role in sorted(list(guild.roles), key=lambda r: r.position, reverse=True):
        if role.is_default() or role.managed:
            continue
        if role.name in managed_role_names:
            try:
                await role.delete(reason="Void_Shop Komplett neu aufsetzen")
                deleted["roles"] += 1
                await asyncio.sleep(0.35)
            except Exception as e:
                print(f"[RESET role] {role} {e}")
    reset_runtime_state()
    save_runtime()
    return deleted

async def perform_server_setup(guild:discord.Guild, actor:discord.Member, status_message, mode:str="add"):
    created = {"roles":0,"channels":0,"categories":0}
    deleted = {"roles":0,"channels":0,"categories":0}
    if mode == "reset":
        deleted = await wipe_managed_server(guild, status_message)
    await status_message.edit(content="🚀 **1/7 Rollen erstellen / prüfen …**")
    existing_roles = {r.name:r for r in guild.roles}
    for name,rgb,hoist,mentionable in reversed(ROLE_DEFS):
        if name in existing_roles:
            role = existing_roles[name]
        else:
            try:
                role = await guild.create_role(name=name, colour=discord.Colour.from_rgb(*rgb), hoist=hoist, mentionable=mentionable, reason="Void_Shop v2 Setup")
                created["roles"] += 1
                await asyncio.sleep(0.35)
            except Exception as e:
                print(f"[ROLE] {name}: {e}")
                continue
        lname = name.lower()
        if "unverifiziert" in lname: RUNTIME["role_unverified"] = role.id
        if name == "✅ Verifiziert": RUNTIME["role_verified"] = role.id
        if name == "👤 Member": RUNTIME["role_member"] = role.id
        if name == "🛒 Kunde": RUNTIME["role_customer"] = role.id
        if "vip kunde" in lname: RUNTIME["role_vip"] = role.id
        if name == "🎁 Booster": RUNTIME["role_booster"] = role.id
        if name == "🎫 Supporter": RUNTIME["role_staff"] = role.id
        if name == "🔧 Head-Staff": RUNTIME["role_head_staff"] = role.id
        if name == "🛡️ Moderator": RUNTIME["role_moderator"] = role.id
        if name == "🧰 Trial-Supporter": RUNTIME["role_trial_supporter"] = role.id
        if name == "⚡ Admin": RUNTIME["role_admin"] = role.id
        if name == "👑 Owner": RUNTIME["role_owner"] = role.id

    await status_message.edit(content=f"🚀 **2/7 Kanäle erstellen / prüfen …** Rollen neu: {created['roles']}")
    async def get_cat(name):
        c = discord.utils.get(guild.categories, name=name)
        if c:
            return c
        try:
            c = await guild.create_category(name, reason="Void_Shop v2")
            created["categories"] += 1
            await asyncio.sleep(0.45)
            return c
        except Exception as e:
            print(f"[CATEGORY] {name}: {e}")
            return None

    for cat_name, channels in CHANNELS_SETUP:
        cat = await get_cat(cat_name)
        for ch_name, ch_type, topic in channels:
            ch = discord.utils.get(guild.channels, name=ch_name)
            if not ch:
                try:
                    if ch_type == "voice":
                        ch = await guild.create_voice_channel(ch_name, category=cat, reason="Void_Shop v2")
                    else:
                        ch = await guild.create_text_channel(ch_name, category=cat, topic=topic[:1024] if topic else None, reason="Void_Shop v2")
                    created["channels"] += 1
                    await asyncio.sleep(0.35)
                except Exception as e:
                    print(f"[CH] {ch_name} {e}")
                    continue
            n = ch_name.lower()
            if "willkommen" in n: RUNTIME["welcome"] = ch.id
            if "wiedersehen" in n or "auf-wiedersehen" in n: RUNTIME["goodbye"] = ch.id
            if "regeln" in n: RUNTIME["rules"] = ch.id
            if "ankündigung" in n: RUNTIME["announcements"] = ch.id
            if n.startswith("✅") and "verify" in n: RUNTIME["verify"] = ch.id
            if "how-to-buy" in n: RUNTIME["how_to_buy"] = ch.id
            if "fastflags" in n and ch.type == discord.ChannelType.text and not RUNTIME.get("fastflags"): RUNTIME["fastflags"] = ch.id
            if "produkte" in n: RUNTIME["products"] = ch.id
            if "vouches" in n: RUNTIME["vouches"] = ch.id
            if "bot-commands" in n: RUNTIME["bot_commands"] = ch.id
            if "ticket-erstellen" in n: RUNTIME["ticket_create"] = ch.id
            if "allgemein" in n and not RUNTIME.get("general"): RUNTIME["general"] = ch.id
            if "media" in n: RUNTIME["media"] = ch.id

    await status_message.edit(content=f"🚀 **3/7 LogSystem – {len(LOG_CHANNEL_DEFS)} Spezial-Kanäle …**")
    log_cat = await get_cat("📊 LOGS")
    for ch_name, key in LOG_CHANNEL_DEFS:
        ch = discord.utils.get(guild.text_channels, name=ch_name)
        if not ch:
            try:
                overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False)}
                for role in guild.roles:
                    if role.id in staff_role_ids():
                        overwrites[role] = discord.PermissionOverwrite(view_channel=True, read_message_history=True)
                ch = await guild.create_text_channel(ch_name, category=log_cat, overwrites=overwrites, reason="Void_Shop Logs")
                created["channels"] += 1
                await asyncio.sleep(0.35)
            except Exception as e:
                print(f"[LOG] {e}")
                continue
        RUNTIME[f"log_{key}"] = ch.id
        if key == "ticker":
            RUNTIME["ticker"] = ch.id

    await status_message.edit(content="🚀 **4/7 Stats-Kanäle …**")
    stats_cat = await get_cat("📊 STATS")
    stats_defs = [
        ("👥・Mitglieder: 0","stat_members"),
        ("🚀・Booster: 0","stat_boosters"),
        ("🛒・Kunden: 0","stat_customers"),
        ("🎫・Offene Tickets: 0","stat_tickets"),
    ]
    for name, rkey in stats_defs:
        found = None
        for vc in guild.voice_channels:
            if vc.category_id == (stats_cat.id if stats_cat else None) and name.split("・")[0] in vc.name:
                found = vc
                break
        if found:
            ch = found
        else:
            try:
                overwrites = {guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True)}
                ch = await guild.create_voice_channel(name, category=stats_cat, overwrites=overwrites, reason="Void_Shop Stats")
                created["channels"] += 1
                await asyncio.sleep(0.35)
            except Exception as e:
                print(f"[STATS] {e}")
                continue
        RUNTIME[rkey] = ch.id

    await status_message.edit(content="🚀 **5/7 Berechtigungen & Security-Hinweise …**")
    # Feintuning der Channel-Permissions kann pro Server individuell nachgezogen werden.

    await status_message.edit(content="🚀 **6/7 Panels posten / aktualisieren …**")
    async def post_panel(channel_id, embed, view=None):
        if not channel_id:
            return
        ch = guild.get_channel(channel_id)
        if not ch:
            try:
                ch = await bot.fetch_channel(channel_id)
            except Exception:
                return
        try:
            async for m in ch.history(limit=8):
                if m.author.id == bot.user.id and m.embeds:
                    return
        except Exception:
            pass
        try:
            await ch.send(embed=embed, view=view)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[PANEL] {e}")

    if C("welcome"):
        emb = discord.Embed(
            title="💎 Herzlich Willkommen bei Void Shop! 💎",
            description=(
                "Schön dass du da bist!\n\n"
                "**🛍️ Was wir bieten:**\n"
                "• ⚡ Premium FastFlags\n"
                "• ☁️ Sky\n"
                "• 👕 T-Shirt Template\n"
                "• 🛡️ Anti Alt Ban\n\n"
                "**🚀 Starte so:**\n"
                f"1️⃣ Öffne <#{C('verify') or C('bot_commands') or status_message.channel.id}>\n"
                "2️⃣ Schalte den Discord-Zugang frei\n"
                "3️⃣ Nutze `!verify RobloxName` für Bulletproof Bio-Code-Auth\n"
                "4️⃣ Danach kaufen → `!checkbuy` → Auto-Delivery\n\n"
                "**💬 Support:** Ticket-System\n"
                "**🪙 Treue:** Sammle Void-Coins + Invite-Rewards!\n\n"
                "*Danke dass du Teil der Void Community bist!* ❤️"
            ),
            color=0xFF2020
        )
        if guild.icon:
            emb.set_thumbnail(url=guild.icon.url)
        emb.set_footer(text="Void_Shop • Bio-Verify • Auto-Delivery • Dashboard")
        await post_panel(C("welcome"), emb)

    if C("rules"):
        emb = discord.Embed(title="📜 Void_Shop Regeln", description=(
            "**1️⃣ Respekt** – Kein Toxic, Rassismus, Beleidigungen\n"
            "**2️⃣ Kein Spam / Scam** – AntiScam ist aktiv 🚨\n"
            "**3️⃣ Kein Self-Promo** – ohne Erlaubnis\n"
            "**4️⃣ Support nur via Tickets** 🎫\n"
            "**5️⃣ Keine Weitergabe** von gekauften Produkten\n"
            "**6️⃣ Deutsch / English**\n"
            "**7️⃣ Folge Discord & Roblox ToS**\n\n"
            "✅ Mit dem Freischalten akzeptierst du die Regeln."
        ), color=0xe74c3c)
        await post_panel(C("rules"), emb)

    if C("verify"):
        emb = discord.Embed(
            title="🔐 Verifizierung & Shop-Freischaltung",
            description=(
                "**Schritt 1 – Discord-Zugang**\n"
                "Klicke unten auf **Discord-Zugang freischalten** für Serverzugang +10 Coins.\n\n"
                "**Schritt 2 – Bulletproof Roblox-Verify**\n"
                "Nutze `!verify DeinRobloxName` im Bot-Channel.\n"
                "Du erhältst einen Sicherheitscode wie `void-8392`, trägst ihn kurz in deine Roblox-Bio ein und klickst anschließend auf **Bestätigen**.\n\n"
                "**Danach möglich:**\n"
                "• `!checkbuy` → Kaufprüfung\n"
                "• Auto-Delivery per DM in unter 5 Sekunden\n"
                "• sichere Roblox-Identität ohne Fake-Namen"
            ),
            color=0x2ecc71
        )
        try:
            bot.add_view(OneClickVerifyView())
        except Exception:
            pass
        await post_panel(C("verify"), emb, OneClickVerifyView())

    if C("how_to_buy"):
        emb = discord.Embed(title="🛒 How to Buy – So kaufst du", description=(
            "**1️⃣ Bulletproof verifizieren**\n"
            "`!verify DeinRobloxName`\n\n"
            "**2️⃣ Produkt wählen**\n"
            f"`!products` in <#{C('bot_commands') or C('general') or status_message.channel.id}>\n\n"
            "**3️⃣ Roblox Gamepass kaufen**\n"
            "Link via Ticket / DM\n\n"
            "**4️⃣ `!checkbuy` ausführen**\n"
            "Bot prüft den Kauf automatisch\n\n"
            "**5️⃣ Auto-Delivery < 5 Sekunden**\n"
            "DM mit Download-Links / Dateien\n\n"
            "❓ Fragen? → Ticket öffnen!"
        ), color=0xFFD700)
        await post_panel(C("how_to_buy"), emb)

    ffid = C("fastflags")
    if ffid:
        emb = discord.Embed(title="⚡ FastFlags – Info", description=(
            "**Was sind FastFlags?**\n"
            "Roblox Client Tweaks für mehr FPS, bessere Grafik.\n\n"
            "**Pakete:**\n"
            "• **Premium FastFlags** – 250 R$\n"
            "• **FastFlags Ultra** – 499 R$\n"
            "• **Starter Bundle** – 75 R$\n"
            "• **Sky** – 180 R$\n"
            "• **T-Shirt Template** – 120 R$\n"
            "• **Anti Alt Ban** – 399 R$\n\n"
            "`!verify` → kaufen → `!checkbuy` → Auto-Delivery <5s"
        ), color=0xff8800)
        await post_panel(ffid, emb)

    if C("ticket_create"):
        emb = discord.Embed(title="🎫 Void_Shop Support – Ticket erstellen", description=(
            "Wähle unten dein Anliegen:\n\n"
            "**🛒 Produkt kaufen**\n"
            "→ Kaufberatung, Produktfragen\n\n"
            "**💬 Allgemeiner Support**\n"
            "→ Technik, Fragen, Hilfe\n\n"
            "**🤝 Partnerschaft**\n"
            "→ Kooperationen, Resell\n\n"
            "*Antwortzeit, Claims und Bewertungen werden jetzt direkt fürs Dashboard getrackt.*"
        ), color=0x1abc9c)
        emb.set_footer(text="Void_Shop Ticket • Claim • 3-Fragen Survey • Staff Leaderboard")
        try:
            bot.add_view(TicketPanelView())
            bot.add_view(TicketControlView())
        except Exception:
            pass
        await post_panel(C("ticket_create"), emb, TicketPanelView())

    await status_message.edit(content="🚀 **7/7 Speichern, Invite-Cache & Stats initialisieren …**")
    save_runtime()
    try:
        await refresh_invite_cache(guild)
    except Exception:
        pass
    try:
        await update_stats_channels(guild)
    except Exception as e:
        print(e)

    emb_done = discord.Embed(
        title="✅ Void_Shop Setup abgeschlossen!",
        description=(
            f"**Modus:** {'Komplett neu aufgesetzt' if mode == 'reset' else 'Nur fehlende Elemente hinzugefügt'}\n\n"
            f"**Neu erstellt:**\n"
            f"• Rollen: **{created['roles']}**\n"
            f"• Kanäle: **{created['channels']}**\n"
            f"• Kategorien: **{created['categories']}**\n\n"
            f"**Beim Reset entfernt:**\n"
            f"• Rollen: **{deleted['roles']}**\n"
            f"• Kanäle: **{deleted['channels']}**\n"
            f"• Kategorien: **{deleted['categories']}**\n\n"
            "**Aktiv:**\n"
            "🛍️ Auto-Delivery • 🔐 Bio-Code-Auth • 🚨 AntiScam\n"
            "📈 Live-Käufe Ticker • 🪙 Void-Coins + Invite-Rewards\n"
            "🎫 Ticket-Claim + Supporter-Leaderboard\n"
            f"📜 {len(LOG_CHANNEL_DEFS)} Log-Kanäle • 📊 Live Stats\n"
            f"👑 Dashboard: http://localhost:{DASHBOARD_PORT}\n\n"
            "**Kommandos:**\n"
            "`!verify` `!checkbuy` `!products` `!coins` `!shop` `!redeem` `!daily`\n\n"
            "*Owner-Daten wie Revenue / Staff / Logs sind jetzt direkt im Dashboard sichtbar.*"
        ),
        color=0x2ecc71
    )
    emb_done.set_footer(text="Void_Shop v2.0 ULTIMATE • RealVexo696")
    if guild.system_channel:
        await guild.system_channel.send(embed=emb_done)
    else:
        await status_message.channel.send(embed=emb_done)
    try:
        log_emb = make_embed(
            "👑 Server Setup abgeschlossen",
            f"Admin: {actor.mention}\nModus: **{mode}**\nRollen neu: {created['roles']}\nKanäle neu: {created['channels']}\nKategorien neu: {created['categories']}",
            0x2ecc71,
            actor
        )
        await send_log(bot, "owner", log_emb, discord_id=actor.id)
        await send_log(bot, "bot", log_emb, discord_id=actor.id)
    except Exception:
        pass
    try:
        await status_message.delete()
    except Exception:
        pass

class StartSetupChoiceView(discord.ui.View):
    def __init__(self, author_id:int):
        super().__init__(timeout=180)
        self.author_id = author_id

    async def interaction_check(self, interaction:discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Nur der Admin, der `!start` ausgeführt hat, kann diese Auswahl benutzen.", ephemeral=True)
            return False
        return True

    async def disable_all(self, message):
        for child in self.children:
            child.disabled = True
        try:
            await message.edit(view=self)
        except Exception:
            pass

    @discord.ui.button(label="❌ Abbruch", style=discord.ButtonStyle.red)
    async def abort_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ Setup abgebrochen.", embed=None, view=self)

    @discord.ui.button(label="➕ Nur hinzufügen", style=discord.ButtonStyle.green)
    async def add_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.defer()
        await self.disable_all(interaction.message)
        await interaction.message.edit(content="➕ **Setup-Modus: Nur hinzufügen** – es werden nur fehlende Elemente ergänzt.", embed=None, view=self)
        await perform_server_setup(interaction.guild, interaction.user, interaction.message, mode="add")

    @discord.ui.button(label="♻️ Komplett neu aufsetzen", style=discord.ButtonStyle.blurple)
    async def reset_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.defer()
        await self.disable_all(interaction.message)
        await interaction.message.edit(content="♻️ **Setup-Modus: Komplett neu aufsetzen** – alte VOID-Struktur wird gelöscht und sauber neu aufgebaut.", embed=None, view=self)
        await perform_server_setup(interaction.guild, interaction.user, interaction.message, mode="reset")

@bot.command(name="start")
@commands.has_permissions(administrator=True)
async def start_cmd(ctx):
    if OWNER_ID and ctx.author.id != OWNER_ID and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Nur Server-Owner / Admin.")
    emb = discord.Embed(
        title="🚀 Void_Shop Setup-Assistent",
        description=(
            "Du hast `!start` ausgeführt.\n\n"
            "Bitte wähle **eine** von 3 Möglichkeiten:\n\n"
            "**1️⃣ Abbruch**\n"
            "→ bricht den Vorgang sofort ab\n\n"
            "**2️⃣ Nur hinzufügen**\n"
            "→ fehlende Rollen, Kanäle, Logs, Panels und Stats ergänzen\n\n"
            "**3️⃣ Komplett neu aufsetzen**\n"
            "→ löscht die vorhandene VOID-Struktur und baut alles sauber neu auf"
        ),
        color=0xFF2020
    )
    emb.set_footer(text="Void_Shop • Setup mit Buttons")
    await ctx.send(embed=emb, view=StartSetupChoiceView(ctx.author.id))

# =====================================================================
#  📊 STATS LOOP
# =====================================================================
async def update_stats_channels(guild:discord.Guild=None):
    if guild is None:
        if not GUILD_ID: return
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            try: guild = await bot.fetch_guild(GUILD_ID)
            except: return
    members = guild.member_count or len(guild.members)
    boosters = len(guild.premium_subscribers)
    try:
        async with get_db() as db:
            cur = await db_execute(db, "SELECT COUNT(*) FROM users WHERE purchases > 0")
            r = await cur.fetchone()
            customers = r[0] if r else 0
    except: customers = 0
    try:
        open_tickets = await count_open_tickets()
    except: open_tickets = 0
    mapping = [
        (RUNTIME.get("stat_members"), f"👥・Mitglieder: {members}"),
        (RUNTIME.get("stat_boosters"), f"🚀・Booster: {boosters}"),
        (RUNTIME.get("stat_customers"), f"🛒・Kunden: {customers}"),
        (RUNTIME.get("stat_tickets"), f"🎫・Offene Tickets: {open_tickets}"),
    ]
    for ch_id, name in mapping:
        if not ch_id: continue
        ch = guild.get_channel(ch_id)
        if ch and ch.name != name:
            try:
                await ch.edit(name=name, reason="Void_Shop Stats Update")
                await asyncio.sleep(1.1)
            except Exception as e:
                print(f"[stats] {e}")

@tasks.loop(minutes=5)
async def stats_loop():
    try:
        guilds = [bot.get_guild(GUILD_ID)] if GUILD_ID else list(bot.guilds)
        for g in guilds:
            if g:
                await update_stats_channels(g)
    except Exception as e:
        print(f"[stats_loop] {e}")

@stats_loop.before_loop
async def before_stats():
    await bot.wait_until_ready()
    await asyncio.sleep(8)

# =====================================================================
#  🤖 EVENTS / LOGSYSTEM 2.0
# =====================================================================
@bot.event
async def on_ready():
    print(f"[READY] {bot.user} ({bot.user.id})")
    for guild in bot.guilds:
        try:
            await refresh_invite_cache(guild)
        except Exception:
            pass
        try:
            await update_stats_channels(guild)
        except Exception:
            pass
    try:
        emb = make_embed("🤖 Bot online", f"Eingeloggt als **{bot.user}**\nGuilds: **{len(bot.guilds)}**\nDashboard-Port: **{DASHBOARD_PORT}**", 0x2ecc71)
        await send_log(bot, "bot", emb, discord_id=(bot.user.id if bot.user else None))
    except Exception:
        pass

@bot.event
async def on_invite_create(invite):
    await refresh_invite_cache(invite.guild)
    inviter = invite.inviter.mention if invite.inviter else "Unbekannt"
    emb = make_embed("🔗 Invite erstellt", f"Code: `{invite.code}`\nEinladender: {inviter}\nChannel: {getattr(invite.channel, 'mention', '–')}", 0x5865F2)
    await send_log(bot, "invite", emb, discord_id=(invite.inviter.id if invite.inviter else None), meta=f"code={invite.code}")

@bot.event
async def on_invite_delete(invite):
    await refresh_invite_cache(invite.guild)
    emb = make_embed("🗑️ Invite gelöscht", f"Code: `{invite.code}`", 0x95a5a6)
    await send_log(bot, "invite", emb, meta=f"code={invite.code}")

@bot.event
async def on_member_join(member):
    used_invite = await detect_used_invite(member.guild)
    inviter_text = ""
    reward_text = ""
    try:
        async with get_db() as db:
            await db_execute(db, "INSERT OR IGNORE INTO users(discord_id, joined_at) VALUES(?, CURRENT_TIMESTAMP)", (member.id,))
            await db_commit(db)
    except Exception:
        pass
    try:
        ur_id = ROL("unverified")
        if ur_id:
            r = member.guild.get_role(ur_id)
            if r:
                await member.add_roles(r, reason="Void_Shop Auto Unverified")
    except Exception:
        pass
    if used_invite and used_invite.inviter:
        inviter_text = f"\nEingeladen von: {used_invite.inviter.mention} (`{used_invite.code}`)"
        try:
            rewarded = await reward_invite_if_needed(used_invite.inviter.id, member.id, used_invite.code)
            if rewarded:
                reward_text = f"\n🎁 {used_invite.inviter.mention} erhielt +{COIN_REWARDS['invite']} Void-Coins."
                coin_emb = make_embed("🪙 Invite-Reward", f"{used_invite.inviter.mention} hat **{member.mention}** eingeladen → +{COIN_REWARDS['invite']} Coins", 0xFFD700, used_invite.inviter)
                await send_log(bot, "coins", coin_emb, discord_id=used_invite.inviter.id)
            invite_emb = make_embed("🔗 Mitglied per Invite beigetreten", f"Neues Mitglied: {member.mention}\nEinladender: {used_invite.inviter.mention}\nCode: `{used_invite.code}`{reward_text}", 0x5865F2, member)
            await send_log(bot, "invite", invite_emb, discord_id=member.id)
        except Exception as e:
            print(f"[invite reward] {e}")
    wc_id = C("welcome")
    if wc_id:
        ch = member.guild.get_channel(wc_id)
        if ch:
            emb = discord.Embed(
                title=f"Willkommen bei Void Shop, {member.display_name}! 💎",
                description=(
                    f"**Herzlich Willkommen bei Void Shop**, {member.mention}!\n\n"
                    "🛍️ **Was dich erwartet:**\n"
                    "• ⚡ FastFlags • ☁️ Sky\n"
                    "• 👕 T-Shirt Template • 🛡️ Anti Alt Ban\n\n"
                    f"👉 **Starte hier:** <#{C('verify') or ch.id}>\n"
                    "🔓 Discord-Zugang freischalten\n"
                    "🔐 Danach `!verify DeinRobloxName` für Bulletproof Roblox-Verify\n\n"
                    "💬 Fragen? Eröffne ein Ticket!\n"
                    "🪙 Sammle Void-Coins für Rabatte!\n"
                    "🎁 Lade Freunde ein und erhalte Invite-Rewards!\n\n"
                    f"*Du bist Mitglied **#{member.guild.member_count}*** ❤️"
                ),
                color=0xFF2020,
                timestamp=datetime.datetime.utcnow()
            )
            try:
                emb.set_thumbnail(url=member.display_avatar.url)
                if member.guild.icon:
                    emb.set_footer(text="Void_Shop • danke dass du da bist", icon_url=member.guild.icon.url)
            except Exception:
                pass
            try:
                await ch.send(content=member.mention, embed=emb)
            except Exception:
                pass
    emb_log = make_embed(
        "📥 Mitglied beigetreten",
        f"{member.mention} **{member}**\nAccount erstellt: <t:{int(member.created_at.timestamp())}:R>\nID: `{member.id}`{inviter_text}{reward_text}",
        0x2ecc71,
        member
    )
    await send_log(bot, "join", emb_log, discord_id=member.id)
    try:
        await update_stats_channels(member.guild)
    except Exception:
        pass

@bot.event
async def on_member_remove(member):
    gc_id = C("goodbye")
    if gc_id:
        ch = member.guild.get_channel(gc_id)
        if ch:
            emb = discord.Embed(
                title="👋 Auf Wiedersehen!",
                description=f"**{member.display_name}** hat den Server verlassen.\n\nWir hoffen du kommst bald wieder zurück zu **Void Shop**! ❤️\n\n`{member}` • `{member.id}`",
                color=0x95a5a6,
                timestamp=datetime.datetime.utcnow()
            )
            try:
                emb.set_thumbnail(url=member.display_avatar.url)
            except Exception:
                pass
            try:
                await ch.send(embed=emb)
            except Exception:
                pass
    emb_log = make_embed("📤 Mitglied verlassen", f"**{member}**\n`{member.id}`", 0xe74c3c, member)
    await send_log(bot, "leave", emb_log, discord_id=member.id)
    try:
        await update_stats_channels(member.guild)
    except Exception:
        pass

@bot.event
async def on_member_update(before, after):
    if before.bot:
        return
    if before.nick != after.nick:
        emb = make_embed("🪪 Nickname geändert", f"{after.mention}\nVorher: `{before.nick or before.name}`\nNachher: `{after.nick or after.name}`", 0x7289DA, after)
        await send_log(bot, "system", emb, discord_id=after.id)
    before_roles = {r.id for r in before.roles if not r.is_default()}
    after_roles = {r.id for r in after.roles if not r.is_default()}
    added = [r.mention for r in after.roles if r.id in (after_roles - before_roles)]
    removed = [r.mention for r in before.roles if r.id in (before_roles - after_roles)]
    if added or removed:
        parts = []
        if added:
            parts.append("Hinzugefügt: " + ", ".join(added[:10]))
        if removed:
            parts.append("Entfernt: " + ", ".join(removed[:10]))
        emb = make_embed("🎭 Rollen-Update", f"{after.mention}\n" + "\n".join(parts), 0x7289DA, after)
        await send_log(bot, "system", emb, discord_id=after.id)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel == after.channel:
        changes = []
        if before.self_mute != after.self_mute: changes.append(f"Mute {before.self_mute}→{after.self_mute}")
        if before.self_deaf != after.self_deaf: changes.append(f"Deaf {before.self_deaf}→{after.self_deaf}")
        if before.self_stream != after.self_stream: changes.append(f"Stream {before.self_stream}→{after.self_stream}")
        if changes:
            emb = make_embed("🎙️ Voice Update", f"{member.mention}\n" + "\n".join(changes), 0x3498db, member)
            await send_log(bot, "voice", emb, discord_id=member.id, channel_id=(after.channel.id if after.channel else None))
        return
    if after.channel and not before.channel:
        desc = f"{member.mention} → 🔊 **{after.channel.name}**"; color = 0x2ecc71
    elif before.channel and not after.channel:
        desc = f"{member.mention} ← 🔊 **{before.channel.name}**"; color = 0xe74c3c
    else:
        desc = f"{member.mention} 🔀 **{before.channel.name}** → **{after.channel.name}**"; color = 0xf39c12
    emb = make_embed("🎙️ Voice", desc, color, member)
    await send_log(bot, "voice", emb, discord_id=member.id, channel_id=(after.channel.id if after.channel else before.channel.id if before.channel else None))

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return
    if message.guild:
        if message.channel.name.startswith("ticket-") and is_staff_member(message.author):
            try:
                await note_ticket_staff_response(message.channel.id, message.author.id)
            except Exception as e:
                print(f"[ticket response] {e}")
        bad = scan_message_antiscam(message.content)
        if bad:
            try:
                await message.delete()
            except Exception:
                pass
            try:
                emb_warn = discord.Embed(title="🚨 Link blockiert – Anti-Scam", description="Dein Link wurde entfernt (nicht gewhitelistet).\n\n**Erlaubt:** `roblox.com`, `discord.com`, `discord.gg`, `youtube.com`, `github.com`", color=0xe74c3c)
                await message.channel.send(f"{message.author.mention}", embed=emb_warn, delete_after=20)
            except Exception:
                pass
            details = "\n".join([f"• `{b['url']}` → {b['reason']}" for b in bad])
            log_emb = make_embed("🚨 AntiScam – Link gelöscht", f"**User:** {message.author.mention}\n**Channel:** {message.channel.mention}\n\n{details}\n\n```{message.content[:800]}```", 0xe74c3c, message.author)
            await send_log(bot, "antiscam", log_emb, discord_id=message.author.id, channel_id=message.channel.id, meta=str(bad))
            try:
                async with get_db() as db:
                    for b in bad:
                        await db_execute(db, "INSERT INTO antiscam_hits(discord_id,channel_id,url,reason) VALUES(?,?,?,?)", (message.author.id, message.channel.id, b["url"], b["reason"]))
                    await db_commit(db)
            except Exception as e:
                print(f"[antiscam db] {e}")
            return
        if "vouch" in message.channel.name.lower():
            c = message.content.lower()
            if message.content.count("⭐") >= 5 or "5/5" in c or "5★" in c or "5 sterne" in c:
                await add_coins(message.author.id, COIN_REWARDS["vouch_5star"], "vouch_5star")
                try:
                    async with get_db() as db:
                        await db_execute(db, "INSERT INTO vouches(discord_id,stars,message,coins_awarded) VALUES(?,?,?,?)", (message.author.id, 5, message.content[:500], COIN_REWARDS["vouch_5star"]))
                        await db_commit(db)
                except Exception:
                    pass
                try:
                    await message.add_reaction("✅")
                    await message.reply(f"Danke für dein 5⭐ Vouch! +{COIN_REWARDS['vouch_5star']} Coins!", delete_after=15)
                except Exception:
                    pass
                log_emb = make_embed("🪙 Vouch belohnt", f"{message.author.mention} 5★ → +{COIN_REWARDS['vouch_5star']} Coins", 0xFFD700, message.author)
                await send_log(bot, "coins", log_emb, discord_id=message.author.id, channel_id=message.channel.id)
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    content = (message.content[:1000] + "…") if len(message.content) > 1000 else message.content
    emb = make_embed("🗑️ Nachricht gelöscht", f"**Channel:** {message.channel.mention}\n**Author:** {message.author.mention}\n\n```{content or '[Embed/Attachment]'}```", 0xe74c3c, message.author)
    await send_log(bot, "message", emb, discord_id=message.author.id, channel_id=message.channel.id, meta=message.content)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or not before.guild:
        return
    if before.content == after.content:
        return
    emb = discord.Embed(title="✏️ Nachricht bearbeitet", color=0xf39c12, timestamp=datetime.datetime.utcnow())
    emb.add_field(name="Vorher", value=(before.content[:1000] or "…"), inline=False)
    emb.add_field(name="Nachher", value=(after.content[:1000] or "…"), inline=False)
    emb.add_field(name="User / Channel", value=f"{after.author.mention} • {after.channel.mention} • [Jump]({after.jump_url})", inline=False)
    await send_log(bot, "message", emb, discord_id=after.author.id, channel_id=after.channel.id)

@bot.event
async def on_member_ban(guild, user):
    emb = make_embed("🔨 Ban", f"{getattr(user,'mention',user)} **{user}**\n`{user.id}`", 0xe74c3c)
    await send_log(bot, "mod", emb, discord_id=user.id)

@bot.event
async def on_member_unban(guild, user):
    emb = make_embed("🔓 Unban", f"{user} `{user.id}`", 0x2ecc71)
    await send_log(bot, "mod", emb, discord_id=user.id)

@bot.event
async def on_guild_role_create(role):
    emb = make_embed("🆕 Rolle erstellt", f"{role.mention if hasattr(role,'mention') else role.name}\nID: `{role.id}`", 0x7289DA)
    await send_log(bot, "system", emb, channel_id=None, meta=f"role_id={role.id}")

@bot.event
async def on_guild_role_delete(role):
    emb = make_embed("🗑️ Rolle gelöscht", f"{role.name}\nID: `{role.id}`", 0x95a5a6)
    await send_log(bot, "system", emb, meta=f"role_id={role.id}")

@bot.event
async def on_guild_role_update(before, after):
    changes = []
    if before.name != after.name:
        changes.append(f"Name: `{before.name}` → `{after.name}`")
    if before.colour != after.colour:
        changes.append(f"Farbe: `{before.colour}` → `{after.colour}`")
    if before.permissions.value != after.permissions.value:
        changes.append("Permissions geändert")
    if changes:
        emb = make_embed("✏️ Rolle bearbeitet", f"**{after.name}**\n" + "\n".join(changes), 0x7289DA)
        await send_log(bot, "system", emb, meta=f"role_id={after.id}")

@bot.event
async def on_guild_channel_create(channel):
    emb = make_embed("🆕 Kanal erstellt", f"#{channel.name}\nTyp: `{channel.type}`", 0x7289DA)
    await send_log(bot, "system", emb, channel_id=channel.id)
    if "ticket" in channel.name.lower():
        emb = make_embed("🎫 Ticket geöffnet", f"{channel.mention} erstellt", 0x1abc9c)
        await send_log(bot, "ticket", emb, channel_id=channel.id)

@bot.event
async def on_guild_channel_delete(channel):
    emb = make_embed("🗑️ Kanal gelöscht", f"#{channel.name}\nTyp: `{channel.type}`", 0x95a5a6)
    await send_log(bot, "system", emb, meta=f"channel_name={channel.name}")
    if "ticket" in channel.name.lower():
        emb = make_embed("🎫 Ticket geschlossen", f"#{channel.name} gelöscht", 0x95a5a6)
        await send_log(bot, "ticket", emb, channel_id=channel.id)

@bot.event
async def on_guild_channel_update(before, after):
    changes = []
    if before.name != after.name:
        changes.append(f"Name: `{before.name}` → `{after.name}`")
    if getattr(before, 'topic', None) != getattr(after, 'topic', None):
        changes.append("Topic geändert")
    if getattr(before, 'category_id', None) != getattr(after, 'category_id', None):
        changes.append("Kategorie geändert")
    if changes:
        emb = make_embed("✏️ Kanal bearbeitet", f"#{after.name}\n" + "\n".join(changes), 0x7289DA)
        await send_log(bot, "system", emb, channel_id=after.id)

# =====================================================================
#  💬 COMMANDS
# =====================================================================
@bot.command(name="help")
async def help_cmd(ctx):
    e = discord.Embed(title="🛍️ Void_Shop v2 ULTIMATE – Befehle", color=0xFF2020)
    e.add_field(name="👑 Setup", value="`!start` – öffnet den Setup-Assistenten mit 3 Auswahlmöglichkeiten", inline=False)
    e.add_field(name="🔐 Verify", value="`!verify Name` – Bulletproof Roblox Bio-Code-Auth\nDiscord-Zugang im <#{}>".format(C("verify") or 0), inline=False)
    e.add_field(name="🛍️ Shop", value="`!checkbuy` – Auto-Delivery\n`!products`", inline=False)
    e.add_field(name="🪙 Coins", value="`!coins` `!shop` `!redeem <150|300|500|800>` `!daily` `!coinlb`", inline=False)
    e.add_field(name="🎫 Tickets", value="Erstellen im Ticket-Panel\nClaim + Survey + Staff-Tracking", inline=False)
    e.add_field(name="👑 Owner", value="Revenue / Staff / Logs / Tickets primär im Dashboard sichtbar", inline=False)
    e.set_footer(text=f"Void_Shop v2.0 ULTIMATE • Web: http://localhost:{DASHBOARD_PORT}")
    await ctx.send(embed=e)

@bot.command(name="verify")
async def verify_cmd(ctx, *, roblox_name:str=None):
    if not roblox_name:
        return await ctx.send("Usage: `!verify DeinRobloxName`")
    try: await ctx.message.delete()
    except: pass
    res = await roblox_username_to_id(roblox_name)
    if not res:
        return await ctx.send(f"❌ Roblox-User **{roblox_name}** nicht gefunden.", delete_after=15)
    roblox_id, display = res
    code = generate_bio_code()
    async with get_db() as db:
        await db_execute(db, "INSERT OR REPLACE INTO verify_codes(discord_id,roblox_id,roblox_name,code,created_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
            (ctx.author.id, roblox_id, roblox_name, code))
        await db_commit(db)
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

@bot.command(name="checkbuy")
async def checkbuy_cmd(ctx):
    async with get_db() as db:
        cur = await db_execute(db, "SELECT roblox_id, roblox_name FROM users WHERE discord_id=? AND verified=1", (ctx.author.id,))
        row = await cur.fetchone()
    if not row:
        return await ctx.send(f"{ctx.author.mention} ❌ Nicht für den Shop verifiziert! Nutze zuerst `!verify DeinRobloxName` für die sichere Bio-Code-Auth.", delete_after=20)
    try: roblox_id=row[0]; roblox_name=row[1]
    except: roblox_id=row["roblox_id"]; roblox_name=row["roblox_name"]
    msg = await ctx.send(f"🔍 Prüfe Käufe für **{roblox_name}** (`{roblox_id}`) …")
    product_key, product = await find_owned_product(roblox_id)
    if not product:
        await msg.edit(content=f"❌ Kein neuer Gamepass-Kauf gefunden für **{roblox_name}**.\nKaufe zuerst im Roblox-Shop → dann `!checkbuy` erneut.")
        log_emb = make_embed("🛍️ checkbuy – nichts gefunden",
            f"{ctx.author.mention} • {roblox_name} (`{roblox_id}`)",0xe67e22,ctx.author)
        await send_log(bot,"shop",log_emb,discord_id=ctx.author.id)
        return
    await record_purchase(ctx.author.id, roblox_id, product_key, product)
    await msg.edit(content=f"✅ Kauf erkannt: **{product['name']}** – bereite Auto-Delivery vor …")
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
    dm_ok=True
    dm_message = None
    try:
        dm = await ctx.author.create_dm()
        dm_message = await dm.send(embed=embed)
    except Exception:
        dm_ok=False
        await ctx.send(f"⚠️ Konnte keine DM senden! Öffne deine DMs.\n\n**Manuell:**\n"+"\n".join(files), delete_after=60)
    try:
        async with get_db() as db:
            cur = await db_execute(db, "SELECT id FROM purchases WHERE discord_id=? AND product_key=? ORDER BY id DESC LIMIT 1", (ctx.author.id, product_key))
            prow = await cur.fetchone()
            purchase_id = prow[0] if prow else None
            await db_execute(db, "INSERT INTO deliveries(purchase_id, discord_id, product_key, dm_message_id, success) VALUES(?,?,?,?,?)", (purchase_id, ctx.author.id, product_key, str(getattr(dm_message, 'id', '')), 1 if dm_ok else 0))
            await db_commit(db)
    except Exception as e:
        print(f"[delivery log] {e}")
    # Rollen
    try:
        role_key = product.get("role_give","customer")
        # map
        role_map_lookup = {
            "customer": ROL("customer"),
            "vip": ROL("vip"),
            "premium": ROL("customer"),
        }
        role_id = role_map_lookup.get(role_key, 0)
        if role_id:
            r = ctx.guild.get_role(role_id)
            if r: await ctx.author.add_roles(r, reason="Void_Shop Auto-Delivery")
    except: pass
    coins_reward = product.get("coins_reward", COIN_REWARDS["purchase"])
    await add_coins(ctx.author.id, coins_reward, "purchase", product_key)
    await msg.edit(content=f"🎉 **{product['name']}** erfolgreich geliefert! Check deine DMs {ctx.author.mention}\n+{coins_reward} Void-Coins!")
    try:
        await update_stats_channels(ctx.guild)
    except Exception:
        pass
    # ticker
    tc = L("ticker")
    if tc:
        await send_purchase_ticker(bot, tc, ctx.author, product["name"], product.get("robux_price",0))
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
    async with get_db() as db:
        cur = await db_execute(db, "SELECT discord_id, coins, purchases FROM users ORDER BY coins DESC LIMIT 10")
        rows = await cur.fetchall()
    desc = ""
    for i,row in enumerate(rows,1):
        try: did=row[0]; coins=row[1]; pur=row[2]
        except: did=row["discord_id"]; coins=row["coins"]; pur=row["purchases"]
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

def is_owner():
    async def predicate(ctx): return ctx.author.id == OWNER_ID or OWNER_ID==0 or ctx.author.guild_permissions.administrator
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
    async with get_db() as db:
        cur = await db_execute(db, "SELECT staff_id,tickets_claimed,tickets_closed,rating_count, CASE WHEN rating_count>0 THEN rating_sum*1.0/rating_count ELSE 0 END as avg FROM staff_stats ORDER BY tickets_closed DESC LIMIT 10")
        rows = await cur.fetchall()
    desc=""
    for i,row in enumerate(rows,1):
        try: sid,claimed,closed,rc,avg = row[0],row[1],row[2],row[3],row[4]
        except: sid=row["staff_id"]; claimed=row["tickets_claimed"]; closed=row["tickets_closed"]; rc=row["rating_count"]; avg=row["avg"]
        desc+=f"**#{i}** <@{sid}> – {closed} closed / {claimed} claimed · ⭐ {avg:.1f} ({rc})\n"
    emb = discord.Embed(title="👑 Staff Leaderboard", description=desc or "Keine Daten – Staff Stats werden beim Ticket-Close automatisch getrackt.", color=0x2c3e50)
    await ctx.send(embed=emb, delete_after=120)

@bot.command(name="ticker")
@commands.has_permissions(manage_guild=True)
async def ticker_test(ctx):
    ch = L("ticker")
    if ch:
        await send_purchase_ticker(bot, ch, ctx.author, "Premium FastFlags Paket", 250)
        await ctx.send("✅ Test-Ticker gesendet", delete_after=5)
    else:
        await ctx.send("Ticker-Kanal nicht gesetzt – führe `!start` aus.", delete_after=10)

# =====================================================================
#  👑 WEB DASHBOARD
# =====================================================================
def run_dashboard():
    if not DASHBOARD_ENABLED or not HAS_FLASK:
        print("[Dashboard] OFF")
        return
    from flask import Flask, render_template_string, request, redirect, session, jsonify
    app = Flask(__name__)
    app.secret_key = DASHBOARD_SECRET
    BASE_HTML = """<!doctype html><html lang=de><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Void_Shop v2 Dashboard</title>
<style>
:root{--bg:#0b0b0f;--card:#141421;--red:#FF2020;--gold:#FFD700;--muted:#889;--green:#2ecc71;--blue:#3498db}
*{box-sizing:border-box;font-family:Inter,Segoe UI,Arial,sans-serif}
body{margin:0;background:var(--bg);color:#eee}
a{color:var(--gold);text-decoration:none}
.nav{display:flex;gap:18px;padding:14px 24px;background:#11111a;border-bottom:2px solid #1f1f2e;position:sticky;top:0;z-index:9}
.nav b{color:var(--red);font-size:18px}
.nav a{padding:6px 12px;border-radius:8px}
.nav a:hover{background:#222239}
.wrap{max-width:1350px;margin:24px auto;padding:0 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:16px}
.card{background:var(--card);border:1px solid #222235;border-radius:16px;padding:18px;box-shadow:0 4px 30px #0005}
.card h3{margin:0 0 8px;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.big{font-size:30px;font-weight:800}
.gold{color:var(--gold)}.red{color:var(--red)}.green{color:var(--green)}.blue{color:var(--blue)}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid #252538}
th{color:var(--muted)}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;background:#222}
.badge.g{background:#133d1a;color:#5feca0}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.two{grid-template-columns:1fr}}
.footer{opacity:.5;text-align:center;padding:30px;font-size:12px}
.btn{background:var(--red);color:#fff;border:none;padding:9px 15px;border-radius:10px;font-weight:600;cursor:pointer}
input,textarea{width:100%;padding:10px;background:#0f0f18;border:1px solid #2a2a40;color:#eee;border-radius:10px}
</style></head><body>
<div class=nav><b>🛍️ VOID_SHOP v2</b>
<a href="/">Dashboard</a><a href="/products">Produkte</a><a href="/coins">Coins</a><a href="/tickets">Tickets</a><a href="/logs">Logs</a><a href="/staff">Staff</a>
<span style="flex:1"></span><a href="/logout">Logout</a></div>
<div class=wrap>{{ content|safe }}
<div class=footer>Void_Shop v2.0 ULTIMATE • RealVexo696 • Companion to VOID-TOOLS v2.6 • aiosqlite={{aiosqlite}}</div>
</div></body></html>"""
    def page(content): return render_template_string(BASE_HTML, content=content, aiosqlite=HAS_AIOSQLITE)
    def q(sql, args=(), one=False):
        con = sqlite3.connect(DATABASE_PATH); con.row_factory=sqlite3.Row
        cur = con.execute(sql, args); rv = cur.fetchall(); con.close()
        return (rv[0] if rv else None) if one else rv
    @app.route("/login", methods=["GET","POST"])
    def login():
        if request.method=="POST":
            if request.form.get("code") in (DASHBOARD_LOGIN_CODE, str(OWNER_ID)):
                session["owner"]=True
                return redirect("/")
            err="<p style=color:#ff6b6b>Falscher Code</p>"
        else: err=""
        return f"""<!doctype html><meta charset=utf-8><title>Void_Shop Login</title>
<style>body{{margin:0;background:#0b0b0f;color:#eee;font-family:Inter,Segoe UI,Arial;display:grid;place-items:center;height:100vh}}
.box{{background:#141421;padding:36px;border-radius:20px;max-width:400px;width:90%;border:1px solid #252538}}
input{{width:100%;padding:13px;background:#0f0f18;border:1px solid #2a2a40;color:#eee;border-radius:12px;margin:10px 0;font-size:16px}}
button{{width:100%;padding:13px;background:#FF2020;color:#fff;border:none;border-radius:12px;font-weight:700;font-size:16px;cursor:pointer}}
</style>
<div class=box><h1 style="margin:0;color:#FF2020">👑 Void_Shop v2</h1><p style="color:#889">Owner Dashboard</p>
{err}
<form method=post><input type=password name=code placeholder="Owner Code" autofocus>
<button>Einloggen</button></form>
<small style="color:#666">Aktueller Login-Code: <b>{DASHBOARD_LOGIN_CODE}</b></small></div>"""
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
        import asyncio
        data = asyncio.run(get_revenue_summary())
        users = q("SELECT COUNT(*) c FROM users", one=True); users = users["c"] if users else 0
        verified = q("SELECT COUNT(*) c FROM users WHERE verified=1", one=True); verified = verified["c"] if verified else 0
        coins_total = q("SELECT COALESCE(SUM(coins),0) s FROM users", one=True); coins_total = coins_total["s"] if coins_total else 0
        recent = q("SELECT p.*, u.roblox_name FROM purchases p LEFT JOIN users u ON u.discord_id=p.discord_id ORDER BY p.created_at DESC LIMIT 15")
        coin_lb = q("SELECT discord_id, coins, purchases FROM users ORDER BY coins DESC LIMIT 10")
        scams = q("SELECT * FROM antiscam_hits ORDER BY created_at DESC LIMIT 10")
        # staff
        staff = q("SELECT staff_id, tickets_closed, tickets_claimed, rating_count, CASE WHEN rating_count>0 THEN CAST(rating_sum AS FLOAT)/rating_count ELSE 0 END as avg FROM staff_stats ORDER BY tickets_closed DESC LIMIT 10")
        # open tickets
        ot = q("SELECT COUNT(*) c FROM tickets_open WHERE closed=0", one=True); open_tickets = ot["c"] if ot else 0
        conv = round((data["total_purchases"]/verified*100) if verified else 0,1)
        html = f"""
<h2>👑 Management Dashboard <span class=badge>v2.0 ULTIMATE</span> <span class=badge style="background:#133d1a;color:#5feca0">LIVE</span></h2>
<div class=grid>
 <div class=card><h3>Heute Umsatz</h3><div class="big gold">{data['today_robux']} <span style="font-size:16px">R$</span></div>{data['today_purchases']} Käufe</div>
 <div class=card><h3>Monat Umsatz</h3><div class="big red">{data['month_robux']} R$</div>{data['month_purchases']} Käufe</div>
 <div class=card><h3>Gesamt</h3><div class=big>{data['total_robux']} R$</div>{data['total_purchases']} Käufe</div>
 <div class=card><h3>User</h3><div class="big blue">{users}</div>{verified} verifiziert</div>
 <div class=card><h3>Void-Coins</h3><div class="big gold">🪙 {coins_total}</div>im Umlauf</div>
 <div class=card><h3>Conversion</h3><div class="big green">{conv}%</div>verified → Kauf</div>
 <div class=card><h3>Offene Tickets</h3><div class="big" style="color:#f39c12">{open_tickets}</div>live</div>
 <div class=card><h3>AntiScam</h3><div class="big green">🛡️ aktiv</div>24/7 Schutz</div>
</div>
<div class=grid style="margin-top:16px">
 <div class=card><h3>👑 Owner-Zentrale</h3><div style="display:grid;gap:10px"><a class=btn href="/staff">Supporter-Leaderboard</a><a class=btn href="/tickets">Ticket-Control-Center</a><a class=btn href="/logs">LogSystem 2.0</a><a class=btn href="/coins">Void-Coins</a></div></div>
 <div class=card><h3>🧩 Aktivierte Features</h3><p>✅ Auto-Delivery<br>✅ Bulletproof Bio-Code-Verify<br>✅ AntiScam / Phishing-Schild<br>✅ Live-Käufe Ticker<br>✅ Invite-Rewards & Void-Coins<br>✅ Staff-Tracking & Ratings</p></div>
</div>
<div class=two style="margin-top:16px">
 <div class=card><h3>📈 Top Produkte</h3><table><tr><th>Produkt</th><th>Verkäufe</th><th>Umsatz</th></tr>"""
        for p,c,r in data["top_products"]:
            html += f"<tr><td>{p}</td><td>{c}</td><td class=gold>{r} R$</td></tr>"
        html += "</table></div><div class=card><h3>🪙 Coin Leaderboard</h3><table><tr><th>#</th><th>User</th><th>Coins</th></tr>"
        for i,row in enumerate(coin_lb,1):
            html += f"<tr><td>{i}</td><td>&lt;@{row['discord_id']}&gt;</td><td class=gold>{row['coins']}</td></tr>"
        html += "</table></div></div>"
        # staff leaderboard
        html += "<div class=card style='margin-top:16px'><h3>👑 Staff Leaderboard – Mitarbeiter des Monats</h3><table><tr><th>#</th><th>Staff</th><th>Closed</th><th>Claimed</th><th>⭐</th></tr>"
        for i,s in enumerate(staff,1):
            html += f"<tr><td>{i}</td><td>&lt;@{s['staff_id']}&gt;</td><td>{s['tickets_closed']}</td><td>{s['tickets_claimed']}</td><td>{round(s['avg'],1) if s['avg'] else '–'}</td></tr>"
        if not staff:
            html += "<tr><td colspan=5 style=color:#666>Noch keine Staff-Daten – werden beim Ticket-Close automatisch getrackt.</td></tr>"
        html += "</table></div>"
        # recent purchases
        html += "<div class=card style='margin-top:16px'><h3>🛍️ Live Käufe – FOMO Ticker</h3><table><tr><th>Zeit</th><th>Käufer</th><th>Produkt</th><th>R$</th></tr>"
        for r in recent:
            rn = f" <small>({r['roblox_name']})</small>" if r["roblox_name"] else ""
            html += f"<tr><td>{r['created_at']}</td><td>&lt;@{r['discord_id']}&gt;{rn}</td><td>{r['product_key']}</td><td class=gold>{r['robux_price']}</td></tr>"
        html += "</table></div>"
        # antiscam
        html += "<div class=card style='margin-top:16px'><h3>🚨 AntiScam – letzte Hits</h3><table><tr><th>Zeit</th><th>User</th><th>URL</th><th>Grund</th></tr>"
        for s in scams:
            html += f"<tr><td>{s['created_at']}</td><td>&lt;@{s['discord_id']}&gt;</td><td style='max-width:340px;overflow:hidden;text-overflow:ellipsis'>{s['url']}</td><td><span class=badge>{s['reason']}</span></td></tr>"
        if not scams: html += "<tr><td colspan=4 style=color:#666>Keine Scam-Versuche – Schild hält! 🛡️</td></tr>"
        html += "</table></div>"
        return page(html)
    @app.route("/products")
    @owner_required
    def products_page():
        import json
        pretty = json.dumps(PRODUCTS, indent=2, ensure_ascii=False)
        html = f"""<h2>🛍️ Produkt-Manager – Auto-Delivery</h2>
<div class=card><p>Produkte sind in v2 ULTIMATE direkt im Code <code>PRODUCTS = {{...}}</code> (Zeile ~95).<br>
Ändere Gamepass IDs & Download-Links dort.</p>
<pre style="background:#0f0f18;padding:16px;border-radius:12px;overflow:auto;max-height:600px;font-size:12px">{pretty}</pre>
<a href="/" class=btn>← Dashboard</a></div>"""
        return page(html)
    @app.route("/coins")
    @owner_required
    def coins_page():
        rows = q("SELECT discord_id, coins, purchases, total_spent_robux, roblox_name FROM users ORDER BY coins DESC LIMIT 120")
        ledger = q("SELECT * FROM coins_ledger ORDER BY created_at DESC LIMIT 200")
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
            rows = q("SELECT * FROM logs WHERE log_type=? ORDER BY created_at DESC LIMIT 400", (t,))
        else:
            rows = q("SELECT * FROM logs ORDER BY created_at DESC LIMIT 400")
        types = [r["log_type"] for r in q("SELECT DISTINCT log_type FROM logs")]
        filt = " ".join([f"<a class=badge href=/logs?type={x}>{x}</a>" for x in types]) + " <a class=badge href=/logs>alle</a>"
        html = f"<h2>📜 LogSystem 2.0 – Kommandozentrale</h2><div class=card style='margin-bottom:12px'>{filt}<br><br><small>{len(LOG_CHANNEL_DEFS)} Kanäle: join · leave · voice · message · invite · shop · verify · antiscam · ticket · coins · mod · system · ticker · bot · owner</small></div>"
        html += "<div class=card><table><tr><th>Zeit</th><th>Typ</th><th>User</th><th>Channel</th><th>Content</th></tr>"
        for r in rows:
            uid = f"&lt;@{r['discord_id']}&gt;" if r["discord_id"] else ""
            ch = f"#{r['channel_id']}" if r["channel_id"] else ""
            cont = (r["content"] or "")[:160]
            html += f"<tr><td>{r['created_at']}</td><td><span class=badge>{r['log_type']}</span></td><td>{uid}</td><td>{ch}</td><td>{cont}</td></tr>"
        html += "</table></div>"
        return page(html)
    @app.route("/tickets")
    @owner_required
    def tickets_page():
        rows = q("""
            SELECT t.channel_id, t.user_id, t.type, t.created_at, t.closed,
                   m.claimed_by, m.claimed_at, m.first_staff_response_at, m.closer_id, m.closed_at, m.survey_product, m.survey_stars
            FROM tickets_open t
            LEFT JOIN ticket_metrics m ON m.channel_id=t.channel_id
            ORDER BY t.closed ASC, t.created_at DESC
            LIMIT 200
        """)
        html = "<h2>🎫 Ticket Control Center</h2><div class=card><table><tr><th>Status</th><th>User</th><th>Typ</th><th>Claimed By</th><th>First Response</th><th>Produkt</th><th>⭐</th><th>Erstellt</th></tr>"
        for r in rows:
            status = "🟢 Offen" if not r["closed"] else "⚫ Geschlossen"
            claimed = f"&lt;@{r['claimed_by']}&gt;" if r["claimed_by"] else "–"
            first_response = r["first_staff_response_at"] or "–"
            product = r["survey_product"] or "–"
            stars = r["survey_stars"] or "–"
            html += f"<tr><td>{status}</td><td>&lt;@{r['user_id']}&gt;</td><td>{r['type']}</td><td>{claimed}</td><td>{first_response}</td><td>{product}</td><td>{stars}</td><td>{r['created_at']}</td></tr>"
        if not rows:
            html += "<tr><td colspan=8 style=color:#666>Noch keine Ticket-Daten vorhanden.</td></tr>"
        html += "</table></div>"
        return page(html)
    @app.route("/staff")
    @owner_required
    def staff_page():
        staff = q("SELECT staff_id, tickets_claimed, tickets_closed, avg_response_sec, rating_sum, rating_count, CASE WHEN rating_count>0 THEN CAST(rating_sum AS FLOAT)/rating_count ELSE 0 END as avg FROM staff_stats ORDER BY tickets_closed DESC, avg DESC")
        html = "<h2>👑 Supporter-Leaderboard – Mitarbeiter des Monats</h2><div class=card>"
        html += "<table><tr><th>#</th><th>Staff</th><th>Tickets Closed</th><th>Claimed</th><th>Ø Antwortzeit</th><th>Bewertung ⭐</th><th>Votes</th></tr>"
        for i,s in enumerate(staff,1):
            medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"#{i}"
            resp = f"{int(s['avg_response_sec'])}s" if s['avg_response_sec'] else "–"
            html += f"<tr><td>{medal}</td><td>&lt;@{s['staff_id']}&gt;</td><td><b>{s['tickets_closed']}</b></td><td>{s['tickets_claimed']}</td><td>{resp}</td><td>{round(s['avg'],2) if s['avg'] else '–'} ⭐</td><td>{s['rating_count']}</td></tr>"
        if not staff:
            html += "<tr><td colspan=7 style=color:#666>Noch keine Daten. Staff-Stats werden beim Ticket-Close automatisch erfasst.</td></tr>"
        html += "</table><br><p><b>Mitarbeiter des Monats</b> wird automatisch an Platz #1 vergeben – perfekt für Monats-Belohnung!</p></div>"
        return page(html)
    @app.route("/api/revenue")
    @owner_required
    def api_revenue():
        import asyncio
        return jsonify(asyncio.run(get_revenue_summary()))
    print(f"[*] Void_Shop v2 Dashboard → http://{DASHBOARD_HOST}:{DASHBOARD_PORT}  Login: {DASHBOARD_LOGIN_CODE}")
    app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT, debug=False, use_reloader=False)

# =====================================================================
#  🚀 START
# =====================================================================
async def main():
    await init_db()
    # persistente Views registrieren – wichtig für Buttons nach Restart
    try:
        bot.add_view(TicketPanelView())
        bot.add_view(TicketControlView())
        bot.add_view(OneClickVerifyView())
    except Exception as e:
        print(f"[views] {e}")
    if not TOKEN or TOKEN.startswith("PUT_"):
        print("""
╔══════════════════════════════════════════════════════════════╗
║  ❌ DISCORD_TOKEN fehlt!                                   ║
║                                                              ║
║  Bearbeite oben im File:                                    ║
║    TOKEN = "MTxxxxxxxxxxxxxxxx..."                           ║
║  oder .env:                                                 ║
║    DISCORD_TOKEN=xxx                                        ║
║    GUILD_ID=123456789                                       ║
║    OWNER_ID=123456789                                       ║
║                                                              ║
║  Dann:                                                      ║
║    !start  → erstellt Rollen + ~30 Kanäle + erweitertes LogSystem ║
║                                                              ║
║  pip install discord.py aiohttp aiosqlite Flask python-dotenv║
╚══════════════════════════════════════════════════════════════╝
""")
        await asyncio.sleep(2)
        sys.exit(0)
    # Stats Loop starten
    if not stats_loop.is_running():
        try: stats_loop.start()
        except: pass
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    if DASHBOARD_ENABLED and HAS_FLASK:
        t = threading.Thread(target=run_dashboard, daemon=True, name="VoidShopDash")
        t.start()
        time.sleep(1.0)
    else:
        print("[Dashboard] OFF – pip install Flask um zu aktivieren")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[+] Shutdown by user.")
        sys.exit(0)
    except Exception as e:
        import traceback
        print("\n[FATAL] Bot crashed:")
        traceback.print_exc()
        print("\n[!] NOT restarting automatically – fix the error above.")
        print("    pip install discord.py aiohttp aiosqlite Flask python-dotenv")
        sys.exit(1)
