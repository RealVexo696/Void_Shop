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
        "desc": "Premium All-in-One Executor — INFINITY × EH Edition.",
        "value": "infinityxeh",
    },
    "fflags_injector": {
        "name": "FFlags Injector",
        "emoji": "💉",
        "price": "300 R$ / 3,00 €",
        "desc": "Automatischer FastFlag-Injector für maximale FPS & Performance.",
        "value": "fflags_injector",
    },
    "anti_ban": {
        "name": "Anti-Ban",
        "emoji": "🛡️",
        "price": "450 R$ / 4,50 €",
        "desc": "Schutzsystem gegen Bans — sicher & stabil.",
        "value": "anti_ban",
    },
    "fastflags": {
        "name": "FastFlags (Premium Config)",
        "emoji": "🚀",
        "price": "150 R$ / 1,50 €",
        "desc": "Handoptimierte Ultra FastFlag Configs.",
        "value": "fastflags",
    },
    "tshirt": {
        "name": "T-Shirt / Kleidung",
        "emoji": "👕",
        "price": "ab 50 R$ / 0,50 €",
        "desc": "Roblox Kleidungs-Templates & Bundles.",
        "value": "tshirt",
    },
    "template": {
        "name": "Discord Template",
        "emoji": "🖥️",
        "price": "400 R$ / 4,00 €",
        "desc": "Fertiges Premium Discord Shop-Layout.",
        "value": "template",
    },
    "other": {
        "name": "Sonstiges Produkt",
        "emoji": "✨",
        "price": "auf Anfrage",
        "desc": "Etwas anderes? Frag uns einfach im Ticket!",
        "value": "other",
    },
}

# Reihenfolge im Dropdown (neue Produkte zuerst!)
PRODUCT_ORDER = [
    "infinityxeh", "fflags_injector", "anti_ban",
    "fastflags", "tshirt", "template", "other",
]


def product_catalog_text() -> str:
    """Schöner Markdown-Block mit allen Produkten + Preisen."""
    lines = ["### 🛍️ Produkt-Katalog"]
    for key in PRODUCT_ORDER:
        p = PRODUCTS[key]
        lines.append(f"{p['emoji']} **{p['name']}** — `{p['price']}`\n-# {p['desc']}")
    return "\n".join(lines)


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
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="INFINITYxEH", description="Premium Executor kaufen",
                                 emoji="♾️", value="buy:infinityxeh"),
            discord.SelectOption(label="FFlags Injector", description="FPS-Injector kaufen",
                                 emoji="💉", value="buy:fflags_injector"),
            discord.SelectOption(label="Anti-Ban", description="Anti-Ban Schutz kaufen",
                                 emoji="🛡️", value="buy:anti_ban"),
            discord.SelectOption(label="Anderes Produkt kaufen", description="FastFlags, T-Shirts, Templates …",
                                 emoji="🛒", value="buy:other"),
            discord.SelectOption(label="Allgemeiner Support", description="Technische Hilfe & Fragen",
                                 emoji="⚙️", value="support"),
            discord.SelectOption(label="Partnerschaft", description="Für Kooperationen",
                                 emoji="🤝", value="partner"),
        ]
        super().__init__(placeholder="🎫 Wähle dein Anliegen...", min_values=1, max_values=1,
                         options=options, custom_id="select_ticket_type")

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        view: "TicketButton" = self.view
        if choice.startswith("buy:"):
            product_key = choice.split(":", 1)[1]
            await view.create_custom_ticket(interaction, "🛒│kauf", "Kauf-Anfrage", product_key=product_key)
        elif choice == "support":
            await view.create_custom_ticket(interaction, "⚙️│support", "Allgemeiner Support")
        elif choice == "partner":
            await view.create_custom_ticket(interaction, "🤝│partner", "Partnerschafts-Anfrage")


TICKET_PANEL_TITLE = "🎟️ 𝗩𝗢𝗜𝗗 • Support & Kauf-Center"
TICKET_PANEL_BODY = (
    "Willkommen im **Premium Support-Center** von **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**!\n"
    "Wähle unten dein Anliegen — ein Ticket wird sofort & privat für dich erstellt.\n\n"
    "**🔥 Top-Produkte:**\n"
    "♾️ **INFINITYxEH** — `750 R$ / 7,50 €`\n"
    "💉 **FFlags Injector** — `300 R$ / 3,00 €`\n"
    "🛡️ **Anti-Ban** — `450 R$ / 4,50 €`\n\n"
    "⚙️ Support · 🤝 Partnerschaft ebenfalls über das Menü."
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
        if not guild:
            return await interaction.response.send_message("Nur auf einem Server nutzbar.", ephemeral=True)

        # bereits offenes Ticket dieses Typs?
        for ch in guild.text_channels:
            if ch.topic and f"creator:{member.id}" in ch.topic and prefix.split("│")[1] in ch.name:
                return await interaction.response.send_message(
                    f"❌ Du hast bereits ein offenes Ticket: {ch.mention}", ephemeral=True)

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
                    "⏳ *Ein Teammitglied übernimmt dein Ticket gleich über 'Claimen'.*")
            elif ticket_type == "Allgemeiner Support":
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

            # Bei Kauf-Ticket: kompletten Produkt-Katalog anhängen
            if ticket_type == "Kauf-Anfrage":
                cat = PrestigeContainer("🛍️ Unser Sortiment", product_catalog_text(),
                                        accent=ACCENT_BUY, footer=False)
                cv = discord.ui.LayoutView(timeout=None); cv.add_item(cat)
                await channel.send(view=cv)

            await interaction.followup.send(
                f"✅ Dein Ticket wurde erstellt: {channel.mention}", ephemeral=True)

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
                await interaction.followup.send(
                    "❌ Fehler beim Erstellen des Tickets. Bitte einen Admin kontaktieren.", ephemeral=True)
            except Exception:
                pass


class TicketsCog(commands.Cog, name="TicketsCog"):
    def __init__(self, bot):
        self.bot = bot
