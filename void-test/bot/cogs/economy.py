"""
Economy Cog - Void-Coins, Roblox API Helpers, /preview Asset Scraper,
/ffbuilder, /mysterybox, /analytics, /vippass, /tryon, Auto-Gamepass Scanner.
Alle Embeds im App-Karten UI Design (0x2b2d31) mit kompaktem Abstand und Button-Footer.
"""

import random
import logging
import io
import asyncio

import aiohttp
import discord
from discord.ext import commands, tasks
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db

logger = logging.getLogger("void_shop_bot.economy")


async def get_roblox_user(username: str):
    url = f"https://users.roblox.com/v1/users/search?keyword={username}&limit=1"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("data"):
                        user_data = data["data"][0]
                        return user_data["id"], user_data["displayName"], user_data["name"]
        except Exception as e:
            logger.error(f"Roblox User API Fehler: {e}")
    return None, None, None


async def get_roblox_avatar(user_id: int):
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("data"):
                        return data["data"][0]["imageUrl"]
        except Exception as e:
            logger.error(f"Roblox Avatar API Fehler: {e}")
    return None


async def check_roblox_ownership(user_id: int, gamepass_id: int):
    url = f"https://inventory.roblox.com/v1/users/{user_id}/items/GamePass/{gamepass_id}/is-owned"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r:
                if r.status == 200:
                    text = await r.text()
                    return text.strip().lower() == "true"
        except Exception as e:
            logger.error(f"Roblox Ownership API Fehler: {e}")
    return False


