"""
Embed Helper - Erstellt einheitliche Prestige Embeds im App-Card Look.
Ohne herkömmlichen Embed-Footer, damit der Button-Footer perfekt andockt.
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
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
        )
        if author_user:
            embed.set_author(
                name=author_user.name,
                icon_url=author_user.display_avatar.url
                if author_user.display_avatar
                else None,
            )
        return embed
