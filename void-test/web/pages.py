"""
HTML-Seiten für VOID Shop.
Bewusst ohne Template-Engine gehalten, damit Railway/Preview einfach bleibt.
"""
from html import escape

DISCORD_INVITE_URL = "https://discord.gg/S7qpm4edEa"

PRODUCT_GROUP_LABELS = {
    "all": "Alle",
    "tools": "Tools",
    "templates": "Templates",
    "performance": "Performance",
    "server": "Server",
}

PRODUCT_GROUPS = {
    "infinityxeh": "tools",
    "fflags_injector": "tools",
    "anti_ban": "tools",
    "tshirt_templates": "templates",
    "fastflags_pack": "performance",
    "discord_template": "server",
}

PRODUCT_MOCKUPS = {
    "infinityxeh": "∞",
    "fflags_injector": "F",
    "anti_ban": "S",
    "tshirt_templates": "T",
    "fastflags_pack": "+FPS",
    "discord_template": "DC",
}

PRODUCT_FAQS = {
    "infinityxeh": [
        ("Wie wird geliefert?", "Nach Bestätigung erhältst du den Key per DM oder im Ticket."),
        ("Bekomme ich Hilfe beim Setup?", "Ja, Support läuft direkt im Ticket."),
    ],
    "fflags_injector": [
        ("Ist das schwer einzurichten?", "Nein, der Injector ist auf einfache Nutzung ausgelegt."),
        ("Hilft ihr bei Problemen?", "Ja, bei Setup-Fragen hilft das Team im Ticket."),
    ],
    "anti_ban": [
        ("Was kostet Anti-Ban?", "Anti-Ban kostet 1.000 R$ / 10,00 €."),
        ("Wie erhalte ich es?", "Nach Kaufbestätigung wird es über das Ticket/DM geliefert."),
    ],
    "tshirt_templates": [
        ("Was ist enthalten?", "50+ Roblox T-Shirt Vorlagen, je nach Paket als PNG/PSD."),
        ("Darf ich sie verwenden?", "Ja, das Paket ist für Creator und Verkauf gedacht."),
    ],
    "fastflags_pack": [
        ("Was bringt das Pack?", "Es enthält Performance-orientierte FastFlags für Roblox."),
        ("Gibt es Vorher/Nachher?", "Auf der Startseite findest du einen einfachen Vergleich."),
    ],
    "discord_template": [
        ("Was bekomme ich?", "Eine fertige Shop-Struktur mit Rollen, Kanälen und Ticket-Idee."),
        ("Kann ich es anpassen?", "Ja, das Template ist als Grundlage gedacht und kann angepasst werden."),
    ],
}

CHANGELOG = [
    ("2026-06-28", "Website aufgeräumt", "Neue Landingpage, Produktfilter, Detailseiten, Changelog und Partnerseite."),
    ("2026-06-28", "Shop-System erweitert", "6 Produkte, Warenkorb, Mengenrabatt und Unlimited-Produkte."),
    ("2026-06-28", "Admin-Tools", "Produktverwaltung, Statistik-APIs und bessere Verkaufsübersicht."),
]


def product_group(key):
    return PRODUCT_GROUPS.get(key, "tools")


def product_mockup(key):
    return PRODUCT_MOCKUPS.get(key, "V")


