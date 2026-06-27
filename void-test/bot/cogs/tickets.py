"""
Tickets Cog - Ticket-System, Close-Process, Kauf-Review
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
                description=f"> {interaction.user.mention} hat {user.mention} zum Ticket hinzugefügt.",
                color=0x39FF14,
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
                description=f"> {interaction.user.mention} hat {user.mention} aus dem Ticket entfernt.",
                color=0xFF003C,
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
        description="> ⚠️ Dieses Ticket wird transkribiert und in **4 Sekunden** endgültig gelöscht...",
        color=0xFF003C,
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
                    "> Das vollständige Gesprächsprotokoll wurde erfolgreich gesichert."
                ),
                color=0xFF003C,
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


# --- KAUF-TICKET SCHLIESSUNGS-QUESTIONNAIRE ---

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

        if vouch_channel:
            vouch_embed = EmbedHelper.create_prestige_embed(
                title="⭐ NEUE KUNDENBEWERTUNG ⭐",
                description=(
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"> **Kunde:** {member.mention} ({member.name})\n"
                    f"> **Produkt:** `{self.product_name}`\n"
                    f"> **Bewertung:** {stars}\n\n"
                    "**Rezension:**\n"
                    f"> *\"{feedback}\"*"
                ),
                color=0xFFD700,
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
                f"> Dein Feedback wurde direkt im Kanal {vouch_channel.mention if vouch_channel else '#vouches'} veröffentlicht!\n\n"
                "Das Ticket wird nun abgeschlossen..."
            ),
            color=0x39FF14,
            author_user=member,
            bot_user=interaction.client.user,
        )
        await interaction.response.send_message(embed=thank_embed)

        await execute_ticket_close_process(interaction.channel, member, interaction.client.user)


class PurchaseQuestion2View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚀 FastFlags", style=discord.ButtonStyle.primary, custom_id="pq2_fastflags")
    async def prod_fastflags(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseReviewModal("FastFlags 🚀"))

    @discord.ui.button(label="👕 T-Shirt / Kleidung", style=discord.ButtonStyle.primary, custom_id="pq2_tshirt")
    async def prod_tshirt(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseReviewModal("T-Shirt / Kleidung 👕"))

    @discord.ui.button(label="🖥️ Discord Template", style=discord.ButtonStyle.primary, custom_id="pq2_template")
    async def prod_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseReviewModal("Discord Template 🖥️"))

    @discord.ui.button(label="✨ Sonstiges Produkt", style=discord.ButtonStyle.secondary, custom_id="pq2_other")
    async def prod_other(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PurchaseReviewModal("Sonstiges Produkt ✨"))

    @discord.ui.button(label="Überspringen ⏩", style=discord.ButtonStyle.danger, custom_id="pq2_skip")
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await execute_ticket_close_process(interaction.channel, interaction.user, interaction.client.user)


class PurchaseQuestion1View(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ja, habe ich! 🛍️", style=discord.ButtonStyle.success, custom_id="pq1_yes")
    async def bought_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        embed_q2 = EmbedHelper.create_prestige_embed(
            title="🛒 Frage 2/3: Produkt-Auswahl",
            description=(
                "> Klasse! 🎉\n\n"
                "**Was genau hast du bei uns gekauft?**\n"
                "Wähle unten das passende Produkt aus:"
            ),
            color=0x00F0FF,
            author_user=interaction.user,
            bot_user=interaction.client.user,
        )
        await interaction.followup.send(embed=embed_q2, view=PurchaseQuestion2View())

    @discord.ui.button(label="Nein, nichts gekauft ❌", style=discord.ButtonStyle.secondary, custom_id="pq1_no")
    async def bought_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await execute_ticket_close_process(interaction.channel, interaction.user, interaction.client.user)


# --- PERSISTENTE TICKET-ANSICHTEN (TICKET SYSTEM) ---

class CloseTicketView(discord.ui.View):
    """View für die Ticket-Steuerung im Ticket-Kanal."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ticket claimen",
        style=discord.ButtonStyle.primary,
        emoji="🙋‍♂️",
        custom_id="claim_ticket_btn",
    )
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = interaction.channel
        member = interaction.user

        support_role = discord.utils.get(guild.roles, name="🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁")
        mod_role = discord.utils.get(guild.roles, name="🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿")
        admin_role = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻")
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
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"> Dieses Ticket wird nun exklusiv von {member.mention} betreut.\n"
                    "> Bitte richte alle weiteren Fragen direkt an deinen zuständigen Supporter."
                ),
                color=0x00F0FF,
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
                        f"> **Supporter:** {member.mention} ({member.id})"
                    ),
                    color=0x00F0FF,
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
    )
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddUserModal())

    @discord.ui.button(
        label="User entfernen",
        style=discord.ButtonStyle.secondary,
        emoji="➖",
        custom_id="remove_user_ticket_btn",
    )
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveUserModal())

    @discord.ui.button(
        label="Ticket schließen",
        style=discord.ButtonStyle.red,
        emoji="🔒",
        custom_id="close_ticket_btn",
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        channel = interaction.channel
        is_buy_ticket = (channel.topic and "Kauf-Anfrage" in channel.topic) or (
            "kauf" in channel.name.lower()
        )

        if is_buy_ticket:
            embed_q1 = EmbedHelper.create_prestige_embed(
                title="🛒 Frage 1/3: Produktkauf",
                description=(
                    "> Bevor wir dein Kauf-Ticket schließen:\n\n"
                    "**Hast du erfolgreich ein Produkt bei uns gekauft?**"
                ),
                color=0xFFD700,
                author_user=interaction.user,
                bot_user=interaction.client.user,
            )
            await channel.send(embed=embed_q1, view=PurchaseQuestion1View())
        else:
            await execute_ticket_close_process(channel, interaction.user, interaction.client.user)


class TicketButton(discord.ui.View):
    """View für das Ticket-Erstellungs-Panel mit Kauf, Support und Partner-Buttons."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Produkt kaufen",
        style=discord.ButtonStyle.success,
        emoji="🛒",
        custom_id="btn_buy_ticket",
    )
    async def buy_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_custom_ticket(interaction, "🛒│kauf", "Kauf-Anfrage")

    @discord.ui.button(
        label="Allgemeiner Support",
        style=discord.ButtonStyle.primary,
        emoji="⚙️",
        custom_id="btn_support_ticket",
    )
    async def support_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_custom_ticket(interaction, "⚙️│support", "Allgemeiner Support")

    @discord.ui.button(
        label="Partnerschaft",
        style=discord.ButtonStyle.secondary,
        emoji="🤝",
        custom_id="btn_partner_ticket",
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
        co_owner_role = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿")
        admin_role = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻")
        manager_role = discord.utils.get(guild.roles, name="⚙️│ 𝗩𝗢𝗜𝗗 • Manager")
        mod_role = discord.utils.get(guild.roles, name="🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿")
        support_role = discord.utils.get(guild.roles, name="🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁")

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

        category = discord.utils.get(guild.categories, name="🎟️│── 𝗩𝗢𝗜𝗗 • 𝗦𝗨𝗣𝗣𝗢𝗥𝗧 ──")

        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"{ticket_type} von {member.name}",
            )

            if ticket_type == "Kauf-Anfrage":
                description = (
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"👋 **Herzlich willkommen, {member.mention}!**\n\n"
                    "> Vielen Dank für dein Interesse an den Produkten von **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**.\n"
                    "> Unser Team wurde benachrichtigt und ist gleich für dich da!\n\n"
                    "📌 **Bitte teile uns direkt folgende Infos mit:**\n"
                    "> 🤖 │ **Roblox Username:**\n"
                    "> 🛍️ │ **Gewünschtes Produkt:** *(z.B. FastFlags, T-Shirt, Template)*\n"
                    "> 💳 │ **Zahlungsart:** *(PayPal, Robux, Paysafecard, Krypto)*\n\n"
                    "⏳ *Ein Teammitglied wird dein Ticket unten über 'Claimen' übernehmen.*"
                )
                color = 0x39FF14
            elif ticket_type == "Allgemeiner Support":
                description = (
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"👋 **Herzlich willkommen, {member.mention}!**\n\n"
                    "> Du benötigst technische Hilfe oder hast Fragen zu unserem Shop?\n"
                    "> Bitte schildere dein Problem so genau wie möglich!\n\n"
                    "📌 **Häufige Themen:**\n"
                    "> 🚀 │ Installation & Nutzung der FastFlags\n"
                    "> ⚙️ │ Hilfe bei Discord Server-Layouts & Rechten\n\n"
                    "⏳ *Ein Supporter widmet sich dir in Kürze.*"
                )
                color = 0x00F0FF
            else:
                description = (
                    "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"🤝 **Partnerschafts-Anfrage von {member.mention}**\n\n"
                    "> Schön, dass du mit **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** kooperieren möchtest!\n\n"
                    "📌 **Bitte nenne uns kurz deine Eckdaten:**\n"
                    "> 🔗 │ **Thema deines Servers:**\n"
                    "> 👥 │ **Mitgliederanzahl:**\n"
                    "> 📍 │ **Dauerhafter Einladungslink:**\n\n"
                    "⏳ *Die Projektleitung wird sich dein Angebot ansehen.*"
                )
                color = 0xFFA500

            embed = EmbedHelper.create_prestige_embed(
                title=f"⚡ 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • {ticket_type.upper()} ⚡",
                description=description,
                color=color,
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
                        f"> **Ersteller:** {member.mention} ({member.id})"
                    ),
                    color=0x39FF14,
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