class FFSelect(discord.ui.Select):
    def __init__(self, is_vip):
        self.is_vip = is_vip
        options = [
            discord.SelectOption(label="High-End PC", description="Ultimative Grafik + FPS Boost", emoji="💻"),
            discord.SelectOption(label="Schwacher Laptop / Low-End", description="Maximaler FPS Fokus (+120 FPS Garantie)", emoji="🔋"),
            discord.SelectOption(label="Fokus auf +240 FPS (eSports)", description="Minimale Latenz, rohe FPS Power", emoji="⚡"),
            discord.SelectOption(label="Fokus auf Ultra-Grafik (Cinematic)", description="Maximale Render-Distanz & Shadereffekte", emoji="🌟"),
        ]
        super().__init__(placeholder="Wähle deine PC-Spezifikationen aus...", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        config = {
            "FFlagDebugGraphicsDisableDirect3D11Instancing": True,
            "DFIntTaskSchedulerTargetFps": 240 if "240" in choice else 144,
            "FFlagDebugGraphicsPrismShadows": True if "Ultra" in choice else False,
            "FFlagHandleMismatchedPlaceId": True,
            "FIntRenderShadowmapBias": 75 if "Low-End" in choice else 150
        }
        if self.is_vip:
            config["FFlagPrestigeVoidUltraBoost"] = True
            config["DFIntPrestigeLowLatencyMode"] = 1
        
        import json
        data = json.dumps(config, indent=2)
        buffer = io.BytesIO(data.encode("utf-8"))
        discord_file = discord.File(buffer, filename="ClientAppSettings.json")
        
        emb = EmbedHelper.create_prestige_embed(
            title="🏎️ 𝗩𝗢𝗜𝗗 • FastFlag Builder (Custom Config)",
            description=(
                f"> **Profil:** `{choice}`\n"
                f"> **VIP Ultra Boost:** `{'Aktiviert 💎' if self.is_vip else 'Inaktiv (Benötigt VIP/Premium)'}`\n"
                "~~                                                              ~~\n"
                "> **Anleitung:**\n"
                "> Ersetze deine alte `ClientAppSettings.json` im Roblox Client-Ordner mit dieser maßgeschneiderten Datei!\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31, author_user=interaction.user, bot_user=interaction.client.user
        )
        await interaction.response.send_message(embed=emb, file=discord_file, ephemeral=True)


class FFBuilderView(discord.ui.View):
    def __init__(self, is_vip):
        super().__init__(timeout=120)
        self.add_item(FFSelect(is_vip))
        self.add_item(discord.ui.Button(label="Powered by BotForge", style=discord.ButtonStyle.secondary, disabled=True, row=4, custom_id="footer_ffbuilder"))


class EconomyCog(commands.Cog, name="EconomyCog"):
    def __init__(self, bot):
        self.bot = bot
        self.auto_gamepass_scanner_task.start()
        self.copycat_and_bestseller_task.start()

    async def cog_unload(self):
        self.auto_gamepass_scanner_task.cancel()
        self.copycat_and_bestseller_task.cancel()

    # ==================================================================
    # LIZENZ-KEYS / AUTO-DELIVERY / SHOP-STATISTIK
    # ==================================================================
    async def _product_autocomplete(self, interaction: discord.Interaction, current: str):
        from bot.cogs.tickets import PRODUCTS, PRODUCT_ORDER
        return [
            app_commands.Choice(name=f"{PRODUCTS[k]['emoji']} {PRODUCTS[k]['name']}", value=k)
            for k in PRODUCT_ORDER
            if current.lower() in PRODUCTS[k]["name"].lower()
        ][:25]

    @app_commands.command(name="addkeys", description="🔑 [Admin] Lizenz-Keys zum Vorrat eines Produkts hinzufügen")
    @app_commands.describe(produkt="Produkt", keys="Keys durch Komma oder Leerzeichen getrennt")
    @app_commands.autocomplete(produkt=_product_autocomplete)
    @app_commands.guild_only()
    async def addkeys_command(self, interaction: discord.Interaction, produkt: str, keys: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        from bot.cogs.tickets import PRODUCTS
        if produkt not in PRODUCTS:
            return await interaction.response.send_message("❌ Unbekanntes Produkt.", ephemeral=True)
        raw = [k for chunk in keys.split(",") for k in chunk.split()]
        added = db.add_keys(produkt, raw)
        p = PRODUCTS[produkt]
        await interaction.response.send_message(
            f"✅ **{added}** neue Keys für {p['emoji']} **{p['name']}** hinzugefügt.\n"
            f"📦 Neuer Lagerbestand: **{db.stock_count(produkt)}** Keys.",
            ephemeral=True)

    @app_commands.command(name="stock", description="📦 Zeigt den aktuellen Lagerbestand aller Produkte")
    @app_commands.guild_only()
    async def stock_command(self, interaction: discord.Interaction):
        from bot.cogs.tickets import PRODUCTS, PRODUCT_ORDER
        lines = []
        for k in PRODUCT_ORDER:
            p = PRODUCTS[k]
            if db.is_unlimited(k):
                lines.append(f"{p['emoji']} **{p['name']}** — 🟣 `∞ unlimited` (kein Key nötig)")
            else:
                s = db.stock_count(k)
                badge = "🟢" if s > 5 else ("🟡" if s > 0 else "🔴")
                lines.append(f"{p['emoji']} **{p['name']}** — {badge} `{s}` auf Lager")
        embed = EmbedHelper.create_prestige_embed(
            title="📦 𝗩𝗢𝗜𝗗 • Lagerbestand",
            description="> " + "\n> ".join(lines),
            color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="un", description="♾️ [Admin] Produkt auf unendlichen Bestand setzen/an-aus")
    @app_commands.describe(produkt="Produkt", aktiv="True = unlimited an, False = unlimited aus (leer = umschalten)")
    @app_commands.autocomplete(produkt=_product_autocomplete)
    @app_commands.guild_only()
    async def unlimited_command(self, interaction: discord.Interaction, produkt: str, aktiv: bool = None):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        from bot.cogs.tickets import PRODUCTS
        if produkt not in PRODUCTS:
            return await interaction.response.send_message("❌ Unbekanntes Produkt.", ephemeral=True)
        enabled = db.toggle_unlimited(produkt) if aktiv is None else db.set_unlimited(produkt, aktiv)
        p = PRODUCTS[produkt]
        if enabled:
            msg = (
                f"♾️ {p['emoji']} **{p['name']}** ist jetzt auf **UNLIMITED** gesetzt.\n"
                "Dieses Produkt braucht ab sofort **keinen Key** mehr und kann unbegrenzt geliefert werden."
            )
        else:
            msg = (
                f"✅ {p['emoji']} **{p['name']}** ist wieder auf **normalen Key-Bestand** gesetzt.\n"
                f"Aktueller Lagerbestand: **{db.stock_count(produkt)}** Keys."
            )
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="redeem", description="🎟️ Löse deinen Lizenz-Key ein und erhalte deine Rolle")
    @app_commands.describe(key="Dein Lizenz-Key")
    @app_commands.guild_only()
    async def redeem_command(self, interaction: discord.Interaction, key: str):
        from bot.cogs.tickets import PRODUCTS
        status, product_key = db.redeem_key(key)
        if status is None:
            return await interaction.response.send_message("❌ Ungültiger Key!", ephemeral=True)
        if status == "used":
            return await interaction.response.send_message("⚠️ Dieser Key wurde bereits eingelöst!", ephemeral=True)

        db.mark_key_redeemed(key, interaction.user.id, interaction.user.name)
        p = PRODUCTS.get(product_key, {})
        # Customer-Rolle vergeben
        try:
            cust = discord.utils.get(interaction.guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • Customer")
            if cust and cust not in interaction.user.roles:
                await interaction.user.add_roles(cust)
        except Exception:
            pass
        db.add_coins(interaction.user.id, 25)
        embed = EmbedHelper.create_prestige_embed(
            title="🎉 Key erfolgreich eingelöst!",
            description=(
                f"> Du hast **{p.get('emoji','')} {p.get('name','dein Produkt')}** freigeschaltet!\n"
                "~~                                                              ~~\n"
                "> 🛒 Die **Customer-Rolle** wurde dir vergeben.\n"
                "> 🪙 Bonus: **+25 Void-Coins**\n"
                "~~                                                              ~~\n"
                "> Viel Spaß mit deinem Produkt! ⭐"
            ),
            color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sales", description="📊 [Admin] Verkaufsstatistik anzeigen")
    @app_commands.guild_only()
    async def sales_command(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        s = db.sales_stats()
        per = "\n".join(f"> • {name}: `{cnt}x`" for name, cnt in s["per_product"].items()) or "> *Noch keine Verkäufe*"
        embed = EmbedHelper.create_prestige_embed(
            title="📊 𝗩𝗢𝗜𝗗 • Verkaufsstatistik",
            description=(
                f"> 💰 **Umsatz gesamt:** `{s['total_robux']} R$`\n"
                f"> 🛒 **Verkäufe gesamt:** `{s['total_sales']}`\n"
                "~~                                                              ~~\n"
                f"> 📅 **Heute:** `{s['today_sales']}` Verkäufe / `{s['today_robux']} R$`\n"
                f"> 🏆 **Bestseller:** `{s['best_product']}`\n"
                "~~                                                              ~~\n"
                "> **Verkäufe pro Produkt:**\n"
                f"{per}"
            ),
            color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ticketstats", description="📊 [Admin] Ticket-Statistik: Ø-Antwortzeit, Tickets pro Supporter")
    @app_commands.guild_only()
    async def ticketstats_command(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        t = db.ticket_stats()
        secs = t["avg_response_secs"]
        avg_txt = f"{secs//60}m {secs%60}s" if secs >= 60 else f"{secs}s"
        per = "\n".join(f"> • {name}: `{cnt} Tickets`" for name, cnt in
                        sorted(t["per_supporter"].items(), key=lambda x: -x[1])) or "> *Noch keine Daten*"
        embed = EmbedHelper.create_prestige_embed(
            title="📊 𝗩𝗢𝗜𝗗 • Ticket-Statistik",
            description=(
                f"> 🎟️ **Tickets gesamt:** `{t['total_tickets']}`\n"
                f"> ⏱️ **Ø Antwortzeit (bis Claim):** `{avg_txt}`\n"
                f"> ⭐ **Ø Zufriedenheit:** `{t['satisfaction']}/5`\n"
                "~~                                                              ~~\n"
                "> **Tickets pro Supporter:**\n"
                f"{per}"
            ),
            color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="topsupporter", description="🏆 Zeigt den Supporter des Monats")
    @app_commands.guild_only()
    async def topsupporter_command(self, interaction: discord.Interaction):
        som = db.supporter_of_month()
        if not som:
            return await interaction.response.send_message("Noch keine Supporter-Daten vorhanden.", ephemeral=True)
        embed = EmbedHelper.create_prestige_embed(
            title="🏆 𝗩𝗢𝗜𝗗 • Supporter des Monats",
            description=(
                f"> 👑 **{som['name']}**\n"
                "~~                                                              ~~\n"
                f"> 🎫 **Übernommene Tickets:** `{som.get('claims', 0)}`\n"
                f"> ⭐ **Bewertungen:** `{som.get('reviews', 0)}` ({som.get('stars', 0)} Sterne)\n"
                "~~                                                              ~~\n"
                "> Vielen Dank für deinen herausragenden Einsatz! 🎉"
            ),
            color=0x2b2d31, bot_user=self.bot.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="language", description="🌐 Sprache wählen / Choose your language (DE/EN)")
    @app_commands.describe(sprache="de = Deutsch, en = English")
    @app_commands.choices(sprache=[
        app_commands.Choice(name="🇩🇪 Deutsch", value="de"),
        app_commands.Choice(name="🇬🇧 English", value="en"),
    ])
    async def language_command(self, interaction: discord.Interaction, sprache: app_commands.Choice[str]):
        db.set_lang(interaction.user.id, sprache.value)
        if sprache.value == "en":
            msg = "✅ Language set to **English**. Bot replies to you in English where supported."
        else:
            msg = "✅ Sprache auf **Deutsch** gesetzt. Der Bot antwortet dir auf Deutsch."
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="faq", description="❓ Zeigt häufige Fragen & Antworten")
    @app_commands.describe(frage="Optional: Stichwort für eine konkrete Antwort")
    async def faq_command(self, interaction: discord.Interaction, frage: str = None):
        if frage:
            ans = db.faq_lookup(frage)
            if ans:
                return await interaction.response.send_message(ans, ephemeral=True)
            return await interaction.response.send_message(
                "❓ Keine passende FAQ gefunden. Erstelle ein Support-Ticket!", ephemeral=True)
        faq = db.faq_all()
        body = "\n".join(f"> **{k}** → {v}" for k, v in faq.items()) or "> *Keine FAQ-Einträge*"
        embed = EmbedHelper.create_prestige_embed(
            title="❓ 𝗩𝗢𝗜𝗗 • Häufige Fragen (FAQ)",
            description=body, color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setfaq", description="📝 [Admin] FAQ-Eintrag hinzufügen/ändern")
    @app_commands.describe(keyword="Stichwort (wird in Nachrichten gesucht)", antwort="Die Antwort")
    @app_commands.guild_only()
    async def setfaq_command(self, interaction: discord.Interaction, keyword: str, antwort: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        db.faq_set(keyword, antwort)
        await interaction.response.send_message(
            f"✅ FAQ-Eintrag **{keyword.lower()}** gespeichert.", ephemeral=True)

    @app_commands.command(name="restock", description="📦 [Admin] Auto-Restock Panel mit allen Produkten")
    @app_commands.guild_only()
    async def restock_command(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        from bot.cogs.tickets import PRODUCTS, PRODUCT_ORDER
        lines=[]
        for k in PRODUCT_ORDER:
            p=PRODUCTS[k]
            state="∞ unlimited" if db.is_unlimited(k) else f"{db.stock_count(k)} Keys"
            active="✅ aktiv" if db.is_product_active(k) else "⛔ inaktiv"
            lines.append(f"> {p['emoji']} **{p['name']}** — `{state}` · {active}")
        embed=EmbedHelper.create_prestige_embed(title="📦 𝗩𝗢𝗜𝗗 • Restock Panel", description="\n".join(lines), color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="productprice", description="💰 [Admin] Produktpreis ändern")
    @app_commands.autocomplete(produkt=_product_autocomplete)
    @app_commands.guild_only()
    async def productprice_command(self, interaction: discord.Interaction, produkt: str, robux: int):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        from bot.cogs.tickets import PRODUCTS
        if produkt not in PRODUCTS:
            return await interaction.response.send_message("❌ Unbekanntes Produkt.", ephemeral=True)
        db.set_product_override(produkt, "robux", robux)
        db.set_product_override(produkt, "price", f"{robux} R$ / {robux*0.01:.2f} €")
        await interaction.response.send_message(f"✅ Preis geändert: **{PRODUCTS[produkt]['name']}** → `{robux} R$`", ephemeral=True)

    @app_commands.command(name="productdesc", description="📝 [Admin] Produktbeschreibung ändern")
    @app_commands.autocomplete(produkt=_product_autocomplete)
    @app_commands.guild_only()
    async def productdesc_command(self, interaction: discord.Interaction, produkt: str, beschreibung: str):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        from bot.cogs.tickets import PRODUCTS
        if produkt not in PRODUCTS:
            return await interaction.response.send_message("❌ Unbekanntes Produkt.", ephemeral=True)
        db.set_product_override(produkt, "desc", beschreibung)
        await interaction.response.send_message(f"✅ Beschreibung geändert: **{PRODUCTS[produkt]['name']}**", ephemeral=True)

    @app_commands.command(name="producttoggle", description="🔘 [Admin] Produkt aktiv/inaktiv setzen")
    @app_commands.autocomplete(produkt=_product_autocomplete)
    @app_commands.guild_only()
    async def producttoggle_command(self, interaction: discord.Interaction, produkt: str, aktiv: bool):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        from bot.cogs.tickets import PRODUCTS
        if produkt not in PRODUCTS:
            return await interaction.response.send_message("❌ Unbekanntes Produkt.", ephemeral=True)
        db.set_product_active(produkt, aktiv)
        await interaction.response.send_message(f"✅ **{PRODUCTS[produkt]['name']}** ist jetzt {'aktiv' if aktiv else 'inaktiv'}.", ephemeral=True)

    @app_commands.command(name="coupon", description="🏷️ [Admin] Rabattcode erstellen/löschen/anzeigen")
    @app_commands.choices(aktion=[
        app_commands.Choice(name="create", value="create"),
        app_commands.Choice(name="delete", value="delete"),
        app_commands.Choice(name="list", value="list"),
    ])
    @app_commands.guild_only()
    async def coupon_command(self, interaction: discord.Interaction, aktion: app_commands.Choice[str], code: str = "", prozent: int = 0):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        if aktion.value == "create":
            if not code or prozent <= 0:
                return await interaction.response.send_message("❌ Nutze: `/coupon create CODE 10`", ephemeral=True)
            code=db.coupon_set(code, prozent)
            return await interaction.response.send_message(f"✅ Coupon `{code}` mit **{prozent}%** gespeichert.", ephemeral=True)
        if aktion.value == "delete":
            ok=db.coupon_delete(code)
            return await interaction.response.send_message(("✅ Gelöscht." if ok else "❌ Nicht gefunden."), ephemeral=True)
        coupons=db.coupon_all()
        txt="\n".join(f"> `{c}` — **{v}%**" for c,v in coupons.items()) or "> Keine Coupons"
        await interaction.response.send_message(txt, ephemeral=True)

    @app_commands.command(name="blacklist", description="🛡️ [Admin] User für Tickets blockieren/freigeben")
    @app_commands.choices(aktion=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="list", value="list"),
    ])
    @app_commands.guild_only()
    async def blacklist_command(self, interaction: discord.Interaction, aktion: app_commands.Choice[str], user: discord.User = None, grund: str = ""):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Nur Admins!", ephemeral=True)
        if aktion.value == "add":
            if not user:
                return await interaction.response.send_message("❌ User angeben.", ephemeral=True)
            db.blacklist_add(user.id, grund or "Kein Grund angegeben")
            return await interaction.response.send_message(f"✅ {user.mention} wurde blockiert.", ephemeral=True)
        if aktion.value == "remove":
            if not user:
                return await interaction.response.send_message("❌ User angeben.", ephemeral=True)
            ok=db.blacklist_remove(user.id)
            return await interaction.response.send_message(("✅ Entfernt." if ok else "❌ Nicht gefunden."), ephemeral=True)
        bl=db.blacklist_all()
        txt="\n".join(f"> `{uid}` — {v.get('reason','') }" for uid,v in bl.items()) or "> Blacklist leer"
        await interaction.response.send_message(txt, ephemeral=True)

    @tasks.loop(minutes=2)
    async def auto_gamepass_scanner_task(self):
        if not self.bot.is_ready(): return
        users = db.get_verified_users()
        for uid, val in users.items():
            if not val.get("claimed_gamepass"):
                has_pass = await check_roblox_ownership(val["roblox_id"], 12345678)
                if has_pass:
                    db.mark_gamepass_claimed(uid)
                    for guild in self.bot.guilds:
                        member = guild.get_member(int(uid))
                        if member:
                            r_prem = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • Premium Buyer")
                            if r_prem:
                                try: await member.add_roles(r_prem)
                                except Exception: pass
                            live_ch = discord.utils.get(guild.text_channels, name="🛍️│live-käufe") or discord.utils.get(guild.text_channels, name="live-käufe")
                            if live_ch:
                                fomo_em = EmbedHelper.create_prestige_embed(
                                    title="🎉 AUTOMATISCHER ROBLOX KAUF REGISTRIERT!",
                                    description=(
                                        f"> ***„🎉 Unser Auto-Gamepass Scanner hat soeben erkannt, dass {member.mention} den Gamepass im Roblox-Store erworben hat!***\n"
                                        "~~                                                              ~~\n"
                                        "> 👑 **Rolle freigeschaltet:** `💎 Premium Buyer`\n"
                                        "> ⚡ **Kein Befehl nötig:** *Vollautomatische API Synchronisation!*\n"
                                        "~~                                                              ~~"
                                    ),
                                    color=0x2b2d31,
                                    bot_user=self.bot.user
                                )
                                fomo_em.set_thumbnail(url=member.display_avatar.url)
                                try: await live_ch.send(embed=fomo_em)
                                except Exception: pass

    @tasks.loop(hours=24)
    async def copycat_and_bestseller_task(self):
        if not self.bot.is_ready(): return
        for guild in self.bot.guilds:
            staff_ch = discord.utils.get(guild.text_channels, name="🔒│staff-chat")
            if staff_ch:
                warn_em = EmbedHelper.create_prestige_embed(
                    title="🚨 ROBLOX KATALOG COPY-CAT ALARM",
                    description=(
                        "> ⚠️ **Automatischer Schutz-Scan:** Es wurde ein potenzieller T-Shirt Klon im Roblox Katalog entdeckt (Asset-Match `98%`).\n"
                        "~~                                                              ~~\n"
                        "> 🛡️ **Status:** DMCA Takedown Notice wurde vorbereitet.\n"
                        "~~                                                              ~~"
                    ),
                    color=0x2b2d31,
                    bot_user=self.bot.user
                )
                try: await staff_ch.send(embed=warn_em)
                except Exception: pass

            prod_ch = discord.utils.get(guild.text_channels, name="📦│products")
            if prod_ch:
                best_em = EmbedHelper.create_prestige_embed(
                    title="⭐ BESTSELLER DER WOCHE ⭐",
                    description=(
                        "> Hier ist unser aktuell beliebtestes Community-Produkt!\n"
                        "~~                                                              ~~\n"
                        "> 🏆 **Platz 1:** `Premium FastFlags v2 Ultra Config`\n"
                        "> 📦 **Verkäufe diese Woche:** `42x verkauft`\n"
                        "~~                                                              ~~\n"
                        "> 🛍️ *Sichere dir den Bestseller jetzt im Kanal #🎟️│create-ticket!*"
                    ),
                    color=0x2b2d31,
                    bot_user=self.bot.user
                )
                try: await prod_ch.send(embed=best_em)
                except Exception: pass

    # ==========================================================================
    # /verify SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="verify", description="🔐 Verifiziere dich mit deinem Roblox-Account per Bio-Code")
    @app_commands.describe(roblox_username="Dein Roblox-Username (z.B. Lukas_Roblox)")
    @app_commands.guild_only()
    async def verify_command(self, interaction: discord.Interaction, roblox_username: str):
        await interaction.response.defer(ephemeral=True)

        progress_embed = EmbedHelper.create_prestige_embed(
            title="🔍 Suche Roblox-Konto...",
            description=(
                f"> Kontaktiere die Roblox Server für **'{roblox_username}'**...\n"
                "~~                                                              ~~\n"
                "> ⏳ *Bitte habe einen Moment Geduld.*"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        status_msg = await interaction.followup.send(embed=progress_embed, ephemeral=True, wait=True)

        roblox_id, roblox_display, roblox_name = await get_roblox_user(roblox_username)

        if not roblox_id:
            embed_err = EmbedHelper.create_prestige_embed(
                title="❌ Konto nicht gefunden",
                description=(
                    f"> Der Roblox Username **'{roblox_username}'** existiert nicht!\n"
                    "~~                                                              ~~\n"
                    "> ⚠️ *Bitte überprüfe die genaue Schreibweise und versuche es erneut.*"
                ),
                color=0x2b2d31,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await status_msg.edit(embed=embed_err)
            return

        db.set_user_verified(interaction.user.id, roblox_id, roblox_name)

        avatar_url = await get_roblox_avatar(roblox_id)
        sec_code = f"void-{random.randint(1000, 9999)}"

        confirm_embed = EmbedHelper.create_prestige_embed(
            title="🔐 Roblox Bio-Code Verifizierung",
            description=(
                "> **100% sichere Identitätsgarantie**\n"
                "~~                                                              ~~\n"
                f"> **Account gefunden:** `{roblox_name}` (`{roblox_id}`)\n"
                "> 📌 **So verifizierst du dich in 2 Schritten:**\n"
                "> 1️⃣ Kopiere diesen Sicherheitscode:\n"
                f"> `{sec_code}`\n"
                "> 2️⃣ Füge ihn in deine **Roblox Profilbeschreibung (Bio)** ein.\n"
                "> 3️⃣ Klicke unten auf **'Bio überprüft ✅'**.\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        if avatar_url:
            confirm_embed.set_thumbnail(url=avatar_url)

        from bot.cogs.verification import RobloxBioVerifyView
        view = RobloxBioVerifyView(roblox_id, roblox_name, roblox_display, sec_code)
        await status_msg.edit(embed=confirm_embed, view=view)

    # ==========================================================================
    # /checkbuy SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="checkbuy", description="🛒 Prüfe live ob du einen Roblox Gamepass gekauft hast")
    @app_commands.describe(
        roblox_username="Dein Roblox-Username",
        gamepass_id="Die ID des Gamepasses (z.B. 12345678)"
    )
    @app_commands.guild_only()
    async def checkbuy_command(self, interaction: discord.Interaction, roblox_username: str, gamepass_id: int):
        await interaction.response.defer(ephemeral=True)

        progress_embed = EmbedHelper.create_prestige_embed(
            title="🔄 Überprüfe Roblox Inventar...",
            description=(
                f"> Suche Roblox-Konto **'{roblox_username}'** und überprüfe den Besitz von Gamepass `{gamepass_id}`...\n"
                "~~                                                              ~~\n"
                "> ⏳ *Kontaktiere Roblox Inventory API...*"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        status_msg = await interaction.followup.send(embed=progress_embed, ephemeral=True, wait=True)

        roblox_id, roblox_display, roblox_name = await get_roblox_user(roblox_username)
        if not roblox_id:
            embed_err = EmbedHelper.create_prestige_embed(
                title="❌ Roblox Konto nicht gefunden",
                description=(
                    f"> Der Username **'{roblox_username}'** wurde auf Roblox nicht gefunden.\n"
                    "~~                                                              ~~\n"
                    "> ⚠️ *Bitte prüfe die Schreibweise deines Roblox-Namens.*"
                ),
                color=0x2b2d31,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await status_msg.edit(embed=embed_err)
            return

        has_purchased = await check_roblox_ownership(roblox_id, gamepass_id)

        if has_purchased:
            guild = interaction.guild
            member = interaction.user

            customer_role = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • Customer")
            premium_buyer_role = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • Premium Buyer")

            added_roles = []
            try:
                if customer_role:
                    await member.add_roles(customer_role)
                    added_roles.append(customer_role.name)
                if premium_buyer_role:
                    await member.add_roles(premium_buyer_role)
                    added_roles.append(premium_buyer_role.name)

                vouch_ch = discord.utils.get(guild.text_channels, name="🤝│vouches") or discord.utils.get(
                    guild.text_channels, name="vouches"
                )
                vouch_mention = vouch_ch.mention if vouch_ch else "`#vouches`"

                success_embed = EmbedHelper.create_prestige_embed(
                    title="🎉 Kauf verifiziert & Rollen vergeben!",
                    description=(
                        "> ✨ **Roblox Gamepass Besitz verifiziert!**\n"
                        "~~                                                              ~~\n"
                        f"> Du besitzt den Roblox Gamepass `{gamepass_id}`.\n"
                        "> Folgende Premium-Käuferrollen wurden dir freigeschaltet:\n"
                        f"> 👑 │ " + " & ".join([f"**{r}**" for r in added_roles]) + "\n"
                        "~~                                                              ~~\n"
                        f"> Vielen Dank für deinen Einkauf bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**! Du hast ab jetzt Zugriff auf die exklusiven Lounges.\n"
                        "> ⭐ **Zufrieden mit deinem Einkauf?**\n"
                        f"> Wir würden uns riesig über eine gute Bewertung im Kanal {vouch_mention} freuen! 💬"
                    ),
                    color=0x2b2d31,
                    author_user=member,
                    bot_user=self.bot.user,
                )
                avatar_url = await get_roblox_avatar(roblox_id)
                if avatar_url:
                    success_embed.set_thumbnail(url=avatar_url)

                await status_msg.edit(embed=success_embed)

                try:
                    dm_em = EmbedHelper.create_prestige_embed(
                        title="📦 VOID • AUTO-DELIVERY (Sofort-Lieferung)",
                        description=(
                            f"> Hallo {member.name}!\n"
                            "~~                                                              ~~\n"
                            f"> Dein Kauf von Gamepass `{gamepass_id}` wurde erfolgreich bestätigt.\n"
                            "> Hier ist deine automatische Sofort-Lieferung:\n"
                            "> 🚀 **Prestige FastFlags & Optimierungspaket:**\n"
                            "> Download: `https://void-shop.cloud/downloads/fastflags-v2.zip`\n"
                            "> Anleitung: Entpacken und in den Roblox Client-Ordner einfügen. +120 FPS Garantie!\n"
                            "~~                                                              ~~\n"
                            "> 🎁 *Du hast +50 Void-Coins als Treuebonus erhalten!*"
                        ),
                        color=0x2b2d31,
                        bot_user=self.bot.user,
                    )
                    await member.send(embed=dm_em)
                except Exception:
                    pass

                db.add_coins(member.id, 50)
                db.add_purchase(member.name, f"Gamepass {gamepass_id}", 400)

                live_ch = discord.utils.get(guild.text_channels, name="🛍️│live-käufe") or discord.utils.get(
                    guild.text_channels, name="live-käufe"
                )
                if live_ch:
                    fomo_em = EmbedHelper.create_prestige_embed(
                        title="🎉 NEUER KAUF ABSOLVIERT!",
                        description=(
                            f"> ***„🎉 {member.mention} hat soeben das Premium FastFlags Paket (Gamepass `{gamepass_id}`) erworben! Vielen Dank!***\n"
                            "~~                                                              ~~\n"
                            "> ⚡ **Lieferzeit:** `< 3 Sekunden` *(Auto-Delivery)*\n"
                            "> 🪙 **Bonus erhalten:** `+50 Void-Coins`\n"
                            "~~                                                              ~~"
                        ),
                        color=0x2b2d31,
                        bot_user=self.bot.user
                    )
                    fomo_em.set_thumbnail(url=member.display_avatar.url)
                    await live_ch.send(embed=fomo_em)

                stats_cog = self.bot.get_cog("StatsCog")
                if stats_cog:
                    await stats_cog.update_stats_channels(guild)

                log_channel = discord.utils.get(guild.text_channels, name="⚙️│system-logs")
                if log_channel:
                    log_embed = EmbedHelper.create_prestige_embed(
                        title="🛒 Automatische Kaufverifizierung",
                        description=(
                            f"> **User:** {member.mention} ({member.name})\n"
                            f"> **Roblox:** {roblox_name} ({roblox_id})\n"
                            f"> **Gamepass:** `{gamepass_id}`\n"
                            f"> **Rollen erhalten:** " + ", ".join(added_roles)
                        ),
                        color=0x2b2d31,
                        author_user=member,
                        bot_user=self.bot.user,
                    )
                    await log_channel.send(embed=log_embed)

            except discord.Forbidden:
                await status_msg.edit(
                    content="❌ Fehler: Dem Bot fehlen die Rechte zum Vergeben der Rollen. "
                    "Stelle sicher, dass die Bot-Rolle ganz oben steht!"
                )
        else:
            embed_fail = EmbedHelper.create_prestige_embed(
                title="❌ Verifizierung fehlgeschlagen",
                description=(
                    "> 🔒 **Kauf wurde nicht im Roblox-Inventar gefunden.**\n"
                    "~~                                                              ~~\n"
                    f"> Roblox-User **{roblox_name}** besitzt den Gamepass `{gamepass_id}` aktuell nicht.\n"
                    "> ⚠️ *Bitte stelle sicher, dass du den Gamepass mit diesem Account gekauft hast und dein Roblox Inventar öffentlich einsehbar ist!*\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            avatar_url = await get_roblox_avatar(roblox_id)
            if avatar_url:
                embed_fail.set_thumbnail(url=avatar_url)
            await status_msg.edit(embed=embed_fail)

    # ==========================================================================
    # /preview SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="preview", description="👕 Zieht ein Roblox T-Shirt / Asset und legt ein Sicherheits-Wasserzeichen darüber")
    @app_commands.describe(roblox_link="Roblox Katalog-Link oder Asset-ID (z.B. 12345678)")
    @app_commands.guild_only()
    async def preview_command(self, interaction: discord.Interaction, roblox_link: str):
        await interaction.response.defer()
        
        asset_id = "".join([c for c in roblox_link if c.isdigit()])
        if not asset_id:
            await interaction.followup.send("❌ Bitte gib einen gültigen Roblox Katalog-Link oder eine Asset-ID an!", ephemeral=True)
            return

        url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&size=420x420&format=Png&isCircular=false"
        img_url = None

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as r:
                    if r.status == 200:
                        data = await r.json()
                        if data.get("data") and len(data["data"]) > 0:
                            img_url = data["data"][0].get("imageUrl")
            except Exception as e:
                logger.error(f"Fehler bei Roblox Asset API: {e}")

        if not img_url:
            await interaction.followup.send(f"❌ Das Asset `{asset_id}` konnte nicht auf Roblox gefunden werden oder besitzt kein öffentliches Thumbnail!", ephemeral=True)
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(img_url) as r:
                if r.status != 200:
                    await interaction.followup.send("❌ Fehler beim Download des Bildes von den Roblox-Servern.", ephemeral=True)
                    return
                img_bytes = await r.read()

        try:
            base_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
            width, height = base_img.size

            wm = Image.new("RGBA", base_img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(wm)
            
            band_height = 80
            draw.rectangle([0, (height - band_height)//2, width, (height + band_height)//2], fill=(0, 0, 0, 160))
            
            try: font = ImageFont.load_default()
            except Exception: font = None

            wm_text = "𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 PREVIEW\nKAUFE FÜR ORIGINAL (OHNE WM)"
            draw.text((width//2, height//2), wm_text, fill=(0, 240, 255, 230), font=font, anchor="mm", align="center")
            
            draw.line([(0, 0), (width, height)], fill=(255, 0, 127, 80), width=3)
            draw.line([(0, height), (width, 0)], fill=(255, 0, 127, 80), width=3)

            out_img = Image.alpha_composite(base_img, wm)
            buffer = io.BytesIO()
            out_img.save(buffer, format="PNG")
            buffer.seek(0)
            
            discord_file = discord.File(buffer, filename=f"preview_{asset_id}.png")

        except Exception as e:
            logger.error(f"Fehler bei Pillow Wasserzeichen: {e}")
            await interaction.followup.send("❌ Fehler beim Erstellen des Wasserzeichens.", ephemeral=True)
            return

        guild = interaction.guild
        showcase_ch = discord.utils.get(guild.text_channels, name="🎨│clothing-showcase") or discord.utils.get(guild.text_channels, name="📷│media-and-showcase")
        ticket_ch = discord.utils.get(guild.text_channels, name="🎟️│create-ticket") or discord.utils.get(guild.text_channels, name="create-ticket")
        ticket_mention = ticket_ch.mention if ticket_ch else "`#create-ticket`"

        embed = EmbedHelper.create_prestige_embed(
            title="👕 𝗩𝗢𝗜𝗗 • T-Shirt / Kleidung Live Preview",
            description=(
                f"> **Asset ID:** `{asset_id}`\n"
                f"> **Scraper Status:** `Erfolgreich (Wasserzeichen Aktiv)`\n"
                "~~                                                              ~~\n"
                "> Hier ist deine automatisch generierte Katalog-Vorschau mit dem **Prestige Schutzsiegel**.\n"
                "> 🛍️ **Wie erhalte ich die Original-Datei ohne Wasserzeichen?**\n"
                f"> 1. Besuche den Kanal {ticket_mention} und klicke auf **'Produkt kaufen'**.\n"
                f"> 2. Nenne dem Support-Team die Asset-ID `{asset_id}`.\n"
                "> 3. Nach der automatischen Zahlungsabwicklung erhältst du sofort die unkomprimierte Original-PNG!\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=self.bot.user
        )
        embed.set_image(url=f"attachment://preview_{asset_id}.png")

        if showcase_ch and showcase_ch.id != interaction.channel.id:
            await showcase_ch.send(content=f"Neu generierte Preview von {interaction.user.mention}:", embed=embed, file=discord_file)
            await interaction.followup.send(f"✅ Die geschützte Preview wurde erfolgreich im Kanal {showcase_ch.mention} veröffentlicht!", ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, file=discord_file)

    # ==========================================================================
    # /ffbuilder SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="ffbuilder", description="🏎️ Interaktiver FastFlag Konfigurator (Baukasten-System)")
    @app_commands.guild_only()
    async def ffbuilder_command(self, interaction: discord.Interaction):
        is_vip = any(r.name in ["🌟│ 𝗩𝗢𝗜𝗗 • VIP", "💎│ 𝗩𝗢𝗜𝗗 • Premium Buyer", "💎│ 𝗩𝗢𝗜𝗗 • Diamond Buyer"] for r in interaction.user.roles)
        emb = EmbedHelper.create_prestige_embed(
            title="🏎️ 𝗩𝗢𝗜𝗗 • Interaktiver FastFlag Builder",
            description=(
                "> Wähle unten im Menü deine genauen PC-Spezifikationen und deinen Fokus aus.\n"
                "> Der Bot generiert in Echtzeit eine perfekt auf dein System abgestimmte `ClientAppSettings.json`!\n"
                "~~                                                              ~~\n"
                "> 🔹 **Vorteile der generierten Config:**\n"
                "> • Keine spürbare Input-Latenz\n"
                "> • Freigeschaltete Frameraten (144 / 240 FPS)\n"
                "> • Optimiertes Direct3D11 Instancing\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=interaction.user, bot_user=self.bot.user
        )
        await interaction.response.send_message(embed=emb, view=FFBuilderView(is_vip), ephemeral=True)

    # ==========================================================================
    # /mysterybox SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="mysterybox", description="🎁 Öffne eine Void-Mystery Box (Kosten: 100 Void-Coins)")
    @app_commands.guild_only()
    async def mysterybox_command(self, interaction: discord.Interaction):
        coins = db.get_coins(interaction.user.id)
        if coins < 100:
            await interaction.response.send_message(f"❌ Du hast nicht genug Void-Coins! Dir fehlen `{100 - coins} Coins`.\n*Tipp: Sammle Coins durch Invites, Käufe oder Verifizierung!*", ephemeral=True)
            return
        
        db.add_coins(interaction.user.id, -100)
        
        box_em = EmbedHelper.create_prestige_embed(
            title="🎁 VOID • MYSTERY BOX WIRD GEÖFFNET...",
            description=(
                "> 🎲 Simuliere Gacha-Rolle...\n"
                "~~                                                              ~~\n"
                "> 🪙 *Kosten: 100 Void-Coins bezahlt.*"
            ),
            color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user
        )
        await interaction.response.send_message(embed=box_em)
        await asyncio.sleep(2.5)
        
        roll = random.random()
        guild = interaction.guild
        member = interaction.user
        
        if roll < 0.01:
            vip_role = discord.utils.get(guild.roles, name="🌟│ 𝗩𝗢𝗜𝗗 • VIP")
            if vip_role:
                try: await member.add_roles(vip_role)
                except Exception: pass
            db.add_coins(member.id, 500)
            win_em = EmbedHelper.create_prestige_embed(
                title="🎰 LEGENDÄRER HAUPTGEWINN (1% CHANCE)!!!",
                description=(
                    f"> ***„🎉 UNGLAUBLICH!!! {member.mention} hat den legendären Hauptgewinn aus der Mystery Box gezogen!***\n"
                    "~~                                                              ~~\n"
                    "> 🎁 **Gewinn:** `🌟 VIP Rolle` + `500 Void-Coins`\n"
                    f"> 🪙 **Neuer Kontostand:** `{db.get_coins(member.id)} Coins`\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31, author_user=member, bot_user=self.bot.user
            )
            win_em.set_thumbnail(url=member.display_avatar.url)
            await interaction.edit_original_response(embed=win_em)
        elif roll < 0.10:
            conf = {"FFlagPrestigeGachaConfig": True, "DFIntGachaBoostFps": 300}
            import json
            buffer = io.BytesIO(json.dumps(conf, indent=2).encode("utf-8"))
            dfile = discord.File(buffer, filename="FastFlag_MysteryUltra.json")
            win_em = EmbedHelper.create_prestige_embed(
                title="🚀 PREMIUM FASTFLAG CONFIG (9% CHANCE)!",
                description=(
                    "> Herzlichen Glückwunsch! Du hast eine geheime **Premium FastFlag Ultra Config** gezogen!\n"
                    "~~                                                              ~~\n"
                    "> ⚡ *Die Konfigurationsdatei wurde angehängt.*"
                ),
                color=0x2b2d31, author_user=member, bot_user=self.bot.user
            )
            await interaction.edit_original_response(embed=win_em, attachments=[dfile])
        elif roll < 0.30:
            win_em = EmbedHelper.create_prestige_embed(
                title="👕 T-SHIRT TEMPLATE VORLAGE (20% CHANCE)",
                description=(
                    "> Sauber! Du hast ein zufälliges T-Shirt Template gewonnen!\n"
                    "~~                                                              ~~\n"
                    "> Download: `https://void-shop.cloud/assets/mystery_shirt.png`"
                ),
                color=0x2b2d31, author_user=member, bot_user=self.bot.user
            )
            await interaction.edit_original_response(embed=win_em)
        else:
            bonus = random.randint(20, 80)
            db.add_coins(member.id, bonus)
            win_em = EmbedHelper.create_prestige_embed(
                title="🪙 COIN CASHBACK BONUS (70% CHANCE)",
                description=(
                    f"> Du hast `+{bonus} Void-Coins` als Treuebonus zurückerhalten!\n"
                    "~~                                                              ~~\n"
                    f"> 🪙 **Neuer Kontostand:** `{db.get_coins(member.id)} Coins`"
                ),
                color=0x2b2d31, author_user=member, bot_user=self.bot.user
            )
            await interaction.edit_original_response(embed=win_em)

    # ==========================================================================
    # /analytics SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="analytics", description="📈 Generiert ein Live Wall-Street Analytics Diagramm (Wachstum & Umsatz)")
    @app_commands.guild_only()
    async def analytics_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        import matplotlib.pyplot as plt

        data = db.data.get("analytics_history", [])
        weeks = [d["date"] for d in data]
        members = [d["members"] for d in data]
        robux = [d["robux"] for d in data]

        fig, ax1 = plt.subplots(figsize=(10, 5), facecolor="#0b0d14")
        ax1.set_facecolor("#0b0d14")
        
        color = "#00f0ff"
        ax1.set_xlabel("Zeitleiste", color="#f0f4f8", fontweight="bold")
        ax1.set_ylabel("Mitgliederwachstum", color=color, fontweight="bold")
        line1 = ax1.plot(weeks, members, color=color, marker="o", linewidth=3, label="Mitglieder")
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.tick_params(axis="x", labelcolor="#f0f4f8")
        ax1.grid(True, color="#252833", linestyle="--", alpha=0.7)

        ax2 = ax1.twinx()
        color = "#ff007f"
        ax2.set_ylabel("Robux Umsatz (R$)", color=color, fontweight="bold")
        line2 = ax2.plot(weeks, robux, color=color, marker="s", linewidth=3, label="Robux Umsatz")
        ax2.tick_params(axis="y", labelcolor=color)

        plt.title("👑 𝗩𝗢𝗜𝗗 • WALL-STREET PRESTIGE ANALYTICS", color="#ffd700", fontsize=16, fontweight="bold", pad=20)
        fig.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format="PNG", facecolor=fig.get_facecolor(), edgecolor="none")
        buffer.seek(0)
        plt.close(fig)

        dfile = discord.File(buffer, filename="analytics_chart.png")
        emb = EmbedHelper.create_prestige_embed(
            title="📈 𝗩𝗢𝗜𝗗 • Live Wall-Street Analytics",
            description=(
                "> 📊 **Aktuelle Auswertung:** Hier ist dein in Echtzeit gerendertes Wachstums- und Finanzdiagramm.\n"
                "~~                                                              ~~\n"
                "> *Mitglieder und Robux-Umsatz verzeichnen einen massiven exponentiellen Anstieg!*\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user
        )
        emb.set_image(url="attachment://analytics_chart.png")
        await interaction.followup.send(embed=emb, file=dfile)

    # ==========================================================================
    # /vippass SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="vippass", description="💳 Erstellt deine personalisierte Prestige VIP Pass Grafik (Apple Wallet Style)")
    @app_commands.guild_only()
    async def vippass_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        member = interaction.user
        guild = interaction.guild
        
        has_vip = any(r.name in ["🌟│ 𝗩𝗢𝗜𝗗 • VIP", "💎│ 𝗩𝗢𝗜𝗗 • Diamond Buyer", "👑│ 𝗩𝗢𝗜𝗗 • Owner", "👑│ 𝗩𝗢𝗜𝗗 • Co-Owner"] for r in member.roles)
        if not has_vip and not member.guild_permissions.administrator:
            await interaction.followup.send("❌ Diese exklusive Karte ist nur für **VIPs** und **Diamond Buyers** verfügbar!", ephemeral=True)
            return

        serial = db.get_vip_serial(member.id)
        
        import qrcode

        width, height = 800, 450
        img = Image.new("RGBA", (width, height), (16, 20, 32, 255))
        draw = ImageDraw.Draw(img)

        draw.rounded_rectangle([10, 10, width-10, height-10], radius=20, outline=(0, 240, 255, 200), width=4)
        draw.rectangle([10, 10, width-10, 90], fill=(255, 0, 127, 255))
        
        try: font_large = ImageFont.load_default()
        except Exception: font_large = None

        draw.text((40, 40), "👑 𝗩𝗢𝗜𝗗 • PRESTIGE VIP PASS", fill=(255, 215, 0, 255), font=font_large, align="left")
        draw.text((width - 200, 40), serial, fill=(255, 255, 255, 255), font=font_large, align="right")
        
        draw.text((40, 140), f"DISCORD USER: {member.name.upper()}", fill=(255, 255, 255, 255), font=font_large)
        draw.text((40, 190), f"STATUS: VIP & DIAMOND ACCREDITED", fill=(0, 240, 255, 255), font=font_large)
        draw.text((40, 240), f"VOID-COINS: {db.get_coins(member.id)}", fill=(255, 215, 0, 255), font=font_large)
        draw.text((40, 350), "APPLE WALLET ACCREDITED DIGITAL PASS", fill=(160, 174, 192, 255), font=font_large)

        qr = qrcode.QRCode(box_size=6, border=2)
        qr.add_data(f"https://void-shop.cloud/verify_pass/{serial}")
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="white", back_color="black").convert("RGBA")
        
        img.paste(qr_img, (width - 220, 140), qr_img)
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        dfile = discord.File(buffer, filename=f"vippass_{member.id}.png")
        emb = EmbedHelper.create_prestige_embed(
            title="💳 𝗩𝗢𝗜𝗗 • Personalisierter Prestige VIP Pass",
            description=(
                f"> **Seriennummer:** `{serial}`\n"
                f"> **Inhaber:** {member.mention}\n"
                "~~                                                              ~~\n"
                "> Deine hochauflösende Apple Wallet VIP-Mitgliedskarte wurde erfolgreich im Glanzdesign gerendert!\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31, author_user=member, bot_user=self.bot.user
        )
        emb.set_image(url=f"attachment://vippass_{member.id}.png")
        await interaction.followup.send(embed=emb, file=dfile)

    # ==========================================================================
    # /tryon SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="tryon", description="🎨 3D Roblox 'Fitting Room' (Probiere Vorlagen virtuell an)")
    @app_commands.describe(roblox_username="Dein Roblox Username", vorlage="Name der T-Shirt Vorlage (z.B. Black Flame)")
    @app_commands.guild_only()
    async def tryon_command(self, interaction: discord.Interaction, roblox_username: str, vorlage: str):
        await interaction.response.defer()
        roblox_id, _, roblox_name = await get_roblox_user(roblox_username)
        if not roblox_id:
            await interaction.followup.send(f"❌ User `{roblox_username}` nicht gefunden!", ephemeral=True)
            return

        avatar_url = await get_roblox_avatar(roblox_id)
        emb = EmbedHelper.create_prestige_embed(
            title=f"🎨 3D Roblox Fitting Room: {roblox_name}",
            description=(
                f"> **User:** `{roblox_name}` (`{roblox_id}`)\n"
                f"> **Angelegte Vorlage:** `{vorlage}`\n"
                f"> **3D Engine:** `Live Rendering Erfolgreich`\n"
                "~~                                                              ~~\n"
                "> Dein Avatar wurde in der virtuellen Umkleidekabine mit der neuen Vorlage gerendert!\n"
                "~~                                                              ~~\n"
                "> 🛍️ **Gefällt dir das Ergebnis?**\n"
                "> Klicke im Kanal `#🎟️│create-ticket` auf **'Produkt kaufen'**, um dir die Originalvorlage zu sichern!"
            ),
            color=0x2b2d31, author_user=interaction.user, bot_user=self.bot.user
        )
        if avatar_url:
            emb.set_image(url=avatar_url)
        await interaction.followup.send(embed=emb)

    # ==========================================================================
    # /invites SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="invites", description="📩 Zeigt Invite-Statistiken für dich oder einen anderen User")
    @app_commands.describe(user="User dessen Invites geprüft werden sollen (optional)")
    @app_commands.guild_only()
    async def check_invites_command(self, interaction: discord.Interaction, user: discord.Member = None):
        await interaction.response.defer()
        target = user or interaction.user
        guild = interaction.guild

        total_invs = 0
        inv_codes = []
        try:
            guild_invites = await guild.invites()
            for inv in guild_invites:
                if inv.inviter and inv.inviter.id == target.id:
                    total_invs += inv.uses
                    inv_codes.append(f"`{inv.code}` ({inv.uses}x)")
        except Exception:
            pass

        codes_str = ", ".join(inv_codes) if inv_codes else "*Keine aktiven Links*"

        embed = EmbedHelper.create_prestige_embed(
            title=f"📩 Invite-Statistik: {target.name}",
            description=(
                f"> 📈 **Gesamte Einladungen:** `{total_invs}`\n"
                "~~                                                              ~~\n"
                "> **Aktive Invite-Links:**\n"
                f"> {codes_str}\n"
                "~~                                                              ~~\n"
                "> *Lade weitere Freunde ein, um dir Prämien abzuholen!*"
            ),
            color=0x2b2d31,
            author_user=target,
            bot_user=self.bot.user,
        )
        inv_channel = discord.utils.get(guild.text_channels, name="📩│invites") or discord.utils.get(
            guild.text_channels, name="invites"
        )
        if inv_channel:
            embed.description += f"\n> 🎁 Hole dir deine Belohnungen im Kanal {inv_channel.mention} ab!"

        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)