def base_head(title="VOID Shop — Roblox Tools, Templates & Support"):
    return f"""<!DOCTYPE html>
<html lang=\"de\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <meta name=\"theme-color\" content=\"#f7f4ef\" />
  <title>{escape(title)}</title>
  <script>
    (function(){{
      try{{
        var saved = localStorage.getItem('void-theme');
        var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', saved || (dark ? 'dark' : 'light'));
      }}catch(e){{document.documentElement.setAttribute('data-theme','light')}}
    }})();
  </script>
  <style>
    :root{{
      --bg:#f7f4ef;--surface:#fffdf9;--surface-2:#efe9df;--ink:#171717;--muted:#756d63;--muted-2:#9a9186;
      --line:#dfd6ca;--line-soft:rgba(30,26,22,.08);--accent:#8b6f47;--accent-soft:#ede2d2;--good:#2f7d55;
      --warn:#9c6b24;--bad:#a33c3c;--shadow:0 20px 70px rgba(28,24,20,.08);--nav:rgba(247,244,239,.82);
      --dark-btn:#151515;--dark-btn-text:#ffffff;
    }}
    html[data-theme=\"dark\"]{{
      --bg:#0f1012;--surface:#17191d;--surface-2:#202328;--ink:#f5f0e8;--muted:#aaa198;--muted-2:#827b72;
      --line:#2b2d31;--line-soft:rgba(255,255,255,.08);--accent:#c1a16d;--accent-soft:#2a241b;--good:#73c995;
      --warn:#d3a55c;--bad:#d47878;--shadow:0 24px 80px rgba(0,0,0,.34);--nav:rgba(15,16,18,.82);
      --dark-btn:#f5f0e8;--dark-btn-text:#111214;
    }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(16px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes float {{ 0%, 100% {{ transform:translateY(0px); }} 50% {{ transform:translateY(-8px); }} }}
    @keyframes pulseGlow {{ 0%, 100% {{ box-shadow:0 0 14px rgba(47,125,85,.28); }} 50% {{ box-shadow:0 0 28px rgba(47,125,85,.6); }} }}
    *{{box-sizing:border-box;margin:0;padding:0}}html{{scroll-behavior:smooth}}body{{background:radial-gradient(circle at 12% -10%,rgba(139,111,71,.12),transparent 30%),radial-gradient(circle at 90% 8%,rgba(47,125,85,.07),transparent 28%),var(--bg);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,\"Segoe UI\",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}}a{{text-decoration:none;color:inherit}}button{{font:inherit}}.wrap{{width:min(1120px,calc(100% - 40px));margin:0 auto}}
    section, .order-card, .product-card, .proof, .review, .offer, .step, .faq, .change-item, .status-card {{ animation:fadeIn 0.65s cubic-bezier(0.16,1,0.3,1) forwards; }}
    .mark, .mockup {{ animation:float 3.8s ease-in-out infinite; }}
    .nav-shell{{position:sticky;top:0;z-index:50;background:var(--nav);backdrop-filter:blur(20px);border-bottom:1px solid var(--line-soft)}}.nav{{height:72px;display:flex;align-items:center;justify-content:space-between;gap:18px}}.nav-left{{display:flex;align-items:center;gap:12px;min-width:238px}}.brand{{display:flex;align-items:center;gap:12px;font-weight:800;letter-spacing:-.04em}}.mark{{width:38px;height:38px;border-radius:14px;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:900;box-shadow:0 12px 30px rgba(0,0,0,.12)}}.brand small{{display:block;color:var(--muted);font-size:12px;font-weight:650;letter-spacing:.01em;margin-top:-5px}}.theme-toggle{{width:40px;height:36px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--ink);display:grid;place-items:center;cursor:pointer;transition:.18s ease}}.theme-toggle:hover{{transform:translateY(-1px);border-color:var(--accent)}}.theme-toggle .sun{{display:none}}html[data-theme=\"dark\"] .theme-toggle .sun{{display:inline}}html[data-theme=\"dark\"] .theme-toggle .moon{{display:none}}
    .links{{display:flex;align-items:center;gap:2px;border:1px solid var(--line);background:rgba(255,255,255,.35);padding:5px;border-radius:999px}}html[data-theme=\"dark\"] .links{{background:rgba(255,255,255,.04)}}.links a{{font-size:14px;font-weight:700;color:var(--muted);padding:9px 13px;border-radius:999px;transition:.18s ease}}.links a:hover{{background:var(--surface);color:var(--ink)}}.nav-actions{{display:flex;align-items:center;gap:10px}}.btn{{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:42px;padding:0 17px;border-radius:999px;border:1px solid var(--line);font-weight:800;font-size:14px;transition:.18s ease;white-space:nowrap;cursor:pointer}}.btn:hover{{transform:translateY(-1px)}}.btn-primary{{background:var(--dark-btn);color:var(--dark-btn-text);border-color:var(--dark-btn);box-shadow:0 14px 34px rgba(0,0,0,.13)}}.btn-secondary{{background:var(--surface);color:var(--ink)}}
    section{{padding:84px 0}}.eyebrow{{display:inline-flex;align-items:center;gap:8px;color:var(--accent);font-size:13px;font-weight:850;letter-spacing:.12em;text-transform:uppercase;margin-bottom:14px}}.eyebrow:before{{content:\"\";width:7px;height:7px;border-radius:50%;background:var(--accent)}}h1{{font-size:clamp(45px,7vw,86px);line-height:.96;letter-spacing:-.075em;font-weight:880;max-width:900px}}h2{{font-size:clamp(32px,4.3vw,56px);line-height:1.04;letter-spacing:-.06em;font-weight:850}}h3{{letter-spacing:-.035em}}.lead{{font-size:clamp(18px,2vw,22px);color:var(--muted);max-width:680px;margin-top:22px}}.section-top{{display:grid;grid-template-columns:minmax(0,.9fr) minmax(280px,.65fr);gap:32px;align-items:end;margin-bottom:32px}}.section-top p{{color:var(--muted);font-size:17px;max-width:560px}}
    .hero{{padding:94px 0 66px}}.hero-grid{{display:grid;grid-template-columns:minmax(0,1.08fr) minmax(340px,.72fr);gap:56px;align-items:center}}.hero-actions{{display:flex;gap:12px;flex-wrap:wrap;margin-top:32px}}.hero-note,.trust-row{{display:flex;gap:24px;flex-wrap:wrap;margin-top:34px;color:var(--muted);font-size:14px}}.hero-note b,.trust-row b{{display:block;color:var(--ink);font-size:18px;letter-spacing:-.04em}}.showcase,.panel{{background:var(--surface);border:1px solid var(--line);border-radius:34px;padding:14px;box-shadow:var(--shadow)}}.order-card{{border-radius:26px;background:linear-gradient(180deg,var(--surface-2),var(--surface));border:1px solid var(--line-soft);padding:26px;min-height:420px;display:flex;flex-direction:column;justify-content:space-between;overflow:hidden;position:relative}}.order-card:after{{content:\"\";position:absolute;right:-80px;top:-80px;width:220px;height:220px;border-radius:50%;background:rgba(139,111,71,.12)}}.small-label{{color:var(--muted);font-size:13px;font-weight:750;text-transform:uppercase;letter-spacing:.11em;margin-bottom:10px}}.order-card h3{{font-size:30px;margin-bottom:10px}}.order-card p{{color:var(--muted)}}.order-lines{{display:grid;gap:10px;margin:28px 0;position:relative;z-index:2}}.order-line{{display:flex;justify-content:space-between;gap:14px;padding:14px 0;border-bottom:1px solid var(--line-soft);font-size:15px}}.order-line span{{color:var(--muted)}}.order-line b{{font-weight:850}}.order-status{{position:relative;z-index:2;background:var(--ink);color:var(--bg);border-radius:18px;padding:16px;display:flex;align-items:center;justify-content:space-between;gap:16px}}.pulse{{width:10px;height:10px;border-radius:50%;background:var(--good);box-shadow:0 0 0 6px rgba(47,125,85,.18);animation:pulseGlow 2.2s infinite;}}
    .status-title{{margin-top:30px;color:var(--muted);font-size:13px;font-weight:850;letter-spacing:.12em;text-transform:uppercase}}.status-bar{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:10px}}.status-card{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;transition:.2s ease}}.status-card:hover{{transform:translateY(-2px);border-color:var(--accent);}}.status-card span{{color:var(--muted);font-size:13px}}.status-card strong{{display:block;font-size:20px;letter-spacing:-.04em;margin-top:3px}}.status-ok{{color:var(--good)}}
    .intro-panel{{background:var(--surface);border:1px solid var(--line);border-radius:24px;padding:34px;box-shadow:0 18px 50px rgba(0,0,0,.045);display:grid;grid-template-columns:1fr 1fr;gap:28px}}.intro-panel p{{color:var(--muted);font-size:17px}}.intro-footer{{grid-column:1/-1;border-top:1px solid var(--line);padding-top:18px;display:flex;justify-content:space-between;gap:16px;color:var(--muted);font-size:14px}}.intro-footer b{{color:var(--ink)}}.proof-grid,.review-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:16px}}.proof,.review,.offer,.step,.faq,.change-item{{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:22px;transition:.2s ease;}}.proof:hover,.review:hover,.step:hover,.faq:hover,.change-item:hover{{transform:translateY(-2px);border-color:var(--accent);}}.proof strong,.review strong{{display:block;font-size:18px;margin-bottom:4px}}.proof span,.review span,.offer p,.step p,.faq p,.change-item p{{color:var(--muted);font-size:15px}}.review small{{color:var(--muted-2)}}
    .offer-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.offer{{min-height:195px;transition:.18s ease}}.offer:hover,.product-card:hover{{transform:translateY(-4px);border-color:var(--accent);}}.offer-icon{{width:42px;height:42px;border-radius:16px;background:var(--accent-soft);display:grid;place-items:center;margin-bottom:18px}}.offer h3{{font-size:21px;margin-bottom:8px}}
    .products-shell{{background:var(--ink);color:var(--bg);border-radius:34px;padding:34px;box-shadow:var(--shadow);overflow:hidden;position:relative}}.products-shell:before{{content:\"\";position:absolute;inset:0;pointer-events:none;background:radial-gradient(circle at 88% 0%,rgba(193,161,109,.18),transparent 34%)}}.products-shell .section-top,.product-grid,.products-note,.filter-tabs{{position:relative;z-index:2}}.products-shell .eyebrow,.products-shell .section-top p{{color:rgba(247,244,239,.7)}}.products-shell .eyebrow:before{{background:rgba(247,244,239,.7)}}.filter-tabs{{display:flex;gap:8px;flex-wrap:wrap;margin:-6px 0 18px}}.filter-tab{{border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.06);color:rgba(247,244,239,.74);border-radius:999px;padding:9px 13px;font-weight:800;font-size:13px;cursor:pointer}}.filter-tab.active{{background:#f7f4ef;color:#151515}}
    .product-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}.product-card{{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.10);border-radius:22px;padding:20px;min-height:280px;display:flex;flex-direction:column;transition:.18s ease}}.product-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;margin-bottom:16px}}.mockup{{width:50px;height:50px;border-radius:18px;background:linear-gradient(135deg,rgba(255,255,255,.18),rgba(255,255,255,.04));display:grid;place-items:center;font-weight:900;font-size:18px}}.tag{{font-size:12px;color:#d9c8a8;border:1px solid rgba(217,200,168,.24);background:rgba(217,200,168,.08);border-radius:999px;padding:5px 9px}}.product-card h3{{font-size:22px;margin-bottom:8px}}.product-card p{{color:rgba(247,244,239,.68);font-size:15px;flex:1}}.price{{margin-top:22px;display:flex;align-items:end;justify-content:space-between;gap:12px}}.price strong{{font-size:23px}}.price span{{display:block;color:rgba(247,244,239,.55);font-size:13px}}.availability{{color:#a7d8b9;background:rgba(47,125,85,.18);border:1px solid rgba(47,125,85,.28);padding:5px 9px;border-radius:999px;font-size:12px}}.product-actions{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:16px}}.product-action{{background:#f7f4ef;color:#151515;border-radius:13px;padding:11px 12px;text-align:center;font-weight:850;font-size:13px;transition:.18s ease}}.product-action.secondary{{background:rgba(255,255,255,.08);color:#f7f4ef;border:1px solid rgba(255,255,255,.12)}}.product-action:hover{{transform:translateY(-1px)}}.products-note{{margin-top:18px;padding-top:18px;border-top:1px solid rgba(255,255,255,.11);display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;color:rgba(247,244,239,.62);font-size:14px}}
    .compare{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:18px}}.compare-card{{background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:22px}}.compare-card strong{{display:block;font-size:22px;margin-bottom:6px}}.compare-card span{{color:var(--muted)}}.meter{{height:9px;background:var(--surface-2);border-radius:999px;margin-top:18px;overflow:hidden}}.meter i{{display:block;height:100%;border-radius:999px;background:var(--accent)}}.meter.good i{{background:var(--good)}}
    .steps{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.num{{width:34px;height:34px;border-radius:50%;background:var(--ink);color:var(--bg);display:grid;place-items:center;font-weight:900;margin-bottom:18px}}.step h3{{font-size:18px;margin-bottom:7px}}.faq-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}details.faq{{cursor:pointer}}details.faq summary{{font-weight:850;list-style:none}}details.faq summary::-webkit-details-marker{{display:none}}details.faq p{{margin-top:10px}}.cta{{background:var(--surface);border:1px solid var(--line);border-radius:32px;padding:38px;display:grid;grid-template-columns:1fr auto;align-items:center;gap:28px;box-shadow:var(--shadow)}}.cta p{{color:var(--muted);font-size:17px;margin-top:10px;max-width:680px}}
    .detail-grid{{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:24px;align-items:start}}.detail-card{{background:var(--surface);border:1px solid var(--line);border-radius:28px;padding:30px;box-shadow:var(--shadow)}}.detail-price{{font-size:34px;font-weight:900;letter-spacing:-.05em;margin:18px 0 6px}}.detail-list{{display:grid;gap:10px;margin:22px 0}}.detail-list li{{list-style:none;padding:13px 0;border-bottom:1px solid var(--line);color:var(--muted)}}.detail-list b{{color:var(--ink)}}.change-list{{display:grid;gap:12px}}.partner-box{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}footer{{border-top:1px solid var(--line-soft);padding:38px 0;color:var(--muted);font-size:14px}}.footer-grid{{display:grid;grid-template-columns:1.2fr repeat(4,auto);gap:24px;align-items:start}}.footer-grid h4{{color:var(--ink);margin-bottom:8px}}.footer-grid a{{display:block;margin:5px 0;text-decoration:underline;text-underline-offset:4px}}
    @media(max-width:940px){{.links{{display:none}}.nav-left{{min-width:auto}}.hero-grid,.section-top,.intro-panel,.proof-grid,.review-grid,.offer-grid,.product-grid,.steps,.faq-grid,.cta,.status-bar,.detail-grid,.partner-box,.compare,.footer-grid{{grid-template-columns:1fr}}.hero{{padding-top:58px}}.showcase{{max-width:520px}}.nav-actions .btn-secondary{{display:none}}.products-shell{{padding:24px;border-radius:26px}}}}
    @media(max-width:540px){{.wrap{{width:min(100% - 24px,1120px)}}.nav{{height:66px}}.brand small{{display:none}}.mark{{width:35px;height:35px}}.theme-toggle{{width:38px;height:34px}}.hero-actions .btn,.cta .btn{{width:100%}}.hero-note,.trust-row{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.intro-footer,.products-note{{flex-direction:column}}.order-card{{min-height:390px;padding:22px}}section{{padding:62px 0}}.product-actions{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
"""


