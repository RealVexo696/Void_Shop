import os
import asyncio
import logging
import io
import threading
import aiohttp
import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
from flask import Flask

# --- FLASK SERVER (FÜR 24/7 RAILWAY WEB SERVICE ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 Bot ist Online!</h1><p>Running 24/7 on Railway.</p>"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()
    print("[Flask] Webserver gestartet.")


# --- CONFIG LOGGER ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger('void_shop_bot')

# ==============================================================================
#                                KONFIGURATION
# ==============================================================================
# Trage hier direkt deinen Discord Bot-Token ein!
TOKEN = "MTUyMDE3MDg0MTQ2NjQ3MDUyMQ.GbIcAF.OBOLoyO8IKC3sbfr1oVuWEMwAw4PphQXy4RCWQ"  

# Der Prefix für deine Befehle (Standard ist !)
PREFIX = "!"
# ==============================================================================


# --- GLOBAL EMBED FACTORY ---

def create_prestige_embed(title: str, description: str, color: int, author_user: discord.User = None, bot_user: discord.ClientUser = None):
    """
    Erstellt ein hochgradig einheitliches, luxuriöses Embed:
    - Author: Immer der ausführende User (Name + Avatar-Icon)
    - Footer: Immer Bot-Icon + "Powered by BotForge" + Zeitstempel
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=discord.utils.utcnow()
    )
    if author_user:
        embed.set_author(
            name=author_user.name, 
            icon_url=author_user.display_avatar.url if author_user.display_avatar else None
        )
    if bot_user:
        embed.set_footer(
            text="Powered by BotForge", 
            icon_url=bot_user.display_avatar.url if bot_user.display_avatar else None
        )
    return embed


# --- ROBLOX API HELPERS ---

async def get_roblox_user(username: str):
    """Sucht einen Roblox-User und gibt ID, Display-Name und System-Name zurück."""
    url = f"https://users.roblox.com/v1/users/search?keyword={username}&limit=1"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("data"):
                        user_data = data["data"][0]
                        return user_data["id"], user_data["displayName"], user_data["name"]
        except Exception as e:
            logger.error(f"Roblox User API Fehler: {e}")
    return None, None, None

async def get_roblox_avatar(user_id: int):
    """Sucht den Kopfschuss-Avatar eines Roblox-Users."""
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png&isCircular=false"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r:
                if r.status == 200:
                    data = await r.json()
                    if data.get("data"):
                        return data["data"][0]["imageUrl"]
        except Exception as e:
            logger.error(f"Roblox Avatar API Fehler: {e}")
    return None

async def check_roblox_ownership(user_id: int, gamepass_id: int):
    """Prüft live über die Roblox API, ob ein User einen bestimmten Gamepass besitzt."""
    url = f"https://inventory.roblox.com/v1/users/{user_id}/items/GamePass/{gamepass_id}/is-owned"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as r:
                if r.status == 200:
                    text = await r.text()
                    return text.strip().lower() == "true"
        except Exception as e:
            logger.error(f"Roblox Ownership API Fehler: {e}")
    return False


# --- REALTIME STATS CHANNELS UPDATE HELPER ---

async def update_stats_channels(guild):
    """Aktualisiert sofort und in Echtzeit die Namen der Server-Statistik Kanäle."""
    member_count = len(guild.members)
    booster_count = guild.premium_subscription_count
    
    customer_role = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿")
    customer_count = len(customer_role.members) if customer_role else 0

    for vc in guild.voice_channels:
        try:
            if vc.name.startswith("👥│Mitglieder:"):
                await vc.edit(name=f"👥│Mitglieder: {member_count}")
            elif vc.name.startswith("💎│Booster:"):
                await vc.edit(name=f"💎│Booster: {booster_count}")
            elif vc.name.startswith("🛒│Kunden:"):
                await vc.edit(name=f"🛒│Kunden: {customer_count}")
        except discord.Forbidden:
            logger.warning(f"Keine Berechtigung zum Bearbeiten des Stats-Kanals {vc.name}.")
        except Exception as e:
            logger.error(f"Fehler bei Stats-Kanal Edit: {e}")


# --- ROBLOX VERIFIZIERUNGS BUTTONS ---

class RobloxVerifyView(discord.ui.View):
    """Zwei-Knopf-Abfrage zur Bestätigung des Roblox Accounts."""
    def __init__(self, roblox_id, roblox_name, roblox_display):
        super().__init__(timeout=60)
        self.roblox_id = roblox_id
        self.roblox_name = roblox_name
        self.roblox_display = roblox_display

    @discord.ui.button(label="Ja, das bin ich ✅", style=discord.ButtonStyle.success, custom_id="verify_yes")
    async def confirm_yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        verified_role = discord.utils.get(guild.roles, name="👤│ 𝗩𝗢𝗜𝗗 • 𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱")
        
        try:
            if verified_role:
                await member.add_roles(verified_role)
            await member.edit(nick=self.roblox_name)

            success_embed = create_prestige_embed(
                title="⚡ Roblox-Verifizierung erfolgreich!",
                description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                            f"> 🎉 Herzlichen Glückwunsch, {member.mention}!\n\n"
                            f"Du hast dich erfolgreich als **{self.roblox_name}** verifiziert.\n"
                            f"> **Roblox-ID:** `{self.roblox_id}`\n"
                            f"> **Display-Name:** `{self.roblox_display}`\n\n"
                            f"Deine Serverrolle wurde aktualisiert und dein Nickname angepasst.",
                color=0x39ff14,
                author_user=member,
                bot_user=interaction.client.user
            )
            
            avatar_url = await get_roblox_avatar(self.roblox_id)
            if avatar_url:
                success_embed.set_thumbnail(url=avatar_url)

            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            self.stop()

            # Live Stats aktualisieren
            await update_stats_channels(guild)

            log_channel = discord.utils.get(guild.text_channels, name="⚙️│system-logs")
            if log_channel:
                log_embed = create_prestige_embed(
                    title="👤 Mitglied verifiziert",
                    description=f"> **User:** {member.mention} ({member.name})\n"
                                f"> **Roblox:** [{self.roblox_name}](https://www.roblox.com/users/{self.roblox_id}/profile)\n"
                                f"> **Roblox-ID:** `{self.roblox_id}`",
                    color=0x39ff14,
                    author_user=member,
                    bot_user=interaction.client.user
                )
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Fehler: Mir fehlen die Rechte, um deine Rolle zu vergeben oder deinen Nickname zu ändern. Stelle sicher, dass meine Rolle in den Server-Einstellungen ganz oben steht!",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Fehler bei Verifizierungs-Abschluss: {e}")
            await interaction.response.send_message("❌ Es ist ein interner Fehler aufgetreten.", ephemeral=True)

    @discord.ui.button(label="Nein, abbrechen ❌", style=discord.ButtonStyle.danger, custom_id="verify_no")
    async def confirm_no(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_prestige_embed(
            title="❌ Verifizierung abgebrochen",
            description="> Der Vorgang wurde abgebrochen. Bitte starte die Verifizierung erneut mit dem richtigen Namen.",
            color=0xff003c,
            author_user=interaction.user,
            bot_user=interaction.client.user
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        self.stop()


# --- INTERAKTIVES TICKET-SYSTEM MODALS (ADD/REMOVE USER) ---

class AddUserModal(discord.ui.Modal, title="User zum Ticket hinzufügen"):
    user_input = discord.ui.TextInput(
        label="User-ID oder Username", 
        placeholder="z.B. 123456789012345678 oder name", 
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel = interaction.channel
        
        user_str = self.user_input.value
        user = None
        
        # Suchen per ID
        if user_str.isdigit():
            user = guild.get_member(int(user_str))
            if not user:
                try:
                    user = await guild.fetch_member(int(user_str))
                except Exception:
                    pass
        # Suchen per Name
        if not user:
            user = discord.utils.get(guild.members, name=user_str)
            
        if not user:
            await interaction.response.send_message(f"❌ User '{user_str}' wurde auf diesem Server nicht gefunden!", ephemeral=True)
            return
            
        try:
            await channel.set_permissions(user, view_channel=True, send_messages=True, read_message_history=True)
            embed = create_prestige_embed(
                title="➕ User hinzugefügt",
                description=f"> {interaction.user.mention} hat {user.mention} zum Ticket hinzugefügt.",
                color=0x39ff14,
                author_user=interaction.user,
                bot_user=interaction.client.user
            )
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ {user.name} wurde erfolgreich hinzugefügt!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Fehler beim Hinzufügen: {e}", ephemeral=True)


class RemoveUserModal(discord.ui.Modal, title="User aus Ticket entfernen"):
    user_input = discord.ui.TextInput(
        label="User-ID oder Username", 
        placeholder="z.B. 123456789012345678", 
        required=True
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
            await interaction.response.send_message(f"❌ User '{user_str}' wurde nicht gefunden!", ephemeral=True)
            return
            
        try:
            await channel.set_permissions(user, overwrite=None)
            embed = create_prestige_embed(
                title="➖ User entfernt",
                description=f"> {interaction.user.mention} hat {user.mention} aus dem Ticket entfernt.",
                color=0xff003c,
                author_user=interaction.user,
                bot_user=interaction.client.user
            )
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ {user.name} wurde erfolgreich entfernt!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Fehler beim Entfernen: {e}", ephemeral=True)


# --- PERSISTENTE TICKET-ANSICHTEN (TICKET SYSTEM) ---

class CloseTicketView(discord.ui.View):
    """View für die Ticket-Steuerung im Ticket-Kanal."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ticket claimen", 
        style=discord.ButtonStyle.primary, 
        emoji="🙋‍♂️", 
        custom_id="claim_ticket_btn"
    )
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = interaction.channel
        member = interaction.user

        support_role = discord.utils.get(guild.roles, name="🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁")
        mod_role = discord.utils.get(guild.roles, name="🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿")
        admin_role = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻")
        owner_role = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿")

        has_staff_role = any(role in [support_role, mod_role, admin_role, owner_role] for role in member.roles)
        if not has_staff_role and not member.guild_permissions.administrator:
            await interaction.response.send_message("❌ Du gehörst nicht zum Support-Team!", ephemeral=True)
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
                member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
            }

            if ticket_creator:
                overwrites[ticket_creator] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

            for role in [support_role, mod_role, admin_role, owner_role]:
                if role and role != guild.default_role:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)

            await channel.edit(overwrites=overwrites)

            claim_embed = create_prestige_embed(
                title="🙋‍♂️ Ticket geclaimed!",
                description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"> Dieses Ticket wird nun exklusiv von {member.mention} betreut.\n"
                    f"> Bitte richte alle weiteren Fragen direkt an deinen zuständigen Supporter.",
                color=0x00f0ff,
                author_user=member,
                bot_user=interaction.client.user
            )
            await channel.send(embed=claim_embed)
            await interaction.response.edit_message(view=self)

            ticket_logs_channel = discord.utils.get(guild.text_channels, name="💾│ticket-logs")
            if ticket_logs_channel:
                log_claim = create_prestige_embed(
                    title="🙋‍♂️ Ticket geclaimed",
                    description=f"> **Kanal:** {channel.mention}\n"
                                f"> **Supporter:** {member.mention} ({member.id})",
                    color=0x00f0ff,
                    author_user=member,
                    bot_user=interaction.client.user
                )
                await ticket_logs_channel.send(embed=log_claim)

        except Exception as e:
            logger.error(f"Fehler beim Claimen des Tickets: {e}")
            await interaction.response.send_message("❌ Fehler beim Aktualisieren der Ticketrechte.", ephemeral=True)

    @discord.ui.button(
        label="User hinzufügen", 
        style=discord.ButtonStyle.success, 
        emoji="➕", 
        custom_id="add_user_ticket_btn"
    )
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AddUserModal())

    @discord.ui.button(
        label="User entfernen", 
        style=discord.ButtonStyle.secondary, 
        emoji="➖", 
        custom_id="remove_user_ticket_btn"
    )
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RemoveUserModal())

    @discord.ui.button(
        label="Ticket schließen", 
        style=discord.ButtonStyle.red, 
        emoji="🔒", 
        custom_id="close_ticket_btn"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        guild = interaction.guild
        channel = interaction.channel

        embed_closing = create_prestige_embed(
            title="🔒 Ticket-Schließung",
            description="> ⚠️ Dieses Ticket wird geschlossen, transkribiert und in **5 Sekunden** gelöscht...",
            color=0xff003c,
            author_user=interaction.user,
            bot_user=interaction.client.user
        )
        await channel.send(embed=embed_closing)
        await asyncio.sleep(5)

        # 📄 AUTOMATISCHER TICKET-TRANSCRIPT-BUILDER
        try:
            messages = []
            async for msg in channel.history(limit=1000, oldest_first=True):
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                author = f"{msg.author.name}#{msg.author.discriminator}" if msg.author.discriminator != "0" else msg.author.name
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
                f"==================================================\n"
                f"         𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 - TICKET TRANSKRIPT             \n"
                f"==================================================\n"
                f"Kanalname:     {channel.name}\n"
                f"Geschlossen:   {interaction.user.name} ({interaction.user.id})\n"
                f"Nachrichten:   {len(messages)}\n"
                f"==================================================\n\n"
                + "\n".join(messages)
            )

            ticket_logs_channel = discord.utils.get(guild.text_channels, name="💾│ticket-logs")
            if ticket_logs_channel:
                file_data = io.BytesIO(transcript_content.encode("utf-8"))
                discord_file = discord.File(file_data, filename=f"transcript-{channel.name}.txt")
                
                embed_log = create_prestige_embed(
                    title="💾 Ticket-Transkript archiviert",
                    description=f"> **Ticket:** {channel.name}\n"
                                f"> **Mitarbeiter:** {interaction.user.mention}\n"
                                f"> Das vollständige Protokoll wurde erfolgreich als Textdatei gesichert.",
                    color=0xff003c,
                    author_user=interaction.user,
                    bot_user=interaction.client.user
                )
                await ticket_logs_channel.send(embed=embed_log, file=discord_file)
                
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Ticket-Transkripts: {e}")

        try:
            await channel.delete()
        except discord.Forbidden:
            logger.error(f"Fehler: Keine Berechtigung zum Löschen des Kanals {channel.name}.")
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Ticket-Kanals: {e}")


