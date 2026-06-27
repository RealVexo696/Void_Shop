"""
Setup Cog - Kompletter Server-Setup.
Original Rollen- und Kanalnamen. 1.0s Pause pro Ressource.
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


async def create_with_retry(guild, coro, name, max_retries=10):
    for attempt in range(max_retries):
        try:
            result = await coro
            logger.info("Erstellt (%d/%d): %s", attempt + 1, max_retries, name)
            return result
        except discord.HTTPException as e:
            if e.status == 429:
                wait = e.retry_after if e.retry_after else 5.0
                logger.warning("Rate-Limit bei %s, warte %.2fs (%d/%d)", name, wait, attempt + 1, max_retries)
                await asyncio.sleep(wait)
            else:
                logger.error("HTTPException bei %s: %s", name, e)
                return None
        except discord.Forbidden as e:
            logger.error("Forbidden bei %s: %s", name, e)
            return None
        except Exception as e:
            logger.error("Fehler bei %s: %s", name, e)
            return None
    logger.error("Max Retries erreicht fuer %s", name)
    return None


class SetupConfirmationView(View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.value = None

    @discord.ui.button(label="Komplett neu aufsetzen", style=discord.ButtonStyle.danger, emoji="\U0001F9F9")
    async def reset_setup(self, interaction, button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "reset"
        self.stop()

    @discord.ui.button(label="Nur hinzufuegen", style=discord.ButtonStyle.success, emoji="\u2795")
    async def add_setup(self, interaction, button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "add"
        self.stop()

    @discord.ui.button(label="Abbrechen", style=discord.ButtonStyle.secondary, emoji="\u274C")
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

    async def safe_edit(self, msg, **kwargs):
        try:
            return await msg.edit(**kwargs)
        except Exception:
            return None

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
            for r in member_roles + [r_support, r_booster, r_customer]:
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

        # SCHRITT 0: RESET
        if modus == "reset":
            await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
                title="Setup-Prozess laeuft...",
                description="> Loeche alte Kanaele...",
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))
            for channel in list(guild.channels):
                try:
                    await channel.delete()
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
            await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
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
                        await asyncio.sleep(0.5)
                    except Exception:
                        pass
            await asyncio.sleep(1)

        # SCHRITT 1: 23 ROLLEN
        await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
            title="Setup-Prozess laeuft...",
            description="> **Schritt 1/4:** Erstelle 23 Premium-Rollen...",
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))

        role_definitions = [
            ("\U0001F916\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D5\U0001D5FC\U0001D5F1", 0x4A00A8),
            ("\U0001F465\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E0\U0001D5F2\U0001D5FA\U0001D5F3\U0001D5F2\U0001D5FF", 0xA0A0A0),
            ("\U0001F4E6\u2502 \U0001D5D4\U0001D5FF\U0001D5FC\U0001D5E1\U0001D5FA\U0001D5F1 \U0001D5D4\U0001D5DE\U0001D5FB\U0001D5D8", 0x32CD32),
            ("\U0001F381\u2502 \U0001D5DA\U0001D5DE\U0001D5F3\U0001D5F2\U0001D5EE\U0001D5EA\U0001D5EC \U0001D5D4\U0001D5DE\U0001D5FB\U0001D5D8", 0xFF4500),
            ("\U0001F4E2\u2502 \U0001D5D4\U0001D5FB\U0001D5FB\U0001D5FC\U0001D5FB\U0001D5F0\U0001D5F2\U0001D5FA\U0001D5F2\U0001D5FB\U0001D5F1 \U0001D5D4\U0001D5DE\U0001D5FB\U0001D5D8", 0x7289DA),
            ("\U0001F949\u2502 \U0001D5D5\U0001D5FF\U0001D5FC\U0001D5FB\U0001D5F9\U0001D5F2 \U0001D5D5\U0001D5FA\U0001D5F6\U0001D5F2\U0001D5FF", 0xCD7F32),
            ("\U0001F948\u2502 \U0001D5E6\U0001D5DE\U0001D5F9\U0001D5F3\U0001D5F2\U0001D5FF \U0001D5D5\U0001D5FA\U0001D5F6\U0001D5F2\U0001D5FF", 0xC0C0C0),
            ("\U0001F947\u2502 \U0001D5DA\U0001D5FC\U0001D5F9\U0001D5E1 \U0001D5D5\U0001D5FA\U0001D5F6\U0001D5F2\U0001D5FF", 0xFFD700),
            ("\U0001F48E\u2502 \U0001D5D7\U0001D5DE\U0001D5D4\U0001D5FA\U0001D5FC\U0001D5FB\U0001D5E1 \U0001D5D5\U0001D5FA\U0001D5F6\U0001D5F2\U0001D5FF", 0xB9F2FF),
            ("\U0001F6D2\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D6\U0001D5FA\U0001D5F0\U0001D5F1\U0001D5FC\U0001D5FA\U0001D5F2\U0001D5FF", 0xFFFF00),
            ("\U0001F48E\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D4\U0001D5FF\U0001D5F2\U0001D5FA\U0001D5DE\U0001D5FA\U0001D5FA \U0001D5D5\U0001D5FA\U0001D5F6\U0001D5F2\U0001D5FF", 0x00FFFF),
            ("\U0001F464\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E9\U0001D5F2\U0001D5FF\U0001D5DE\U0001D5F3\U0001D5F2\U0001D5E1", 0x7F8C8D),
            ("\U0001FAC2\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D9\U0001D5FF\U0001D5DE\U0001D5F2\U0001D5FB\U0001D5E1", 0xFF69B4),
            ("\U0001F31F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E9\U0001D5D7\U0001D5D4", 0xFFD700),
            ("\U0001F48E\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D5\U0001D5FC\U0001D5FC\U0001D5F0\U0001D5F1\U0001D5F2\U0001D5FF", 0xF47FFF),
            ("\U0001F91D\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D4\U0001D5D4\U0001D5FF\U0001D5F1\U0001D5F2\U0001D5FF", 0xFFA500),
            ("\U0001F6A8\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DF\U0001D5FF\U0001D5DE\U0001D5D4\U0001D5F9 \U0001D5DF\U0001D5FC\U0001D5E1", 0xADFF2F),
            ("\U0001F3AB\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E6\U0001D5FA\U0001D5FD\U0001D5FD\U0001D5FC\U0001D5FF\U0001D5F1", 0x20B2AA),
            ("\U0001F6E1\uFE0F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DF\U0001D5FC\U0001D5E1\U0001D5F2\U0001D5FF\U0001D5D4\U0001D5F1\U0001D5FC\U0001D5FF", 0x39FF14),
            ("\u2699\uFE0F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DF\U0001D5D4\U0001D5FB\U0001D5D4\U0001D5D8\U0001D5F2\U0001D5FF", 0x00A8A8),
            ("\U0001F6E0\uFE0F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D4\U0001D5E1\U0001D5FA\U0001D5DE\U0001D5FB", 0x00F0FF),
            ("\U0001F451\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D6\U0001D5FC-\U0001D5E2\U0001D5EA\U0001D5FB\U0001D5F2\U0001D5FF", 0xFF3366),
            ("\U0001F451\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E2\U0001D5EA\U0001D5FB\U0001D5F2\U0001D5FF", 0xFF003C),
        ]

        all_roles = {}
        roles_created = 0
        roles_skipped = 0
        roles_failed = 0
        role_errors = []
        total_roles = len(role_definitions)

        for idx, (role_name, color_hex) in enumerate(role_definitions, 1):
            existing = discord.utils.get(guild.roles, name=role_name)
            if existing:
                all_roles[role_name] = existing
                roles_skipped += 1
                await asyncio.sleep(1.0)
                continue

            if idx % 4 == 0:
                await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
                    title="Setup-Prozess laeuft...",
                    description="> **Schritt 1/4:** Erstelle Rollen... (" + str(idx) + "/" + str(total_roles) + ")\n> Aktuell: `" + role_name + "`",
                    color=0x00F0FF,
                    author_user=interaction.user,
                    bot_user=self.bot.user,
                ))

            result = await create_with_retry(
                guild=guild,
                coro=guild.create_role(
                    name=role_name,
                    color=discord.Color(color_hex),
                    hoist=True,
                    mentionable=True,
                    reason="VOID Setup",
                ),
                name=role_name,
                max_retries=10,
            )

            if result:
                all_roles[role_name] = result
                roles_created += 1
            else:
                roles_failed += 1
                role_errors.append(role_name + ": Erstellung fehlgeschlagen")

            await asyncio.sleep(1.0)

        if roles_created == 0 and roles_skipped == 0:
            error_list = "\n".join(["> " + err for err in role_errors[:10]])
            await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
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
            error_note = "\n> **{0} Rollen fehlgeschlagen**".format(roles_failed)

        await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
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

        # SCHRITT 2: ROLLEN-REFERENZEN
        r_everyone = guild.default_role

        def get_role(name):
            return all_roles.get(name, r_everyone)

        r_member = get_role("\U0001F465\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E0\U0001D5F2\U0001D5FA\U0001D5F3\U0001D5F2\U0001D5FF")
        r_customer = get_role("\U0001F6D2\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D6\U0001D5FA\U0001D5F0\U0001D5F1\U0001D5FC\U0001D5FA\U0001D5F2\U0001D5FF")
        r_premium_buyer = get_role("\U0001F48E\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D4\U0001D5FF\U0001D5F2\U0001D5FA\U0001D5DE\U0001D5FA\U0001D5FA \U0001D5D5\U0001D5FA\U0001D5F6\U0001D5F2\U0001D5FF")
        r_vip = get_role("\U0001F31F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E9\U0001D5D7\U0001D5D4")
        r_booster = get_role("\U0001F48E\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D5\U0001D5FC\U0001D5FC\U0001D5F0\U0001D5F1\U0001D5F2\U0001D5FF")
        r_partner = get_role("\U0001F91D\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D4\U0001D5D4\U0001D5FF\U0001D5F1\U0001D5F2\U0001D5FF")
        r_support = get_role("\U0001F3AB\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E6\U0001D5FA\U0001D5FD\U0001D5FD\U0001D5FC\U0001D5FF\U0001D5F1")
        r_trial_mod = get_role("\U0001F6A8\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DF\U0001D5FF\U0001D5DE\U0001D5D4\U0001D5F9 \U0001D5DF\U0001D5FC\U0001D5E1")
        r_mod = get_role("\U0001F6E1\uFE0F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DF\U0001D5FC\U0001D5E1\U0001D5F2\U0001D5FF\U0001D5D4\U0001D5F1\U0001D5FC\U0001D5FF")
        r_manager = get_role("\u2699\uFE0F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DF\U0001D5D4\U0001D5FB\U0001D5D4\U0001D5D8\U0001D5F2\U0001D5FF")
        r_admin = get_role("\U0001F6E0\uFE0F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D4\U0001D5E1\U0001D5FA\U0001D5DE\U0001D5FB")
        r_co_owner = get_role("\U0001F451\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D6\U0001D5FC-\U0001D5E2\U0001D5EA\U0001D5FB\U0001D5F2\U0001D5FF")
        r_owner = get_role("\U0001F451\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E2\U0001D5EA\U0001D5FB\U0001D5F2\U0001D5FF")

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
                "name": "\U0001F4CA\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E6\U0001D5DF\U0001D5D4\U0001D5DF\U0001D5E6 \U2500\u2500",
                "mode": "stats",
                "channels": [
                    {"name": "\U0001F465\u2502Mitglieder: 0", "type": "voice"},
                    {"name": "\U0001F48E\u2502Booster: 0", "type": "voice"},
                    {"name": "\U0001F6D2\u2502Kunden: 0", "type": "voice"},
                    {"name": "\U0001F39F\uFE0F\u2502Offene Tickets: 0", "type": "voice"},
                ],
            },
            {
                "name": "\U0001F510\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E9\U0001D5D8\U0001D5E5\U0001D5D7\U0001D5D9\U0001D5EC \U2500\u2500",
                "mode": "verify",
                "channels": [
                    {"name": "\U0001F44B\u2502willkommen", "type": "text", "topic": "Begruessungskanal fuer neue Mitglieder"},
                    {"name": "\U0001F510\u2502verify-here", "type": "text", "topic": "Klicke unten auf den Button, um dich freizuschalten!"},
                ],
            },
            {
                "name": "\U0001F4E2\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DC\U0001D5E0\U0001D5D9\U0001D5E2 \U2500\u2500",
                "mode": "info",
                "channels": [
                    {"name": "\U0001F4E2\u2502news", "type": "text", "topic": "Wichtige Ank\u00fcndigungen & News"},
                    {"name": "\U0001F4DC\u2502rules", "type": "text", "topic": "Das Serverregelwerk"},
                    {"name": "\U0001F4A8\u2502aufwiedersehen", "type": "text", "topic": "Verabschiedungskanal"},
                    {"name": "\U0001F381\u2502giveaways", "type": "text", "topic": "Spannende Giveaways & Gewinne"},
                    {"name": "\U0001F91D\u2502vouches", "type": "text", "topic": "Erfahrungen unserer K\u00e4ufer"},
                    {"name": "\U0001F4E9\u2502invites", "type": "text", "topic": "Lade Freunde ein f\u00fcr Belohnungen!"},
                    {"name": "\U0001F517\u2502partners", "type": "text", "topic": "Unsere Partner-Server"},
                ],
            },
            {
                "name": "\U0001F6D2\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E6\U0001D5DB\U0001D5E2\U0001D5E3 \U2500\u2500",
                "mode": "info",
                "channels": [
                    {"name": "\U0001F455\u2502tshirt-templates", "type": "text", "topic": "Exklusive T-Shirt Vorlagen f\u00fcr Roblox"},
                    {"name": "\u2699\uFE0F\u2502fastflags", "type": "text", "topic": "FPS & Performance Optimierungen"},
                    {"name": "\U0001F5A5\uFE0F\u2502discord-templates", "type": "text", "topic": "Schicke Discord Server Vorlagen"},
                    {"name": "\U0001F4E6\u2502products", "type": "text", "topic": "Unsere Produkt- & Preis\u00fcbersicht"},
                    {"name": "\U0001F6D2\u2502how-to-buy", "type": "text", "topic": "Wie du bei uns einkaufen kannst"},
                    {"name": "\U0001F4C8\u2502updates", "type": "text", "topic": "Entwicklungs-Updates & Produktnews"},
                    {"name": "\U0001F6CD\uFE0F\u2502live-k\u00e4ufe", "type": "text", "topic": "Live Feier-Ticker f\u00fcr erfolgreiche Shop-K\u00e4ufe"},
                ],
            },
            {
                "name": "\U0001F4AC\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5D6\U0001D5DB\U0001D5D4\U0001D5DF \U2500\u2500",
                "mode": "community",
                "channels": [
                    {"name": "\U0001F4AC\u2502general-chat", "type": "text", "topic": "Der Hauptchat f\u00fcr jedermann"},
                    {"name": "\U0001F4F7\u2502media-and-showcase", "type": "text", "topic": "Teile Bilder, Videos oder Avatare"},
                    {"name": "\U0001F3A8\u2502clothing-showcase", "type": "text", "topic": "Zeige deine eigenen Roblox-Kleidungsdesigns!"},
                    {"name": "\U0001F5A5\uFE0F\u2502setup-showcase", "type": "text", "topic": "Zeige deinen Gaming-Setup oder Studio-Setup"},
                    {"name": "\U0001F4C8\u2502trading", "type": "text", "topic": "Tausche und handle mit Roblox-Gegenst\u00e4nden"},
                    {"name": "\U0001F91D\u2502suggestions", "type": "text", "topic": "Deine Verbesserungsvorschl\u00e4ge f\u00fcr den Shop"},
                    {"name": "\U0001F916\u2502bot-commands", "type": "text", "topic": "Nutze die Bot-Befehle hier"},
                ],
            },
            {
                "name": "\U0001F399\uFE0F\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DF\U0001D5D4\U0001D5DF\U0001D5D6 \U2500\u2500",
                "mode": "community",
                "channels": [
                    {"name": "\U0001F50A\u2502Lobby \u2022 Public", "type": "voice"},
                    {"name": "\U0001F50A\u2502Lounge \u2022 Chill", "type": "voice"},
                    {"name": "\U0001F50A\u2502Roblox \u2022 Talk", "type": "voice"},
                    {"name": "\U0001F50A\u2502Gaming \u2022 Duo", "type": "voice"},
                    {"name": "\U0001F50A\u2502Gaming \u2022 Squad", "type": "voice"},
                    {"name": "\U0001F50A\u2502Support \u2022 Voice", "type": "voice"},
                ],
            },
            {
                "name": "\U0001F48E\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5DF\U0001D5E2\U0001D5E8\U0001D5E1\U0001D5DA\U0001D5D8 \U2500\u2500",
                "mode": "community",
                "channels": [
                    {"name": "\U0001F48E\u2502booster-lounge", "type": "text", "topic": "Spezialchat f\u00fcr Server-Booster", "overwrite_mode": "booster_lounge"},
                    {"name": "\U0001F31F\u2502vip-lounge", "type": "text", "topic": "Exklusiver Chat f\u00fcr VIP-Kunden", "overwrite_mode": "vip_lounge"},
                    {"name": "\U0001F6D2\u2502customer-lounge", "type": "text", "topic": "Austauschbereich f\u00fcr alle K\u00e4ufer", "overwrite_mode": "customer_lounge"},
                ],
            },
            {
                "name": "\U0001F39F\uFE0F\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E6\U0001D5E8\U0001D5D4\U0001D5D4\U0001D5E2\U0001D5E5\U0001D5DF \U2500\u2500",
                "mode": "info",
                "channels": [
                    {"name": "\U0001F39F\uFE0F\u2502create-ticket", "type": "text", "topic": "Erstelle ein Support- oder Kauf-Ticket"},
                    {"name": "\u2753\u2502faq", "type": "text", "topic": "H\u00e4ufig gestellte Fragen (FAQs)"},
                ],
            },
            {
                "name": "\U0001F512\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \U2022 \U0001D5E6\U0001D5DF\U0001D5D4\U0001D5D9\U0001D5D9 \u2500\u2500",
                "mode": "staff",
                "channels": [
                    {"name": "\U0001F512\u2502staff-chat", "type": "text", "topic": "Das interne Besprechungszimmer"},
                    {"name": "\U0001F6E0\uFE0F\u2502mod-commands", "type": "text", "topic": "Eingabe von Admin- und Moderations-Commands"},
                    {"name": "\U0001F50A\u2502Staff \u2022 Voice", "type": "voice"},
                ],
            },
            {
                "name": "\U0001F4C1\u2502\u2500\u2500 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \u2022 \U0001D5DF\U0001D5E2\U0001D5DA\U0001D5E6 \u2500\u2500",
                "mode": "logs",
                "channels": [
                    {"name": "\U0001F4AC\u2502voice-logs", "type": "text", "topic": "Logs f\u00fcr Sprachkan\u00e4le"},
                    {"name": "\U0001F528\u2502ban-kick-logs", "type": "text", "topic": "Logs f\u00fcr Banns, Kicks und Timeouts"},
                    {"name": "\U0001F4DD\u2502message-logs", "type": "text", "topic": "Logs f\u00fcr gel\u00f6schte & editierte Nachrichten"},
                    {"name": "\U0001F4E9\u2502invite-logs", "type": "text", "topic": "Logs f\u00fcr erstellte & genutzte Einladungslinks"},
                    {"name": "\U0001F4E5\u2502join-leave-logs", "type": "text", "topic": "Logs f\u00fcr Serverbeitritte & Austritte"},
                    {"name": "\U0001F4BE\u2502ticket-logs", "type": "text", "topic": "Ticket-Protokolle & Transkripte"},
                    {"name": "\u2699\uFE0F\u2502system-logs", "type": "text", "topic": "System-Logs f\u00fcr Kan\u00e4le & Rollen"},
                    {"name": "\U0001F6A8\u2502security-logs", "type": "text", "topic": "Logs f\u00fcr blockierte Scam- & Phishing-Links"},
                ],
            },
        ]

        channels_by_name = {}
        channels_created = 0
        total_categories = len(categories_layout)

        for cat_idx, cat_data in enumerate(categories_layout, 1):
            cat_overwrites = make_cat_overwrites(cat_data["mode"])

            await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
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

            category = discord.utils.get(guild.categories, name=cat_data["name"])
            if not category:
                category = await create_with_retry(
                    guild=guild,
                    coro=guild.create_category(
                        name=cat_data["name"],
                        overwrites=cat_overwrites,
                        reason="VOID Setup",
                    ),
                    name=cat_data["name"],
                    max_retries=10,
                )
                if not category:
                    await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
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
                await asyncio.sleep(1.0)

            for ch_data in cat_data["channels"]:
                ch_overwrites = make_cat_overwrites(ch_data.get("overwrite_mode", cat_data["mode"]))

                existing = None
                if ch_data["type"] == "voice":
                    existing = discord.utils.get(category.voice_channels, name=ch_data["name"])
                else:
                    existing = discord.utils.get(category.text_channels, name=ch_data["name"])

                if not existing:
                    if ch_data["type"] == "voice":
                        coro = guild.create_voice_channel(
                            name=ch_data["name"],
                            category=category,
                            overwrites=ch_overwrites,
                            reason="VOID Setup",
                        )
                    else:
                        coro = guild.create_text_channel(
                            name=ch_data["name"],
                            category=category,
                            overwrites=ch_overwrites,
                            topic=ch_data.get("topic", ""),
                            reason="VOID Setup",
                        )

                    result = await create_with_retry(
                        guild=guild,
                        coro=coro,
                        name=ch_data["name"],
                        max_retries=10,
                    )
                    if result:
                        channels_by_name[ch_data["name"]] = result
                        channels_created += 1
                    await asyncio.sleep(1.0)
                else:
                    channels_by_name[ch_data["name"]] = existing

        await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
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

        # SCHRITT 4: EMBED-NACHRICHTEN
        c_ticket_mention = channels_by_name["\U0001F39F\uFE0F\u2502create-ticket"].mention if "\U0001F39F\uFE0F\u2502create-ticket" in channels_by_name else "#create-ticket"
        c_ff_mention = channels_by_name["\u2699\uFE0F\u2502fastflags"].mention if "\u2699\uFE0F\u2502fastflags" in channels_by_name else "#fastflags"

        c_rules = channels_by_name.get("\U0001F4DC\u2502rules")
        if c_rules:
            await c_rules.send(embed=EmbedHelper.create_prestige_embed(
                title="\U0001F4DC\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3\U0001D5DF\U0001D5E6\U0001D5D6\U0001D5E2\U0001D5D4 - SERVER REGELN",
                description=(
                    "Um eine sichere, professionelle und angenehme Atmosph\u00e4re f\u00fcr alle Kunden und Creator zu gew\u00e4hrleisten, "
                    "bitten wir dich, die folgenden Richtlinien einzuhalten:\n\n"
                    "\U0001F916 \u2502 **\U0001D5ED. \U0001D5E5\U0001D5F2\U0001D5F0\U0001D5FD\U0001D5F2\U0001D5F8\U0001D5F1 & \U0001D5DB\u0001D5FC\u0001D5F3\U0001D5F9\U0001D5DE\U0001D5F0\U0001D5F5\U0001D5F2\U0001D5DE\U0001D5F1**\n"
                    "> Behandle jedes Mitglied und jeden Staff mit vollstem Respekt. "
                    "Beleidigungen, Toxizit\u00e4t, Bel\u00e4stigung oder Drohungen jeglicher Art f\u00fchren zum sofortigen Serverausschluss.\n\n"
                    "\U0001F6AB \u2502 **\U0001D5EE. \U0001D5DE\U0001D5F2\U0001D5DE\U0001D5FB \U0001D5E6\U0001D5D4\U0001D5D4\U0001D5FA & \U0001D5D9\U0001D5FF\U0001D5F2\U0001D5FA\U0001D5E1\U0001D5F4\U0001D5F2\U0001D5FF\U0001D5F3\U0001D5FA\U0001D5F4\U0001D5F2\U0001D5FF\U0001D5F4**\n"
                    "> Spamming in den Kan\u00e4len ist verboten. Das Posten von Werbelinks zu anderen Discord-Servern, "
                    "Dienstleistungen oder Fremdprodukten (sowohl in Chats als auch per DM) wird permanent gebannt.\n\n"
                    "\U0001F6D2 \u2502 **\U0001D5EE. \U0001D5E6\U0001D5DE\U0001D5F0\U0001D5F5\U0001D5F2\U0001D5FF\U0001D5F2\U0001D5FF & \U0001D5E2\U0001D5F3\U0001D5F3\U0001D5DE\U0001D5F9\U0001D5DE\U0001D5F2\U0001D5F9\U0001D5F9\U0001D5F2\U0001D5FF \U0001D5DB\U0001D5D4\U0001D5FB\U0001D5E1\U0001D5F2\U0001D5F9**\n"
                    "> Jegliche Verk\u00e4ufe und Dienstleistungen finden ausschlie\u00dflich \u00fcber unser offizielles "
                    "Ticket-System in " + c_ticket_mention + " statt. Privater Handel oder das Anbieten eigener "
                    "Produkte ist untersagt.\n\n"
                    "\U0001F4CE \u2502 **\U0001D5EE. \U0001D5DF\U0001D5E6\U0001D5D9\U0001D5EA & \U0001D5E8\U0001D5FB\U0001D5D4\U0001D5FB\U0001D5D8\U0001D5F2\U0001D5FA\U0001D5F0\U0001D5F0\U0001D5F2\U0001D5FB\U0001D5F2 \U0001D5DC\U0001D5FB\U0001D5F5\U0001D5D4\U0001D5F9\U0001D5F1\U0001D5F2**\n"
                    "> Keine jugendgef\u00e4hrdenden, pornografischen, gewaltverherrlichenden oder illegalen Medien.\n\n"
                    "\U0001F4CC \u2502 **\U0001D5DB\U0001D5DE\U0001D5FB\U0001D5F4\U0001D5F2\U0001D5DE\U0001D5F0**\n"
                    "> Mit dem Aufenthalt auf diesem Server akzeptierst du die Discord Nutzungsbedingungen (TOS) "
                    "sowie unsere Serverregeln. Unsere Moderatoren haben das Recht, bei Verst\u00f6\u00dfen ohne Vorwarnung einzugreifen."
                ),
                color=0xFF003C,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))

        c_buy = channels_by_name.get("\U0001F6D2\u2502how-to-buy")
        if c_buy:
            buy_desc = (
                "Der Ablauf eines Einkaufs bei **\U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3\U0001D5DF\U0001D5E6\U0001D5D6\U0001D5E2\U0001D5D4** ist vollst\u00e4ndig automatisiert und absolut sicher. "
                "Folge einfach diesem einfachen Ablauf:\n\n"
                "1\ufe0f\u20e3 \u2502 **Ticket erstellen**\n"
                "> Besuche den Kanal " + c_ticket_mention + " und klicke auf den Button **"
                "Produkt kaufen"**. Ein privater Supportkanal wird nur f\u00fcr dich erstellt.\n\n"
                "2\ufe0f\u20e3 \u2502 **Produktdetails angeben**\n"
                "> Teile unserem Supportteam im Ticket mit, was du kaufen m\u00f6chtest "
                "(z.B. Premium FastFlags, bestimmte T-Shirt Templates, Serverlayouts).\n\n"
                "3\ufe0f\u20e3 \u2502 **Zahlungsabwicklung**\n"
                "> W\u00e4hle deine bevorzugte Zahlungsmethode aus. Wir unterst\u00fctzen:\n"
                "> \U0001F539 PayPal (Familie & Freunde)\n"
                "> \U0001F539 Robux (via Gamepass oder Gruppen-Auszahlung)\n"
                "> \U0001F539 Paysafecard\n"
                "> \U0001F539 Kryptow\u00e4hrungen (Litecoin - LTC, Bitcoin - BTC, USDT)\n\n"
                "4\ufe0f\u20e3 \u2502 **Lieferung erhalten**\n"
                "> Nach der Zahlungsbest\u00e4tigung wird dein digitales Produkt "
                "(Config, Code, PNG-Datei) direkt im Ticket an dich \u00fcbergeben!"
            )
            await c_buy.send(embed=EmbedHelper.create_prestige_embed(
                title="\U0001F6D2\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \u2022 \U0001D5EA\U0001D5DC\U0001D5DA \U0001D5DE\U0001D5D4\U0001D5E8\U0001D5D9\U0001D5DA \U0001D5DC\U0001D5D6\U0001D5DB?",
                description=buy_desc,
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))

        c_products = channels_by_name.get("\U0001F4E6\u2502products")
        if c_products:
            await c_products.send(embed=EmbedHelper.create_prestige_embed(
                title="\U0001F4E6\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \u2022 \U0001D5E8\U0001D5DF\U0001D5E6\U0001D5DA\U0001D5E5\U0001D5DA \U0001D5D4\U0001D5E5\U0001D5E2\U0001D5D7\U0001D5E8\U0001D5D6\U0001D5DF\U0001D5DA",
                description=(
                    "Finde hier deine Roblox- und Discord-Upgrades:\n\n"
                    "**\U0001F455 Roblox Kleidung:**\n"
                    "> - *Klassische T-Shirt PNGs:* ab 50 Robux / 0,50\u20ac\n"
                    "> - *Exklusive Bundles (50+ Vorlagen):* ab 500 Robux / 5,00\u20ac\n\n"
                    "**\u2699\uFE0F FastFlags (FPS-Boost):**\n"
                    "> - *Standard-Configs:* Gratis (siehe " + c_ff_mention + ")\n"
                    "> - *Premium Ultra Configs:* 150 Robux / 1,50\u20ac\n\n"
                    "**\U0001F5A5\uFE0F Discord Templates:**\n"
                    "> - *Fertiges Shop-Layout:* 400 Robux / 4,00\u20ac"
                ),
                color=0xFFD700,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))

        c_ticket_panel = channels_by_name.get("\U0001F39F\uFE0F\u2502create-ticket")
        if c_ticket_panel:
            from bot.cogs.tickets import TicketButton
            await c_ticket_panel.send(
                embed=EmbedHelper.create_prestige_embed(
                    title="\U0001F39F\uFE0F\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \u2022 Support & Kauf-Center",
                    description=(
                        "Ben\u00f6tigst du Hilfe oder m\u00f6chtest etwas kaufen?\n"
                        "W\u00e4hle einfach die passende Kategorie aus:\n\n"
                        "> \U0001F6D2 \u2502 **Produkt kaufen** \u27a4 Roblox Items, FastFlags, Templates\n"
                        "> \u2699\uFE0F \u2502 **Allgemeiner Support** \u27a4 Technische Hilfe\n"
                        "> \U0001F91D \u2502 **Partnerschaft** \u27a4 F\u00fcr Kooperationen"
                    ),
                    color=0x00F0FF,
                    author_user=interaction.user,
                    bot_user=self.bot.user,
                ),
                view=TicketButton(),
            )

        c_faq = channels_by_name.get("\u2753\u2502faq")
        if c_faq:
            await c_faq.send(embed=EmbedHelper.create_prestige_embed(
                title="\u2753\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \u2022 FAQ (H\u00e4ufige Fragen)",
                description=(
                    "**Sind FastFlags erlaubt?**\n"
                    "> Ja, FastFlags sind Teil der offiziellen Roblox-Einstellungen. Es ist keine Cheat-Software!\n\n"
                    "**Wie lange dauert die Lieferung?**\n"
                    "> Fast immer innerhalb von 15 Minuten nach Zahlungseingang im Ticket."
                ),
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))

        c_inv = channels_by_name.get("\U0001F4E9\u2502invites")
        if c_inv:
            await c_inv.send(embed=EmbedHelper.create_prestige_embed(
                title="\U0001F4E9\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \u2022 Invite Belohnungen",
                description=(
                    "Lade Freunde auf unseren Server ein und staube dicke Gewinne ab:\n\n"
                    "> \U0001F381 \u2502 **5 Invites** \u27a4 Gratis T-Shirt Template\n"
                    "> \U0001F381 \u2502 **10 Invites** \u27a4 Gratis Premium FastFlags\n"
                    "> \U0001F381 \u2502 **20 Invites** \u27a4 Gratis Discord Server-Layout"
                ),
                color=0xFFA500,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))

        c_v_here = channels_by_name.get("\U0001F510\u2502verify-here")
        if c_v_here:
            from bot.cogs.verification import SimpleVerifyButton
            await c_v_here.send(
                embed=EmbedHelper.create_prestige_embed(
                    title="\U0001F510\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \u2022 SERVEREINTRETEN VERIFIZIERUNG",
                    description=(
                        "Herzlich Willkommen bei **\U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3\U0001D5DF\U0001D5E6\U0001D5D6\U0001D5E2\U0001D5D4**!\n\n"
                        "Um vollen Zugriff auf den Server (Chats, Produkte, Giveaways) zu erhalten, "
                        "musst du dich verifizieren.\n\n"
                        "**So einfach geht's:**\n"
                        "> 1\ufe0f\u20e3 \u2502 Klicke unten auf den gr\u00fcnen Button **'Verifizieren \U0001F510'**.\n"
                        "> 2\ufe0f\u20e3 \u2502 Du erh\u00e4ltst sofort die **Member-Rolle** und wirst freigeschaltet.\n\n"
                        "*Hinweis: F\u00fcr erweiterte K\u00e4ufe kannst du zus\u00e4tzlich die Roblox-Verifizierung nutzen!*"
                    ),
                    color=0x39FF14,
                    author_user=interaction.user,
                    bot_user=self.bot.user,
                ),
                view=SimpleVerifyButton(),
            )

        c_vouches = channels_by_name.get("\U0001F91D\u2502vouches")
        if c_vouches:
            await c_vouches.send(embed=EmbedHelper.create_prestige_embed(
                title="\U0001F91D\u2502 \U0001D5E9\U0001D5E2\U0001D5D7\U0001D5D3 \u2022 \U0001D5DE\U0001D5E8\U0001D5DF\U0001D5D7\U0001D5DA\U0001D5DF-\U0001D5D5\U0001D5DA\U0001D5E9\U0001D5DA\U0001D5E5\U0001D5DF\U0001D5E8\U0001D5DF\U0001D5DA\U0001D5DF",
                description=(
                    "Kundenzufriedenheit steht bei uns an oberster Stelle!\n\n"
                    "Wenn du bei uns eingekauft hast, w\u00fcrden wir uns sehr \u00fcber eine Bewertung freuen. "
                    "Das hilft uns und st\u00e4rkt das Vertrauen neuer Kunden.\n\n"
                    "**Beispiel f\u00fcr eine Bewertung:**\n"
                    "\u2b50 \u2b50 \u2b50 \u2b50 \u2b50 - *Sehr schneller Support, FastFlags funktionieren perfekt "
                    "und habe direkt +120 FPS bekommen! Gerne wieder!*"
                ),
                color=0xFFD700,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))

        stats_cog = self.bot.get_cog("StatsCog")
        if stats_cog:
            await stats_cog.update_stats_channels(guild)

        await self.safe_edit(status_msg, embed=EmbedHelper.create_prestige_embed(
            title="\U0001F389 Server-Setup erfolgreich abgeschlossen! \U0001F389",
            description=(
                "> \U0001F451 **Rollen:** {0} erstellt, {1} uebersprungen\n"
                "> \U0001F4C1 **Kanaele:** {2} erstellt\n"
                "> \U0001F512 **Rechte:** Hochsicheres Rechtesystem aktiv\n"
                "> \U0001F4DD **Embeds:** Alle Infos, Regeln, Tickets und Verifikation gesendet\n"
                "> \U0001F39F\uFE0F **Tickets:** Interaktive Multi-Tickets einsatzbereit!\n\n"
                "Dein Server ist jetzt komplett fertig! \U0001F680"
            ).format(roles_created, roles_skipped, channels_created),
            color=0x39FF14,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))
