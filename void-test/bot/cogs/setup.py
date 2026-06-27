"""
Setup Cog - Kompletter Server-Setup mit verbessertem Rate-Limiting.
Alle Rollen, Kanäle, Berechtigungen und Embeds werden erstellt.
"""

import asyncio
import logging

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db

logger = logging.getLogger("void_shop_bot.setup")


async def safe_role_create(guild, name, color, hoist=True, mentionable=True, reason="VOID Setup", max_retries=5):
    for attempt in range(max_retries):
        try:
            role = await guild.create_role(
                name=name,
                color=discord.Color(color),
                hoist=hoist,
                mentionable=mentionable,
                reason=reason,
            )
            logger.info("Rolle erstellt (%d/%d): %s", attempt + 1, max_retries, name)
            return role
        except discord.HTTPException as e:
            if e.status == 429:
                wait = (e.retry_after if e.retry_after else 5) + (attempt * 1.5)
                logger.warning("Rate-Limit bei Rolle %s, warte %.1fs (Versuch %d/%d)", name, wait, attempt + 1, max_retries)
                await asyncio.sleep(wait)
            else:
                logger.error("HTTPException bei Rolle %s: %s", name, e)
                return None
        except discord.Forbidden as e:
            logger.error("Forbidden bei Rolle %s: %s", name, e)
            return None
        except Exception as e:
            logger.error("Fehler bei Rolle %s: %s", name, e)
            return None
    logger.error("Max Retries erreicht fuer Rolle %s", name)
    return None


async def safe_channel_create(guild, channel_type, name, category=None, overwrites=None, topic=None, reason="VOID Setup", max_retries=5):
    for attempt in range(max_retries):
        try:
            if channel_type == "voice":
                ch = await guild.create_voice_channel(
                    name=name, category=category, overwrites=overwrites or {}, reason=reason
                )
            elif channel_type == "category":
                ch = await guild.create_category(
                    name=name, overwrites=overwrites or {}, reason=reason
                )
            else:
                ch = await guild.create_text_channel(
                    name=name, category=category, overwrites=overwrites or {}, topic=topic or "", reason=reason
                )
            logger.info("Kanal erstellt (%d/%d): %s", attempt + 1, max_retries, name)
            return ch
        except discord.HTTPException as e:
            if e.status == 429:
                wait = (e.retry_after if e.retry_after else 5) + (attempt * 1.5)
                logger.warning("Rate-Limit bei Kanal %s, warte %.1fs (Versuch %d/%d)", name, wait, attempt + 1, max_retries)
                await asyncio.sleep(wait)
            else:
                logger.error("HTTPException bei Kanal %s: %s", name, e)
                return None
        except discord.Forbidden as e:
            logger.error("Forbidden bei Kanal %s: %s", name, e)
            return None
        except Exception as e:
            logger.error("Fehler bei Kanal %s: %s", name, e)
            return None
    logger.error("Max Retries erreicht fuer Kanal %s", name)
    return None


