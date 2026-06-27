"""
Embed Helper - Erstellt einheitliche Prestige Embeds.
Wird von allen Cogs genutzt.
"""

import discord


class EmbedHelper(discord.ext.commands.Cog, name="EmbedHelper"):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def create_prestige_embed(
        title: str,
        description: str,
        color: int,
        author_user: discord.User = None,
        bot_user: discord.ClientUser = None,
    ):
        """
        Erstellt ein hochgradig einheitliches, luxuriöses Embed:
        - Author: Immer der ausführende User (Name + Avatar-Icon)
        - Footer: Immer Bot-Icon + "Powered by BotForge" + Zeitstempel
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=discord.utils.utcnow(),
        )
        if author_user:
            embed.set_author(
                name=author_user.name,
                icon_url=author_user.display_avatar.url
                if author_user.display_avatar
                else None,
            )
        if bot_user:
            embed.set_footer(
                text="Powered by BotForge",
                icon_url=bot_user.display_avatar.url
                if bot_user.display_avatar
                else None,
            )
        return embed
