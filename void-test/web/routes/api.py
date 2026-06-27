"""
Web Dashboard — Vollständiges Cloud Executive Center (1:1 Original)
"""

import threading
import os

from flask import Flask, jsonify
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
      --bg: #0a0b10;
      --panel: rgba(16, 18, 28, 0.85);
      --cyan: #00f0ff;
      --pink: #ff007f;
      --green: #39ff14;
      --gold: #ffd700;
      --text: #f0f4f8;
      --border: rgba(0, 240, 255, 0.22);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Roboto, sans-serif; }
    body { background: var(--bg); color: var(--text); padding: 1.5rem; min-height: 100vh; background-image: radial-gradient(circle at 10% 10%, rgba(0,240,255,0.06) 0%, transparent 40%), radial-gradient(circle at 90% 90%, rgba(255,0,127,0.06) 0%, transparent 40%); }
    header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--border); padding-bottom: 1.2rem; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem; }
    h1 { font-size: 2rem; letter-spacing: 2px; text-transform: uppercase; background: linear-gradient(90deg, var(--cyan), var(--pink)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 20px rgba(0,240,255,0.4); }
    .status-badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(57,255,20,0.12); border: 1px solid var(--green); padding: 8px 18px; border-radius: 30px; font-weight: bold; color: var(--green); box-shadow: 0 0 15px rgba(57,255,20,0.3); font-size: 0.85rem; }
    .status-dot { width: 10px; height: 10px; background: var(--green); border-radius: 50%; animation: pulse 1.5s infinite; }
    @keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.3; transform: scale(1.3); } 100% { opacity: 1; transform: scale(1); } }
    .tabs { display: flex; gap: 10px; margin-bottom: 2rem; flex-wrap: wrap; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; }
    .tab-btn { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #a0aec0; padding: 10px 20px; border-radius: 10px; cursor: pointer; font-weight: 600; transition: all 0.3s; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; }
    .tab-btn:hover, .tab-btn.active { background: rgba(0,240,255,0.15); border-color: var(--cyan); color: #fff; box-shadow: 0 0 15px rgba(0,240,255,0.3); }
    .tab-content { display: none; animation: fadeIn 0.4s ease; }
    .tab-content.active { display: block; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .card { background: var(--panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; padding: 1.6rem; position: relative; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
    .card::before { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px; background: linear-gradient(90deg, var(--cyan), var(--pink)); }
    .card-title { font-size: 0.85rem; text-transform: uppercase; color: #a0aec0; letter-spacing: 1px; margin-bottom: 0.6rem; font-weight: 600; }
    .card-value { font-size: 2.2rem; font-weight: 800; color: #fff; }
    .val-cyan { color: var(--cyan); } .val-green { color: var(--green); } .val-pink { color: var(--pink); } .val-gold { color: var(--gold); }
    .section-title { font-size: 1.3rem; margin-bottom: 1rem; color: var(--gold); font-weight: 700; display: flex; align-items: center; gap: 10px; }
    .table-container { background: var(--panel); backdrop-filter: blur(12px); border: 1px solid var(--border); border-radius: 16px; padding: 1.4rem; overflow-x: auto; margin-bottom: 2rem; }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th { padding: 12px 14px; border-bottom: 1px solid var(--border); color: var(--cyan); font-weight: 600; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px; }
    td { padding: 14px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.95rem; }
    tr:hover td { background: rgba(0,240,255,0.04); }
    .tag { background: rgba(0,240,255,0.15); border: 1px solid var(--cyan); padding: 4px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; }
    .split-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1.8rem; }
    @media(max-width: 900px) { .split-grid { grid-template-columns: 1fr; } }
    .log-nav { display: flex; gap: 8px; margin-bottom: 1.2rem; flex-wrap: wrap; }
    .log-btn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #cbd5e0; padding: 6px 14px; border-radius: 8px; cursor: pointer; font-size: 0.85rem; font-weight: 600; }
    .log-btn.active { background: var(--cyan); color: #000; font-weight: bold; }
    .log-box { background: #050608; border: 1px solid var(--border); border-radius: 12px; padding: 1.2rem; font-family: 'Consolas', monospace; font-size: 0.9rem; height: 420px; overflow-y: auto; line-height: 1.6; color: #a0aec0; }
    .log-entry { margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 4px; }
    .ticket-card { background: rgba(255,255,255,0.03); border: 1px solid rgba(0,240,255,0.3); padding: 12px 16px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
  </style>
</head>
<body>
  <header>
    <h1>👑 𝗩𝗢𝗜𝗗 • Cloud Executive Center</h1>
    <div class="status-badge"><div class="status-dot"></div> DISCORD & RAILWAY LIVE API</div>
  </header>

  <div class="tabs">
    <div class="tab-btn active" onclick="switchTab('overview', this)">📊 Übersicht</div>
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
        <div style="color:#a0aec0; margin-top:6px; font-size:0.9rem;" id="rev-euro">≈ 145,00 €</div>
      </div>
      <div class="card">
        <div class="card-title">👥 Server Mitglieder (Live)</div>
        <div class="card-value val-green" id="stat-mem">0</div>
        <div style="color:#a0aec0; margin-top:6px; font-size:0.9rem;"><span id="stat-on">0</span> Online / Idle</div>
      </div>
      <div class="card">
        <div class="card-title">🎟️ Aktive Tickets</div>
        <div class="card-value val-gold" id="stat-tix">0</div>
        <div style="color:#a0aec0; margin-top:6px; font-size:0.9rem;">Multi-Kategorie Panel</div>
      </div>
      <div class="card">
        <div class="card-title">🚨 Anti-Scam Phishing Block</div>
        <div class="card-value val-pink" id="scam-cnt">23</div>
        <div style="color:#a0aec0; margin-top:6px; font-size:0.9rem;">Schutzschild 100% Aktiv</div>
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
        <div class="table-container" id="purchases-feed" style="max-height: 380px; overflow-y: auto;"></div>
      </div>
    </div>
  </div>

  <!-- TAB 2: LOGS -->
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

  <!-- TAB 3: TICKETS & VERIFY -->
  <div id="tab-tickets" class="tab-content">
    <div class="grid">
      <div class="card">
        <div class="card-title">🔐 Verifizierte Kunden</div>
        <div class="card-value val-cyan" id="stat-ver">0</div>
        <div style="color:#a0aec0; margin-top:6px; font-size:0.9rem;">Erfolgreich freigeschaltet</div>
      </div>
      <div class="card">
        <div class="card-title">💎 Server Booster</div>
        <div class="card-value val-pink" id="stat-bst">0</div>
        <div style="color:#a0aec0; margin-top:6px; font-size:0.9rem;">Lounge Zugriff aktiv</div>
      </div>
    </div>
    <div class="section-title">🎟️ Live Aktive Support- & Kaufkanäle</div>
    <div class="table-container" id="tickets-list-container">Keine offenen Tickets vorhanden.</div>
  </div>

  <!-- TAB 4: ECONOMY -->
  <div id="tab-economy" class="tab-content">
    <div class="section-title">🪙 Void-Coins & Treuepunkte Leaderboard</div>
    <div class="table-container">
      <table>
        <thead><tr><th>Platz</th><th>Discord User-ID</th><th>Kontostand (Void-Coins)</th><th>Rang</th></tr></thead>
        <tbody id="economy-body"></tbody>
      </table>
    </div>
  </div>

  <!-- TAB 5: HEALTH -->
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
          pf.innerHTML += `<div style="padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.06); display:flex; justify-content:space-between;"><span style="color:#fff;">${p.user}<br><small style="color:var(--cyan);">${p.product}</small></span><span style="color:#718096;">${p.time}</span></div>`;
        });

        const eb = document.getElementById('economy-body');
        eb.innerHTML = '';
        let place = 1;
        const sortedCoins = Object.entries(data.coins).sort((a,b) => b[1] - a[1]);
        sortedCoins.forEach(([uid, coins]) => {
          eb.innerHTML += `<tr><td><strong>#${place++}</strong></td><td style="color:var(--cyan);">${uid}</td><td style="color:var(--gold); font-weight:bold;">🪙 ${coins} Coins</td><td>VIP Kunde</td></tr>`;
        });

        renderLogs();
      } catch(e) {}
    }
    updateDashboard();
    setInterval(updateDashboard, 5000);
  </script>
</body>
</html>"""


@app.route("/")
def home():
    return DASHBOARD_HTML


@app.route("/api/stats")
def api_stats():
    return db.get_dashboard_data(bot_instance)


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    t = threading.Thread(target=run_flask)
    t.start()
