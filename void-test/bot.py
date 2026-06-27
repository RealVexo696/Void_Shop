"""
𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 — Einstiegsdatei für Railway.
Startet den Flask Webserver (keep_alive) und den Discord Bot.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.routes.api import keep_alive
from bot import bot as _bot_instance

if __name__ == "__main__":
    # Flask Webserver für 24/7 online halten und Web-Dashboard starten
    keep_alive()

    _bot_instance.run(
        os.environ.get("DISCORD_TOKEN")
        or os.environ.get("TOKEN")
        or os.environ.get("BOT_TOKEN")
        or ""
    )
