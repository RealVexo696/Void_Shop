# 𝗩𝗢𝗜𝗗 • Prestige Discord Bot 🚀 (24/7 Railway Ready)


Dieser Bot ist ein absolutes **Prestige-Meisterwerk** für Roblox- und Discord-Verkaufsshops. Er ist darauf ausgelegt, komplett stabil und vollautomatisiert **24/7 auf Railway** (oder ähnlichen Cloud-Diensten) gehostet zu werden.

Er enthält ein **integriertes Flask-Webportal**, welches dafür sorgt, dass der Bot permanent online bleibt, ohne einzuschlafen, sowie ein beispielloses **7-faches Premium-Logging-System** und ein **Multi-Kategorie Ticket-System**.

---

## ✨ Neue High-End Features im Prestige-Update

1. **👑 Dedizierter `!role` Befehl:**
   - Erstellt alle **22 Premium-Rollen** vollautomatisiert und prüft, ob sie bereits existieren, um Duplikate zu vermeiden.
   - Setzt im Anschluss **vollautomatisch alle Kanalberechtigungen (Rechte)** im gesamten Server für jede dieser 22 Rollen so ein, dass Kunden, VIPs, Teammitglieder und Booster exakt die für sie bestimmten Kanäle sehen und nutzen können.
   - Erkennt fehlende Admin-Rechte des Bots sofort und gibt eine **interaktive Schritt-für-Schritt-Anleitung**, wie man das Problem behebt!

2. **📊 Hochmodernes 7-Kanal-Logging (`📁│── 𝗩𝗢𝗜𝗗 • 𝗟𝗢𝗚𝗦 ──`):**
   Der Bot protokolliert jetzt absolut jede Aktion in spezialisierten, wunderschönen Embed-Nachrichten:
   - `💬│voice-logs` ➔ Protokolliert jeden Sprachkanal-Beitritt, Wechsel und Austritt von Mitgliedern.
   - `🔨│ban-kick-logs` ➔ Loggt Banns, Kicks und **Timeouts (Stummschaltungen)** live inklusive des verantwortlichen Moderators und des Grundes (sucht direkt im Audit-Log!).
   - `📝│message-logs` ➔ Protokolliert gelöschte und bearbeitete Nachrichten (zeigt exakt den Zustand *Zuvor* und *Danach*).
   - `📩│invite-logs` ➔ Registriert das Erstellen neuer Einladungen und **trackt live, welcher User mit welchem Invite-Link beigetreten ist**.
   - `📥│join-leave-logs` ➔ Dokumentiert jeden Beitritt (mit Account-Alter zur Erkennung von Fake-Accounts) und jedes Verlassen des Servers.
   - `💾│ticket-logs` ➔ Archiviert nach der Schließung eines Tickets ein vollständiges, formatiertes **Gesprächsprotokoll (Transkript)** als Textdatei.
   - `⚙️│system-logs` ➔ Dokumentiert jede Erstellung, Löschung oder Bearbeitung von Kanälen und Serverrollen.

3. **🎨 Einzigartiges Prestige Embed-Design:**
   - **Autor-Feld:** In absolut jedem Log und jeder Benachrichtigung ist der Autor des Embeds auf den ausführenden Benutzer (Name + Avatar-Icon) gesetzt.
   - **Zitat-Layout:** Alle Beschreibungen sind mit eleganten Blockzitaten (`>`) formatiert, was dem Server ein unverwechselbar sauberes, strukturiertes und ansprechendes Aussehen verleiht.
   - **Footer-Branding:** Jeder Footer ist mit dem Bot-Avatar und dem Schriftzug `Powered by BotForge` sowie einem Echtzeit-Zeitstempel versehen.

4. **🎟️ Interaktives Multi-Kategorie Ticket-System:**
   Das Ticket-Panel im Kanal `#🎟️│create-ticket` ist direkt in das Embed integriert und bietet 3 spezialisierte Knöpfe (Buttons):
   - ` Produkt kaufen` ➔ Erstellt ein Kauf-Ticket und pingt das Verkaufsteam.
   - ` Allgemeiner Support` ➔ Erstellt ein Support-Ticket für technische Fragen.
   - ` Partnerschaft` ➔ Erstellt ein Partnerschafts-Ticket für Kooperationen.

5. **🌐 Integrierter Flask-Webserver (24/7 Railway Online-Garantie):**
   - Der Bot startet im Hintergrund automatisch eine Web-App auf einem separaten Thread, welche an den von Railway verlangten `PORT` bindet.
   - Eine einfache Website zeigt "𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 Bot ist Online!", was verhindert, dass die Cloud den Bot schlafen legt.

---

## 📂 Enthaltene Projektdateien (für GitHub)

