"""
Tickets Cog - Ticket-System, Close-Process mit Web-Transkripten, Vouch-Leveling
Alle interaktiven Embeds im App-Karten UI Design (0x2b2d31) mit kompaktem Abstand und Button-Footer.
"""

import io
import asyncio
import logging

import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Button

from bot.cogs.embed_helper import EmbedHelper
from bot.cogs.database import db

logger = logging.getLogger("void_shop_bot.tickets")


# --- INTERAKTIVES TICKET-SYSTEM MODALS (ADD/REMOVE USER) ---

class AddUserModal(discord.ui.Modal, title="User zum Ticket hinzufügen"):
    user_input = TextInput(
        label="User-ID oder Username",
        placeholder="z.B. 123456789012345678 oder name",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = interaction.channel

        user_str = self.user_input.value
        user = None

        if user_str.isdigit():
            user = guild.get_member(int(user_str))
            if not user:
                try:
                    user = await guild.fetch_member(int(user_str))
                except Exception:
                    pass
        if not user:
            user = discord.utils.get(guild.members, name=user_str)

        if not user:
            await interaction.response.send_message(
                f"❌ User '{user_str}' wurde auf diesem Server nicht gefunden!",
                ephemeral=True,
            )
            return

        try:
            await channel.set_permissions(
                user, view_channel=True, send_messages=True, read_message_history=True
            )
            embed = EmbedHelper.create_prestige_embed(
                title="➕ User hinzugefügt",
                description=(
                    f"> {interaction.user.mention} hat {user.mention} zum Ticket hinzugefügt.\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=interaction.user,
                bot_user=interaction.client.user,
            )
            await channel.send(embed=embed)
            await interaction.response.send_message(
                f"✅ {user.name} wurde erfolgreich hinzugefügt!", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Fehler beim Hinzufügen: {e}", ephemeral=True
            )


class RemoveUserModal(discord.ui.Modal, title="User aus Ticket entfernen"):
    user_input = TextInput(
        label="User-ID oder Username",
        placeholder="z.B. 123456789012345678",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = interaction.channel

        user_str = self.user_input.value
        user = None

        if user_str.isdigit():
            user = guild.get_member(int(user_str))
            if not user:
                try:
                    user = await guild.fetch_member(int(user_str))
                except Exception:
                    pass
        if not user:
            user = discord.utils.get(guild.members, name=user_str)

        if not user:
            await interaction.response.send_message(
                f"❌ User '{user_str}' wurde nicht gefunden!", ephemeral=True
            )
            return

        try:
            await channel.set_permissions(user, overwrite=None)
            embed = EmbedHelper.create_prestige_embed(
                title="➖ User entfernt",
                description=(
                    f"> {interaction.user.mention} hat {user.mention} aus dem Ticket entfernt.\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=interaction.user,
                bot_user=interaction.client.user,
            )
            await channel.send(embed=embed)
            await interaction.response.send_message(
                f"✅ {user.name} wurde erfolgreich entfernt!", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Fehler beim Entfernen: {e}", ephemeral=True
            )


# --- TICKET TRANSCRIPT & CLOSE HELPER ---

async def execute_ticket_close_process(channel, closed_by_user, bot_user):
    db.add_log("ticket", f"Ticket '{channel.name}' von {closed_by_user.name} geschlossen & archiviert")
    embed_closing = EmbedHelper.create_prestige_embed(
        title="🔒 Ticket-Schließung",
        description=(
            "> ⚠️ Dieses Ticket wird transkribiert und in **4 Sekunden** endgültig gelöscht...\n"
            "~~                                                              ~~"
        ),
        color=0x2b2d31,
        author_user=closed_by_user,
        bot_user=bot_user,
    )
    try:
        await channel.send(embed=embed_closing)
    except Exception:
        pass
    await asyncio.sleep(4)

    try:
        messages = []
        transcript_messages_json = []
        async for msg in channel.history(limit=1000, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = (
                f"{msg.author.name}#{msg.author.discriminator}"
                if msg.author.discriminator != "0"
                else msg.author.name
            )
            if msg.author.bot:
                author += " [BOT]"
            content_str = msg.content if msg.content else "[Kein Textinhalt]"
            if msg.attachments:
                att_urls = ", ".join([att.url for att in msg.attachments])
                content_str += f" (Anhänge: {att_urls})"
            if msg.embeds:
                content_str += f" [Embed: {msg.embeds[0].title or 'Ohne Titel'}]"
            messages.append(f"[{timestamp}] {author}: {content_str}")

            transcript_messages_json.append({
                "author": msg.author.name,
                "avatar": msg.author.display_avatar.url if msg.author.display_avatar else "https://cdn.discordapp.com/embed/avatars/0.png",
                "timestamp": timestamp,
                "content": content_str,
                "bot": msg.author.bot
            })

        db.add_ticket_transcript(channel.name, closed_by_user, transcript_messages_json)

        transcript_content = (
            "==================================================\n"
            "         𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 - TICKET TRANSKRIPT             \n"
            "==================================================\n"
            f"Kanalname:     {channel.name}\n"
            f"Geschlossen:   {closed_by_user.name} ({closed_by_user.id})\n"
            f"Nachrichten:   {len(messages)}\n"
            "==================================================\n\n"
            + "\n".join(messages)
        )

        ticket_logs_channel = discord.utils.get(channel.guild.text_channels, name="💾│ticket-logs")
        if ticket_logs_channel:
            file_data = io.BytesIO(transcript_content.encode("utf-8"))
            discord_file = discord.File(file_data, filename=f"transcript-{channel.name}.txt")
            embed_log = EmbedHelper.create_prestige_embed(
                title="💾 Ticket-Transkript archiviert",
                description=(
                    f"> **Ticket:** {channel.name}\n"
                    f"> **Geschlossen von:** {closed_by_user.mention}\n"
                    "~~                                                              ~~\n"
                    "> Das vollständige Gesprächsprotokoll wurde erfolgreich gesichert und ist auch im Web-Dashboard verfügbar!\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=closed_by_user,
                bot_user=bot_user,
            )
            await ticket_logs_channel.send(embed=embed_log, file=discord_file)
    except Exception as e:
        logger.error(f"Fehler beim Erstellen des Ticket-Transkripts: {e}")

    try:
        await channel.delete()
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Ticket-Kanals: {e}")


# --- KAUF-TICKET SCHLIESSUNGS-QUESTIONNAIRE & VOUCH LEVELING ---

class PurchaseReviewModal(discord.ui.Modal):
    def __init__(self, product_name: str):
        super().__init__(title="⭐ Deine Bewertung (3/3)")
        self.product_name = product_name

    stars_input = TextInput(
        label="Sterne-Bewertung (1 bis 5)",
        placeholder="z.B. ⭐⭐⭐⭐⭐ oder 5/5",
        required=True,
        max_length=25,
    )

    feedback_input = TextInput(
        label="Wie fandest du Support & Produkt?",
        style=discord.TextStyle.paragraph,
        placeholder="Beschreibe kurz deine Erfahrung... (Sehr schneller Support, FastFlags funktionieren perfekt etc.)",
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        stars = self.stars_input.value
        feedback = self.feedback_input.value

        vouch_channel = discord.utils.get(guild.text_channels, name="🤝│vouches") or discord.utils.get(
            guild.text_channels, name="vouches"
        )

        stars_cnt = 5
        if "1" in stars: stars_cnt = 1
        elif "2" in stars: stars_cnt = 2
        elif "3" in stars: stars_cnt = 3
        elif "4" in stars: stars_cnt = 4

        vouch_count = db.add_user_vouch(member.id)
        role_reward_str = ""

        try:
            r_bronze = discord.utils.get(guild.roles, name="🥉│ 𝗩𝗢𝗜𝗗 • Bronze Buyer")
            r_silver = discord.utils.get(guild.roles, name="🥈│ 𝗩𝗢𝗜𝗗 • Silver Buyer")
            r_gold = discord.utils.get(guild.roles, name="🥇│ 𝗩𝗢𝗜𝗗 • Gold Buyer")
            r_diamond = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • Diamond Buyer")

            if vouch_count == 1:
                if r_bronze: await member.add_roles(r_bronze)
                db.add_coins(member.id, 20)
                role_reward_str = "\n~~                                                              ~~\n> 🎁 **Vouch-Leveling Bonus (1 Vouch):** Du hast die Rolle `🥉 Bronze Buyer` und `+20 Void-Coins` erhalten!"
            elif vouch_count == 3:
                if r_silver: await member.add_roles(r_silver)
                role_reward_str = "\n~~                                                              ~~\n> 🎁 **Vouch-Leveling Bonus (3 Vouches):** Du hast die Rolle `🥈 Silver Buyer` erhalten! Eine gratis T-Shirt Vorlage wurde dir per DM gesendet."
                try:
                    dm_em = EmbedHelper.create_prestige_embed(
                        title="🎁 VOID • AUTO-DELIVERY (Treue-Prämie)",
                        description=(
                            "> Vielen Dank für deinen 3. Vouch! Hier ist dein exklusives T-Shirt Template:\n"
                            "~~                                                              ~~\n"
                            "> Download: `https://void-shop.cloud/assets/free_template.png`\n"
                            "~~                                                              ~~"
                        ),
                        color=0x2b2d31, bot_user=interaction.client.user
                    )
                    await member.send(embed=dm_em)
                except Exception: pass
            elif vouch_count == 5:
                if r_gold: await member.add_roles(r_gold)
                role_reward_str = "\n~~                                                              ~~\n> 🎁 **Vouch-Leveling Bonus (5 Vouches):** Du hast die Rolle `🥇 Gold Buyer` erhalten und hast nun Zugriff auf die exklusive VIP-Lounge!"
            elif vouch_count >= 10:
                if r_diamond: await member.add_roles(r_diamond)
                role_reward_str = "\n~~                                                              ~~\n> 💎 **Vouch-Leveling Meister (10 Vouches):** Du hast die ultimative Rolle `💎 Diamond Buyer` erreicht! Du erhältst ab sofort lebenslang 10% Rabatt im Shop."
        except Exception:
            pass

        if vouch_channel:
            vouch_embed = EmbedHelper.create_prestige_embed(
                title="⭐ NEUE KUNDENBEWERTUNG ⭐",
                description=(
                    f"> **Kunde:** {member.mention} ({member.name})\n"
                    f"> **Produkt:** `{self.product_name}`\n"
                    f"> **Bewertung:** {stars}\n"
                    f"> **Vouch-Zähler:** `{vouch_count}x bewertet`\n"
                    "~~                                                              ~~\n"
                    "> **Rezension:**\n"
                    f"> *\"{feedback}\"*\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=member,
                bot_user=interaction.client.user,
            )
            vouch_embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await vouch_channel.send(embed=vouch_embed)
            except Exception:
                pass

        thank_embed = EmbedHelper.create_prestige_embed(
            title="🎉 Herzlichen Dank für deine wunderbare Bewertung!",
            description=(
                f"> Dein Feedback wurde direkt im Kanal {vouch_channel.mention if vouch_channel else '#vouches'} veröffentlicht!{role_reward_str}\n"
                "~~                                                              ~~\n"
                "> Das Ticket wird nun abgeschlossen...\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=member,
            bot_user=interaction.client.user,
        )
        await interaction.response.send_message(embed=thank_embed)

        await execute_ticket_close_process(interaction.channel, member, interaction.client.user)


class PurchaseQuestion2View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Powered by BotForge", style=discord.ButtonStyle.secondary, disabled=True, row=4))

    @discord.ui.button(label="🚀 FastFlags", style=discord.ButtonStyle.primary, custom_id="pq2_fastflags", row=0)
    async def prod_fastflags(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseReviewModal("FastFlags 🚀"))

    @discord.ui.button(label="👕 T-Shirt / Kleidung", style=discord.ButtonStyle.primary, custom_id="pq2_tshirt", row=0)
    async def prod_tshirt(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseReviewModal("T-Shirt / Kleidung 👕"))

    @discord.ui.button(label="🖥️ Discord Template", style=discord.ButtonStyle.primary, custom_id="pq2_template", row=0)
    async def prod_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseReviewModal("Discord Template 🖥️"))

    @discord.ui.button(label="✨ Sonstiges Produkt", style=discord.ButtonStyle.secondary, custom_id="pq2_other", row=0)
    async def prod_other(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseReviewModal("Sonstiges Produkt ✨"))

    @discord.ui.button(label="Überspringen ⏩", style=discord.ButtonStyle.danger, custom_id="pq2_skip", row=1)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await execute_ticket_close_process(interaction.channel, interaction.user, interaction.client.user)


class CloseTicketMenu(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Powered by BotForge", style=discord.ButtonStyle.secondary, disabled=True, row=4))

    @discord.ui.button(label="🔒 Direkt Schließen", style=discord.ButtonStyle.danger, custom_id="ctm_close", row=0)
    async def direct_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(view=self)
        await execute_ticket_close_process(interaction.channel, interaction.user, interaction.client.user)

    @discord.ui.button(label="🛒 Kauf bewerten & Belohnung erhalten", style=discord.ButtonStyle.success, custom_id="ctm_review", row=0)
    async def review_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(view=self)
        
        embed_q2 = EmbedHelper.create_prestige_embed(
            title="🛒 Vouch-Leveling: Produkt-Auswahl",
            description=(
                "> Klasse! Mit deiner Bewertung nimmst du automatisch am **Vouch-Leveling** teil! 🎉\n"
                "~~                                                              ~~\n"
                "> **Was genau hast du bei uns gekauft?**\n"
                "> Wähle unten das passende Produkt aus:\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=interaction.client.user,
        )
        await interaction.followup.send(embed=embed_q2, view=PurchaseQuestion2View())

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, custom_id="ctm_cancel", row=0)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


# --- PERSISTENTE TICKET-ANSICHTEN (TICKET SYSTEM) ---

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Powered by BotForge", style=discord.ButtonStyle.secondary, disabled=True, row=4))

    @discord.ui.button(
        label="Ticket claimen",
        style=discord.ButtonStyle.primary,
        emoji="🙋‍♂️",
        custom_id="claim_ticket_btn",
        row=0
    )
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = interaction.channel
        member = interaction.user

        support_role = discord.utils.get(guild.roles, name="🎫│ 𝗩𝗢𝗜𝗗 • Support")
        mod_role = discord.utils.get(guild.roles, name="🛡️│ 𝗩𝗢𝗜𝗗 • Moderator")
        admin_role = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • Admin")
        owner_role = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • Owner")

        has_staff_role = any(
            role in [support_role, mod_role, admin_role, owner_role] for role in member.roles
        )
        if not has_staff_role and not member.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ Du gehörst nicht zum Support-Team!", ephemeral=True
            )
            return

        button.disabled = True
        button.label = "Ticket geclaimed"
        button.style = discord.ButtonStyle.secondary

        try:
            ticket_creator = None
            for overwrite_target, overwrite_value in channel.overwrites.items():
                if isinstance(overwrite_target, discord.Member) and not overwrite_target.bot:
                    ticket_creator = overwrite_target
                    break

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                member: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                ),
            }

            if ticket_creator:
                overwrites[ticket_creator] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

            for role in [support_role, mod_role, admin_role, owner_role]:
                if role and role != guild.default_role:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True, send_messages=False, read_message_history=True
                    )

            await channel.edit(overwrites=overwrites)

            claim_embed = EmbedHelper.create_prestige_embed(
                title="🙋‍♂️ Ticket geclaimed!",
                description=(
                    f"> Dieses Ticket wird nun exklusiv von {member.mention} betreut.\n"
                    "~~                                                              ~~\n"
                    "> Bitte richte alle weiteren Fragen direkt an deinen zuständigen Supporter.\n"
                    "~~                                                              ~~"
                ),
                color=0x2b2d31,
                author_user=member,
                bot_user=interaction.client.user,
            )
            await channel.send(embed=claim_embed)
            await interaction.response.edit_message(view=self)

            ticket_logs_channel = discord.utils.get(guild.text_channels, name="💾│ticket-logs")
            if ticket_logs_channel:
                log_claim = EmbedHelper.create_prestige_embed(
                    title="🙋‍♂️ Ticket geclaimed",
                    description=(
                        f"> **Kanal:** {channel.mention}\n"
                        f"> **Supporter:** {member.mention} ({member.id})\n"
                        "~~                                                              ~~"
                    ),
                    color=0x2b2d31,
                    author_user=member,
                    bot_user=interaction.client.user,
                )
                await ticket_logs_channel.send(embed=log_claim)

            db.add_supporter_claim(member.name)

        except Exception as e:
            logger.error(f"Fehler beim Claimen des Tickets: {e}")
            await interaction.response.send_message(
                "❌ Fehler beim Aktualisieren der Ticketrechte.", ephemeral=True
            )

    @discord.ui.button(
        label="User hinzufügen",
        style=discord.ButtonStyle.success,
        emoji="➕",
        custom_id="add_user_ticket_btn",
        row=0
    )
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddUserModal())

    @discord.ui.button(
        label="User entfernen",
        style=discord.ButtonStyle.secondary,
        emoji="➖",
        custom_id="remove_user_ticket_btn",
        row=0
    )
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveUserModal())

    @discord.ui.button(
        label="Ticket schließen",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="close_ticket_btn",
        row=0
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_menu = EmbedHelper.create_prestige_embed(
            title="🔒 Ticket Schließen & Vouch-Leveling",
            description=(
                "> Möchtest du dieses Ticket direkt schließen oder an unserem **Gamifizierten Vouch-Leveling** teilnehmen?\n"
                "~~                                                              ~~\n"
                "> 🎁 **Deine Vorteile beim Bewerten:**\n"
                "> • **1 Vouch:** `🥉 Bronze Buyer` Rolle + 20 Void-Coins\n"
                "> • **3 Vouches:** `🥈 Silver Buyer` Rolle + 1 gratis T-Shirt Vorlage\n"
                "> • **5 Vouches:** `🥇 Gold Buyer` Rolle + VIP Lounge\n"
                "> • **10 Vouches:** `💎 Diamond Buyer` Rolle + 10% Lifetime Rabatt!\n"
                "~~                                                              ~~"
            ),
            color=0x2b2d31,
            author_user=interaction.user,
            bot_user=interaction.client.user,
        )
        await interaction.response.send_message(embed=embed_menu, view=CloseTicketMenu())


class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="Powered by BotForge", style=discord.ButtonStyle.secondary, disabled=True, row=4))

    @discord.ui.button(
        label="Produkt kaufen",
        style=discord.ButtonStyle.success,
        emoji="🛒",
        custom_id="btn_buy_ticket",
        row=0
    )
    async def buy_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_custom_ticket(interaction, "🛒│kauf", "Kauf-Anfrage")

    @discord.ui.button(
        label="Allgemeiner Support",
        style=discord.ButtonStyle.primary,
        emoji="⚙️",
        custom_id="btn_support_ticket",
        row=0
    )
    async def support_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_custom_ticket(interaction, "⚙️│support", "Allgemeiner Support")

    @discord.ui.button(
        label="Partnerschaft",
        style=discord.ButtonStyle.secondary,
        emoji="🤝",
        custom_id="btn_partner_ticket",
        row=0
    )
    async def partner_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_custom_ticket(interaction, "🤝│partner", "Partnerschafts-Anfrage")

    async def create_custom_ticket(self, interaction: discord.Interaction, prefix: str, ticket_type: str):
        guild = interaction.guild
        member = interaction.user

        if not guild:
            await interaction.response.send_message(
                "Dieser Befehl kann nur auf einem Server genutzt werden.", ephemeral=True
            )
            return

        ticket_channel_name = f"{prefix}-{member.name.lower()}"

        existing_channel = discord.utils.get(guild.channels, name=ticket_channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ Du hast bereits ein offenes Ticket für diesen Bereich: {existing_channel.mention}",
                ephemeral=True,
            )
            return

        owner_role = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • Owner")
        co_owner_role = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • Co-Owner")
        admin_role = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • Admin")
        manager_role = discord.utils.get(guild.roles, name="⚙️│ 𝗩𝗢𝗜𝗗 • Manager")
        mod_role = discord.utils.get(guild.roles, name="🛡️│ 𝗩𝗢𝗜𝗗 • Moderator")
        support_role = discord.utils.get(guild.roles, name="🎫│ 𝗩𝗢𝗜𝗗 • Support")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                add_reactions=True,
                read_message_history=True,
            ),
        }

        for role in [owner_role, co_owner_role, admin_role, manager_role, mod_role, support_role]:
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

        category = discord.utils.get(guild.categories, name="🎟️│── 𝗩𝗢𝗜𝗗 • 𝗦Ｕ𝗣𝗣𝗢𝗥𝗧 ──")

        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"{ticket_type} von {member.name}",
            )

            if ticket_type == "Kauf-Anfrage":
                description = (
                    f"> 👋 **Herzlich willkommen, {member.mention}!**\n"
                    "> Vielen Dank für dein Interesse an den Produkten von **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**.\n"
                    "> Unser Team wurde benachrichtigt und ist gleich für dich da!\n"
                    "~~                                                              ~~\n"
                    "> 📌 **Bitte teile uns direkt folgende Infos mit:**\n"
                    "> 🤖 │ **Roblox Username:**\n"
                    "> 🛍️ │ **Gewünschtes Produkt:** *(z.B. FastFlags, T-Shirt, Template)*\n"
                    "> 💳 │ **Zahlungsart:** *(PayPal, Robux, Paysafecard, Krypto)*\n"
                    "~~                                                              ~~\n"
                    "> ⏳ *Ein Teammitglied wird dein Ticket unten über 'Claimen' übernehmen.*"
                )
            elif ticket_type == "Allgemeiner Support":
                description = (
                    f"> 👋 **Herzlich willkommen, {member.mention}!**\n"
                    "> Du benötigst technische Hilfe oder hast Fragen zu unserem Shop?\n"
                    "> Bitte schildere dein Problem so genau wie möglich!\n"
                    "~~                                                              ~~\n"
                    "> 📌 **Häufige Themen:**\n"
                    "> 🚀 │ Installation & Nutzung der FastFlags\n"
                    "> ⚙️ │ Hilfe bei Discord Server-Layouts & Rechten\n"
                    "~~                                                              ~~\n"
                    "> ⏳ *Ein Supporter widmet sich dir in Kürze.*"
                )
            else:
                description = (
                    f"> 🤝 **Partnerschafts-Anfrage von {member.mention}**\n"
                    "> Schön, dass du mit **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** kooperieren möchtest!\n"
                    "~~                                                              ~~\n"
                    "> 📌 **Bitte nenne uns kurz deine Eckdaten:**\n"
                    "> 🔗 │ **Thema deines Servers:**\n"
                    "> 👥 │ **Mitgliederanzahl:**\n"
                    "> 📍 │ **Dauerhafter Einladungslink:**\n"
                    "~~                                                              ~~\n"
                    "> ⏳ *Die Projektleitung wird sich dein Angebot ansehen.*"
                )

            embed = EmbedHelper.create_prestige_embed(
                title=f"⚡ 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • {ticket_type.upper()} ⚡",
                description=description,
                color=0x2b2d31,
                author_user=member,
                bot_user=interaction.client.user,
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

            staff_pings = []
            for role in [owner_role, co_owner_role, admin_role, support_role]:
                if role:
                    staff_pings.append(role.mention)
            pings_str = " ".join(staff_pings) if staff_pings else ""

            await ticket_channel.send(
                content=f"{member.mention} {pings_str}",
                embed=embed,
                view=CloseTicketView(),
            )

            await interaction.response.send_message(
                f"✅ Dein Ticket wurde erfolgreich erstellt: {ticket_channel.mention}",
                ephemeral=True,
            )

            ticket_logs_channel = discord.utils.get(guild.text_channels, name="💾│ticket-logs")
            if ticket_logs_channel:
                embed_created = EmbedHelper.create_prestige_embed(
                    title="🎟️ Ticket erstellt",
                    description=(
                        f"> **Kanal:** {ticket_channel.mention}\n"
                        f"> **Typ:** {ticket_type}\n"
                        f"> **Ersteller:** {member.mention} ({member.id})\n"
                        "~~                                                              ~~"
                    ),
                    color=0x2b2d31,
                    author_user=member,
                    bot_user=interaction.client.user,
                )
                await ticket_logs_channel.send(embed=embed_created)

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Ticket-Kanals: {e}")
            await interaction.response.send_message(
                "❌ Fehler beim Erstellen des Tickets. Bitte wende dich an einen Administrator.",
                ephemeral=True,
            )


class TicketsCog(commands.Cog, name="TicketsCog"):
    def __init__(self, bot):
        self.bot = bot
