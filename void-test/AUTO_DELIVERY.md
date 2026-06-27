# 🛒 Verkauf & Auto-Delivery — 𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣

## Ticket-System (gefixt)
- **Nur noch 3 Ticket-Typen**: 🛒 Produkt kaufen · ⚙️ Fragen / Support · 🤝 Partnerschaft
- Bei **„Produkt kaufen"** erscheint zuerst eine **Produkt-Auswahl mit Buttons**
  (INFINITYxEH · FFlags Injector · Anti-Ban) — der Kunde tippt **nichts** selbst.
- Ausverkaufte Produkte (0 Keys) werden im Auswahl-Menü automatisch ausgegraut.

## Produkte & Preise
| Produkt | Preis | Robux |
|---------|-------|-------|
| ♾️ INFINITYxEH | 750 R$ / 7,50 € | 750 |
| 💉 FFlags Injector | 300 R$ / 3,00 € | 300 |
| 🛡️ **Anti-Ban** | **1.000 R$ / 10,00 €** | **1000** |

## Auto-Delivery
1. Kunde öffnet Kauf-Ticket → wählt Produkt per Button.
2. Im Ticket erscheint ein **„✅ Kauf bestätigen & liefern"**-Panel (nur Team).
3. Nach Zahlungseingang klickt das Team den Button:
   - Ein **freier Lizenz-Key** wird aus dem Vorrat gezogen & als „benutzt" markiert.
   - Der Key wird dem Käufer **automatisch per DM** zugestellt (Fallback: im Ticket, falls DMs aus).
   - Die **Customer-Rolle** wird vergeben, der Verkauf wird protokolliert.

## Lizenz-Keys verwalten (Slash-Commands)
| Befehl | Wer | Funktion |
|--------|-----|----------|
| `/addkeys produkt:<…> keys:<k1, k2, …>` | Admin | Keys zum Vorrat hinzufügen |
| `/stock` | alle | Lagerbestand aller Produkte anzeigen |
| `/redeem key:<…>` | Kunde | Key selbst einlösen → Customer-Rolle + 25 Coins |
| `/sales` | Admin | Verkaufsstatistik (Umsatz gesamt/heute, Bestseller) |

**Beispiel Keys hinzufügen:**
```
/addkeys produkt:♾️ INFINITYxEH keys:INF-AAA-111, INF-BBB-222, INF-CCC-333
```

## Datenbank
Neue Felder in `shop_db.json`:
- `license_keys` → `{produkt: [{key, used, used_by, used_at}]}`
- `sales_log` → Liste aller Verkäufe (für `/sales`-Statistik)

## Wichtiger Bugfix
Ein **Deadlock** in der Datenbank wurde behoben: Methoden, die innerhalb von
`with self.lock:` speichern, nutzen jetzt `_save_unlocked()` statt `save()`
(der `threading.Lock` ist nicht reentrant — `save()` im Lock hätte den Bot eingefroren).

## Noch offen (auf Wunsch nachziehbar)
- 🛒 Warenkorb (mehrere Produkte / Mengenrabatt)
- 📊 Dashboard-Diagramme, Web-Login (Passwort), Ø-Antwortzeit
- ⭐ FAQ-Auto-Bot, Supporter des Monats, DE/EN-Sprachwahl
