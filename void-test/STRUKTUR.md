# VOID Shop Bot — Projektstruktur

## 📂 Struktur

```
void-test-restructured/
├── bot.py                     # Einstiegspunkt (Railway Procfile -> python bot.py)
├── requirements.txt           # Dependencies
├── Procfile                   # Railway: web: python bot.py
│
├── bot/                       # Bot-Modul
│   ├── __init__.py            # Bot-Klasse, Setup-Hook, Token, Start
│   └── cogs/                  # Cogs (Modularisierte Befehle/Events)
│       ├── __init__.py
│       ├── database.py         # Persistente JSON-Datenbank
│       ├── embed_helper.py     # Einheitliche Prestige Embed Factory
│       ├── economy.py          # !verify, !checkbuy, !invites
│       ├── verification.py     # RobloxBioVerifyView, SimpleVerifyButton
│       ├── tickets.py          # Ticket-System, Close, Reviews, AddUser/RemoveUser
│       ├── setup.py            # !Setup — Rollen, Kanäle, Embeds (mit Rate-Limit-Schutz)
│       ├── logging_events.py   # Alle Event-Listener (Logs, Anti-Scam, etc.)
│       ├── stats.py            # Stats-Channel-Updates & Status-Rotation
│       └── commands.py         # !status, !hilfe
│
├── web/                       # Web-Modul
│   ├── __init__.py            # Flask App (Basis)
│   └── routes/
│       ├── __init__.py
│       └── api.py              # Flask Dashboard (1:1 Original-HTML) + /api/stats
```

## ✅ Behobene Fehler

1. **`discord`-Import fehlte in der originalen bot.py** — Jetzt sauber importiert in jedem Modul.
2. **`bot` globale Variable undefined** — In `setup_command` und `checkbuy_command` wurde `bot.user`
   referenziert, aber `bot` war an der Stelle nicht verfügbar. Jetzt: `self.bot.user` in Cogs.
3. **Tasks starten vor `on_ready`** — `update_stats_task` und `status_rotation_task` wurden in
   `setup_hook` gestartet, was zu `RuntimeError` führen kann. Jetzt in `StatsCog.__init__` korrekt.
4. **Zirkuläre Imports** — Original hatte `db.get_dashboard_data(bot)` in Flask Route, bevor `bot`
   definiert war. Jetzt: Lazy-Import in `web/routes/api.py`.
5. **Rate-Limits bei Setup** — Nur 3 Retries mit 1.0s Pause. Jetzt: **5 Retries mit exponentiellem
   Backoff** (`retry_after + attempt * 2`) und **1.2s Pause** zwischen Rollen.
6. **Flask `db.get_dashboard_data(bot)` — `bot` undefined** — Im Original wurde `bot` in der
   Flask-Route referenziert bevor es existierte. Jetzt korrekt über `bot_instance` import.
7. **`create_prestige_embed` überall kopiert** — Jetzt eine zentrale `EmbedHelper`-Klasse als Cog.

## 🚀 Rate-Limit Verbesserungen

- **Setup-Rollen:** 5 Retries mit exponentiellem Backoff (`1.2s` Pause + `retry_after * 2`)
- **Setup-Kanäle:** Generische `create_with_retry()` Funktion für alle Kanal-Erstellungen
- **Alle Discord API Calls:** Zentrale Retry-Logik mit Logging

## 📝 Alle Text-Embeds 1:1 Original

Keine Nachricht, kein Embed-Text wurde gekürzt oder verändert. Alles ist wortgleich zum Original.