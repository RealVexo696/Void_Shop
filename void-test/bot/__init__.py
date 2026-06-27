"""
𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 — Prestige Discord Bot (24/7 Railway Ready)
Alle Befehle jetzt als Slash Commands (/)
"""

import os
import logging

import discord
from discord.ext import commands
import discord.app_commands

# ==============================================================================
# KONFIGURATION
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
)
logger = logging.getLogger('void_shop_bot')

TOKEN = (
    os.environ.get("DISCORD_TOKEN")
    or os.environ.get("TOKEN")
    or os.environ.get("BOT_TOKEN")
    or ""
)

# ==============================================================================
# BOT-KLASSE
# ==============================================================================
class VoidShopBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.invites = True
        super().__init__(
            command_prefix="!",  # Fallback, aber alle Commands sind jetzt Slash
            intents=intents,
            help_command=None,
        )
        self.invites_cache = {}
        self.setup_synced = False

    async def setup_hook(self):
        """Lädt alle Cogs und registriert persistente Views."""
        from bot.cogs.embed_helper import EmbedHelper
        from bot.cogs.economy import EconomyCog
        from bot.cogs.verification import VerificationCog
        from bot.cogs.tickets import TicketsCog
        from bot.cogs.setup import SetupCog
        from bot.cogs.logging_events import LoggingEventsCog
        from bot.cogs.stats import StatsCog
        from bot.cogs.commands import CommandsCog

        cogs = [
            EmbedHelper(self),
            EconomyCog(self),
            VerificationCog(self),
            TicketsCog(self),
            SetupCog(self),
            LoggingEventsCog(self),
            StatsCog(self),
            CommandsCog(self),
        ]
        for cog in cogs:
            await self.add_cog(cog)
            logger.info(f"✅ Cog geladen: {cog.__class__.__name__}")

        # Persistente UI-Views registrieren
        from bot.cogs.tickets import (
            TicketButton,
            CloseTicketView,
            CloseTicketMenu,
            PurchaseQuestion2View,
        )
        from bot.cogs.verification import SimpleVerifyButton

        self.add_view(TicketButton())
        self.add_view(CloseTicketView())
        self.add_view(SimpleVerifyButton())
        self.add_view(CloseTicketMenu())
        self.add_view(PurchaseQuestion2View())

        # Slash Commands global syncen (einmalig)
        await self.tree.sync()
        self.setup_synced = True
        logger.info("🔄 Slash Commands synchronisiert.")
        logger.info("Persistente UI-Views und Stats-Loop geladen.")

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="über 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 | !Start",
            ),
        )

        for guild in self.guilds:
            try:
                self.invites_cache[guild.id] = await guild.invites()
                stats_cog = self.get_cog("StatsCog")
                if stats_cog:
                    await stats_cog.update_stats_channels(guild)
            except Exception:
                pass

        logger.info(f"============= 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 PRESTIGE BOT ONLINE =============")
        logger.info(f"Eingeloggt als: {self.user.name} ({self.user.id})")
        logger.info(f"Slash Commands: {len(self.tree.get_commands())} registriert")

    async def on_guild_join(self, guild):
        """Sync Commands beim Beitreten eines neuen Servers."""
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


bot = VoidShopBot()


# ==============================================================================
# START
# ==============================================================================
if __name__ == "__main__":
    if not TOKEN or TOKEN == "DEIN_BOT_TOKEN_HIER":
        logger.error(
            "FEHLER: Kein gültiger Discord Bot-Token gefunden!\n"
            "-> Bitte hinterlege deinen Token in Railway unter 'Variables' (Secrets) als 'DISCORD_TOKEN'."
        )
    else:
        from web.routes.api import keep_alive
        keep_alive()

        try:
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            logger.error(
                "FEHLER: Der angegebene Bot-Token ist ungültig! "
                "Bitte überprüfe dein 'DISCORD_TOKEN' Secret in Railway."
            )
        except Exception as e:
            logger.error(f"Fehler beim Starten des Bots: {e}")
