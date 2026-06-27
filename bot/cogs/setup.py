"""
Setup Cog - Kompletter Server-Setup mit verbessertem Rate-Limiting.
Alle Rollen, Kanäle, Berechtigungen und Embeds werden erstellt.
Jetz als /setup Slash Command.
"""

import asyncio
import logging
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db

logger = logging.getLogger("void_shop_bot.setup")


# --- RATE-LIMIT WRAPPER ---

async def safe_role_create(guild, name, color, hoist=True, mentionable=True, reason="VOID Setup", max_retries=5):
    """Erstelle eine Rolle mit robustem Rate-Limit-Schutz."""
    for attempt in range(max_retries):
        try:
            role = await guild.create_role(
                name=name,
                color=discord.Color(color),
                hoist=hoist,
                mentionable=mentionable,
                reason=reason,
            )
            logger.info(f"✅ Rolle erstellt ({attempt+1}/{max_retries}): {name}")
            return role
        except discord.HTTPException as e:
            if e.status == 429:
                wait = (e.retry_after if e.retry_after else 5) + (attempt * 1.5)
                logger.warning(f"⏳ Rate-Limit bei Rolle '{name}', warte {wait:.1f}s (Versuch {attempt+1}/{max_retries})")
                await asyncio.sleep(wait)
            else:
                logger.error(f"❌ HTTPException bei Rolle '{name}': {e}")
                return None
        except discord.Forbidden as e:
            logger.error(f"❌ Forbidden bei Rolle '{name}': {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Fehler bei Rolle '{name}': {e}")
            return None
    logger.error(f"❌ Max Retries erreicht für Rolle '{name}'")
    return None


async def safe_channel_create(guild, channel_type, name, category=None, overwrites=None, topic=None, reason="VOID Setup", max_retries=5):
    """Erstelle einen Kanal mit robustem Rate-Limit-Schutz."""
    for attempt in range(max_retries):
        try:
            if channel_type == "voice":
                ch = await guild.create_voice_channel(
                    name=name, category=category, overwrites=overwrites or {}, reason=reason
                )
            else:
                ch = await guild.create_text_channel(
                    name=name, category=category, overwrites=overwrites or {}, topic=topic or "", reason=reason
                )
            logger.info(f"✅ Kanal erstellt ({attempt+1}/{max_retries}): {name}")
            return ch
        except discord.HTTPException as e:
            if e.status == 429:
                wait = (e.retry_after if e.retry_after else 5) + (attempt * 1.5)
                logger.warning(f"⏳ Rate-Limit bei Kanal '{name}', warte {wait:.1f}s (Versuch {attempt+1}/{max_retries})")
                await asyncio.sleep(wait)
            else:
                logger.error(f"❌ HTTPException bei Kanal '{name}': {e}")
                return None
        except discord.Forbidden as e:
            logger.error(f"❌ Forbidden bei Kanal '{name}': {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Fehler bei Kanal '{name}': {e}")
            return None
    logger.error(f"❌ Max Retries erreicht für Kanal '{name}'")
    return None


# --- SETUP CONFIRMATION VIEW ---

class SetupConfirmationView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.value = None

    @app_commands.checks.has_permissions(administrator=True)
    @discord.ui.button(label="🧹 Komplett neu aufsetzen", style=discord.ButtonStyle.danger, emoji="🧹")
    async def reset_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "reset"
        self.stop()

    @discord.ui.button(label="➕ Nur hinzufügen", style=discord.ButtonStyle.success, emoji="➕")
    async def add_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "add"
        self.stop()

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "cancel"
        self.stop()