def nav():
    return f"""
  <div class=\"nav-shell\">
    <nav class=\"nav wrap\">
      <div class=\"nav-left\">
        <a class=\"brand\" href=\"/\" aria-label=\"VOID Shop Startseite\">
          <span class=\"mark\">V</span><span>VOID Shop<small>Roblox Tools & Templates</small></span>
        </a>
        <button class=\"theme-toggle\" id=\"themeToggle\" type=\"button\" aria-label=\"Hell/Dunkel umschalten\" title=\"Hell/Dunkel\"><span class=\"moon\">☾</span><span class=\"sun\">☀</span></button>
      </div>
      <div class=\"links\" aria-label=\"Navigation\">
        <a href=\"/#about\">Wer wir sind</a><a href=\"/#offer\">Leistungen</a><a href=\"/#products\">Produkte</a><a href=\"/leaderboard\">Hall of Fame</a><a href=\"/verify\">Verifizierung</a><a href=\"/changelog\">Changelog</a>
      </div>
      <div class=\"nav-actions\"><a class=\"btn btn-secondary\" href=\"/store\">Store</a><a class=\"btn btn-primary\" href=\"{DISCORD_INVITE_URL}\">Discord beitreten</a></div>
    </nav>
  </div>
"""


def theme_script():
    return """
  <script>
    (function(){
      var btn=document.getElementById('themeToggle');var meta=document.querySelector('meta[name="theme-color"]');
      function apply(theme){document.documentElement.setAttribute('data-theme',theme);try{localStorage.setItem('void-theme',theme)}catch(e){} if(meta) meta.setAttribute('content',theme==='dark'?'#0f1012':'#f7f4ef');}
      if(btn){btn.addEventListener('click',function(){var c=document.documentElement.getAttribute('data-theme')||'light';apply(c==='dark'?'light':'dark');});}
      apply(document.documentElement.getAttribute('data-theme')||'light');
      document.querySelectorAll('[data-filter]').forEach(function(btn){btn.addEventListener('click',function(){var f=btn.getAttribute('data-filter');document.querySelectorAll('[data-filter]').forEach(function(b){b.classList.toggle('active',b===btn)});document.querySelectorAll('[data-group]').forEach(function(card){card.style.display=(f==='all'||card.getAttribute('data-group')===f)?'flex':'none';});});});
      function loadStatus(){fetch('/api/site/status').then(function(r){return r.json()}).then(function(d){
        var map={bot:d.bot_online?'Online':'Offline',tickets:d.open_tickets,products:d.products_available,support:d.avg_response};
        Object.keys(map).forEach(function(k){var el=document.querySelector('[data-status="'+k+'"]');if(el)el.textContent=map[k];});
      }).catch(function(){});fetch('/api/products').then(function(r){return r.json()}).then(function(d){Object.keys(d.products||{}).forEach(function(k){var el=document.querySelector('[data-stock="'+k+'"]');if(el)el.textContent=d.products[k].stock_label;});}).catch(function(){});} loadStatus(); setInterval(loadStatus,30000);
      window.openTicketHelp=function(){var m=document.getElementById('ticketHelpModal'); if(m)m.style.display='flex';};
      window.closeTicketHelp=function(){var m=document.getElementById('ticketHelpModal'); if(m)m.style.display='none';};
    })();
  </script>
</body>
</html>"""


def render_product_cards(products, best_key=None):
    cards = []
    for key, p in products.items():
        group = product_group(key)
        tag = PRODUCT_GROUP_LABELS.get(group, group.title())
        if best_key == key:
            tag = "Bestseller"
        stock = p.get("stock_label", "auf Lager")
        badges = " ".join(f"<span class=\"tag\">{escape(b)}</span>" for b in p.get("badges", [tag])[:3])
        cards.append(f"""
          <article class=\"product-card\" data-group=\"{escape(group)}\" data-product=\"{escape(key)}\">
            <div class=\"product-head\"><div class=\"mockup\">{escape(product_mockup(key))}</div><div style=\"display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end\">{badges}</div></div>
            <h3>{escape(p['name'])}</h3><p>{escape(p['desc'])}</p>
            <div class=\"price\"><div><strong>{escape(str(p['robux']))} R$</strong><span>{escape(p.get('euro', p['price'].split('/')[-1].strip()))}</span></div><span class=\"availability\" data-stock=\"{escape(key)}\">{escape(stock)}</span></div>
            <div class=\"product-actions\"><a class=\"product-action\" href=\"/product/{escape(key)}\">Details</a><button class=\"product-action secondary\" onclick=\"openTicketHelp()\">In Discord kaufen</button></div>
          </article>""")
    return "\n".join(cards)



def render_compare_rows(products=None):
    rows = [
        "<tr><td style='padding:14px;border-bottom:1px solid var(--line)'><b>♾️ INFINITYxEH</b></td><td style='padding:14px;border-bottom:1px solid var(--line)'>750 R$</td><td style='padding:14px;border-bottom:1px solid var(--line)'><span class='availability'>Ja</span></td><td style='padding:14px;border-bottom:1px solid var(--line)'>Auto</td><td style='padding:14px;border-bottom:1px solid var(--line)'>Tools</td></tr>",
        "<tr><td style='padding:14px;border-bottom:1px solid var(--line)'><b>🛡️ Anti-Ban</b></td><td style='padding:14px;border-bottom:1px solid var(--line)'>1000 R$</td><td style='padding:14px;border-bottom:1px solid var(--line)'><span class='availability'>Ja/Unlimited</span></td><td style='padding:14px;border-bottom:1px solid var(--line)'>Auto</td><td style='padding:14px;border-bottom:1px solid var(--line)'>Schutz</td></tr>",
        "<tr><td style='padding:14px;border-bottom:1px solid var(--line)'><b>🖥️ Discord Template</b></td><td style='padding:14px;border-bottom:1px solid var(--line)'>400 R$</td><td style='padding:14px;border-bottom:1px solid var(--line)'><span class='availability' style='background:rgba(139,111,71,.18);color:var(--ink)'>Nein/Unlimited</span></td><td style='padding:14px;border-bottom:1px solid var(--line)'>Ticket</td><td style='padding:14px;border-bottom:1px solid var(--line)'>Server</td></tr>",
    ]
    return "".join(rows)


def render_recent_sales(status):
    sales = status.get('recent_sales', [])
    if not sales:
        samples = [
            ("🛡️ Anti-Ban", "gekauft vor 12 Minuten"),
            ("🚀 FastFlags Pack", "gekauft vor 1 Stunde"),
            ("🖥️ Discord Server Template", "gekauft gestern"),
        ]
        return "".join(f"<article class='change-item' style='display:flex;justify-content:space-between;align-items:center'><strong>{escape(prod)}</strong><span class='availability'>{escape(time_txt)}</span></article>" for prod, time_txt in samples)
    return "".join(f"<article class='change-item' style='display:flex;justify-content:space-between;align-items:center'><strong>{escape(x.get('product_name','Produkt'))}</strong><span class='availability'>{escape(x.get('text', f'gekauft {x.get('time','vor kurzem')}' ))}</span></article>" for x in sales)

