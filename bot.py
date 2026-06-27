#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Void Shop – Role & Permission Setup Bot

Dieser Bot macht absichtlich nur noch 2 Dinge:
1. Rollen erstellen / aktualisieren
2. Rechte / Kanal-Sichtbarkeit für diese Rollen setzen

Commands:
- !start  -> erstellt Rollen und setzt Rechte
- !help   -> zeigt Hilfe

Config via .env:
DISCORD_TOKEN=...
PREFIX=!
OWNER_ID=123456789
"""

import os
import asyncio
from typing import Iterable

import discord
from discord.ext import commands

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

TOKEN = os.getenv("DISCORD_TOKEN", "")
PREFIX = os.getenv("PREFIX", "!")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)

# ------------------------------------------------------------------
# Intents
# ------------------------------------------------------------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None, case_insensitive=True)

# ------------------------------------------------------------------
# Permission helpers
# ------------------------------------------------------------------
def perms(**kwargs) -> discord.Permissions:
    p = discord.Permissions.none()
    for key, value in kwargs.items():
        setattr(p, key, value)
    return p

ROLE_DEFS = [
    # name, color, permissions, hoist, mentionable
    ("👑 Owner", (255, 0, 0), perms(administrator=True), True, True),
    ("⚡ Admin", (255, 70, 70), perms(
        view_audit_log=True, manage_guild=True, manage_roles=True, manage_channels=True,
        manage_messages=True, kick_members=True, ban_members=True, moderate_members=True,
        manage_nicknames=True, manage_threads=True, mention_everyone=True, move_members=True,
        mute_members=True, deafen_members=True, connect=True, speak=True, view_channel=True,
        send_messages=True, read_message_history=True, embed_links=True, attach_files=True,
        add_reactions=True, use_external_emojis=True
    ), True, True),
    ("🔧 Head-Staff", (255, 120, 0), perms(
        view_audit_log=True, manage_channels=True, manage_messages=True, kick_members=True,
        moderate_members=True, manage_nicknames=True, manage_threads=True, move_members=True,
        mute_members=True, deafen_members=True, connect=True, speak=True, view_channel=True,
        send_messages=True, read_message_history=True, embed_links=True, attach_files=True,
        add_reactions=True, use_external_emojis=True
    ), True, False),
    ("🛡️ Moderator", (0, 170, 255), perms(
        manage_messages=True, kick_members=True, moderate_members=True, manage_nicknames=True,
        move_members=True, mute_members=True, deafen_members=True, connect=True, speak=True,
        view_channel=True, send_messages=True, read_message_history=True, embed_links=True,
        attach_files=True, add_reactions=True, use_external_emojis=True
    ), True, False),
    ("🎫 Supporter", (0, 220, 120), perms(
        manage_messages=True, read_message_history=True, view_channel=True, send_messages=True,
        embed_links=True, attach_files=True, add_reactions=True, connect=True, speak=True,
        move_members=True, use_external_emojis=True
    ), True, False),
    ("🧰 Trial-Supporter", (120, 220, 120), perms(
        read_message_history=True, view_channel=True, send_messages=True, embed_links=True,
        attach_files=True, add_reactions=True, connect=True, speak=True
    ), False, False),

    ("💎 VIP Kunde", (255, 215, 0), perms(view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True), False, False),
    ("🛒 Kunde", (0, 255, 136), perms(view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True), False, False),
    ("⭐ Premium", (255, 105, 180), perms(view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True), False, False),
    ("🎁 Booster", (255, 115, 250), perms(view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True), False, False),

    ("✅ Verifiziert", (46, 204, 113), perms(view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True), False, False),
    ("👤 Member", (88, 180, 255), perms(
        view_channel=True, send_messages=True, read_message_history=True, connect=True, speak=True,
        embed_links=True, attach_files=True, add_reactions=True, use_external_emojis=True,
        stream=True, create_public_threads=True, send_messages_in_threads=True
    ), False, False),
    ("❌ Unverifiziert", (120, 120, 120), perms(read_message_history=True), False, False),

    ("⚡ FastFlags", (255, 200, 0), discord.Permissions.none(), False, False),
    ("☁️ Sky", (135, 206, 250), discord.Permissions.none(), False, False),
    ("👕 T-Shirt", (255, 150, 200), discord.Permissions.none(), False, False),
    ("🛡️ Anti Alt Ban", (180, 0, 255), discord.Permissions.none(), False, False),

    ("🔥 Aktiv", (255, 69, 0), discord.Permissions.none(), False, False),
    ("💬 Chatter", (0, 200, 255), discord.Permissions.none(), False, False),
    ("🌟 Stammkunde", (255, 215, 0), discord.Permissions.none(), False, False),
    ("🏆 Top Käufer", (255, 215, 0), discord.Permissions.none(), False, False),
    ("🎖️ Veteran", (192, 192, 192), discord.Permissions.none(), False, False),

    ("🤝 Partner", (100, 255, 180), discord.Permissions.none(), False, False),
    ("🎨 Designer", (255, 105, 180), discord.Permissions.none(), False, False),
    ("🧪 Beta Tester", (0, 255, 200), discord.Permissions.none(), False, False),
    ("📢 Event Ping", (255, 220, 0), discord.Permissions.none(), False, False),
    ("🎉 Giveaway Ping", (255, 180, 0), discord.Permissions.none(), False, False),
    ("🛍️ Shop Ping", (0, 255, 150), discord.Permissions.none(), False, False),
    ("📣 News Ping", (0, 150, 255), discord.Permissions.none(), False, False),

    ("❤️ Rot", (231, 76, 60), discord.Permissions.none(), False, False),
    ("💙 Blau", (52, 152, 219), discord.Permissions.none(), False, False),
    ("💚 Grün", (46, 204, 113), discord.Permissions.none(), False, False),
    ("💛 Gelb", (241, 196, 15), discord.Permissions.none(), False, False),
    ("💜 Lila", (155, 89, 182), discord.Permissions.none(), False, False),
    ("🩷 Pink", (253, 121, 168), discord.Permissions.none(), False, False),
    ("🧡 Orange", (230, 126, 34), discord.Permissions.none(), False, False),
    ("🤍 Weiß", (236, 240, 241), discord.Permissions.none(), False, False),
    ("🖤 Schwarz", (44, 62, 80), discord.Permissions.none(), False, False),

    ("🤖 Bot", (88, 101, 242), perms(
        view_channel=True, send_messages=True, read_message_history=True,
        manage_messages=True, manage_channels=True, manage_roles=True,
        embed_links=True, attach_files=True, add_reactions=True,
        connect=True, speak=True, move_members=True
    ), True, False),
]

PUBLIC_CHANNEL_KEYWORDS = {
    "verify", "regeln", "rules", "willkommen", "welcome", "auf-wiedersehen",
    "goodbye", "faq", "links", "how-to-buy", "announcements", "ankündigungen"
}

STAFF_CHANNEL_KEYWORDS = {
    "log", "logs", "staff", "owner", "admin", "mod", "claim", "payout",
    "crm", "ticket-log", "bot-log"
}

STATS_CHANNEL_KEYWORDS = {"mitglieder", "booster", "kunden", "offene tickets", "stats"}

STAFF_ROLE_NAMES = {"👑 Owner", "⚡ Admin", "🔧 Head-Staff", "🛡️ Moderator", "🎫 Supporter", "🧰 Trial-Supporter"}
MEMBER_ROLE_NAMES = {"👤 Member", "✅ Verifiziert", "🛒 Kunde", "💎 VIP Kunde", "⭐ Premium", "🎁 Booster"}

SETUP_LOCKS: set[int] = set()

# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------
def role_map(guild: discord.Guild) -> dict[str, discord.Role]:
    return {role.name: role for role in guild.roles}


def is_staff_channel(name: str) -> bool:
    low = (name or "").lower()
    return any(key in low for key in STAFF_CHANNEL_KEYWORDS)


def is_public_channel(name: str) -> bool:
    low = (name or "").lower()
    return any(key in low for key in PUBLIC_CHANNEL_KEYWORDS)


def is_stats_channel(name: str) -> bool:
    low = (name or "").lower()
    return any(key in low for key in STATS_CHANNEL_KEYWORDS)


def is_textish(channel: discord.abc.GuildChannel) -> bool:
    return isinstance(channel, (discord.TextChannel, discord.ForumChannel, discord.VoiceChannel, discord.StageChannel, discord.CategoryChannel))


async def safe_edit_status(message: discord.Message, content: str):
    try:
        await message.edit(content=content)
    except Exception:
        pass


async def create_or_update_roles(guild: discord.Guild, status_message: discord.Message):
    created = 0
    updated = 0
    failures: list[str] = []
    existing = role_map(guild)
    total = len(ROLE_DEFS)

    for idx, (name, rgb, permissions, hoist, mentionable) in enumerate(reversed(ROLE_DEFS), start=1):
        if idx == 1 or idx % 10 == 0 or idx == total:
            await safe_edit_status(status_message, f"🚀 Rollen werden erstellt / aktualisiert … {idx}/{total} · {name}")

        role = existing.get(name)
        if role is None:
            try:
                role = await guild.create_role(
                    name=name,
                    colour=discord.Colour.from_rgb(*rgb),
                    permissions=permissions,
                    hoist=hoist,
                    mentionable=mentionable,
                    reason="Role Setup Bot"
                )
                existing[name] = role
                created += 1
            except Exception as e:
                failures.append(f"{name}: {e}")
                continue
        else:
            try:
                if role.permissions != permissions or role.colour != discord.Colour.from_rgb(*rgb) or role.hoist != hoist or role.mentionable != mentionable:
                    await role.edit(
                        colour=discord.Colour.from_rgb(*rgb),
                        permissions=permissions,
                        hoist=hoist,
                        mentionable=mentionable,
                        reason="Role Setup Bot"
                    )
                    updated += 1
            except Exception as e:
                failures.append(f"{name}: {e}")

    return created, updated, failures


async def apply_channel_permissions(guild: discord.Guild, status_message: discord.Message):
    roles = role_map(guild)
    everyone = guild.default_role
    unverified = roles.get("❌ Unverifiziert")
    member_roles = [roles[name] for name in MEMBER_ROLE_NAMES if name in roles]
    staff_roles = [roles[name] for name in STAFF_ROLE_NAMES if name in roles]

    processed = 0
    failures: list[str] = []
    channels = list(guild.channels)
    total = len(channels)

    for channel in channels:
        processed += 1
        if processed == 1 or processed % 15 == 0 or processed == total:
            await safe_edit_status(status_message, f"🔐 Rechte werden gesetzt … {processed}/{total} · {channel.name}")

        try:
            overwrites: dict[discord.abc.Snowflake, discord.PermissionOverwrite] = {}

            if is_public_channel(channel.name):
                overwrites[everyone] = discord.PermissionOverwrite(view_channel=True)
                if unverified:
                    overwrites[unverified] = discord.PermissionOverwrite(view_channel=True)
                for role in member_roles:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
                for role in staff_roles:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)

                if "verify" in channel.name.lower():
                    for role in member_roles:
                        overwrites[role] = discord.PermissionOverwrite(view_channel=False)
                    if unverified:
                        overwrites[unverified] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

            elif is_staff_channel(channel.name) or (channel.category and is_staff_channel(channel.category.name)):
                overwrites[everyone] = discord.PermissionOverwrite(view_channel=False)
                if unverified:
                    overwrites[unverified] = discord.PermissionOverwrite(view_channel=False)
                for role in member_roles:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=False)
                for role in staff_roles:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)

            elif is_stats_channel(channel.name):
                overwrites[everyone] = discord.PermissionOverwrite(view_channel=True)
                if unverified:
                    overwrites[unverified] = discord.PermissionOverwrite(view_channel=True)
                for role in member_roles:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                for role in staff_roles:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                if isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
                    overwrites[everyone].connect = False
                    if unverified:
                        overwrites[unverified].connect = False
                    for role in member_roles:
                        overwrites[role].connect = False
                    for role in staff_roles:
                        overwrites[role].connect = False

            else:
                overwrites[everyone] = discord.PermissionOverwrite(view_channel=False)
                if unverified:
                    overwrites[unverified] = discord.PermissionOverwrite(view_channel=False)
                for role in member_roles:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
                for role in staff_roles:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_messages=True)

            await channel.edit(overwrites=overwrites, reason="Role Setup Bot – channel permissions")
        except Exception as e:
            failures.append(f"{channel.name}: {e}")

    return processed, failures


async def run_role_only_setup(ctx: commands.Context):
    guild = ctx.guild
    if guild.id in SETUP_LOCKS:
        return await ctx.send("⚠️ Es läuft bereits ein Setup auf diesem Server.")

    SETUP_LOCKS.add(guild.id)
    try:
        msg = await ctx.send("🚀 Starte Role-Only Setup …")

        created, updated, role_failures = await create_or_update_roles(guild, msg)
        channel_count, perm_failures = await apply_channel_permissions(guild, msg)

        await safe_edit_status(msg, "✅ Setup abgeschlossen.")

        summary = discord.Embed(title="✅ Role-Only Setup abgeschlossen", color=0x2ecc71)
        summary.add_field(name="Rollen erstellt", value=str(created), inline=True)
        summary.add_field(name="Rollen aktualisiert", value=str(updated), inline=True)
        summary.add_field(name="Kanäle verarbeitet", value=str(channel_count), inline=True)
        summary.add_field(name="Rollen-Fehler", value=str(len(role_failures)), inline=True)
        summary.add_field(name="Rechte-Fehler", value=str(len(perm_failures)), inline=True)
        summary.add_field(name="Modus", value="Nur Rollen + Rechte", inline=True)
        await ctx.send(embed=summary)

        if role_failures or perm_failures:
            details = []
            if role_failures:
                details.append("**Rollen-Fehler:**")
                details.extend([f"• {x}" for x in role_failures[:10]])
            if perm_failures:
                if details:
                    details.append("")
                details.append("**Rechte-Fehler:**")
                details.extend([f"• {x}" for x in perm_failures[:10]])
            await ctx.send(embed=discord.Embed(title="⚠️ Setup Hinweise", description="\n".join(details)[:4000], color=0xf39c12))
    finally:
        SETUP_LOCKS.discard(guild.id)

# ------------------------------------------------------------------
# Commands
# ------------------------------------------------------------------
@bot.command(name="help")
async def help_cmd(ctx: commands.Context):
    emb = discord.Embed(title="Role Setup Bot – Hilfe", color=0x5865F2)
    emb.add_field(name="!start", value="Erstellt nur Rollen und setzt nur Rechte / Sichtbarkeit", inline=False)
    emb.add_field(name="!help", value="Zeigt diese Hilfe", inline=False)
    emb.set_footer(text="Minimaler Bot: nur Rollen + Rechte, nichts anderes")
    await ctx.send(embed=emb)


@bot.command(name="start")
@commands.has_permissions(administrator=True)
async def start_cmd(ctx: commands.Context):
    if OWNER_ID and ctx.author.id != OWNER_ID and not ctx.author.guild_permissions.administrator:
        return await ctx.send("❌ Nur der Server-Owner / Admin kann das Setup starten.")
    await run_role_only_setup(ctx)


@start_cmd.error
async def start_cmd_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Du brauchst Administrator-Rechte für `!start`.")
    else:
        await ctx.send(f"❌ Fehler bei `!start`: {error}")

# ------------------------------------------------------------------
# Events
# ------------------------------------------------------------------
@bot.event
async def on_ready():
    print(f"[READY] Eingeloggt als {bot.user} ({bot.user.id})")

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main():
    if not TOKEN:
        raise SystemExit("DISCORD_TOKEN fehlt. Bitte in .env setzen.")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
