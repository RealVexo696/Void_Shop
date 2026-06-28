"""
Tickets Cog — 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 (Components V2 Edition)
==================================================================
Komplett neu aufgebautes, hochmodernes Ticket-System.

Features (deutlich verbessert):
  • 100% Discord Components V2 (Container / TextDisplay / ActionRow / Separator)
  • Produkt-Auswahl direkt im Panel (6 Produkte, inkl. Unlimited-Produkte)
  • Fortlaufende Ticket-Nummern (ticket-0001, ticket-0002, ...)
  • Live Produkt-Katalog mit Preisen im Kauf-Ticket
  • Claim / Unclaim, Priorität setzen, User add/remove, Umbenennen
  • Sterne-Bewertung per Buttons (kein Tippen mehr nötig)
  • Saubere Transkripte + Ticket-Logs
"""

import io
import asyncio
import logging

import discord
from discord.ext import commands, tasks
from discord.ui import Modal, TextInput

from bot.cogs.database import db
from bot.cogs.components_v2 import PrestigeContainer, build_layout

logger = logging.getLogger("void_shop_bot.tickets")

ACCENT = 0x2b2d31
ACCENT_BUY = 0x00d26a       # grün für Kauf
ACCENT_SUPPORT = 0x5865f2   # blurple für Support
ACCENT_PARTNER = 0xffd700   # gold für Partner

SUPPORT_CATEGORY = "🎟️│── 𝗩𝗢𝗜𝗗 • ＳＵＰ𝗣Ｏ𝗥𝗧 ──"
BUY_CATEGORY = "🛒│── 𝗩𝗢𝗜𝗗 • ＫＡＵＦＥＮ ──"
PARTNER_CATEGORY = "🤝│── 𝗩𝗢𝗜𝗗 • ＰＡＲＴＮＥＲ ──"
TICKET_LOG_CHANNEL = "💾│ticket-logs"

STAFF_ROLE_NAMES = [
    "👑│ 𝗩𝗢𝗜𝗗 • Owner",
    "👑│ 𝗩𝗢𝗜𝗗 • Co-Owner",
    "🛠️│ 𝗩𝗢𝗜𝗗 • Admin",
    "⚙️│ 𝗩𝗢𝗜𝗗 • Manager",
    "🛡️│ 𝗩𝗢𝗜𝗗 • Moderator",
    "🎫│ 𝗩𝗢𝗜𝗗 • Support",
]

# ==================================================================
# PRODUKT-KATALOG  (zentral — auch fürs Web-Dashboard wiederverwendbar)
# ==================================================================
PRODUCTS = {
    "infinityxeh": {
        "name": "INFINITYxEH", "emoji": "♾️", "price": "750 R$ / 7,50 €", "robux": 750,
        "desc": "Premium All-in-One Executor — INFINITY × EH Edition.",
        "value": "infinityxeh", "auto_delivery": True, "needs_key": True,
    },
    "fflags_injector": {
        "name": "FFlags Injector", "emoji": "💉", "price": "300 R$ / 3,00 €", "robux": 300,
        "desc": "Automatischer FastFlag-Injector für maximale FPS & Performance.",
        "value": "fflags_injector", "auto_delivery": True, "needs_key": True,
    },
    "anti_ban": {
        "name": "Anti-Ban", "emoji": "🛡️", "price": "1.000 R$ / 10,00 €", "robux": 1000,
        "desc": "Schutzsystem gegen Bans — sicher & stabil.",
        "value": "anti_ban", "auto_delivery": True, "needs_key": True,
    },
    "tshirt_templates": {
        "name": "T-Shirt Templates", "emoji": "👕", "price": "500 R$ / 5,00 €", "robux": 500,
        "desc": "50+ Roblox T-Shirt Vorlagen mit Verkaufsrechten (PNG/PSD).",
        "value": "tshirt_templates", "auto_delivery": True, "needs_key": True,
    },
    "fastflags_pack": {
        "name": "FastFlags Pack", "emoji": "🚀", "price": "150 R$ / 1,50 €", "robux": 150,
        "desc": "Ultra FPS-Boost Config mit stabilen Roblox FastFlags.",
        "value": "fastflags_pack", "auto_delivery": True, "needs_key": True,
    },
    "discord_template": {
        "name": "Discord Server Template", "emoji": "🖥️", "price": "400 R$ / 4,00 €", "robux": 400,
        "desc": "Premium Discord-Shop Template mit Struktur, Rollen & Kanälen.",
        "value": "discord_template", "auto_delivery": True, "needs_key": True,
    },
}

# Reihenfolge im Produkt-Auswahlmenü (Kaufen-Ticket)
PRODUCT_ORDER = ["infinityxeh", "fflags_injector", "anti_ban", "tshirt_templates", "fastflags_pack", "discord_template"]


def product_catalog_text() -> str:
    """Schöner Markdown-Block mit allen Produkten + Preisen."""
    lines = ["### 🛍️ Produkt-Katalog"]
    for key in PRODUCT_ORDER:
        p = PRODUCTS[key]
        stock = "∞ unlimited" if db.is_unlimited(key) else f"{db.stock_count(key)} auf Lager"
        lines.append(f"{p['emoji']} **{p['name']}** — `{p['price']}` · **{stock}**\n-# {p['desc']}")
    return "\n".join(lines)


# Mengenrabatt-Staffel: ab N Artikeln X% Rabatt
QUANTITY_DISCOUNTS = [(4, 0.20), (3, 0.15), (2, 0.10)]


def cart_summary(cart_keys, coupon_code=None):
    """Berechnet Warenkorb: Zeilen, Zwischensumme, Rabatt, Endpreis (in Robux)."""
    subtotal = sum(PRODUCTS[k]["robux"] for k in cart_keys if k in PRODUCTS)
    qty = len(cart_keys)
    discount_pct = 0.0
    for threshold, pct in QUANTITY_DISCOUNTS:
        if qty >= threshold:
            discount_pct = pct
            break
    coupon_pct = db.coupon_get(coupon_code) if coupon_code else None
    if not coupon_pct and coupon_code:
        aff = db.affiliate_get(coupon_code)
        if aff: coupon_pct = aff.get("discount", 10)
    if coupon_pct:
        discount_pct = max(discount_pct, min(int(coupon_pct), 90) / 100)
    discount_robux = round(subtotal * discount_pct)
    total = subtotal - discount_robux
    counts = {}
    for k in cart_keys:
        counts[k] = counts.get(k, 0) + 1
    lines = []
    for k, c in counts.items():
        p = PRODUCTS[k]
        lines.append(f"{p['emoji']} **{p['name']}** ×{c} — `{p['robux']*c} R$`")
    return {
        "lines": lines, "subtotal": subtotal, "qty": qty,
        "discount_pct": discount_pct, "discount_robux": discount_robux, "total": total,
        "coupon_code": coupon_code if coupon_pct else None,
    }


def cart_text(cart_keys, coupon_code=None):
    if not cart_keys:
        return "🛒 Dein Warenkorb ist **leer**. Füge unten Produkte hinzu."
    s = cart_summary(cart_keys, coupon_code)
    out = ["🛒 **Dein Warenkorb:**", ""] + s["lines"] + [""]
    out.append(f"Zwischensumme: `{s['subtotal']} R$`")
    if s["discount_pct"] > 0:
        label = f"Coupon `{s['coupon_code']}`" if s.get("coupon_code") else "Mengenrabatt"
        out.append(f"🎉 {label} ({int(s['discount_pct']*100)}%): `−{s['discount_robux']} R$`")
    out.append(f"**Gesamt: `{s['total']} R$ / {s['total']*0.01:.2f} €`**")
    return "\n".join(out)


# ==================================================================
# HELFER
# ==================================================================
def get_roles(guild, names):
    return [discord.utils.get(guild.roles, name=n) for n in names]