def render_landing(products, status, best_key=None):
    bot_state = "Online" if status.get("bot_online") else "Offline"
    fs = status.get('flash_sale', {})
    fs_banner = ""
    if fs and fs.get("active"):
        fs_banner = f"""
  <div style=\"background:linear-gradient(90deg,#8a1a1a,#d43838,#8a1a1a);background-size:200% auto;color:#fff;text-align:center;padding:14px;font-weight:850;font-size:15px;letter-spacing:-.01em;box-shadow:0 10px 30px rgba(163,60,60,.35)\">
    🔥 BLITZANGEBOT: 🛡️ Anti-Ban ab sofort −{escape(str(fs.get('discount',25)))}% REDUZIERT! <span style=\"margin-left:12px;background:#fff;color:#a33c3c;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:900\">Endet in 18:42 Min</span>
  </div>"""
    html = base_head() + fs_banner + nav() + f"""
  <main id=\"top\">
    <header class=\"hero wrap\">
      <div class=\"hero-grid\">
        <div>
          <div class=\"eyebrow\">VOID Shop</div>
          <h1>Digitale Roblox-Produkte, klar sortiert und zuverlässig geliefert.</h1>
          <p class=\"lead\">Ein ruhiger Shop für Tools, Vorlagen und Server-Setups — mit privaten Tickets, transparenter Preisübersicht und persönlichem Support.</p>
          <div class=\"hero-actions\"><a class=\"btn btn-primary\" href=\"#products\">Produkte ansehen</a><a class=\"btn btn-secondary\" href=\"{DISCORD_INVITE_URL}\">Discord beitreten</a></div>
          <div class=\"hero-note\"><div><b>6 Produkte</b>übersichtlich sortiert</div><div><b>Private Tickets</b>saubere Abwicklung</div><div><b>Rabatt</b>bei mehreren Artikeln</div></div>
          <div class=\"status-title\">Live-Status</div>
          <div class=\"status-bar\">
            <div class=\"status-card\"><span>Bot</span><strong class=\"status-ok\" data-status=\"bot\">{escape(bot_state)}</strong></div>
            <div class=\"status-card\"><span>Tickets offen</span><strong data-status=\"tickets\">{escape(str(status.get('open_tickets', 0)))}</strong></div>
            <div class=\"status-card\"><span>Produkte verfügbar</span><strong data-status=\"products\">{escape(str(status.get('products_available', 0)))}</strong></div>
            <div class=\"status-card\"><span>Antwort meist</span><strong data-status=\"support\">{escape(status.get('avg_response', '—'))}</strong></div>
          </div>
        </div>
        <aside class=\"showcase\"><div class=\"order-card\"><div><div class=\"small-label\">Bestellung</div><h3>Einfacher Ablauf. Keine Umwege.</h3><p>Produkt wählen, Ticket öffnen, Zahlung klären und Lieferung erhalten.</p><div class=\"order-lines\"><div class=\"order-line\"><span>Ticket</span><b>privat</b></div><div class=\"order-line\"><span>Lieferung</span><b>automatisch</b></div><div class=\"order-line\"><span>Support</span><b>DE / EN</b></div></div></div><div class=\"order-status\"><span><b>Shop aktiv</b><br><small>bereit für neue Anfragen</small></span><i class=\"pulse\"></i></div></div></aside>
      </div>
    </header>

    <section id=\"about\" class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Wer wir sind</div><h2>Ein kompakter Shop mit Fokus auf Übersicht.</h2></div><p>VOID Shop ist bewusst schlicht aufgebaut. Statt überladener Versprechen gibt es klare Produkte, klare Preise und einen nachvollziehbaren Kaufprozess über Discord.</p></div><div class=\"intro-panel\"><p>Jede Bestellung läuft über ein privates Ticket. So bleiben Produktwahl, Zahlung, Lieferung und Rückfragen an einem Ort.</p><p>Das Sortiment ist klein gehalten: Performance-Tools, Schutz, Templates und fertige Server-Strukturen.</p><div class=\"intro-footer\"><span><b>VOID Shop</b> · Roblox Tools, Templates & Support</span><span>Schlicht. Direkt. Verlässlich.</span></div></div><div class=\"proof-grid\"><div class=\"proof\"><strong>Private Tickets</strong><span>Jede Anfrage bekommt einen eigenen Bereich.</span></div><div class=\"proof\"><strong>Auto Delivery</strong><span>Lieferung nach Bestätigung per DM oder Ticket.</span></div><div class=\"proof\"><strong>Warenkorb-Rabatt</strong><span>2 Artikel −10%, 3 Artikel −15%, 4+ Artikel −20%.</span></div></div></section>

    <section id=\"offer\" class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Leistungen</div><h2>Was du bei uns bekommst.</h2></div><p>Ein sauberer digitaler Kaufprozess: verständlich, privat und ohne unnötige Ablenkung.</p></div><div class=\"offer-grid\"><article class=\"offer\"><div class=\"offer-icon\">🎟️</div><h3>Ticket-System</h3><p>Bestellungen, Support und Partner-Anfragen laufen getrennt.</p></article><article class=\"offer\"><div class=\"offer-icon\">📦</div><h3>Auto-Delivery</h3><p>Keys und digitale Produkte werden nach Bestätigung schnell zugestellt.</p></article><article class=\"offer\"><div class=\"offer-icon\">🛒</div><h3>Warenkorb</h3><p>Mehrere Produkte, Mengenrabatt inklusive.</p></article><article class=\"offer\"><div class=\"offer-icon\">🧾</div><h3>Klare Preise</h3><p>Robux- und Europreise ohne versteckte Schritte.</p></article><article class=\"offer\"><div class=\"offer-icon\">💬</div><h3>Support</h3><p>Fragen zu Setup, Nutzung und Lieferung werden direkt beantwortet.</p></article><article class=\"offer\"><div class=\"offer-icon\">🌐</div><h3>DE / EN</h3><p>Sprachwahl im Bot für verständlicheren Support.</p></article></div></section>

    <section id=\"products\" class=\"wrap\"><div class=\"products-shell\"><div class=\"section-top\"><div><div class=\"eyebrow\">Produkte</div><h2>Sechs Produkte. Sauber filterbar.</h2></div><p>Wähle eine Kategorie oder öffne direkt eine Detailseite. Kauf läuft über den Store/Discord.</p></div><div class=\"filter-tabs\"><button class=\"filter-tab active\" data-filter=\"all\">Alle</button><button class=\"filter-tab\" data-filter=\"tools\">Tools</button><button class=\"filter-tab\" data-filter=\"templates\">Templates</button><button class=\"filter-tab\" data-filter=\"performance\">Performance</button><button class=\"filter-tab\" data-filter=\"server\">Server</button></div><div class=\"product-grid\">{render_product_cards(products, best_key)}</div><div class=\"products-note\"><span>Mengenrabatt: 2 Artikel −10% · 3 Artikel −15% · 4+ Artikel −20%</span><span>Bestseller wird automatisch aus Verkäufen markiert.</span></div></div></section>

    <section class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Vergleich</div><h2>Alle Produkte auf einen Blick.</h2></div><p>Preis, Key-Status, Lieferung und Zielgruppe direkt vergleichbar.</p></div><div class=\"detail-card\" style=\"overflow:auto\"><table style=\"width:100%;border-collapse:collapse;min-width:720px\"><thead><tr><th style=\"text-align:left;padding:12px;border-bottom:1px solid var(--line)\">Produkt</th><th style=\"text-align:left;padding:12px;border-bottom:1px solid var(--line)\">Preis</th><th style=\"text-align:left;padding:12px;border-bottom:1px solid var(--line)\">Key nötig</th><th style=\"text-align:left;padding:12px;border-bottom:1px solid var(--line)\">Lieferung</th><th style=\"text-align:left;padding:12px;border-bottom:1px solid var(--line)\">Für wen?</th></tr></thead><tbody>{render_compare_rows(products)}</tbody></table></div></section>

    <section class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Warum VOID?</div><h2>Weniger Schritte, mehr Klarheit.</h2></div><p>Der Shop bleibt einfach — von der Auswahl bis zur Lieferung.</p></div><div class=\"steps\"><div class=\"proof\"><strong>Keine unnötigen Schritte</strong><span>Produkt wählen und Ticket öffnen.</span></div><div class=\"proof\"><strong>Private Tickets</strong><span>Alles bleibt nachvollziehbar.</span></div><div class=\"proof\"><strong>Nachvollziehbare Lieferung</strong><span>Receipt, Bestellnummer und Log.</span></div><div class=\"proof\"><strong>Persönlicher Support</strong><span>Direkte Beratung im Discord.</span></div></div></section>

    <section class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Produkt-Finder</div><h2>Für wen ist welches Produkt?</h2></div><p>Schnelle Orientierung, wenn du noch nicht sicher bist.</p></div><div class=\"offer-grid\"><article class=\"offer\"><h3>Du brauchst FPS?</h3><p>→ FastFlags Pack oder FFlags Injector.</p></article><article class=\"offer\"><h3>Du brauchst Schutz?</h3><p>→ Anti-Ban.</p></article><article class=\"offer\"><h3>Du brauchst Server-Struktur?</h3><p>→ Discord Server Template.</p></article><article class=\"offer\"><h3>Du willst Kleidung erstellen?</h3><p>→ T-Shirt Templates.</p></article></div></section>

    <section class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Performance</div><h2>Vorher / Nachher mit FastFlags.</h2></div><p>Eine einfache Darstellung, wie Performance-Konfigurationen gedacht sind: weniger unnötige Last, klarere Einstellungen.</p></div><div class=\"compare\"><div class=\"compare-card\"><strong>Standard</strong><span>Unoptimierte Einstellungen, höhere Last, wechselnde FPS.</span><div class=\"meter\"><i style=\"width:42%\"></i></div></div><div class=\"compare-card\"><strong>Optimiert</strong><span>Auf Performance ausgelegte Config mit stabileren Werten.</span><div class=\"meter good\"><i style=\"width:86%\"></i></div></div></div></section>

    <section id=\"reviews\" class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Bewertungen</div><h2>Kurz, ruhig, ehrlich.</h2></div><p>Keine übertriebenen Versprechen — nur typische Rückmeldungen aus einem sauberen Kaufprozess.</p></div><div class=\"review-grid\"><div class=\"review\"><strong>„Schnelle Lieferung“</strong><span>Nach der Bestätigung war alles direkt da.</span><br><small>VOID Kunde</small></div><div class=\"review\"><strong>„Support war korrekt“</strong><span>Fragen wurden im Ticket verständlich beantwortet.</span><br><small>VOID Kunde</small></div><div class=\"review\"><strong>„Alles direkt bekommen“</strong><span>Produkt, Hinweis und Rolle kamen ohne Stress.</span><br><small>VOID Kunde</small></div></div></section>

    <section id=\"how\" class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Ablauf</div><h2>So läuft der Kauf ab.</h2></div><p>Der Prozess ist kurz gehalten und passiert über Discord, damit alles nachvollziehbar bleibt.</p></div><div class=\"steps\"><article class=\"step\"><div class=\"num\">1</div><h3>Ticket öffnen</h3><p>Wähle „Produkt kaufen“ und dein Wunschprodukt.</p></article><article class=\"step\"><div class=\"num\">2</div><h3>Warenkorb prüfen</h3><p>Füge weitere Produkte hinzu.</p></article><article class=\"step\"><div class=\"num\">3</div><h3>Zahlung klären</h3><p>Das Team bestätigt Art und Betrag.</p></article><article class=\"step\"><div class=\"num\">4</div><h3>Lieferung erhalten</h3><p>Produkt kommt per DM oder Ticket.</p></article></div></section>

    <section id=\"faq\" class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">FAQ</div><h2>Kurze Antworten.</h2></div><p>Die wichtigsten Punkte, bevor du ein Ticket öffnest.</p></div><div class=\"faq-grid\"><details class=\"faq\"><summary>Wie schnell bekomme ich mein Produkt?</summary><p>Nach bestätigter Zahlung wird die Lieferung automatisch oder direkt durch das Team ausgelöst.</p></details><details class=\"faq\"><summary>Welche Zahlungsarten gibt es?</summary><p>Im Ticket können Robux, PayPal, Paysafecard oder andere verfügbare Methoden geklärt werden.</p></details><details class=\"faq\"><summary>Kann ich mehrere Produkte kaufen?</summary><p>Ja. Der Warenkorb berechnet Mengenrabatte automatisch.</p></details><details class=\"faq\"><summary>Was bedeutet Unlimited?</summary><p>Einige digitale Produkte brauchen keinen einzelnen Lizenz-Key und werden direkt bereitgestellt.</p></details></div></section>

    <section class=\"wrap\"><div class=\"section-top\"><div><div class=\"eyebrow\">Letzte Verkäufe</div><h2>Anonymisiert und live.</h2></div><p>Nur Produkt und Zeitpunkt — keine Kundendaten.</p></div><div class=\"change-list\">{render_recent_sales(status)}</div></section>

    <section class=\"wrap\"><div class=\"cta\"><div><h2>Bereit für dein Produkt?</h2><p>Sieh dir den Store an oder öffne im Discord ein Kauf-Ticket. Bei Fragen hilft dir das Team direkt weiter.</p></div><div class=\"hero-actions\" style=\"margin:0\"><a class=\"btn btn-primary\" href=\"/store\">Zum Store</a><a class=\"btn btn-secondary\" href=\"{DISCORD_INVITE_URL}\">Discord beitreten</a></div></div></section>
    <div id="ticketHelpModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:99;align-items:center;justify-content:center;padding:20px"><div class="detail-card" style="max-width:520px;width:100%"><div class="eyebrow">Discord Kauf</div><h2>So öffnest du ein Kauf-Ticket.</h2><ul class="detail-list"><li><b>1.</b> Discord beitreten</li><li><b>2.</b> Kanal <code>#🎟️│create-ticket</code> öffnen</li><li><b>3.</b> „Produkt kaufen“ auswählen</li></ul><div class="hero-actions"><a class="btn btn-primary" href="https://discord.gg/S7qpm4edEa">Discord beitreten</a><button class="btn btn-secondary" onclick="closeTicketHelp()">Schließen</button></div></div></div>
  </main>
""" + footer() + theme_script()
    return html