class SetupConfirmationView(View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.value = None

    @discord.ui.button(label="Komplett neu aufsetzen", style=discord.ButtonStyle.danger, emoji="G")
    async def reset_setup(self, interaction, button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "reset"
        self.stop()

    @discord.ui.button(label="Nur hinzufuegen", style=discord.ButtonStyle.success, emoji="+")
    async def add_setup(self, interaction, button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "add"
        self.stop()

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="x")
    async def cancel_setup(self, interaction, button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "cancel"
        self.stop()


class SetupCog(commands.Cog, name="SetupCog"):
    def __init__(self, bot):
        self.bot = bot

    def build_overwrites(self, mode, r_everyone, staff_roles, member_roles, high_staff, r_booster, r_vip, r_member, r_customer, r_premium_buyer):
        ow = {}
        if mode == "stats":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=True, connect=False)

        elif mode == "verify":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
            for r in staff_roles + member_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)

        elif mode == "info":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in staff_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
            for r in member_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)

        elif mode == "community":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in staff_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
            for r in member_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)

        elif mode == "staff":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in member_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=False)
            for r in staff_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        elif mode == "logs":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in member_roles + [r_member, r_booster, r_customer]:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=False)
            for r in high_staff:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        elif mode == "booster_lounge":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in [r_member, r_customer, r_premium_buyer, r_vip]:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=False)
            if r_booster != r_everyone:
                ow[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            for r in staff_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        elif mode == "vip_lounge":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in [r_member, r_customer, r_premium_buyer]:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=False)
            if r_booster != r_everyone:
                ow[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            if r_vip != r_everyone:
                ow[r_vip] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            for r in staff_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        elif mode == "customer_lounge":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            if r_member != r_everyone:
                ow[r_member] = discord.PermissionOverwrite(view_channel=False)
            for r in [r_booster, r_customer, r_premium_buyer, r_vip]:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            for r in staff_roles:
                if r != r_everyone:
                    ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        return ow

    @app_commands.command(name="setup", description="Komplettes Server-Setup: Rollen, Kanaele, Rechte und Embeds")
    @app_commands.choices(modus=[
        app_commands.Choice(name="Komplett neu aufsetzen", value="reset"),
        app_commands.Choice(name="Nur hinzufuegen", value="add"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def setup_command(self, interaction, modus: str):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("Dieser Befehl kann nur auf einem Server genutzt werden.", ephemeral=True)
            return

        bot_member = guild.me

        desc_choice = (
            "Hallo " + interaction.user.mention + ",\n\n"
            "du bist dabei, das **Prestige Server-Layout** fuer **VOID SHOP** aufzubauen.\n"
            "Dieses Setup generiert:\n"
            "> Rollen: **23 Premium-Rollen** mit optimalen Berechtigungen\n"
            "> Kanaele: **10 Kategorien mit insgesamt 42 Kanaelen**\n"
            "> Embeds: **Vollstaendiges Embed-Design in allen Infokanaelen**\n\n"
            "**Gewaelter Modus:** `" + modus + "`\n\n"
            "Bitte bestaetige mit einem der Buttons unten:"
        )

        embed_choice = EmbedHelper.create_prestige_embed(
            title="VOID - SERVER SETUP INITIALISIERUNG",
            description=desc_choice,
            color=0xFF003C,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )

        view = SetupConfirmationView(interaction.user.id)
        await interaction.response.send_message(embed=embed_choice, view=view, ephemeral=True)
        await view.wait()

        if view.value is None or view.value == "cancel":
            embed_cancel = EmbedHelper.create_prestige_embed(
                title="Setup abgebrochen",
                description="> Das Server-Setup wurde abgebrochen. Es wurden keine Aenderungen vorgenommen.",
                color=0x3E3E3E,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await interaction.edit_original_response(embed=embed_cancel, view=None)
            return

        status_embed = EmbedHelper.create_prestige_embed(
            title="Setup-Prozess laeuft...",
            description="> Initialisiere...",
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        status_msg = await interaction.followup.send(embed=status_embed, ephemeral=True, wait=True)

        if modus == "reset":
            await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
                title="Setup-Prozess laeuft...",
                description="> Loeche alte Kanaele...",
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))

            for channel in list(guild.channels):
                try:
                    await channel.delete()
                    await asyncio.sleep(0.8)
                except Exception:
                    pass

            await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
                title="Setup-Prozess laeuft...",
                description="> Loeche alte Rollen...",
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))

            for role in list(guild.roles):
                if role != guild.default_role and not role.managed and role < bot_member.top_role:
                    try:
                        await role.delete()
                        await asyncio.sleep(0.8)
                    except Exception:
                        pass

            await asyncio.sleep(2)

        await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
            title="Setup-Prozess laeuft...",
            description="> **Schritt 1/4:** Erstelle 23 Premium-Rollen...",
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))

        role_definitions = [
            ("BOT", 0x4A00A8),
            ("MEMBER", 0xA0A0A0),
            ("PRODUCT PING", 0x32CD32),
            ("GIVEAWAY PING", 0xFF4500),
            ("ANNOUNCEMENT PING", 0x7289DA),
            ("BRONZE BUYER", 0xCD7F32),
            ("SILVER BUYER", 0xC0C0C0),
            ("GOLD BUYER", 0xFFD700),
            ("DIAMOND BUYER", 0xB9F2FF),
            ("CUSTOMER", 0xFFFF00),
            ("PREMIUM BUYER", 0x00FFFF),
            ("VERIFIED", 0x7F8C8D),
            ("FRIEND", 0xFF69B4),
            ("VIP", 0xFFD700),
            ("BOOSTER", 0xF47FFF),
            ("PARTNER", 0xFFA500),
            ("TRIAL MOD", 0xADFF2F),
            ("SUPPORT", 0x20B2AA),
            ("MODERATOR", 0x39FF14),
            ("MANAGER", 0x00A8A8),
            ("ADMIN", 0x00F0FF),
            ("CO-OWNER", 0xFF3366),
            ("OWNER", 0xFF003C),
        ]

        all_roles = {}
        roles_created = 0
        roles_skipped = 0
        roles_failed = 0
        role_errors = []
        total_roles = len(role_definitions)
        bot_top_role = bot_member.top_role

        for idx, (role_name, color_hex) in enumerate(role_definitions, 1):
            existing = discord.utils.get(guild.roles, name=role_name)
            if existing:
                all_roles[role_name] = existing
                roles_skipped += 1
                continue

            if (idx - 1) % 3 == 0:
                try:
                    await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
                        title="Setup-Prozess laeuft...",
                        description="> **Schritt 1/4:** Erstelle Rollen... (" + str(idx) + "/" + str(total_roles) + ")\n> Aktuell: `" + role_name + "`",
                        color=0x00F0FF,
                        author_user=interaction.user,
                        bot_user=self.bot.user,
                    ))
                except Exception:
                    pass

            result = await safe_role_create(
                guild=guild,
                name=role_name,
                color=color_hex,
                hoist=True,
                mentionable=True,
                reason="VOID Setup",
                max_retries=5,
            )

            if result:
                all_roles[role_name] = result
                roles_created += 1
                try:
                    await result.edit(position=bot_top_role.position - 1 if bot_top_role.position > 0 else 1)
                except Exception:
                    pass
            else:
                roles_failed += 1
                role_errors.append(role_name + ": Erstellung fehlgeschlagen")

            await asyncio.sleep(1.5)

        if roles_created == 0 and roles_skipped == 0:
            error_list = "\n".join(["> " + err for err in role_errors[:10]])
            await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
                title="FEHLER: Keine Rollen erstellt!",
                description=(
                    "> Es konnte **keine einzige Rolle** erstellt werden!\n\n"
                    "**Fehlerdetails:**\n" + error_list + "\n\n"
                    "**So behebst du das:**\n"
                    "1. **Server-Einstellungen** -> **Rollen**\n"
                    "2. Ziehe die Bot-Rolle **ganz nach oben**\n"
                    "3. Gib der Bot-Rolle **Administrator**-Berechtigung\n"
                    "4. Fuehre `/setup` erneut aus"
                ),
                color=0xFF003C,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))
            return

        error_note = ""
        if roles_failed > 0:
            error_note = "\n> **{0} Rollen fehlgeschlagen** (Bot-Rolle hoeher ziehen!)".format(roles_failed)

        await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
            title="Setup-Prozess laeuft...",
            description=(
                "> **Schritt 1/4:** Rollen fertig!\n"
                "> Erstellt: **{0}** | Uebersprungen: **{1}**{2}\n\n"
                "> **Schritt 2/4:** Erstelle Kategorien und Kanaele..."
            ).format(roles_created, roles_skipped, error_note),
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))

        r_everyone = guild.default_role

        def get_role(name):
            return all_roles.get(name, r_everyone)

        r_member = get_role("MEMBER")
        r_customer = get_role("CUSTOMER")
        r_premium_buyer = get_role("PREMIUM BUYER")
        r_vip = get_role("VIP")
        r_booster = get_role("BOOSTER")
        r_partner = get_role("PARTNER")
        r_support = get_role("SUPPORT")
        r_trial_mod = get_role("TRIAL MOD")
        r_mod = get_role("MODERATOR")
        r_manager = get_role("MANAGER")
        r_admin = get_role("ADMIN")
        r_co_owner = get_role("CO-OWNER")
        r_owner = get_role("OWNER")

        staff_roles = [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]
        member_roles = [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]
        high_staff = [r_manager, r_admin, r_co_owner, r_owner]

        def make_cat_overwrites(mode):
            return self.build_overwrites(
                mode, r_everyone, staff_roles, member_roles,
                high_staff, r_booster, r_vip, r_member, r_customer, r_premium_buyer
            )

        categories_layout = [
            {
                "name": "STATS",
                "mode": "stats",
                "channels": [
                    {"name": "Mitglieder: 0", "type": "voice"},
                    {"name": "Booster: 0", "type": "voice"},
                    {"name": "Kunden: 0", "type": "voice"},
                    {"name": "Offene Tickets: 0", "type": "voice"},
                ],
            },
            {
                "name": "VERIFY",
                "mode": "verify",
                "channels": [
                    {"name": "willkommen", "type": "text", "topic": "Begruessungskanal fuer neue Mitglieder"},
                    {"name": "verify-here", "type": "text", "topic": "Klicke unten auf den Button, um dich freizuschalten!"},
                ],
            },
            {
                "name": "INFO",
                "mode": "info",
                "channels": [
                    {"name": "news", "type": "text", "topic": "Wichtige Ankuendigungen und News"},
                    {"name": "rules", "type": "text", "topic": "Das Serverregelwerk"},
                    {"name": "aufwiedersehen", "type": "text", "topic": "Verabschiedungskanal"},
                    {"name": "giveaways", "type": "text", "topic": "Spannende Giveaways und Gewinne"},
                    {"name": "vouches", "type": "text", "topic": "Erfahrungen unserer Kaeufer"},
                    {"name": "invites", "type": "text", "topic": "Lade Freunde ein fuer Belohnungen!"},
                    {"name": "partners", "type": "text", "topic": "Unsere Partner-Server"},
                ],
            },
            {
                "name": "SHOP",
                "mode": "info",
                "channels": [
                    {"name": "tshirt-templates", "type": "text", "topic": "Exklusive T-Shirt Vorlagen fuer Roblox"},
                    {"name": "fastflags", "type": "text", "topic": "FPS und Performance Optimierungen"},
                    {"name": "discord-templates", "type": "text", "topic": "Schicke Discord Server Vorlagen"},
                    {"name": "products", "type": "text", "topic": "Unsere Produkt- und Preisuebersicht"},
                    {"name": "how-to-buy", "type": "text", "topic": "Wie du bei uns einkaufen kannst"},
                    {"name": "updates", "type": "text", "topic": "Entwicklungs-Updates und Produktnews"},
                    {"name": "live-kaeufe", "type": "text", "topic": "Live Feier-Ticker fuer erfolgreiche Shop-Kaeufe"},
                ],
            },
            {
                "name": "CHAT",
                "mode": "community",
                "channels": [
                    {"name": "general-chat", "type": "text", "topic": "Der Hauptchat fuer jedermann"},
                    {"name": "media-and-showcase", "type": "text", "topic": "Teile Bilder, Videos oder Avatare"},
                    {"name": "clothing-showcase", "type": "text", "topic": "Zeige deine eigenen Roblox-Kleidungsdesigns!"},
                    {"name": "setup-showcase", "type": "text", "topic": "Zeige deinen Gaming-Setup oder Studio-Setup"},
                    {"name": "trading", "type": "text", "topic": "Tausche und handle mit Roblox-Gegenstaenden"},
                    {"name": "suggestions", "type": "text", "topic": "Deine Verbesserungsvorschlaege fuer den Shop"},
                    {"name": "bot-commands", "type": "text", "topic": "Nutze die Bot-Befehle hier"},
                ],
            },
            {
                "name": "TALK",
                "mode": "community",
                "channels": [
                    {"name": "Lobby - Public", "type": "voice"},
                    {"name": "Lounge - Chill", "type": "voice"},
                    {"name": "Roblox - Talk", "type": "voice"},
                    {"name": "Gaming - Duo", "type": "voice"},
                    {"name": "Gaming - Squad", "type": "voice"},
                    {"name": "Support - Voice", "type": "voice"},
                ],
            },
            {
                "name": "LOUNGE",
                "mode": "community",
                "channels": [
                    {"name": "booster-lounge", "type": "text", "topic": "Spezialchat fuer Server-Booster", "overwrite_mode": "booster_lounge"},
                    {"name": "vip-lounge", "type": "text", "topic": "Exklusiver Chat fuer VIP-Kunden", "overwrite_mode": "vip_lounge"},
                    {"name": "customer-lounge", "type": "text", "topic": "Austauschbereich fuer alle Kaeufer", "overwrite_mode": "customer_lounge"},
                ],
            },
            {
                "name": "SUPPORT",
                "mode": "info",
                "channels": [
                    {"name": "create-ticket", "type": "text", "topic": "Erstelle ein Support- oder Kauf-Ticket"},
                    {"name": "faq", "type": "text", "topic": "Haeufig gestellte Fragen"},
                ],
            },
            {
                "name": "STAFF",
                "mode": "staff",
                "channels": [
                    {"name": "staff-chat", "type": "text", "topic": "Das interne Besprechungszimmer"},
                    {"name": "mod-commands", "type": "text", "topic": "Eingabe von Admin- und Moderations-Commands"},
                    {"name": "Staff - Voice", "type": "voice"},
                ],
            },
            {
                "name": "LOGS",
                "mode": "logs",
                "channels": [
                    {"name": "voice-logs", "type": "text", "topic": "Logs fuer Sprachkanaele"},
                    {"name": "ban-kick-logs", "type": "text", "topic": "Logs fuer Banns, Kicks und Timeouts"},
                    {"name": "message-logs", "type": "text", "topic": "Logs fuer geloeschte und editierte Nachrichten"},
                    {"name": "invite-logs", "type": "text", "topic": "Logs fuer erstellte und genutzte Einladungslinks"},
                    {"name": "join-leave-logs", "type": "text", "topic": "Logs fuer Serverbeitritte und Austritte"},
                    {"name": "ticket-logs", "type": "text", "topic": "Ticket-Protokolle und Transkripte"},
                    {"name": "system-logs", "type": "text", "topic": "System-Logs fuer Kanaele und Rollen"},
                    {"name": "security-logs", "type": "text", "topic": "Logs fuer blockierte Scam- und Phishing-Links"},
                ],
            },
        ]

        channels_by_name = {}
        channels_created = 0
        total_categories = len(categories_layout)

        for cat_idx, cat_data in enumerate(categories_layout, 1):
            cat_overwrites = make_cat_overwrites(cat_data["mode"])

            try:
                await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
                    title="Setup-Prozess laeuft...",
                    description=(
                        "> **Schritt 1/4:** {0} Rollen erstellt, {1} uebersprungen\n\n"
                        "> **Schritt 2/4:** Erstelle Kanaele... (Kategorie {2}/{3})\n"
                        "> Aktuell: `{4}`"
                    ).format(roles_created, roles_skipped, cat_idx, total_categories, cat_data["name"]),
                    color=0x00F0FF,
                    author_user=interaction.user,
                    bot_user=self.bot.user,
                ))
            except Exception:
                pass

            category = discord.utils.get(guild.categories, name=cat_data["name"])
            if not category:
                category = await safe_channel_create(
                    guild=guild,
                    channel_type="category",
                    name=cat_data["name"],
                    overwrites=cat_overwrites,
                    reason="VOID Setup",
                )
                if not category:
                    await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
                        title="FEHLER: Keine Berechtigung fuer Kanaele!",
                        description=(
                            "> Ich kann keine Kategorien und Kanaele erstellen!\n\n"
                            "**Behebung:**\n"
                            "> 1. Bot-Rolle in den Server-Einstellungen ganz nach oben ziehen\n"
                            "> 2. **Administrator**-Berechtigung aktivieren\n"
                            "> 3. `/setup` erneut ausfuehren"
                        ),
                        color=0xFF003C,
                        author_user=interaction.user,
                        bot_user=self.bot.user,
                    ))
                    return
                await asyncio.sleep(1.2)

            for ch_data in cat_data["channels"]:
                ch_overwrites = make_cat_overwrites(ch_data.get("overwrite_mode", cat_data["mode"]))

                existing = None
                if ch_data["type"] == "voice":
                    existing = discord.utils.get(category.voice_channels, name=ch_data["name"])
                else:
                    existing = discord.utils.get(category.text_channels, name=ch_data["name"])

                if not existing:
                    result = await safe_channel_create(
                        guild=guild,
                        channel_type=ch_data["type"],
                        name=ch_data["name"],
                        category=category,
                        overwrites=ch_overwrites,
                        topic=ch_data.get("topic", ""),
                        reason="VOID Setup",
                    )
                    if result:
                        channels_by_name[ch_data["name"]] = result
                        channels_created += 1
                    await asyncio.sleep(1.0)
                else:
                    channels_by_name[ch_data["name"]] = existing

        await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
            title="Setup-Prozess laeuft...",
            description=(
                "> **Schritt 1/4:** {0} Rollen erstellt, {1} uebersprungen\n"
                "> **Schritt 2/4:** {2} Kanaele erstellt\n"
                "> **Schritt 3/4:** Berechtigungen gesetzt\n\n"
                "> **Schritt 4/4:** Sende Embed-Nachrichten..."
            ).format(roles_created, roles_skipped, channels_created),
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))

        c_ticket_mention = channels_by_name["create-ticket"].mention if "create-ticket" in channels_by_name else "#create-ticket"
        c_ff_mention = channels_by_name["fastflags"].mention if "fastflags" in channels_by_name else "#fastflags"

        c_rules = channels_by_name.get("rules")
        if c_rules:
            embed_rules = EmbedHelper.create_prestige_embed(
                title="VOID SHOP - SERVER REGELN",
                description=(
                    "Um eine sichere, professionelle und angenehme Atmosphaere fuer alle Kunden und Creator zu gewaehrleisten, "
                    "bitten wir dich, die folgenden Richtlinien einzuhalten:\n\n"
                    "1. **Respekt und Hoeflichkeit**\n"
                    "> Behandle jedes Mitglied und jeden Staff mit vollstem Respekt. "
                    "Beleidigungen, Toxizitaet, Belaestigung oder Drohungen jeglicher Art fuehren zum sofortigen Serverausschluss.\n\n"
                    "2. **Kein Spam und Fremdwerbung**\n"
                    "> Spamming in den Kanaelen ist verboten. Das Posten von Werbelinks zu anderen Discord-Servern, "
                    "Dienstleistungen oder Fremdprodukten (sowohl in Chats als auch per DM) wird permanent gebannt.\n\n"
                    "3. **Sicherer und offizieller Handel**\n"
                    "> Jegliche Verkaeufe und Dienstleistungen finden ausschliesslich ueber unser offizielles "
                    "Ticket-System in " + c_ticket_mention + " statt. Privater Handel oder das Anbieten eigener "
                    "Produkte ist untersagt.\n\n"
                    "4. **NSFW und unangemessene Inhalte**\n"
                    "> Keine jugendgefaehrdenden, pornografischen, gewaltverherrlichenden oder illegalen Medien.\n\n"
                    "**Hinweis**\n"
                    "> Mit dem Aufenthalt auf diesem Server akzeptierst du die Discord Nutzungsbedingungen (TOS) "
                    "sowie unsere Serverregeln. Unsere Moderatoren haben das Recht, bei Verstoesen ohne Vorwarnung einzugreifen."
                ),
                color=0xFF003C,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_rules.send(embed=embed_rules)

        c_buy = channels_by_name.get("how-to-buy")
        if c_buy:
            buy_desc = (
                "Der Ablauf eines Einkaufs bei **VOID SHOP** ist vollstaendig automatisiert und absolut sicher. "
                "Folge einfach diesem einfachen Ablauf:\n\n"
                "1. **Ticket erstellen**\n"
                "> Besuche den Kanal " + c_ticket_mention + " und klicke auf den Button **Produkt kaufen**. Ein privater Supportkanal wird nur fuer dich erstellt.\n\n"
                "2. **Produktdetails angeben**\n"
                "> Teile unserem Supportteam im Ticket mit, was du kaufen moechtest "
                "(z.B. Premium FastFlags, bestimmte T-Shirt Templates, Serverlayouts).\n\n"
                "3. **Zahlungsabwicklung**\n"
                "> Waehle deine bevorzugte Zahlungsmethode aus. Wir unterstuetzen:\n"
                "> - PayPal (Familie und Freunde)\n"
                "> - Robux (via Gamepass oder Gruppen-Auszahlung)\n"
                "> - Paysafecard\n"
                "> - Kryptowaehrungen (Litecoin, Bitcoin, USDT)\n\n"
                "4. **Lieferung erhalten**\n"
                "> Nach der Zahlungsbestaetigung wird dein digitales Produkt "
                "(Config, Code, PNG-Datei) direkt im Ticket an dich uebergeben!"
            )
            embed_buy = EmbedHelper.create_prestige_embed(
                title="VOID - WIE KAUFE ICH?",
                description=buy_desc,
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_buy.send(embed=embed_buy)

        c_products = channels_by_name.get("products")
        if c_products:
            embed_products = EmbedHelper.create_prestige_embed(
                title="VOID - UNSERE PRODUKTE",
                description=(
                    "Finde hier deine Roblox- und Discord-Upgrades:\n\n"
                    "**Roblox Kleidung:**\n"
                    "> - *Klassische T-Shirt PNGs:* ab 50 Robux / 0,50 EUR\n"
                    "> - *Exklusive Bundles (50+ Vorlagen):* ab 500 Robux / 5,00 EUR\n\n"
                    "**FastFlags (FPS-Boost):**\n"
                    "> - *Standard-Configs:* Gratis (siehe " + c_ff_mention + ")\n"
                    "> - *Premium Ultra Configs:* 150 Robux / 1,50 EUR\n\n"
                    "**Discord Templates:**\n"
                    "> - *Fertiges Shop-Layout:* 400 Robux / 4,00 EUR"
                ),
                color=0xFFD700,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_products.send(embed=embed_products)

        c_ticket_panel = channels_by_name.get("create-ticket")
        if c_ticket_panel:
            embed_ticket_panel = EmbedHelper.create_prestige_embed(
                title="VOID - Support und Kauf-Center",
                description=(
                    "Benoetigst du Hilfe oder moechtest etwas kaufen?\n"
                    "Waehle einfach die passende Kategorie aus:\n\n"
                    "> **Produkt kaufen** -> Roblox Items, FastFlags, Templates\n"
                    "> **Allgemeiner Support** -> Technische Hilfe\n"
                    "> **Partnerschaft** -> Fuer Kooperationen"
                ),
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            from bot.cogs.tickets import TicketButton
            await c_ticket_panel.send(embed=embed_ticket_panel, view=TicketButton())

        c_faq = channels_by_name.get("faq")
        if c_faq:
            embed_faq = EmbedHelper.create_prestige_embed(
                title="VOID - FAQ (Haeufige Fragen)",
                description=(
                    "**Sind FastFlags erlaubt?**\n"
                    "> Ja, FastFlags sind Teil der offiziellen Roblox-Einstellungen. Es ist keine Cheat-Software!\n\n"
                    "**Wie lange dauert die Lieferung?**\n"
                    "> Fast immer innerhalb von 15 Minuten nach Zahlungseingang im Ticket."
                ),
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_faq.send(embed=embed_faq)

        c_inv = channels_by_name.get("invites")
        if c_inv:
            embed_inv = EmbedHelper.create_prestige_embed(
                title="VOID - Invite Belohnungen",
                description=(
                    "Lade Freunde auf unseren Server ein und staube dicke Gewinne ab:\n\n"
                    "> **5 Invites** -> Gratis T-Shirt Template\n"
                    "> **10 Invites** -> Gratis Premium FastFlags\n"
                    "> **20 Invites** -> Gratis Discord Server-Layout"
                ),
                color=0xFFA500,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_inv.send(embed=embed_inv)

        c_v_here = channels_by_name.get("verify-here")
        if c_v_here:
            embed_v_here = EmbedHelper.create_prestige_embed(
                title="VOID - SERVEREINTRETEN VERIFIZIERUNG",
                description=(
                    "Herzlich Willkommen bei **VOID SHOP**!\n\n"
                    "Um vollen Zugriff auf den Server (Chats, Produkte, Giveaways) zu erhalten, "
                    "musst du dich verifizieren.\n\n"
                    "**So einfach geht's:**\n"
                    "> 1. Klicke unten auf den gruenen Button **Verifizieren**.\n"
                    "> 2. Du erhaeltst sofort die **Member-Rolle** und wirst freigeschaltet.\n\n"
                    "*Hinweis: Fuer erweiterte Kaeufe kannst du zusaetzlich die Roblox-Verifizierung nutzen!*"
                ),
                color=0x39FF14,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            from bot.cogs.verification import SimpleVerifyButton
            await c_v_here.send(embed=embed_v_here, view=SimpleVerifyButton())

        c_vouches = channels_by_name.get("vouches")
        if c_vouches:
            embed_vouch_placeholder = EmbedHelper.create_prestige_embed(
                title="VOID - KUNDEN-BEWERTUNGEN",
                description=(
                    "Kundenzufriedenheit steht bei uns an oberster Stelle!\n\n"
                    "Wenn du bei uns eingekauft hast, wuerden wir uns sehr ueber eine Bewertung freuen. "
                    "Das hilft uns und staerkt das Vertrauen neuer Kunden.\n\n"
                    "**Beispiel fuer eine Bewertung:**\n"
                    "5 Sterne - *Sehr schneller Support, FastFlags funktionieren perfekt "
                    "und habe direkt +120 FPS bekommen! Gerne wieder!*"
                ),
                color=0xFFD700,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_vouches.send(embed=embed_vouch_placeholder)

        stats_cog = self.bot.get_cog("StatsCog")
        if stats_cog:
            await stats_cog.update_stats_channels(guild)

        await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
            title="Server-Setup erfolgreich abgeschlossen!",
            description=(
                "> **Rollen:** {0} erstellt, {1} uebersprungen\n"
                "> **Kanaele:** {2} erstellt\n"
                "> **Rechte:** Hochsicheres Rechtesystem aktiv\n"
                "> **Embeds:** Alle Infos, Regeln, Tickets und Verifikation gesendet\n"
                "> **Tickets:** Interaktive Multi-Tickets einsatzbereit!\n\n"
                "Dein Server ist jetzt komplett fertig!"
            ).format(roles_created, roles_skipped, channels_created),
            color=0x39FF14,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))
