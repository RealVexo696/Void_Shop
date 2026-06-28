"""
Commands Cog - /help und /status Slash Commands
Alle Embeds im ultimativen App-Karten UI Design (0x2b2d31) mit kompaktem Abstand.
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
                "> 🟢 **System:** `Online & API Synchronisiert`\n"
                "~~                                                              ~~\n"
                f"> 👥 **Mitglieder:** `{member_count}`\n"
                f"> 💎 **Booster:** `{booster_count}`\n"
                f"> 🛒 **Kunden:** `{customer_count}`\n"
                f"> ⚡ **Gateway Ping:** `{ping}ms`\n"
                "~~                                                              ~~\n"
                "> ☁️ *Host: 24/7 Railway Cloud Engine*"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="help", description="📖 Zeigt alle verfügbaren Befehle des VOID Bots")
    async def help_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed = EmbedHelper.create_prestige_embed(
            title="⚡ 𝗩𝗢𝗜𝗗 • BEFEHLSÜBERSICHT ⚡",
            description=(
                "> Hier findest du alle verfügbaren System- und Kundenbefehle für **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**.\n"
                "~~                                                              ~~\n"
                "> **🛠️ ADMIN-BEFEHLE:**\n"
                "> **`!role`** — Alle 23 Premium-Rollen erstellen & Kanalrechte anpassen\n"
                "> **`!uz`** — Bestehende Kanäle mit den passenden 23 Rollen-Rechten synchronisieren\n"
                "> **`!Start`** — Komplettes Server-Layout erstellen (Kategorien, Kanäle, Embeds)\n"
                "> ▸ Modus: `reset` (löscht alles & neu) oder `add` (nur ergänzen)\n"
                "> ▸ Benötigt: Administrator-Berechtigung\n"
                "~~                                                              ~~\n"
                "> **🔐 VERIFIZIERUNG:**\n"
                "> **`/verify`** — Roblox-Account per Bio-Code verifizieren\n"
                "> ▸ Parameter: `roblox_username`\n"
                "> ▸ Weist Rollen zu & gibt +10 Void-Coins\n"
                "~~                                                              ~~\n"
                "> **🛒 SHOP & KÄUFE:**\n"
                "> **`/checkbuy`** — Gamepass-Kauf über Roblox API prüfen\n"
                "> ▸ Parameter: `roblox_username`, `gamepass_id`\n"
                "> ▸ Schaltet Customer-Rollen automatisch frei\n"
                "> **`/preview`** — Zieht ein Roblox T-Shirt / Asset mit Wasserzeichen\n"
                "~~                                                              ~~\n"
                "> **🪙 ECONOMY & STATUS:**\n"
                "> **`/invites`** — Invite-Statistik anzeigen\n"
                "> **`/status`** — Server-Statistiken & Bot-Info anzeigen\n"
                "> **`/ffbuilder`** — Interaktiver FastFlag Konfigurator\n"
                "> **`/mysterybox`** — Öffne eine Gacha Mystery Box (100 Coins)\n"
                "> **`/analytics`** — Generiert ein Live Wall-Street Diagramm\n"
                "> **`/vippass`** — Erstellt deine Apple Wallet VIP Pass Grafik\n"
                "> **`/tryon`** — 3D Roblox Fitting Room Vorschau\n"
                "~~                                                              ~~\n"
                "> **🛒 SHOP & KEYS:**\n"
                "> **`/redeem`** — Lizenz-Key einlösen → Rolle + 25 Coins\n"
                "> **`/stock`** — Lagerbestand aller Produkte anzeigen\n"
                "> **`/faq`** — Häufige Fragen & Antworten\n"
                "> **`/language`** — Sprache wählen (🇩🇪 DE / 🇬🇧 EN)\n"
                "> **`/topsupporter`** — Supporter des Monats anzeigen\n"
                "~~                                                              ~~\n"
                "> **🛠️ ADMIN-SHOP:**\n"
                "> **`/addkeys`** — Lizenz-Keys zum Vorrat hinzufügen\n"
                "> **`/sales`** — Verkaufsstatistik\n"
                "> **`/ticketstats`** — Ø-Antwortzeit & Tickets pro Supporter\n"
                "> **`/setfaq`** — FAQ-Eintrag hinzufügen/ändern\n"
                "~~                                                              ~~\n"
                "> **🎟️ TICKET-SYSTEM:**\n"
                "> Wähle im Kanal `#🎟️│create-ticket` im Menü:\n"
                "> ▸ 🛒 **Produkt kaufen** — danach Produkt per Klick wählen (Warenkorb!)\n"
                "> ▸ ⚙️ **Fragen / Support** — Support-Ticket\n"
                "> ▸ 🤝 **Partnerschaft** — Partner-Ticket\n"
                "~~                                                              ~~\n"
                "> 🌐 **Admin-Dashboard:** `/admin` auf der Web-URL (Passwort-Login)\n"
                "~~                                                              ~~\n"
                "> 💡 *Tipp: Tippe `/` in den Chat, um alle Befehle schnell auszuführen!*"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=self.bot.user,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)