def footer():
    return f"""
  <footer><div class=\"wrap footer-grid\"><div><h4>VOID Shop</h4><p>Roblox Tools, Templates und Support — schlicht, direkt und nachvollziehbar.</p></div><div><h4>Shop</h4><a href=\"/#products\">Produkte</a><a href=\"/store\">Store</a></div><div><h4>Community</h4><a href=\"{DISCORD_INVITE_URL}\">Discord</a><a href=\"/partner\">Partner</a></div><div><h4>Info</h4><a href=\"/changelog\">Changelog</a><a href=\"/#faq\">FAQ</a></div><div><h4>Intern</h4><a href=\"/admin/login\">Admin</a><a href=\"#top\">Nach oben</a></div></div></footer>
"""


def render_product_detail(key, product, best_key=None):
    if not product:
        return render_simple_page("Produkt nicht gefunden", "Dieses Produkt existiert nicht.")
    faqs = PRODUCT_FAQS.get(key, [])
    faq_html = "".join(f"<details class=\"faq\"><summary>{escape(q)}</summary><p>{escape(a)}</p></details>" for q, a in faqs)
    best = " · Bestseller" if best_key == key else ""
    return base_head(f"{product['name']} — VOID Shop") + nav() + f"""
  <main class=\"wrap\">
    <section>
      <div class=\"detail-grid\">
        <div class=\"detail-card\"><div class=\"eyebrow\">Produktdetail{escape(best)}</div><h1>{escape(product['emoji'])} {escape(product['name'])}</h1><p class=\"lead\">{escape(product['desc'])}</p><div class=\"detail-price\">{escape(str(product['robux']))} R$</div><p class=\"muted\">{escape(product['price'])}</p><ul class=\"detail-list\"><li><b>Lieferung:</b> per DM oder Ticket nach Bestätigung</li><li><b>Lager:</b> {escape(product.get('stock_label','auf Lager'))}</li><li><b>Key nötig:</b> {escape(product.get('key_needed','Ja'))}</li><li><b>Kategorie:</b> {escape(PRODUCT_GROUP_LABELS.get(product_group(key), 'Tools'))}</li></ul><div class=\"hero-actions\"><button class=\"btn btn-primary\" onclick=\"openTicketHelp()\">In Discord kaufen</button><a class=\"btn btn-secondary\" href=\"/\">Zurück</a></div></div>
        <aside class=\"detail-card\"><div class=\"mockup\" style=\"width:86px;height:86px;font-size:26px;margin-bottom:20px\">{escape(product_mockup(key))}</div><h2 style=\"font-size:34px\">Kurzinfo</h2><ul class=\"detail-list\"><li>Private Kaufabwicklung</li><li>Receipt nach Kauf</li><li>Support im Ticket</li><li>Mengenrabatt im Warenkorb</li></ul></aside>
      </div>
    </section>
    <section><div class=\"section-top\"><div><div class=\"eyebrow\">Vorteile</div><h2>Was du bekommst.</h2></div><p>Lieferumfang, Anleitung nach Kauf und passende Produkte.</p></div><div class=\"offer-grid\"><article class=\"offer\"><h3>Vorteile</h3><p>Klare Lieferung, Support im Ticket und Receipt mit Bestellnummer.</p></article><article class=\"offer\"><h3>Lieferumfang</h3><p>Digitales Produkt, Hinweise zur Nutzung und Support bei Fragen.</p></article><article class=\"offer\"><h3>Anleitung nach Kauf</h3><p>Discord öffnen, Ticket verfolgen, Lieferung per DM/Ticket prüfen.</p></article></div></section>
    <section><div class=\"section-top\"><div><div class=\"eyebrow\">Ähnliche Produkte</div><h2>Passt vielleicht auch.</h2></div><p>Weitere Produkte aus dem Shop.</p></div><div class=\"hero-actions\"><a class=\"btn btn-secondary\" href=\"/product/fastflags_pack\">FastFlags Pack</a><a class=\"btn btn-secondary\" href=\"/product/anti_ban\">Anti-Ban</a><a class=\"btn btn-secondary\" href=\"/product/discord_template\">Discord Template</a></div></section>
    <section><div class=\"section-top\"><div><div class=\"eyebrow\">FAQ</div><h2>Fragen zu {escape(product['name'])}</h2></div><p>Kurze Antworten zum Produkt und zur Lieferung.</p></div><div class=\"faq-grid\">{faq_html}</div></section>
    <div id="ticketHelpModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:99;align-items:center;justify-content:center;padding:20px"><div class="detail-card" style="max-width:520px;width:100%"><div class="eyebrow">Discord Kauf</div><h2>So öffnest du ein Kauf-Ticket.</h2><ul class="detail-list"><li><b>1.</b> Discord beitreten</li><li><b>2.</b> Kanal <code>#🎟️│create-ticket</code> öffnen</li><li><b>3.</b> „Produkt kaufen“ auswählen</li></ul><div class="hero-actions"><a class="btn btn-primary" href="https://discord.gg/S7qpm4edEa">Discord beitreten</a><button class="btn btn-secondary" onclick="closeTicketHelp()">Schließen</button></div></div></div>
  </main>
""" + footer() + theme_script()