Wenn du das Projekt auf GitHub hochlädst, stelle sicher, dass du folgende Dateien hochlädst (sie sind bereits in deinem Arbeitsbereich erstellt):
1. 📄 **`bot.py`** – Die komplette, fehlerfreie Python-Datei mit allen Logik- und Server-Setups.
2. 📄 **`requirements.txt`** – Listet die benötigten Bibliotheken (`discord.py` und `Flask`).
3. 📄 **`Procfile`** – Sagt Railway ganz genau, welchen Befehl es ausführen muss, um den Bot und die Website zu starten.

---

## 🚀 Schritt-für-Schritt Anleitung: Auf GitHub hochladen & auf Railway hosten

### Schritt 1: Token eintragen
1. Öffne die Datei **`bot.py`** in einem Texteditor deiner Wahl.
2. Trage in **Zeile 30** deinen Discord-Bot-Token ein:
   ```python
   TOKEN = "DEIN_BOT_TOKEN_HIER"
   ```
3. Speichere die Datei ab.

### Schritt 2: Auf GitHub hochladen
1. Erstelle ein kostenloses Konto auf [GitHub](https://github.com/), falls du noch keines hast.
2. Klicke auf **"New Repository"**, gib ihm einen Namen (z.B. `void-shop-bot`) und stelle es auf **Private** (damit niemand deinen Token stehlen kann!).
3. Lade die drei Dateien (`bot.py`, `requirements.txt`, `Procfile`) direkt in das Repository hoch (entweder über das Terminal per Git oder ganz einfach per Drag & Drop im Browser auf GitHub).

### Schritt 3: Auf Railway hosten (24/7)
1. Erstelle ein Konto auf [Railway.app](https://railway.app/) (du kannst dich einfach mit deinem GitHub-Konto einloggen).
2. Klicke auf **"New Project"** ➔ **"Deploy from GitHub repo"**.
3. Wähle dein erstelltes, privates Repository (`void-shop-bot`) aus.
4. Klicke auf **"Deploy Now"**.
5. Railway erkennt das `Procfile` und die `requirements.txt` vollautomatisch, startet den Flask-Webserver, bindet die Website und startet den Bot im Hintergrund.
6. **Fertig!** Dein Bot läuft nun stabil 24/7 in der Cloud!

---

## ⚡ Befehle auf deinem Server ausführen

1. Stelle sicher, dass die Rolle des Bots (`𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣`) in den Rollen-Einstellungen deines Servers **ganz oben** steht und Admin-Rechte besitzt.
2. Führe als erstes den Befehl:
   ```text
   !role
   ```
   aus. Der Bot erstellt nun alle 22 Rollen und prüft, ob alles geklappt hat.
3. Führe im Anschluss den Befehl:
   ```text
   !Start
   ```
   aus, um alle Kategorien, Kanäle, Logos und Embed-Inhalte einzurichten!

---

## 🔮 Ideen & Vorschläge für die nächsten Upgrades:

Hier sind einige absolut geniale Ideen, die wir als nächstes für dich umsetzen können:

1. **🪙 Roblox-Verknüpfung (Roblox-Auth):**
   - Einbindung einer Verifizierung (z.B. über Bloxlink-API), sodass User ihren Roblox-Account mit dem Discord-Server verknüpfen müssen, um auf Kanäle zuzugreifen.
2. **🛍️ Automatisierter Roblox-Shop (Robux API):**
   - Einbindung eines automatischen Robux-Prüfers, der direkt über die Roblox-API checkt, ob der User das T-Shirt oder einen Gamepass gekauft hat, und ihm im Anschluss vollautomatisch die Rolle `🛒│ 𝗩𝗢𝗜𝗗 • 𝗖𝘂𝘀𝘁𝗼𝗺𝗲𝗿` und das Produkt liefert!
3. **📊 Server-Statistiken (Voice-Kanäle):**
   - Automatische Voice-Kanäle, die live die Server-Mitglieder, die Anzahl der Booster und die Verkäufe als Namen anzeigen (z.B. `👥│Mitglieder: 124`).
4. **🧠 Auto-Moderator (AI-Filter):**
   - Ein intelligenter Wortfilter, der Beleidigungen, Einladungs-Links zu anderen Servern oder Spam sofort blockiert, den Verursacher warnt und ihn nach 3 Verwarnungen automatisch stummschaltet.
5. **🎰 Server-Wirtschaft & Minispiele (Economy-System):**
   - Ein eigenes Punktesystem (z.B. `Void-Coins`), die Mitglieder durch tägliche Aktivität verdienen und im Shop gegen Rabatte oder T-Shirts einlösen können.

Lass mich einfach wissen, welche dieser Ideen wir als nächstes in deinen Bot einbauen sollen! ⚡
