"""
Components V2 Helper — 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣
==================================================================
Zentrale Factory für das neue Discord "Components V2" Layout
(Container = type 17, TextDisplay = type 10, ActionRow = type 1,
Separator = type 14), wie im vom Owner gewünschten JSON-Format.

Benötigt discord.py >= 2.6 (LayoutView / ui.Container / ui.TextDisplay).
Beim Senden einer LayoutView setzt discord.py automatisch das
Flag IS_COMPONENTS_V2 (32768) — man sendet die View OHNE `embed=`.

Verwendung:
    from bot.cogs.components_v2 import PrestigeContainer, build_layout

    view = build_layout(
        title="⚠️ 𝗩𝗢𝗜𝗗 • SERVER SETUP",
        body="Hallo ...",
        accent=0x2b2d31,
        buttons=[my_button1, my_button2],   # optional
    )
    await ctx.send(view=view)
"""

import discord

# Prestige-Akzentfarbe (linker Farbstreifen des Containers)
PRESTIGE_ACCENT = 0x2b2d31
FOOTER_TEXT = "Powered by BotForge"


def prestige_text(title: str, body: str = "", author: discord.abc.User = None) -> str:
    """Baut den Markdown-Text-Block für ein TextDisplay (type 10).

    Components V2 kennt KEIN klassisches Embed-Author/Footer mehr,
    deshalb wird alles in einen Markdown-Text gegossen.
    """
    lines = []
    if title:
        lines.append(f"## {title}")
    if author is not None:
        # Author dezent als zweite Zeile (Mention statt Avatar-Icon)
        lines.append(f"-# {author.mention}")
    if body:
        if lines:
            lines.append("")  # Leerzeile zwischen Kopf und Body
        lines.append(body)
    return "\n".join(lines)


class PrestigeContainer(discord.ui.Container):
    """Ein V2-Container (type 17) mit Akzentfarbe, Textblock,
    optionalem Trenner, optionalen Buttons/Selects und Footer."""

    def __init__(
        self,
        title: str,
        body: str = "",
        *,
        accent: int = PRESTIGE_ACCENT,
        author: discord.abc.User = None,
        items: list = None,
        footer: bool = True,
    ):
        super().__init__(accent_colour=discord.Colour(accent))

        # 1) Hauptinhalt als TextDisplay (type 10)
        self.add_item(discord.ui.TextDisplay(prestige_text(title, body, author)))

        # 2) Interaktive Elemente (Buttons/Selects) — je in eigener ActionRow
        if items:
            self.add_item(discord.ui.Separator())
            for it in items:
                if isinstance(it, discord.ui.ActionRow):
                    self.add_item(it)
                elif isinstance(it, (discord.ui.Button, discord.ui.Select)):
                    row = discord.ui.ActionRow()
                    row.add_item(it)
                    self.add_item(row)
                else:
                    # bereits ein Container-fähiges Item (z. B. TextDisplay)
                    self.add_item(it)

        # 3) Footer als kleiner grauer Text (-# = subtext)
        if footer:
            self.add_item(discord.ui.Separator())
            self.add_item(discord.ui.TextDisplay(f"-# {FOOTER_TEXT}"))


class PrestigeLayoutView(discord.ui.LayoutView):
    """LayoutView-Wrapper. Persistente Views: timeout=None setzen."""

    def __init__(self, container: discord.ui.Container, *, timeout=None):
        super().__init__(timeout=timeout)
        self.add_item(container)


def build_layout(
    title: str,
    body: str = "",
    *,
    accent: int = PRESTIGE_ACCENT,
    author: discord.abc.User = None,
    items: list = None,
    footer: bool = True,
    timeout=None,
) -> PrestigeLayoutView:
    """Bequeme Kurzform: gibt eine fertige LayoutView zurück."""
    container = PrestigeContainer(
        title, body, accent=accent, author=author, items=items, footer=footer
    )
    return PrestigeLayoutView(container, timeout=timeout)
