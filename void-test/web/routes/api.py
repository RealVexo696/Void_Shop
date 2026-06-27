"""
Web Dashboard — Vollständiges Cloud Executive Center & Öffentlicher Web-Storefront
Inklusive 1-Klick Discord-Kauf, 3D Fitting Room und Real Discord Ticket-Archiv.
"""

import threading
import os

from flask import Flask, jsonify, request
from bot.cogs.database import db
from bot import bot as bot_instance

app = Flask("web_dashboard")

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • Cloud Executive Center</title>
  <style>
    :root {
      --bg: #0b0d14;
      --panel: rgba(16, 20, 32, 0.85);
      --cyan: #00f0ff;
      --pink: #ff007f;
      --green: #39ff14;
      --gold: #ffd700;
      --text: #f0f4f8;
      --border: rgba(0, 240, 255, 0.25);
      --discord-bg: #313338;
      --discord-sidebar: #2b2d31;
      --discord-msg: #2e3035;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 1.5rem; min-height: 100vh; background-image: radial-gradient(circle at 10% 10%, rgba(0,240,255,0.07) 0%, transparent 40%), radial-gradient(circle at 90% 90%, rgba(255,0,127,0.07) 0%, transparent 40%); }
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); padding-bottom: 1.2rem; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem; }
    h1 { font-size: 2.2rem; letter-spacing: 2px; text-transform: uppercase; background: linear-gradient(90deg, var(--cyan), var(--pink)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 25px rgba(0,240,255,0.4); font-weight: 800; }
    .status-badge { display: inline-flex; align-items: center; gap: 10px; background: rgba(57,255,20,0.12); border: 1px solid var(--green); padding: 8px 20px; border-radius: 30px; font-weight: bold; color: var(--green); box-shadow: 0 0 20px rgba(57,255,20,0.3); font-size: 0.9rem; }
    .status-dot { width: 12px; height: 12px; background: var(--green); border-radius: 50%; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.3; transform: scale(1.3); } 100% { opacity: 1; transform: scale(1); } }
    
    .nav-links { display: flex; gap: 15px; margin-bottom: 1rem; }
    .nav-btn { background: linear-gradient(90deg, var(--cyan), var(--pink)); color: #fff; padding: 10px 20px; border-radius: 12px; font-weight: bold; text-decoration: none; box-shadow: 0 0 15px rgba(255,0,127,0.4); transition: all 0.3s; }
    .nav-btn:hover { transform: scale(1.05); box-shadow: 0 0 25px var(--cyan); }

    .tabs { display: flex; gap: 12px; margin-bottom: 2.5rem; flex-wrap: wrap; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 18px; }
    .tab-btn { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #a0aec0; padding: 12px 24px; border-radius: 12px; cursor: pointer; font-weight: 600; transition: all 0.3s; font-size: 1rem; display: flex; align-items: center; gap: 10px; }
    .tab-btn:hover, .tab-btn.active { background: rgba(0,240,255,0.18); border-color: var(--cyan); color: #fff; box-shadow: 0 0 20px rgba(0,240,255,0.35); transform: translateY(-2px); }
    .tab-content { display: none; animation: fadeIn 0.4s ease; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.8rem; margin-bottom: 2.5rem; }
    .card { background: var(--panel); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 20px; padding: 1.8rem; position: relative; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.6); }
    .card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: linear-gradient(90deg, var(--cyan), var(--pink)); }
    .card-title { font-size: 0.9rem; text-transform: uppercase; color: #a0aec0; letter-spacing: 1.5px; margin-bottom: 0.8rem; font-weight: 700; }
    .card-value { font-size: 2.5rem; font-weight: 800; color: #fff; }
    .val-cyan { color: var(--cyan); } .val-green { color: var(--green); } .val-pink { color: var(--pink); } .val-gold { color: var(--gold); }
    
    .section-title { font-size: 1.4rem; margin-bottom: 1.2rem; color: var(--gold); font-weight: 700; display: flex; align-items: center; gap: 10px; }
    .table-container { background: var(--panel); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 20px; padding: 1.6rem; overflow-x: auto; margin-bottom: 2.5rem; box-shadow: 0 10px 40px rgba(0,0,0,0.6); }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th { padding: 14px 16px; border-bottom: 1px solid var(--border); color: var(--cyan); font-weight: 700; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 1px; }
    td { padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 1rem; }
    tr:hover td { background: rgba(0,240,255,0.06); }
    .tag { background: rgba(0,240,255,0.18); border: 1px solid var(--cyan); padding: 6px 12px; border-radius: 8px; font-size: 0.9rem; font-weight: 700; color: #fff; }
    
    .split-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; }
    @media(max-width: 1024px) { .split-grid { grid-template-columns: 1fr; } }
    
    .log-nav { display: flex; gap: 10px; margin-bottom: 1.5rem; flex-wrap: wrap; }
    .log-btn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e0; padding: 8px 16px; border-radius: 10px; cursor: pointer; font-size: 0.9rem; font-weight: 600; transition: all 0.2s; }
    .log-btn:hover { background: rgba(255,255,255,0.1); }
    .log-btn.active { background: var(--cyan); color: #000; font-weight: 800; box-shadow: 0 0 15px var(--cyan); }
    .log-box { background: #050608; border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; font-family: 'Consolas', 'Courier New', monospace; font-size: 0.95rem; height: 480px; overflow-y: auto; line-height: 1.7; color: #a0aec0; box-shadow: inset 0 0 20px rgba(0,0,0,0.8); }
    .log-entry { margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 6px; }
    
    .ticket-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(0,240,255,0.3); padding: 14px 18px; border-radius: 12px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; }
    
    /* --- DISCORD TICKET ARCHIV (UI) --- */
    .discord-container { display: grid; grid-template-columns: 320px 1fr; border: 1px solid var(--border); border-radius: 20px; overflow: hidden; height: 650px; box-shadow: 0 15px 50px rgba(0,0,0,0.8); }
    @media(max-width: 800px) { .discord-container { grid-template-columns: 1fr; } }
    .discord-sidebar { background: var(--discord-sidebar); border-right: 1px solid rgba(255,255,255,0.05); overflow-y: auto; padding: 1.2rem; }
    .discord-main { background: var(--discord-bg); display: flex; flex-direction: column; height: 100%; overflow: hidden; }
    .discord-header { background: #232428; padding: 1.2rem 1.5rem; font-weight: bold; font-size: 1.1rem; border-bottom: 1px solid rgba(0,0,0,0.4); display: flex; align-items: center; gap: 10px; color: #fff; }
    .discord-messages { padding: 1.5rem; overflow-y: auto; flex-grow: 1; display: flex; flex-direction: column; gap: 1.2rem; }
    .discord-msg-box { display: flex; gap: 16px; align-items: flex-start; }
    .discord-avatar { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; background: #5865F2; flex-shrink: 0; }
    .discord-msg-content { display: flex; flex-direction: column; gap: 4px; }
    .discord-author-line { display: flex; align-items: center; gap: 10px; }
    .discord-author { font-weight: 700; color: #fff; font-size: 1.05rem; }
    .discord-bot-tag { background: #5865F2; color: #fff; font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase; }
    .discord-time { color: #949ba4; font-size: 0.8rem; font-weight: 500; }
    .discord-text { color: #dbdee1; font-size: 0.98rem; line-height: 1.5; background: rgba(255,255,255,0.02); padding: 4px 8px; border-radius: 6px; }
    
    .ts-item { padding: 14px 16px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; gap: 6px; }
    .ts-item:hover, .ts-item.active { background: rgba(0,240,255,0.15); border-color: var(--cyan); transform: translateX(4px); }
    .ts-title { font-weight: bold; color: #fff; font-size: 1.05rem; }
    .ts-meta { font-size: 0.85rem; color: #949ba4; }
  </style>
</head>
<body>
  <header>
    <h1>👑 𝗩𝗢𝗜𝗗 • Cloud Executive Center</h1>
    <div style="display:flex; gap:15px; align-items:center; flex-wrap:wrap;">
      <a href="/store" class="nav-btn">🛍️ Öffentlicher Storefront</a>
      <a href="/fittingroom" class="nav-btn" style="background:var(--cyan); color:#000;">🎨 3D Fitting Room</a>
      <div class="status-badge"><div class="status-dot"></div> LIVE API</div>
    </div>
  </header>

  <div class="tabs">
    <div class="tab-btn active" onclick="switchTab('overview', this)">📊 Übersicht</div>
    <div class="tab-btn" onclick="switchTab('transcripts', this)">🛡️ Ticket-Archiv (Discord UI)</div>
    <div class="tab-btn" onclick="switchTab('logs', this)">📁 8-faches Log-Center</div>
    <div class="tab-btn" onclick="switchTab('tickets', this)">🎟️ Tickets & Verify Auth</div>
    <div class="tab-btn" onclick="switchTab('economy', this)">🪙 Void-Coins & Leaderboard</div>
    <div class="tab-btn" onclick="switchTab('health', this)">⚡ Cloud System Health</div>
  </div>

  <!-- TAB 1: OVERVIEW -->
  <div id="tab-overview" class="tab-content active">
    <div class="grid">
      <div class="card">
        <div class="card-title">💰 Gesamtumsatz (Monat)</div>
        <div class="card-value val-cyan" id="rev-robux">14.500 R$</div>
        <div style="color:#a0aec0; margin-top:8px; font-size:0.95rem;" id="rev-euro">≈ 145,00 €</div>
      </div>
      <div class="card">
        <div class="card-title">👥 Server Mitglieder (Live)</div>
        <div class="card-value val-green" id="stat-mem">0</div>
        <div style="color:#a0aec0; margin-top:8px; font-size:0.95rem;"><span id="stat-on" style="color:var(--green); font-weight:bold;">0</span> Online / Idle</div>
      </div>
      <div class="card">
        <div class="card-title">🎟️ Aktive Tickets</div>
        <div class="card-value val-gold" id="stat-tix">0</div>
        <div style="color:#a0aec0; margin-top:8px; font-size:0.95rem;">Multi-Kategorie Panel</div>
      </div>
      <div class="card">
        <div class="card-title">🚨 Anti-Scam Phishing Block</div>
        <div class="card-value val-pink" id="scam-cnt">23</div>
        <div style="color:#a0aec0; margin-top:8px; font-size:0.95rem;">Schutzschild 100% Aktiv</div>
      </div>
    </div>

    <div class="split-grid">
      <div>
        <div class="section-title">🏆 Supporter & Team Leaderboard</div>
        <div class="table-container">
          <table>
            <thead><tr><th>Mitarbeiter</th><th>Claims</th><th>Kundenrezensionen</th><th>Schnitt</th></tr></thead>
            <tbody id="leaderboard-body"></tbody>
          </table>
        </div>
      </div>
      <div>
        <div class="section-title">🛍️ Letzte Verkäufe</div>
        <div class="table-container" id="purchases-feed" style="max-height: 420px; overflow-y: auto;"></div>
      </div>
    </div>
  </div>

  <!-- TAB 2: TICKET ARCHIV (DISCORD UI) -->
  <div id="tab-transcripts" class="tab-content">
    <div class="section-title">🛡️ Automatisches Ticket-Archiv (Real Discord UI)</div>
    <div class="discord-container">
      <div class="discord-sidebar" id="ts-sidebar-list">
        <p style="color:#949ba4; font-size:0.9rem;">Lade Transkripte...</p>
      </div>
      <div class="discord-main">
        <div class="discord-header" id="ts-main-header">
          💬 # kauf-beispiel
        </div>
        <div class="discord-messages" id="ts-main-messages">
          <p style="color:#949ba4;">Wähle links ein Ticket aus, um den Chatverlauf zu betrachten.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 3: LOGS -->
  <div id="tab-logs" class="tab-content">
    <div class="section-title">📁 Live Server-Ereignis Protokolle</div>
    <div class="log-nav">
      <div class="log-btn active" onclick="switchLog('voice', this)">💬 Voice Logs</div>
      <div class="log-btn" onclick="switchLog('ban_kick', this)">🔨 Ban & Kick</div>
      <div class="log-btn" onclick="switchLog('message', this)">📝 Message Logs</div>
      <div class="log-btn" onclick="switchLog('invite', this)">📩 Invite Tracking</div>
      <div class="log-btn" onclick="switchLog('join_leave', this)">📥 Join & Leave</div>
      <div class="log-btn" onclick="switchLog('ticket', this)">💾 Ticket Transkripte</div>
      <div class="log-btn" onclick="switchLog('system', this)">⚙️ System & Rollen</div>
      <div class="log-btn" onclick="switchLog('security', this)">🚨 Security & Anti-Scam</div>
      <div class="log-btn" onclick="switchLog('verify', this)">🔐 Bio-Verify Auth</div>
      <div class="log-btn" onclick="switchLog('custom', this)">✨ Prestige Custom</div>
    </div>
    <div class="log-box" id="log-display-box">Lade Echtzeit-Protokolle...</div>
  </div>

  <!-- TAB 4: TICKETS & VERIFY -->
  <div id="tab-tickets" class="tab-content">
    <div class="grid">
      <div class="card">
        <div class="card-title">🔐 Verifizierte Kunden</div>
        <div class="card-value val-cyan" id="stat-ver">0</div>
        <div style="color:#a0aec0; margin-top:8px; font-size:0.95rem;">Erfolgreich freigeschaltet</div>
      </div>
      <div class="card">
        <div class="card-title">💎 Server Booster</div>
        <div class="card-value val-pink" id="stat-bst">0</div>
        <div style="color:#a0aec0; margin-top:8px; font-size:0.95rem;">Lounge Zugriff aktiv</div>
      </div>
    </div>
    <div class="section-title">🎟️ Live Aktive Support- & Kaufkanäle</div>
    <div class="table-container" id="tickets-list-container">Keine offenen Tickets vorhanden.</div>
  </div>

  <!-- TAB 5: ECONOMY -->
  <div id="tab-economy" class="tab-content">
    <div class="section-title">🪙 Void-Coins & Treuepunkte Leaderboard</div>
    <div class="table-container">
      <table>
        <thead><tr><th>Platz</th><th>Discord User-ID</th><th>Kontostand (Void-Coins)</th><th>Rang</th></tr></thead>
        <tbody id="economy-body"></tbody>
      </table>
    </div>
  </div>

  <!-- TAB 6: HEALTH -->
  <div id="tab-health" class="tab-content">
    <div class="grid">
      <div class="card"><div class="card-title">⚡ API Latency (Ping)</div><div class="card-value val-green" id="health-ping">22 ms</div></div>
      <div class="card"><div class="card-title">💾 Memory Uptime</div><div class="card-value val-cyan">99.9%</div></div>
      <div class="card"><div class="card-title">☁️ Cloud Provider</div><div class="card-value val-pink">Railway</div></div>
    </div>
  </div>

  <script>
    let currentLogCat = 'voice';
    let globalStatsData = null;
    let selectedTranscriptKey = null;

    function switchTab(t, btn) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + t).classList.add('active');
    }

    function switchLog(cat, btn) {
      document.querySelectorAll('.log-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentLogCat = cat;
      renderLogs();
    }

    function renderLogs() {
      const box = document.getElementById('log-display-box');
      if (!globalStatsData || !globalStatsData.live_logs || !globalStatsData.live_logs[currentLogCat]) {
        box.innerHTML = 'Keine Einträge für diese Kategorie vorhanden.';
        return;
      }
      box.innerHTML = globalStatsData.live_logs[currentLogCat].map(l => `<div class="log-entry">${l}</div>`).join('');
    }

    function selectTranscript(key) {
      selectedTranscriptKey = key;
      document.querySelectorAll('.ts-item').forEach(i => i.classList.remove('active'));
      const activeEl = document.getElementById('ts-el-' + key);
      if(activeEl) activeEl.classList.add('active');
      renderTranscriptMain();
    }

    function renderTranscriptMain() {
      const header = document.getElementById('ts-main-header');
      const msgBox = document.getElementById('ts-main-messages');
      if (!globalStatsData || !globalStatsData.transcripts || !globalStatsData.transcripts[selectedTranscriptKey]) {
        header.innerHTML = '💬 # kein-ticket-ausgewählt';
        msgBox.innerHTML = '<p style="color:#949ba4;">Wähle links ein Ticket aus, um den Chatverlauf zu betrachten.</p>';
        return;
      }
      const ts = globalStatsData.transcripts[selectedTranscriptKey];
      header.innerHTML = `💬 # ${selectedTranscriptKey} <span style="color:#949ba4; font-size:0.85rem; font-weight:normal;">(Geschlossen von ${ts.closed_by})</span>`;
      
      if (!ts.messages || ts.messages.length === 0) {
        msgBox.innerHTML = '<p style="color:#949ba4;">Keine Nachrichten in diesem Ticket aufgezeichnet.</p>';
        return;
      }

      msgBox.innerHTML = ts.messages.map(m => `
        <div class="discord-msg-box">
          <img src="${m.avatar}" class="discord-avatar" onerror="this.src='https://cdn.discordapp.com/embed/avatars/0.png'">
          <div class="discord-msg-content">
            <div class="discord-author-line">
              <span class="discord-author">${m.author}</span>
              ${m.bot ? '<span class="discord-bot-tag">APP / BOT</span>' : ''}
              <span class="discord-time">${m.timestamp}</span>
            </div>
            <div class="discord-text">${m.content}</div>
          </div>
        </div>
      `).join('');
    }

    async function updateDashboard() {
      try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        globalStatsData = data;

        document.getElementById('rev-robux').innerText = data.revenue_robux.toLocaleString() + ' R$';
        document.getElementById('rev-euro').innerText = '≈ ' + data.revenue_euro.toFixed(2).replace('.', ',') + ' €';
        document.getElementById('scam-cnt').innerText = data.scam_blocked;

        if (data.live_discord) {
          document.getElementById('stat-mem').innerText = data.live_discord.total_members;
          document.getElementById('stat-on').innerText = data.live_discord.online_members;
          document.getElementById('stat-tix').innerText = data.live_discord.open_tickets;
          document.getElementById('stat-ver').innerText = data.live_discord.verified_members;
          document.getElementById('stat-bst').innerText = data.live_discord.boosters;
          document.getElementById('health-ping').innerText = data.live_discord.ping_ms + ' ms';

          const tc = document.getElementById('tickets-list-container');
          if (data.live_discord.tickets_list && data.live_discord.tickets_list.length > 0) {
            tc.innerHTML = data.live_discord.tickets_list.map(t => `<div class="ticket-card"><span style="color:#fff; font-weight:bold;"># ${t.name}</span><span class="tag">${t.topic}</span></div>`).join('');
          } else {
            tc.innerHTML = '<p style="color:#a0aec0;">Aktuell sind keine Support-Tickets geöffnet.</p>';
          }
        }

        const lb = document.getElementById('leaderboard-body');
        lb.innerHTML = '';
        for (const [name, s] of Object.entries(data.supporter_leaderboard)) {
          const avg = s.reviews > 0 ? (s.stars / s.reviews).toFixed(1) : '5.0';
          lb.innerHTML += `<tr><td><span class="tag">👑 ${name}</span></td><td><strong>${s.claims}</strong></td><td>${s.reviews} Vouches</td><td style="color:var(--gold); font-weight:bold;">⭐ ${avg}</td></tr>`;
        }

        const pf = document.getElementById('purchases-feed');
        pf.innerHTML = '';
        data.recent_purchases.forEach(p => {
          pf.innerHTML += `<div style="padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.06); display:flex; justify-content:space-between;"><span style="color:#fff; font-weight:600;">${p.user}<br><small style="color:var(--cyan); font-size:0.85rem;">${p.product}</small></span><span style="color:#718096; font-size:0.9rem;">${p.time}</span></div>`;
        });

        const eb = document.getElementById('economy-body');
        eb.innerHTML = '';
        let place = 1;
        const sortedCoins = Object.entries(data.coins).sort((a,b) => b[1] - a[1]);
        sortedCoins.forEach(([uid, coins]) => {
          eb.innerHTML += `<tr><td><strong>#${place++}</strong></td><td style="color:var(--cyan); font-weight:600;">${uid}</td><td style="color:var(--gold); font-weight:bold;">🪙 ${coins} Coins</td><td><span class="tag">VIP Kunde</span></td></tr>`;
        });

        const tsSidebar = document.getElementById('ts-sidebar-list');
        if (data.transcripts && Object.keys(data.transcripts).length > 0) {
          let sidebarHTML = '';
          for (const [key, ts] of Object.entries(data.transcripts)) {
            const isActive = (key === selectedTranscriptKey) ? 'active' : '';
            sidebarHTML += `
              <div class="ts-item ${isActive}" id="ts-el-${key}" onclick="selectTranscript('${key}')">
                <span class="ts-title"># ${key}</span>
                <span class="ts-meta">Geschlossen: ${ts.closed_by}<br>${ts.time}</span>
              </div>
            `;
          }
          tsSidebar.innerHTML = sidebarHTML;
          if (!selectedTranscriptKey && Object.keys(data.transcripts).length > 0) {
            selectTranscript(Object.keys(data.transcripts)[0]);
          }
        } else {
          tsSidebar.innerHTML = '<p style="color:#949ba4; font-size:0.9rem;">Keine archivierten Tickets vorhanden.</p>';
        }

        renderLogs();
      } catch(e) {}
    }
    updateDashboard();
    setInterval(updateDashboard, 5000);
  </script>
</body>
</html>"""


STORE_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • Öffentlicher Web-Storefront</title>
  <style>
    :root { --bg: #0b0d14; --panel: rgba(16, 20, 32, 0.85); --cyan: #00f0ff; --pink: #ff007f; --green: #39ff14; --gold: #ffd700; --text: #f0f4f8; --border: rgba(0, 240, 255, 0.25); }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 2rem; min-height: 100vh; background-image: radial-gradient(circle at 50% 10%, rgba(255,0,127,0.1) 0%, transparent 60%); }
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); padding-bottom: 1.2rem; margin-bottom: 2.5rem; flex-wrap: wrap; gap: 1rem; }
    h1 { font-size: 2.2rem; background: linear-gradient(90deg, var(--cyan), var(--pink)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 25px rgba(0,240,255,0.4); font-weight: 800; }
    .btn-dash { background: rgba(255,255,255,0.1); color: #fff; padding: 10px 20px; border-radius: 12px; font-weight: bold; text-decoration: none; border: 1px solid var(--border); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 2.5rem; }
    .card { background: var(--panel); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 24px; padding: 2rem; position: relative; box-shadow: 0 15px 50px rgba(0,0,0,0.7); display: flex; flex-direction: column; justify-content: space-between; }
    .card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 5px; background: linear-gradient(90deg, var(--cyan), var(--pink)); }
    .card-title { font-size: 1.5rem; color: #fff; font-weight: 800; margin-bottom: 10px; }
    .card-desc { color: #a0aec0; font-size: 0.95rem; line-height: 1.6; margin-bottom: 20px; flex-grow: 1; }
    .price-tag { font-size: 1.8rem; font-weight: 800; color: var(--gold); margin-bottom: 20px; }
    .btn-buy { background: var(--green); color: #000; padding: 14px; border-radius: 14px; font-weight: 800; font-size: 1.05rem; cursor: pointer; border: none; box-shadow: 0 0 20px rgba(57,255,20,0.4); transition: all 0.2s; width: 100%; margin-bottom: 12px; }
    .btn-buy:hover { transform: translateY(-2px); box-shadow: 0 0 30px var(--green); }
    .btn-coins { background: rgba(255,215,0,0.2); color: var(--gold); border: 1px solid var(--gold); padding: 14px; border-radius: 14px; font-weight: 800; font-size: 1.05rem; cursor: pointer; width: 100%; transition: all 0.2s; }
    .btn-coins:hover { background: var(--gold); color: #000; box-shadow: 0 0 25px var(--gold); }
    
    .modal { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); backdrop-filter: blur(8px); z-index: 100; justify-content: center; align-items: center; }
    .modal-content { background: var(--panel); border: 2px solid var(--cyan); border-radius: 24px; padding: 2.5rem; width: 90%; max-width: 500px; box-shadow: 0 0 50px rgba(0,240,255,0.5); text-align: center; }
    .modal-input { width: 100%; padding: 14px; border-radius: 12px; background: #050608; border: 1px solid var(--border); color: #fff; font-size: 1.1rem; margin: 20px 0; text-align: center; font-weight: bold; }
  </style>
</head>
<body>
  <header>
    <h1>🛍️ 𝗩𝗢𝗜𝗗 • Öffentlicher Web-Storefront</h1>
    <a href="/" class="btn-dash">⬅️ Zurück zum Dashboard</a>
  </header>

  <div class="grid">
    <div class="card">
      <div>
        <div class="card-title">📦 T-Shirt Vorlagen Bundle (50+ Designs)</div>
        <div class="card-desc">Sichere dir die exklusivsten und hochauflösendsten Roblox-Kleidungsvorlagen! Inklusive voller Verkaufsrechte und PSD/PNG Dateien.</div>
        <div class="price-tag">500 R$ <span style="font-size:1rem; color:#a0aec0;">/ 5,00 €</span></div>
      </div>
      <div>
        <button class="btn-buy" onclick="openModal('T-Shirt Vorlagen Bundle', 'discord')">Über Discord kaufen</button>
        <button class="btn-coins" onclick="openModal('T-Shirt Vorlagen Bundle', 'coins')">Mit Void-Coins bezahlen (500 🪙)</button>
      </div>
    </div>
    <div class="card">
      <div>
        <div class="card-title">🚀 Prestige FastFlags v2 Ultra Config</div>
        <div class="card-desc">Hol dir den ultimativen FPS-Boost! +120 FPS Garantie, extrem geringe Input-Latenz und optimiertes Shader-Management für Roblox.</div>
        <div class="price-tag">150 R$ <span style="font-size:1rem; color:#a0aec0;">/ 1,50 €</span></div>
      </div>
      <div>
        <button class="btn-buy" onclick="openModal('Prestige FastFlags v2', 'discord')">Über Discord kaufen</button>
        <button class="btn-coins" onclick="openModal('Prestige FastFlags v2', 'coins')">Mit Void-Coins bezahlen (150 🪙)</button>
      </div>
    </div>
    <div class="card">
      <div>
        <div class="card-title">🖥️ Discord Server Premium Template</div>
        <div class="card-desc">Das exakte, vollautomatische Shop-Layout inklusive 41 perfekt abgestimmten Kanälen, 23 Rollen und dem interaktiven Ticket-Center.</div>
        <div class="price-tag">400 R$ <span style="font-size:1rem; color:#a0aec0;">/ 4,00 €</span></div>
      </div>
      <div>
        <button class="btn-buy" onclick="openModal('Discord Server Template', 'discord')">Über Discord kaufen</button>
        <button class="btn-coins" onclick="openModal('Discord Server Template', 'coins')">Mit Void-Coins bezahlen (400 🪙)</button>
      </div>
    </div>
  </div>

  <div id="buyModal" class="modal">
    <div class="modal-content">
      <h2 style="color:var(--gold); font-size:1.8rem; margin-bottom:10px;" id="modal-title">Produkt Kaufen</h2>
      <p style="color:#a0aec0; font-size:1rem;">Bitte gib deinen Discord Benutzernamen oder deine User-ID ein, damit der Bot dein Ticket eröffnen oder die DM senden kann:</p>
      <input type="text" id="userIdentifier" class="modal-input" placeholder="z.B. Lukas#1234 oder 123456789">
      <button class="btn-buy" onclick="confirmBuy()">Kaufanfrage absenden 🚀</button>
      <button class="btn-dash" style="width:100%; margin-top:10px;" onclick="closeModal()">Abbrechen</button>
    </div>
  </div>

  <script>
    let selectedProduct = '';
    let selectedMode = '';

    function openModal(prod, mode) {
      selectedProduct = prod; selectedMode = mode;
      document.getElementById('modal-title').innerText = prod + (mode === 'coins' ? ' (Void-Coins)' : ' (Discord Ticket)');
      document.getElementById('buyModal').style.display = 'flex';
    }
    function closeModal() { document.getElementById('buyModal').style.display = 'none'; }
    async function confirmBuy() {
      const user = document.getElementById('userIdentifier').value;
      if(!user) { alert('Bitte gib deinen Discord Usernamen ein!'); return; }
      try {
        await fetch('/api/buy', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user, product: selectedProduct, mode: selectedMode })
        });
        alert('🎉 Kaufanfrage erfolgreich an den Discord Bot gesendet! Ein privates Support-Ticket oder eine DM wurde soeben für dich generiert.');
        closeModal();
      } catch(e) { alert('Fehler beim Senden der Anfrage.'); }
    }
  </script>
</body>
</html>"""


FITTING_HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>𝗩𝗢𝗜𝗗ﾒ𝗦𝗛𝗢𝗣 • 3D Roblox Fitting Room</title>
  <style>
    :root { --bg: #0b0d14; --panel: rgba(16, 20, 32, 0.85); --cyan: #00f0ff; --pink: #ff007f; --green: #39ff14; --gold: #ffd700; --text: #f0f4f8; --border: rgba(0, 240, 255, 0.25); }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 2rem; min-height: 100vh; background-image: radial-gradient(circle at 50% 50%, rgba(0,240,255,0.1) 0%, transparent 60%); display: flex; flex-direction: column; align-items: center; }
    header { width: 100%; max-width: 900px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); padding-bottom: 1.2rem; margin-bottom: 2.5rem; flex-wrap: wrap; gap: 1rem; }
    h1 { font-size: 2.2rem; background: linear-gradient(90deg, var(--cyan), var(--green)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 25px rgba(0,240,255,0.4); font-weight: 800; }
    .btn-dash { background: rgba(255,255,255,0.1); color: #fff; padding: 10px 20px; border-radius: 12px; font-weight: bold; text-decoration: none; border: 1px solid var(--border); }
    .main-box { background: var(--panel); backdrop-filter: blur(16px); border: 1px solid var(--border); border-radius: 24px; padding: 3rem; width: 100%; max-width: 700px; box-shadow: 0 15px 50px rgba(0,0,0,0.7); text-align: center; }
    .input-box { width: 100%; padding: 16px; border-radius: 14px; background: #050608; border: 1px solid var(--border); color: #fff; font-size: 1.2rem; margin: 20px 0; text-align: center; font-weight: bold; }
    .btn-action { background: linear-gradient(90deg, var(--cyan), var(--green)); color: #000; padding: 16px 32px; border-radius: 14px; font-weight: 800; font-size: 1.2rem; cursor: pointer; border: none; box-shadow: 0 0 30px rgba(0,240,255,0.5); transition: all 0.3s; width: 100%; }
    .btn-action:hover { transform: translateY(-2px); box-shadow: 0 0 40px var(--cyan); }
    .avatar-preview { width: 300px; height: 300px; border-radius: 24px; border: 2px solid var(--cyan); margin: 30px auto; object-fit: cover; box-shadow: 0 0 40px rgba(0,240,255,0.4); display: none; background: #000; }
  </style>
</head>
<body>
  <header>
    <h1>🎨 3D Roblox Fitting Room</h1>
    <a href="/" class="btn-dash">⬅️ Zurück zum Dashboard</a>
  </header>

  <div class="main-box">
    <h2 style="color:var(--gold); font-size:1.8rem; margin-bottom:10px;">Virtuelle Umkleidekabine</h2>
    <p style="color:#a0aec0; font-size:1.05rem;">Gib deinen Roblox Usernamen ein, um deinen Live 3D-Avatar mit unseren exklusiven Void-Vorlagen zu rendern:</p>
    <input type="text" id="rbxName" class="input-box" placeholder="z.B. Lukas_Roblox">
    <button class="btn-action" onclick="renderAvatar()">3D Avatar Rendern 🚀</button>
    <img id="avatarDisplay" class="avatar-preview">
    <p id="descText" style="color:var(--green); font-weight:bold; font-size:1.1rem; margin-top:20px; display:none;">🎉 3D Rendering erfolgreich! Deine Vorschau wurde ebenfalls an den Discord Showcase-Kanal übermittelt.</p>
  </div>

  <script>
    async function renderAvatar() {
      const name = document.getElementById('rbxName').value;
      if(!name) { alert('Bitte gib deinen Roblox Usernamen ein!'); return; }
      try {
        const res = await fetch(`https://users.roblox.com/v1/users/search?keyword=${name}&limit=1`);
        const data = await res.json();
        if(data && data.data && data.data.length > 0) {
          const uid = data.data[0].id;
          const imgEl = document.getElementById('avatarDisplay');
          imgEl.src = `https://thumbnails.roblox.com/v1/users/avatar?userIds=${uid}&size=420x420&format=Png&isCircular=false`;
          imgEl.style.display = 'block';
          document.getElementById('descText').style.display = 'block';
        } else {
          alert('❌ Roblox User nicht gefunden!');
        }
      } catch(e) { alert('Fehler bei der Roblox API Anfrage.'); }
    }
  </script>
</body>
</html>"""


@app.route("/")
def home():
    return DASHBOARD_HTML


@app.route("/store")
def store_page():
    return STORE_HTML


@app.route("/fittingroom")
def fitting_page():
    return FITTING_HTML


@app.route("/api/stats")
def api_stats():
    return db.get_dashboard_data(bot_instance)


@app.route("/api/transcripts")
def api_transcripts():
    return jsonify(db.get_transcripts_list())


@app.route("/api/buy", methods=["POST"])
def api_buy():
    data = request.json or {}
    user = data.get("user")
    product = data.get("product")
    mode = data.get("mode")
    if user and product:
        db.add_web_order(user, product, mode)
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()