def render_changelog():
    items = "".join(f"<article class=\"change-item\"><strong>{escape(date)} · {escape(title)}</strong><p>{escape(text)}</p></article>" for date, title, text in CHANGELOG)
    return base_head("Changelog — VOID Shop") + nav() + f"""
  <main class=\"wrap\"><section><div class=\"eyebrow\">Changelog</div><h1>Updates und Änderungen.</h1><p class=\"lead\">Neue Features, Fixes und Preis-/Produktänderungen werden hier gesammelt.</p></section><section style=\"padding-top:0\"><div class=\"change-list\">{items}</div></section></main>
""" + footer() + theme_script()


def render_partner():
    return base_head("Partner — VOID Shop") + nav() + f"""
  <main class=\"wrap\"><section><div class=\"eyebrow\">Partner</div><h1>Partnerschaften mit VOID Shop.</h1><p class=\"lead\">Für Kooperationen, gegenseitige Werbung oder Community-Projekte kannst du ein Partner-Ticket öffnen.</p><div class=\"hero-actions\"><a class=\"btn btn-primary\" href=\"{DISCORD_INVITE_URL}\">Partner-Ticket öffnen</a><a class=\"btn btn-secondary\" href=\"/\">Zurück</a></div></section><section style=\"padding-top:0\"><div class=\"partner-box\"><div class=\"proof\"><strong>Was wir brauchen</strong><span>Server-Thema, Mitgliederzahl, Invite-Link und kurze Beschreibung.</span></div><div class=\"proof\"><strong>Was wir bieten</strong><span>Saubere Abwicklung, klare Anforderungen und schnelle Rückmeldung im Ticket.</span></div></div></section></main>
""" + footer() + theme_script()


def render_simple_page(title, text):
    return base_head(title) + nav() + f"<main class=\"wrap\"><section><h1>{escape(title)}</h1><p class=\"lead\">{escape(text)}</p><div class=\"hero-actions\"><a class=\"btn btn-primary\" href=\"/\">Zurück</a></div></section></main>" + footer() + theme_script()


def render_roadmap():
    groups = {
        "Geplant": ["Dashboard Produktbilder", "mehr Produkt-Guides", "automatische Discord Deep Links"],
        "In Arbeit": ["Admin-Produktverwaltung", "Live-Stock", "CSV-Exports"],
        "Fertig": ["Warenkorb", "Auto-Delivery", "Receipt per DM", "Produktfilter", "Detailseiten"],
    }
    cols = "".join(f"<div class=\"offer\"><h3>{escape(k)}</h3><p>" + "<br>".join("• "+escape(x) for x in v) + "</p></div>" for k,v in groups.items())
    return base_head("Roadmap — VOID Shop") + nav() + f"<main class=\"wrap\"><section><div class=\"eyebrow\">Roadmap</div><h1>Kleine Roadmap.</h1><p class=\"lead\">Geplant, in Arbeit und bereits fertig.</p></section><section style=\"padding-top:0\"><div class=\"offer-grid\">{cols}</div></section></main>" + footer() + theme_script()


def render_status_page(status):
    items = [("Bot online", "Online" if status.get("bot_online") else "Offline"), ("API online", "Online" if status.get("api_online") else "Offline"), ("Delivery aktiv", "Aktiv" if status.get("delivery_active") else "Inaktiv"), ("Ticket-System", "Aktiv" if status.get("ticket_system_active") else "Inaktiv")]
    cards = "".join(f"<div class=\"status-card\"><span>{escape(k)}</span><strong>{escape(v)}</strong></div>" for k,v in items)
    updates = "".join(f"<article class=\"change-item\"><strong>{escape(x)}</strong><p>Letztes Update</p></article>" for x in status.get("last_updates", []))
    return base_head("Status — VOID Shop") + nav() + f"<main class=\"wrap\"><section><div class=\"eyebrow\">Status</div><h1>Systemstatus.</h1><p class=\"lead\">Bot, API, Delivery und Ticket-System auf einen Blick.</p></section><section style=\"padding-top:0\"><div class=\"status-bar\">{cards}</div></section><section><div class=\"section-top\"><div><div class=\"eyebrow\">Updates</div><h2>Letzte Updates.</h2></div></div><div class=\"change-list\">{updates}</div></section></main>" + footer() + theme_script()


def render_store(products):
    cards = "".join(f"""
    <article class=\"product-card\" style=\"color:var(--bg)\"><div class=\"product-head\"><div class=\"mockup\">{escape(product_mockup(k))}</div><span class=\"tag\">{escape(PRODUCT_GROUP_LABELS.get(product_group(k),'Tools'))}</span></div><h3>{escape(p['emoji'])} {escape(p['name'])}</h3><p>{escape(p['desc'])}</p><div class=\"price\"><div><strong>{escape(str(p['robux']))} R$</strong><span>{escape(p['price'])}</span></div><span class=\"availability\">{escape(p.get('stock_label','auf Lager'))}</span></div><div style=\"display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px\"><button class=\"product-action\" onclick=\"openModal('{escape(p['name'])}','discord')\">Ticket</button><button class=\"product-action\" style=\"background:#00d26a;color:#fff\" onclick=\"openMagic('{escape(k)}','{escape(p['name'])}')\">⚡ Magic Push</button></div></article>""" for k, p in products.items())
    return base_head("Store — VOID Shop") + nav() + f"""
  <main class=\"wrap\"><section><div class=\"eyebrow\">Store</div><h1>Produkte kaufen.</h1><p class=\"lead\">Wähle ein Produkt aus. Die Anfrage wird an den Bot weitergegeben und im Discord bearbeitet.</p></section><section style=\"padding-top:0\"><div class=\"products-shell\"><div class=\"product-grid\">{cards}</div></div></section></main>
  <div id=\"buyModal\" style=\"display:none;position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:99;align-items:center;justify-content:center;padding:20px\"><div class=\"detail-card\" style=\"max-width:460px;width:100%\"><h2 id=\"modal-title\">Produkt kaufen</h2><p class=\"muted\">Gib Discord Username oder User-ID ein.</p><input id=\"userIdentifier\" style=\"width:100%;padding:14px;border-radius:14px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);margin:18px 0\" placeholder=\"Discord Username / ID\"><div class=\"hero-actions\"><button class=\"btn btn-primary\" onclick=\"confirmBuy()\">Senden</button><button class=\"btn btn-secondary\" onclick=\"closeModal()\">Abbrechen</button></div></div></div>
  <script>
    let selectedProduct='',selectedMode='discord',selKey='';
    function openModal(p,m){{selectedProduct=p;selectedMode=m;selKey='';document.getElementById('modal-title').textContent=p;document.getElementById('buyModal').style.display='flex'}}
    function openMagic(k,name){{selKey=k;selectedProduct=name;selectedMode='magic';document.getElementById('modal-title').textContent='⚡ Magic Push: '+name;document.getElementById('buyModal').style.display='flex'}}
    function closeModal(){{document.getElementById('buyModal').style.display='none'}}
    async function confirmBuy(){{
      const user=document.getElementById('userIdentifier').value;if(!user){{alert('Bitte Discord Username/ID eingeben.');return}}
      try{{
        if(selectedMode==='magic'){{
          await fetch('/api/magic_push',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{user:user,product:selKey||'infinityxeh'}})}});
          alert('🎉 Magic Push erfolgreich! Dein Kauf-Ticket mit Warenkorb wurde in Discord erstellt.');
        }}else{{
          await fetch('/api/buy',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{user:user,product:selectedProduct,mode:selectedMode}})}});
          alert('Kaufanfrage gesendet. Bitte Discord prüfen.');
        }}
        closeModal();
      }}catch(e){{alert('Fehler beim Senden.')}}
    }}
  </script>
""" + footer() + theme_script()


def render_verify_page(oid="", result=None):
    res_html = ""
    if oid:
        if result and result.get("valid"):
            res_html = f"""
            <div class=\"order-card\" style=\"min-height:auto;border-color:#2f7d55;background:rgba(47,125,85,.08);margin-top:24px\">
              <div style=\"display:flex;align-items:center;gap:12px;color:#2f7d55;font-weight:900;font-size:20px\">
                <span style=\"font-size:28px\">✅</span> OFFIZIELLES VOID SIEGEL
              </div>
              <p style=\"margin:14px 0;color:var(--ink);font-size:16px\">Dieser Kaufbeleg wurde von der 24/7 Engine verifiziert und ist <b>authentisch</b>.</p>
              <div class=\"order-lines\" style=\"margin:14px 0\">
                <div class=\"order-line\"><span>Bestellnummer</span><b>{escape(result.get('order_id',''))}</b></div>
                <div class=\"order-line\"><span>Produkt</span><b>{escape(result.get('product',''))}</b></div>
                <div class=\"order-line\"><span>Käufer</span><b>{escape(result.get('buyer','K***'))}</b></div>
                <div class=\"order-line\"><span>Datum</span><b>{escape(result.get('date',''))}</b></div>
              </div>
            </div>"""
        else:
            res_html = f"""
            <div class=\"order-card\" style=\"min-height:auto;border-color:#a33c3c;background:rgba(163,60,60,.08);margin-top:24px\">
              <div style=\"display:flex;align-items:center;gap:12px;color:#a33c3c;font-weight:900;font-size:20px\">
                <span style=\"font-size:28px\">❌</span> UNGÜLTIGER KAUFBELEG
              </div>
              <p style=\"margin-top:10px;color:var(--ink)\">Zur Bestellnummer <b>{escape(oid)}</b> wurde kein Beleg im System gefunden.</p>
            </div>"""

    return base_head("Receipt Verifier — VOID Shop") + nav() + f"""
  <main class=\"wrap\">
    <section>
      <div class=\"eyebrow\">Transparenz & Schutz</div>
      <h1>Öffentlicher Receipt Verifier.</h1>
      <p class=\"lead\">Prüfe die Authentizität jeder VOID-Bestellung live in der Cloud-Datenbank — ohne vertrauliche Lizenz-Keys zu entblößen.</p>
      <form method=\"get\" action=\"/verify\" style=\"margin-top:32px;display:flex;gap:12px;max-width:540px;flex-wrap:wrap\">
        <input name=\"order\" value=\"{escape(oid)}\" placeholder=\"Bestellnummer (z. B. VOID-0042)\" style=\"flex:1;min-width:240px;padding:14px 18px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--ink);font-weight:700;font-size:15px\" required>
        <button class=\"btn btn-primary\" type=\"submit\">Siegel prüfen</button>
      </form>
      {res_html}
    </section>
  </main>
""" + footer() + theme_script()


