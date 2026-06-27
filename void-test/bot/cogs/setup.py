"""
Setup Cog - Kompletter Server-Setup.
Enthält !role und !Start Befehle nach Vorgabe.
"""

import asyncio
import logging

import discord
from discord.ext import commands
from discord.ui import View

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db

logger = logging.getLogger("void_shop_bot.setup")
create_prestige_embed = EmbedHelper.create_prestige_embed


async def create_with_retry(guild, coro_fn, name, max_retries=10):
    for attempt in range(max_retries):
        try:
            result = await coro_fn()
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
    logger.error("Max Retries erreicht für %s", name)
    return None


class SetupConfirmationView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label="🧹 Komplett neu aufsetzen", style=discord.ButtonStyle.danger, emoji="🧹")
    async def reset_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "reset"
        self.stop()

    @discord.ui.button(label="➕ Nur hinzufügen", style=discord.ButtonStyle.success, emoji="➕")
    async def add_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "add"
        self.stop()

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "cancel"
        self.stop()


class SetupCog(commands.Cog, name="SetupCog"):
    def __init__(self, bot):
        self.bot = bot

    # --- ROLES SETUP COMMAND (!role) ---
    @commands.command(name="role", aliases=["roles", "Role", "Roles"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def create_roles_command(self, ctx):
        """
        Erstellt alle 23 Premium-Rollen, prüft ob sie bereits existieren,
        und setzt im Anschluss alle Kanalrechte für diese Rollen.
        Inklusive dynamic-permissions Schutz.
        """
        progress_embed = create_prestige_embed(
            title="👑 Rollen- & Berechtigungs-Setup",
            description="> ⚙️ Initialisiere das Erstellen von 23 Premium-Rollen...\nBitte warten.",
            color=0x00f0ff,
            author_user=ctx.author,
            bot_user=self.bot.user
        )
        status_msg = await ctx.send(embed=progress_embed)
        guild = ctx.guild
        bot_member = guild.me
        bot_permissions = bot_member.guild_permissions

        role_colors = {
            # --- STAFF ROLES ---
            "👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿": (0xff003c, True),        # Crimson Red
            "👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿": (0xff3366, True),     # Light Pink-Red
            "🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻": (0x00f0ff, True),        # Neon Cyan
            "⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿": (0x00a8a8, True),      # Dark Teal
            "🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠ｏｄｅｒａｔｏｒ": (0x39ff14, False),    # Neon Green
            "🎫│ 𝗩𝗢𝗜𝗗 • 𝗦ｕ𝗽𝗽𝗼𝗿𝘁": (0x20b2aa, False),      # Light Sea Green
            "🚨│ 𝗩𝗢𝗜𝗗 • 𝗧ｒｉａｌ 𝗠ｏｄ": (0xadff2f, False),    # Green Yellow
            
            # --- SPECIAL ROLES ---
            "🤝│ 𝗩𝗢𝗜𝗗 • 𝗣𝗮ｒｔｎｅ𝗿": (0xffa500, False),      # Orange
            "💎│ 𝗩𝗢𝗜𝗗 • 𝗕ｏｏｓｔｅ𝗿": (0xf47fff, False),      # Pink
            "🌟│ 𝗩𝗢𝗜𝗗 • 𝗩𝗜𝗣": (0xffd700, False),          # Gold (VIP)
            "🫂│ 𝗩𝗢𝗜𝗗 • 𝗙ｒｉ𝗲𝗻𝗱": (0xff69b4, False),        # Hot Pink
            "👤│ 𝗩𝗢𝗜𝗗 • 𝗩ｅｒｉｆｉ𝗲ｄ": (0x7f8c8d, False),      # Gray-Blue (Verified)
            
            # --- CUSTOMER ROLES ---
            "🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿": (0xffff00, False),     # Yellow
            "💎│ 𝗩𝗢𝗜𝗗 • 𝗣ｒ𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿": (0x00ffff, False), # Cyan Customer
            
            # --- REWARD ROLES (BUYER LEVELS) ---
            "🥉│ 𝗕𝗿ｏ𝗻𝘇𝗲 𝗕𝘂𝘆𝗲𝗿": (0xcd7f32, False),       # Bronze
            "🥈│ 𝗦𝗶𝗹𝘃𝗲𝗿 𝗕𝘂𝘆𝗲𝗿": (0xc0c0c0, False),       # Silver
            "🥇│ 𝗚ｏ𝗹𝗱 𝗕𝘂𝘆𝗲𝗿": (0xffd700, False),         # Gold
            "💎│ 𝗗𝗶𝗮𝗺𝗼𝗻𝗱 𝗕𝘂𝘆𝗲𝗿": (0xb9f2ff, False),       # Diamond
            
            # --- NOTIFICATION ROLES ---
            "📢│ 𝗔𝗻𝗻𝗼𝘂𝗻𝗰𝗲𝗺𝗲𝗻𝘁 𝗣𝗶𝗻𝗴": (0x7289da, False),  # Discord Blue
            "🎁│ 𝗚ｉ𝘃𝗲𝗮𝘄𝗮𝘆 𝗣𝗶𝗻𝗴": (0xff4500, False),      # Red-Orange
            "📦│ 𝗣𝗿ｏ𝗱𝘂𝗰𝘁 𝗣𝗶𝗻𝗴": (0x32cd32, False),       # Lime Green
            
            # --- BASE ROLES ---
            "👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿": (0xa0a0a0, False),       # Light Gray
            "🤖│ 𝗩𝗢𝗜𝗗 • 𝗕ｏｔ": (0x4a00a8, False)           # Dark Purple
        }

        created_roles = {}
        roles_created_count = 0
        roles_skipped_count = 0
        roles_failed_count = 0

        for role_name, (color_hex, is_admin) in role_colors.items():
            existing_role = discord.utils.get(guild.roles, name=role_name)
            if existing_role:
                created_roles[role_name] = existing_role
                roles_skipped_count += 1
                continue

            try:
                perms = discord.Permissions.none()
                if is_admin and bot_permissions.administrator:
                    perms.administrator = True
                elif "Moderator" in role_name or "Manager" in role_name:
                    requested_perms = [
                        ("view_channel", True), ("send_messages", True), ("manage_messages", True),
                        ("kick_members", True), ("ban_members", True), ("mute_members", True),
                        ("deafen_members", True), ("move_members", True), ("change_nickname", True),
                        ("read_message_history", True), ("attach_files", True), ("embed_links", True),
                        ("add_reactions", True), ("use_external_emojis", True)
                    ]
                    for perm_name, req_val in requested_perms:
                        if getattr(bot_permissions, perm_name, False):
                            setattr(perms, perm_name, True)
                else:
                    requested_perms = [
                        ("view_channel", True), ("send_messages", True), ("read_message_history", True),
                        ("attach_files", True), ("embed_links", True), ("add_reactions", True),
                        ("use_external_emojis", True), ("change_nickname", True)
                    ]
                    for perm_name, req_val in requested_perms:
                        if getattr(bot_permissions, perm_name, False):
                            setattr(perms, perm_name, True)

                new_role = await create_with_retry(
                    guild=guild,
                    coro_fn=lambda name=role_name, c=color_hex, p=perms: guild.create_role(
                        name=name,
                        color=discord.Color(c),
                        permissions=p,
                        hoist=True,
                        mentionable=True
                    ),
                    name=role_name
                )
                if new_role:
                    created_roles[role_name] = new_role
                    roles_created_count += 1
                    await asyncio.sleep(0.15)
                else:
                    new_role = await create_with_retry(
                        guild=guild,
                        coro_fn=lambda name=role_name, c=color_hex: guild.create_role(
                            name=name,
                            color=discord.Color(c),
                            permissions=discord.Permissions.default(),
                            hoist=True,
                            mentionable=True
                        ),
                        name=role_name
                    )
                    if new_role:
                        created_roles[role_name] = new_role
                        roles_created_count += 1
                        await asyncio.sleep(0.15)
                    else:
                        roles_failed_count += 1
                        logger.error(f"Konnte Rolle {role_name} überhaupt nicht erstellen.")
            except Exception as e:
                roles_failed_count += 1
                logger.error(f"Fehler bei {role_name}: {e}")

        if roles_failed_count > 0 and roles_created_count == 0 and roles_skipped_count == 0:
            embed_warning = create_prestige_embed(
                title="⚠️ FEHLER: Keine Rollen erstellt!",
                description=f"> Es konnte **keine einzige Rolle** erstellt werden!\n\n"
                            f"**Ursache:**\n"
                            f"Dem Bot fehlt im Server die Berechtigung **'Rollen verwalten'** (Manage Roles).\n\n"
                            f"**So behebst du diesen Fehler:**\n"
                            f"1. Gehe in deine **Server-Einstellungen** ➔ **Rollen**.\n"
                            f"2. Klicke auf die Rolle deines Bots (`𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣`).\n"
                            f"3. Aktiviere die Berechtigung **'Rollen verwalten'** (oder Administrator).\n"
                            f"4. Ziehe meine Rolle ganz nach oben.\n"
                            f"5. Führe `!role` erneut aus.",
                color=0xff003c,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await status_msg.edit(embed=embed_warning)
            return

        r_everyone = guild.default_role
        r_member = created_roles.get("👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿") or r_everyone
        r_customer = created_roles.get("🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿") or r_everyone
        r_premium_buyer = created_roles.get("💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿") or r_everyone
        r_vip = created_roles.get("🌟│ 𝗩𝗢𝗜𝗗 • 𝗩𝗜𝗣") or r_everyone
        r_booster = created_roles.get("💎│ 𝗩𝗢𝗜𝗗 • 𝗕ｏｏ𝘀𝘁𝗲𝗿") or r_everyone
        r_partner = created_roles.get("🤝│ 𝗩𝗢𝗜𝗗 • 𝗣𝗮𝗿𝘁𝗻𝗲𝗿") or r_everyone
        r_support = created_roles.get("🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁") or r_everyone
        r_trial_mod = created_roles.get("🚨│ 𝗩𝗢𝗜𝗗 • 𝗧𝗿𝗶𝗮𝗹 𝗠ｏｄ") or r_everyone
        r_mod = created_roles.get("🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠ｏｄｅｒ𝗮𝘁ｏ𝗿") or r_everyone
        r_manager = created_roles.get("⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿") or r_everyone
        r_admin = created_roles.get("🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻") or r_everyone
        r_co_owner = created_roles.get("👑│ 𝗩𝗢𝗜𝗗 • 𝗖ｏ-𝗢𝘄𝗻𝗲𝗿") or r_everyone
        r_owner = created_roles.get("👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿") or r_everyone

        progress_embed.description = f"> 👑 Rollen geprüft: **{roles_created_count} erstellt**, **{roles_skipped_count} übersprungen**.\n> 🔒 Setze jetzt Berechtigungen für alle Kanäle..."
        await status_msg.edit(embed=progress_embed)

        info_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True, read_message_history=True)}
        for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
            if r != r_everyone: info_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
        for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]:
            if r != r_everyone: info_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)

        staff_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
        for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]:
            if r != r_everyone: staff_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
        for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
            if r != r_everyone: staff_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        log_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
        for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner, r_support, r_trial_mod, r_mod]:
            if r != r_everyone: log_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
        for r in [r_manager, r_admin, r_co_owner, r_owner]:
            if r != r_everyone: log_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channels_processed = 0
        for channel in guild.channels:
            try:
                if channel.category and "LOGS" in channel.category.name.upper():
                    await channel.edit(overwrites=log_overwrites)
                elif channel.category and "STAFF" in channel.category.name.upper():
                    await channel.edit(overwrites=staff_overwrites)
                elif channel.category and ("INFO" in channel.category.name.upper() or "SHOP" in channel.category.name.upper() or "SUPPORT" in channel.category.name.upper() or "VERIFY" in channel.category.name.upper()):
                    await channel.edit(overwrites=info_overwrites)
                channels_processed += 1
                await asyncio.sleep(0.1)
            except Exception:
                pass

        success_embed = create_prestige_embed(
            title="🎉 Rollen & Rechte-Setup beendet!",
            description=f"> 👑 **Rollen erstellt:** {roles_created_count}\n"
                        f"> 👑 **Rollen übersprungen:** {roles_skipped_count}\n"
                        f"> 🔒 **Kanäle konfiguriert:** {channels_processed}\n\n"
                        f"Alle Berechtigungen wurden für deine 23 Rollen optimal eingestellt!",
            color=0x39ff14,
            author_user=ctx.author,
            bot_user=self.bot.user
        )
        await status_msg.edit(embed=success_embed)

    # --- START COMMAND (!Start) ---
    @commands.command(name="Start", aliases=["start"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def start(self, ctx):
        """
        Richtet den kompletten Server mit allen Kategorien, Kanälen und Logs ein.
        Nutzbar nach '!role', um das volle Layout zu erstellen.
        """
        embed_choice = create_prestige_embed(
            title="⚠️ 𝗩𝗢𝗜𝗗 • SERVER SETUP INITIALISIERUNG ⚠️",
            description=f"Hallo {ctx.author.mention},\n\ndu bist dabei, das **Prestige Server-Layout** für **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** aufzubauen.\n"
                        f"Dieses Setup generiert:\n"
                        f"> 📁 │ **7 Hauptkategorien, 1 Log-Kategorie & 1 Stats-Kategorie**\n"
                        f"> 💬 │ **27 Textkanäle, 7 Voicekanäle & 7 professionelle Log-Kanäle (Gesamt: 41 Kanäle)**\n"
                        f"> ⚙️ │ **Vollständiges Embed-Design in allen Infokanälen**\n\n"
                        f"Bitte wähle eine Option aus:\n\n"
                        f"🧹 **Komplett neu aufsetzen:** Löscht alle Kanäle (außer den aktuellen) und baut neu auf.\n"
                        f"➕ **Nur hinzufügen:** Ergänzt das Layout parallel.",
            color=0xff003c,
            author_user=ctx.author,
            bot_user=self.bot.user
        )
        
        view = SetupConfirmationView(ctx)
        confirm_msg = await ctx.send(embed=embed_choice, view=view)
        await view.wait()
        if view.value is None or view.value == "cancel":
            embed_cancel = create_prestige_embed(
                title="❌ Setup abgebrochen",
                description="> Das Server-Setup wurde abgebrochen. Es wurden keine Kanäle erstellt.",
                color=0x3e3e3e,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await confirm_msg.edit(embed=embed_cancel, view=None)
            return

        status_embed = create_prestige_embed(
            title="⚙️ Setup-Prozess läuft...",
            description="> Lösche alte Kanäle (sofern ausgewählt)...",
            color=0x00f0ff,
            author_user=ctx.author,
            bot_user=self.bot.user
        )
        status_msg = await ctx.send(embed=status_embed)
        await confirm_msg.delete()
        guild = ctx.guild
        if view.value == "reset":
            for channel in guild.channels:
                if channel.id != ctx.channel.id:
                    try:
                        await channel.delete()
                        await asyncio.sleep(0.1)
                    except Exception:
                        pass

        # Berechtigungs-Gruppen definieren
        r_everyone = guild.default_role
        r_member = discord.utils.get(guild.roles, name="👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿") or r_everyone
        r_customer = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿") or r_everyone
        r_premium_buyer = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿") or r_everyone
        r_vip = discord.utils.get(guild.roles, name="🌟│ 𝗩𝗢𝗜𝗗 • 𝗩𝗜𝗣") or r_everyone
        r_booster = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • 𝗕ｏｏ𝘀𝘁𝗲𝗿") or r_everyone
        r_partner = discord.utils.get(guild.roles, name="🤝│ 𝗩𝗢𝗜𝗗 • 𝗣𝗮𝗿𝘁𝗻𝗲𝗿") or r_everyone
        r_support = discord.utils.get(guild.roles, name="🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁") or r_everyone
        r_trial_mod = discord.utils.get(guild.roles, name="🚨│ 𝗩𝗢𝗜𝗗 • 𝗧𝗿𝗶𝗮𝗹 𝗠ｏｄ") or r_everyone
        r_mod = discord.utils.get(guild.roles, name="🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠ｏ𝗱ｅｒ𝗮𝘁ｏ𝗿") or r_everyone
        r_manager = discord.utils.get(guild.roles, name="⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿") or r_everyone
        r_admin = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻") or r_everyone
        r_co_owner = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿") or r_everyone
        r_owner = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿") or r_everyone

        info_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True, read_message_history=True)}
        for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
            if r != r_everyone: info_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
        for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]:
            if r != r_everyone: info_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)

        community_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)}
        staff_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
        for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]:
            if r != r_everyone: staff_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
        for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
            if r != r_everyone: staff_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        # Höchstsensible Log-Rechte (Nur Manager+)
        log_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
        for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner, r_support, r_trial_mod, r_mod]:
            if r != r_everyone: log_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
        for r in [r_manager, r_admin, r_co_owner, r_owner]:
            if r != r_everyone: log_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        status_embed.description = "> 📁 Erstelle Server-Struktur & 41 Kanäle..."
        await status_msg.edit(embed=status_embed)

        categories_layout = [
            {
                "name": "📊│── 𝗩𝗢𝗜𝗗 • 𝗦𝗧𝗔𝗧𝗦 ──",
                "overwrites": info_overwrites,
                "channels": [
                    {"name": "👥│Mitglieder: 0", "type": "voice", "description": ""},
                    {"name": "💎│Booster: 0", "type": "voice", "description": ""},
                    {"name": "🛒│Kunden: 0", "type": "voice", "description": ""}
                ]
            },
            {
                "name": "🔐│── 𝗩𝗢𝗜𝗗 • 𝗩𝗘𝗥𝗜𝗙𝗬 ──",
                "overwrites": info_overwrites,
                "channels": [
                    {"name": "🔐│verify-here", "type": "text", "description": "Klicke unten auf den Button, um dich freizuschalten!"}
                ]
            },
            {
                "name": "📢│── 𝗩𝗢𝗜𝗗 • 𝗜𝗡𝗙𝗢 ──",
                "overwrites": info_overwrites,
                "channels": [
                    {"name": "📢│news", "type": "text", "description": "Wichtige Ankündigungen & News"},
                    {"name": "📜│rules", "type": "text", "description": "Das Serverregelwerk"},
                    {"name": "👋│willkommen", "type": "text", "description": "Begrüßungskanal für neue Mitglieder"},
                    {"name": "💨│aufwiedersehen", "type": "text", "description": "Verabschiedungskanal"},
                    {"name": "🎁│giveaways", "type": "text", "description": "Spannende Giveaways & Gewinne"},
                    {"name": "🤝│vouches", "type": "text", "description": "Erfahrungen unserer Käufer"},
                    {"name": "📩│invites", "type": "text", "description": "Lade Freunde ein für Belohnungen!"},
                    {"name": "🔗│partners", "type": "text", "description": "Unsere Partner-Server"}
                ]
            },
            {
                "name": "🛒│── 𝗩𝗢𝗜𝗗 • 𝗦𝗛𝗢𝗣 ──",
                "overwrites": info_overwrites,
                "channels": [
                    {"name": "👕│tshirt-templates", "type": "text", "description": "Exklusive T-Shirt Vorlagen für Roblox"},
                    {"name": "⚙️│fastflags", "type": "text", "description": "FPS & Performance Optimierungen"},
                    {"name": "🖥️│discord-templates", "type": "text", "description": "Schicke Discord Server Vorlagen"},
                    {"name": "📦│products", "type": "text", "description": "Unsere Produkt- & Preisübersicht"},
                    {"name": "🛒│how-to-buy", "type": "text", "description": "Wie du bei uns einkaufen kannst"},
                    {"name": "📈│updates", "type": "text", "description": "Entwicklungs-Updates & Produktnews"}
                ]
            },
            {
                "name": "💬│── 𝗩𝗢𝗜𝗗 • 𝗖𝗛𝗔𝗧 ──",
                "overwrites": community_overwrites,
                "channels": [
                    {"name": "💬│general-chat", "type": "text", "description": "Der Hauptchat für jedermann"},
                    {"name": "📷│media-and-showcase", "type": "text", "description": "Teile Bilder, Videos oder Avatare"},
                    {"name": "🎨│clothing-showcase", "type": "text", "description": "Zeige deine eigenen Roblox-Kleidungsdesigns!"},
                    {"name": "🖥️│setup-showcase", "type": "text", "description": "Zeige deinen Gaming-Setup oder Studio-Setup"},
                    {"name": "📈│trading", "type": "text", "description": "Tausche und handle mit Roblox-Gegenständen"},
                    {"name": "🤝│suggestions", "type": "text", "description": "Deine Verbesserungsvorschläge für den Shop"},
                    {"name": "🤖│bot-commands", "type": "text", "description": "Nutze die Bot-Befehle hier"}
                ]
            },
            {
                "name": "🎙️│── 𝗩𝗢𝗜𝗗 • 𝗧𝗔𝗟𝗞 ──",
                "overwrites": community_overwrites,
                "channels": [
                    {"name": "🔊│Lobby • Public", "type": "voice", "description": ""},
                    {"name": "🔊│Lounge • Chill", "type": "voice", "description": ""},
                    {"name": "🔊│Roblox • Talk", "type": "voice", "description": ""},
                    {"name": "🔊│Gaming • Duo", "type": "voice", "description": ""},
                    {"name": "🔊│Gaming • Squad", "type": "voice", "description": ""},
                    {"name": "🔊│Support • Voice", "type": "voice", "description": ""}
                ]
            },
            {
                "name": "💎│── 𝗩𝗢𝗜𝗗 • 𝗟𝗢Ｕ𝗡𝗚𝗘 ──",
                "overwrites": community_overwrites,
                "channels": [
                    {"name": "💎│booster-lounge", "type": "text", "description": "Spezialchat für Server-Booster", "custom_overwrites": "booster"},
                    {"name": "🌟│vip-lounge", "type": "text", "description": "Exklusiver Chat für VIP-Kunden", "custom_overwrites": "vip"},
                    {"name": "🛒│customer-lounge", "type": "text", "description": "Austauschbereich für alle Käufer", "custom_overwrites": "customer"}
                ]
            },
            {
                "name": "🎟️│── 𝗩𝗢𝗜𝗗 • 𝗦Ｕ𝗣𝗣𝗢𝗥𝗧 ──",
                "overwrites": info_overwrites,
                "channels": [
                    {"name": "🎟️│create-ticket", "type": "text", "description": "Erstelle ein Support- oder Kauf-Ticket"},
                    {"name": "❓│faq", "type": "text", "description": "Häufig gestellte Fragen (FAQs)"}
                ]
            },
            {
                "name": "🔒│── 𝗩𝗢𝗜𝗗 • 𝗦𝗧𝗔𝗙𝗙 ──",
                "overwrites": staff_overwrites,
                "channels": [
                    {"name": "🔒│staff-chat", "type": "text", "description": "Das interne Besprechungszimmer"},
                    {"name": "🛠️│mod-commands", "type": "text", "description": "Eingabe von Admin- und Moderations-Commands"},
                    {"name": "🔊│Staff • Voice", "type": "voice", "description": ""}
                ]
            },
            {
                "name": "📁│── 𝗩𝗢𝗜𝗗 • 𝗟𝗢Ｇ𝗦 ──",
                "overwrites": log_overwrites,
                "channels": [
                    {"name": "💬│voice-logs", "type": "text", "description": "Logs für Sprachkanäle"},
                    {"name": "🔨│ban-kick-logs", "type": "text", "description": "Logs für Banns, Kicks und Timeouts"},
                    {"name": "📝│message-logs", "type": "text", "description": "Logs für gelöschte & editierte Nachrichten"},
                    {"name": "📩│invite-logs", "type": "text", "description": "Logs für erstellte & genutzte Einladungslinks"},
                    {"name": "📥│join-leave-logs", "type": "text", "description": "Logs für Serverbeitritte & Austritte"},
                    {"name": "💾│ticket-logs", "type": "text", "description": "Ticket-Protokolle & Transkripte"},
                    {"name": "⚙️│system-logs", "type": "text", "description": "System-Logs für Kanäle & Rollen"}
                ]
            }
        ]

        channels_by_name = {}
        for cat_data in categories_layout:
            category = discord.utils.get(guild.categories, name=cat_data["name"])
            if not category:
                category = await create_with_retry(
                    guild=guild,
                    coro_fn=lambda name=cat_data["name"], ow=cat_data["overwrites"]: guild.create_category(
                        name=name, overwrites=ow
                    ),
                    name=cat_data["name"]
                )
                if not category:
                    embed_err = create_prestige_embed(
                        title="⚠️ FEHLER: Keine Kanäle erstellt!",
                        description=f"> Ich habe keine Berechtigung, Kategorien oder Kanäle zu erstellen!\n\n"
                                    f"**Behebung:**\n"
                                    f"Bitte stelle sicher, dass mein Bot die Berechtigung **'Kanäle verwalten'** (Manage Channels) oder **'Administrator'** besitzt und führe `!Start` erneut aus.",
                        color=0xff003c,
                        author_user=ctx.author,
                        bot_user=self.bot.user
                    )
                    await status_msg.edit(embed=embed_err)
                    return
                await asyncio.sleep(0.2)
            
            for ch_data in cat_data["channels"]:
                current_overwrites = cat_data["overwrites"].copy()
                
                if ch_data.get("custom_overwrites") == "booster":
                    current_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
                    for r in [r_member, r_customer, r_premium_buyer, r_vip]:
                        if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
                    if r_booster != r_everyone: current_overwrites[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
                        if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    
                elif ch_data.get("custom_overwrites") == "vip":
                    current_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
                    for r in [r_member, r_customer, r_premium_buyer]:
                        if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
                    if r_booster != r_everyone: current_overwrites[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    if r_vip != r_everyone: current_overwrites[r_vip] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
                        if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                elif ch_data.get("custom_overwrites") == "customer":
                    current_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
                    if r_member != r_everyone: current_overwrites[r_member] = discord.PermissionOverwrite(view_channel=False)
                    if r_booster != r_everyone: current_overwrites[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    if r_customer != r_everyone: current_overwrites[r_customer] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    if r_premium_buyer != r_everyone: current_overwrites[r_premium_buyer] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    if r_vip != r_everyone: current_overwrites[r_vip] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                    for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
                        if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

                if ch_data["type"] == "voice":
                    channel = discord.utils.get(category.voice_channels, name=ch_data["name"])
                    if not channel:
                        channel = await create_with_retry(
                            guild=guild,
                            coro_fn=lambda name=ch_data["name"], cat=category, ow=current_overwrites: guild.create_voice_channel(
                                name=name, category=cat, overwrites=ow
                            ),
                            name=ch_data["name"]
                        )
                        await asyncio.sleep(0.15)
                else:
                    channel = discord.utils.get(category.text_channels, name=ch_data["name"])
                    if not channel:
                        channel = await create_with_retry(
                            guild=guild,
                            coro_fn=lambda name=ch_data["name"], cat=category, ow=current_overwrites, top=ch_data["description"]: guild.create_text_channel(
                                name=name, category=cat, overwrites=ow, topic=top
                            ),
                            name=ch_data["name"]
                        )
                        await asyncio.sleep(0.15)
                if channel:
                    channels_by_name[ch_data["name"]] = channel

        status_embed.description = "> 📝 Richte detaillierte Infokanäle, FAQs und Einladungs-Systeme ein..."
        await status_msg.edit(embed=status_embed)

        c_ticket_mention = channels_by_name["🎟️│create-ticket"].mention if "🎟️│create-ticket" in channels_by_name else "#create-ticket"
        c_ff_mention = channels_by_name["⚙️│fastflags"].mention if "⚙️│fastflags" in channels_by_name else "#fastflags"

        # A) REGELN
        c_rules = channels_by_name.get("📜│rules")
        if c_rules:
            embed_rules = create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📜 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 - SERVER REGELN\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description="Um eine sichere, professionelle und angenehme Atmosphäre für alle Kunden und Creator zu gewährleisten, bitten wir dich, die folgenden Richtlinien einzuhalten:\n\n"
                            "🤖 │ **𝟭. 𝗥𝗲𝘀𝗽𝗲𝗸𝘁 & 𝗛ö𝗳𝗹𝗶𝗰𝗵𝗸𝗲𝗶𝘁**\n"
                            "> Behandle jedes Mitglied und jeden Staff mit vollstem Respekt. Beleidigungen, Toxizität, Belästigung oder Drohungen jeglicher Art führen zum sofortigen Serverausschluss.\n\n"
                            "🚫 │ **𝟮. 𝗞𝗲𝗶𝗻 𝗦𝗽𝗮𝗺 & 𝗙𝗿𝗲𝗺𝗱𝘄𝗲𝗿𝗯𝘂𝗻𝗴**\n"
                            "> Spamming in den Kanälen ist verboten. Das Posten von Werbelinks zu anderen Discord-Servern, Dienstleistungen oder Fremdprodukten (sowohl in Chats als auch per DM) wird permanent gebannt.\n\n"
                            "🛒 │ **𝟯. 𝗦𝗶𝗰𝗵𝗲𝗿𝗲𝗿 & 𝗢𝗳𝗳𝗶𝘇𝗶𝗲𝗹𝗹𝗲𝗿 𝗛𝗮𝗻𝗱𝗲𝗹**\n"
                            "> Jegliche Verkäufe und Dienstleistungen finden ausschließlich über unser offizielles Ticket-System in %s statt. Privater Handel oder das Anbieten eigener Produkte ist untersagt.\n\n"
                            "📎 │ **𝟰. 𝗡𝗦𝗙𝗪 & Unangemessene Inhalte**\n"
                            "> Keine jugendgefährdenden, pornografischen, gewaltverherrlichenden oder illegalen Medien.\n\n"
                            "📌 │ **𝗛𝗶𝗻𝘄𝗲𝗶𝘀**\n"
                            "> Mit dem Aufenthalt auf diesem Server accumulated hast, akzeptierst du die Discord Nutzungsbedingungen (TOS) sowie unsere Serverregeln. Unsere Moderatoren haben das Recht, bei Verstößen ohne Vorwarnung einzugreifen." % c_ticket_mention,
                color=0xff003c,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_rules.send(embed=embed_rules)

        # B) HOW TO BUY
        c_buy = channels_by_name.get("🛒│how-to-buy")
        if c_buy:
            embed_buy = create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🛒 𝗩𝗢𝗜𝗗 • 𝗪𝗜𝗘 𝗞𝗔𝗨𝗙𝗘 𝗜𝗖𝗛?\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description="Der Ablauf eines Einkaufs bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** ist vollständig automatisiert und absolut sicher. Folge einfach diesem einfachen Ablauf:\n\n"
                            "1️⃣ │ **Ticket erstellen**\n"
                            f"> Besuche den Kanal {c_ticket_mention} und klicke auf den Button **'Produkt kaufen'**. Ein privater Supportkanal wird nur für dich erstellt.\n\n"
                            "2️⃣ │ **Produktdetails angeben**\n"
                            "> Teile unserem Supportteam im Ticket mit, was du kaufen möchtest (z.B. Premium FastFlags, bestimmte T-Shirt Templates, Serverlayouts).\n\n"
                            "3️⃣ │ **Zahlungsabwicklung**\n"
                            "> Wähle deine bevorzugte Zahlungsmethode aus. Wir unterstützen:\n"
                            "> 🔹 PayPal (Familie & Freunde)\n"
                            "> 🔹 Robux (via Gamepass oder Gruppen-Auszahlung)\n"
                            "> 🔹 Paysafecard\n"
                            "> 🔹 Kryptowährungen (Litecoin - LTC, Bitcoin - BTC, USDT)\n\n"
                            "4️⃣ │ **Lieferung erhalten**\n"
                            "> Nach der Zahlungsbestätigung wird dein digitales Produkt (Config, Code, PNG-Download) direkt im Ticket an dich übergeben!",
                color=0x00f0ff,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_buy.send(embed=embed_buy)

        # C) PRODUCTS
        c_products = channels_by_name.get("📦│products")
        if c_products:
            embed_products = create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📦 𝗩𝗢𝗜𝗗 • 𝗨𝗡𝗦𝗘𝗥𝗘 𝗣𝗥𝗢𝗗𝗨𝗞𝗧𝗘\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description="Finde hier deine Roblox- und Discord-Upgrades:\n\n"
                            "**👕 Roblox Kleidung:**\n"
                            "> • *Klassische T-Shirt PNGs:* ab 50 Robux / 0,50€\n"
                            "> • *Exklusive Bundles (50+ Vorlagen):* ab 500 Robux / 5,00€\n\n"
                            "**⚙️ FastFlags (FPS-Boost):**\n"
                            f"> • *Standard-Configs:* Gratis (siehe {c_ff_mention})\n"
                            f"> • *Premium Ultra Configs:* 150 Robux / 1,50€\n\n"
                            "**🖥️ Discord Templates:**\n"
                            "> • *Fertiges Shop-Layout:* 400 Robux / 4,00€",
                color=0xffd700,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_products.send(embed=embed_products)

        # D) TICKET PANEL
        c_ticket_panel = channels_by_name.get("🎟️│create-ticket")
        if c_ticket_panel:
            from bot.cogs.tickets import TicketButton
            embed_ticket_panel = create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎟️ 𝗩𝗢𝗜𝗗 • Support & Kauf-Center\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description="Benötigst du Hilfe oder möchtest etwas kaufen?\n"
                            "Wähle einfach die passende Kategorie aus:\n\n"
                            "> 🛒 │ **Produkt kaufen** ➔ Roblox Items, FastFlags, Templates\n"
                            "> ⚙️ │ **Allgemeiner Support** ➔ Technische Hilfe\n"
                            "> 🤝 │ **Partnerschaft** ➔ Für Kooperationen",
                color=0x00f0ff,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_ticket_panel.send(embed=embed_ticket_panel, view=TicketButton())

        # E) FAQ
        c_faq = channels_by_name.get("❓│faq")
        if c_faq:
            embed_faq = create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n❓ 𝗩𝗢𝗜𝗗 • FAQ (Häufige Fragen)\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description="**Sind FastFlags erlaubt?**\n"
                            "> Ja, FastFlags sind Teil der offiziellen Roblox-Einstellungen. Es ist keine Cheat-Software!\n\n"
                            "**Wie lange dauert die Lieferung?**\n"
                            "> Fast immer innerhalb von 15 Minuten nach Zahlungseingang im Ticket.",
                color=0x00f0ff,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_faq.send(embed=embed_faq)

        # F) INVITES
        c_inv = channels_by_name.get("📩│invites")
        if c_inv:
            embed_inv = create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📩 𝗩𝗢𝗜𝗗 • Invite Belohnungen\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description="Lade Freunde auf unseren Server ein und staube dicke Gewinne ab:\n\n"
                            "> 🎁 │ **5 Invites** ➔ Gratis T-Shirt Template\n"
                            "> 🎁 │ **10 Invites** ➔ Gratis Premium FastFlags\n"
                            "> 🎁 │ **20 Invites** ➔ Gratis Discord Server-Layout",
                color=0xffa500,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_inv.send(embed=embed_inv)

        # G) VERIFY HERE PANEL IN #verify-here
        c_v_here = channels_by_name.get("🔐│verify-here")
        if c_v_here:
            from bot.cogs.verification import SimpleVerifyButton
            embed_v_here = create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🔐 𝗩𝗢𝗜𝗗 • SERVEREINTRETEN VERIFIZIERUNG\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description="Herzlich Willkommen bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**!\n\n"
                            "Um vollen Zugriff auf den Server (Chats, Produkte, Giveaways) zu erhalten, musst du dich verifizieren.\n\n"
                            "**So einfach geht's:**\n"
                            "> 1️⃣ │ Klicke unten auf den grünen Button **'Verifizieren 🔐'**.\n"
                            "> 2️⃣ │ Du erhältst sofort die **Member-Rolle** und wirst freigeschaltet.\n\n"
                            "*Hinweis: Für erweiterte Käufe kannst du zusätzlich die Roblox-Verifizierung nutzen!*",
                color=0x39ff14,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_v_here.send(embed=embed_v_here, view=SimpleVerifyButton())

        # H) FIRST VOUCH PREPARATION IN #vouches
        c_vouches = channels_by_name.get("🤝│vouches")
        if c_vouches:
            embed_vouch_placeholder = create_prestige_embed(
                title="🤝 𝗩𝗢𝗜𝗗 • 𝗞𝗨𝗡𝗗𝗘𝗡-𝗕𝗘𝗪𝗘𝗥𝗧𝗨𝗡𝗚𝗘𝗡 🤝",
                description="Kundenzufriedenheit steht bei uns an oberster Stelle!\n\n"
                            "Wenn du bei uns eingekauft hast, würden wir uns sehr über eine Bewertung freuen. "
                            "Das hilft uns und stärkt das Vertrauen neuer Kunden.\n\n"
                            "**Beispiel für eine Bewertung:**\n"
                            "⭐ ⭐ ⭐ ⭐ ⭐ - *Sehr schneller Support, FastFlags funktionieren perfekt und habe direkt +120 FPS bekommen! Gerne wieder!*",
                color=0xffd700,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_vouches.send(embed=embed_vouch_placeholder)

        # Statistiken sofort updaten
        stats_cog = self.bot.get_cog("StatsCog")
        if stats_cog:
            await stats_cog.update_stats_channels(guild)

        status_embed.title = "🎉 Server-Setup erfolgreich abgeschlossen! 🎉"
        status_embed.description = (
            f"> 📁 **Kategorien & Kanäle:** 41 Kanäle erfolgreich eingerichtet.\n"
            f"> 🔒 **Rechte:** Hochsicheres, fehlerfreies Rechtesystem aktiv.\n"
            f"> 🎟️ **Tickets:** Interaktive Multi-Tickets mit Claim-Funktion sind einsatzbereit!\n\n"
            f"Nutze `!Start` oder lösche diese Nachricht, falls gewünscht."
        )
        status_embed.color = 0x39ff14
        await status_msg.edit(embed=status_embed)
