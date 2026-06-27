"""
Commands Cog - /help und /status Slash Commands
"""

import discord
from discord.ext import commands
from discord import app_commands

from bot.cogs.embed_helper import EmbedHelper


class CommandsCog(commands.Cog, name="CommandsCog"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="status", description="⚡ Zeigt Bot-Status und Server-Statistiken")
    @app_commands.guild_only()
    async def status_command(self, interaction: discord.Interaction):
        """Zeigt den aktuellen Bot-Status und Server-Statistiken an."""
        await interaction.response.defer()
        guild = interaction.guild
        member_count = len(guild.members)
        booster_count = guild.premium_subscription_count

        customer_role = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • Customer")
        customer_count = len(customer_role.members) if customer_role else 0

        ping = round(self.bot.latency * 1000) if self.bot.latency else 0

        embed = EmbedHelper.create_prestige_embed(
            title="⚡ 𝗩𝗢𝗜𝗗 • Server Status",
            description=(
                "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                f"> 👥 **Mitglieder:** `{member_count}`\n"
                f"> 💎 **Booster:** `{booster_count}`\n"
                f"> 🛒 **Kunden:** `{customer_count}`\n"
                f"> ⚡ **Ping:** `{ping}ms`\n"
                f"> 🟢 **Status:** `Online`"
            ),
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="help", description="📖 Zeigt alle verfügbaren Befehle des VOID Bots")
    async def help_command(self, interaction: discord.Interaction):
        """Zeigt alle verfügbaren Befehle an."""
        await interaction.response.defer(ephemeral=True)

        embed = EmbedHelper.create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n⚡ 𝗩𝗢𝗜𝗗 • BEFEHLSÜBERSICHT ⚡\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description=(
                "**🛠️ ADMIN-BEFEHLE:**\n"
                f"> **`!role`** — Alle 23 Premium-Rollen erstellen & Kanalrechte anpassen\n"
                f"> **`!uz`** — Bestehende Kanäle mit den passenden 23 Rollen-Rechten synchronisieren\n"
                f"> **`!Start`** — Komplettes Server-Layout erstellen (Kategorien, Kanäle, Embeds)\n"
                f"> ▸ Modus: `reset` (löscht alles & neu) oder `add` (nur ergänzen)\n"
                f"> ▸ Benötigt: Administrator-Berechtigung\n\n"

                "**🔐 VERIFIZIERUNG:**\n"
                f"> **`/verify`** — Roblox-Account per Bio-Code verifizieren\n"
                f"> ▸ Parameter: `roblox_username`\n"
                f"> ▸ Weist Rollen zu & gibt +10 Void-Coins\n\n"

                "**🛒 SHOP & KÄUFE:**\n"
                f"> **`/checkbuy`** — Gamepass-Kauf über Roblox API prüfen\n"
                f"> ▸ Parameter: `roblox_username`, `gamepass_id`\n"
                f"> ▸ Schaltet Customer-Rollen automatisch frei\n\n"

                "**📩 INVITES:**\n"
                f"> **`/invites`** — Invite-Statistik anzeigen\n"
                f"> ▸ Optional: `user` (sonst eigene Statistik)\n\n"

                "**📊 STATUS:**\n"
                f"> **`/status`** — Server-Statistiken & Bot-Info anzeigen\n\n"

                "**🎟️ TICKET-SYSTEM:**\n"
                f"> Klicke im Kanal `#🎟️│create-ticket` auf die Buttons:\n"
                f"> ▸ 🛒 **Produkt kaufen** — Kauf-Ticket erstellen\n"
                f"> ▸ ⚙️ **Allgemeiner Support** — Support-Ticket erstellen\n"
                f"> ▸ 🤝 **Partnerschaft** — Partner-Ticket erstellen\n\n"

                "**💡 TIPP:**\n"
                f"> Tippe `/` in den Chat um alle verfügbaren Befehle zu sehen!"
            ),
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