def is_staff(member: discord.Member) -> bool:
    if member.guild_permissions.administrator:
        return True
    staff = [r for r in get_roles(member.guild, STAFF_ROLE_NAMES) if r]
    return any(r in member.roles for r in staff)


async def send_ticket_log(guild, container: discord.ui.Container):
    ch = discord.utils.get(guild.text_channels, name=TICKET_LOG_CHANNEL)
    if ch:
        view = discord.ui.LayoutView(timeout=None)
        view.add_item(container)
        try:
            await ch.send(view=view)
        except Exception:
            pass


# ==================================================================
# MODALS: USER HINZUFÜGEN / ENTFERNEN / UMBENENNEN
# ==================================================================
async def _resolve_member(guild, user_str):
    user = None
    if user_str.isdigit():
        user = guild.get_member(int(user_str))
        if not user:
            try:
                user = await guild.fetch_member(int(user_str))
            except Exception:
                pass
    if not user:
        user = discord.utils.get(guild.members, name=user_str)
    return user


class AddUserModal(Modal, title="➕ User zum Ticket hinzufügen"):
    user_input = TextInput(label="User-ID oder Username",
                           placeholder="z.B. 123456789012345678 oder name", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user = await _resolve_member(interaction.guild, self.user_input.value)
        if not user:
            return await interaction.response.send_message(
                f"❌ User '{self.user_input.value}' nicht gefunden!", ephemeral=True)
        try:
            await interaction.channel.set_permissions(
                user, view_channel=True, send_messages=True, read_message_history=True)
            cont = PrestigeContainer(
                "➕ User hinzugefügt",
                f"{interaction.user.mention} hat {user.mention} zum Ticket hinzugefügt.",
                accent=ACCENT)
            v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
            await interaction.channel.send(view=v)
            await interaction.response.send_message(f"✅ {user.name} hinzugefügt!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)


class RemoveUserModal(Modal, title="➖ User aus Ticket entfernen"):
    user_input = TextInput(label="User-ID oder Username",
                           placeholder="z.B. 123456789012345678", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user = await _resolve_member(interaction.guild, self.user_input.value)
        if not user:
            return await interaction.response.send_message(
                f"❌ User '{self.user_input.value}' nicht gefunden!", ephemeral=True)
        try:
            await interaction.channel.set_permissions(user, overwrite=None)
            cont = PrestigeContainer(
                "➖ User entfernt",
                f"{interaction.user.mention} hat {user.mention} aus dem Ticket entfernt.",
                accent=ACCENT)
            v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
            await interaction.channel.send(view=v)
            await interaction.response.send_message(f"✅ {user.name} entfernt!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)


class RenameModal(Modal, title="✏️ Ticket umbenennen"):
    name_input = TextInput(label="Neuer Name (ohne Präfix)",
                           placeholder="z.B. vip-kunde", required=True, max_length=80)

    async def on_submit(self, interaction: discord.Interaction):
        ch = interaction.channel
        prefix = ch.name.split("-")[0]
        try:
            await ch.edit(name=f"{prefix}-{self.name_input.value.lower().replace(' ', '-')}")
            await interaction.response.send_message("✅ Ticket umbenannt!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Fehler: {e}", ephemeral=True)


# ==================================================================
# TICKET SCHLIESSEN + TRANSKRIPT
# ==================================================================
async def execute_ticket_close_process(channel, closed_by_user, bot_user):
    db.add_log("ticket", f"Ticket '{channel.name}' von {closed_by_user.name} geschlossen")

    closing = PrestigeContainer(
        "🔒 Ticket wird geschlossen",
        "⚠️ Dieses Ticket wird transkribiert und in **4 Sekunden** gelöscht...",
        accent=ACCENT)
    try:
        v = discord.ui.LayoutView(timeout=None); v.add_item(closing)
        await channel.send(view=v)
    except Exception:
        pass
    await asyncio.sleep(4)

    try:
        messages, transcript_json = [], []
        async for msg in channel.history(limit=1000, oldest_first=True):
            ts = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = msg.author.name + (" [BOT]" if msg.author.bot else "")
            content = msg.content or "[Kein Textinhalt]"
            if msg.attachments:
                content += " (Anhänge: " + ", ".join(a.url for a in msg.attachments) + ")"
            messages.append(f"[{ts}] {author}: {content}")
            transcript_json.append({
                "author": msg.author.name,
                "avatar": msg.author.display_avatar.url if msg.author.display_avatar
                          else "https://cdn.discordapp.com/embed/avatars/0.png",
                "timestamp": ts, "content": content, "bot": msg.author.bot})

        db.add_ticket_transcript(channel.name, closed_by_user, transcript_json)
        try:
            meta = db.data.get("ticket_meta", {}).get(str(channel.id), {})
            response_secs = 0
            if meta.get("opened") and meta.get("claimed"):
                try:
                    import datetime
                    response_secs = int((datetime.datetime.fromisoformat(meta["claimed"]) - datetime.datetime.fromisoformat(meta["opened"])).total_seconds())
                except Exception:
                    response_secs = 0
            creator_id = None
            if channel.topic and "creator:" in channel.topic:
                creator_id = channel.topic.split("creator:", 1)[1].split()[0]
            related_sales = [x for x in db.data.get("sales_log", []) if not creator_id or str(x.get("buyer_id")) == str(creator_id)]
            latest_sale = related_sales[0] if related_sales else {}
            db.add_ticket_summary(channel.id, {
                "channel": channel.name,
                "ticket_type": channel.topic or "Support",
                "buyer_id": creator_id,
                "product": latest_sale.get("product_name", "—"),
                "amount": latest_sale.get("robux", 0),
                "supporter": meta.get("supporter"),
                "response_secs": response_secs,
                "delivery": db.get_payment_status(channel.id),
                "closed_by": closed_by_user.name,
                "messages": len(transcript_json),
                "closed_at": discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            })
        except Exception:
            pass

        transcript = (
            "==================================================\n"
            "         𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 - TICKET TRANSKRIPT\n"
            "==================================================\n"
            f"Kanalname:   {channel.name}\n"
            f"Geschlossen: {closed_by_user.name} ({closed_by_user.id})\n"
            f"Nachrichten: {len(messages)}\n"
            "==================================================\n\n" + "\n".join(messages))

        logch = discord.utils.get(channel.guild.text_channels, name=TICKET_LOG_CHANNEL)
        if logch:
            f = discord.File(io.BytesIO(transcript.encode("utf-8")),
                             filename=f"transcript-{channel.name}.txt")
            prod_val = latest_sale.get("product_name", "—") if 'latest_sale' in locals() and latest_sale else "—"
            amt_val = latest_sale.get("robux", 0) if 'latest_sale' in locals() and latest_sale else 0
            supp_val = meta.get("supporter", "—") if 'meta' in locals() and meta else "—"
            resp_val = f"{response_secs}s" if 'response_secs' in locals() else "—"
            deliv_val = db.get_payment_status(channel.id)
            buyer_mention = f"<@{creator_id}>" if 'creator_id' in locals() and creator_id else "—"
            cont = PrestigeContainer(
                "💾 Automatische Ticket-Zusammenfassung",
                f"**Produkt:** `{prod_val}`\n"
                f"**Käufer:** {buyer_mention}\n"
                f"**Betrag:** `{amt_val} R$`\n"
                f"**Supporter:** `{supp_val}`\n"
                f"**Zeit bis Antwort:** `{resp_val}`\n"
                f"**Lieferung:** `{deliv_val}`\n\n"
                f"**Ticket:** `{channel.name}` · **Geschlossen von:** {closed_by_user.mention} ({len(messages)} Msgs)",
                accent=ACCENT)
            v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
            await logch.send(view=v, file=f)
    except Exception as e:
        logger.error(f"Transkript-Fehler: {e}")

    try:
        await channel.delete()
    except Exception as e:
        logger.error(f"Kanal-Löschfehler: {e}")


# ==================================================================
# BEWERTUNG (STERNE PER BUTTON)
# ==================================================================
class FeedbackModal(Modal, title="⭐ Deine Rezension"):
    def __init__(self, product_name, stars):
        super().__init__()
        self.product_name = product_name
        self.stars = stars

    feedback = TextInput(label="Wie war Support & Produkt?",
                         style=discord.TextStyle.paragraph,
                         placeholder="Beschreibe kurz deine Erfahrung...",
                         required=True, max_length=1000)

    async def on_submit(self, interaction: discord.Interaction):
        guild, member = interaction.guild, interaction.user
        stars_str = "⭐" * self.stars + "▫️" * (5 - self.stars)
        vouch_count = db.add_user_vouch(member.id)
        db.add_supporter_review(member.name, self.stars)

        reward = ""
        try:
            r_bronze = discord.utils.get(guild.roles, name="🥉│ 𝗩𝗢𝗜𝗗 • Bronze Buyer")
            r_silver = discord.utils.get(guild.roles, name="🥈│ 𝗩𝗢𝗜𝗗 • Silver Buyer")
            r_gold = discord.utils.get(guild.roles, name="🥇│ 𝗩𝗢𝗜𝗗 • Gold Buyer")
            r_diamond = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • Diamond Buyer")
            if vouch_count == 1 and r_bronze:
                await member.add_roles(r_bronze); db.add_coins(member.id, 20)
                reward = "\n🎁 **+1 Vouch:** `🥉 Bronze Buyer` + 20 Void-Coins!"
            elif vouch_count == 3 and r_silver:
                await member.add_roles(r_silver)
                reward = "\n🎁 **3 Vouches:** `🥈 Silver Buyer` + gratis T-Shirt Vorlage!"
            elif vouch_count == 5 and r_gold:
                await member.add_roles(r_gold)
                reward = "\n🎁 **5 Vouches:** `🥇 Gold Buyer` + VIP-Lounge!"
            elif vouch_count >= 10 and r_diamond:
                await member.add_roles(r_diamond)
                reward = "\n💎 **10 Vouches:** `💎 Diamond Buyer` + 10% Lifetime-Rabatt!"
        except Exception:
            pass

        vouch_ch = (discord.utils.get(guild.text_channels, name="🤝│vouches")
                    or discord.utils.get(guild.text_channels, name="vouches"))
        if vouch_ch:
            cont = PrestigeContainer(
                "⭐ NEUE KUNDENBEWERTUNG ⭐",
                f"**Kunde:** {member.mention}\n"
                f"**Produkt:** `{self.product_name}`\n"
                f"**Bewertung:** {stars_str}  ({self.stars}/5)\n"
                f"**Vouch-Zähler:** `{vouch_count}x`\n\n"
                f"**Rezension:**\n> *\"{self.feedback.value}\"*",
                accent=ACCENT_BUY, author=member)
            v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
            try:
                await vouch_ch.send(view=v)
            except Exception:
                pass

        thanks = build_layout(
            "🎉 Vielen Dank für deine Bewertung!",
            f"Dein Feedback wurde in {vouch_ch.mention if vouch_ch else '#vouches'} veröffentlicht!{reward}\n\n"
            "Das Ticket wird nun abgeschlossen...",
            accent=ACCENT_BUY, author=member)
        await interaction.response.send_message(view=thanks)
        await execute_ticket_close_process(interaction.channel, member, interaction.client.user)


class StarRatingView(discord.ui.LayoutView):
    """Sterne 1–5 als Buttons + Produktname."""
    def __init__(self, product_name):
        super().__init__(timeout=300)
        self.product_name = product_name
        star_btns = []
        for i in range(1, 6):
            b = discord.ui.Button(label=f"{i} ⭐", style=discord.ButtonStyle.success
                                  if i >= 4 else discord.ButtonStyle.secondary)
            b.callback = self._make_cb(i)
            star_btns.append(b)
        row = discord.ui.ActionRow()
        for b in star_btns:
            row.add_item(b)
        cont = PrestigeContainer(
            "⭐ Wie zufrieden bist du?",
            f"Du bewertest: **{product_name}**\nKlicke auf deine Sterne-Anzahl:",
            accent=ACCENT_BUY, items=[row])
        self.add_item(cont)

    def _make_cb(self, stars):
        async def cb(interaction: discord.Interaction):
            await interaction.response.send_modal(FeedbackModal(self.product_name, stars))
        return cb


class ProductReviewSelect(discord.ui.Select):
    def __init__(self):
        opts = [discord.SelectOption(label=PRODUCTS[k]["name"], emoji=PRODUCTS[k]["emoji"],
                                     value=k) for k in PRODUCT_ORDER]
        super().__init__(placeholder="Welches Produkt hast du gekauft?",
                         options=opts, custom_id="review_product_select")

    async def callback(self, interaction: discord.Interaction):
        p = PRODUCTS[self.values[0]]
        await interaction.response.send_message(
            view=StarRatingView(f"{p['emoji']} {p['name']}"), ephemeral=False)


class PurchaseQuestion2View(discord.ui.LayoutView):
    """Produkt-Auswahl vor der Bewertung (persistent)."""
    def __init__(self):
        super().__init__(timeout=None)
        cont = PrestigeContainer(
            "🛒 Vouch-Leveling: Produkt-Auswahl",
            "Klasse! Mit deiner Bewertung nimmst du am **Vouch-Leveling** teil 🎉\n\n"
            "Wähle unten dein gekauftes Produkt:",
            accent=ACCENT_BUY, items=[ProductReviewSelect()])
        self.add_item(cont)


# ==================================================================
# CLOSE-MENÜ (direkt schließen / bewerten / abbrechen)
# ==================================================================
class CloseTicketMenu(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        b_close = discord.ui.Button(label="🔒 Direkt Schließen", style=discord.ButtonStyle.danger,
                                    custom_id="ctm_close")
        b_review = discord.ui.Button(label="🛒 Bewerten & Belohnung", style=discord.ButtonStyle.success,
                                     custom_id="ctm_review")
        b_cancel = discord.ui.Button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary,
                                     custom_id="ctm_cancel")
        b_close.callback = self._close
        b_review.callback = self._review
        b_cancel.callback = self._cancel
        row = discord.ui.ActionRow()
        for b in (b_close, b_review, b_cancel):
            row.add_item(b)
        cont = PrestigeContainer(
            "🔒 Ticket Schließen & Vouch-Leveling",
            "Direkt schließen oder am **Vouch-Leveling** teilnehmen?\n\n"
            "🎁 **Vorteile beim Bewerten:**\n"
            "• **1 Vouch:** `🥉 Bronze` + 20 Coins\n"
            "• **3 Vouches:** `🥈 Silver` + gratis Vorlage\n"
            "• **5 Vouches:** `🥇 Gold` + VIP-Lounge\n"
            "• **10 Vouches:** `💎 Diamond` + 10% Lifetime-Rabatt",
            accent=ACCENT, items=[row])
        self.add_item(cont)

    async def _close(self, interaction):
        await interaction.response.send_message("🔒 Schließe Ticket...", ephemeral=True)
        await execute_ticket_close_process(interaction.channel, interaction.user, interaction.client.user)

    async def _review(self, interaction):
        await interaction.response.send_message(view=PurchaseQuestion2View())

    async def _cancel(self, interaction):
        try:
            await interaction.message.delete()
        except Exception:
            await interaction.response.send_message("Abgebrochen.", ephemeral=True)


# ==================================================================
# HAUPT-STEUERUNG IM TICKET (Claim / Add / Remove / Rename / Priority / Close)
# ==================================================================
class CloseTicketView(discord.ui.LayoutView):
    """Steuerleiste im Ticket-Kanal (persistent, Components V2)."""
    def __init__(self):
        super().__init__(timeout=None)

        b_claim = discord.ui.Button(label="Claimen", emoji="🙋‍♂️",
                                    style=discord.ButtonStyle.primary, custom_id="claim_ticket_btn")
        b_priority = discord.ui.Button(label="Priorität", emoji="⚡",
                                       style=discord.ButtonStyle.secondary, custom_id="priority_ticket_btn")
        b_add = discord.ui.Button(label="User +", emoji="➕",
                                  style=discord.ButtonStyle.success, custom_id="add_user_ticket_btn")
        b_remove = discord.ui.Button(label="User −", emoji="➖",
                                     style=discord.ButtonStyle.secondary, custom_id="remove_user_ticket_btn")
        b_rename = discord.ui.Button(label="Umbenennen", emoji="✏️",
                                     style=discord.ButtonStyle.secondary, custom_id="rename_ticket_btn")
        b_close = discord.ui.Button(label="Schließen", emoji="🔒",
                                    style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")

        b_claim.callback = self._claim
        b_priority.callback = self._priority
        b_add.callback = lambda i: i.response.send_modal(AddUserModal())
        b_remove.callback = lambda i: i.response.send_modal(RemoveUserModal())
        b_rename.callback = self._rename
        b_close.callback = self._close

        row1 = discord.ui.ActionRow()
        for b in (b_claim, b_priority):
            row1.add_item(b)
        row2 = discord.ui.ActionRow()
        for b in (b_add, b_remove, b_rename):
            row2.add_item(b)
        row3 = discord.ui.ActionRow()
        row3.add_item(b_close)

        cont = PrestigeContainer(
            "🎛️ Ticket-Steuerung",
            "Nutze die Buttons unten zur Verwaltung dieses Tickets.",
            accent=ACCENT, items=[row1, row2, row3])
        self.add_item(cont)

    async def _claim(self, interaction: discord.Interaction):
        if not is_staff(interaction.user):
            return await interaction.response.send_message("❌ Du gehörst nicht zum Support-Team!", ephemeral=True)
        guild, channel, member = interaction.guild, interaction.channel, interaction.user

        creator = None
        for tgt, _ in channel.overwrites.items():
            if isinstance(tgt, discord.Member) and not tgt.bot and not is_staff(tgt):
                creator = tgt
                break

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        if creator:
            overwrites[creator] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        for role in get_roles(guild, STAFF_ROLE_NAMES):
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
        try:
            await channel.edit(overwrites=overwrites)
        except Exception as e:
            logger.error(f"Claim-Fehler: {e}")

        cont = PrestigeContainer(
            "🙋‍♂️ Ticket geclaimed!",
            f"Dieses Ticket wird nun exklusiv von {member.mention} betreut.\n"
            "Bitte richte alle weiteren Fragen direkt an deinen Supporter.",
            accent=ACCENT_SUPPORT, author=member)
        v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
        await interaction.response.send_message(view=v)
        db.add_supporter_claim(member.name)
        await send_ticket_log(guild, PrestigeContainer(
            "🙋‍♂️ Ticket geclaimed",
            f"**Kanal:** {channel.mention}\n**Supporter:** {member.mention}", accent=ACCENT))

    async def _priority(self, interaction: discord.Interaction):
        if not is_staff(interaction.user):
            return await interaction.response.send_message("❌ Nur Team!", ephemeral=True)
        await interaction.response.send_message(view=PriorityView(), ephemeral=True)

    async def _rename(self, interaction: discord.Interaction):
        if not is_staff(interaction.user):
            return await interaction.response.send_message("❌ Nur Team!", ephemeral=True)
        await interaction.response.send_modal(RenameModal())

    async def _close(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=CloseTicketMenu())


class PriorityView(discord.ui.LayoutView):
    """Priorität setzen (Emoji-Präfix am Kanalnamen)."""
    def __init__(self):
        super().__init__(timeout=120)
        levels = [("🟢 Niedrig", "🟢", discord.ButtonStyle.success),
                  ("🟡 Mittel", "🟡", discord.ButtonStyle.secondary),
                  ("🔴 Hoch", "🔴", discord.ButtonStyle.danger)]
        row = discord.ui.ActionRow()
        for label, emoji, style in levels:
            b = discord.ui.Button(label=label, style=style)
            b.callback = self._make_cb(emoji, label)
            row.add_item(b)
        cont = PrestigeContainer("⚡ Priorität setzen",
                                 "Wähle die Dringlichkeit dieses Tickets:", accent=ACCENT, items=[row])
        self.add_item(cont)

    def _make_cb(self, emoji, label):
        async def cb(interaction: discord.Interaction):
            ch = interaction.channel
            base = ch.name
            for e in ("🟢", "🟡", "🔴"):
                base = base.replace(f"{e}-", "")
            try:
                await ch.edit(name=f"{emoji}-{base}")
            except Exception:
                pass
            cont = PrestigeContainer("⚡ Priorität aktualisiert",
                                     f"Dieses Ticket wurde als **{label}** markiert.", accent=ACCENT)
            v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
            await interaction.response.send_message(view=v)
        return cb


# ==================================================================
# TICKET ERSTELLEN — DROPDOWN MIT PRODUKTEN & KATEGORIEN
# ==================================================================
# ==================================================================
# AUTO-DELIVERY — Staff bestätigt Kauf → Key wird per DM geliefert
# ==================================================================
class DeliveryView(discord.ui.LayoutView):
    """Panel im Kauf-Ticket. Nur Team kann den Kauf bestätigen.
    Bei Bestätigung wird ein freier Key aus dem Vorrat gezogen,
    dem Käufer per DM zugestellt, der Verkauf protokolliert und
    die Customer-Rolle vergeben.

    Hinweis: custom_id enthält product_key & buyer_id, damit der Button
    auch nach Bot-Neustart funktioniert (wird in on_interaction geparst)."""
    def __init__(self, product_key, buyer_id):
        super().__init__(timeout=None)
        self.product_key = product_key
        self.buyer_id = buyer_id
        p = PRODUCTS.get(product_key, {})
        stock = db.stock_count(product_key)

        b_confirm = discord.ui.Button(
            label="✅ Kauf bestätigen & liefern",
            style=discord.ButtonStyle.success,
            custom_id=f"deliver:{product_key}:{buyer_id}",
            disabled=(not db.is_unlimited(product_key) and stock <= 0),
        )
        b_confirm.callback = self._confirm
        row = discord.ui.ActionRow()
        row.add_item(b_confirm)

        stock_txt = "🟣 ∞ unlimited — kein Key nötig" if db.is_unlimited(product_key) else (f"🟢 {stock} Keys auf Lager" if stock > 0 else "🔴 KEINE Keys auf Lager — bitte mit /addkeys auffüllen!")
        cont = PrestigeContainer(
            "📦 Auto-Delivery (Team)",
            f"**Produkt:** {p.get('emoji','')} {p.get('name','?')} — `{p.get('price','?')}`\n"
            f"**Käufer:** <@{buyer_id}>\n"
            f"**Lager:** {stock_txt}\n\n"
            "Sobald die Zahlung eingegangen ist, klicke unten — der Käufer "
            "erhält seinen Key **automatisch per DM**.",
            accent=ACCENT_BUY, items=[row], footer=False)
        self.add_item(cont)

    async def _confirm(self, interaction: discord.Interaction):
        if not is_staff(interaction.user):
            return await interaction.response.send_message("❌ Nur das Team kann Käufe bestätigen!", ephemeral=True)
        await deliver_product(interaction, self.product_key, self.buyer_id)


async def warn_low_stock(guild, product_key):
    """Warnt im Ticket-Log und per DM/Ping, wenn ein Produkt <= 2 Keys hat."""
    try:
        if db.is_unlimited(product_key):
            return
        stock = db.stock_count(product_key)
        if stock <= 2:
            p = PRODUCTS.get(product_key, {"name": product_key, "emoji": "📦"})
            name = p.get('name', product_key)
            admin_role = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • Admin") if guild else None
            ping = admin_role.mention if admin_role else "@admin"
            msg = (f"{ping}\n⚠️ **{name} hat nur noch {stock} Keys.**\n"
                   "Bitte mit `/addkeys` auffüllen oder `/un` aktivieren.")
            await send_ticket_log(guild, PrestigeContainer("⚠️ Stock-Warnung", msg, accent=0xffa500))
            if guild and guild.owner:
                try:
                    await guild.owner.send(f"⚠️ **Anti-Ban / {name} hat nur noch {stock} Keys.**")
                except Exception:
                    pass
    except Exception:
        pass


async def deliver_product(interaction: discord.Interaction, product_key, buyer_id):
    """Zentrale Liefer-Logik: Key ziehen, DM senden, Sale loggen, Rolle vergeben.
    Wird nur noch für alte/persistente deliver:<product>:<buyer>-Buttons genutzt;
    der neue Kauf-Flow nutzt deliver_cart()."""
    guild = interaction.guild
    p = PRODUCTS.get(product_key)
    if not p:
        return await interaction.response.send_message("❌ Unbekanntes Produkt.", ephemeral=True)

    buyer = guild.get_member(int(buyer_id)) if guild else None
    order_id = db.next_order_number()
    key = db.claim_key(product_key, buyer_id, buyer.name if buyer else str(buyer_id))
    if not key:
        return await interaction.response.send_message(
            f"❌ Keine Keys mehr für **{p['name']}** im Vorrat! Bitte mit `/addkeys` auffüllen oder `/un` aktivieren.",
            ephemeral=True)

    is_unlimited_delivery = key == "__UNLIMITED__"
    delivered_dm = False
    if buyer:
        try:
            if is_unlimited_delivery:
                delivery_text = (
                    f"{p['emoji']} **{p['name']}** ist auf **Unlimited** gesetzt.\n"
                    "Für dieses Produkt brauchst du keinen Lizenz-Key. Ein Teammitglied erklärt dir im Ticket die nächsten Schritte.\n\n"
                )
            else:
                delivery_text = (
                    f"🔑 **Dein Lizenz-Key:**\n```\n{key}\n```\n"
                    "Nutze ihn mit `/redeem <key>` oder bewahre ihn sicher auf.\n\n"
                )
            ov_txt = db.get_product_overrides().get(product_key, {}).get("delivery_msg", "").strip()
            extra_hint = f"📌 **Dateien & Anleitung:**\n{ov_txt}\n\n" if ov_txt else ""
            dm_cont = PrestigeContainer(
                "🧾 𝗩𝗢𝗜𝗗 • Receipt & Lieferung",
                f"**Bestellnummer:** `{order_id}`\n"
                f"**Produkt:** {p['emoji']} **{p['name']}**\n"
                f"**Preis:** `{p.get('robux', 0)} R$ / {p.get('robux', 0)*0.01:.2f} €`\n"
                f"**Datum:** {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n"
                f"{delivery_text}{extra_hint}"
                "-# Powered by 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • Auto-Delivery",
                accent=ACCENT_BUY, footer=False)
            dv = discord.ui.LayoutView(timeout=None); dv.add_item(dm_cont)
            await buyer.send(view=dv)
            delivered_dm = True
        except Exception:
            delivered_dm = False

        try:
            cust = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • Customer")
            if cust and cust not in buyer.roles:
                await buyer.add_roles(cust)
        except Exception:
            pass

    db.log_sale(product_key, p["name"], buyer_id, buyer.name if buyer else str(buyer_id), p.get("robux", 0), order_id=order_id)
    db.add_purchase(buyer.name if buyer else str(buyer_id), p["name"], p.get("robux", 0))

    dm_status = "✅ per DM zugestellt" if delivered_dm else "⚠️ DM fehlgeschlagen (DMs aus?)"
    fallback = ""
    if not delivered_dm:
        fallback = "\nDieses Produkt ist Unlimited und braucht keinen Key.\n" if is_unlimited_delivery else f"\n```\n{key}\n```\n"
    cont = PrestigeContainer(
        "🎉 Kauf bestätigt & geliefert!",
        f"**Bestellnummer:** `{order_id}`\n"
        f"**Produkt:** {p['emoji']} {p['name']}\n"
        f"**Käufer:** <@{buyer_id}>\n"
        f"**Lieferung:** {dm_status}{fallback}"
        f"**Restbestand:** {db.stock_label(product_key)}\n\n"
        "Die Customer-Rolle wurde automatisch vergeben. ⭐",
        accent=ACCENT_BUY)
    v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
    await interaction.response.send_message(view=v)
    await send_ticket_log(guild, PrestigeContainer(
        "📦 Auto-Delivery ausgeführt",
        f"**Bestellnummer:** `{order_id}`\n**Produkt:** {p['name']}\n**Käufer:** <@{buyer_id}>\n"
        f"**Lieferung:** {'DM' if delivered_dm else 'im Ticket'}\n**Rest:** {db.stock_label(product_key)}",
        accent=ACCENT))
    await warn_low_stock(guild, product_key)

# ==================================================================
# WARENKORB im Kauf-Ticket
# ==================================================================
def build_cart_view(channel_id, buyer_id):
    """Erzeugt die LayoutView mit Warenkorb-Inhalt + Buttons (Add/Clear/Checkout)."""
    cart = db.get_cart(channel_id)
    coupon_code = db.cart_get_coupon(channel_id)

    # Add-Buttons je Produkt (Discord erlaubt max. 5 Buttons pro Reihe → 2 Reihen)
    add_rows = [discord.ui.ActionRow(), discord.ui.ActionRow()]
    for idx, key in enumerate(PRODUCT_ORDER):
        p = PRODUCTS[key]
        b = discord.ui.Button(
            label=f"+ {p['name']}", emoji=p["emoji"],
            style=discord.ButtonStyle.secondary,
            custom_id=f"cart_add:{channel_id}:{buyer_id}:{key}")
        add_rows[0 if idx < 3 else 1].add_item(b)

    # Aktions-Buttons
    action_row = discord.ui.ActionRow()
    action_row.add_item(discord.ui.Button(
        label="🏷️ Coupon", style=discord.ButtonStyle.secondary,
        custom_id=f"cart_coupon:{channel_id}:{buyer_id}"))
    action_row.add_item(discord.ui.Button(
        label="🎁 Geschenk", style=discord.ButtonStyle.secondary,
        custom_id=f"cart_gift:{channel_id}:{buyer_id}"))
    action_row.add_item(discord.ui.Button(
        label="🗑️ Leeren", style=discord.ButtonStyle.danger,
        custom_id=f"cart_clear:{channel_id}:{buyer_id}"))
    action_row.add_item(discord.ui.Button(
        label="✅ Kauf bestätigen & liefern (Team)", style=discord.ButtonStyle.success,
        custom_id=f"cart_checkout:{channel_id}:{buyer_id}",
        disabled=(len(cart) == 0)))

    cont = PrestigeContainer(
        "🛒 Warenkorb",
        cart_text(cart) + "\n\n-# Mengenrabatt: 2 Artikel −10% · 3 Artikel −15% · 4+ Artikel −20%",
        accent=ACCENT_BUY, items=[r for r in add_rows if len(r.children) > 0] + [action_row], footer=False)
    v = discord.ui.LayoutView(timeout=None)
    v.add_item(cont)
    return v


class CouponModal(discord.ui.Modal, title="🏷️ Coupon einlösen"):
    code = discord.ui.TextInput(label="Coupon-Code", placeholder="z. B. SUMMER10", max_length=32)
    def __init__(self, channel_id, buyer_id):
        super().__init__()
        self.channel_id = channel_id
        self.buyer_id = buyer_id
    async def on_submit(self, interaction: discord.Interaction):
        code = str(self.code.value).upper().strip()
        pct = db.coupon_get(code)
        if not pct:
            aff = db.affiliate_get(code)
            if not aff:
                return await interaction.response.send_message("❌ Ungültiger Coupon oder Partnercode.", ephemeral=True)
        db.cart_set_coupon(self.channel_id, code)
        await interaction.response.send_message(f"✅ Code `{code}` angewendet! Bitte aktualisiere den Warenkorb mit einem Klick.", ephemeral=True)


class GiftModal(discord.ui.Modal, title="🎁 Als Geschenk kaufen"):
    friend = discord.ui.TextInput(label="User-ID oder Name des Freundes", placeholder="z. B. 123456789012345678 oder Name", max_length=64)
    def __init__(self, channel_id, buyer_id):
        super().__init__()
        self.channel_id = channel_id
        self.buyer_id = buyer_id
    async def on_submit(self, interaction: discord.Interaction):
        friend_val = str(self.friend.value).strip()
        db.cart_set_gift(self.channel_id, friend_val)
        await interaction.response.send_message(f"🎁 Als Geschenk markiert für: **{friend_val}**! Nach Zahlungsauslösung erhält dein Freund die Lieferung per DM.", ephemeral=True)


async def handle_cart_interaction(interaction: discord.Interaction):
    """Wird aus on_interaction für cart_* custom_ids aufgerufen."""
    cid = interaction.data.get("custom_id", "")
    parts = cid.split(":")
    action = parts[0]
    channel_id, buyer_id = parts[1], parts[2]

    if action == "cart_add":
        product_key = parts[3]
        if not db.is_product_active(product_key):
            return await interaction.response.send_message("❌ Dieses Produkt ist aktuell deaktiviert.", ephemeral=True)
        if not db.is_unlimited(product_key) and db.stock_count(product_key) <= 0:
            return await interaction.response.send_message(
                f"❌ {PRODUCTS[product_key]['name']} ist leider ausverkauft.", ephemeral=True)
        db.cart_add(channel_id, product_key)
        await interaction.response.edit_message(view=build_cart_view(channel_id, buyer_id))

    elif action == "cart_coupon":
        await interaction.response.send_modal(CouponModal(channel_id, buyer_id))

    elif action == "cart_gift":
        await interaction.response.send_modal(GiftModal(channel_id, buyer_id))

    elif action == "cart_clear":
        db.cart_clear(channel_id)
        await interaction.response.edit_message(view=build_cart_view(channel_id, buyer_id))

    elif action == "cart_checkout":
        if not is_staff(interaction.user):
            return await interaction.response.send_message(
                "❌ Nur das Team kann den Kauf bestätigen!", ephemeral=True)
        cart = db.get_cart(channel_id)
        if not cart:
            return await interaction.response.send_message("❌ Warenkorb ist leer.", ephemeral=True)
        await deliver_cart(interaction, channel_id, buyer_id, cart)


async def deliver_cart(interaction, channel_id, buyer_id, cart):
    """Liefert ALLE Produkte im Warenkorb (mehrere Keys) per DM."""
    guild = interaction.guild
    buyer = guild.get_member(int(buyer_id)) if guild else None
    order_id = db.next_order_number()
    delivered, missing = [], []
    keys_for_dm = []

    for product_key in cart:
        key = db.claim_key(product_key, buyer_id, buyer.name if buyer else str(buyer_id))
        if key:
            delivered.append(product_key)
            # Unlimited-Produkte brauchen keinen echten Key
            if key != "__UNLIMITED__":
                keys_for_dm.append((PRODUCTS[product_key], key))
        else:
            missing.append(PRODUCTS[product_key]["name"])

    coupon_code = db.cart_get_coupon(channel_id)
    s = cart_summary(cart, coupon_code)
    dm_ok = False
    if buyer and delivered:
        try:
            key_block = "\n".join(
                f"{p['emoji']} **{p['name']}**\n```\n{k}\n```" for p, k in keys_for_dm)
            if not key_block:
                delivered_names = "\n".join(f"{PRODUCTS[k]['emoji']} **{PRODUCTS[k]['name']}**" for k in delivered)
                key_block = delivered_names + "\n-# Dieses Produkt ist auf Unlimited gesetzt und benötigt keinen Key."
            custom_dm_blocks = []
            overrides = db.get_product_overrides()
            for pk in set(delivered):
                ov_txt = overrides.get(pk, {}).get("delivery_msg", "").strip()
                if ov_txt: custom_dm_blocks.append(f"📌 **Dateien / Setup für {PRODUCTS[pk]['name']}:**\n{ov_txt}")
            extra_dm_str = "\n\n".join(custom_dm_blocks) + "\n\n" if custom_dm_blocks else ""
            dm_cont = PrestigeContainer(
                "🧾 𝗩𝗢𝗜𝗗 • Receipt & Lieferung",
                f"**Bestellnummer:** `{order_id}`\n"
                f"**Gesamt:** `{s['total']} R$ / {s['total']*0.01:.2f} €`\n"
                f"**Datum:** {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n"
                f"{key_block}\n\n{extra_dm_str}Bewahre deine Lieferung sicher auf!\n\n"
                "-# Powered by 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • Auto-Delivery",
                accent=ACCENT_BUY, footer=False)
            dv = discord.ui.LayoutView(timeout=None); dv.add_item(dm_cont)
            await buyer.send(view=dv)
            dm_ok = True
        except Exception:
            dm_ok = False
        try:
            cust = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • Customer")
            if cust and cust not in buyer.roles:
                await buyer.add_roles(cust)
        except Exception:
            pass

    # Verkäufe protokollieren
    for product_key in delivered:
        p = PRODUCTS[product_key]
        db.log_sale(product_key, p["name"], buyer_id, buyer.name if buyer else str(buyer_id), p["robux"], order_id=order_id)
    db.cart_clear(channel_id)

    if coupon_code and db.affiliate_get(coupon_code):
        db.affiliate_reward(coupon_code, s['total'])

    gift_friend_str = db.cart_get_gift(channel_id)
    if gift_friend_str and guild:
        friend_mem = None
        if gift_friend_str.isdigit(): friend_mem = guild.get_member(int(gift_friend_str))
        if not friend_mem: friend_mem = discord.utils.get(guild.members, name=gift_friend_str)
        if friend_mem:
            try:
                gcont = PrestigeContainer(
                    "🎁 PRESTIGE GESCHENK ERHALTEN!",
                    f"🎉 **@{buyer.name if buyer else buyer_id}** hat dir ein exklusives Geschenk aus dem **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** zugesendet!\n\n**Bestellnummer:** `{order_id}`\n{key_block}\n\nViel Spaß mit deinen Prestige-Produkten!",
                    accent=ACCENT_PARTNER, footer=False)
                gv = discord.ui.LayoutView(timeout=None); gv.add_item(gcont)
                await friend_mem.send(view=gv)
            except Exception: pass

    missing_txt = f"\n⚠️ Ausverkauft (nicht geliefert): {', '.join(missing)}" if missing else ""
    dm_status = "✅ Keys per DM zugestellt" if dm_ok else "⚠️ DM fehlgeschlagen — Keys im Ticket-Log"
    cont = PrestigeContainer(
        "🎉 Bestellung abgeschlossen!",
        f"**Bestellnummer:** `{order_id}`\n"
        f"**Käufer:** <@{buyer_id}>\n"
        f"**Artikel:** {len(delivered)}\n"
        f"**Gesamt:** `{s['total']} R$ / {s['total']*0.01:.2f} €`\n"
        f"**Lieferung:** {dm_status}{missing_txt}\n\n"
        "Customer-Rolle vergeben. Danke für deinen Einkauf! ⭐",
        accent=ACCENT_BUY)
    v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
    await interaction.response.send_message(view=v)
    await send_ticket_log(guild, PrestigeContainer(
        "📦 Warenkorb-Lieferung",
        f"**Bestellnummer:** `{order_id}`\n**Käufer:** <@{buyer_id}>\n**Artikel:** {len(delivered)}\n**Umsatz:** `{s['total']} R$`",
        accent=ACCENT))
    for product_key in set(delivered):
        await warn_low_stock(guild, product_key)


class PaymentStatusView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        row = discord.ui.ActionRow()
        for label, status, style in [
            ("💳 Zahlung offen", "offen", discord.ButtonStyle.secondary),
            ("✅ Zahlung erhalten", "erhalten", discord.ButtonStyle.success),
            ("📦 Lieferung erfolgt", "geliefert", discord.ButtonStyle.primary),
        ]:
            b = discord.ui.Button(label=label, style=style, custom_id=f"paystatus:{status}")
            row.add_item(b)
        cont = PrestigeContainer("💳 Payment-Status", "Team kann hier den Zahlungs-/Lieferstatus setzen.", accent=ACCENT_BUY, items=[row], footer=False)
        self.add_item(cont)


class ProductChoiceView(discord.ui.LayoutView):
    """Schritt 2 (ephemeral): Welches Produkt will der Kunde kaufen?
    Reine Button-Auswahl — der Kunde tippt NICHTS selbst."""
    def __init__(self):
        super().__init__(timeout=180)
        rows = [discord.ui.ActionRow(), discord.ui.ActionRow()]
        for idx, key in enumerate(PRODUCT_ORDER):
            p = PRODUCTS[key]
            stock = db.stock_count(key)
            unlimited = db.is_unlimited(key)
            disabled = (not db.is_product_active(key)) or (not unlimited and stock <= 0)
            label = f"{p['name']}"
            b = discord.ui.Button(
                label=label,
                emoji=p["emoji"],
                style=discord.ButtonStyle.success if not disabled else discord.ButtonStyle.secondary,
                disabled=disabled,
            )
            b.callback = self._make_cb(key)
            rows[0 if idx < 3 else 1].add_item(b)

        # Produkt-Liste mit Preisen + Lagerstatus als Text
        lines = ["Welches Produkt möchtest du kaufen? Wähle unten per Klick:\n"]
        for key in PRODUCT_ORDER:
            p = PRODUCTS[key]
            if db.is_unlimited(key):
                stock_txt = "🟣 ∞ unlimited"
            else:
                stock = db.stock_count(key)
                stock_txt = f"🟢 {stock} auf Lager" if stock > 0 else "🔴 Ausverkauft"
            lines.append(f"{p['emoji']} **{p['name']}** — `{p['price']}`  ·  {stock_txt}")

        cont = PrestigeContainer(
            "🛒 Produkt auswählen",
            "\n".join(lines),
            accent=ACCENT_BUY, items=[r for r in rows if len(r.children) > 0], footer=False)
        self.add_item(cont)

    def _make_cb(self, product_key):
        async def cb(interaction: discord.Interaction):
            # Ticket mit gewähltem Produkt erstellen
            await TicketButton().create_custom_ticket(
                interaction, "🛒│kauf", "Kauf-Anfrage", product_key=product_key)
        return cb


class TicketSelect(discord.ui.Select):
    """Schritt 1: Genau 3 Anliegen — Kaufen, Support/Fragen, Partnerschaft."""
    def __init__(self):
        options = [
            discord.SelectOption(label="Produkt kaufen", description="Wähle danach dein Produkt aus",
                                 emoji="🛒", value="buy"),
            discord.SelectOption(label="Fragen / Support", description="Technische Hilfe & Fragen",
                                 emoji="⚙️", value="support"),
            discord.SelectOption(label="Partnerschaft", description="Für Kooperationen",
                                 emoji="🤝", value="partner"),
        ]
        super().__init__(placeholder="🎫 Wähle dein Anliegen...", min_values=1, max_values=1,
                         options=options, custom_id="select_ticket_type")

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        view: "TicketButton" = self.view
        if choice == "buy":
            # Schritt 2: erst Produkt auswählen (ephemeral, nur Buttons)
            await interaction.response.send_message(view=ProductChoiceView(), ephemeral=True)
        elif choice == "support":
            await view.create_custom_ticket(interaction, "⚙️│support", "Fragen / Support")
        elif choice == "partner":
            await view.create_custom_ticket(interaction, "🤝│partner", "Partnerschafts-Anfrage")


TICKET_PANEL_TITLE = "🎟️ 𝗩𝗢𝗜𝗗 • Support & Kauf-Center"


def ticket_panel_body() -> str:
    """Dynamischer Text fürs Ticket-Panel, damit Stock/Unlimited aktuell ist."""
    return (
        "Willkommen im **Premium Support-Center** von **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**!\n"
        "Hier kannst du privat ein Ticket öffnen. Wähle unten aus, ob du kaufen, Support brauchst oder eine Partnerschaft anfragen möchtest.\n\n"
        "**🛒 Kaufen:** Wähle danach eines unserer 6 Produkte aus. Im Ticket bekommst du einen Warenkorb mit Mengenrabatt.\n"
        "**⚙️ Support:** Fragen, technische Hilfe, Setup-Probleme oder Beratung.\n"
        "**🤝 Partner:** Kooperationen, Werbung und Server-Partnerschaften.\n\n"
        + product_catalog_text() +
        "\n\n-# Hinweis: Unlimited-Produkte brauchen keinen Lizenz-Key. Normale Produkte werden nach Zahlung automatisch geliefert."
    )


class TicketButton(discord.ui.LayoutView):
    """Components-V2 Ticket-Panel (persistent)."""
    def __init__(self):
        super().__init__(timeout=None)
        cont = PrestigeContainer(TICKET_PANEL_TITLE, ticket_panel_body(),
                                 accent=ACCENT, items=[TicketSelect()])
        self.add_item(cont)

    async def create_custom_ticket(self, interaction, prefix, ticket_type, product_key=None):
        guild, member = interaction.guild, interaction.user

        # Response-sicher (Kauf-Flow hat evtl. schon geantwortet)
        async def _reply(msg):
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)

        if not guild:
            return await _reply("Nur auf einem Server nutzbar.")
        blocked = db.blacklist_get(member.id)
        if blocked:
            return await _reply(f"❌ Du bist für Tickets gesperrt. Grund: {blocked.get('reason','kein Grund')}")

        # bereits offenes Ticket dieses Typs?
        for ch in guild.text_channels:
            if ch.topic and f"creator:{member.id}" in ch.topic and prefix.split("│")[1] in ch.name:
                return await _reply(f"❌ Du hast bereits ein offenes Ticket: {ch.mention}")

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        num = db.next_ticket_number()
        channel_name = f"{prefix}-{num:04d}"

        staff_roles = [r for r in get_roles(guild, STAFF_ROLE_NAMES) if r]
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True,
                                                attach_files=True, embed_links=True,
                                                add_reactions=True, read_message_history=True),
        }
        for role in staff_roles:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        category_name = SUPPORT_CATEGORY
        if ticket_type == "Kauf-Anfrage":
            category_name = BUY_CATEGORY
        elif ticket_type == "Partnerschafts-Anfrage":
            category_name = PARTNER_CATEGORY
        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            try:
                category = await guild.create_category(category_name)
            except Exception:
                category = None

        try:
            channel = await guild.create_text_channel(
                name=channel_name, category=category, overwrites=overwrites,
                topic=f"{ticket_type} | creator:{member.id}")

            # --- Ticket-Inhalt je nach Typ ---
            accent = ACCENT_SUPPORT
            if ticket_type == "Kauf-Anfrage":
                accent = ACCENT_BUY
                past_purchases = db.get_purchase_count(member.id)
                welcome_back = f"🎉 **Willkommen zurück — du hast bereits {past_purchases} Käufe.**\n\n" if past_purchases > 0 else ""
                vip_level = "🥉 Bronze Buyer" if past_purchases >= 1 else "Standard Buyer"
                if past_purchases >= 10: vip_level = "💎 Diamond Buyer"
                elif past_purchases >= 5: vip_level = "🥇 Gold Buyer"
                elif past_purchases >= 3: vip_level = "🥈 Silver Buyer"
                vip_line = f"🏅 **VIP-Level:** `{vip_level}`\n\n"

                prod_line = ""
                if product_key and product_key in PRODUCTS:
                    p = PRODUCTS[product_key]
                    stock_txt = "∞ unlimited" if db.is_unlimited(product_key) else f"{db.stock_count(product_key)} auf Lager"
                    key_txt = "Nein" if db.is_unlimited(product_key) else "Ja"
                    prod_line = (f"**Dein gewähltes Produkt:**\n"
                                 f"{p['emoji']} **{p['name']}** — `{p['price']}`\n"
                                 f"**Beschreibung:** {p['desc']}\n"
                                 f"**Lager:** `{stock_txt}`\n"
                                 f"**Key nötig:** `{key_txt}`\n"
                                 f"**Lieferart:** `DM oder Ticket nach Bestätigung`\n\n")
                body = (
                    f"👋 **Willkommen, {member.mention}!**\n"
                    f"{vip_line}{welcome_back}"
                    "Danke für dein Interesse an **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**. Unser Team ist gleich für dich da!\n\n"
                    f"{prod_line}"
                    "📌 **Bitte teile uns mit:**\n"
                    "🤖 **Roblox Username:**\n"
                    "💳 **Zahlungsart:** *(PayPal · Robux · Paysafecard · Krypto)*\n\n"
                    "⏳ *Ein Teammitglied übernimmt dein Ticket und bestätigt deinen Kauf — "
                    "danach erhältst du deinen Key automatisch per DM!*")
            elif ticket_type == "Fragen / Support":
                body = (
                    f"👋 **Willkommen, {member.mention}!**\n"
                    "Schildere dein Problem so genau wie möglich.\n\n"
                    "📌 **Häufige Themen:**\n"
                    "🚀 Installation & Nutzung aller 6 Produkte\n"
                    "💉 FFlags Injector / FastFlags Setup\n"
                    "🛡️ Anti-Ban Aktivierung\n"
                    "👕 Templates & Downloads\n\n"
                    "⏳ *Ein Supporter widmet sich dir in Kürze.*")
            else:
                accent = ACCENT_PARTNER
                body = (
                    f"🤝 **Partnerschafts-Anfrage von {member.mention}**\n"
                    "Schön, dass du mit **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** kooperieren möchtest!\n\n"
                    "📌 **Bitte nenne uns:**\n"
                    "🔗 **Server-Thema:**\n"
                    "👥 **Mitgliederanzahl:**\n"
                    "📍 **Dauerhafter Invite-Link:**\n\n"
                    "⏳ *Die Projektleitung meldet sich.*")

            # Header-Container + Steuerleiste
            header = PrestigeContainer(
                f"⚡ TICKET #{num:04d} • {ticket_type.upper()}",
                body, accent=accent, author=member, footer=True)
            header_view = discord.ui.LayoutView(timeout=None)
            header_view.add_item(header)

            pings = " ".join(r.mention for r in staff_roles[:4])
            mention_text = f"{member.mention} {pings}".strip()
            if mention_text:
                await channel.send(content=mention_text)
            await channel.send(view=header_view)
            await channel.send(view=CloseTicketView())
            if ticket_type == "Kauf-Anfrage":
                await channel.send(view=PaymentStatusView())

            # Ticket-Timing für Statistik starten
            db.ticket_open(channel.id)

            # Bei Kauf-Ticket: Warenkorb starten (mit vorgewähltem Produkt) + Cart-Panel
            if ticket_type == "Kauf-Anfrage" and product_key in PRODUCTS:
                db.cart_clear(channel.id)
                db.cart_add(channel.id, product_key)
                await channel.send(view=build_cart_view(channel.id, member.id))

            await _reply(f"✅ Dein Ticket wurde erstellt: {channel.mention}")

            db.add_log("ticket", f"Ticket #{num:04d} ({ticket_type}) von {member.name} erstellt")
            await send_ticket_log(guild, PrestigeContainer(
                "🎟️ Ticket erstellt",
                f"**Ticket:** #{num:04d} — {channel.mention}\n"
                f"**Typ:** {ticket_type}\n"
                f"**Ersteller:** {member.mention} ({member.id})"
                + (f"\n**Produkt:** {PRODUCTS[product_key]['name']}" if product_key in PRODUCTS else ""),
                accent=ACCENT))

        except Exception as e:
            logger.error(f"Ticket-Erstellungsfehler: {e}")
            try:
                await _reply("❌ Fehler beim Erstellen des Tickets. Bitte einen Admin kontaktieren.")
            except Exception:
                pass


class TicketsCog(commands.Cog, name="TicketsCog"):
    def __init__(self, bot):
        self.bot = bot
        # Task erst starten, wenn der Bot wirklich initialisiert ist (Tests/offline sicher)
        try:
            if getattr(bot, "loop", None) and not self.auto_close_inactive_tickets.is_running():
                self.auto_close_inactive_tickets.start()
        except Exception:
            pass

    def cog_unload(self):
        self.auto_close_inactive_tickets.cancel()

    @tasks.loop(hours=6)
    async def auto_close_inactive_tickets(self):
        if not self.bot.is_ready():
            return
        import datetime
        now = discord.utils.utcnow()
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if not any(x in channel.name for x in ["kauf-", "support-", "partner-"]):
                    continue
                try:
                    last = None
                    async for msg in channel.history(limit=1):
                        last = msg.created_at
                    if not last:
                        continue
                    if (now - last).total_seconds() >= 48 * 3600:
                        await channel.send("⏳ Dieses Ticket war 48h inaktiv und wird automatisch geschlossen.")
                        await execute_ticket_close_process(channel, guild.me or self.bot.user, self.bot.user)
                except Exception:
                    pass

    @auto_close_inactive_tickets.before_loop
    async def before_auto_close_inactive_tickets(self):
        try:
            await self.bot.wait_until_ready()
        except RuntimeError:
            return


async def trigger_magic_push(bot, user_str, product_key):
    for guild in bot.guilds:
        member = None
        if str(user_str).isdigit(): member = guild.get_member(int(user_str))
        if not member: member = discord.utils.get(guild.members, name=str(user_str))
        if member:
            num = db.next_ticket_number()
            prefix = "🛒│kauf"
            ch_name = f"{prefix}-{num:04d}"
            cat = discord.utils.get(guild.categories, name=BUY_CATEGORY)
            ow = {guild.default_role: discord.PermissionOverwrite(view_channel=False), member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)}
            ch = await guild.create_text_channel(name=ch_name, category=cat, overwrites=ow, topic=f"Kauf-Anfrage | creator:{member.id}")
            p = PRODUCTS.get(product_key, PRODUCTS["infinityxeh"])
            cont = PrestigeContainer(
                f"⚡ MAGIC PUSH KAUFANFRAGE #{num:04d}",
                f"👋 Hallo {member.mention}!\nDu hast über den Web-Store **{p['emoji']} {p['name']}** angefordert.\n\nDas Produkt liegt bereits in deinem Warenkorb:",
                accent=ACCENT_BUY, author=member)
            v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
            await ch.send(content=member.mention, view=v)
            await ch.send(view=CloseTicketView())
            await ch.send(view=PaymentStatusView())
            db.ticket_open(ch.id)
            db.cart_clear(ch.id)
            db.cart_add(ch.id, product_key if product_key in PRODUCTS else "infinityxeh")
            await ch.send(view=build_cart_view(ch.id, member.id))
            return {"status": "success", "channel": ch.name}
    return {"status": "error", "message": "User nicht auf dem Server gefunden"}