class TicketButton(discord.ui.View):
    """View für das Ticket-Erstellungs-Panel mit Kauf, Support und Partner-Buttons."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Produkt kaufen", 
        style=discord.ButtonStyle.success, 
        emoji="🛒", 
        custom_id="btn_buy_ticket"
    )
    async def buy_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_custom_ticket(interaction, "🛒│kauf", "Kauf-Anfrage")

    @discord.ui.button(
        label="Allgemeiner Support", 
        style=discord.ButtonStyle.primary, 
        emoji="⚙️", 
        custom_id="btn_support_ticket"
    )
    async def support_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_custom_ticket(interaction, "⚙️│support", "Allgemeiner Support")

    @discord.ui.button(
        label="Partnerschaft", 
        style=discord.ButtonStyle.secondary, 
        emoji="🤝", 
        custom_id="btn_partner_ticket"
    )
    async def partner_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_custom_ticket(interaction, "🤝│partner", "Partnerschafts-Anfrage")

    async def create_custom_ticket(self, interaction: discord.Interaction, prefix: str, ticket_type: str):
        guild = interaction.guild
        member = interaction.user

        if not guild:
            await interaction.response.send_message("Dieser Befehl kann nur auf einem Server genutzt werden.", ephemeral=True)
            return

        ticket_channel_name = f"{prefix}-{member.name.lower()}"

        existing_channel = discord.utils.get(guild.channels, name=ticket_channel_name)
        if existing_channel:
            await interaction.response.send_message(
                f"❌ Du hast bereits ein offenes Ticket für diesen Bereich: {existing_channel.mention}", 
                ephemeral=True
            )
            return

        owner_role = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿")
        co_owner_role = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿")
        admin_role = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻")
        manager_role = discord.utils.get(guild.roles, name="⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿")
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
                read_message_history=True
            )
        }

        for role in [owner_role, co_owner_role, admin_role, manager_role, mod_role, support_role]:
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        category = discord.utils.get(guild.categories, name="🎟️│── 𝗩𝗢𝗜𝗗 • 𝗦𝗨𝗣𝗣𝗢𝗥𝗧 ──")

        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"{ticket_type} von {member.name}"
            )

            if ticket_type == "Kauf-Anfrage":
                description = (
                    f"Hallo {member.mention},\n\nvielen Dank, dass du ein Ticket bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** geöffnet hast!\nUnser Support-Team wird sich in Kürze um dich kümmern.\n\n"
                    f"**Bitte bereite bereits folgende Informationen vor:**\n"
                    f"> 🤖 │ **Roblox Username:**\n"
                    f"> 📦 │ **Gewünschte Produkte:** (z.B. T-Shirt Vorlagen, Premium FastFlags)\n"
                    f"> 💳 │ **Zahlungsmethode:** (PayPal, Robux, Paysafecard, Krypto)\n\n"
                    f"*Mitarbeiter können das Ticket über den Knopf unten 'claimen'.*"
                )
                color = 0x39ff14
            elif ticket_type == "Allgemeiner Support":
                description = (
                    f"Hallo {member.mention},\n\nvielen Dank für deine Anfrage!\n"
                    f"Beschreibe dein Anliegen bitte so detailliert wie möglich.\n\n"
                    f"**Beispiele für Support-Anfragen:**\n"
                    f"> ⚙️ │ Fragen zur Aktivierung der FastFlags\n"
                    f"> 🖥️ │ Technische Probleme mit Discord-Vorlagen\n\n"
                    f"*Mitarbeiter können das Ticket unten claimen.*"
                )
                color = 0x00f0ff
            else:
                description = (
                    f"Hallo {member.mention},\n\nvielen Dank für deine Partnerschafts-Anfrage!\n"
                    f"Bitte lade deinen Einladungslink hoch und nenne uns einige Eckdaten.\n\n"
                    f"**Eckdaten für Partnerschaften:**\n"
                    f"> 🔗 │ Server-Thema / Nische\n"
                    f"> 👥 │ Aktuelle Mitgliederanzahl\n"
                    f"> 📍 │ Unendlicher Einladungslink deines Servers\n\n"
                    f"*Mitarbeiter können dieses Ticket unten annehmen.*"
                )
                color = 0xffa500

            embed = create_prestige_embed(
                title=f"⚡ 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • {ticket_type.upper()} ⚡",
                description=description,
                color=color,
                author_user=member,
                bot_user=interaction.client.user
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

            staff_pings = []
            for role in [owner_role, co_owner_role, admin_role, support_role]:
                if role: staff_pings.append(role.mention)
            pings_str = " ".join(staff_pings) if staff_pings else ""

            await ticket_channel.send(
                content=f"{member.mention} {pings_str}", 
                embed=embed, 
                view=CloseTicketView()
            )

            await interaction.response.send_message(
                f"✅ Dein Ticket wurde erfolgreich erstellt: {ticket_channel.mention}", 
                ephemeral=True
            )

            ticket_logs_channel = discord.utils.get(guild.text_channels, name="💾│ticket-logs")
            if ticket_logs_channel:
                embed_created = create_prestige_embed(
                    title="🎟️ Ticket erstellt",
                    description=f"> **Kanal:** {ticket_channel.mention}\n"
                                f"> **Typ:** {ticket_type}\n"
                                f"> **Ersteller:** {member.mention} ({member.id})",
                    color=0x39ff14,
                    author_user=member,
                    bot_user=interaction.client.user
                )
                await ticket_logs_channel.send(embed=embed_created)

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Ticket-Kanals: {e}")
            await interaction.response.send_message(
                "❌ Fehler beim Erstellen des Tickets. Bitte wende dich an einen Administrator.", 
                ephemeral=True
            )


# --- PERSISTENTER VERIFIZIERUNGS BUTTON (EINTRETEN VERIFIZIERUNG) ---

class SimpleVerifyButton(discord.ui.View):
    """View für die 1-Klick-Verifizierung im Server."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verifizieren 🔐", 
        style=discord.ButtonStyle.success, 
        emoji="🔐", 
        custom_id="simple_verify_btn"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        
        member_role = discord.utils.get(guild.roles, name="👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿")
        if not member_role:
            await interaction.response.send_message("❌ Fehler: Die Mitgliederrolle wurde nicht gefunden!", ephemeral=True)
            return

        if member_role in member.roles:
            await interaction.response.send_message("ℹ️ Du bist bereits verifiziert!", ephemeral=True)
            return

        try:
            await member.add_roles(member_role)
            await interaction.response.send_message("✅ Du hast dich erfolgreich verifiziert und die Mitglieder-Rolle erhalten!", ephemeral=True)
            
            log_channel = discord.utils.get(guild.text_channels, name="⚙️│system-logs")
            if log_channel:
                embed = create_prestige_embed(
                    title="🔐 Mitglied verifiziert (1-Klick)",
                    description=f"> **User:** {member.mention} ({member.name})\n"
                                f"> Hat die Verifizierung per Knopfdruck abgeschlossen.",
                    color=0x39ff14,
                    author_user=member,
                    bot_user=interaction.client.user
                )
                await log_channel.send(embed=embed)
                
            # Echtzeit Stats-Update
            await update_stats_channels(guild)

        except discord.Forbidden:
            await interaction.response.send_message("❌ Fehler: Mir fehlen die Rechte, um dir die Rolle zu geben. Bitte wende dich an einen Admin!", ephemeral=True)