def render_leaderboard_page(leaders):
    rows = []
    medals = ["🥇", "🥈", "🥉"]
    for idx, l in enumerate(leaders):
        icon = medals[idx] if idx < 3 else f"#{idx+1}"
        rows.append(f"""
        <article class=\"offer\" style=\"min-height:auto;display:flex;align-items:center;justify-content:space-between;padding:18px 24px;margin-bottom:10px\">
          <div style=\"display:flex;align-items:center;gap:16px\">
            <span style=\"font-size:24px;font-weight:900;width:36px\">{icon}</span>
            <div><strong style=\"font-size:19px;color:var(--ink)\">{escape(l['name'])}</strong><br><span class=\"tag\" style=\"margin-top:4px;display:inline-block\">{escape(l['level'])}</span></div>
          </div>
          <div style=\"text-align:right\">
            <strong style=\"font-size:18px;color:var(--good)\">{l['vouches']}x Vouches</strong>
            <span style=\"display:block;color:var(--muted);font-size:13px\">🪙 {l['coins']} Coins</span>
          </div>
        </article>""")
    return base_head("Hall of Fame — VOID Shop") + nav() + f"""
  <main class=\"wrap\">
    <section>
      <div class=\"eyebrow\">Leaderboard</div>
      <h1>Prestige Hall of Fame.</h1>
      <p class=\"lead\">Unsere loyalsten Diamond & Gold VIP-Käufer im globalen Community-Ranking.</p>
      <div style=\"margin-top:36px;max-width:760px\">
        {"".join(rows)}
      </div>
    </section>
  </main>
""" + footer() + theme_script()


def render_fitting():
    return base_head("Fitting Room — VOID Shop") + nav() + "<main class=\"wrap\"><section><div class=\"eyebrow\">Fitting Room</div><h1>Roblox Vorschau.</h1><p class=\"lead\">Dieser Bereich bleibt für spätere 3D-/Preview-Funktionen vorbereitet.</p></section></main>" + footer() + theme_script()


def render_login(error=""):
    err = f"<p style='color:var(--bad);margin-bottom:12px'>{escape(error)}</p>" if error else ""
    return base_head("Admin Login — VOID Shop") + f"""
  <main class=\"wrap\"><section style=\"min-height:80vh;display:grid;place-items:center\"><form class=\"detail-card\" method=\"post\" action=\"/admin/login\" style=\"width:min(420px,100%)\"><div class=\"eyebrow\">Admin</div><h2>Einloggen</h2><p class=\"muted\">Passwort eingeben, um das Dashboard zu öffnen.</p>{err}<input type=\"password\" name=\"password\" placeholder=\"Admin-Passwort\" style=\"width:100%;padding:14px;border-radius:14px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);margin:18px 0\" autofocus><button class=\"btn btn-primary\" style=\"width:100%\" type=\"submit\">Anmelden</button></form></section></main>
""" + theme_script()


