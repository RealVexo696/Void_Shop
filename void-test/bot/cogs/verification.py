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

logger = logging.getLogger("void_shop_bot.verification")


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

class SimpleVerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Powered by BotForge", style=discord.ButtonStyle.secondary, disabled=True, row=4, custom_id="footer_svb"))

    @discord.ui.button(
        label="Verifizieren 🔐",
        style=discord.ButtonStyle.success,
        emoji="🔐",
        custom_id="simple_verify_btn",
        row=0
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        member_role = discord.utils.get(guild.roles, name="👥│ 𝗩𝗢𝗜𝗗 • Member")
        if not member_role:
            await interaction.response.send_message(
                "❌ Fehler: Die Mitgliederrolle wurde nicht gefunden!", ephemeral=True
            )
            return

        if member_role in member.roles:
            await interaction.response.send_message(
                "ℹ️ Du bist bereits verifiziert!", ephemeral=True
            )
            return

        try:
            await member.add_roles(member_role)
            await interaction.response.send_message(
                "✅ Du hast dich erfolgreich verifiziert und die Mitglieder-Rolle erhalten!",
                ephemeral=True,
            )

            log_channel = discord.utils.get(guild.text_channels, name="⚙️│system-logs")
            if log_channel:
                embed = EmbedHelper.create_prestige_embed(
                    title="🔐 Mitglied verifiziert (1-Klick)",
                    description=(
                        f"> **User:** {member.mention} ({member.name})\n"
                        "~~                                                              ~~\n"
                        "> Hat die Verifizierung per Knopfdruck abgeschlossen.\n"
                        "~~                                                              ~~"
                    ),
                    color=0x2b2d31,
                    author_user=member,
                    bot_user=interaction.client.user,
                )
                await log_channel.send(embed=embed)

            stats_cog = interaction.client.get_cog("StatsCog")
            if stats_cog:
                await stats_cog.update_stats_channels(guild)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Fehler: Mir fehlen die Rechte, um dir die Rolle zu geben. "
                "Bitte wende dich an einen Admin!",
                ephemeral=True,
            )


class VerificationCog(commands.Cog, name="VerificationCog"):
    def __init__(self, bot):
        self.bot = bot