# --- BOT KLASSE ---

class VoidShopBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.invites = True
        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.invites_cache = {}

    async def setup_hook(self):
        self.add_view(TicketButton())
        self.add_view(CloseTicketView())
        self.add_view(SimpleVerifyButton())
        
        # Starte den Stats-Update-Loop (hier läuft die Event-Loop garantiert!)
        if not update_stats_task.is_running():
            update_stats_task.start()
            
        logger.info("Persistente UI-Views und Stats-Loop geladen.")

    async def on_ready(self):
        activity = discord.Activity(
            type=discord.ActivityType.watching, 
            name="über 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 | !Start"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
        
        # Cache Invites für Invite-Tracking
        for guild in self.guilds:
            try:
                self.invites_cache[guild.id] = await guild.invites()
                # Aktualisiere Statistiken beim Botstart sofort
                await update_stats_channels(guild)
            except Exception:
                pass

        logger.info(f"============= 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 PRESTIGE BOT ONLINE =============")
        logger.info(f"Eingeloggt als: {self.user.name} ({self.user.id})")
        logger.info(f"Webserver läuft auf Port: {os.environ.get('PORT', 8080)}")
        logger.info(f"======================================================")


bot = VoidShopBot()


# --- STATS-LOOP TASK (24/7 LIVE STATS COUNTER) ---

@tasks.loop(minutes=10)
async def update_stats_task():
    """Backup-Loop: Aktualisiert alle 10 Minuten die Namen der Server-Statistik Kanäle."""
    logger.info("Führe Backup-Aktualisierung der Server-Statistiken durch...")
    for guild in bot.guilds:
        await update_stats_channels(guild)


# --- VERIFY & CHECKBUY COMMANDS (REAL ROBLOX API INTEGRATION) ---

@bot.command(name="verify", aliases=["verify-roblox", "Verify"])
@commands.guild_only()
async def verify_command(ctx, roblox_username: str = None):
    """
    Verifiziert ein Discord-Mitglied mit seinem Roblox-Account.
    Sucht live über die Roblox API, fragt nach Bestätigung und ändert Nickname + Rolle.
    """
    if not roblox_username:
        embed_help = create_prestige_embed(
            title="💡 Roblox Verifizierung",
            description="> Bitte gib deinen Roblox Usernamen an!\n\n**Beispiel:**\n`!verify Lukas_Roblox`",
            color=0xff003c,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await ctx.send(embed=embed_help)
        return

    progress_embed = create_prestige_embed(
        title="🔍 Suche Roblox-Konto...",
        description=f"> Kontaktiere die Roblox Server für **'{roblox_username}'**...",
        color=0x00f0ff,
        author_user=ctx.author,
        bot_user=bot.user
    )
    status_msg = await ctx.send(embed=progress_embed)

    roblox_id, roblox_display, roblox_name = await get_roblox_user(roblox_username)

    if not roblox_id:
        embed_err = create_prestige_embed(
            title="❌ Konto nicht gefunden",
            description=f"> Der Roblox Username **'{roblox_username}'** existiert nicht!\nBitte überprüfe die Schreibweise.",
            color=0xff003c,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await status_msg.edit(embed=embed_err)
        return

    avatar_url = await get_roblox_avatar(roblox_id)

    confirm_embed = create_prestige_embed(
        title="🤖 Roblox-Account Bestätigung",
        description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                    f"> **Bist du das wirklich?**\n\n"
                    f"Bitte bestätige, ob dies dein echter Roblox-Account ist:\n"
                    f"> **Roblox-Name:** {roblox_name}\n"
                    f"> **Display-Name:** {roblox_display}\n"
                    f"> **Roblox-ID:** `{roblox_id}`\n\n"
                    f"Klicke auf den passenden Knopf unten, um den Vorgang abzuschließen.",
        color=0xffd700,
        author_user=ctx.author,
        bot_user=bot.user
    )
    if avatar_url:
        confirm_embed.set_thumbnail(url=avatar_url)

    view = RobloxVerifyView(roblox_id, roblox_name, roblox_display)
    await status_msg.edit(embed=confirm_embed, view=view)


@bot.command(name="checkbuy", aliases=["Checkbuy", "kaufprüfen"])
@commands.guild_only()
async def checkbuy_command(ctx, roblox_username: str = None, gamepass_id: int = None):
    """
    Prüft live über die Roblox Inventory API, ob der User den angegebenen Gamepass besitzt.
    Wenn ja, schaltet er automatisch die Customer-Rollen frei!
    """
    if not roblox_username or not gamepass_id:
        embed_help = create_prestige_embed(
            title="🛒 Automatische Kaufprüfung",
            description="> Prüfe live deinen Einkauf über Roblox und erhalte deine Rollen!\n\n"
                        "**Nutzung:**\n"
                        f"`!checkbuy <Roblox_Username> <Gamepass_ID>`\n\n"
                        f"**Beispiel:**\n"
                        f"`!checkbuy Lukas_Roblox 12345678`",
            color=0x00f0ff,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await ctx.send(embed=embed_help)
        return

    progress_embed = create_prestige_embed(
        title="🔄 Überprüfe Roblox Inventar...",
        description=f"> Suche Roblox-Konto **'{roblox_username}'** und überprüfe den Besitz von Gamepass `{gamepass_id}`...",
        color=0xffd700,
        author_user=ctx.author,
        bot_user=bot.user
    )
    status_msg = await ctx.send(embed=progress_embed)

    roblox_id, roblox_display, roblox_name = await get_roblox_user(roblox_username)
    if not roblox_id:
        embed_err = create_prestige_embed(
            title="❌ Roblox Konto nicht gefunden",
            description=f"> Der Username **'{roblox_username}'** wurde auf Roblox nicht gefunden.",
            color=0xff003c,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await status_msg.edit(embed=embed_err)
        return

    has_purchased = await check_roblox_ownership(roblox_id, gamepass_id)

    if has_purchased:
        guild = ctx.guild
        member = ctx.author

        customer_role = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿")
        premium_buyer_role = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿")

        added_roles = []
        try:
            if customer_role:
                await member.add_roles(customer_role)
                added_roles.append(customer_role.name)
            if premium_buyer_role:
                await member.add_roles(premium_buyer_role)
                added_roles.append(premium_buyer_role.name)

            success_embed = create_prestige_embed(
                title="🎉 Kauf verifiziert & Rollen vergeben!",
                description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                            f"> ✨ **Besitz verifiziert!**\n\n"
                            f"Du besitzt den Roblox Gamepass `{gamepass_id}`.\n"
                            f"Folgende Premium-Käuferrollen wurden dir freigeschaltet:\n"
                            f"> 👑 │ " + " & ".join([f"**{r}**" for r in added_roles]) + "\n\n"
                            f"Vielen Dank für deinen Einkauf bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**! Du hast ab jetzt Zugriff auf die exklusiven Lounges.",
                color=0x39ff14,
                author_user=member,
                bot_user=bot.user
            )
            avatar_url = await get_roblox_avatar(roblox_id)
            if avatar_url:
                success_embed.set_thumbnail(url=avatar_url)
            
            await status_msg.edit(embed=success_embed)

            # Echtzeit Stats-Update
            await update_stats_channels(guild)

            log_channel = discord.utils.get(guild.text_channels, name="⚙️│system-logs")
            if log_channel:
                log_embed = create_prestige_embed(
                    title="🛒 Automatische Kaufverifizierung",
                    description=f"> **User:** {member.mention} ({member.name})\n"
                                f"> **Roblox:** {roblox_name} ({roblox_id})\n"
                                f"> **Gamepass:** `{gamepass_id}`\n"
                                f"> **Rollen erhalten:** " + ", ".join(added_roles),
                    color=0x39ff14,
                    author_user=member,
                    bot_user=bot.user
                )
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await status_msg.edit(content="❌ Fehler: Dem Bot fehlen die Rechte zum Vergeben der Rollen. Stelle sicher, dass die Bot-Rolle ganz oben steht!")
    else:
        embed_fail = create_prestige_embed(
            title="❌ Verifizierung fehlgeschlagen",
            description=f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                        f"> 🔒 **Kauf wurde nicht gefunden.**\n\n"
                        f"Roblox-User **{roblox_name}** besitzt den Gamepass `{gamepass_id}` aktuell nicht.\n"
                        f"> Bitte stelle sicher, dass du den Gamepass mit diesem Account gekauft hast und dein Roblox Inventar öffentlich einsehbar ist!",
            color=0xff003c,
            author_user=ctx.author,
            bot_user=bot.user
        )
        avatar_url = await get_roblox_avatar(roblox_id)
        if avatar_url:
            embed_fail.set_thumbnail(url=avatar_url)
        await status_msg.edit(embed=embed_fail)


# --- ROLES SETUP COMMAND (!role) ---

@bot.command(name="role", aliases=["roles", "Role", "Roles"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def create_roles_command(ctx):
    """
    Erstellt alle 23 Premium-Rollen, prüft ob sie bereits existieren,
    und setzt im Anschluss alle Kanalrechte für diese Rollen.
    Inklusive dynamic-permissions Schutz.
    """
    progress_embed = create_prestige_embed(
        title="👑 Rollen- & Berechtigungs-Setup",
        description="> ⚙️ Initialisiere das Erstellen von 23 Premium-Rollen...\nBitte warten.",
        color=0x00f0ff,
        author_user=ctx.author,
        bot_user=bot.user
    )
    status_msg = await ctx.send(embed=progress_embed)

    guild = ctx.guild
    bot_member = guild.me
    bot_permissions = bot_member.guild_permissions

    role_colors = {
        # --- STAFF ROLES ---
        "👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿": (0xff003c, True),        # Crimson Red
        "👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿": (0xff3366, True),     # Light Pink-Red
        "🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻": (0x00f0ff, True),        # Neon Cyan
        "⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿": (0x00a8a8, True),      # Dark Teal
        "🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿": (0x39ff14, False),    # Neon Green
        "🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁": (0x20b2aa, False),      # Light Sea Green
        "🚨│ 𝗩𝗢𝗜𝗗 • 𝗧𝗿𝗶𝗮𝗹 𝗠𝗼𝗱": (0xadff2f, False),    # Green Yellow
        
        # --- SPECIAL ROLES ---
        "🤝│ 𝗩𝗢𝗜𝗗 • 𝗣𝗮𝗿𝘁𝗻𝗲𝗿": (0xffa500, False),      # Orange
        "💎│ 𝗩𝗢𝗜𝗗 • 𝗕𝗼𝗼𝘀𝘁𝗲𝗿": (0xf47fff, False),      # Pink
        "🌟│ 𝗩𝗢𝗜𝗗 • 𝗩𝗜𝗣": (0xffd700, False),          # Gold (VIP)
        "🫂│ 𝗩𝗢𝗜𝗗 • 𝗙𝗿𝗶𝗲𝗻𝗱": (0xff69b4, False),        # Hot Pink
        "👤│ 𝗩𝗢𝗜𝗗 • 𝗩𝗲𝗿𝗶𝗳𝗶𝗲𝗱": (0x7f8c8d, False),      # Gray-Blue (Verified)
        
        # --- CUSTOMER ROLES ---
        "🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿": (0xffff00, False),     # Yellow
        "💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿": (0x00ffff, False), # Cyan Customer
        
        # --- REWARD ROLES (BUYER LEVELS) ---
        "🥉│ 𝗕𝗿𝗼𝗻𝘇𝗲 𝗕𝘂𝘆𝗲𝗿": (0xcd7f32, False),       # Bronze
        "🥈│ 𝗦𝗶𝗹𝘃𝗲𝗿 𝗕𝘂𝘆𝗲𝗿": (0xc0c0c0, False),       # Silver
        "🥇│ 𝗚𝗼𝗹𝗱 𝗕𝘂𝘆𝗲𝗿": (0xffd700, False),         # Gold
        "💎│ 𝗗𝗶𝗮𝗺𝗼𝗻𝗱 𝗕𝘂𝘆𝗲𝗿": (0xb9f2ff, False),       # Diamond
        
        # --- NOTIFICATION ROLES ---
        "📢│ 𝗔𝗻𝗻𝗼𝘂𝗻𝗰𝗲𝗺𝗲𝗻𝘁 𝗣𝗶𝗻𝗴": (0x7289da, False),  # Discord Blue
        "🎁│ 𝗚𝗶𝘃𝗲𝗮𝘄𝗮𝘆 𝗣𝗶𝗻𝗴": (0xff4500, False),      # Red-Orange
        "📦│ 𝗣𝗿𝗼𝗱𝘂𝗰𝘁 𝗣𝗶𝗻𝗴": (0x32cd32, False),       # Lime Green
        
        # --- BASE ROLES ---
        "👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿": (0xa0a0a0, False),       # Light Gray
        "🤖│ 𝗩𝗢𝗜𝗗 • 𝗕𝗼𝘁": (0x4a00a8, False)           # Dark Purple
    }

    created_roles = {}
    roles_created_count = 0
    roles_skipped_count = 0
    roles_failed_count = 0

    for role_name, (color_hex, is_admin) in role_colors.items():
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            created_roles[role_name] = existing_role
            roles_skipped_count += 1
            continue

        try:
            perms = discord.Permissions.none()
            if is_admin and bot_permissions.administrator:
                perms.administrator = True
            elif "Moderator" in role_name or "Manager" in role_name:
                requested_perms = [
                    ("view_channel", True), ("send_messages", True), ("manage_messages", True),
                    ("kick_members", True), ("ban_members", True), ("mute_members", True),
                    ("deafen_members", True), ("move_members", True), ("change_nickname", True),
                    ("read_message_history", True), ("attach_files", True), ("embed_links", True),
                    ("add_reactions", True), ("use_external_emojis", True)
                ]
                for perm_name, req_val in requested_perms:
                    if getattr(bot_permissions, perm_name, False):
                        setattr(perms, perm_name, True)
            else:
                requested_perms = [
                    ("view_channel", True), ("send_messages", True), ("read_message_history", True),
                    ("attach_files", True), ("embed_links", True), ("add_reactions", True),
                    ("use_external_emojis", True), ("change_nickname", True)
                ]
                for perm_name, req_val in requested_perms:
                    if getattr(bot_permissions, perm_name, False):
                        setattr(perms, perm_name, True)

            new_role = await guild.create_role(
                name=role_name,
                color=discord.Color(color_hex),
                permissions=perms,
                hoist=True,
                mentionable=True
            )
            created_roles[role_name] = new_role
            roles_created_count += 1
            await asyncio.sleep(0.15)
        except discord.Forbidden:
            try:
                new_role = await guild.create_role(
                    name=role_name,
                    color=discord.Color(color_hex),
                    permissions=discord.Permissions.default(),
                    hoist=True,
                    mentionable=True
                )
                created_roles[role_name] = new_role
                roles_created_count += 1
                await asyncio.sleep(0.15)
            except discord.Forbidden:
                roles_failed_count += 1
                logger.error(f"Konnte Rolle {role_name} überhaupt nicht erstellen.")
        except Exception as e:
            roles_failed_count += 1
            logger.error(f"Fehler bei {role_name}: {e}")

    if roles_failed_count > 0 and roles_created_count == 0 and roles_skipped_count == 0:
        embed_warning = create_prestige_embed(
            title="⚠️ FEHLER: Keine Rollen erstellt!",
            description=f"> Es konnte **keine einzige Rolle** erstellt werden!\n\n"
                        f"**Ursache:**\n"
                        f"Dem Bot fehlt im Server die Berechtigung **'Rollen verwalten'** (Manage Roles).\n\n"
                        f"**So behebst du diesen Fehler:**\n"
                        f"1. Gehe in deine **Server-Einstellungen** ➔ **Rollen**.\n"
                        f"2. Klicke auf die Rolle deines Bots (`𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣`).\n"
                        f"3. Aktiviere die Berechtigung **'Rollen verwalten'** (oder Administrator).\n"
                        f"4. Ziehe meine Rolle ganz nach oben.\n"
                        f"5. Führe `!role` erneut aus.",
            color=0xff003c,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await status_msg.edit(embed=embed_warning)
        return

    r_everyone = guild.default_role
    r_member = created_roles.get("👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿") or r_everyone
    r_customer = created_roles.get("🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿") or r_everyone
    r_premium_buyer = created_roles.get("💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿") or r_everyone
    r_vip = created_roles.get("🌟│ 𝗩𝗢𝗜𝗗 • 𝗩𝗜𝗣") or r_everyone
    r_booster = created_roles.get("💎│ 𝗩𝗢𝗜𝗗 • 𝗕𝗼𝗼𝘀𝘁𝗲𝗿") or r_everyone
    r_partner = created_roles.get("🤝│ 𝗩𝗢𝗜𝗗 • 𝗣𝗮𝗿𝘁𝗻𝗲𝗿") or r_everyone
    r_support = created_roles.get("🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁") or r_everyone
    r_trial_mod = created_roles.get("🚨│ 𝗩𝗢𝗜𝗗 • 𝗧𝗿𝗶𝗮𝗹 𝗠𝗼𝗱") or r_everyone
    r_mod = created_roles.get("🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿") or r_everyone
    r_manager = created_roles.get("⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿") or r_everyone
    r_admin = created_roles.get("🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻") or r_everyone
    r_co_owner = created_roles.get("👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿") or r_everyone
    r_owner = created_roles.get("👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿") or r_everyone

    progress_embed.description = f"> 👑 Rollen geprüft: **{roles_created_count} erstellt**, **{roles_skipped_count} übersprungen**.\n> 🔒 Setze jetzt Berechtigungen für alle Kanäle..."
    await status_msg.edit(embed=progress_embed)

    info_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True, read_message_history=True)}
    for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
        if r != r_everyone: info_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
    for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]:
        if r != r_everyone: info_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)

    staff_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
    for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]:
        if r != r_everyone: staff_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
    for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
        if r != r_everyone: staff_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    log_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
    for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner, r_support, r_trial_mod, r_mod]:
        if r != r_everyone: log_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
    for r in [r_manager, r_admin, r_co_owner, r_owner]:
        if r != r_everyone: log_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    channels_processed = 0
    for channel in guild.channels:
        try:
            if channel.category and "LOGS" in channel.category.name.upper():
                await channel.edit(overwrites=log_overwrites)
            elif channel.category and "STAFF" in channel.category.name.upper():
                await channel.edit(overwrites=staff_overwrites)
            elif channel.category and ("INFO" in channel.category.name.upper() or "SHOP" in channel.category.name.upper() or "SUPPORT" in channel.category.name.upper() or "VERIFY" in channel.category.name.upper()):
                await channel.edit(overwrites=info_overwrites)
            channels_processed += 1
            await asyncio.sleep(0.1)
        except Exception:
            pass

    success_embed = create_prestige_embed(
        title="🎉 Rollen & Rechte-Setup beendet!",
        description=f"> 👑 **Rollen erstellt:** {roles_created_count}\n"
                    f"> 👑 **Rollen übersprungen:** {roles_skipped_count}\n"
                    f"> 🔒 **Kanäle konfiguriert:** {channels_processed}\n\n"
                    f"Alle Berechtigungen wurden für deine 23 Rollen optimal eingestellt!",
        color=0x39ff14,
        author_user=ctx.author,
        bot_user=bot.user
    )
    await status_msg.edit(embed=success_embed)


# --- SETUP CONFIRMATION VIEW & COMMAND (!Start) ---

class SetupConfirmationView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label="🧹 Komplett neu aufsetzen", style=discord.ButtonStyle.danger, emoji="🧹")
    async def reset_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "reset"
        self.stop()

    @discord.ui.button(label="➕ Nur hinzufügen", style=discord.ButtonStyle.success, emoji="➕")
    async def add_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "add"
        self.stop()

    @discord.ui.button(label="❌ Abbrechen", style=discord.ButtonStyle.secondary, emoji="❌")
    async def cancel_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Das kannst du nicht entscheiden!", ephemeral=True)
            return
        await interaction.response.defer()
        self.value = "cancel"
        self.stop()


@bot.command(name="Start", aliases=["start"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def start(ctx):
    """
    Richtet den kompletten Server mit allen Kategorien, Kanälen und Logs ein.
    Nutzbar nach '!role', um das volle Layout zu erstellen.
    """
    embed_choice = create_prestige_embed(
        title="⚠️ 𝗩𝗢𝗜𝗗 • SERVER SETUP INITIALISIERUNG ⚠️",
        description=f"Hallo {ctx.author.mention},\n\ndu bist dabei, das **Prestige Server-Layout** für **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** aufzubauen.\n"
                    f"Dieses Setup generiert:\n"
                    f"> 📁 │ **7 Hauptkategorien, 1 Log-Kategorie & 1 Stats-Kategorie**\n"
                    f"> 💬 │ **27 Textkanäle, 7 Voicekanäle & 7 professionelle Log-Kanäle (Gesamt: 41 Kanäle)**\n"
                    f"> ⚙️ │ **Vollständiges Embed-Design in allen Infokanälen**\n\n"
                    f"Bitte wähle eine Option aus:\n\n"
                    f"🧹 **Komplett neu aufsetzen:** Löscht alle Kanäle (außer den aktuellen) und baut neu auf.\n"
                    f"➕ **Nur hinzufügen:** Ergänzt das Layout parallel.",
        color=0xff003c,
        author_user=ctx.author,
        bot_user=bot.user
    )
    
    view = SetupConfirmationView(ctx)
    confirm_msg = await ctx.send(embed=embed_choice, view=view)

    await view.wait()

    if view.value is None or view.value == "cancel":
        embed_cancel = create_prestige_embed(
            title="❌ Setup abgebrochen",
            description="> Das Server-Setup wurde abgebrochen. Es wurden keine Kanäle erstellt.",
            color=0x3e3e3e,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await confirm_msg.edit(embed=embed_cancel, view=None)
        return

    status_embed = create_prestige_embed(
        title="⚙️ Setup-Prozess läuft...",
        description="> Lösche alte Kanäle (sofern ausgewählt)...",
        color=0x00f0ff,
        author_user=ctx.author,
        bot_user=bot.user
    )
    status_msg = await ctx.send(embed=status_embed)
    await confirm_msg.delete()

    guild = ctx.guild

    if view.value == "reset":
        for channel in guild.channels:
            if channel.id != ctx.channel.id:
                try:
                    await channel.delete()
                    await asyncio.sleep(0.1)
                except Exception:
                    pass

    # Berechtigungs-Gruppen definieren
    r_everyone = guild.default_role
    r_member = discord.utils.get(guild.roles, name="👥│ 𝗩𝗢𝗜𝗗 • 𝗠𝗲𝗺𝗯𝗲𝗿") or r_everyone
    r_customer = discord.utils.get(guild.roles, name="🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿") or r_everyone
    r_premium_buyer = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • 𝗣𝗿𝗲𝗺𝗶𝘂𝗺 𝗕𝘂𝘆𝗲𝗿") or r_everyone
    r_vip = discord.utils.get(guild.roles, name="🌟│ 𝗩𝗢𝗜𝗗 • 𝗩𝗜package") or r_everyone
    r_booster = discord.utils.get(guild.roles, name="💎│ 𝗩𝗢𝗜𝗗 • 𝗕𝗼𝗼𝘀𝘁𝗲𝗿") or r_everyone
    r_partner = discord.utils.get(guild.roles, name="🤝│ 𝗩𝗢𝗜𝗗 • 𝗣𝗮𝗿𝘁𝗻𝗲𝗿") or r_everyone
    r_support = discord.utils.get(guild.roles, name="🎫│ 𝗩𝗢𝗜𝗗 • 𝗦𝘂𝗽𝗽𝗼𝗿𝘁") or r_everyone
    r_trial_mod = discord.utils.get(guild.roles, name="🚨│ 𝗩𝗢𝗜𝗗 • 𝗧𝗿𝗶𝗮𝗹 𝗠𝗼𝗱") or r_everyone
    r_mod = discord.utils.get(guild.roles, name="🛡️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗼𝗱𝗲𝗿𝗮𝘁𝗼𝗿") or r_everyone
    r_manager = discord.utils.get(guild.roles, name="⚙️│ 𝗩𝗢𝗜𝗗 • 𝗠𝗮𝗻𝗮𝗴𝗲𝗿") or r_everyone
    r_admin = discord.utils.get(guild.roles, name="🛠️│ 𝗩𝗢𝗜𝗗 • 𝗔𝗱𝗺𝗶𝗻") or r_everyone
    r_co_owner = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • 𝗖𝗼-𝗢𝘄𝗻𝗲𝗿") or r_everyone
    r_owner = discord.utils.get(guild.roles, name="👑│ 𝗩𝗢𝗜𝗗 • 𝗢𝘄𝗻𝗲𝗿") or r_everyone

    info_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False, add_reactions=True, read_message_history=True)}
    for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
        if r != r_everyone: info_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True, read_message_history=True)
    for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]:
        if r != r_everyone: info_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=False, read_message_history=True)

    community_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True, add_reactions=True, read_message_history=True)}

    staff_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
    for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner]:
        if r != r_everyone: staff_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
    for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
        if r != r_everyone: staff_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    # Höchstsensible Log-Rechte (Nur Manager+)
    log_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
    for r in [r_member, r_customer, r_premium_buyer, r_vip, r_booster, r_partner, r_support, r_trial_mod, r_mod]:
        if r != r_everyone: log_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
    for r in [r_manager, r_admin, r_co_owner, r_owner]:
        if r != r_everyone: log_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

    status_embed.description = "> 📁 Erstelle Server-Struktur & 41 Kanäle..."
    await status_msg.edit(embed=status_embed)

    categories_layout = [
        {
            "name": "📊│── 𝗩𝗢𝗜𝗗 • 𝗦𝗧𝗔𝗧𝗦 ──",
            "overwrites": info_overwrites,
            "channels": [
                {"name": "👥│Mitglieder: 0", "type": "voice", "description": ""},
                {"name": "💎│Booster: 0", "type": "voice", "description": ""},
                {"name": "🛒│Kunden: 0", "type": "voice", "description": ""}
            ]
        },
        {
            "name": "🔐│── 𝗩𝗢𝗜𝗗 • 𝗩𝗘𝗥𝗜𝗙𝗬 ──",
            "overwrites": info_overwrites,
            "channels": [
                {"name": "🔐│verify-here", "type": "text", "description": "Klicke unten auf den Button, um dich freizuschalten!"}
            ]
        },
        {
            "name": "📢│── 𝗩𝗢𝗜𝗗 • 𝗜𝗡𝗙𝗢 ──",
            "overwrites": info_overwrites,
            "channels": [
                {"name": "📢│news", "type": "text", "description": "Wichtige Ankündigungen & News"},
                {"name": "📜│rules", "type": "text", "description": "Das Serverregelwerk"},
                {"name": "👋│willkommen", "type": "text", "description": "Begrüßungskanal für neue Mitglieder"},
                {"name": "💨│aufwiedersehen", "type": "text", "description": "Verabschiedungskanal"},
                {"name": "🎁│giveaways", "type": "text", "description": "Spannende Giveaways & Gewinne"},
                {"name": "🤝│vouches", "type": "text", "description": "Erfahrungen unserer Käufer"},
                {"name": "📩│invites", "type": "text", "description": "Lade Freunde ein für Belohnungen!"},
                {"name": "🔗│partners", "type": "text", "description": "Unsere Partner-Server"}
            ]
        },
        {
            "name": "🛒│── 𝗩𝗢𝗜𝗗 • 𝗦𝗛𝗢𝗣 ──",
            "overwrites": info_overwrites,
            "channels": [
                {"name": "👕│tshirt-templates", "type": "text", "description": "Exklusive T-Shirt Vorlagen für Roblox"},
                {"name": "⚙️│fastflags", "type": "text", "description": "FPS & Performance Optimierungen"},
                {"name": "🖥️│discord-templates", "type": "text", "description": "Schicke Discord Server Vorlagen"},
                {"name": "📦│products", "type": "text", "description": "Unsere Produkt- & Preisübersicht"},
                {"name": "🛒│how-to-buy", "type": "text", "description": "Wie du bei uns einkaufen kannst"},
                {"name": "📈│updates", "type": "text", "description": "Entwicklungs-Updates & Produktnews"}
            ]
        },
        {
            "name": "💬│── 𝗩𝗢𝗜𝗗 • 𝗖𝗛𝗔𝗧 ──",
            "overwrites": community_overwrites,
            "channels": [
                {"name": "💬│general-chat", "type": "text", "description": "Der Hauptchat für jedermann"},
                {"name": "📷│media-and-showcase", "type": "text", "description": "Teile Bilder, Videos oder Avatare"},
                {"name": "🎨│clothing-showcase", "type": "text", "description": "Zeige deine eigenen Roblox-Kleidungsdesigns!"},
                {"name": "🖥️│setup-showcase", "type": "text", "description": "Zeige deinen Gaming-Setup oder Studio-Setup"},
                {"name": "📈│trading", "type": "text", "description": "Tausche und handle mit Roblox-Gegenständen"},
                {"name": "🤝│suggestions", "type": "text", "description": "Deine Verbesserungsvorschläge für den Shop"},
                {"name": "🤖│bot-commands", "type": "text", "description": "Nutze die Bot-Befehle hier"}
            ]
        },
        {
            "name": "🎙️│── 𝗩𝗢𝗜𝗗 • 𝗧𝗔𝗟𝗞 ──",
            "overwrites": community_overwrites,
            "channels": [
                {"name": "🔊│Lobby • Public", "type": "voice", "description": ""},
                {"name": "🔊│Lounge • Chill", "type": "voice", "description": ""},
                {"name": "🔊│Roblox • Talk", "type": "voice", "description": ""},
                {"name": "🔊│Gaming • Duo", "type": "voice", "description": ""},
                {"name": "🔊│Gaming • Squad", "type": "voice", "description": ""},
                {"name": "🔊│Support • Voice", "type": "voice", "description": ""}
            ]
        },
        {
            "name": "💎│── 𝗩𝗢𝗜𝗗 • 𝗟𝗢𝗨𝗡𝗚𝗘 ──",
            "overwrites": community_overwrites,
            "channels": [
                {"name": "💎│booster-lounge", "type": "text", "description": "Spezialchat für Server-Booster", "custom_overwrites": "booster"},
                {"name": "🌟│vip-lounge", "type": "text", "description": "Exklusiver Chat für VIP-Kunden", "custom_overwrites": "vip"},
                {"name": "🛒│customer-lounge", "type": "text", "description": "Austauschbereich für alle Käufer", "custom_overwrites": "customer"}
            ]
        },
        {
            "name": "🎟️│── 𝗩𝗢𝗜𝗗 • 𝗦𝗨𝗣𝗣𝗢𝗥𝗧 ──",
            "overwrites": info_overwrites,
            "channels": [
                {"name": "🎟️│create-ticket", "type": "text", "description": "Erstelle ein Support- oder Kauf-Ticket"},
                {"name": "❓│faq", "type": "text", "description": "Häufig gestellte Fragen (FAQs)"}
            ]
        },
        {
            "name": "🔒│── 𝗩𝗢𝗜𝗗 • 𝗦𝗧𝗔𝗙𝗙 ──",
            "overwrites": staff_overwrites,
            "channels": [
                {"name": "🔒│staff-chat", "type": "text", "description": "Das interne Besprechungszimmer"},
                {"name": "🛠️│mod-commands", "type": "text", "description": "Eingabe von Admin- und Moderations-Commands"},
                {"name": "🔊│Staff • Voice", "type": "voice", "description": ""}
            ]
        },
        {
            "name": "📁│── 𝗩𝗢𝗜𝗗 • 𝗟𝗢𝗚𝗦 ──",
            "overwrites": log_overwrites,
            "channels": [
                {"name": "💬│voice-logs", "type": "text", "description": "Logs für Sprachkanäle"},
                {"name": "🔨│ban-kick-logs", "type": "text", "description": "Logs für Banns, Kicks und Timeouts"},
                {"name": "📝│message-logs", "type": "text", "description": "Logs für gelöschte & editierte Nachrichten"},
                {"name": "📩│invite-logs", "type": "text", "description": "Logs für erstellte & genutzte Einladungslinks"},
                {"name": "📥│join-leave-logs", "type": "text", "description": "Logs für Serverbeitritte & Austritte"},
                {"name": "💾│ticket-logs", "type": "text", "description": "Ticket-Protokolle & Transkripte"},
                {"name": "⚙️│system-logs", "type": "text", "description": "System-Logs für Kanäle & Rollen"}
            ]
        }
    ]

    channels_by_name = {}

    for cat_data in categories_layout:
        category = discord.utils.get(guild.categories, name=cat_data["name"])
        if not category:
            try:
                category = await guild.create_category(name=cat_data["name"], overwrites=cat_data["overwrites"])
                await asyncio.sleep(0.2)
            except discord.Forbidden:
                embed_err = create_prestige_embed(
                    title="⚠️ FEHLER: Keine Kanäle erstellt!",
                    description=f"> Ich habe keine Berechtigung, Kategorien oder Kanäle zu erstellen!\n\n"
                                f"**Behebung:**\n"
                                f"Bitte stelle sicher, dass mein Bot die Berechtigung **'Kanäle verwalten'** (Manage Channels) oder **'Administrator'** besitzt und führe `!Start` erneut aus.",
                    color=0xff003c,
                    author_user=ctx.author,
                    bot_user=bot.user
                )
                await status_msg.edit(embed=embed_err)
                return
            except Exception as e:
                logger.error(f"Fehler bei Kategorie {cat_data['name']}: {e}")
                continue
        
        for ch_data in cat_data["channels"]:
            current_overwrites = cat_data["overwrites"].copy()
            
            # Custom Overwrites für Lounges
            if ch_data.get("custom_overwrites") == "booster":
                current_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
                for r in [r_member, r_customer, r_premium_buyer, r_vip]:
                    if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
                if r_booster != r_everyone: current_overwrites[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
                    if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                
            elif ch_data.get("custom_overwrites") == "vip":
                current_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
                for r in [r_member, r_customer, r_premium_buyer]:
                    if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=False)
                if r_booster != r_everyone: current_overwrites[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                if r_vip != r_everyone: current_overwrites[r_vip] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
                    if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            elif ch_data.get("custom_overwrites") == "customer":
                current_overwrites = {r_everyone: discord.PermissionOverwrite(view_channel=False)}
                if r_member != r_everyone: current_overwrites[r_member] = discord.PermissionOverwrite(view_channel=False)
                if r_booster != r_everyone: current_overwrites[r_booster] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                if r_customer != r_everyone: current_overwrites[r_customer] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                if r_premium_buyer != r_everyone: current_overwrites[r_premium_buyer] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                if r_vip != r_everyone: current_overwrites[r_vip] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                for r in [r_support, r_trial_mod, r_mod, r_manager, r_admin, r_co_owner, r_owner]:
                    if r != r_everyone: current_overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

            if ch_data["type"] == "voice":
                channel = discord.utils.get(category.voice_channels, name=ch_data["name"])
                if not channel:
                    try:
                        channel = await guild.create_voice_channel(
                            name=ch_data["name"],
                            category=category,
                            overwrites=current_overwrites
                        )
                        await asyncio.sleep(0.15)
                    except Exception as e:
                        logger.error(f"Fehler bei Voice-Kanal {ch_data['name']}: {e}")
                        continue
            else:
                channel = discord.utils.get(category.text_channels, name=ch_data["name"])
                if not channel:
                    try:
                        channel = await guild.create_text_channel(
                            name=ch_data["name"],
                            category=category,
                            overwrites=current_overwrites,
                            topic=ch_data["description"]
                        )
                        await asyncio.sleep(0.15)
                    except Exception as e:
                        logger.error(f"Fehler bei Text-Kanal {ch_data['name']}: {e}")
                        continue
            channels_by_name[ch_data["name"]] = channel

    # 5. SCHRITT: Kanäle befüllen (Embeds mit 1000x schönem Layout)
    status_embed.description = "> 📝 Richte detaillierte Infokanäle, FAQs und Einladungs-Systeme ein..."
    await status_msg.edit(embed=status_embed)

    c_ticket_mention = channels_by_name["🎟️│create-ticket"].mention if "🎟️│create-ticket" in channels_by_name else "#create-ticket"
    c_ff_mention = channels_by_name["⚙️│fastflags"].mention if "⚙️│fastflags" in channels_by_name else "#fastflags"

    # A) REGELN
    c_rules = channels_by_name.get("📜│rules")
    if c_rules:
        embed_rules = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📜 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 - SERVER REGELN\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description="Um eine sichere, professionelle und angenehme Atmosphäre für alle Kunden und Creator zu gewährleisten, bitten wir dich, die folgenden Richtlinien einzuhalten:\n\n"
                        "🤖 │ **𝟭. 𝗥𝗲𝘀𝗽𝗲𝗸𝘁 & 𝗛ö𝗳𝗹𝗶𝗰𝗵𝗸𝗲𝗶𝘁**\n"
                        "> Behandle jedes Mitglied und jeden Staff mit vollstem Respekt. Beleidigungen, Toxizität, Belästigung oder Drohungen jeglicher Art führen zum sofortigen Serverausschluss.\n\n"
                        "🚫 │ **𝟮. 𝗞𝗲𝗶𝗻 𝗦𝗽𝗮𝗺 & 𝗙𝗿𝗲𝗺𝗱𝘄𝗲𝗿𝗯𝘂𝗻𝗴**\n"
                        "> Spamming in den Kanälen ist verboten. Das Posten von Werbelinks zu anderen Discord-Servern, Dienstleistungen oder Fremdprodukten (sowohl in Chats als auch per DM) wird permanent gebannt.\n\n"
                        "🛒 │ **𝟯. 𝗦𝗶𝗰𝗵𝗲𝗿𝗲𝗿 & 𝗢𝗳𝗳𝗶𝘇𝗶𝗲𝗹𝗹𝗲𝗿 𝗛𝗮𝗻𝗱𝗲𝗹**\n"
                        "> Jegliche Verkäufe und Dienstleistungen finden ausschließlich über unser offizielles Ticket-System in %s statt. Privater Handel oder das Anbieten eigener Produkte ist untersagt.\n\n"
                        "📎 │ **𝟰. 𝗡𝗦𝗙𝗪 & Unangemessene Inhalte**\n"
                        "> Keine jugendgefährdenden, pornografischen, gewaltverherrlichenden oder illegalen Medien.\n\n"
                        "📌 │ **𝗛𝗶𝗻𝘄𝗲𝗶𝘀**\n"
                        "> Mit dem Aufenthalt auf diesem Server akzeptierst du die Discord Nutzungsbedingungen (TOS) sowie unsere Serverregeln. Unsere Moderatoren haben das Recht, bei Verstößen ohne Vorwarnung einzugreifen." % c_ticket_mention,
            color=0xff003c,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await c_rules.send(embed=embed_rules)

    # B) HOW TO BUY
    c_buy = channels_by_name.get("🛒│how-to-buy")
    if c_buy:
        embed_buy = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🛒 𝗩𝗢𝗜𝗗 • 𝗪𝗜𝗘 𝗞𝗔𝗨𝗙𝗘 𝗜𝗖𝗛?\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description="Der Ablauf eines Einkaufs bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣** ist vollständig automatisiert und absolut sicher. Folge einfach diesem einfachen Ablauf:\n\n"
                        "1️⃣ │ **Ticket erstellen**\n"
                        f"> Besuche den Kanal {c_ticket_mention} und klicke auf den Button **'Produkt kaufen'**. Ein privater Supportkanal wird nur für dich erstellt.\n\n"
                        "2️⃣ │ **Produktdetails angeben**\n"
                        "> Teile unserem Supportteam im Ticket mit, was du kaufen möchtest (z.B. Premium FastFlags, bestimmte T-Shirt Templates, Serverlayouts).\n\n"
                        "3️⃣ │ **Zahlungsabwicklung**\n"
                        "> Wähle deine bevorzugte Zahlungsmethode aus. Wir unterstützen:\n"
                        "> 🔹 PayPal (Familie & Freunde)\n"
                        "> 🔹 Robux (via Gamepass oder Gruppen-Auszahlung)\n"
                        "> 🔹 Paysafecard\n"
                        "> 🔹 Kryptowährungen (Litecoin - LTC, Bitcoin - BTC, USDT)\n\n"
                        "4️⃣ │ **Lieferung erhalten**\n"
                        "> Nach der Zahlungsbestätigung wird dein digitales Produkt (Config, Code, PNG-Download) direkt im Ticket an dich übergeben!",
            color=0x00f0ff,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await c_buy.send(embed=embed_buy)

    # C) PRODUCTS
    c_products = channels_by_name.get("📦│products")
    if c_products:
        embed_products = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📦 𝗩𝗢𝗜𝗗 • 𝗨𝗡𝗦𝗘𝗥𝗘 𝗣𝗥𝗢𝗗𝗨𝗞𝗧𝗘\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description="Finde hier deine Roblox- und Discord-Upgrades:\n\n"
                        "**👕 Roblox Kleidung:**\n"
                        "> • *Klassische T-Shirt PNGs:* ab 50 Robux / 0,50€\n"
                        "> • *Exklusive Bundles (50+ Vorlagen):* ab 500 Robux / 5,00€\n\n"
                        "**⚙️ FastFlags (FPS-Boost):**\n"
                        f"> • *Standard-Configs:* Gratis (siehe {c_ff_mention})\n"
                        f"> • *Premium Ultra Configs:* 150 Robux / 1,50€\n\n"
                        "**🖥️ Discord Templates:**\n"
                        "> • *Fertiges Shop-Layout:* 400 Robux / 4,00€",
            color=0xffd700,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await c_products.send(embed=embed_products)

    # D) TICKET PANEL
    c_ticket_panel = channels_by_name.get("🎟️│create-ticket")
    if c_ticket_panel:
        embed_ticket_panel = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🎟️ 𝗩𝗢𝗜𝗗 • Support & Kauf-Center\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description="Benötigst du Hilfe oder möchtest etwas kaufen?\n"
                        "Wähle einfach die passende Kategorie aus:\n\n"
                        "> 🛒 │ **Produkt kaufen** ➔ Roblox Items, FastFlags, Templates\n"
                        "> ⚙️ │ **Allgemeiner Support** ➔ Technische Hilfe\n"
                        "> 🤝 │ **Partnerschaft** ➔ Für Kooperationen",
            color=0x00f0ff,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await c_ticket_panel.send(embed=embed_ticket_panel, view=TicketButton())

    # E) FAQ
    c_faq = channels_by_name.get("❓│faq")
    if c_faq:
        embed_faq = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n❓ 𝗩𝗢𝗜𝗗 • FAQ (Häufige Fragen)\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description="**Sind FastFlags erlaubt?**\n"
                        "> Ja, FastFlags sind Teil der offiziellen Roblox-Einstellungen. Es ist keine Cheat-Software!\n\n"
                        "**Wie lange dauert die Lieferung?**\n"
                        "> Fast immer innerhalb von 15 Minuten nach Zahlungseingang im Ticket.",
            color=0x00f0ff,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await c_faq.send(embed=embed_faq)

    # F) INVITES
    c_inv = channels_by_name.get("📩│invites")
    if c_inv:
        embed_inv = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n📩 𝗩𝗢𝗜𝗗 • Invite Belohnungen\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description="Lade Freunde auf unseren Server ein und staube dicke Gewinne ab:\n\n"
                        "> 🎁 │ **5 Invites** ➔ Gratis T-Shirt Template\n"
                        "> 🎁 │ **10 Invites** ➔ Gratis Premium FastFlags\n"
                        "> 🎁 │ **20 Invites** ➔ Gratis Discord Server-Layout",
            color=0xffa500,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await c_inv.send(embed=embed_inv)

    # G) VERIFY HERE PANEL IN #verify-here
    c_v_here = channels_by_name.get("🔐│verify-here")
    if c_v_here:
        embed_v_here = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n🔐 𝗩𝗢𝗜𝗗 • SERVEREINTRETEN VERIFIZIERUNG\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description="Herzlich Willkommen bei **𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣**!\n\n"
                        "Um vollen Zugriff auf den Server (Chats, Produkte, Giveaways) zu erhalten, musst du dich verifizieren.\n\n"
                        "**So einfach geht's:**\n"
                        "> 1️⃣ │ Klicke unten auf den grünen Button **'Verifizieren 🔐'**.\n"
                        "> 2️⃣ │ Du erhältst sofort die **Member-Rolle** und wirst freigeschaltet.\n\n"
                        "*Hinweis: Für erweiterte Käufe kannst du zusätzlich die Roblox-Verifizierung nutzen!*",
            color=0x39ff14,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await c_v_here.send(embed=embed_v_here, view=SimpleVerifyButton())

    # H) FIRST VOUCH PREPARATION IN #vouches
    c_vouches = channels_by_name.get("🤝│vouches")
    if c_vouches:
        embed_vouch_placeholder = create_prestige_embed(
            title="🤝 𝗩𝗢𝗜𝗗 • 𝗞𝗨𝗡𝗗𝗘𝗡-𝗕𝗘𝗪𝗘𝗥𝗧𝗨𝗡𝗚𝗘𝗡 🤝",
            description="Kundenzufriedenheit steht bei uns an oberster Stelle!\n\n"
                        "Wenn du bei uns eingekauft hast, würden wir uns sehr über eine Bewertung freuen. "
                        "Das hilft uns und stärkt das Vertrauen neuer Kunden.\n\n"
                        "**Beispiel für eine Bewertung:**\n"
                        "⭐ ⭐ ⭐ ⭐ ⭐ - *Sehr schneller Support, FastFlags funktionieren perfekt und habe direkt +120 FPS bekommen! Gerne wieder!*",
            color=0xffd700,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await c_vouches.send(embed=embed_vouch_placeholder)

    # Statistiken sofort updaten
    await update_stats_channels(guild)

    status_embed.title = "🎉 Server-Setup erfolgreich abgeschlossen! 🎉"
    status_embed.description = (
        f"> 📁 **Kategorien & Kanäle:** 41 Kanäle erfolgreich eingerichtet.\n"
        f"> 🔒 **Rechte:** Hochsicheres, fehlerfreies Rechtesystem aktiv.\n"
        f"> 🎟️ **Tickets:** Interaktive Multi-Tickets mit Claim-Funktion sind einsatzbereit!\n\n"
        f"Nutze `!Start` oder lösche diese Nachricht, falls gewünscht."
    )
    status_embed.color = 0x39ff14
    await status_msg.edit(embed=status_embed)


# --- AUTOMATISCHES DETEILLIERTES LOGGING (LOGS CATEGORY) ---

@bot.event
async def on_message_delete(message):
    """Loggt gelöschte Nachrichten."""
    if not message.guild or message.author.bot:
        return
    log_channel = discord.utils.get(message.guild.text_channels, name="📝│message-logs")
    if log_channel:
        embed = create_prestige_embed(
            title="🗑️ Nachricht gelöscht",
            description=f"> **Kanal:** {message.channel.mention}\n"
                        f"> **Autor:** {message.author.mention} ({message.author.name})\n\n"
                        f"**Inhalt:**\n"
                        f"> {message.content if message.content else '*Kein Text (z.B. Bild)*'}",
            color=0xff003c,
            author_user=message.author,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    """Loggt bearbeitete Nachrichten."""
    if not before.guild or before.author.bot or before.content == after.content:
        return
    log_channel = discord.utils.get(before.guild.text_channels, name="📝│message-logs")
    if log_channel:
        embed = create_prestige_embed(
            title="✏️ Nachricht bearbeitet",
            description=f"> **Kanal:** {before.channel.mention}\n"
                        f"> **Autor:** {before.author.mention} ({before.author.name})\n\n"
                        f"**Zuvor:**\n"
                        f"> {before.content}\n\n"
                        f"**Danach:**\n"
                        f"> {after.content}",
            color=0x00f0ff,
            author_user=before.author,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_create(channel):
    """Loggt erstellte Kanäle."""
    log_channel = discord.utils.get(channel.guild.text_channels, name="⚙️│system-logs")
    if log_channel:
        moderator = None
        try:
            now = discord.utils.utcnow()
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=1):
                if entry.target.id == channel.id and (now - entry.created_at).total_seconds() < 15:
                    moderator = entry.user
                    break
        except Exception:
            pass
        embed = create_prestige_embed(
            title="📁 Kanal erstellt",
            description=f"> **Kanal:** {channel.name}\n"
                        f"> **Kategorie:** {channel.category.name if channel.category else 'Keine'}\n"
                        f"> **Mitarbeiter:** {moderator.mention if moderator else 'Unbekannt'}",
            color=0x39ff14,
            author_user=moderator if moderator else bot.user,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_channel_delete(channel):
    """Loggt gelöschte Kanäle."""
    log_channel = discord.utils.get(channel.guild.text_channels, name="⚙️│system-logs")
    if log_channel:
        moderator = None
        try:
            now = discord.utils.utcnow()
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                if entry.target.id == channel.id and (now - entry.created_at).total_seconds() < 15:
                    moderator = entry.user
                    break
        except Exception:
            pass
        embed = create_prestige_embed(
            title="🛑 Kanal gelöscht",
            description=f"> **Kanal:** {channel.name}\n"
                        f"> **Mitarbeiter:** {moderator.mention if moderator else 'Unbekannt'}",
            color=0xff003c,
            author_user=moderator if moderator else bot.user,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    """Loggt erstellte Rollen."""
    log_channel = discord.utils.get(role.guild.text_channels, name="⚙️│system-logs")
    if log_channel:
        moderator = None
        try:
            now = discord.utils.utcnow()
            async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_create, limit=1):
                if entry.target.id == role.id and (now - entry.created_at).total_seconds() < 15:
                    moderator = entry.user
                    break
        except Exception:
            pass
        embed = create_prestige_embed(
            title="👑 Rolle erstellt",
            description=f"> **Rolle:** {role.mention} ({role.name})\n"
                        f"> **Mitarbeiter:** {moderator.mention if moderator else 'Unbekannt'}",
            color=0x39ff14,
            author_user=moderator if moderator else bot.user,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    """Loggt gelöschte Rollen."""
    log_channel = discord.utils.get(role.guild.text_channels, name="⚙️│system-logs")
    if log_channel:
        moderator = None
        try:
            now = discord.utils.utcnow()
            async for entry in role.guild.audit_logs(action=discord.AuditLogAction.role_delete, limit=1):
                if entry.target.id == role.id and (now - entry.created_at).total_seconds() < 15:
                    moderator = entry.user
                    break
        except Exception:
            pass
        embed = create_prestige_embed(
            title="🛑 Rolle gelöscht",
            description=f"> **Rolle:** {role.name}\n"
                        f"> **Mitarbeiter:** {moderator.mention if moderator else 'Unbekannt'}",
            color=0xff003c,
            author_user=moderator if moderator else bot.user,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    """Loggt Voice-Kanal Wechsel."""
    if member.bot:
        return
    log_channel = discord.utils.get(member.guild.text_channels, name="💬│voice-logs")
    if not log_channel:
        return

    if before.channel is None and after.channel is not None:
        embed = create_prestige_embed(
            title="🔊 Voice-Kanal betreten",
            description=f"> {member.mention} hat den Sprachkanal {after.channel.mention} betreten.",
            color=0x39ff14,
            author_user=member,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)
    elif before.channel is not None and after.channel is None:
        embed = create_prestige_embed(
            title="🔇 Voice-Kanal verlassen",
            description=f"> {member.mention} hat den Sprachkanal {before.channel.mention} verlassen.",
            color=0xff003c,
            author_user=member,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)
    elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        embed = create_prestige_embed(
            title="🔄 Voice-Kanal gewechselt",
            description=f"> {member.mention} hat den Sprachkanal gewechselt.\n\n"
                        f"**Von:** {before.channel.mention}\n"
                        f"**Zu:** {after.channel.mention}",
            color=0x00f0ff,
            author_user=member,
            bot_user=bot.user
        )
        await log_channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    """Loggt Serverbeitritte, sendet Willkommens-Embeds & Invite-Tracking."""
    guild = member.guild
    
    # ✉️ NETTE BEGRÜSSUNG IM WILLKOMMENS-KANAL (DIZZY JOIN)
    welcome_channel = discord.utils.get(guild.text_channels, name="👋│willkommen")
    if welcome_channel:
        embed_welcome_msg = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n👋 HERZLICH WILLKOMMEN BEI 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 👋\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description=f"Hallo **{member.name}**! Schön, dass du da bist!\n"
                        f"Wir freuen uns ungemein, dich auf unserem prestigeträchtigen Server begrüßen zu dürfen.\n\n"
                        f"**Deine ersten Schritte:**\n"
                        f"> 🔐 │ Schalte dich sofort frei im Kanal <#verify_channel_id_here> (oder `#verify-here`).\n"
                        f"> 👤 │ Roblox-Verifizierung nutzen: `!verify <Username>`\n"
                        f"> 🛒 │ Schalte exklusive Rollen frei mit: `!checkbuy <Username> <Gamepass_ID>`\n\n"
                        f"📌 │ Du bist unser **{len(guild.members)}.** wertvolles Mitglied!\n"
                        f"Genieße deinen Aufenthalt und hab eine tolle Zeit bei uns! ✨",
            color=0x00f0ff,
            author_user=member,
            bot_user=bot.user
        )
        embed_welcome_msg.set_thumbnail(url=member.display_avatar.url)
        # Suche den echten Kanal
        v_channel = discord.utils.get(guild.text_channels, name="🔐│verify-here")
        if v_channel:
            embed_welcome_msg.description = embed_welcome_msg.description.replace("<#verify_channel_id_here>", v_channel.mention)
        await welcome_channel.send(content=f"Hallo {member.mention}, schön dass du da bist! 👋", embed=embed_welcome_msg)

    # Echtzeit Stats-Update bei Join
    await update_stats_channels(guild)

    # Standard-Logs befüllen
    log_channel = discord.utils.get(guild.text_channels, name="📥│join-leave-logs")
    invite_log_channel = discord.utils.get(guild.text_channels, name="📩│invite-logs")
    
    used_invite = None
    try:
        if guild.id in bot.invites_cache:
            old_invites = bot.invites_cache[guild.id]
            new_invites = await guild.invites()
            bot.invites_cache[guild.id] = new_invites
            
            for old_inv in old_invites:
                for new_inv in new_invites:
                    if old_inv.code == new_inv.code and new_inv.uses > old_inv.uses:
                        used_invite = new_inv
                        break
    except Exception:
        pass

    if log_channel:
        embed = create_prestige_embed(
            title="📥 Mitglied beigetreten",
            description=f"> {member.mention} ({member.name}) hat den Server betreten.\n"
                        f"> **Account-Erstellung:** {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            color=0x39ff14,
            author_user=member,
            bot_user=bot.user
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_channel.send(embed=embed)

    if invite_log_channel and used_invite:
        embed_inv = create_prestige_embed(
            title="📩 Einladung genutzt",
            description=f"> {member.mention} ist beigetreten mit der Einladung von {used_invite.inviter.mention}.\n\n"
                        f"**Code:** `{used_invite.code}`\n"
                        f"**Nutzungen:** {used_invite.uses}",
            color=0xffa500,
            author_user=used_invite.inviter,
            bot_user=bot.user
        )
        await invite_log_channel.send(embed=embed_inv)

@bot.event
async def on_member_remove(member):
    """Loggt Austritte, Abschieds-Embeds & Kicks."""
    guild = member.guild
    
    goodbye_channel = discord.utils.get(guild.text_channels, name="💨│aufwiedersehen")
    if goodbye_channel:
        embed_goodbye_msg = create_prestige_embed(
            title="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n💨 AUF WIEDERSEHEN...\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            description=f"> **{member.name}** hat uns verlassen.\n"
                        f"> Wir wünschen dir alles Gute auf deinem weiteren Weg! 💨",
            color=0xff003c,
            author_user=member,
            bot_user=bot.user
        )
        embed_goodbye_msg.set_thumbnail(url=member.display_avatar.url)
        await goodbye_channel.send(embed=embed_goodbye_msg)

    # Echtzeit Stats-Update bei Leave
    await update_stats_channels(guild)

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

    if kicked_by:
        log_channel = discord.utils.get(guild.text_channels, name="🔨│ban-kick-logs")
        if log_channel:
            embed = create_prestige_embed(
                title="👢 Mitglied gekickt",
                description=f"> **Mitglied:** {member.name} ({member.id})\n"
                            f"> **Moderator:** {kicked_by.mention}\n"
                            f"> **Grund:** {reason}",
                color=0xff003c,
                author_user=kicked_by,
                bot_user=bot.user
            )
            await log_channel.send(embed=embed)
    else:
        log_channel = discord.utils.get(guild.text_channels, name="📥│join-leave-logs")
        if log_channel:
            embed = create_prestige_embed(
                title="📤 Mitglied verlassen",
                description=f"> {member.mention} ({member.name}) hat den Server verlassen.",
                color=0xff003c,
                author_user=member,
                bot_user=bot.user
            )
            await log_channel.send(embed=embed)

@bot.event
async def on_member_ban(guild, user):
    """Loggt Banns."""
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

    embed = create_prestige_embed(
        title="🔨 Mitglied gebannt",
        description=f"> **Mitglied:** {user.name} ({user.id})\n"
                    f"> **Moderator:** {banned_by.mention if banned_by else 'Unbekannt'}\n"
                    f"> **Grund:** {reason}",
        color=0xff003c,
        author_user=banned_by if banned_by else user,
        bot_user=bot.user
    )
    await log_channel.send(embed=embed)

@bot.event
async def on_member_update(before, after):
    """Loggt Timeouts, Rollen-Updates und aktualisiert Stats-Kanäle in Echtzeit."""
    guild = after.guild
    
    # 📊 ECHTZEIT STATS UPDATE BEI ROLLENÄNDERUNG ODER SUBSCRIPTION
    if before.roles != after.roles or before.premium_since != after.premium_since:
        await update_stats_channels(guild)

    if before.timed_out_until != after.timed_out_until:
        log_channel = discord.utils.get(guild.text_channels, name="🔨│ban-kick-logs")
        if log_channel:
            if after.timed_out_until is not None:
                moderator = None
                reason = "Kein Grund angegeben"
                try:
                    async for entry in guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
                        if entry.target.id == after.id and hasattr(entry.after, 'communication_disabled_until'):
                            moderator = entry.user
                            reason = entry.reason if entry.reason else "Kein Grund angegeben"
                            break
                except Exception:
                    pass

                embed = create_prestige_embed(
                    title="⏳ Timeout verhängt (Stummgeschaltet)",
                    description=f"> **Mitglied:** {after.mention}\n"
                                f"> **Moderator:** {moderator.mention if moderator else 'Unbekannt'}\n"
                                f"> **Bis:** {after.timed_out_until.strftime('%Y-%m-%d %H:%M:%S')}\n"
                                f"> **Grund:** {reason}",
                    color=0xffa500,
                    author_user=moderator if moderator else after,
                    bot_user=bot.user
                )
                await log_channel.send(embed=embed)
            else:
                embed = create_prestige_embed(
                    title="🔊 Timeout vorzeitig aufgehoben",
                    description=f"> Der Timeout für {after.mention} wurde aufgehoben.",
                    color=0x39ff14,
                    author_user=after,
                    bot_user=bot.user
                )
                await log_channel.send(embed=embed)


# --- ERROR HANDLING ---

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        embed_err = create_prestige_embed(
            title="❌ Keine Berechtigung",
            description="> Du benötigst Administrator-Berechtigungen auf diesem Server, um diesen Befehl auszuführen!",
            color=0xff003c,
            author_user=ctx.author,
            bot_user=bot.user
        )
        await ctx.send(embed=embed_err, delete_after=10)
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("Dieser Befehl kann nicht in Direktnachrichten ausgeführt werden.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        logger.error(f"Ein Fehler ist aufgetreten: {error}")


# --- START DES BOTS ---

if __name__ == "__main__":
    if not TOKEN or TOKEN == "DEIN_BOT_TOKEN_HIER":
        logger.error("FEHLER: Bitte gib einen gültigen Discord Bot-Token direkt in der 'bot.py' Datei (Zeile 37) an!")
    else:
        # Flask Webserver für 24/7 online halten auf Railway starten
        keep_alive()
        
        try:
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            logger.error("FEHLER: Der angegebene Bot-Token ist ungültig! Bitte überprüfe den Token in deiner 'bot.py' Datei (Zeile 37).")
        except Exception as e:
            logger.error(f"Fehler beim Starten des Bots: {e}")