def render_admin():
    return base_head("Admin Dashboard — VOID Shop") + nav() + """
  <main class=\"wrap\"><section><div class=\"eyebrow\">Admin</div><h1>Dashboard.</h1><p class=\"lead\">Live-Statistiken, Produktbestand, Keys, Tickets, Exports und Produktverwaltung.</p><div class=\"hero-actions\"><a class=\"btn btn-secondary\" href=\"/admin/logout\">Abmelden</a><a class=\"btn btn-secondary\" href=\"/api/admin/export/sales\">Sales CSV</a><a class=\"btn btn-secondary\" href=\"/api/admin/export/keys\">Keys CSV</a><a class=\"btn btn-secondary\" href=\"/api/admin/export/tickets\">Tickets CSV</a><a class=\"btn btn-secondary\" href=\"/api/admin/export/reviews\">Reviews CSV</a></div></section><section style=\"padding-top:0\"><div class=\"status-bar\" id=\"adminKpis\"></div></section><section style=\"padding-top:0\"><div class=\"section-top\"><div><div class=\"eyebrow\">Produkte</div><h2>Produktverwaltung.</h2></div><p>Preis, Beschreibung, Aktiv-Status, Unlimited und Keys bearbeiten.</p></div><div class=\"offer-grid\" id=\"adminProducts\"></div></section><section style=\"padding-top:0\"><div class=\"section-top\"><div><div class=\"eyebrow\">Tickets</div><h2>Offene Tickets.</h2></div><p>Name, Typ, Ersteller, Claimed by, Alter.</p></div><div class=\"change-list\" id=\"ticketList\"></div></section><section style=\"padding-top:0\"><div class=\"section-top\"><div><div class=\"eyebrow\">Sales</div><h2>Verkäufe filtern.</h2></div><p>Letzte Verkäufe nach Zeitraum, Produkt oder Supporter ansehen.</p></div>
    <div style=\"display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px\">
      <button class=\"filter-tab active\" data-speriod=\"\" onclick=\"filterSPer(this,'')\">Alle Zeit</button>
      <button class=\"filter-tab\" data-speriod=\"today\" onclick=\"filterSPer(this,'today')\">Heute</button>
      <button class=\"filter-tab\" data-speriod=\"7d\" onclick=\"filterSPer(this,'7d')\">7 Tage</button>
      <button class=\"filter-tab\" data-speriod=\"30d\" onclick=\"filterSPer(this,'30d')\">30 Tage</button>
      <select id=\"salesFilter\" class=\"btn btn-secondary\" style=\"padding:8px 14px\"><option value=\"\">Alle Produkte</option></select>
      <select id=\"supporterFilter\" class=\"btn btn-secondary\" style=\"padding:8px 14px\"><option value=\"\">Alle Supporter</option></select>
    </div>
    <div class=\"change-list\" id=\"salesList\"></div>
  </section>
  <section style=\"padding-top:0\">
    <div class=\"section-top\"><div><div class=\"eyebrow\">Blitzangebot</div><h2>Flash-Sale Steuerung.</h2></div><p>Live Ticker-Banner & Angebote verwalten.</p></div>
    <div class=\"detail-card\" style=\"display:flex;gap:12px;flex-wrap:wrap;align-items:center\">
      <select id=\"fsProdSelect\" class=\"btn btn-secondary\" style=\"padding:10px 14px\"></select>
      <input id=\"fsDiscInput\" type=\"number\" placeholder=\"Rabatt %\" value=\"25\" style=\"width:110px;padding:12px;border-radius:14px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);font-weight:bold\">
      <input id=\"fsMinInput\" type=\"number\" placeholder=\"Dauer Min\" value=\"30\" style=\"width:110px;padding:12px;border-radius:14px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);font-weight:bold\">
      <button class=\"btn btn-primary\" style=\"background:#d43838;border-color:#d43838\" onclick=\"startFS()\">⚡ Blitzangebot starten</button>
      <button class=\"btn btn-secondary\" style=\"color:var(--bad);border-color:var(--bad)\" onclick=\"stopFS()\">⛔ Beenden</button>
    </div>
  </section>
  <section style=\"padding-top:0\">
    <div class=\"section-top\"><div><div class=\"eyebrow\">Bot Delivery</div><h2>DM-Nachrichten Konfigurator.</h2></div><p>Sondertexte, Dateien & Links, die der Bot beim Key-Einlösen per Privat-DM sendet.</p></div>
    <div class=\"detail-card\">
      <div style=\"display:flex;gap:12px;margin-bottom:14px;align-items:center;flex-wrap:wrap\">
        <select id=\"dmProdSelect\" class=\"btn btn-secondary\" style=\"padding:10px 14px\" onchange=\"loadDmText()\"></select>
        <span class=\"muted\">Produkt wählen:</span>
      </div>
      <textarea id=\"dmTextInput\" rows=\"4\" placeholder=\"Sonderhinweise, Download-Links, Setup-Anleitung (Markdown/Links)...\" style=\"width:100%;padding:14px;border-radius:14px;border:1px solid var(--line);background:var(--surface-2);color:var(--ink);font-family:monospace;line-height:1.4\"></textarea>
      <div class=\"hero-actions\" style=\"margin-top:14px\">
        <button class=\"btn btn-primary\" onclick=\"saveDmText()\">💾 DM-Text Speichern</button>
        <button class=\"btn btn-secondary\" onclick=\"resetDmText()\">Standard herstellen</button>
      </div>
    </div>
  </section>
</main>
  <div id=\"keyModal\" style=\"display:none;position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:99;align-items:center;justify-content:center;padding:20px\">
    <div class=\"detail-card\" style=\"max-width:620px;width:100%;max-height:80vh;display:flex;flex-direction:column\">
      <div style=\"display:flex;justify-content:space-between;align-items:center;margin-bottom:16px\">
        <h2 id=\"keyModalTitle\">Keys</h2>
        <button class=\"btn btn-secondary\" onclick=\"document.getElementById('keyModal').style.display='none'\">Schließen</button>
      </div>
      <div style=\"overflow-y:auto;flex:1\">
        <table style=\"width:100%;border-collapse:collapse;font-size:14px\">
          <thead><tr><th style=\"text-align:left;padding:10px;border-bottom:1px solid var(--line)\">Key</th><th style=\"text-align:left;padding:10px;border-bottom:1px solid var(--line)\">Status</th><th style=\"text-align:left;padding:10px;border-bottom:1px solid var(--line)\">Genutzt von</th></tr></thead>
          <tbody id=\"keyModalBody\"></tbody>
        </table>
      </div>
    </div>
  </div>
  <script>
    let curSPer='', cachedProds={};
    function filterSPer(btn,p){document.querySelectorAll('[data-speriod]').forEach(b=>b.classList.toggle('active',b===btn));curSPer=p;loadSales();}
    async function loadAdmin(){
      const s=await fetch('/api/admin/stats').then(r=>r.json());
      document.getElementById('adminKpis').innerHTML=[['Umsatz',s.total_robux+' R$'],['Heute',s.today_robux+' R$'],['Tickets',s.total_tickets],['Antwort',s.avg_response]].map(x=>`<div class="status-card"><span>${x[0]}</span><strong>${x[1]}</strong></div>`).join('');
      const p=await fetch('/api/admin/products').then(r=>r.json());
      const oldProd=document.getElementById('salesFilter').value;
      const oldFs=document.getElementById('fsProdSelect').value;
      const oldDm=document.getElementById('dmProdSelect').value;
      const prodOpts=p.products.map(x=>`<option value="${x.key}">${x.name}</option>`).join('');
      document.getElementById('salesFilter').innerHTML='<option value="">Alle Produkte</option>'+prodOpts;
      if(oldProd) document.getElementById('salesFilter').value=oldProd;
      document.getElementById('fsProdSelect').innerHTML=prodOpts;
      if(oldFs) document.getElementById('fsProdSelect').value=oldFs;
      document.getElementById('dmProdSelect').innerHTML=prodOpts;
      if(oldDm) document.getElementById('dmProdSelect').value=oldDm;
      p.products.forEach(x=>{ cachedProds[x.key]=x; });
      loadDmText();
      document.getElementById('adminProducts').innerHTML=p.products.map(x=>`<article class="offer"><h3>${x.emoji} ${x.name}</h3><p>Preis: <b>${x.robux} R$</b><br>Stock: <b>${x.stock_label}</b><br>Unlimited: <b>${x.unlimited?'Ja':'Nein'}</b><br>Aktiv: <b>${x.active?'Ja':'Nein'}</b></p><div class="hero-actions" style="margin-top:14px"><button class="btn btn-primary" onclick="toggleUn('${x.key}',${!x.unlimited})">Unlimited ${x.unlimited?'aus':'an'}</button><button class="btn btn-secondary" onclick="editProduct('${x.key}',${x.robux})">Bearbeiten</button><button class="btn btn-secondary" onclick="addKeys('${x.key}')">Keys +</button><button class="btn btn-secondary" onclick="showKeys('${x.key}')">Key-Liste</button></div></article>`).join('');
      const t=await fetch('/api/admin/tickets').then(r=>r.json());
      document.getElementById('ticketList').innerHTML=(t.tickets||[]).map(x=>`<article class="change-item" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px"><div><strong>#${x.name}</strong> · <span class="tag">${x.topic||'Support'}</span></div><div style="font-size:13px"><span style="color:var(--muted)">Ersteller:</span> <b>${x.creator||'Kunde'}</b> | <span style="color:var(--muted)">Claimed:</span> <b>${x.claimed_by||'—'}</b> | <span style="color:var(--muted)">Alter:</span> <b>${x.age||'neu'}</b></div></article>`).join('')||'<p class="muted">Keine offenen Tickets.</p>';
      loadSales();
    }
    function loadDmText(){
      const k=document.getElementById('dmProdSelect').value;
      if(k && cachedProds[k]) document.getElementById('dmTextInput').value = cachedProds[k].delivery_msg || '';
    }
    async function saveDmText(){
      const k=document.getElementById('dmProdSelect').value;
      const txt=document.getElementById('dmTextInput').value;
      await fetch('/api/admin/products/'+k,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({delivery_msg:txt})});
      alert('💾 DM-Text für '+k+' gespeichert! Der Bot sendet ab sofort diesen Sondertext bei Kauf & Key-Einlösung.');
      loadAdmin();
    }
    async function resetDmText(){
      const k=document.getElementById('dmProdSelect').value;
      await fetch('/api/admin/products/'+k,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({delivery_msg:''})});
      alert('Standard wiederhergestellt.');
      loadAdmin();
    }
    async function startFS(){
      const p=document.getElementById('fsProdSelect').value;
      const d=document.getElementById('fsDiscInput').value;
      const m=document.getElementById('fsMinInput').value;
      await fetch('/api/admin/flashsale',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({active:true,product:p,discount:parseInt(d),minutes:parseInt(m)})});
      alert('⚡ Blitzangebot wurde auf Website & Discord aktiviert!');
      loadAdmin();
    }
    async function stopFS(){
      await fetch('/api/admin/flashsale',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({active:false})});
      alert('⛔ Blitzangebot beendet.');
      loadAdmin();
    }
    async function toggleUn(k,v){await fetch('/api/admin/products/'+k+'/unlimited',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:v})});loadAdmin();}
    async function editProduct(k,current){const robux=prompt('Neuer Robux Preis (leer = nicht ändern)',current);const desc=prompt('Neue Beschreibung (leer = nicht ändern)','');const active=confirm('Produkt aktiv? OK=aktiv, Abbrechen=inaktiv');let body={active:active};if(robux)body.robux=parseInt(robux);if(desc)body.desc=desc;await fetch('/api/admin/products/'+k,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});loadAdmin();}
    async function addKeys(k){const keys=prompt('Keys einfügen (Komma oder Zeilen):');if(!keys)return;await fetch('/api/admin/products/'+k+'/keys',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({keys:keys})});loadAdmin();}
    async function showKeys(k){
      const d=await fetch('/api/admin/products/'+k+'/keys').then(r=>r.json());
      document.getElementById('keyModalTitle').textContent='Keys: '+k;
      document.getElementById('keyModalBody').innerHTML=(d.keys||[]).map(x=>`<tr><td style="padding:10px;border-bottom:1px solid var(--line)"><code>${x.key}</code></td><td style="padding:10px;border-bottom:1px solid var(--line)">${x.used?'<span style="color:var(--bad);font-weight:bold">GENUTZT</span>':'<span style="color:var(--good);font-weight:bold">FREI</span>'}</td><td style="padding:10px;border-bottom:1px solid var(--line)">${x.used_by||'—'}</td></tr>`).join('')||'<tr><td colspan="3" style="padding:16px;text-align:center">Keine Keys</td></tr>';
      document.getElementById('keyModal').style.display='flex';
    }
    async function loadSales(){
      const prod=document.getElementById('salesFilter').value;
      const supp=document.getElementById('supporterFilter').value;
      let url='/api/admin/sales?';
      if(curSPer) url+='period='+curSPer+'&';
      if(prod) url+='product='+encodeURIComponent(prod)+'&';
      if(supp) url+='supporter='+encodeURIComponent(supp);
      const d=await fetch(url).then(r=>r.json());
      if(d.supporters){
        const oldS=supp;
        document.getElementById('supporterFilter').innerHTML='<option value="">Alle Supporter</option>'+d.supporters.map(x=>`<option value="${x}" ${x===oldS?'selected':''}>${x}</option>`).join('');
      }
      document.getElementById('salesList').innerHTML=(d.sales||[]).map(x=>`<article class="change-item" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap"><div><strong>${x.order_id||''} · ${x.product_name||x.product}</strong><br><small style="color:var(--muted)">Käufer: <b>${x.buyer_name}</b></small></div><div style="text-align:right"><strong style="color:var(--good)">+${x.robux} R$</strong><br><small style="color:var(--muted)">${x.time}</small></div></article>`).join('')||'<p class="muted">Keine Verkäufe.</p>';
    }
    document.getElementById('salesFilter').addEventListener('change',loadSales);
    document.getElementById('supporterFilter').addEventListener('change',loadSales);
    loadAdmin();setInterval(loadAdmin,20000);
  </script>
""" + footer() + theme_script()
