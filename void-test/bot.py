"""
𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 — Einstiegsdatei für Railway.
Leitet sofort weiter an bot/__init__.py
"""

# Arbeitsverzeichnis sicherstellen
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import bot as _bot_instance

if __name__ == "__main__":
    _bot_instance.run(
        os.environ.get("DISCORD_TOKEN")
        or os.environ.get("TOKEN")
        or os.environ.get("BOT_TOKEN")
        or ""
    )