class SetupCog(commands.Cog, name="SetupCog"):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================================================
    # BERECHTIGUNGS-OVERWRITES
    # ==========================================================================
    def build_overwrites(self, mode, r_everyone, staff_roles, member_roles, high_staff, r_booster, r_vip, r_member, r_customer, r_premium_buyer):
        """Erstellt Overwrites basierend auf dem Kanal-Typ."""
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

    # ==========================================================================
    # /setup SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="setup", description="🔧 Komplettes Server-Setup: Rollen, Kanäle, Rechte & Embeds")
    @app_commands.describe(
        modus="Wähle: 'reset' löscht alles und baut neu auf, 'add' ergänzt nur Fehlendes"
    )
    @app_commands.choices(modus=[
        app_commands.Choice(name="🧹 Komplett neu aufsetzen (löscht alles)", value="reset"),
        app_commands.Choice(name="➕ Nur hinzufügen (ergänzt)", value="add"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def setup_command(self, interaction: discord.Interaction, modus: str):
        """
        KOMPLETTER SERVER-SETUP als Slash Command.
        Reihenfolge: Rollen → Kanäle → Rechte → Embeds
        """
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("❌ Dieser Befehl kann nur auf einem Server genutzt werden.", ephemeral=True)
            return

        bot_member = guild.me

        # ═══════════════════════════════════════
        # BESTÄTIGUNG HOLEN
        # ═══════════════════════════════════════
        embed_choice = EmbedHelper.create_prestige_embed(
            title="⚠️ 𝗩𝗢𝗜𝗗 • SERVER SETUP INITIALISIERUNG ⚠️",
            description=(
                f"Hallo {interaction.user.mention},\n\n"
                "du bist dabei, das **Prestige Server-Layout** für **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** aufzubauen.\n"
                "Dieses Setup generiert:\n"
                "> 👑 │ **23 Premium-Rollen** mit optimalen Berechtigungen\n"
                "> 📁 │ **10 Kategorien mit insgesamt 42 Kanälen**\n"
                "> ⚙️ │ **Vollständiges Embed-Design in allen Infokanälen**\n\n"
                f"**Gewählter Modus:** `{modus}`\n\n"
                "Bitte bestätige mit einem der Buttons unten:"
            ),
            color=0xFF003C,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )

        view = SetupConfirmationView(interaction.user.id)
        await interaction.response.send_message(embed=embed_choice, view=view, ephemeral=True)
        await view.wait()

        if view.value is None or view.value == "cancel":
            embed_cancel = EmbedHelper.create_prestige_embed(
                title="❌ Setup abgebrochen",
                description="> Das Server-Setup wurde abgebrochen. Es wurden keine Änderungen vorgenommen.",
                color=0x3E3E3E,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await interaction.edit_original_response(embed=embed_cancel, view=None)
            return

        # Followup für Status-Nachrichten
        status_embed = EmbedHelper.create_prestige_embed(
            title="⚙️ Setup-Prozess läuft...",
            description="> ⏳ Initialisiere...",
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        status_msg = await interaction.followup.send(embed=status_embed, ephemeral=True, wait=True)

        # ═══════════════════════════════════════
        # SCHRITT 0: RESET (falls gewählt)
        # ═══════════════════════════════════════
        if modus == "reset":
            await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
                title="⚙️ Setup-Prozess läuft...",
                description="> 🧹 Lösche alte Kanäle...",
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
                title="⚙️ Setup-Prozess läuft...",
                description="> 🧹 Lösche alte Rollen...",
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

        # ═══════════════════════════════════════
        # SCHRITT 1: ALLE 23 ROLLEN ERSTELLEN (FIXED)
        # ═══════════════════════════════════════
        await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
            title="⚙️ Setup-Prozess läuft...",
            description="> 👑 **Schritt 1/4:** Erstelle 23 Premium-Rollen...",
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))

        role_definitions = [
            ("🤖│ 𝗩𝗢𝗜𝗗 • 𝗕𝗼𝘁", 0x4A00A8),
            ("👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿", 0xA0A0A0),
            ("📦│ 𝗣𝗿𝗼𝗱𝘂𝗰𝘁 𝗣𝗶𝗻𝗴", 0x32CD32),
            ("🎁│ 𝗚𝗶𝘃𝗲𝗮𝘄𝗮𝘆 𝗣𝗶𝗻𝗴", 0xFF4500),
            ("📢│ 𝗔𝗻𝗻𝗼𝘂𝗻𝗰𝗲𝗺𝗲𝗻𝘁 𝗣𝗶𝗻𝗴", 0x7289DA),
            ("🥉│ 𝗕𝗿𝗼𝗻𝘇𝗲 𝗕𝘂𝘆𝗲𝗿", 0xCD7F32),
            ("🥈│ 𝗦𝗶𝗹𝘃𝗲𝗿 𝗕𝘂𝘆𝗲𝗿", 0xC0C0C0),
            ("🥇│ 𝗚𝗼𝗹𝗱 𝗕𝘂𝘆𝗲𝗿", 0xFFD700),
            ("💎│ 𝗗𝗶𝗮𝗺𝗼𝗻𝗱 𝗕𝘂𝘆𝗲𝗿", 0xB9F2FF),
            ("🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿", 0xFFFF00),
            ("💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿", 0x00FFFF),
            ("👤│ 𝗩𝗢𝗜𝗗 • 𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱", 0x7F8C8D),
            ("🫂│ 𝗩𝗢𝗜𝗗 • 𝗙𝗿𝗶𝗲𝗻𝗱", 0xFF69B4),
            ("🌟│ 𝗩𝗢𝗜𝗗 • 𝗩𝗜𝗣", 0xFFD700),
            ("💎│ 𝗩𝗢𝗜𝗗 • 𝗕𝗼𝗼𝘀𝘁𝗲𝗿", 0xF47FFF),
            ("🤝│ 𝗩𝗢𝗜𝗗 • 𝗣𝗮𝗿𝘁𝗻𝗲𝗿", 0xFFA500),
            ("🚨│ 𝗩𝗢𝗜𝗗 • 𝗧𝗿𝗶𝗮𝗹 𝗠𝗼𝗱", 0xADFF2F),
            ("🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁", 0x20B2AA),
            ("🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿", 0x39FF14),
            ("⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿", 0x00A8A8),
            ("🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻", 0x00F0FF),
            ("👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿", 0xFF3366),
            ("👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿", 0xFF003C),
        ]

        all_roles = {}
        roles_created = 0
        roles_skipped = 0
        roles_failed = 0
        role_errors = []
        total_roles = len(role_definitions)

        # ⚠️ WICHTIG: Hole die Bot-Position EINMAL am Anfang, damit Rollen richtig sortiert werden
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
                        title="⚙️ Setup-Prozess läuft...",
                        description=(
                            f"> 👑 **Schritt 1/4:** Erstelle Rollen... ({idx}/{total_roles})\n"
                            f"> Aktuell: `{role_name}`"
                        ),
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
                # Versuche die Rolle direkt über die Bot-Position zu schieben
                try:
                    await result.edit(position=bot_top_role.position - 1 if bot_top_role.position > 0 else 1)
                except Exception as e:
                    logger.debug(f"Konnte Rolle {role_name} nicht positionieren: {e}")
            else:
                roles_failed += 1
                role_errors.append(f"{role_name}: Erstellung fehlgeschlagen")

            # ⚠️ Rate-Limit Pause zwischen Rollen (Discord erlaubt max 2 Rollen-Erstellungen pro 10s)
            await asyncio.sleep(1.5)

        if roles_created == 0 and roles_skipped == 0:
            error_list = "\n".join(f"> ❌ {err}" for err in role_errors[:10])
            await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
                title="⚠️ FEHLER: Keine Rollen erstellt!",
                description=(
                    "> Es konnte **keine einzige Rolle** erstellt werden!\n\n"
                    "**Fehlerdetails:**\n"
                    f"{error_list}\n\n"
                    "**So behebst du das:**\n"
                    "1. **Server-Einstellungen** ➔ **Rollen**\n"
                    "2. Ziehe die Bot-Rolle **ganz nach oben** (über alle anderen Rollen)\n"
                    "3. Gib der Bot-Rolle **Administrator**-Berechtigung\n"
                    "4. Führe `/setup` erneut aus"
                ),
                color=0xFF003C,
                author_user=interaction.user,
                bot_user=self.bot.user,
            ))
            return

        error_note = ""
        if roles_failed > 0:
            error_note = f"\n> ⚠️ **{roles_failed} Rollen fehlgeschlagen** (Bot-Rolle höher ziehen!)"

        await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
            title="⚙️ Setup-Prozess läuft...",
            description=(
                f"> 👑 **Schritt 1/4:** ✅ Rollen fertig!\n"
                f"> Erstellt: **{roles_created}** | Übersprungen: **{roles_skipped}**{error_note}\n\n"
                f"> 📁 **Schritt 2/4:** Erstelle Kategorien & Kanäle..."
            ),
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))

        # ═══════════════════════════════════════
        # SCHRITT 2: ROLLEN-REFERENZEN
        # ═══════════════════════════════════════
        r_everyone = guild.default_role

        def get_role(name):
            return all_roles.get(name, r_everyone)

        r_member = get_role("👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿")
        r_customer = get_role("🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿")
        r_premium_buyer = get_role("💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿")
        r_vip = get_role("🌟│ 𝗩𝗢𝗜𝗗 • 𝗩𝗜𝗣")
        r_booster = get_role("💎│ 𝗩𝗢𝗜𝗗 • 𝗕𝗼𝗼𝘀𝘁𝗲𝗿")
        r_partner = get_role("🤝│ 𝗩𝗢𝗜𝗗 • 𝗣𝗮𝗿𝘁𝗻𝗲𝗿")
        r_support = get_role("🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁")
        r_trial_mod = get_role("🚨│ 𝗩𝗢𝗜𝗗 • 𝗧𝗿𝗶𝗮𝗹 𝗠𝗼𝗱")
        r_mod = get_role("🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿")
        r_manager = get_role("⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿")
        r_admin = get_role("🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻")
        r_co_owner = get_role("👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿")
        r_owner = get_role("👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿")

        staff_roles = [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]
        member_roles = [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]
        high_staff = [r_manager, r_admin, r_co_owner, r_owner]

        # ═══════════════════════════════════════
        # SCHRITT 3: KATEGORIEN & KANÄLE
        # ═══════════════════════════════════════
        def make_cat_overwrites(mode):
            return self.build_overwrites(
                mode, r_everyone, staff_roles, member_roles,
                high_staff, r_booster, r_vip, r_member, r_customer, r_premium_buyer
            )

        categories_layout = [
            {
                "name": "📊│── 𝗩𝗢𝗜𝗗 • 𝗦𝗧𝗔𝗧𝗦 ──",
                "mode": "stats",
                "channels": [
                    {"name": "👥│Mitglieder: 0", "type": "voice"},
                    {"name": "💎│Booster: 0", "type": "voice"},
                    {"name": "🛒│Kunden: 0", "type": "voice"},
                    {"name": "🎟️│Offene Tickets: 0", "type": "voice"},
                ],
            },
            {
                "name": "🔐│── 𝗩𝗢𝗜𝗗 • 𝗩𝗘𝗥𝗜𝗙𝗬 ──",
                "mode": "verify",
                "channels": [
                    {"name": "👋│willkommen", "type": "text", "topic": "Begrüßungskanal für neue Mitglieder"},
                    {"name": "🔐│verify-here", "type": "text", "topic": "Klicke unten auf den Button, um dich freizuschalten!"},
                ],
            },
            {
                "name": "📢│── 𝗩𝗢𝗜𝗗 • 𝗜𝗡𝗙𝗢 ──",
                "mode": "info",
                "channels": [
                    {"name": "📢│news", "type": "text", "topic": "Wichtige Ankündigungen & News"},
                    {"name": "📜│rules", "type": "text", "topic": "Das Serverregelwerk"},
                    {"name": "💨│aufwiedersehen", "type": "text", "topic": "Verabschiedungskanal"},
                    {"name": "🎁│giveaways", "type": "text", "topic": "Spannende Giveaways & Gewinne"},
                    {"name": "🤝│vouches", "type": "text", "topic": "Erfahrungen unserer Käufer"},
                    {"name": "📩│invites", "type": "text", "topic": "Lade Freunde ein für Belohnungen!"},
                    {"name": "🔗│partners", "type": "text", "topic": "Unsere Partner-Server"},
                ],
            },
            {
                "name": "🛒│── 𝗩𝗢𝗜𝗗 • 𝗦𝗛𝗢𝗣 ──",
                "mode": "info",
                "channels": [
                    {"name": "👕│tshirt-templates", "type": "text", "topic": "Exklusive T-Shirt Vorlagen für Roblox"},
                    {"name": "⚙️│fastflags", "type": "text", "topic": "FPS & Performance Optimierungen"},
                    {"name": "🖥️│discord-templates", "type": "text", "topic": "Schicke Discord Server Vorlagen"},
                    {"name": "📦│products", "type": "text", "topic": "Unsere Produkt- & Preisübersicht"},
                    {"name": "🛒│how-to-buy", "type": "text", "topic": "Wie du bei uns einkaufen kannst"},
                    {"name": "📈│updates", "type": "text", "topic": "Entwicklungs-Updates & Produktnews"},
                    {"name": "🛍️│live-käufe", "type": "text", "topic": "Live Feier-Ticker für erfolgreiche Shop-Käufe"},
                ],
            },
            {
                "name": "💬│── 𝗩𝗢𝗜𝗗 • 𝗖𝗛𝗔𝗧 ──",
                "mode": "community",
                "channels": [
                    {"name": "💬│general-chat", "type": "text", "topic": "Der Hauptchat für jedermann"},
                    {"name": "📷│media-and-showcase", "type": "text", "topic": "Teile Bilder, Videos oder Avatare"},
                    {"name": "🎨│clothing-showcase", "type": "text", "topic": "Zeige deine eigenen Roblox-Kleidungsdesigns!"},
                    {"name": "🖥️│setup-showcase", "type": "text", "topic": "Zeige deinen Gaming-Setup oder Studio-Setup"},
                    {"name": "📈│trading", "type": "text", "topic": "Tausche und handle mit Roblox-Gegenständen"},
                    {"name": "🤝│suggestions", "type": "text", "topic": "Deine Verbesserungsvorschläge für den Shop"},
                    {"name": "🤖│bot-commands", "type": "text", "topic": "Nutze die Bot-Befehle hier"},
                ],
            },
            {
                "name": "🎙️│── 𝗩𝗢𝗜𝗗 • 𝗧𝗔𝗟𝗞 ──",
                "mode": "community",
                "channels": [
                    {"name": "🔊│Lobby • Public", "type": "voice"},
                    {"name": "🔊│Lounge • Chill", "type": "voice"},
                    {"name": "🔊│Roblox • Talk", "type": "voice"},
                    {"name": "🔊│Gaming • Duo", "type": "voice"},
                    {"name": "🔊│Gaming • Squad", "type": "voice"},
                    {"name": "🔊│Support • Voice", "type": "voice"},
                ],
            },
            {
                "name": "💎│── 𝗩𝗢𝗜𝗗 • 𝗟𝗢𝗨𝗡𝗚𝗘 ──",
                "mode": "community",
                "channels": [
                    {"name": "💎│booster-lounge", "type": "text", "topic": "Spezialchat für Server-Booster", "overwrite_mode": "booster_lounge"},
                    {"name": "🌟│vip-lounge", "type": "text", "topic": "Exklusiver Chat für VIP-Kunden", "overwrite_mode": "vip_lounge"},
                    {"name": "🛒│customer-lounge", "type": "text", "topic": "Austauschbereich für alle Käufer", "overwrite_mode": "customer_lounge"},
                ],
            },
            {
                "name": "🎟️│── 𝗩𝗢𝗜𝗗 • 𝗦𝗨𝗣𝗣𝗢𝗥𝗧 ──",
                "mode": "info",
                "channels": [
                    {"name": "🎟️│create-ticket", "type": "text", "topic": "Erstelle ein Support- oder Kauf-Ticket"},
                    {"name": "❓│faq", "type": "text", "topic": "Häufig gestellte Fragen (FAQs)"},
                ],
            },
            {
                "name": "🔒│── 𝗩𝗢𝗜𝗗 • 𝗦𝗧𝗔𝗙𝗙 ──",
                "mode": "staff",
                "channels": [
                    {"name": "🔒│staff-chat", "type": "text", "topic": "Das interne Besprechungszimmer"},
                    {"name": "🛠️│mod-commands", "type": "text", "topic": "Eingabe von Admin- und Moderations-Commands"},
                    {"name": "🔊│Staff • Voice", "type": "voice"},
                ],
            },
            {
                "name": "📁│── 𝗩𝗢𝗜𝗗 • 𝗟𝗢𝗚𝗦 ──",
                "mode": "logs",
                "channels": [
                    {"name": "💬│voice-logs", "type": "text", "topic": "Logs für Sprachkanäle"},
                    {"name": "🔨│ban-kick-logs", "type": "text", "topic": "Logs für Banns, Kicks und Timeouts"},
                    {"name": "📝│message-logs", "type": "text", "topic": "Logs für gelöschte & editierte Nachrichten"},
                    {"name": "📩│invite-logs", "type": "text", "topic": "Logs für erstellte & genutzte Einladungslinks"},
                    {"name": "📥│join-leave-logs", "type": "text", "topic": "Logs für Serverbeitritte & Austritte"},
                    {"name": "💾│ticket-logs", "type": "text", "topic": "Ticket-Protokolle & Transkripte"},
                    {"name": "⚙️│system-logs", "type": "text", "topic": "System-Logs für Kanäle & Rollen"},
                    {"name": "🚨│security-logs", "type": "text", "topic": "Logs für blockierte Scam- & Phishing-Links"},
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
                    title="⚙️ Setup-Prozess läuft...",
                    description=(
                        f"> 👑 **Schritt 1/4:** ✅ {roles_created} Rollen erstellt, {roles_skipped} übersprungen\n\n"
                        f"> 📁 **Schritt 2/4:** Erstelle Kanäle... (Kategorie {cat_idx}/{total_categories})\n"
                        f"> Aktuell: `{cat_data['name']}`"
                    ),
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
                        title="⚠️ FEHLER: Keine Berechtigung für Kanäle!",
                        description=(
                            "> Ich kann keine Kategorien/Kanäle erstellen!\n\n"
                            "**Behebung:**\n"
                            "> 1. Bot-Rolle in den Server-Einstellungen ganz nach oben ziehen\n"
                            "> 2. **Administrator**-Berechtigung aktivieren\n"
                            "> 3. `/setup` erneut ausführen"
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
            title="⚙️ Setup-Prozess läuft...",
            description=(
                f"> 👑 **Schritt 1/4:** ✅ {roles_created} Rollen erstellt, {roles_skipped} übersprungen\n"
                f"> 📁 **Schritt 2/4:** ✅ {channels_created} Kanäle erstellt\n"
                f"> 🔒 **Schritt 3/4:** ✅ Berechtigungen gesetzt\n\n"
                f"> 📝 **Schritt 4/4:** Sende Embed-Nachrichten..."
            ),
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))

        # ═══════════════════════════════════════
        # SCHRITT 4: EMBED-NACHRICHTEN (1:1 ORIGINAL)
        # ═══════════════════════════════════════
        c_ticket_mention = channels_by_name["🎟️│create-ticket"].mention if "🎟️│create-ticket" in channels_by_name else "#create-ticket"
        c_ff_mention = channels_by_name["⚙️│fastflags"].mention if "⚙️│fastflags" in channels_by_name else "#fastflags"

        # A) REGELN
        c_rules = channels_by_name.get("📜│rules")
        if c_rules:
            embed_rules = EmbedHelper.create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📜 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 - SERVER REGELN\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description=(
                    "Um eine sichere, professionelle und angenehme Atmosphäre für alle Kunden und Creator zu gewährleisten, "
                    "bitten wir dich, die folgenden Richtlinien einzuhalten:\n\n"
                    "🤖 │ **𝟭. 𝗥𝗲𝘀𝗽𝗲𝗸𝘁 & 𝗛ö𝗳𝗹𝗶𝗰𝗵𝗸𝗲𝗶𝘁**\n"
                    "> Behandle jedes Mitglied und jeden Staff mit vollstem Respekt. "
                    "Beleidigungen, Toxizität, Belästigung oder Drohungen jeglicher Art führen zum sofortigen Serverausschluss.\n\n"
                    "🚫 │ **𝟮. 𝗞𝗲𝗶𝗻 𝗦𝗽𝗮𝗺 & 𝗙𝗿𝗲𝗺𝗱𝘄𝗲𝗿𝗯𝘂𝗻𝗴**\n"
                    "> Spamming in den Kanälen ist verboten. Das Posten von Werbelinks zu anderen Discord-Servern, "
                    "Dienstleistungen oder Fremdprodukten (sowohl in Chats als auch per DM) wird permanent gebannt.\n\n"
                    "🛒 │ **𝟯. 𝗦𝗶𝗰𝗵𝗲𝗿𝗲𝗿 & 𝗢𝗳𝗳𝗶𝘇𝗶𝗲𝗹𝗹𝗲𝗿 𝗛𝗮𝗻𝗱𝗲𝗹**\n"
                    f"> Jegliche Verkäufe und Dienstleistungen finden ausschließlich über unser offizielles "
                    f"Ticket-System in {c_ticket_mention} statt. Privater Handel oder das Anbieten eigener "
                    "Produkte ist untersagt.\n\n"
                    "📎 │ **𝟰. 𝗡𝗦𝗙𝗪 & Unangemessene Inhalte**\n"
                    "> Keine jugendgefährdenden, pornografischen, gewaltverherrlichenden oder illegalen Medien.\n\n"
                    "📌 │ **𝗛𝗶𝗻𝘄𝗲𝗶𝘀**\n"
                    "> Mit dem Aufenthalt auf diesem Server akzeptierst du die Discord Nutzungsbedingungen (TOS) "
                    "sowie unsere Serverregeln. Unsere Moderatoren haben das Recht, bei Verstößen ohne Vorwarnung einzugreifen."
                ),
                color=0xFF003C,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_rules.send(embed=embed_rules)

        # B) HOW TO BUY
        c_buy = channels_by_name.get("🛒│how-to-buy")
        if c_buy:
            embed_buy = EmbedHelper.create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🛒 𝗩𝗢𝗜𝗗 • 𝗪𝗜𝗘 𝗞𝗔𝗨𝗙𝗘 𝗜𝗖𝗛?\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description=(
                    "Der Ablauf eines Einkaufs bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** ist vollständig automatisiert und absolut sicher. "
                    "Folge einfach diesem einfachen Ablauf:\n\n"
                    "1️⃣ │ **Ticket erstellen**\n"
                    f"> Besuche den Kanal {c_ticket_mention} und klicke auf den Button **"
                    "Produkt kaufen"**. Ein privater Supportkanal wird nur für dich erstellt.\n\n"
                    "2️⃣ │ **Produktdetails angeben**\n"
                    "> Teile unserem Supportteam im Ticket mit, was du kaufen möchtest "
                    "(z.B. Premium FastFlags, bestimmte T-Shirt Templates, Serverlayouts).\n\n"
                    "3️⃣ │ **Zahlungsabwicklung**\n"
                    "> Wähle deine bevorzugte Zahlungsmethode aus. Wir unterstützen:\n"
                    "> 🔹 PayPal (Familie & Freunde)\n"
                    "> 🔹 Robux (via Gamepass oder Gruppen-Auszahlung)\n"
                    "> 🔹 Paysafecard\n"
                    "> 🔹 Kryptowährungen (Litecoin - LTC, Bitcoin - BTC, USDT)\n\n"
                    "4️⃣ │ **Lieferung erhalten**\n"
                    "> Nach der Zahlungsbestätigung wird dein digitales Produkt "
                    "(Config, Code, PNG-Datei) direkt im Ticket an dich übergeben!"
                ),
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_buy.send(embed=embed_buy)

        # C) PRODUCTS
        c_products = channels_by_name.get("📦│products")
        if c_products:
            embed_products = EmbedHelper.create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📦 𝗩𝗢𝗜𝗗 • 𝗨𝗡𝗦𝗘𝗥𝗘 𝗣𝗥𝗢𝗗𝗨𝗞𝗧𝗘\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description=(
                    "Finde hier deine Roblox- und Discord-Upgrades:\n\n"
                    "**👕 Roblox Kleidung:**\n"
                    "> • *Klassische T-Shirt PNGs:* ab 50 Robux / 0,50€\n"
                    "> • *Exklusive Bundles (50+ Vorlagen):* ab 500 Robux / 5,00€\n\n"
                    "**⚙️ FastFlags (FPS-Boost):**\n"
                    f"> • *Standard-Configs:* Gratis (siehe {c_ff_mention})\n"
                    "> • *Premium Ultra Configs:* 150 Robux / 1,50€\n\n"
                    "**🖥️ Discord Templates:**\n"
                    "> • *Fertiges Shop-Layout:* 400 Robux / 4,00€"
                ),
                color=0xFFD700,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_products.send(embed=embed_products)

        # D) TICKET PANEL
        c_ticket_panel = channels_by_name.get("🎟️│create-ticket")
        if c_ticket_panel:
            embed_ticket_panel = EmbedHelper.create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎟️ 𝗩𝗢𝗜𝗗 • Support & Kauf-Center\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description=(
                    "Benötigst du Hilfe oder möchtest etwas kaufen?\n"
                    "Wähle einfach die passende Kategorie aus:\n\n"
                    "> 🛒 │ **Produkt kaufen** ➔ Roblox Items, FastFlags, Templates\n"
                    "> ⚙️ │ **Allgemeiner Support** ➔ Technische Hilfe\n"
                    "> 🤝 │ **Partnerschaft** ➔ Für Kooperationen"
                ),
                color=0x00F0FF,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            from bot.cogs.tickets import TicketButton
            await c_ticket_panel.send(embed=embed_ticket_panel, view=TicketButton())

        # E) FAQ
        c_faq = channels_by_name.get("❓│faq")
        if c_faq:
            embed_faq = EmbedHelper.create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n❓ 𝗩𝗢𝗜𝗗 • FAQ (Häufige Fragen)\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
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

        # F) INVITES
        c_inv = channels_by_name.get("📩│invites")
        if c_inv:
            embed_inv = EmbedHelper.create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📩 𝗩𝗢𝗜𝗗 • Invite Belohnungen\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description=(
                    "Lade Freunde auf unseren Server ein und staube dicke Gewinne ab:\n\n"
                    "> 🎁 │ **5 Invites** ➔ Gratis T-Shirt Template\n"
                    "> 🎁 │ **10 Invites** ➔ Gratis Premium FastFlags\n"
                    "> 🎁 │ **20 Invites** ➔ Gratis Discord Server-Layout"
                ),
                color=0xFFA500,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_inv.send(embed=embed_inv)

        # G) VERIFY HERE PANEL
        c_v_here = channels_by_name.get("🔐│verify-here")
        if c_v_here:
            embed_v_here = EmbedHelper.create_prestige_embed(
                title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🔐 𝗩𝗢𝗜𝗗 • SERVEREINTRETEN VERIFIZIERUNG\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                description=(
                    "Herzlich Willkommen bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**!\n\n"
                    "Um vollen Zugriff auf den Server (Chats, Produkte, Giveaways) zu erhalten, "
                    "musst du dich verifizieren.\n\n"
                    "**So einfach geht's:**\n"
                    "> 1️⃣ │ Klicke unten auf den grünen Button **'Verifizieren 🔐'**.\n"
                    "> 2️⃣ │ Du erhältst sofort die **Member-Rolle** und wirst freigeschaltet.\n\n"
                    "*Hinweis: Für erweiterte Käufe kannst du zusätzlich die Roblox-Verifizierung nutzen!*"
                ),
                color=0x39FF14,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            from bot.cogs.verification import SimpleVerifyButton
            await c_v_here.send(embed=embed_v_here, view=SimpleVerifyButton())

        # H) VOUCHES
        c_vouches = channels_by_name.get("🤝│vouches")
        if c_vouches:
            embed_vouch_placeholder = EmbedHelper.create_prestige_embed(
                title="🤝 𝗩𝗢𝗜𝗗 • 𝗞𝗨𝗡𝗗𝗘𝗡-𝗕𝗘𝗪𝗘𝗥𝗧𝗨𝗡𝗚𝗘𝗡 🤝",
                description=(
                    "Kundenzufriedenheit steht bei uns an oberster Stelle!\n\n"
                    "Wenn du bei uns eingekauft hast, würden wir uns sehr über eine Bewertung freuen. "
                    "Das hilft uns und stärkt das Vertrauen neuer Kunden.\n\n"
                    "**Beispiel für eine Bewertung:**\n"
                    "⭐ ⭐ ⭐ ⭐ ⭐ - *Sehr schneller Support, FastFlags funktionieren perfekt "
                    "und habe direkt +120 FPS bekommen! Gerne wieder!*"
                ),
                color=0xFFD700,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await c_vouches.send(embed=embed_vouch_placeholder)

        # Stats updaten
        stats_cog = self.bot.get_cog("StatsCog")
        if stats_cog:
            await stats_cog.update_stats_channels(guild)

        # ═══════════════════════════════════════
        # FERTIG!
        # ═══════════════════════════════════════
        await status_msg.edit(embed=EmbedHelper.create_prestige_embed(
            title="🎉 Server-Setup erfolgreich abgeschlossen! 🎉",
            description=(
                f"> 👑 **Rollen:** {roles_created} erstellt, {roles_skipped} übersprungen\n"
                f"> 📁 **Kanäle:** {channels_created} erstellt\n"
                f"> 🔒 **Rechte:** Hochsicheres Rechtesystem aktiv\n"
                f"> 📝 **Embeds:** Alle Infos, Regeln, Tickets & Verifikation gesendet\n"
                f"> 🎟️ **Tickets:** Interaktive Multi-Tickets einsatzbereit!\n\n"
                f"Dein Server ist jetzt komplett fertig! 🚀"
            ),
            color=0x39FF14,
            author_user=interaction.user,
            bot_user=self.bot.user,
        ))
