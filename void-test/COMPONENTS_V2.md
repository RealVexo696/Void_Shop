# Components V2 — Umstellung 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣

Die Embeds **mit Buttons** wurden auf das neue **Discord Components V2** Format
umgestellt (genau das Container-Layout aus dem gewünschten JSON):

| V2-Typ | Bedeutung | im JSON |
|--------|-----------|---------|
| `17` | **Container** (mit Akzent-Farbstreifen) | `type: 17` |
| `10` | **Text Display** (Markdown statt Embed-Description) | `type: 10` |
| `1`  | **Action Row** (enthält Buttons/Selects) | `type: 1` |
| `2`  | **Button** | `type: 2` |
| `3`  | **Select-Menü** | `type: 3` |
| `14` | **Separator** (Trennlinie) | `type: 14` |
| Flag `32768` | `IS_COMPONENTS_V2` (setzt discord.py automatisch) | `flags: 32768` |

## Was wurde umgebaut?

1. **`bot/cogs/components_v2.py`** *(neu)* — zentraler Helper:
   - `PrestigeContainer(title, body, items=[...])` → fertiger V2-Container
   - `build_layout(...)` → fertige `LayoutView` (für einfache Panels ohne eigene Klasse)

2. **`SetupConfirmationView`** (`setup.py`) — `!Start`-Bestätigung
   → Container + Text + 3 Buttons (🧹 komplett neu / ➕ nur hinzufügen / ❌ abbrechen).
   Auch die **Abbruch-Meldung** ist jetzt V2.

3. **`TicketButton`** (`tickets.py`) — Ticket-Panel
   → Container + Text + Select-Menü. Persistent.

4. **`SimpleVerifyButton`** (`verification.py`) — Verify-Panel
   → Container + Text + Verify-Button. Persistent.

5. **`requirements.txt`** → `discord.py>=2.6.0` (Components V2 braucht 2.6+; lokal 2.7.1 getestet).

## Wichtig zu wissen

- Eine **LayoutView wird OHNE `embed=` gesendet** — der Text steckt jetzt im Container:
  ```python
  await ctx.send(view=TicketButton())          # richtig
  # await ctx.send(embed=..., view=...)         # falsch (mischen geht bei V2 nicht)
  ```
- In einer LayoutView **kann man kein klassisches Embed mehr mitschicken**. Author-Avatar
  und Embed-Footer gibt es im V2-Format nicht — der Helper bildet sie als Text nach
  (`-# @user` als Subtext, `-# Powered by BotForge` als Footer).
- Die persistenten Views sind weiterhin in `bot/__init__.py` via `self.add_view(...)`
  registriert — das funktioniert mit LayoutViews unverändert.

## 🎟️ Ticket-System — komplett neu (Components V2)

Das gesamte Ticket-System (`bot/cogs/tickets.py`) wurde neu aufgebaut:

**Neue Produkte** (zentral in `PRODUCTS` / `PRODUCT_ORDER`):
| # | Produkt | Preis |
|---|---------|-------|
| 1 | ♾️ **INFINITYxEH** | 750 R$ / 7,50 € |
| 2 | 💉 **FFlags Injector** | 300 R$ / 3,00 € |
| 3 | 🛡️ **Anti-Ban** | 450 R$ / 4,50 € |

**Verbesserungen:**
- 100% Components V2 — jedes Embed ist jetzt ein Container.
- **Produkt-Auswahl direkt im Panel-Dropdown** — wer „INFINITYxEH“ wählt, bekommt
  ein Kauf-Ticket mit genau diesem Produkt schon vorausgefüllt.
- **Fortlaufende Ticket-Nummern** (`🛒│kauf-0001`, `⚙️│support-0002`, …) statt Username.
- **Produkt-Katalog** wird automatisch ins Kauf-Ticket gepostet.
- **Steuerleiste** im Ticket: Claimen · Priorität (🟢🟡🔴) · User +/− · Umbenennen · Schließen.
- **Sterne-Bewertung per Buttons** (1–5 ⭐) statt Tippen, danach optionaler Feedback-Text.
- **Vouch-Leveling** (Bronze→Silver→Gold→Diamond) bleibt erhalten.

**Neue Channels** (im Setup `!Start`, Kategorie SHOP):
`♾️│infinityxeh`, `💉│fflags-injector`, `🛡️│anti-ban` — jeder mit eigenem
Showcase-Panel. Kanal-Gesamtzahl: 41 → **44**.

## Weitere Embeds umstellen (Vorlage)

Reines Info-Panel ohne Buttons:
```python
from bot.cogs.components_v2 import build_layout
view = build_layout(title="📢 News", body="Dein Text …", author=ctx.author)
await channel.send(view=view)
```

Panel mit eigenen Buttons + Logik (eigene Klasse):
```python
class MyView(discord.ui.LayoutView):
    def __init__(self):
        super().__init__(timeout=None)
        btn = discord.ui.Button(label="Klick", style=discord.ButtonStyle.success,
                                custom_id="my_btn")
        btn.callback = self.on_click
        self.add_item(PrestigeContainer("Titel", "Body", items=[btn]))

    async def on_click(self, interaction):
        await interaction.response.send_message("Hi!", ephemeral=True)
```
