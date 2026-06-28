"""
app.py — Energical Assistant Commercial
Fixed version.

Bugs fixed vs previous:
1. get_groq_client() no longer called at module top-level (was crashing on import).
2. LLM replies now render markdown properly (bold, lists) instead of showing raw **.
3. Product cards rendered OUTSIDE the message bubble (not crammed inside it).
4. Spinner shows "Karim réfléchit..." so user knows the bot is working.
5. Logo loader no longer has hardcoded Windows path.
6. Reset button style no longer conflicts with chip button override.
7. Token usage only shown when > 0 and only on demand (sidebar toggle).
8. Chat input placeholder is friendly, not technical.
9. `eg-reset-row` button selector made specific so it doesn't fight other buttons.
10. st.chat_message wrappers removed (we render our own HTML bubbles cleanly).
"""

import html
import textwrap
import datetime
import base64
import os
import re
import streamlit as st
from src.chat import ChatManager

st.set_page_config(
    page_title="Energical",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Helpers ────────────────────────────────────────────────────────────────────
def md(html_str: str):
    st.markdown(textwrap.dedent(html_str).strip(), unsafe_allow_html=True)

def esc(text: str) -> str:
    return html.escape(str(text), quote=False)

def time_label() -> str:
    return datetime.datetime.now().strftime("%H:%M")

def markdown_to_html(text: str) -> str:
    """
    Convert basic markdown in LLM replies to HTML so it renders properly
    inside our custom bubble (not inside st.markdown which we don't use here).
    Handles: **bold**, *italic*, numbered lists, bullet lists, line breaks.
    """
    # Escape HTML first so we don't break the bubble
    t = html.escape(str(text), quote=False)

    # Bold **text**
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    # Italic *text* (not inside bold)
    t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
    # Line breaks
    t = t.replace('\n', '<br>')
    # Numbered list items that start with "1." "2." etc
    t = re.sub(r'(?:^|<br>)(\d+)\.\s+', r'<br><span class="eg-li-num">\1.</span> ', t)
    # Bullet list items that start with "- " or "• "
    t = re.sub(r'(?:^|<br>)[•\-]\s+', r'<br><span class="eg-li-bul">•</span> ', t)
    # Remove leading <br> if any
    t = t.lstrip('<br>')
    return t

# ── Logo loader ────────────────────────────────────────────────────────────────
def get_logo_b64(path: str = "static/logo.png") -> str:
    candidates = [
        path,
        "./static/logo.png",
        os.path.join(os.getcwd(), "static", "logo.png"),
        os.path.abspath(os.path.join("static", "logo.png")),
    ]
    for p in candidates:
        if os.path.exists(p):
            with open(p, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{data}"
    return ""

LOGO_URI = get_logo_b64()

def logo_img(size: str = "100%", radius: str = "inherit") -> str:
    if not LOGO_URI:
        return ""
    return (
        f'<img src="{LOGO_URI}" '
        f'style="width:{size};height:{size};object-fit:contain;'
        f'border-radius:{radius};display:block;" alt="logo">'
    )

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    box-sizing: border-box;
}

/* ── Global ── */
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f4f9 100%) !important;
}
.block-container {
    max-width: 860px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* Hide Streamlit chrome */
#MainMenu, header, footer { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Hide default Streamlit chat avatars — we draw our own */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"] { display: none !important; }
.stChatMessage {
    background: transparent !important;
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── Topbar ── */
.eg-topbar {
    background: #fff;
    padding: 11px 24px;
    border-radius: 14px;
    margin: 18px auto 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 780px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    border: 1px solid rgba(226,232,240,0.7);
}
.eg-brand { display: flex; align-items: center; gap: 11px; }
.eg-logo {
    width: 30px; height: 30px; border-radius: 8px;
    
    display: flex; align-items: center; justify-content: center;
    font-size: 15px; font-weight: 700; color: #fff; overflow: hidden;
    flex-shrink: 0;
}
.eg-brand-name { font-size: 15px; font-weight: 700; color: #f97316; letter-spacing: -0.02em; }
.eg-vsep { width: 1px; height: 16px; background: #e2e8f0; }
.eg-brand-role { font-size: 12px; color: #f97316; }
.eg-right { display: flex; align-items: center; gap: 12px; }
.eg-online { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #475569; font-weight: 500; }
.eg-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #22c55e;
    animation: pulse 2.5s ease-in-out infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.6; transform:scale(0.9); }
}
.eg-lang {
    font-size: 9px; font-weight: 600; color: #f97316; background: #f1f5f9;
    border: 1px solid #e2e8f0; padding: 3px 8px; border-radius: 6px;
    font-family: 'JetBrains Mono', monospace; letter-spacing: 0.06em;
}

/* ── Landing ── */
.eg-landing {
    min-height: calc(100vh - 160px);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 20px 24px 80px;
}
.eg-landing-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(249,115,22,0.15);
border: 1px solid rgba(249,115,22,0.3);
    border-radius: 24px; padding: 6px 16px; margin-bottom: 26px;
    font-size: 11.5px; font-weight: 600; color: #f97316;
}
.eg-landing-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: #f97316; }
.eg-landing-icon {
    width: 76px; height: 76px; border-radius: 22px;
    
    display: flex; align-items: center; justify-content: center;
    font-size: 32px; font-weight: 700; color: #fff; margin-bottom: 22px;
    box-shadow: 0 8px 32px rgba(37,99,235,0.25); overflow: hidden;
}
.eg-landing-title {
    font-size: 34px; font-weight: 700; color: #f97316;
    letter-spacing: -0.03em; line-height: 1.2;
    text-align: center; margin-bottom: 14px;
}
.eg-landing-title span { color: #f97316; }
.eg-landing-sub {
    font-size: 14.5px; color: #64748b; line-height: 1.7;
    text-align: center; max-width: 420px; margin-bottom: 30px;
}
.eg-features { display: flex; gap: 9px; margin-bottom: 36px; flex-wrap: wrap; justify-content: center; }
.eg-feat {
    background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 7px 15px; font-size: 12px; color: #475569; font-weight: 500;
}

/* Landing CTA button — very specific selector */
.eg-start-col .stButton > button {
    background: linear-gradient(135deg,#2563eb,#1d4ed8) !important;
    border: none !important; border-radius: 12px !important;
    color: #fff !important; font-size: 14px !important;
    font-weight: 600 !important; padding: 14px 32px !important;
    box-shadow: 0 4px 20px rgba(37,99,235,0.35) !important;
    transition: all 0.2s !important; width: 100% !important;
}
.eg-start-col .stButton > button:hover {
    opacity: 0.9 !important; transform: translateY(-2px) !important;
    box-shadow: 0 6px 28px rgba(37,99,235,0.45) !important;
}

/* ── Empty state (chat page, no messages yet) ── */
.eg-empty-wrap {
    display: flex; flex-direction: column; align-items: center;
    padding: 60px 24px 20px;
}
.eg-empty-icon {
    width: 52px; height: 52px; border-radius: 16px;
   
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; font-weight: 700; color: #fff; margin-bottom: 16px;
    box-shadow: 0 6px 24px rgba(37,99,235,0.22); overflow: hidden;
}
.eg-empty-title { font-size: 20px; font-weight: 700; color: #f97316; letter-spacing: -0.02em; margin-bottom: 8px; text-align: center; }
.eg-empty-sub { font-size: 13px; color: #64748b; max-width: 300px; text-align: center; margin-bottom: 24px; }

/* Starter chip buttons — scoped to .eg-chips-row */
.eg-chips-row .stButton > button {
    background: #fff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    color: #f97316 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 12px 14px !important;
    text-align: left !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    transition: all 0.15s !important;
    width: 100% !important;
    height: auto !important;
    line-height: 1.4 !important;
    white-space: normal !important;
}
.eg-chips-row .stButton > button:hover {
    background: #f0f4ff !important;
    border-color: #2563eb !important;
    color: #2563eb !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.1) !important;
}

/* ── Messages ── */
.eg-scroll { padding: 12px 0 12px; }
.eg-ci { max-width: 680px; margin: 0 auto; padding: 0 20px; }

.eg-msg {
    display: flex; gap: 11px; align-items: flex-start;
    margin-bottom: 18px;
    animation: fadeup 0.18s ease;
}
.eg-msg.user { flex-direction: row-reverse; }
@keyframes fadeup {
    from { opacity:0; transform:translateY(5px); }
    to   { opacity:1; transform:translateY(0); }
}

.eg-av {
    width: 32px; height: 32px; border-radius: 50%;
    flex-shrink: 0; display: flex; align-items: center;
    justify-content: center; font-size: 13px; font-weight: 600;
    margin-top: 2px; overflow: hidden;
}
.eg-av.ai {
    
    color: #fff; box-shadow: 0 2px 8px rgba(37,99,235,0.28);
}
.eg-av.usr { background: #e2e8f0; color: #f97316; }

.eg-bc { display: flex; flex-direction: column; gap: 4px; min-width: 0; max-width: 82%; }
.eg-msg.user .eg-bc { align-items: flex-end; }

/* The text bubble */
.eg-bub {
    padding: 13px 17px; border-radius: 18px;
    font-size: 14px; line-height: 1.68; word-break: break-word;
}
.eg-bub.ai {
    background: #fff; border: 1px solid #e2e8f0; color: #0f172a;
    border-top-left-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.eg-bub.usr {
    background: #f97316; color: #fff;
    border-top-right-radius: 4px;
}

/* Inline list items inside bubbles */
.eg-li-num { font-weight: 600; color: #2563eb; margin-right: 2px; }
.eg-li-bul { color: #2563eb; margin-right: 4px; }
.eg-bub.usr .eg-li-num,
.eg-bub.usr .eg-li-bul { color: #bfdbfe; }

/* Timestamp */
.eg-mt {
    font-size: 10px; color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
    padding: 0 4px; letter-spacing: 0.02em;
}

/* Date divider */
.eg-divider {
    display: flex; align-items: center; gap: 12px;
    margin: 4px 0 16px; color: #94a3b8;
    font-size: 10.5px; font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.06em;
}
.eg-divider::before, .eg-divider::after {
    content: ''; flex: 1; height: 1px; background: #e2e8f0;
}

/* ── Product cards — rendered BELOW the bubble, not inside it ── */
.eg-cards-wrap {
    max-width: 82%;
    margin-top: 8px;
    padding-left: 43px;   /* align with bubble, accounting for avatar width + gap */
}
.eg-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 9px;
}
.eg-card {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 11px; padding: 13px; position: relative;
    overflow: hidden; transition: all 0.18s; cursor: default;
}
.eg-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 11px 11px 0 0;
}
.eg-card.ok::before  { background: linear-gradient(90deg,#2563eb,#3b82f6); }
.eg-card.alt::before { background: linear-gradient(90deg,#d97706,#f59e0b); }
.eg-card.out::before { background: linear-gradient(90deg,#dc2626,#ef4444); }
.eg-card:hover {
    border-color: #f97316;
    box-shadow: 0 4px 14px rgba(0,0,0,0.07);
    transform: translateY(-2px);
}
.eg-badge {
    display: inline-block; font-size: 8.5px; font-weight: 600;
    padding: 2px 7px; border-radius: 4px; margin-bottom: 7px;
    text-transform: uppercase; font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.06em;
}
.eg-badge.ok  { background: #dbeafe; color: #1d4ed8; border: 1px solid #bfdbfe; }
.eg-badge.alt { background: #fef3c7; color: #92400e; border: 1px solid #fde68a; }
.eg-badge.out { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
.eg-cn { font-size: 12px; font-weight: 500; color: #f97316; line-height: 1.4; margin-bottom: 6px; min-height: 28px; }
.eg-chr { height: 1px; background: #e2e8f0; margin: 7px 0; }
.eg-cp {
    font-size: 14px; font-weight: 700; color: #2563eb;
    font-family: 'JetBrains Mono', monospace; letter-spacing: -0.02em;
}
.eg-cr { font-size: 9px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-top: 3px; letter-spacing: 0.05em; }

/* ── Chat input ── */
[data-testid="stChatInput"] {
    background: #fff !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 16px !important;
    padding: 4px 6px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    max-width: 680px !important;
    margin: 0 auto 16px auto !important;
    transition: all 0.15s !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 4px rgba(37,99,235,0.09), 0 2px 12px rgba(0,0,0,0.06) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important; border: none !important;
    color: #f97316 !important; font-size: 14px !important;
    padding: 11px 14px !important; min-height: 46px !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #94a3b8 !important; }
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg,#f97316,#ea580c) !important;
    border-radius: 11px !important; color: #fff !important;
    margin: 4px !important; min-width: 38px !important; min-height: 38px !important;
    transition: all 0.15s !important;
}
[data-testid="stChatInput"] button:hover { transform: scale(1.06) !important; }

/* Reset button — scoped to .eg-reset-wrap */
.eg-reset-wrap .stButton > button {
    background: transparent !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    color: #64748b !important;
    font-size: 12px !important;
    padding: 7px 18px !important;
    box-shadow: none !important;
    transition: all 0.15s !important;
    width: auto !important;
}
.eg-reset-wrap .stButton > button:hover {
    background: #f8fafc !important;
    border-color: #94a3b8 !important;
    color: #0f172a !important;
}
</style>
""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────────
if "chat" not in st.session_state:
    with st.spinner("Démarrage de l'assistant..."):
        st.session_state.chat     = ChatManager()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "started" not in st.session_state:
    st.session_state.started  = False

# ── Product cards HTML ─────────────────────────────────────────────────────────
def product_cards_html(products: list) -> str:
    if not products:
        return ""
    cards = []
    for p in products[:4]:
        m        = p.get("metadata", {})
        nom      = esc(m.get("nom", "Produit"))
        prix     = m.get("prix", "")
        stock    = str(m.get("statut_stock", ""))
        ref      = esc(str(p.get("id", "")))
        replaced = p.get("status") == "REPLACED"

        if "rupture" in stock.lower():
            cls, bc, bt = "out", "out", "Rupture"
        elif replaced:
            cls, bc, bt = "alt", "alt", "Alternative"
        else:
            cls, bc, bt = "ok",  "ok",  "Disponible"

        try:
            prix_fmt = f"{float(str(prix).replace(' ','').replace(',','.')):,.0f}".replace(",", "\u202f") + " DA"
        except Exception:
            prix_fmt = f"{esc(str(prix))} DA" if prix else "Prix sur demande"

        cards.append(
            f'<div class="eg-card {cls}">'
            f'  <span class="eg-badge {bc}">{bt}</span>'
            f'  <div class="eg-cn">{nom}</div>'
            f'  <div class="eg-chr"></div>'
            f'  <div class="eg-cp">{prix_fmt}</div>'
            f'  <div class="eg-cr">Ref. {ref}</div>'
            f'</div>'
        )
    return (
        '<div class="eg-cards-wrap">'
        '<div class="eg-cards">' + "".join(cards) + "</div>"
        "</div>"
    )

# ── Render one message ─────────────────────────────────────────────────────────
def render_message(msg: dict):
    role     = msg["role"]
    content  = markdown_to_html(msg["content"])   # ← renders bold/lists properly
    products = msg.get("products", [])
    t        = msg.get("time", "")

    if role == "user":
        md(f"""
        <div class="eg-msg user">
            <div class="eg-av usr">M</div>
            <div class="eg-bc">
                <div class="eg-bub usr">{content}</div>
                <div class="eg-mt">{t}</div>
            </div>
        </div>""")
    else:
        av = logo_img("20px", "50%") if LOGO_URI else "E"
        # Cards rendered OUTSIDE the bubble — separate div below it
        cards = product_cards_html(products)
        md(f"""
        <div class="eg-msg">
            <div class="eg-av ai">{av}</div>
            <div class="eg-bc">
                <div class="eg-bub ai">{content}</div>
                <div class="eg-mt">Energical · {t}</div>
            </div>
        </div>
        {cards}""")

# ── Topbar HTML ────────────────────────────────────────────────────────────────
def topbar():
    logo_sm = logo_img("28px", "7px") if LOGO_URI else "E"
    md(f"""
    <div class="eg-topbar">
        <div class="eg-brand">
            <div class="eg-logo">{logo_sm}</div>
            <span class="eg-brand-name">Energical</span>
            <div class="eg-vsep"></div>
            <span class="eg-brand-role">Conseiller produits</span>
        </div>
        <div class="eg-right">
            <div class="eg-online"><div class="eg-dot"></div>En ligne</div>
            <span class="eg-lang">FR · DZ · AR</span>
        </div>
    </div>""")

# ══════════════════════════════════════════════════════════════════════════════
#  LANDING PAGE
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.started:
    topbar()

    logo_lg = logo_img("56px", "14px") if LOGO_URI else "E"
    md(f"""
    <div class="eg-landing">
        <div class="eg-landing-badge">
            <div class="eg-landing-badge-dot"></div>
            Assistant intelligent · Energical
        </div>
        <div class="eg-landing-icon">{logo_lg}</div>
        <div class="eg-landing-title">
            Trouvez le bon produit,<br><span>instantanement.</span>
        </div>
        <div class="eg-landing-sub">
            Posez votre question en francais, darija ou arabe —
            chaudieres, robinetterie, electricite, sanitaire.
            Je vous guide vers la meilleure reference Energical.
        </div>
        <div class="eg-features">
            <div class="eg-feat">Chauffage</div>
            <div class="eg-feat">Robinetterie</div>
            <div class="eg-feat">Electricite</div>
            <div class="eg-feat">Climatisation</div>
            <div class="eg-feat">Visiophonie</div>
        </div>
    </div>""")

    c_l, c_c, c_r = st.columns([1, 1.4, 1])
    with c_c:
        md('<div class="eg-start-col">')
        if st.button("Commencer la conversation", key="start_btn", use_container_width=True):
            st.session_state.started = True
            st.rerun()
        md('</div>')

# ══════════════════════════════════════════════════════════════════════════════
#  CHAT PAGE
# ══════════════════════════════════════════════════════════════════════════════
else:
    topbar()

    # ── Empty state with starter chips ────────────────────────────────────────
    if not st.session_state.messages:
        logo_md = logo_img("38px", "10px") if LOGO_URI else "E"
        md(f"""
        <div class="eg-empty-wrap">
            <div class="eg-empty-icon">{logo_md}</div>
            <div class="eg-empty-title">Quel produit recherchez-vous ?</div>
            <div class="eg-empty-sub">
                Choisissez une suggestion ou decrivez votre besoin ci-dessous.
            </div>
        </div>""")

        starters = [
            ("Chaudiere gaz",      "Je cherche une chaudiere au gaz"),
            ("Mitigeur lavabo",     "Je cherche un mitigeur lavabo chrome"),
            ("Visiophone immeuble", "Je veux installer un visiophone"),
        ]
        md('<div class="eg-chips-row">')
        cols = st.columns(3)
        for col, (label, query) in zip(cols, starters):
            with col:
                if st.button(label, key=f"chip_{query}", use_container_width=True):
                    t = time_label()
                    with st.spinner("Karim réfléchit..."):
                        result = st.session_state.chat.send_message(query)
                    st.session_state.messages.append({"role": "user", "content": query, "time": t})
                    st.session_state.messages.append({
                        "role":     "assistant",
                        "content":  result["llm_answer"],
                        "products": result.get("retrieved_products", []),
                        "time":     time_label(),
                    })
                    st.rerun()
        md('</div>')

    # ── Conversation ───────────────────────────────────────────────────────────
    else:
        md('<div class="eg-scroll"><div class="eg-ci">')
        md('<div class="eg-divider">Aujourd\'hui</div>')
        for msg in st.session_state.messages:
            render_message(msg)
        md('</div></div>')

    # ── Chat input ─────────────────────────────────────────────────────────────
    user_input = st.chat_input("Posez votre question (francais, darija, arabe)...")

    if user_input:
        t = time_label()
        st.session_state.messages.append({"role": "user", "content": user_input, "time": t})

        with st.spinner("Karim réfléchit..."):
            result = st.session_state.chat.send_message(user_input)

        st.session_state.messages.append({
            "role":     "assistant",
            "content":  result["llm_answer"],
            "products": result.get("retrieved_products", []),
            "time":     time_label(),
        })
        st.rerun()

    # ── Reset ──────────────────────────────────────────────────────────────────
    _, col_btn, _ = st.columns([1, 1, 1])
    with col_btn:
        md('<div class="eg-reset-wrap">')
        if st.button("Nouvelle conversation", key="reset_btn"):
            st.session_state.chat     = ChatManager()
            st.session_state.messages = []
            st.rerun()
        md('</div>')

    # ── Sidebar — tech panel (dev only, hidden from customer) ─────────────────
    with st.sidebar:
        st.markdown("### Panneau Technique")

        if st.session_state.messages:
            try:
                from llm.groq_client import get_groq_client
                gc = get_groq_client()
                used  = gc.token_tracker.used_today
                limit = gc.token_tracker.daily_limit
                if used > 0:
                    pct = used / limit
                    st.markdown("**Tokens utilises**")
                    st.progress(min(pct, 1.0))
                    remaining = limit - used
                    st.caption(f"{used:,} / {limit:,} — {remaining:,} restants")
                    if pct > 0.8:
                        st.warning(f"{remaining:,} tokens restants")
            except Exception:
                pass

            st.divider()

            st.markdown(f"**Tours :** {st.session_state.chat.turns.get_turn_count()}")
            cat = getattr(st.session_state.chat, "stable_category", "")
            st.markdown(f"**Categorie :** `{cat or ''}`")

            mem = st.session_state.chat.memory.to_dict()
            filled = {k: v for k, v in mem.items() if v is not None}
            if filled:
                st.markdown("**Memoire :**")
                st.json(filled)
        else:
            st.info("En attente du premier message.")