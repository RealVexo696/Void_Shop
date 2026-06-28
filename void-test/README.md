# 𝗩𝗢𝗜𝗗 • Prestige Discord Bot 🚀 (24/7 Railway Ready)

Dieser Bot ist ein absolutes **Prestige-Meisterwerk** für Roblox- und Discord-Verkaufsshops. Er ist darauf ausgelegt, komplett stabil und vollautomatisiert **24/7 auf Railway** (oder ähnlichen Cloud-Diensten) gehostet zu werden.

Er enthält ein **integriertes Flask-Webportal**, welches dafür sorgt, dass der Bot permanent online bleibt, ohne einzuschlafen, sowie ein beispielloses **8-faches Premium-Logging-System** und ein **Multi-Kategorie Ticket-System**.

---

## ✨ Features

1. **👑 Alle Befehle als Slash Commands (/):**
   - `/setup` — Komplettes Server-Layout (23 Rollen, 42 Kanäle, Embeds)
   - `/verify` — Roblox Bio-Code Verifizierung
   - `/checkbuy` — Gamepass-Kaufprüfung über Roblox API
   - `/invites` — Invite-Statistik
   - `/status` — Server-Statistiken & Bot-Info
   - `/help` — Vollständige Befehlsübersicht

2. **📊 Hochmodernes 8-Kanal-Logging (`📁│── 𝗩𝗢𝗜𝗗 • 𝗟𝗢𝗚𝗦 ──`):**
   - `💬│voice-logs` ➔ Sprachkanal-Beitritt, Wechsel, Austritt
   - `🔨│ban-kick-logs` ➔ Banns, Kicks, Timeouts mit Audit-Log
   - `📝│message-logs` ➔ Gelöschte & bearbeitete Nachrichten
   - `📩│invite-logs` ➔ Einladungsnutzung live tracken
   - `📥│join-leave-logs` ➔ Serverbeitritte & Austritte
   - `💾│ticket-logs` ➔ Ticket-Transkripte als .txt
   - `⚙️│system-logs` ➔ Kanäle & Rollen Änderungen
   - `🚨│security-logs` ➔ Scam- & Phishing-Block

3. **🎨 Einzigartiges Prestige Embed-Design:**
   - **Author-Feld:** Ausführender Benutzer (Name + Avatar)
   - **Zitat-Layout:** Elegante Blockzitate (`>`)
   - **Footer-Branding:** Bot-Avatar + "Powered by BotForge" + Zeitstempel

4. **🎟️ Interaktives Multi-Kategorie Ticket-System:**
   - 🛒 Produkt kaufen → Kauf-Ticket mit Team-Ping
   - ⚙️ Allgemeiner Support → Support-Ticket
   - 🤝 Partnerschaft → Partner-Ticket

5. **🌐 Integrierter Flask-Webserver (24/7 Railway):**
   - Automatische Web-App im Hintergrund
   - Bindet an Railway `PORT` Variable

6. **🛡️ Verbessertes Rate-Limiting:**
   - 5 Retries mit exponentiellem Backoff
   - 1.5s Pause zwischen Rollen-Erstellungen
   - Zentrale `safe_role_create()` & `safe_channel_create()` Funktionen

---

## 📂 Projektstruktur

```
void-test-restructured/
├── bot.py                     # Einstiegspunkt (Railway Procfile → python bot.py)
├── requirements.txt           # Python Dependencies
├── Procfile                   # Railway: web: python bot.py
│
├── bot/                       # Bot-Modul
│   ├── __init__.py            # VoidShopBot Klasse, Slash-Commands Sync, Start
│   └── cogs/                  # Cogs (Modularisierte Befehle/Events)
│       ├── __init__.py
│       ├── database.py        # Persistente JSON-Datenbank
│       ├── embed_helper.py    # Einheitliche Prestige Embed Factory
│       ├── economy.py         # /verify, /checkbuy, /invites
│       ├── verification.py    # RobloxBioVerifyView, SimpleVerifyButton
│       ├── tickets.py         # Ticket-System, Close, Reviews, AddUser/RemoveUser
│       ├── setup.py           # /setup — Rollen, Kanäle, Embeds (mit Rate-Limit-Schutz)
│       ├── logging_events.py  # Alle Event-Listener (Logs, Anti-Scam, etc.)
│       ├── stats.py           # Stats-Channel-Updates & Status-Rotation
│       └── commands.py        # /status, /help
│
└── web/                       # Web-Modul
    ├── __init__.py            # Flask App (Basis)
    └── routes/
        ├── __init__.py
        └── api.py             # Flask Dashboard (1:1 Original-HTML) + /api/stats
```

---

## 🚀 Deployment auf Railway

### Schritt 1: Token eintragen
1. Gehe zu deinem Railway-Projekt
2. Öffne **Variables** → **Secrets**
3. Erstelle eine Variable: `DISCORD_TOKEN` = `DEIN_BOT_TOKEN`

### Schritt 2: Repository verbinden
1. Lade den Code auf GitHub hoch (Private Repo empfohlen)
2. Verbinde Railway mit dem GitHub Repo
3. Railway erkennt `Procfile` und `requirements.txt` automatisch

### Schritt 3: Bot-Rolle konfigurieren
1. Bot-Rolle in Server-Einstellungen **ganz nach oben** ziehen
2. **Administrator**-Berechtigung aktivieren
3. `/setup` mit Modus `reset` oder `add` ausführen

---

## ⚡ Befehlsübersicht

| Befehl | Beschreibung | Berechtigung |
|--------|-------------|--------------|
| `/setup <modus>` | Komplettes Server-Layout erstellen | Administrator |
| `/verify <username>` | Roblox-Account verifizieren | Jeder |
| `/checkbuy <user> <id>` | Gamepass-Kauf prüfen | Jeder |
| `/invites [user]` | Invite-Statistik | Jeder |
| `/status` | Server-Statistiken | Jeder |
| `/help` | Alle Befehle anzeigen | Jeder |

---

## 🔧 Rate-Limit Verbesserungen

- **Rollen-Erstellung:** 5 Retries + exponentielles Backoff + 1.5s Pause
- **Kanal-Erstellung:** Zentrale `safe_channel_create()` mit Retry-Logik
- **Discord API:** Alle externen Calls mit Fehlerbehandlung & Logging
- **Setup-Positionierung:** Rollen werden automatisch über der Bot-Position erstellt

---

## 📝 Alle Text-Embeds 1:1 Original

Keine Nachricht, kein Embed-Text wurde gekürzt oder verändert. Alles ist wortgleich zum Original.