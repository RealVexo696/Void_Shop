"""
Logging Events Cog - Automatisch alle Server-Ereignisse protokollieren.
Alle Event-Listener und System-Logs im App-Karten UI Design (0x2b2d31) mit kompaktem Abstand.
"""

import logging

import discord
from discord.ext import commands

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db

logger = logging.getLogger("void_shop_bot.logging_events")


class LoggingEventsCog(commands.Cog, name="LoggingEventsCog"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return

        # --- FAQ-Auto-Bot: in Ticket-Kanälen häufige Fragen automatisch beantworten ---
        try:
            if any(p in message.channel.name for p in ["kauf-", "support-", "partner-"]):
                answer = db.faq_lookup(message.content)
                if answer:
                    from bot.cogs.components_v2 import PrestigeContainer
                    cont = PrestigeContainer(
                        "🤖 Auto-FAQ", answer + "\n\n-# Ein Teammitglied meldet sich trotzdem persönlich bei dir.",
                        accent=0x5865f2, footer=False)
                    v = discord.ui.LayoutView(timeout=None)
                    v.add_item(cont)
                    await message.channel.send(view=v)
        except Exception:
            pass

        is_staff = message.author.guild_permissions.manage_messages or any(
            r.name in [
                "👑│ 𝗩𝗢𝗜𝗗 • Owner",
                "👑│ 𝗩𝗢𝗜𝗗 • Co-Owner",
                "🛠️│ 𝗩𝗢𝗜𝗗 • Admin",
                "🛡️│ 𝗩𝗢𝗜𝗗 • Moderator",
                "🎫│ 𝗩𝗢𝗜𝗗 • Support",
            ]
            for r in message.author.roles
        )

        if not is_staff:
            content_low = message.content.lower()
            if any(x in content_low for x in [
                "http://", "https://", "www.", ".com", ".net", ".org",
                ".ru", ".xyz", "free robux", "discord.gg/",
            ]):
                allowed_domains = [
                    "roblox.com", "discord.com", "youtube.com",
                    "youtu.be", "tenor.com", "giphy.com", "railway.app",
                    "void-shop",
                ]
                if not any(dom in content_low for dom in allowed_domains):
                    try:
                        await message.delete()
                        warn_em = EmbedHelper.create_prestige_embed(
                            title="🚨 ANTI-SCAM SCHILD AKTIV",
                            description=(
                                f"> {message.author.mention}, das Posten externer / unautorisierter Links oder Phishing-Begriffe ist hier verboten!\n"
                                "~~                                                              ~~\n"
                                "> 🛡️ *Unser Sicherheitsschild hat die Nachricht automatisch entfernt.*"
                            ),
                            color=0x2b2d31,
                            author_user=message.author,
                            bot_user=self.bot.user,
                        )
                        await message.channel.send(embed=warn_em, delete_after=10)
                        db.add_scam_block()
                        db.add_log(
                            "security",
                            f"Scam-Link von {message.author.name} in #{message.channel.name} blockiert",
                        )

                        sec_log = discord.utils.get(
                            message.guild.text_channels, name="🚨│security-logs"
                        ) or discord.utils.get(
                            message.guild.text_channels, name="security-logs"
                        )
                        if sec_log:
                            lem = EmbedHelper.create_prestige_embed(
                                title="🚨 Phishing / Scam blockiert",
                                description=(
                                    f"> **User:** {message.author.mention} ({message.author.name})\n"
                                    f"> **Kanal:** {message.channel.mention}\n"
                                    "~~                                                              ~~\n"
                                    f"> **Blockierter Inhalt:** `{message.content}`\n"
                                    "~~                                                              ~~"
                                ),
                                color=0x2b2d31,
                                bot_user=self.bot.user
                            )
                            await sec_log.send(embed=lem)
                    except Exception:
                        pass
                    return

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild or message.author.bot:
            return
        log_channel = discord.utils.get(message.guild.text_channels, name="📝│message-logs")
        if log_channel:
            embed = EmbedHelper.create_prestige_embed(
                title="🗑️ Nachricht gelöscht",
                description=(
                    f"> **Kanal:** {message.channel.mention}\n"
                    f"> **Autor:** {message.author.mention} ({message.author.name})\n"
                    "~~                                                              ~~\n"
                    "> **Inhalt:**\n"
                    f"> {message.content if message.content else '*Kein Text (z.B. Bild)*'}\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=message.author,
                bot_user=self.bot.user,
            )
            db.add_log("message", f"Nachricht in #{message.channel.name} gelöscht")
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        log_channel = discord.utils.get(before.guild.text_channels, name="📝│message-logs")
        if log_channel:
            embed = EmbedHelper.create_prestige_embed(
                title="✏️ Nachricht bearbeitet",
                description=(
                    f"> **Kanal:** {before.channel.mention}\n"
                    f"> **Autor:** {before.author.mention} ({before.author.name})\n"
                    "~~                                                              ~~\n"
                    f"> **Zuvor:**\n"
                    f"> {before.content}\n"
                    "~~                                                              ~~\n"
                    f"> **Danach:**\n"
                    f"> {after.content}\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=before.author,
                bot_user=self.bot.user,
            )
            db.add_log(
                "message",
                f"Nachricht von {before.author.name} in #{before.channel.name} bearbeitet",
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_channel = discord.utils.get(channel.guild.text_channels, name="⚙️│system-logs")
        if not log_channel:
            return
        moderator = None
        try:
            now = discord.utils.utcnow()
            async for entry in channel.guild.audit_logs(
                action=discord.AuditLogAction.channel_create, limit=1
            ):
                if entry.target.id == channel.id and (now - entry.created_at).total_seconds() < 15:
                    moderator = entry.user
                    break
        except Exception:
            pass
        embed = EmbedHelper.create_prestige_embed(
            title="📁 Kanal erstellt",
            description=(
                f"> **Kanal:** {channel.name}\n"
                f"> **Kategorie:** {channel.category.name if channel.category else 'Keine'}\n"
                "~~                                                              ~~\n"
                f"> **Mitarbeiter:** {moderator.mention if moderator else 'Unbekannt'}\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=moderator if moderator else self.bot.user,
            bot_user=self.bot.user,
        )
        db.add_log("system", f"Kanal #{channel.name} erstellt")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_channel = discord.utils.get(channel.guild.text_channels, name="⚙️│system-logs")
        if not log_channel:
            return
        moderator = None
        try:
            now = discord.utils.utcnow()
            async for entry in channel.guild.audit_logs(
                action=discord.AuditLogAction.channel_delete, limit=1
            ):
                if entry.target.id == channel.id and (now - entry.created_at).total_seconds() < 15:
                    moderator = entry.user
                    break
        except Exception:
            pass
        embed = EmbedHelper.create_prestige_embed(
            title="🛑 Kanal gelöscht",
            description=(
                f"> **Kanal:** {channel.name}\n"
                "~~                                                              ~~\n"
                f"> **Mitarbeiter:** {moderator.mention if moderator else 'Unbekannt'}\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=moderator if moderator else self.bot.user,
            bot_user=self.bot.user,
        )
        db.add_log("system", f"Kanal #{channel.name} gelöscht")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        log_channel = discord.utils.get(role.guild.text_channels, name="⚙️│system-logs")
        if not log_channel:
            return
        moderator = None
        try:
            now = discord.utils.utcnow()
            async for entry in role.guild.audit_logs(
                action=discord.AuditLogAction.role_create, limit=1
            ):
                if entry.target.id == role.id and (now - entry.created_at).total_seconds() < 15:
                    moderator = entry.user
                    break
        except Exception:
            pass
        embed = EmbedHelper.create_prestige_embed(
            title="👑 Rolle erstellt",
            description=(
                f"> **Rolle:** {role.mention} ({role.name})\n"
                "~~                                                              ~~\n"
                f"> **Mitarbeiter:** {moderator.mention if moderator else 'Unbekannt'}\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=moderator if moderator else self.bot.user,
            bot_user=self.bot.user,
        )
        db.add_log("system", f"Rolle @{role.name} erstellt")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        log_channel = discord.utils.get(role.guild.text_channels, name="⚙️│system-logs")
        if not log_channel:
            return
        moderator = None
        try:
            now = discord.utils.utcnow()
            async for entry in role.guild.audit_logs(
                action=discord.AuditLogAction.role_delete, limit=1
            ):
                if entry.target.id == role.id and (now - entry.created_at).total_seconds() < 15:
                    moderator = entry.user
                    break
        except Exception:
            pass
        embed = EmbedHelper.create_prestige_embed(
            title="🛑 Rolle gelöscht",
            description=(
                f"> **Rolle:** {role.name}\n"
                "~~                                                              ~~\n"
                f"> **Mitarbeiter:** {moderator.mention if moderator else 'Unbekannt'}\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=moderator if moderator else self.bot.user,
            bot_user=self.bot.user,
        )
        db.add_log("system", f"Rolle @{role.name} gelöscht")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        log_channel = discord.utils.get(member.guild.text_channels, name="💬│voice-logs")
        if not log_channel:
            return

        db.add_log("voice", f"{member.name} änderte Sprachkanal")
        if before.channel is None and after.channel is not None:
            embed = EmbedHelper.create_prestige_embed(
                title="🔊 Voice-Kanal betreten",
                description=f"> {member.mention} hat den Sprachkanal {after.channel.mention} betreten.",
                color=0x2b2d31,
                author_user=member,
                bot_user=self.bot.user,
            )
            await log_channel.send(embed=embed)
        elif before.channel is not None and after.channel is None:
            embed = EmbedHelper.create_prestige_embed(
                title="🔇 Voice-Kanal verlassen",
                description=f"> {member.mention} hat den Sprachkanal {before.channel.mention} verlassen.",
                color=0x2b2d31,
                author_user=member,
                bot_user=self.bot.user,
            )
            await log_channel.send(embed=embed)
        elif (
            before.channel is not None
            and after.channel is not None
            and before.channel.id != after.channel.id
        ):
            embed = EmbedHelper.create_prestige_embed(
                title="🔄 Voice-Kanal gewechselt",
                description=(
                    f"> {member.mention} hat den Sprachkanal gewechselt.\n"
                    "~~                                                              ~~\n"
                    f"> **Von:** {before.channel.mention}\n"
                    f"> **Zu:** {after.channel.mention}\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=member,
                bot_user=self.bot.user,
            )
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        welcome_channel = discord.utils.get(guild.text_channels, name="👋│willkommen")
        if welcome_channel:
            embed_welcome_msg = EmbedHelper.create_prestige_embed(
                title="👋 HERZLICH WILLKOMMEN BEI 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 👋",
                description=(
                    f"> Hallo **{member.name}**! Schön, dass du da bist!\n"
                    "> Wir freuen uns ungemein, dich auf unserem prestigeträchtigen Server begrüßen zu dürfen.\n"
                    "~~                                                              ~~\n"
                    "> **Deine ersten Schritte:**\n"
                    "> 🔐 │ Schalte dich sofort frei im Kanal <#verify_channel_id_here> (oder `#verify-here`).\n"
                    f"> 👤 │ Roblox-Verifizierung nutzen: `/verify <Username>`\n"
                    f"> 🛒 │ Schalte exklusive Rollen frei mit: `/checkbuy <Username> <Gamepass_ID>`\n"
                    "~~                                                              ~~\n"
                    f"> 📌 │ Du bist unser **{len(guild.members)}.** wertvolles Mitglied!\n"
                    "> Genieße deinen Aufenthalt und hab eine tolle Zeit bei uns! ✨"
                ),
                color=0x2b2d31,
                author_user=member,
                bot_user=self.bot.user,
            )
            embed_welcome_msg.set_thumbnail(url=member.display_avatar.url)
            v_channel = discord.utils.get(guild.text_channels, name="🔐│verify-here")
            if v_channel:
                embed_welcome_msg.description = embed_welcome_msg.description.replace(
                    "<#verify_channel_id_here>", v_channel.mention
                )
            await welcome_channel.send(
                content=f"Hallo {member.mention}, schön dass du da bist! 👋",
                embed=embed_welcome_msg,
            )

        stats_cog = self.bot.get_cog("StatsCog")
        if stats_cog:
            await stats_cog.update_stats_channels(guild)

        log_channel = discord.utils.get(guild.text_channels, name="📥│join-leave-logs")
        invite_log_channel = discord.utils.get(guild.text_channels, name="📩│invite-logs")

        used_invite = None
        try:
            if guild.id in self.bot.invites_cache:
                old_invites = self.bot.invites_cache[guild.id]
                new_invites = await guild.invites()
                self.bot.invites_cache[guild.id] = new_invites

                for old_inv in old_invites:
                    for new_inv in new_invites:
                        if old_inv.code == new_inv.code and new_inv.uses > old_inv.uses:
                            used_invite = new_inv
                            break
        except Exception:
            pass

        db.add_log("join_leave", f"{member.name} trat dem Server bei")
        if log_channel:
            embed = EmbedHelper.create_prestige_embed(
                title="📥 Mitglied beigetreten",
                description=(
                    f"> {member.mention} ({member.name}) hat den Server betreten.\n"
                    "~~                                                              ~~\n"
                    f"> **Account-Erstellung:** {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=member,
                bot_user=self.bot.user,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            await log_channel.send(embed=embed)

        if used_invite:
            total_invs = 0
            try:
                curr_invs = self.bot.invites_cache.get(guild.id, [])
                total_invs = sum(
                    i.uses
                    for i in curr_invs
                    if i.inviter and i.inviter.id == used_invite.inviter.id
                )
            except Exception:
                total_invs = used_invite.uses

            invites_pub_channel = discord.utils.get(
                guild.text_channels, name="📩│invites"
            ) or discord.utils.get(guild.text_channels, name="invites")
            if invites_pub_channel:
                embed_pub_inv = EmbedHelper.create_prestige_embed(
                    title="🎉 Neuer Server-Beitritt über Einladung!",
                    description=(
                        f"> Herzlich willkommen, {member.mention}!\n"
                        "~~                                                              ~~\n"
                        f"> **Eingeladen von:** {used_invite.inviter.mention}\n"
                        f"> 📈 **Gesamte Invites von {used_invite.inviter.name}:** `{total_invs}`\n"
                        "~~                                                              ~~\n"
                        "> *Sammle ebenfalls Invites, um dir exklusive Belohnungen aus dem Shop zu sichern!*"
                    ),
                    color=0x2b2d31,
                    author_user=used_invite.inviter,
                    bot_user=self.bot.user,
                )
                embed_pub_inv.set_thumbnail(url=member.display_avatar.url)
                await invites_pub_channel.send(embed=embed_pub_inv)

            if invite_log_channel:
                embed_inv = EmbedHelper.create_prestige_embed(
                    title="📩 Einladung genutzt",
                    description=(
                        f"> {member.mention} ist beigetreten mit der Einladung von {used_invite.inviter.mention}.\n"
                        "~~                                                              ~~\n"
                        f"> **Code:** `{used_invite.code}`\n"
                        f"> **Code-Nutzungen:** {used_invite.uses}\n"
                        f"> **Gesamte Invites des Users:** `{total_invs}`\n"
                        "~~                                                              ~~"
                    ),
                    color=0x2b2d31,
                    author_user=used_invite.inviter,
                    bot_user=self.bot.user,
                )
                await invite_log_channel.send(embed=embed_inv)

            if total_invs in [5, 10, 20]:
                gen_ch = discord.utils.get(guild.text_channels, name="💬│general-chat") or discord.utils.get(guild.text_channels, name="general-chat")
                if gen_ch:
                    m_title = f"🎆 VOID-BOUNTY MEILENSTEIN ERREICHT: {total_invs} INVITES! 🎆"
                    m_desc = (
                        f"> ***„🎉 Herzlichen Glückwunsch an {used_invite.inviter.mention}! Du hast {total_invs} Freunde auf unseren Server eingeladen!***\n"
                        "~~                                                              ~~\n"
                    )
                    if total_invs == 5:
                        m_desc += "> 🎁 **Deine Prämie:** `Gratis T-Shirt Template PNG`\n> ⚡ **Status:** *Wurde dir soeben per Auto-Delivery DM zugestellt!*\n~~                                                              ~~"
                    elif total_invs == 10:
                        m_desc += "> 🎁 **Deine Prämie:** `Premium FastFlags v2 Ultra Config`\n> ⚡ **Status:** *Wurde dir soeben per Auto-Delivery DM zugestellt!*\n~~                                                              ~~"
                    elif total_invs == 20:
                        m_desc += "> 🎁 **Deine Prämie:** `Premium Discord Server Template Layout`\n> ⚡ **Status:** *Wurde dir soeben per Auto-Delivery DM zugestellt!*\n~~                                                              ~~"
                    
                    bounty_em = EmbedHelper.create_prestige_embed(title=m_title, description=m_desc, color=0x2b2d31, bot_user=self.bot.user)
                    bounty_em.set_thumbnail(url=used_invite.inviter.display_avatar.url)
                    await gen_ch.send(embed=bounty_em)

                try:
                    dm_title = f"🎁 VOID • AUTO-DELIVERY ({total_invs} Invites Prämie)"
                    if total_invs == 5:
                        dm_desc = "> Glückwunsch zu 5 Invites! Hier ist dein gratis T-Shirt Template:\n~~                                                              ~~\n> Download: `https://void-shop.cloud/assets/bounty_shirt.png`\n~~                                                              ~~"
                    elif total_invs == 10:
                        dm_desc = "> Glückwunsch zu 10 Invites! Hier ist deine Premium FastFlags Ultra Config:\n~~                                                              ~~\n> Download: `https://void-shop.cloud/assets/fastflags_ultra.zip`\n~~                                                              ~~"
                    elif total_invs == 20:
                        dm_desc = "> Glückwunsch zu 20 Invites! Hier ist dein Premium Discord Server Layout:\n~~                                                              ~~\n> Backup Code: `https://void-shop.cloud/assets/discord_template.json`\n~~                                                              ~~"
                    dm_em = EmbedHelper.create_prestige_embed(title=dm_title, description=dm_desc, color=0x2b2d31, bot_user=self.bot.user)
                    await used_invite.inviter.send(embed=dm_em)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild

        goodbye_channel = discord.utils.get(guild.text_channels, name="💨│aufwiedersehen")
        if goodbye_channel:
            embed_goodbye_msg = EmbedHelper.create_prestige_embed(
                title="💨 AUF WIEDERSEHEN...",
                description=(
                    f"> **{member.name}** hat uns verlassen.\n"
                    "~~                                                              ~~\n"
                    "> Wir wünschen dir alles Gute auf deinem weiteren Weg! 💨\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=member,
                bot_user=self.bot.user,
            )
            embed_goodbye_msg.set_thumbnail(url=member.display_avatar.url)
            await goodbye_channel.send(embed=embed_goodbye_msg)

        stats_cog = self.bot.get_cog("StatsCog")
        if stats_cog:
            await stats_cog.update_stats_channels(guild)

        kicked_by = None
        reason = "Kein Grund angegeben"

        try:
            now = discord.utils.utcnow()
            async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
                if entry.target.id == member.id and (now - entry.created_at).total_seconds() < 15:
                    kicked_by = entry.user
                    reason = entry.reason if entry.reason else "Kein Grund angegeben"
                    break
        except Exception:
            pass

        db.add_log("join_leave", f"{member.name} verließ den Server")
        if kicked_by:
            log_channel = discord.utils.get(guild.text_channels, name="🔨│ban-kick-logs")
            if log_channel:
                embed = EmbedHelper.create_prestige_embed(
                    title="👢 Mitglied gekickt",
                    description=(
                        f"> **Mitglied:** {member.name} ({member.id})\n"
                        f"> **Moderator:** {kicked_by.mention}\n"
                        "~~                                                              ~~\n"
                        f"> **Grund:** {reason}\n"
                        "~~                                                              ~~"
                    ),
                    color=0x2b2d31,
                    author_user=kicked_by,
                    bot_user=self.bot.user,
                )
                await log_channel.send(embed=embed)
        else:
            log_channel = discord.utils.get(guild.text_channels, name="📥│join-leave-logs")
            if log_channel:
                embed = EmbedHelper.create_prestige_embed(
                    title="📤 Mitglied verlassen",
                    description=f"> {member.mention} ({member.name}) hat den Server verlassen.",
                    color=0x2b2d31,
                    author_user=member,
                    bot_user=self.bot.user,
                )
                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        log_channel = discord.utils.get(guild.text_channels, name="🔨│ban-kick-logs")
        if not log_channel:
            return

        banned_by = None
        reason = "Kein Grund angegeben"

        try:
            now = discord.utils.utcnow()
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                if entry.target.id == user.id and (now - entry.created_at).total_seconds() < 15:
                    banned_by = entry.user
                    reason = entry.reason if entry.reason else "Kein Grund angegeben"
                    break
        except Exception:
            pass

        embed = EmbedHelper.create_prestige_embed(
            title="🔨 Mitglied gebannt",
            description=(
                f"> **Mitglied:** {user.name} ({user.id})\n"
                f"> **Moderator:** {banned_by.mention if banned_by else 'Unbekannt'}\n"
                "~~                                                              ~~\n"
                f"> **Grund:** {reason}\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=banned_by if banned_by else user,
            bot_user=self.bot.user,
        )
        db.add_log("ban_kick", f"{user.name} wurde gebannt")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        guild = after.guild

        if before.roles != after.roles or before.premium_since != after.premium_since:
            stats_cog = self.bot.get_cog("StatsCog")
            if stats_cog:
                await stats_cog.update_stats_channels(guild)

        if before.timed_out_until != after.timed_out_until:
            log_channel = discord.utils.get(guild.text_channels, name="🔨│ban-kick-logs")
            if log_channel:
                if after.timed_out_until is not None:
                    moderator = None
                    reason = "Kein Grund angegeben"
                    try:
                        async for entry in guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
                            if entry.target.id == after.id and hasattr(entry.after, "communication_disabled_until"):
                                moderator = entry.user
                                reason = entry.reason if entry.reason else "Kein Grund angegeben"
                                break
                    except Exception:
                        pass

                    embed = EmbedHelper.create_prestige_embed(
                        title="⏳ Timeout verhängt (Stummgeschaltet)",
                        description=(
                            f"> **Mitglied:** {after.mention}\n"
                            f"> **Moderator:** {moderator.mention if moderator else 'Unbekannt'}\n"
                            "~~                                                              ~~\n"
                            f"> **Bis:** {after.timed_out_until.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"> **Grund:** {reason}\n"
                            "~~                                                              ~~"
                        ),
                        color=0x2b2d31,
                        author_user=moderator if moderator else after,
                        bot_user=self.bot.user,
                    )
                    await log_channel.send(embed=embed)
                else:
                    embed = EmbedHelper.create_prestige_embed(
                        title="🔊 Timeout vorzeitig aufgehoben",
                        description=f"> Der Timeout für {after.mention} wurde aufgehoben.",
                        color=0x2b2d31,
                        author_user=after,
                        bot_user=self.bot.user,
                    )
                    await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            cid = interaction.data.get("custom_id", "")
            # Persistente Auto-Delivery-Buttons (deliver:<product>:<buyer_id>)
            if cid.startswith("deliver:"):
                try:
                    from bot.cogs.tickets import is_staff, deliver_product
                    parts = cid.split(":")
                    product_key, buyer_id = parts[1], parts[2]
                    if not is_staff(interaction.user):
                        await interaction.response.send_message("❌ Nur das Team kann Käufe bestätigen!", ephemeral=True)
                    else:
                        await deliver_product(interaction, product_key, buyer_id)
                except Exception as e:
                    logger.error(f"Delivery-Button Fehler: {e}")
                return
            # Warenkorb-Buttons (cart_add / cart_clear / cart_checkout)
            if cid.startswith("cart_"):
                try:
                    from bot.cogs.tickets import handle_cart_interaction
                    await handle_cart_interaction(interaction)
                except Exception as e:
                    logger.error(f"Cart-Button Fehler: {e}")
                return
            if cid == "claim_ticket_btn":
                db.add_log("ticket", f"Button 'Claim' von {interaction.user.name} gedrückt")
                try:
                    db.ticket_claim(interaction.channel.id, interaction.user.name)
                except Exception:
                    pass
            elif cid == "close_ticket_btn":
                db.add_log("ticket", f"Button 'Close' von {interaction.user.name} gedrückt")
                try:
                    db.ticket_close(interaction.channel.id)
                except Exception:
                    pass
