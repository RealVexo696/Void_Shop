"""
Stats Cog - Echtzeit Stats-Kanäle, Status-Rotation
"""

import discord
from discord.ext import commands, tasks

import logging
from bot.cogs.database import db

logger = logging.getLogger("void_shop_bot.stats")


class StatsCog(commands.Cog, name="StatsCog"):
    def __init__(self, bot):
        self.bot = bot
        self.update_stats_task.start()
        self.status_rotation_task.start()

    async def cog_unload(self):
        self.update_stats_task.cancel()
        self.status_rotation_task.cancel()

    async def update_stats_channels(self, guild):
        """Aktualisiert sofort und in Echtzeit die Namen der Server-Statistik Kanäle."""
        member_count = len(guild.members)
        booster_count = guild.premium_subscription_count

        customer_role = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • Customer")
        customer_count = len(customer_role.members) if customer_role else 0

        open_tix_count = 0
        for c in guild.text_channels:
            n = c.name.lower()
            topic = (c.topic or "").lower()
            if any(x in n for x in ["kauf-", "support-", "partner-"]) or "creator:" in topic:
                open_tix_count += 1

        for vc in guild.voice_channels:
            try:
                if vc.name.startswith("👥│Mitglieder:"):
                    await vc.edit(name=f"👥│Mitglieder: {member_count}")
                elif vc.name.startswith("💎│Booster:"):
                    await vc.edit(name=f"💎│Booster: {booster_count}")
                elif vc.name.startswith("🛒│Kunden:"):
                    await vc.edit(name=f"🛒│Kunden: {customer_count}")
                elif vc.name.startswith("🎟️│Offene Tickets:"):
                    await vc.edit(name=f"🎟️│Offene Tickets: {open_tix_count}")
            except discord.Forbidden:
                logger.warning(f"Keine Berechtigung zum Bearbeiten des Stats-Kanals {vc.name}.")
            except Exception as e:
                logger.error(f"Fehler bei Stats-Kanal Edit: {e}")

    @tasks.loop(minutes=10)
    async def update_stats_task(self):
        """Backup-Loop: Aktualisiert alle 10 Minuten die Namen der Server-Statistik Kanäle."""
        logger.info("Führe Backup-Aktualisierung der Server-Statistiken durch...")
        for guild in self.bot.guilds:
            await self.update_stats_channels(guild)

    @tasks.loop(seconds=5)
    async def status_rotation_task(self):
        """Wechselt alle 5 Sekunden durch 5 repräsentative Prestige-Statusmeldungen."""
        if not self.bot.is_ready():
            return
        statuses = [
            ("⭐ 5 von 5 Sterne Bewertungen!", discord.ActivityType.watching),
            ("🚀 +120 FPS mit VOID FastFlags", discord.ActivityType.playing),
            ("🛍️ 24/7 Auto-Delivery Cloud Shop", discord.ActivityType.competing),
            ("🎟️ Live Support & Ticket Center", discord.ActivityType.listening),
            ("👑 Powered by VOID • Prestige", discord.ActivityType.watching),
        ]
        idx = getattr(self.bot, "status_idx", 0)
        text, act_type = statuses[idx % len(statuses)]
        self.bot.status_idx = idx + 1

        try:
            activity = discord.Activity(type=act_type, name=text)
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
        except Exception:
            pass
