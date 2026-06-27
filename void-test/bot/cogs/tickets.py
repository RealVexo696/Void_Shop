"""
Tickets Cog — 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 (Components V2 Edition)
==================================================================
Komplett neu aufgebautes, hochmodernes Ticket-System.

Features (deutlich verbessert):
  • 100% Discord Components V2 (Container / TextDisplay / ActionRow / Separator)
  • Produkt-Auswahl direkt im Panel-Dropdown (inkl. neuer Produkte:
      1) INFINITYxEH   2) FFlags Injector   3) Anti-Ban)
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
from discord.ext import commands
from discord.ui import Modal, TextInput

from bot.cogs.database import db
from bot.cogs.components_v2 import PrestigeContainer, build_layout

logger = logging.getLogger("void_shop_bot.tickets")

ACCENT = 0x2b2d31
ACCENT_BUY = 0x00d26a       # grün für Kauf
ACCENT_SUPPORT = 0x5865f2   # blurple für Support
ACCENT_PARTNER = 0xffd700   # gold für Partner

SUPPORT_CATEGORY = "🎟️│── 𝗩𝗢𝗜𝗗 • 𝗦Ｕ𝗣𝗣𝗢𝗥𝗧 ──"
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
        "name": "INFINITYxEH",
        "emoji": "♾️",
        "price": "750 R$ / 7,50 €",
        "robux": 750,
        "desc": "Premium All-in-One Executor — INFINITY × EH Edition.",
        "value": "infinityxeh",
        "auto_delivery": True,
    },
    "fflags_injector": {
        "name": "FFlags Injector",
        "emoji": "💉",
        "price": "300 R$ / 3,00 €",
        "robux": 300,
        "desc": "Automatischer FastFlag-Injector für maximale FPS & Performance.",
        "value": "fflags_injector",
        "auto_delivery": True,
    },
    "anti_ban": {
        "name": "Anti-Ban",
        "emoji": "🛡️",
        "price": "1.000 R$ / 10,00 €",
        "robux": 1000,
        "desc": "Schutzsystem gegen Bans — sicher & stabil.",
        "value": "anti_ban",
        "auto_delivery": True,
    },
}

# Reihenfolge im Produkt-Auswahlmenü (Kaufen-Ticket)
PRODUCT_ORDER = ["infinityxeh", "fflags_injector", "anti_ban"]


def product_catalog_text() -> str:
    """Schöner Markdown-Block mit allen Produkten + Preisen."""
    lines = ["### 🛍️ Produkt-Katalog"]
    for key in PRODUCT_ORDER:
        p = PRODUCTS[key]
        lines.append(f"{p['emoji']} **{p['name']}** — `{p['price']}`\n-# {p['desc']}")
    return "\n".join(lines)


# Mengenrabatt-Staffel: ab N Artikeln X% Rabatt
QUANTITY_DISCOUNTS = [(4, 0.20), (3, 0.15), (2, 0.10)]


def cart_summary(cart_keys):
    """Berechnet Warenkorb: Zeilen, Zwischensumme, Rabatt, Endpreis (in Robux)."""
    subtotal = sum(PRODUCTS[k]["robux"] for k in cart_keys if k in PRODUCTS)
    qty = len(cart_keys)
    discount_pct = 0.0
    for threshold, pct in QUANTITY_DISCOUNTS:
        if qty >= threshold:
            discount_pct = pct
            break
    discount_robux = round(subtotal * discount_pct)
    total = subtotal - discount_robux
    # Zeilen mit Anzahl je Produkt
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
    }


def cart_text(cart_keys):
    if not cart_keys:
        return "🛒 Dein Warenkorb ist **leer**. Füge unten Produkte hinzu."
    s = cart_summary(cart_keys)
    out = ["🛒 **Dein Warenkorb:**", ""] + s["lines"] + [""]
    out.append(f"Zwischensumme: `{s['subtotal']} R$`")
    if s["discount_pct"] > 0:
        out.append(f"🎉 Mengenrabatt ({int(s['discount_pct']*100)}%): `−{s['discount_robux']} R$`")
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
            cont = PrestigeContainer(
                "💾 Ticket-Transkript archiviert",
                f"**Ticket:** {channel.name}\n"
                f"**Geschlossen von:** {closed_by_user.mention}\n"
                f"**Nachrichten:** {len(messages)}\n\n"
                "Das vollständige Protokoll ist auch im Web-Dashboard verfügbar.",
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
            disabled=(stock <= 0),
        )
        b_confirm.callback = self._confirm
        row = discord.ui.ActionRow()
        row.add_item(b_confirm)

        stock_txt = f"🟢 {stock} Keys auf Lager" if stock > 0 else "🔴 KEINE Keys auf Lager — bitte mit /addkeys auffüllen!"
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


async def deliver_product(interaction: discord.Interaction, product_key, buyer_id):
    """Zentrale Liefer-Logik: Key ziehen, DM senden, Sale loggen, Rolle vergeben."""
    guild = interaction.guild
    p = PRODUCTS.get(product_key)
    if not p:
        return await interaction.response.send_message("❌ Unbekanntes Produkt.", ephemeral=True)

    key = db.claim_key(product_key, buyer_id, "")
    if not key:
        return await interaction.response.send_message(
            f"❌ Keine Keys mehr für **{p['name']}** im Vorrat! Bitte mit `/addkeys` auffüllen.", ephemeral=True)

    buyer = guild.get_member(int(buyer_id)) if guild else None
    delivered_dm = False
    if buyer:
        try:
            dm_cont = PrestigeContainer(
                "📦 𝗩𝗢𝗜𝗗 • Deine Bestellung wurde geliefert!",
                f"Vielen Dank für deinen Kauf von {p['emoji']} **{p['name']}**!\n\n"
                f"🔑 **Dein Lizenz-Key:**\n```\n{key}\n```\n"
                f"Bewahre ihn sicher auf. Bei Problemen melde dich im Ticket!\n\n"
                "-# Powered by 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • Auto-Delivery",
                accent=ACCENT_BUY, footer=False)
            dv = discord.ui.LayoutView(timeout=None); dv.add_item(dm_cont)
            await buyer.send(view=dv)
            delivered_dm = True
        except Exception:
            delivered_dm = False

        # Customer-Rolle vergeben
        try:
            cust = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • Customer")
            if cust and cust not in buyer.roles:
                await buyer.add_roles(cust)
        except Exception:
            pass

    # Verkauf protokollieren
    db.log_sale(product_key, p["name"], buyer_id, buyer.name if buyer else str(buyer_id), p.get("robux", 0))
    db.add_purchase(buyer.name if buyer else str(buyer_id), p["name"], p.get("robux", 0))

    # Bestätigung im Ticket
    dm_status = "✅ per DM zugestellt" if delivered_dm else "⚠️ DM fehlgeschlagen (DMs aus?) — Key hier:"
    cont = PrestigeContainer(
        "🎉 Kauf bestätigt & geliefert!",
        f"**Produkt:** {p['emoji']} {p['name']}\n"
        f"**Käufer:** <@{buyer_id}>\n"
        f"**Lieferung:** {dm_status}\n"
        + ("" if delivered_dm else f"```\n{key}\n```\n")
        + f"**Restbestand:** {db.stock_count(product_key)} Keys\n\n"
        "Die Customer-Rolle wurde automatisch vergeben. ⭐",
        accent=ACCENT_BUY)
    v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
    await interaction.response.send_message(view=v)
    await send_ticket_log(guild, PrestigeContainer(
        "📦 Auto-Delivery ausgeführt",
        f"**Produkt:** {p['name']}\n**Käufer:** <@{buyer_id}>\n"
        f"**Lieferung:** {'DM' if delivered_dm else 'im Ticket'}\n**Rest:** {db.stock_count(product_key)} Keys",
        accent=ACCENT))


# ==================================================================
# WARENKORB im Kauf-Ticket
# ==================================================================
def build_cart_view(channel_id, buyer_id):
    """Erzeugt die LayoutView mit Warenkorb-Inhalt + Buttons (Add/Clear/Checkout)."""
    cart = db.get_cart(channel_id)

    # Add-Buttons je Produkt
    add_row = discord.ui.ActionRow()
    for key in PRODUCT_ORDER:
        p = PRODUCTS[key]
        b = discord.ui.Button(
            label=f"+ {p['name']}", emoji=p["emoji"],
            style=discord.ButtonStyle.secondary,
            custom_id=f"cart_add:{channel_id}:{buyer_id}:{key}")
        add_row.add_item(b)

    # Aktions-Buttons
    action_row = discord.ui.ActionRow()
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
        accent=ACCENT_BUY, items=[add_row, action_row], footer=False)
    v = discord.ui.LayoutView(timeout=None)
    v.add_item(cont)
    return v


async def handle_cart_interaction(interaction: discord.Interaction):
    """Wird aus on_interaction für cart_* custom_ids aufgerufen."""
    cid = interaction.data.get("custom_id", "")
    parts = cid.split(":")
    action = parts[0]
    channel_id, buyer_id = parts[1], parts[2]

    if action == "cart_add":
        product_key = parts[3]
        if db.stock_count(product_key) <= 0:
            return await interaction.response.send_message(
                f"❌ {PRODUCTS[product_key]['name']} ist leider ausverkauft.", ephemeral=True)
        db.cart_add(channel_id, product_key)
        await interaction.response.edit_message(view=build_cart_view(channel_id, buyer_id))

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
    delivered, missing = [], []
    keys_for_dm = []

    for product_key in cart:
        key = db.claim_key(product_key, buyer_id, buyer.name if buyer else str(buyer_id))
        if key:
            delivered.append(product_key)
            keys_for_dm.append((PRODUCTS[product_key], key))
        else:
            missing.append(PRODUCTS[product_key]["name"])

    s = cart_summary(cart)
    dm_ok = False
    if buyer and keys_for_dm:
        try:
            key_block = "\n".join(
                f"{p['emoji']} **{p['name']}**\n```\n{k}\n```" for p, k in keys_for_dm)
            dm_cont = PrestigeContainer(
                "📦 𝗩𝗢𝗜𝗗 • Deine Bestellung wurde geliefert!",
                f"Vielen Dank für deinen Einkauf! (Gesamt: `{s['total']} R$`)\n\n"
                f"{key_block}\n\nBewahre deine Keys sicher auf!\n\n"
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
        db.log_sale(product_key, p["name"], buyer_id, buyer.name if buyer else str(buyer_id), p["robux"])
    db.cart_clear(channel_id)

    missing_txt = f"\n⚠️ Ausverkauft (nicht geliefert): {', '.join(missing)}" if missing else ""
    dm_status = "✅ Keys per DM zugestellt" if dm_ok else "⚠️ DM fehlgeschlagen — Keys im Ticket-Log"
    cont = PrestigeContainer(
        "🎉 Bestellung abgeschlossen!",
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
        f"**Käufer:** <@{buyer_id}>\n**Artikel:** {len(delivered)}\n**Umsatz:** `{s['total']} R$`",
        accent=ACCENT))


class ProductChoiceView(discord.ui.LayoutView):
    """Schritt 2 (ephemeral): Welches Produkt will der Kunde kaufen?
    Reine Button-Auswahl — der Kunde tippt NICHTS selbst."""
    def __init__(self):
        super().__init__(timeout=180)
        row = discord.ui.ActionRow()
        for key in PRODUCT_ORDER:
            p = PRODUCTS[key]
            stock = db.stock_count(key)
            disabled = stock <= 0
            label = f"{p['name']}"
            b = discord.ui.Button(
                label=label,
                emoji=p["emoji"],
                style=discord.ButtonStyle.success if not disabled else discord.ButtonStyle.secondary,
                disabled=disabled,
            )
            b.callback = self._make_cb(key)
            row.add_item(b)

        # Produkt-Liste mit Preisen + Lagerstatus als Text
        lines = ["Welches Produkt möchtest du kaufen? Wähle unten per Klick:\n"]
        for key in PRODUCT_ORDER:
            p = PRODUCTS[key]
            stock = db.stock_count(key)
            stock_txt = f"🟢 {stock} auf Lager" if stock > 0 else "🔴 Ausverkauft"
            lines.append(f"{p['emoji']} **{p['name']}** — `{p['price']}`  ·  {stock_txt}")

        cont = PrestigeContainer(
            "🛒 Produkt auswählen",
            "\n".join(lines),
            accent=ACCENT_BUY, items=[row], footer=False)
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
TICKET_PANEL_BODY = (
    "Willkommen im **Premium Support-Center** von **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**!\n"
    "Wähle unten dein Anliegen — ein Ticket wird sofort & privat für dich erstellt.\n\n"
    "🛒 **Produkt kaufen** — danach wählst du dein Produkt per Klick aus\n"
    "⚙️ **Fragen / Support** — technische Hilfe & Fragen\n"
    "🤝 **Partnerschaft** — für Kooperationen\n\n"
    "**🔥 Top-Produkte:**\n"
    "♾️ INFINITYxEH · 💉 FFlags Injector · 🛡️ Anti-Ban"
)


class TicketButton(discord.ui.LayoutView):
    """Components-V2 Ticket-Panel (persistent)."""
    def __init__(self):
        super().__init__(timeout=None)
        cont = PrestigeContainer(TICKET_PANEL_TITLE, TICKET_PANEL_BODY,
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

        category = discord.utils.get(guild.categories, name=SUPPORT_CATEGORY)

        try:
            channel = await guild.create_text_channel(
                name=channel_name, category=category, overwrites=overwrites,
                topic=f"{ticket_type} | creator:{member.id}")

            # --- Ticket-Inhalt je nach Typ ---
            accent = ACCENT_SUPPORT
            if ticket_type == "Kauf-Anfrage":
                accent = ACCENT_BUY
                prod_line = ""
                if product_key and product_key in PRODUCTS:
                    p = PRODUCTS[product_key]
                    prod_line = (f"**Dein gewähltes Produkt:**\n"
                                 f"{p['emoji']} **{p['name']}** — `{p['price']}`\n"
                                 f"-# {p['desc']}\n\n")
                body = (
                    f"👋 **Willkommen, {member.mention}!**\n"
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
                    "🚀 Installation & Nutzung der Produkte\n"
                    "💉 FFlags Injector Setup\n"
                    "🛡️ Anti-Ban Aktivierung\n\n"
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
            await channel.send(content=f"{member.mention} {pings}".strip(), view=header_view)
            await channel.send(view=CloseTicketView())

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
