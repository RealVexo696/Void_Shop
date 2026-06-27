"""
Setup Cog - Kompletter Server-Setup.
Enthält !role, !Start und !uz Befehle mit sofortigem Berechtigungs-Check,
Rollenlimit-Prüfung und vertikal gestaffeltem App-Karten UI Design (0x2b2d31).
"""

import asyncio
import logging

import discord
from discord.ext import commands
from discord.ui import View

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db
from bot.cogs.components_v2 import PrestigeContainer, build_layout

logger = logging.getLogger("void_shop_bot.setup")
create_prestige_embed = EmbedHelper.create_prestige_embed


async def create_with_retry(guild, coro_fn, name, max_retries=5):
    for attempt in range(max_retries):
        try:
            result = await coro_fn()
            logger.info("Erstellt (%d/%d): %s", attempt + 1, max_retries, name)
            return result
        except discord.HTTPException as e:
            if e.status == 429 or getattr(e, 'code', 0) == 429:
                wait = (getattr(e, 'retry_after', 5.0) or 5.0) + (attempt * 2.0)
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
            await asyncio.sleep(2.0)
    logger.error("Max Retries erreicht für %s", name)
    return None


class SetupConfirmationView(discord.ui.LayoutView):
    """Components-V2 Setup-Auswahl: Container (type 17) mit Textblock und
    drei vertikal gestaffelten Buttons (komplett neu / hinzufügen / abbrechen)."""

    def __init__(self, ctx, *, title: str, body: str):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.value = None

        # Buttons als eigenständige Items (Callbacks per .callback gesetzt)
        self.btn_reset = discord.ui.Button(
            label="🧹 Komplett neu aufsetzen", style=discord.ButtonStyle.danger
        )
        self.btn_add = discord.ui.Button(
            label="➕ Nur hinzufügen", style=discord.ButtonStyle.success
        )
        self.btn_cancel = discord.ui.Button(
            label="❌ Abbrechen", style=discord.ButtonStyle.secondary
        )
        self.btn_reset.callback = self._reset
        self.btn_add.callback = self._add
        self.btn_cancel.callback = self._cancel

        container = PrestigeContainer(
            title=title,
            body=body,
            author=ctx.author,
            items=[self.btn_reset, self.btn_add, self.btn_cancel],
        )
        self.add_item(container)

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Das kannst du nicht entscheiden!", ephemeral=True
            )
            return False
        await interaction.response.defer()
        return True

    async def _reset(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self.value = "reset"
        self.stop()

    async def _add(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self.value = "add"
        self.stop()

    async def _cancel(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        self.value = "cancel"
        self.stop()


class SetupCog(commands.Cog, name="SetupCog"):
    def __init__(self, bot):
        self.bot = bot

    def build_overwrites(self, guild, mode):
        r_everyone = guild.default_role

        def get_r(name):
            return discord.utils.get(guild.roles, name=name)

        # --- STAFF ROLES ---
        r_owner = get_r("👑│ 𝗩𝗢𝗜𝗗 • Owner")
        r_co_owner = get_r("👑│ 𝗩𝗢𝗜𝗗 • Co-Owner")
        r_admin = get_r("🛠️│ 𝗩𝗢𝗜𝗗 • Admin")
        r_manager = get_r("⚙️│ 𝗩𝗢𝗜𝗗 • Manager")
        r_mod = get_r("🛡️│ 𝗩𝗢𝗜𝗗 • Moderator")
        r_support = get_r("🎫│ 𝗩𝗢𝗜𝗗 • Support")
        r_trial = get_r("🚨│ 𝗩𝗢𝗜𝗗 • Trial Mod")

        high_staff = [r for r in [r_owner, r_co_owner, r_admin, r_manager] if r]
        mod_staff = [r for r in [r_mod, r_support, r_trial] if r]
        all_staff = high_staff + mod_staff

        # --- SPECIAL & BUYER ROLES ---
        r_partner = get_r("🤝│ 𝗩𝗢𝗜𝗗 • Partner")
        r_booster = get_r("💎│ 𝗩𝗢𝗜𝗗 • Booster")
        r_vip = get_r("🌟│ 𝗩𝗢𝗜𝗗 • VIP")
        r_friend = get_r("🫂│ 𝗩𝗢𝗜𝗗 • Friend")
        r_verified = get_r("👤│ 𝗩𝗢𝗜𝗗 • Verified")
        r_customer = get_r("🛒│ 𝗩𝗢𝗜𝗗 • Customer")
        r_premium = get_r("💎│ 𝗩𝗢𝗜𝗗 • Premium Buyer")

        # --- REWARD ROLES ---
        r_bronze = get_r("🥉│ 𝗩𝗢𝗜𝗗 • Bronze Buyer")
        r_silver = get_r("🥈│ 𝗩𝗢𝗜𝗗 • Silver Buyer")
        r_gold = get_r("🥇│ 𝗩𝗢𝗜𝗗 • Gold Buyer")
        r_diamond = get_r("💎│ 𝗩𝗢𝗜𝗗 • Diamond Buyer")

        # --- NOTIFICATION ROLES ---
        r_ping_ann = get_r("📢│ 𝗩𝗢𝗜𝗗 • Announcement Ping")
        r_ping_gw = get_r("🎁│ 𝗩𝗢𝗜𝗗 • Giveaway Ping")
        r_ping_prod = get_r("📦│ 𝗩𝗢𝗜𝗗 • Product Ping")

        # --- BASE ROLES ---
        r_member = get_r("👥│ 𝗩𝗢𝗜𝗗 • Member")
        r_bot = get_r("🤖│ 𝗩𝗢𝗜𝗗 • Bot")

        all_member_roles = [r for r in [
            r_partner, r_booster, r_vip, r_friend, r_verified, r_customer, r_premium,
            r_bronze, r_silver, r_gold, r_diamond,
            r_ping_ann, r_ping_gw, r_ping_prod, r_member
        ] if r]

        ow = {}

        if mode == "stats":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=True, connect=False)
            for r in all_member_roles + all_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, connect=False)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True)

        elif mode == "verify":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
            for r in all_member_roles:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)
            for r in all_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, read_message_history=True)

        elif mode == "info":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True, read_message_history=True)
            for r in all_member_roles:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True, read_message_history=True)
            for r in all_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True)

        elif mode == "community":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True, connect=True, speak=True)
            for r in all_member_roles:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True, connect=True, speak=True)
            for r in all_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True, connect=True, speak=True, mute_members=True, deafen_members=True, move_members=True)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, connect=True, speak=True)

        elif mode == "booster_lounge":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in all_member_roles:
                ow[r] = discord.PermissionOverwrite(view_channel=False)
            if r_booster:
                ow[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)
            for r in all_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True)

        elif mode == "vip_lounge":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in all_member_roles:
                ow[r] = discord.PermissionOverwrite(view_channel=False)
            for r in [r_booster, r_vip, r_gold, r_diamond]:
                if r: ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)
            for r in all_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True)

        elif mode == "customer_lounge":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in all_member_roles:
                ow[r] = discord.PermissionOverwrite(view_channel=False)
            for r in [r_booster, r_vip, r_customer, r_premium, r_bronze, r_silver, r_gold, r_diamond]:
                if r: ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)
            for r in all_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True)

        elif mode == "staff":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in all_member_roles:
                ow[r] = discord.PermissionOverwrite(view_channel=False)
            for r in all_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, read_message_history=True, connect=True, speak=True)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True, connect=True, speak=True)

        elif mode == "logs":
            ow[r_everyone] = discord.PermissionOverwrite(view_channel=False)
            for r in all_member_roles + mod_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=False)
            for r in high_staff:
                ow[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            if r_bot:
                ow[r_bot] = discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True, attach_files=True, read_message_history=True)

        return ow

    # --- RECHTE-UPDATE COMMAND (!uz) ---
    @commands.command(name="uz", aliases=["Uz", "UZ"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def update_permissions_command(self, ctx):
        guild = ctx.guild
        bot_member = guild.me

        if not bot_member.guild_permissions.manage_channels or not bot_member.guild_permissions.manage_roles:
            embed_warning = create_prestige_embed(
                title="⚠️ FEHLER: Keine Berechtigung!",
                description=(
                    "> Mir fehlt die Berechtigung **'Kanäle verwalten'** oder **'Rollen verwalten'** auf diesem Server!\n"
                    "~~                                                              ~~\n"
                    "> ⚠️ *Bitte aktiviere die Berechtigungen in den Servereinstellungen.*"
                ),
                color=0x2b2d31,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await ctx.send(embed=embed_warning)
            return

        progress_embed = create_prestige_embed(
            title="🔒 𝗩𝗢𝗜𝗗 • KANAL-RECHTE UPDATE (!uz)",
            description=(
                "> ⚙️ **Synchronisiere Rechte für alle 23 Rollen...**\n"
                "~~                                                              ~~\n"
                f"> ⏳ *Prüfe und bearbeite `{len(guild.channels)} Kanäle & Kategorien` in Echtzeit. Bitte warten...*"
            ),
            color=0x2b2d31,
            author_user=ctx.author,
            bot_user=self.bot.user
        )
        status_msg = await ctx.send(embed=progress_embed)

        channels_processed = 0
        for channel in guild.channels:
            try:
                cat_name = channel.category.name.upper() if channel.category else ""
                ch_name = channel.name.lower()

                mode = "info"
                if "booster-lounge" in ch_name:
                    mode = "booster_lounge"
                elif "vip-lounge" in ch_name:
                    mode = "vip_lounge"
                elif "customer-lounge" in ch_name:
                    mode = "customer_lounge"
                elif "logs" in cat_name or "logs" in ch_name:
                    mode = "logs"
                elif "staff" in cat_name or "staff" in ch_name or "mod-commands" in ch_name:
                    mode = "staff"
                elif "stats" in cat_name or "mitglieder" in ch_name or "booster:" in ch_name or "kunden:" in ch_name or "tickets:" in ch_name:
                    mode = "stats"
                elif "verify" in cat_name or "verify" in ch_name:
                    mode = "verify"
                elif "chat" in cat_name or "talk" in cat_name or "lounge" in cat_name or "general" in ch_name or "showcase" in ch_name or "trading" in ch_name or "lobby" in ch_name or "gaming" in ch_name:
                    mode = "community"
                elif "support" in cat_name or "ticket" in ch_name or "faq" in ch_name:
                    mode = "info"

                ow = self.build_overwrites(guild, mode)
                await channel.edit(overwrites=ow)
                channels_processed += 1
                await asyncio.sleep(0.3)
            except Exception:
                pass

        success_embed = create_prestige_embed(
            title="🎉 Kanal-Rechte erfolgreich aktualisiert!",
            description=(
                f"> 🔒 **Kanäle konfiguriert:** `{channels_processed} von {len(guild.channels)}`\n"
                "~~                                                              ~~\n"
                "> Sämtliche Kanäle und Kategorien besitzen nun 100% passgenaue Zugriffsrechte für alle 23 Rollen!"
            ),
            color=0x2b2d31,
            author_user=ctx.author,
            bot_user=self.bot.user
        )
        await status_msg.edit(embed=success_embed)

    # --- ROLES SETUP COMMAND (!role) ---
    @commands.command(name="role", aliases=["roles", "Role", "Roles"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def create_roles_command(self, ctx):
        guild = ctx.guild
        bot_member = guild.me
        bot_permissions = bot_member.guild_permissions

        progress_embed = create_prestige_embed(
            title="👑 Rollen- & Berechtigungs-Setup",
            description=(
                "> ⚙️ Initialisiere Systemprüfungen...\n"
                "~~                                                              ~~\n"
                "> ⏳ *Bitte warten.*"
            ),
            color=0x2b2d31,
            author_user=ctx.author,
            bot_user=self.bot.user
        )
        status_msg = await ctx.send(embed=progress_embed)

        if not bot_permissions.manage_roles:
            embed_warning = create_prestige_embed(
                title="⚠️ FEHLER: Keine Berechtigung zum Rollenerstellen!",
                description=(
                    "> Mir fehlt die Berechtigung **'Rollen verwalten'** (Manage Roles) auf diesem Server!\n"
                    "~~                                                              ~~\n"
                    "> **So behebst du diesen Fehler in 30 Sekunden:**\n"
                    "> 1. Gehe in deine **Server-Einstellungen** ➔ **Rollen**.\n"
                    "> 2. Klicke auf die Rolle deines Bots (`𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣`).\n"
                    "> 3. Aktiviere die Berechtigung **'Rollen verwalten'** (oder Administrator).\n"
                    "> 4. Ziehe meine Rolle ganz nach oben.\n"
                    "> 5. Führe `!role` erneut aus."
                ),
                color=0x2b2d31,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await status_msg.edit(embed=embed_warning)
            return

        if len(guild.roles) >= 240:
            embed_max = create_prestige_embed(
                title="⚠️ FEHLER: Maximales Rollenlimit erreicht!",
                description=(
                    f"> Dieser Server hat bereits `{len(guild.roles)} Rollen`!\n"
                    "~~                                                              ~~\n"
                    "> Discord erlaubt maximal 250 Rollen pro Server. Bitte lösche ungenutzte Rollen, damit ich die 23 Premium-Rollen erstellen kann!"
                ),
                color=0x2b2d31,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await status_msg.edit(embed=embed_max)
            return

        role_colors = {
            "👑│ 𝗩𝗢𝗜𝗗 • Owner": (0xff003c, True),
            "👑│ 𝗩𝗢𝗜𝗗 • Co-Owner": (0xff3366, True),
            "🛠️│ 𝗩𝗢𝗜𝗗 • Admin": (0x00f0ff, True),
            "⚙️│ 𝗩𝗢𝗜𝗗 • Manager": (0x00a8a8, True),
            "🛡️│ 𝗩𝗢𝗜𝗗 • Moderator": (0x39ff14, False),
            "🎫│ 𝗩𝗢𝗜𝗗 • Support": (0x20b2aa, False),
            "🚨│ 𝗩𝗢𝗜𝗗 • Trial Mod": (0xadff2f, False),
            "🤝│ 𝗩𝗢𝗜𝗗 • Partner": (0xffa500, False),
            "💎│ 𝗩𝗢𝗜𝗗 • Booster": (0xf47fff, False),
            "🌟│ 𝗩𝗢𝗜𝗗 • VIP": (0xffd700, False),
            "🫂│ 𝗩𝗢𝗜𝗗 • Friend": (0xff69b4, False),
            "👤│ 𝗩𝗢𝗜𝗗 • Verified": (0x7f8c8d, False),
            "🛒│ 𝗩𝗢𝗜𝗗 • Customer": (0xffff00, False),
            "💎│ 𝗩𝗢𝗜𝗗 • Premium Buyer": (0x00ffff, False),
            "🥉│ 𝗩𝗢𝗜𝗗 • Bronze Buyer": (0xcd7f32, False),
            "🥈│ 𝗩𝗢𝗜𝗗 • Silver Buyer": (0xc0c0c0, False),
            "🥇│ 𝗩𝗢𝗜𝗗 • Gold Buyer": (0xffd700, False),
            "💎│ 𝗩𝗢𝗜𝗗 • Diamond Buyer": (0xb9f2ff, False),
            "📢│ 𝗩𝗢𝗜𝗗 • Announcement Ping": (0x7289da, False),
            "🎁│ 𝗩𝗢𝗜𝗗 • Giveaway Ping": (0xff4500, False),
            "📦│ 𝗩𝗢𝗜𝗗 • Product Ping": (0x32cd32, False),
            "👥│ 𝗩𝗢𝗜𝗗 • Member": (0xa0a0a0, False),
            "🤖│ 𝗩𝗢𝗜𝗗 • Bot": (0x4a00a8, False)
        }

        created_roles = {}
        roles_created_count = 0
        roles_skipped_count = 0

        for idx, (role_name, (color_hex, is_admin)) in enumerate(role_colors.items(), 1):
            progress_embed.description = (
                f"> ⚙️ Erstelle Premium-Rollen... ({idx}/23)\n"
                f"> Aktuell: `{role_name}`\n"
                "~~                                                              ~~\n"
                "> ⚠️ *Hinweis: Discord hat ein strenges Rate-Limit für Rollen. Sollte der Bot hier kurz pausieren, bricht er NICHT ab, sondern wartet lediglich das Discord Rate-Limit ab! Bitte einfach laufen lassen.*"
            )
            try:
                await status_msg.edit(embed=progress_embed)
            except Exception:
                pass

            existing_role = discord.utils.get(guild.roles, name=role_name)
            if existing_role:
                created_roles[role_name] = existing_role
                roles_skipped_count += 1
                await asyncio.sleep(0.5)
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
                        mentionable=True,
                        reason="VOID Setup"
                    ),
                    name=role_name
                )
                
                if not new_role:
                    new_role = await create_with_retry(
                        guild=guild,
                        coro_fn=lambda name=role_name, c=color_hex: guild.create_role(
                            name=name,
                            color=discord.Color(c),
                            permissions=discord.Permissions.default(),
                            hoist=True,
                            mentionable=True,
                            reason="VOID Setup Fallback"
                        ),
                        name=role_name
                    )

                if not new_role:
                    embed_fail = create_prestige_embed(
                        title=f"⚠️ FEHLER beim Erstellen von '{role_name}'!",
                        description=(
                            f"> Die Rolle `{role_name}` konnte von Discord nicht erstellt werden!\n"
                            "~~                                                              ~~\n"
                            "> **Mögliche Ursachen:**\n"
                            "> 1. Die Bot-Rolle steht in den Server-Einstellungen nicht ganz oben.\n"
                            "> 2. Ein vorübergehendes Discord API Rate-Limit blockiert die Erstellung.\n"
                            "> 3. Fehlende Berechtigungen im Server.\n"
                            "~~                                                              ~~\n"
                            "> ⚠️ *Bitte ziehe die Bot-Rolle in den Einstellungen ganz nach oben und versuche es in wenigen Minuten erneut!*"
                        ),
                        color=0x2b2d31,
                        author_user=ctx.author,
                        bot_user=self.bot.user
                    )
                    await status_msg.edit(embed=embed_fail)
                    return

                created_roles[role_name] = new_role
                roles_created_count += 1
                await asyncio.sleep(2.0)

            except Exception as e:
                logger.error(f"Fehler bei {role_name}: {e}")
                await asyncio.sleep(2.0)

        progress_embed.description = (
            f"> 👑 Rollen geprüft: **{roles_created_count} erstellt**, **{roles_skipped_count} übersprungen**.\n"
            "~~                                                              ~~\n"
            "> 🔒 *Setze jetzt passende Berechtigungen für absolut jeden Kanal...*"
        )
        await status_msg.edit(embed=progress_embed)

        channels_processed = 0
        for channel in guild.channels:
            try:
                cat_name = channel.category.name.upper() if channel.category else ""
                ch_name = channel.name.lower()

                mode = "info"
                if "booster-lounge" in ch_name: mode = "booster_lounge"
                elif "vip-lounge" in ch_name: mode = "vip_lounge"
                elif "customer-lounge" in ch_name: mode = "customer_lounge"
                elif "logs" in cat_name or "logs" in ch_name: mode = "logs"
                elif "staff" in cat_name or "staff" in ch_name or "mod-commands" in ch_name: mode = "staff"
                elif "stats" in cat_name or "mitglieder" in ch_name or "booster:" in ch_name or "kunden:" in ch_name: mode = "stats"
                elif "verify" in cat_name or "verify" in ch_name: mode = "verify"
                elif "chat" in cat_name or "talk" in cat_name or "lounge" in cat_name or "general" in ch_name: mode = "community"

                ow = self.build_overwrites(guild, mode)
                await channel.edit(overwrites=ow)
                channels_processed += 1
                await asyncio.sleep(0.3)
            except Exception:
                pass

        success_embed = create_prestige_embed(
            title="🎉 Rollen & Rechte-Setup beendet!",
            description=(
                f"> 👑 **Rollen erstellt:** {roles_created_count}\n"
                f"> 👑 **Rollen übersprungen:** {roles_skipped_count}\n"
                f"> 🔒 **Kanäle konfiguriert:** {channels_processed}\n"
                "~~                                                              ~~\n"
                "> Alle Berechtigungen wurden für wirklich jede der 23 Rollen optimal eingestellt!"
            ),
            color=0x2b2d31,
            author_user=ctx.author,
            bot_user=self.bot.user
        )
        await status_msg.edit(embed=success_embed)

    # --- START COMMAND (!Start) ---
    @commands.command(name="Start", aliases=["start"])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def start(self, ctx):
        setup_body = (
            "du bist dabei, das **Prestige Server-Layout** für **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** aufzubauen.\n"
            "Dieses Setup generiert in wenigen Sekunden:\n\n"
            "📁 │ **7 Hauptkategorien, 1 Log-Kategorie & 1 Stats-Kategorie**\n"
            "💬 │ **30 Textkanäle, 8 Voicekanäle & 7 Log-Kanäle (Gesamt: 45+ Kanäle)**\n"
            "⚙️ │ **Vollständiges High-End Design in allen Infokanälen**\n\n"
            "📌 **Bitte wähle unten eine Setup-Option aus:**\n"
            "🧹 **Komplett neu aufsetzen:** Löscht alte Kanäle und baut das System komplett neu auf.\n"
            "➕ **Nur hinzufügen:** Ergänzt das Layout parallel zur bestehenden Struktur."
        )

        view = SetupConfirmationView(
            ctx,
            title="⚠️ 𝗩𝗢𝗜𝗗 • SERVER SETUP INITIALISIERUNG ⚠️",
            body=setup_body,
        )
        confirm_msg = await ctx.send(view=view)
        await view.wait()
        if view.value is None or view.value == "cancel":
            cancel_view = build_layout(
                title="❌ Setup abgebrochen",
                body="Das Server-Setup wurde abgebrochen. Es wurden keine Kanäle erstellt.",
                author=ctx.author,
            )
            await confirm_msg.edit(view=cancel_view)
            return

        status_embed = create_prestige_embed(
            title="⚙️ Setup-Prozess läuft...",
            description="> Lösche alte Kanäle (sofern ausgewählt)...",
            color=0x2b2d31,
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

        status_embed.description = "> 📁 Erstelle Server-Struktur & 44 Kanäle mit passenden Rechten für jede Rolle..."
        await status_msg.edit(embed=status_embed)

        categories_layout = [
            {
                "name": "📊│── 𝗩𝗢𝗜𝗗 • 𝗦𝗧𝗔𝗧𝗦 ──",
                "mode": "stats",
                "channels": [
                    {"name": "👥│Mitglieder: 0", "type": "voice", "description": ""},
                    {"name": "💎│Booster: 0", "type": "voice", "description": ""},
                    {"name": "🛒│Kunden: 0", "type": "voice", "description": ""},
                    {"name": "🎟️│Offene Tickets: 0", "type": "voice", "description": ""}
                ]
            },
            {
                "name": "🔐│── 𝗩𝗢𝗜𝗗 • 𝗩𝗘𝗥𝗜𝗙𝗬 ──",
                "mode": "verify",
                "channels": [
                    {"name": "🔐│verify-here", "type": "text", "description": "Klicke unten auf den Button, um dich freizuschalten!"}
                ]
            },
            {
                "name": "📢│── 𝗩𝗢𝗜𝗗 • 𝗜𝗡𝗙𝗢 ──",
                "mode": "info",
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
                "mode": "info",
                "channels": [
                    {"name": "♾️│infinityxeh", "type": "text", "description": "INFINITYxEH — Premium All-in-One Executor"},
                    {"name": "💉│fflags-injector", "type": "text", "description": "FFlags Injector — Auto FPS-Boost"},
                    {"name": "🛡️│anti-ban", "type": "text", "description": "Anti-Ban — Schutzsystem gegen Bans"},
                    {"name": "👕│tshirt-templates", "type": "text", "description": "Exklusive T-Shirt Vorlagen für Roblox"},
                    {"name": "🚀│fastflags-pack", "type": "text", "description": "FastFlags Pack — Ultra FPS-Boost Config"},
                    {"name": "🖥️│discord-template", "type": "text", "description": "Discord Server Template — Premium Shop-Layout"},
                    {"name": "📦│products", "type": "text", "description": "Unsere Produkt- & Preisübersicht"},
                    {"name": "🛒│how-to-buy", "type": "text", "description": "Wie du bei uns einkaufen kannst"},
                    {"name": "📈│updates", "type": "text", "description": "Entwicklungs-Updates & Produktnews"}
                ]
            },
            {
                "name": "💬│── 𝗩𝗢𝗜𝗗 • 𝗖𝗛𝗔𝗧 ──",
                "mode": "community",
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
                "name": "🎙️│── 𝗩𝗢𝗜𝗗 • ＴＡＬＫ ──",
                "mode": "community",
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
                "name": "💎│── 𝗩𝗢𝗜𝗗 • ＬＯＵＮＧ𝗘 ──",
                "mode": "community",
                "channels": [
                    {"name": "💎│booster-lounge", "type": "text", "description": "Spezialchat für Server-Booster", "overwrite_mode": "booster_lounge"},
                    {"name": "🌟│vip-lounge", "type": "text", "description": "Exklusiver Chat für VIP-Kunden", "overwrite_mode": "vip_lounge"},
                    {"name": "🛒│customer-lounge", "type": "text", "description": "Austauschbereich für alle Käufer", "overwrite_mode": "customer_lounge"}
                ]
            },
            {
                "name": "🎟️│── 𝗩𝗢𝗜𝗗 • ＳＵＰ𝗣ＯＲＴ ──",
                "mode": "info",
                "channels": [
                    {"name": "🎟️│create-ticket", "type": "text", "description": "Erstelle ein Kauf-, Support- oder Partner-Ticket"},
                    {"name": "❓│faq", "type": "text", "description": "Häufig gestellte Fragen (FAQs)"}
                ]
            },
            {
                "name": "🛒│── 𝗩𝗢𝗜𝗗 • ＫＡＵＦＥＮ ──",
                "mode": "info",
                "channels": []
            },
            {
                "name": "🤝│── 𝗩𝗢𝗜𝗗 • ＰＡＲＴＮＥＲ ──",
                "mode": "info",
                "channels": []
            },
            {
                "name": "🔒│── 𝗩𝗢𝗜𝗗 • ＳＴＡＦＦ ──",
                "mode": "staff",
                "channels": [
                    {"name": "🔒│staff-chat", "type": "text", "description": "Das interne Besprechungszimmer"},
                    {"name": "🛠️│mod-commands", "type": "text", "description": "Eingabe von Admin- und Moderations-Commands"},
                    {"name": "🔊│Staff • Voice", "type": "voice", "description": ""}
                ]
            },
            {
                "name": "📁│── 𝗩𝗢𝗜𝗗 • ＬＯГ𝗦 ──",
                "mode": "logs",
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
            cat_ow = self.build_overwrites(guild, cat_data["mode"])

            if not category:
                category = await create_with_retry(
                    guild=guild,
                    coro_fn=lambda name=cat_data["name"], ow=cat_ow: guild.create_category(
                        name=name, overwrites=ow
                    ),
                    name=cat_data["name"]
                )
                if not category:
                    embed_err = create_prestige_embed(
                        title="⚠️ FEHLER: Keine Kanäle erstellt!",
                        description=(
                            "> Ich habe keine Berechtigung, Kategorien oder Kanäle zu erstellen!\n"
                            "~~                                                              ~~\n"
                            "> **Behebung:**\n"
                            "> Bitte stelle sicher, dass mein Bot die Berechtigung **'Kanäle verwalten'** (Manage Channels) oder **'Administrator'** besitzt und führe `!Start` erneut aus."
                        ),
                        color=0x2b2d31,
                        author_user=ctx.author,
                        bot_user=self.bot.user
                    )
                    await status_msg.edit(embed=embed_err)
                    return
                await asyncio.sleep(0.3)
            
            for ch_data in cat_data["channels"]:
                ch_ow = self.build_overwrites(guild, ch_data.get("overwrite_mode", cat_data["mode"]))

                if ch_data["type"] == "voice":
                    channel = discord.utils.get(category.voice_channels, name=ch_data["name"])
                    if not channel:
                        channel = await create_with_retry(
                            guild=guild,
                            coro_fn=lambda name=ch_data["name"], cat=category, ow=ch_ow: guild.create_voice_channel(
                                name=name, category=cat, overwrites=ow
                            ),
                            name=ch_data["name"]
                        )
                        await asyncio.sleep(0.3)
                else:
                    channel = discord.utils.get(category.text_channels, name=ch_data["name"])
                    if not channel:
                        channel = await create_with_retry(
                            guild=guild,
                            coro_fn=lambda name=ch_data["name"], cat=category, ow=ch_ow, top=ch_data["description"]: guild.create_text_channel(
                                name=name, category=cat, overwrites=ow, topic=top
                            ),
                            name=ch_data["name"]
                        )
                        await asyncio.sleep(0.3)
                if channel:
                    channels_by_name[ch_data["name"]] = channel

        status_embed.description = "> 📝 Richte detaillierte Infokanäle, FAQs und Einladungs-Systeme ein..."
        await status_msg.edit(embed=status_embed)

        c_ticket_mention = channels_by_name["🎟️│create-ticket"].mention if "🎟️│create-ticket" in channels_by_name else "#create-ticket"
        c_ff_mention = channels_by_name["🚀│fastflags-pack"].mention if "🚀│fastflags-pack" in channels_by_name else "#fastflags-pack"

        # === NEUE PRODUKT-SHOWCASES (Components V2) ===
        product_showcases = [
            ("♾️│infinityxeh", "♾️ INFINITYxEH", 0x9b59ff,
             "**INFINITYxEH** — unser Premium All-in-One Executor der Extraklasse.\n\n"
             "✨ **Features:**\n♾️ Unlimitierte Script-Ausführung\n⚡ Ultra-schnelle Injection-Engine\n🔒 Stabil & regelmäßig geupdatet\n\n"
             "💰 **Preis:** `750 R$ / 7,50 €`"),
            ("💉│fflags-injector", "💉 FFlags Injector", 0x00d26a,
             "**FFlags Injector** — hol das Maximum an FPS & Performance heraus.\n\n"
             "✨ **Features:**\n💉 Automatischer FastFlag-Injector\n🚀 Bis zu +120 FPS Boost\n🎯 1-Klick Setup\n\n"
             "💰 **Preis:** `300 R$ / 3,00 €`"),
            ("🛡️│anti-ban", "🛡️ Anti-Ban", 0xff4757,
             "**Anti-Ban** — dein zuverlässiger Schutz gegen Bans.\n\n"
             "✨ **Features:**\n🛡️ Aktiver Ban-Schutz\n🕶️ Sicher & unauffällig\n🔄 Laufende Updates\n\n"
             "💰 **Preis:** `1.000 R$ / 10,00 €`"),
            ("👕│tshirt-templates", "👕 T-Shirt Templates", 0xffa500,
             "**T-Shirt Templates** — 50+ Roblox T-Shirt Vorlagen mit Verkaufsrechten.\n\n"
             "✨ **Features:**\n👕 PNG/PSD Dateien\n💼 Verkaufsrechte\n📦 Sofortige Lieferung\n\n"
             "💰 **Preis:** `500 R$ / 5,00 €`"),
            ("🚀│fastflags-pack", "🚀 FastFlags Pack", 0x00f0ff,
             "**FastFlags Pack** — Ultra FPS-Boost Config für Roblox.\n\n"
             "✨ **Features:**\n🚀 Performance Boost\n🎯 Stabile Flags\n🛠️ Setup-Hilfe\n\n"
             "💰 **Preis:** `150 R$ / 1,50 €`"),
            ("🖥️│discord-template", "🖥️ Discord Server Template", 0x5865f2,
             "**Discord Server Template** — Premium Shop-Layout mit Rollen & Kanälen.\n\n"
             "✨ **Features:**\n🖥️ Rollen & Kanäle\n🎟️ Ticket-Struktur\n⚡ Sofort nutzbar\n\n"
             "💰 **Preis:** `400 R$ / 4,00 €`"),
        ]
        for ch_name, title, color, body in product_showcases:
            ch_obj = channels_by_name.get(ch_name)
            if ch_obj:
                showcase_view = build_layout(
                    title=title,
                    body=body + f"\n\n🛒 **Jetzt kaufen** → erstelle ein Ticket in {c_ticket_mention}!",
                    accent=color,
                )
                await ch_obj.send(view=showcase_view)

        # A) REGELN
        c_rules = channels_by_name.get("📜│rules")
        if c_rules:
            embed_rules = create_prestige_embed(
                title="📜 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 - SERVER REGELN",
                description=(
                    "> Um eine sichere, professionelle und angenehme Atmosphäre für alle Kunden und Creator zu gewährleisten, bitten wir dich, die folgenden Richtlinien einzuhalten:\n"
                    "~~                                                              ~~\n"
                    "> 🤖 │ **𝟭. 𝗥𝗲𝘀𝗽𝗲𝗸𝘁 & 𝗛ö𝗳𝗹𝗶𝗰𝗵𝗸𝗲𝗶𝘁**\n"
                    "> Behandle jedes Mitglied und jeden Staff mit vollstem Respekt. Beleidigungen, Toxizität, Belästigung oder Drohungen jeglicher Art führen zum sofortigen Serverausschluss.\n"
                    "~~                                                              ~~\n"
                    "> 🚫 │ **𝟮. 𝗞𝗲𝗶𝗻 𝗦𝗽𝗮𝗺 & 𝗙𝗿𝗲𝗺𝗱𝘄𝗲𝗿𝗯𝘂𝗻𝗴**\n"
                    "> Spamming in den Kanälen ist verboten. Das Posten von Werbelinks zu anderen Discord-Servern, Dienstleistungen oder Fremdprodukten (sowohl in Chats als auch per DM) wird permanent gebannt.\n"
                    "~~                                                              ~~\n"
                    "> 🛒 │ **𝟯. 𝗦𝗶𝗰𝗵𝗲𝗿𝗲𝗿 & 𝗢𝗳𝗳𝗶𝘇𝗶𝗲𝗹𝗹𝗲𝗿 𝗛𝗮𝗻𝗱𝗲𝗹**\n"
                    "> Jegliche Verkäufe und Dienstleistungen finden ausschließlich über unser offizielles Ticket-System in %s statt. Privater Handel oder das Anbieten eigener Produkte ist untersagt.\n"
                    "~~                                                              ~~\n"
                    "> 📎 │ **𝟰. 𝗡𝗦𝗙𝗪 & Unangemessene Inhalte**\n"
                    "> Keine jugendgefährdenden, pornografischen, gewaltverherrlichenden oder illegalen Medien.\n"
                    "~~                                                              ~~\n"
                    "> 📌 │ **𝗛𝗶𝗻𝘄𝗲𝗶𝘀**\n"
                    "> Mit dem Aufenthalt auf diesem Server akzeptierst du die Discord Nutzungsbedingungen (TOS) sowie unsere Serverregeln. Unsere Moderatoren haben das Recht, bei Verstößen ohne Vorwarnung einzugreifen."
                ) % c_ticket_mention,
                color=0x2b2d31,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_rules.send(embed=embed_rules)

        # B) HOW TO BUY
        c_buy = channels_by_name.get("🛒│how-to-buy")
        if c_buy:
            embed_buy = create_prestige_embed(
                title="🛒 𝗩𝗢𝗜𝗗 • 𝗪𝗜𝗘 ＫＡＵＦＥ ＩＣＨ?",
                description=(
                    "> Der Ablauf eines Einkaufs bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** ist vollständig automatisiert und absolut sicher. Folge einfach diesem einfachen Ablauf:\n"
                    "~~                                                              ~~\n"
                    "> 1️⃣ │ **Ticket erstellen**\n"
                    f"> Besuche den Kanal {c_ticket_mention} und klicke auf den Button **'Produkt kaufen'**. Ein privater Supportkanal wird nur für dich erstellt.\n"
                    "~~                                                              ~~\n"
                    "> 2️⃣ │ **Produktdetails angeben**\n"
                    "> Teile unserem Supportteam im Ticket mit, was du kaufen möchtest (z.B. Premium FastFlags, bestimmte T-Shirt Templates, Serverlayouts).\n"
                    "~~                                                              ~~\n"
                    "> 3️⃣ │ **Zahlungsabwicklung**\n"
                    "> Wähle deine bevorzugte Zahlungsmethode aus. Wir unterstützen:\n"
                    "> 🔹 PayPal (Familie & Freunde)\n"
                    "> 🔹 Robux (via Gamepass oder Gruppen-Auszahlung)\n"
                    "> 🔹 Paysafecard\n"
                    "> 🔹 Kryptowährungen (Litecoin - LTC, Bitcoin - BTC, USDT)\n"
                    "~~                                                              ~~\n"
                    "> 4️⃣ │ **Lieferung erhalten**\n"
                    "> Nach der Zahlungsbestätigung wird dein digitales Produkt (Config, Code, PNG-Download) direkt im Ticket an dich übergeben!"
                ),
                color=0x2b2d31,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_buy.send(embed=embed_buy)

        # C) PRODUCTS — Components V2 mit zentralem Live-Katalog
        c_products = channels_by_name.get("📦│products")
        if c_products:
            from bot.cogs.tickets import build_products_panel_view
            ticket_mention = c_ticket_mention
            await c_products.send(view=build_products_panel_view(ticket_mention))

        # D) TICKET PANEL
        c_ticket_panel = channels_by_name.get("🎟️│create-ticket")
        if c_ticket_panel:
            from bot.cogs.tickets import TicketButton
            await c_ticket_panel.send(view=TicketButton())

        # E) FAQ
        c_faq = channels_by_name.get("❓│faq")
        if c_faq:
            embed_faq = create_prestige_embed(
                title="❓ 𝗩𝗢𝗜𝗗 • FAQ (Häufige Fragen)",
                description=(
                    "> **Sind FastFlags erlaubt?**\n"
                    "> Ja, FastFlags sind Teil der offiziellen Roblox-Einstellungen. Es ist keine Cheat-Software!\n"
                    "~~                                                              ~~\n"
                    "> **Wie lange dauert die Lieferung?**\n"
                    "> Fast immer innerhalb von 15 Minuten nach Zahlungseingang im Ticket."
                ),
                color=0x2b2d31,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_faq.send(embed=embed_faq)

        # F) INVITES
        c_inv = channels_by_name.get("📩│invites")
        if c_inv:
            embed_inv = create_prestige_embed(
                title="📩 𝗩𝗢𝗜𝗗 • Invite Belohnungen",
                description=(
                    "> Lade Freunde auf unseren Server ein und staube dicke Gewinne ab:\n"
                    "~~                                                              ~~\n"
                    "> 🎁 │ **5 Invites** ➔ Gratis T-Shirt Template\n"
                    "> 🎁 │ **10 Invites** ➔ Gratis Premium FastFlags\n"
                    "> 🎁 │ **20 Invites** ➔ Gratis Discord Server-Layout"
                ),
                color=0x2b2d31,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_inv.send(embed=embed_inv)

        # G) VERIFY HERE PANEL
        c_v_here = channels_by_name.get("🔐│verify-here")
        if c_v_here:
            from bot.cogs.verification import SimpleVerifyButton
            await c_v_here.send(view=SimpleVerifyButton())

        # H) FIRST VOUCH PREPARATION IN #vouches
        c_vouches = channels_by_name.get("🤝│vouches")
        if c_vouches:
            embed_vouch_placeholder = create_prestige_embed(
                title="🤝 𝗩𝗢𝗜𝗗 • ＫＵＮＤＥＮ-Ｂ𝗘ＷＥＲ𝗧ＵＮＧＥＮ 🤝",
                description=(
                    "> Kundenzufriedenheit steht bei uns an oberster Stelle!\n"
                    "~~                                                              ~~\n"
                    "> Wenn du bei uns eingekauft hast, würden wir uns sehr über eine Bewertung freuen. Das hilft uns und stärkt das Vertrauen neuer Kunden.\n"
                    "~~                                                              ~~\n"
                    "> **Beispiel für eine Bewertung:**\n"
                    "> ⭐ ⭐ ⭐ ⭐ ⭐ - *Sehr schneller Support, FastFlags funktionieren perfekt und habe direkt +120 FPS bekommen! Gerne wieder!*"
                ),
                color=0x2b2d31,
                author_user=ctx.author,
                bot_user=self.bot.user
            )
            await c_vouches.send(embed=embed_vouch_placeholder)

        stats_cog = self.bot.get_cog("StatsCog")
        if stats_cog:
            await stats_cog.update_stats_channels(guild)

        status_embed.title = "🎉 Server-Setup erfolgreich abgeschlossen! 🎉"
        status_embed.description = (
            f"> 📁 **Kategorien & Kanäle:** 44 Kanäle erfolgreich eingerichtet.\n"
            f"> 🔒 **Rechte:** Hochsicheres, dynamisches Rechtesystem für alle 23 Rollen aktiv.\n"
            f"> 🎟️ **Tickets:** Interaktive Multi-Tickets mit Claim-Funktion sind einsatzbereit!\n"
            "~~                                                              ~~\n"
            f"> Nutze `!Start` oder lösche diese Nachricht, falls gewünscht."
        )
        status_embed.color = 0x2b2d31
        await status_msg.edit(embed=status_embed)
