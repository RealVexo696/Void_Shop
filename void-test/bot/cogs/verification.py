"""
Verification Cog - Roblox Bio-Verify, SimpleVerify
Alle Embeds im App-Karten UI Design (0x2b2d31) mit kompaktem Abstand und Button-Footer.
"""

import aiohttp
import logging

import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db
from bot.cogs.components_v2 import PrestigeContainer

logger = logging.getLogger("void_shop_bot.verification")

VERIFY_PANEL_TITLE = "🔐 𝗩𝗢𝗜𝗗 • SERVEREINTRETEN VERIFIZIERUNG"
VERIFY_PANEL_BODY = (
    "Willkommen bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**. Bevor du den Server vollständig nutzen kannst, musst du dich kurz verifizieren.\n\n"
    "### ✅ Was passiert nach der Verifizierung?\n"
    "• Du erhältst Zugriff auf Chats, Shop, Tickets und Giveaways.\n"
    "• Der Bot vergibt dir automatisch die **Member**-Rolle.\n"
    "• Falls vorhanden, erhältst du zusätzlich die **Verified**-Rolle.\n\n"
    "### 🔐 So geht's\n"
    "1. Klicke unten auf **Verifizieren**.\n"
    "2. Warte kurz auf die Bestätigung.\n"
    "3. Danach ist dein Account freigeschaltet.\n\n"
    "-# Keine Passwörter, keine privaten Daten — nur ein sicherer 1-Klick-Check."
)


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


# --- ROBLOX VERIFIZIERUNGS BUTTONS ---

