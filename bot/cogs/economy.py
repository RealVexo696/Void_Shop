"""
Economy Cog - Void-Coins, Roblox API Helpers
Alle Befehle jetzt als /slash commands
"""

import random
import logging

import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db

logger = logging.getLogger("void_shop_bot.economy")


async def get_roblox_user(username: str):
    """Sucht einen Roblox-User und gibt ID, Display-Name und System-Name zurück."""
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
    """Sucht den Kopfschuss-Avatar eines Roblox-Users."""
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
    """Prüft live über die Roblox API, ob ein User einen bestimmten Gamepass besitzt."""
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


class EconomyCog(commands.Cog, name="EconomyCog"):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================================================
    # /verify SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="verify", description="🔐 Verifiziere dich mit deinem Roblox-Account per Bio-Code")
    @app_commands.describe(roblox_username="Dein Roblox-Username (z.B. Lukas_Roblox)")
    @app_commands.guild_only()
    async def verify_command(self, interaction: discord.Interaction, roblox_username: str):
        """
        Verifiziert ein Discord-Mitglied mit seinem Roblox-Account.
        Sucht live über die Roblox API, fragt nach Bestätigung und ändert Nickname + Rolle.
        """
        await interaction.response.defer(ephemeral=True)

        progress_embed = EmbedHelper.create_prestige_embed(
            title="🔍 Suche Roblox-Konto...",
            description=f"> Kontaktiere die Roblox Server für **'{roblox_username}'**...",
            color=0x00F0FF,
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
                    "Bitte überprüfe die Schreibweise."
                ),
                color=0xFF003C,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await status_msg.edit(embed=embed_err)
            return

        avatar_url = await get_roblox_avatar(roblox_id)
        sec_code = f"void-{random.randint(1000, 9999)}"

        confirm_embed = EmbedHelper.create_prestige_embed(
            title="🔐 Roblox Bio-Code Verifizierung",
            description=(
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                "> **100% sichere Identitätsgarantie**\n\n"
                f"Account gefunden: **{roblox_name}** (`{roblox_id}`)\n\n"
                "📌 **So verifizierst du dich:**\n"
                "1️⃣ Kopiere diesen Sicherheitscode:\n"
                f"> `{sec_code}`\n"
                "2️⃣ Füge ihn in deine **Roblox Profilbeschreibung (Bio)** ein.\n"
                "3️⃣ Klicke unten auf **'Bio überprüft ✅'**."
            ),
            color=0xFFD700,
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
        """
        Prüft live über die Roblox Inventory API, ob der User den angegebenen Gamepass besitzt.
        Wenn ja, schaltet er automatisch die Customer-Rollen frei!
        """
        await interaction.response.defer(ephemeral=True)

        progress_embed = EmbedHelper.create_prestige_embed(
            title="🔄 Überprüfe Roblox Inventar...",
            description=(
                f"> Suche Roblox-Konto **'{roblox_username}'** und überprüfe "
                f"den Besitz von Gamepass `{gamepass_id}`..."
            ),
            color=0xFFD700,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        status_msg = await interaction.followup.send(embed=progress_embed, ephemeral=True, wait=True)

        roblox_id, roblox_display, roblox_name = await get_roblox_user(roblox_username)
        if not roblox_id:
            embed_err = EmbedHelper.create_prestige_embed(
                title="❌ Roblox Konto nicht gefunden",
                description=(
                    f"> Der Username **'{roblox_username}'** wurde auf Roblox nicht gefunden."
                ),
                color=0xFF003C,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            await status_msg.edit(embed=embed_err)
            return

        has_purchased = await check_roblox_ownership(roblox_id, gamepass_id)

        if has_purchased:
            guild = interaction.guild
            member = interaction.user

            customer_role = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿")
            premium_buyer_role = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿")

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
                        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                        "> ✨ **Besitz verifiziert!**\n\n"
                        f"Du besitzt den Roblox Gamepass `{gamepass_id}`.\n"
                        "Folgende Premium-Käuferrollen wurden dir freigeschaltet:\n"
                        f"> 👑 │ " + " & ".join([f"**{r}**" for r in added_roles]) + "\n\n"
                        f"Vielen Dank für deinen Einkauf bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**! "
                        "Du hast ab jetzt Zugriff auf die exklusiven Lounges.\n\n"
                        "⭐ **Zufrieden mit deinem Einkauf?**\n"
                        f"> Wir würden uns riesig über eine gute Bewertung im Kanal {vouch_mention} freuen! 💬"
                    ),
                    color=0x39FF14,
                    author_user=member,
                    bot_user=self.bot.user,
                )
                avatar_url = await get_roblox_avatar(roblox_id)
                if avatar_url:
                    success_embed.set_thumbnail(url=avatar_url)

                await status_msg.edit(embed=success_embed)

                # --- AUTO-DELIVERY DM ---
                try:
                    dm_em = EmbedHelper.create_prestige_embed(
                        title="📦 VOID • AUTO-DELIVERY (Sofort-Lieferung)",
                        description=(
                            f"Hallo {member.name}!\n\n"
                            f"Dein Kauf von Gamepass `{gamepass_id}` wurde erfolgreich bestätigt.\n"
                            "Hier ist deine automatische Sofort-Lieferung:\n\n"
                            "🚀 **Prestige FastFlags & Optimierungspaket:**\n"
                            "> Download: `https://void-shop.cloud/downloads/fastflags-v2.zip`\n"
                            "> Anleitung: Entpacken und in den Roblox Client-Ordner einfügen. +120 FPS Garantie!\n\n"
                            "🎁 *Du hast +50 Void-Coins als Treuebonus erhalten!*"
                        ),
                        color=0x39FF14,
                        bot_user=self.bot.user,
                    )
                    await member.send(embed=dm_em)
                except Exception:
                    pass

                # --- FOMO TICKER & DATABASE ---
                db.add_coins(member.id, 50)
                db.add_purchase(member.name, f"Gamepass {gamepass_id}", 400)

                live_ch = discord.utils.get(guild.text_channels, name="🛍️│live-käufe") or discord.utils.get(
                    guild.text_channels, name="live-käufe"
                )
                if live_ch:
                    fomo_em = EmbedHelper.create_prestige_embed(
                        title="🎉 NEUER KAUF ABSOLVIERT!",
                        description=(
                            "***„🎉 {mention} hat soeben das Premium FastFlags Paket (Gamepass `{gp}`) erworben! Vielen Dank!"
                            "***\n\n"
                            "> ⚡ **Lieferzeit:** `< 3 Sekunden` *(Auto-Delivery)*\n"
                            "> 🪙 **Bonus erhalten:** `+50 Void-Coins`"
                        ).format(mention=member.mention, gp=gamepass_id),
                        color=0x00FFFF,
                    )
                    fomo_em.set_thumbnail(url=member.display_avatar.url)
                    await live_ch.send(embed=fomo_em)

                # Echtzeit Stats-Update
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
                        color=0x39FF14,
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
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"> 🔒 **Kauf wurde nicht gefunden.**\n\n"
                    f"Roblox-User **{roblox_name}** besitzt den Gamepass `{gamepass_id}` aktuell nicht.\n"
                    "> Bitte stelle sicher, dass du den Gamepass mit diesem Account gekauft hast "
                    "und dein Roblox Inventar öffentlich einsehbar ist!"
                ),
                color=0xFF003C,
                author_user=interaction.user,
                bot_user=self.bot.user,
            )
            avatar_url = await get_roblox_avatar(roblox_id)
            if avatar_url:
                embed_fail.set_thumbnail(url=avatar_url)
            await status_msg.edit(embed=embed_fail)

    # ==========================================================================
    # /invites SLASH COMMAND
    # ==========================================================================
    @app_commands.command(name="invites", description="📩 Zeigt Invite-Statistiken für dich oder einen anderen User")
    @app_commands.describe(user="User dessen Invites geprüft werden sollen (optional)")
    @app_commands.guild_only()
    async def check_invites_command(self, interaction: discord.Interaction, user: discord.Member = None):
        """Zeigt an, wie viele Einladungen ein User insgesamt besitzt."""
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
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"> 📈 **Gesamte Einladungen:** `{total_invs}`\n\n"
                "**Aktive Invite-Links:**\n"
                f"> {codes_str}\n\n"
                "*Lade weitere Freunde ein, um dir Prämien abzuholen!*"
            ),
            color=0x00F0FF,
            author_user=target,
            bot_user=self.bot.user,
        )
        inv_channel = discord.utils.get(guild.text_channels, name="📩│invites") or discord.utils.get(
            guild.text_channels, name="invites"
        )
        if inv_channel:
            embed.description += f"\n\n🎁 Hole dir deine Belohnungen im Kanal {inv_channel.mention} ab!"

        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)
