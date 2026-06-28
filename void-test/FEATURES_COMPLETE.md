# 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 — Vollständige Feature-Übersicht

Alle gewünschten Features sind gebaut, getestet und lauffähig.

---

## 🛒 Verkauf & Auto-Delivery

### Ticket-System (gefixt)
- **3 Ticket-Typen**: 🛒 Produkt kaufen · ⚙️ Fragen / Support · 🤝 Partnerschaft
- Bei „Produkt kaufen" → **Button-Auswahl** des Produkts (kein Tippen)

### Warenkorb (NEU)
- Im Kauf-Ticket erscheint ein **Warenkorb-Panel**.
- Per Klick mehrere Produkte hinzufügen / leeren.
- **Mengenrabatt automatisch**: 2 Artikel −10 % · 3 Artikel −15 % · 4+ Artikel −20 %.
- Gesamtpreis (R$ + €) wird live berechnet.

### Auto-Delivery + Lizenz-Keys
- Team klickt **„✅ Kauf bestätigen & liefern"** → alle Keys aus dem Warenkorb
  werden gezogen und dem Käufer **automatisch per DM** zugestellt.
- Fallback: bei deaktivierten DMs landen die Keys im Ticket-Log.
- Customer-Rolle wird vergeben, Verkauf wird protokolliert.

### Preise
| Produkt | Preis | Robux |
|---------|-------|-------|
| ♾️ INFINITYxEH | 750 R$ / 7,50 € | 750 |
| 💉 FFlags Injector | 300 R$ / 3,00 € | 300 |
| 🛡️ **Anti-Ban** | **1.000 R$ / 10,00 €** | **1000** |

### Key-Befehle
| Befehl | Wer | Funktion |
|--------|-----|----------|
| `/addkeys produkt keys` | Admin | Keys zum Vorrat hinzufügen |
| `/stock` | alle | Lagerbestand (🟢🟡🔴) |
| `/redeem key` | Kunde | Key einlösen → Rolle + 25 Coins |
| Lager-Anzeige | — | live im Web-Dashboard + `/stock` |

---

## 📊 Dashboard & Analytics

### Admin-Login (Passwort)
- Aufruf: **`https://DEINE-URL/admin`** → Passwort-Login.
- Passwort über Umgebungsvariable **`ADMIN_PASSWORD`** (Default: `voidadmin` — bitte ändern!).
- Session-Secret über **`SECRET_KEY`** setzen.

### Dashboard zeigt
- 💰 Umsatz gesamt / heute, 🛒 Verkäufe, 🏆 Bestseller
- 📈 **Umsatz-Diagramm (letzte 7 Tage)** (Balken)
- 🏆 **Tickets pro Supporter** (Balken)
- ⏱️ **Ø Antwortzeit** (Ticket-Öffnung → Claim)
- ⭐ **Ø Zufriedenheit** (aus Bewertungen)
- 📦 Lagerbestand & Verkäufe pro Produkt (Tabelle)
- Aktualisiert sich automatisch alle 15 Sek.

### Befehle für Statistik
| Befehl | Wer | Funktion |
|--------|-----|----------|
| `/sales` | Admin | Verkaufsstatistik |
| `/ticketstats` | Admin | Ø-Antwortzeit, Tickets/Supporter, Zufriedenheit |

---

## ⭐ Support-Qualität

### FAQ-Auto-Bot
- In Ticket-Kanälen beantwortet der Bot **häufige Fragen automatisch** (Keyword-basiert).
- Standard-Keywords: `preis`, `zahlung`, `lieferung`, `key`, `anti-ban`.
- `/faq` zeigt alle Einträge · `/setfaq keyword antwort` (Admin) pflegt sie.

### Supporter des Monats
- `/topsupporter` zeigt den Supporter mit den meisten Sternen.

### Sprach-Wahl DE/EN
- `/language` → 🇩🇪 Deutsch oder 🇬🇧 English (pro User gespeichert).

---

## ⚙️ Wichtige Umgebungsvariablen (Railway)

| Variable | Zweck | Default |
|----------|-------|---------|
| `DISCORD_TOKEN` | Bot-Token | — (Pflicht) |
| `ADMIN_PASSWORD` | Dashboard-Login | `voidadmin` |
| `SECRET_KEY` | Flask-Session-Secret | unsicherer Default |
| `PORT` | Web-Port | 8080 |

> ⚠️ **Wichtig:** `ADMIN_PASSWORD` und `SECRET_KEY` unbedingt in Railway setzen!

---

## ✅ Getestet
- Datenbank: Keys, Warenkorb, Ticket-Timing, FAQ, Sprache — alle ohne Deadlock.
- Warenkorb-Rabatt: 3 Artikel (2050 R$) → 15 % → **1742 R$** korrekt.
- Flask-Admin: Login/Logout, geschützte API (401 ohne Login), Charts-Daten.
- Bot lädt **8 Cogs, 20 Slash-Commands**, alle persistenten Views registrieren sauber.

## 🔧 Technische Hinweise
- Warenkorb-/Delivery-Buttons sind über `on_interaction` persistent (custom_id-basiert),
  funktionieren also auch nach Bot-Neustart.
- Alle neuen Ticket-Embeds sind **Components V2** (Container-Layout).
- Daten liegen in `shop_db.json` (auf Railway ggf. ephemer — für echten Dauerbetrieb
  später externes Volume/DB empfohlen).