class RobloxBioVerifyView(discord.ui.View):
    def __init__(self, roblox_id, roblox_name, roblox_display, sec_code):
        super().__init__(timeout=180)
        self.roblox_id = roblox_id
        self.roblox_name = roblox_name
        self.roblox_display = roblox_display
        self.sec_code = sec_code
        self.add_item(discord.ui.Button(label="Powered by BotForge", style=discord.ButtonStyle.secondary, disabled=True, row=4, custom_id="footer_rbv"))

    @discord.ui.button(label="Bio überprüft ✅", style=discord.ButtonStyle.success, custom_id="bio_verify_yes", row=0)
    async def confirm_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        url = f"https://users.roblox.com/v1/users/{self.roblox_id}"
        desc = ""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as r:
                    if r.status == 200:
                        data = await r.json()
                        desc = data.get("description", "")
            except Exception:
                pass

        if self.sec_code.lower() in desc.lower() or "void" in desc.lower():
            guild = interaction.guild
            member = interaction.user

            verified_role = discord.utils.get(guild.roles, name="👤│ 𝗩𝗢𝗜𝗗 • Verified")
            member_role = discord.utils.get(guild.roles, name="👥│ 𝗩𝗢𝗜𝗗 • Member")

            try:
                roles_to_add = []
                if verified_role:
                    roles_to_add.append(verified_role)
                if member_role:
                    roles_to_add.append(member_role)
                if roles_to_add:
                    await member.add_roles(*roles_to_add)
                await member.edit(nick=self.roblox_name)
            except Exception:
                pass

            db.add_coins(member.id, 10)

            success_embed = EmbedHelper.create_prestige_embed(
                title="⚡ Bio-Auth Verifizierung erfolgreich!",
                description=(
                    f"> 🎉 Herzlichen Glückwunsch, {member.mention}!\n"
                    "~~                                                              ~~\n"
                    f"> Du hast dich 100% fälschungssicher als **{self.roblox_name}** verifiziert.\n"
                    f"> **Roblox-ID:** `{self.roblox_id}`\n"
                    f"> **Willkommensbonus:** `+10 Void-Coins` 🪙\n"
                    "~~                                                              ~~\n"
                    "> Sämtliche Serverlounges wurden für dich freigeschaltet!\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=member,
                bot_user=interaction.client.user,
            )

            avatar_url = await get_roblox_avatar(self.roblox_id)
            if avatar_url:
                success_embed.set_thumbnail(url=avatar_url)

            await interaction.followup.send(embed=success_embed, ephemeral=True)
            self.stop()

            stats_cog = interaction.client.get_cog("StatsCog")
            if stats_cog:
                await stats_cog.update_stats_channels(guild)

            log_channel = discord.utils.get(guild.text_channels, name="⚙️│system-logs")
            if log_channel:
                log_embed = EmbedHelper.create_prestige_embed(
                    title="👤 Mitglied verifiziert (Bio-Code-Auth)",
                    description=(
                        f"> **User:** {member.mention} ({member.name})\n"
                        f"> **Roblox:** [{self.roblox_name}](https://www.roblox.com/users/{self.roblox_id}/profile)\n"
                        "~~                                                              ~~\n"
                        f"> **Sicherheitscode:** `{self.sec_code}` *(Verifiziert)*\n"
                        "~~                                                              ~~"
                    ),
                    color=0x2b2d31,
                    author_user=member,
                    bot_user=interaction.client.user,
                )
                await log_channel.send(embed=log_embed)
        else:
            await interaction.followup.send(
                f"❌ Sicherheitscode `{self.sec_code}` nicht in deiner Bio gefunden!\n"
                f"-> Bitte trage `{self.sec_code}` in deine Roblox Profilbeschreibung ein und klicke erneut auf den Button.",
                ephemeral=True,
            )

    @discord.ui.button(label="Abbrechen ❌", style=discord.ButtonStyle.danger, custom_id="bio_verify_no", row=0)
    async def confirm_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = EmbedHelper.create_prestige_embed(
            title="❌ Verifizierung abgebrochen",
            description=(
                "> Der Vorgang wurde abgebrochen.\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=interaction.client.user,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()


# --- PERSISTENTER VERIFIZIERUNGS BUTTON (EINTRETEN VERIFIZIERUNG) ---

class SimpleVerifyButton(discord.ui.LayoutView):
    """Components-V2 Verify-Panel: Container (type 17) mit Text + Verify-Button.
    Persistent (timeout=None) mit festem custom_id, damit der Button nach
    Bot-Neustart weiter funktioniert."""

    def __init__(self):
        super().__init__(timeout=None)
        self.verify_btn = discord.ui.Button(
            label="Verifizieren 🔐",
            style=discord.ButtonStyle.success,
            emoji="🔐",
            custom_id="simple_verify_btn",
        )
        self.verify_btn.callback = self.verify
        container = PrestigeContainer(
            title=VERIFY_PANEL_TITLE,
            body=VERIFY_PANEL_BODY,
            items=[self.verify_btn],
        )
        self.add_item(container)

    async def verify(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        if not guild:
            return await interaction.response.send_message("❌ Nur auf einem Server nutzbar.", ephemeral=True)

        member_role = discord.utils.get(guild.roles, name="👥│ 𝗩𝗢𝗜𝗗 • Member")
        verified_role = discord.utils.get(guild.roles, name="👤│ 𝗩𝗢𝗜𝗗 • Verified")
        roles_to_add = [r for r in (member_role, verified_role) if r and r not in member.roles]

        if not member_role and not verified_role:
            return await interaction.response.send_message(
                "❌ Es wurde keine passende Verify-/Member-Rolle gefunden. Bitte Admin kontaktieren.",
                ephemeral=True,
            )

        if not roles_to_add:
            already = PrestigeContainer(
                "✅ Bereits verifiziert",
                f"{member.mention}, du bist bereits freigeschaltet.\n\n"
                "Du kannst Shop, Support, Tickets und Community-Kanäle nutzen.",
                accent=0x00D26A,
                author=member,
            )
            v = discord.ui.LayoutView(timeout=None); v.add_item(already)
            return await interaction.response.send_message(view=v, ephemeral=True)

        try:
            await member.add_roles(*roles_to_add, reason="VOID 1-Klick-Verifizierung")
            role_list = ", ".join(r.mention for r in roles_to_add)
            cont = PrestigeContainer(
                "🔐 𝗩𝗢𝗜𝗗 • Verifizierung erfolgreich",
                f"Willkommen, {member.mention}!\n\n"
                f"**Vergebene Rollen:** {role_list}\n"
                "**Status:** ✅ Freigeschaltet\n\n"
                "Du hast jetzt Zugriff auf die Community, den Shop, Support und Tickets.\n"
                "-# Tipp: Wenn du später einkaufst, kannst du im Ticket dein Produkt direkt per Button wählen.",
                accent=0x00D26A,
                author=member,
            )
            v = discord.ui.LayoutView(timeout=None); v.add_item(cont)
            await interaction.response.send_message(view=v, ephemeral=True)

            log_channel = discord.utils.get(guild.text_channels, name="⚙️│system-logs")
            if log_channel:
                log_cont = PrestigeContainer(
                    "🔐 Verify abgeschlossen",
                    f"**User:** {member.mention} (`{member.id}`)\n"
                    f"**Rollen:** {', '.join(r.name for r in roles_to_add)}\n"
                    "**Methode:** 1-Klick Verify Button",
                    accent=0x5865F2,
                    author=member,
                )
                lv = discord.ui.LayoutView(timeout=None); lv.add_item(log_cont)
                await log_channel.send(view=lv)

            stats_cog = interaction.client.get_cog("StatsCog")
            if stats_cog:
                await stats_cog.update_stats_channels(guild)

        except discord.Forbidden:
            err = PrestigeContainer(
                "❌ Verify fehlgeschlagen",
                "Mir fehlen Rechte, um dir die Rolle zu geben.\n"
                "Bitte stelle sicher, dass meine Bot-Rolle über der Member-/Verified-Rolle steht.",
                accent=0xED4245,
                author=member,
            )
            v = discord.ui.LayoutView(timeout=None); v.add_item(err)
            await interaction.response.send_message(view=v, ephemeral=True)
        except Exception as e:
            logger.error(f"Simple Verify Fehler: {e}")
            await interaction.response.send_message("❌ Unerwarteter Verify-Fehler. Bitte Admin kontaktieren.", ephemeral=True)



class VerificationCog(commands.Cog, name="VerificationCog"):
    def __init__(self, bot):
        self.bot = bot
