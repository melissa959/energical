import html
import textwrap
import datetime
import base64
import os
import streamlit as st
from src.chat import ChatManager

st.set_page_config(
    page_title="Energical",
    page_icon="",
    layout="centered",
    initial_sidebar_state="collapsed",
)

def md(html_str: str):
    st.markdown(textwrap.dedent(html_str).strip(), unsafe_allow_html=True)

def esc(text: str) -> str:
    return html.escape(str(text), quote=False)

def time_label() -> str:
    return datetime.datetime.now().strftime("%H:%M")

# ── Logo loader ─────────────────────────────────────────────
def get_logo_b64(path: str = "static/logo.png") -> str:
    """Ultra robust logo loader (Windows + Streamlit safe)"""

    paths = [
        path,
        "./static/logo.png",
        os.path.join(os.getcwd(), "static/logo.png"),
        os.path.abspath("static/logo.png"),
        "C:/Users/SAN/Documents/GitHub/energical/static/logo.png",
    ]

    for p in paths:
        if os.path.exists(p):
            with open(p, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            print("✅ Logo FOUND at:", p)
            return f"data:image/png;base64,{data}"

    print("❌ Logo NOT FOUND. Checked:", paths)
    return ""

LOGO_URI = get_logo_b64() 
print("LOGO LOADED:", bool(LOGO_URI))

def logo_img(size: str = "100%", radius: str = "inherit") -> str:
    if not LOGO_URI:
        return ""
    return (
        f'<img src="{LOGO_URI}" '
        f'style="width:{size};height:{size};object-fit:contain;'
        f'border-radius:{radius};display:block !important;" alt="logo">'
    )

LOGO_SM  = logo_img("24px", "6px")
LOGO_LG  = logo_img("56px", "14px")
LOGO_MD  = logo_img("40px", "10px")
LOGO_AV  = logo_img("26px", "50%")

st.markdown(f"""
<style>
/* ========================================================
   FONT & RESET
   ======================================================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* {{
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}

/* ========================================================
   GLOBAL BACKGROUND & LAYOUT
   ======================================================== */
.stApp {{
    background: linear-gradient(135deg, #f8fafc 0%, #f1f4f9 100%) !important;
}}
.block-container {{
    max-width: 900px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}}
.block-container > div,
.block-container > div > div,
section.main > div,
section.main > div > div {{
    padding: 0 !important;
    margin: 0 !important;
}}

/* Hide Streamlit chrome */
#MainMenu, header, footer,
[data-testid="collapsedControl"],
[data-testid="stSidebar"],
section[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
button[kind="header"] {{
    display: none !important;
    visibility: hidden !important;
}}

/* Hide Streamlit avatars */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"] {{
    display: none !important;
}}
.stChatMessage {{
    background: transparent !important;
    padding: 0 !important;
    border: none !important;
}}

/* ========================================================
   TOPBAR
   ======================================================== */
.eg-topbar {{
    background: #ffffff;
    padding: 12px 28px;
    border-radius: 16px;
    margin: 20px auto 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 780px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    border: 1px solid rgba(226, 232, 240, 0.6);
}}
.eg-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
}}
.eg-logo {{
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    flex-shrink: 0;
    overflow: hidden;
    color: white;
    font-weight: 700;
}}
.eg-brand-name {{
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.02em;
}}
.eg-vsep {{
    width: 1px;
    height: 18px;
    background: #e2e8f0;
}}
.eg-brand-role {{
    font-size: 12px;
    color: #64748b;
    font-weight: 400;
}}
.eg-right {{
    display: flex;
    align-items: center;
    gap: 14px;
}}
.eg-online {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: #475569;
    font-weight: 500;
}}
.eg-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #22c55e;
    animation: pulse 2.5s ease-in-out infinite;
}}
@keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.6; transform: scale(0.9); }}
}}
.eg-lang {{
    font-size: 9px;
    font-weight: 600;
    color: #94a3b8;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    padding: 3px 8px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.06em;
}}

/* ========================================================
   LANDING PAGE
   ======================================================== */
.eg-landing {{
    min-height: calc(100vh - 150px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px 24px 60px;
    background: transparent;
}}
.eg-landing-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(37, 99, 235, 0.08);
    border: 1px solid rgba(37, 99, 235, 0.15);
    border-radius: 24px;
    padding: 6px 16px;
    margin-bottom: 28px;
    font-size: 11.5px;
    font-weight: 600;
    color: #2563eb;
}}
.eg-landing-badge-dot {{
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #2563eb;
}}
.eg-landing-icon {{
    width: 76px;
    height: 76px;
    border-radius: 22px;
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(37, 99, 235, 0.25);
    overflow: hidden;
    color: white;
}}
.eg-landing-title {{
    font-size: 36px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.03em;
    line-height: 1.2;
    text-align: center;
    margin-bottom: 14px;
}}
.eg-landing-title span {{
    color: #2563eb;
}}
.eg-landing-sub {{
    font-size: 15px;
    color: #64748b;
    line-height: 1.7;
    text-align: center;
    max-width: 440px;
    margin-bottom: 32px;
}}
.eg-features {{
    display: flex;
    gap: 10px;
    margin-bottom: 38px;
    flex-wrap: wrap;
    justify-content: center;
}}
.eg-feat {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 8px 16px;
    font-size: 12px;
    color: #475569;
    font-weight: 500;
    transition: all 0.15s;
}}
.eg-feat:hover {{
    border-color: #2563eb;
    color: #2563eb;
    background: #f8fafc;
}}

/* Landing button */
.stButton > button {{
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    padding: 14px 32px !important;
    letter-spacing: -0.01em !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px rgba(37, 99, 235, 0.35) !important;
    width: 100% !important;
}}
.stButton > button:hover {{
    opacity: 0.9 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 28px rgba(37, 99, 235, 0.45) !important;
}}

/* ========================================================
   CHAT PAGE
   ======================================================== */
.eg-chat-page {{
    background: transparent;
    height: 100vh;
    display: flex;
    flex-direction: column;
}}

/* Empty state */
.eg-empty-wrap {{
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0 24px 60px;
}}
.eg-empty-icon {{
    width: 56px;
    height: 56px;
    border-radius: 18px;
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 18px;
    box-shadow: 0 6px 24px rgba(37, 99, 235, 0.25);
    overflow: hidden;
    color: white;
}}
.eg-empty-title {{
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
    text-align: center;
}}
.eg-empty-sub {{
    font-size: 13.5px;
    color: #64748b;
    line-height: 1.6;
    max-width: 320px;
    text-align: center;
    margin-bottom: 28px;
}}

/* Starter chips */
[data-testid="stHorizontalBlock"] .stButton > button {{
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    color: #0f172a !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 12px 16px !important;
    text-align: left !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    transition: all 0.15s !important;
    width: 100% !important;
    height: auto !important;
    line-height: 1.4 !important;
    white-space: normal !important;
}}
[data-testid="stHorizontalBlock"] .stButton > button:hover {{
    background: #f8fafc !important;
    border-color: #2563eb !important;
    color: #2563eb !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.12) !important;
}}

/* Messages scroll */
.eg-scroll {{
    flex: 1;
    overflow-y: auto;
    padding: 12px 0 20px;
    scroll-behavior: smooth;
}}
.eg-scroll::-webkit-scrollbar {{
    width: 4px;
}}
.eg-scroll::-webkit-scrollbar-thumb {{
    background: #cbd5e1;
    border-radius: 4px;
}}
.eg-scroll::-webkit-scrollbar-track {{
    background: transparent;
}}
.eg-ci {{
    max-width: 680px;
    margin: 0 auto;
    padding: 0 24px;
}}

/* Messages */
.eg-msg {{
    display: flex;
    gap: 12px;
    align-items: flex-start;
    margin-bottom: 20px;
    animation: up 0.2s ease;
}}
.eg-msg.user {{
    flex-direction: row-reverse;
}}
@keyframes up {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.eg-av {{
    width: 34px;
    height: 34px;
    border-radius: 50%;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 600;
    margin-top: 2px;
    overflow: hidden;
}}
.eg-av.ai {{
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: #fff;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}}
.eg-av.usr {{
    background: #e2e8f0;
    color: #0f172a;
}}

.eg-bc {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
    max-width: 80%;
}}
.eg-msg.user .eg-bc {{
    align-items: flex-end;
}}

.eg-bub {{
    padding: 14px 18px;
    border-radius: 18px;
    font-size: 14.5px;
    line-height: 1.65;
    word-break: break-word;
}}
.eg-bub.ai {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    color: #0f172a;
    border-top-left-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.eg-bub.usr {{
    background: #2563eb;
    color: #ffffff;
    border-top-right-radius: 4px;
}}
.eg-mt {{
    font-size: 10.5px;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
    padding: 0 4px;
    letter-spacing: 0.02em;
}}

/* Divider */
.eg-divider {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 6px 0 18px;
    color: #94a3b8;
    font-size: 10.5px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.06em;
}}
.eg-divider::before,
.eg-divider::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: #e2e8f0;
}}

/* ========================================================
   PRODUCT CARDS
   ======================================================== */
.eg-cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
    margin-top: 14px;
}}
.eg-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 14px;
    position: relative;
    overflow: hidden;
    transition: all 0.2s;
}}
.eg-card::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    border-radius: 12px 12px 0 0;
}}
.eg-card.ok::before {{
    background: linear-gradient(90deg, #2563eb, #3b82f6);
}}
.eg-card.alt::before {{
    background: linear-gradient(90deg, #d97706, #f59e0b);
}}
.eg-card.out::before {{
    background: linear-gradient(90deg, #dc2626, #ef4444);
}}
.eg-card:hover {{
    border-color: #2563eb;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    transform: translateY(-2px);
}}

.eg-badge {{
    display: inline-block;
    font-size: 9px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 4px;
    margin-bottom: 8px;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.06em;
}}
.eg-badge.ok {{
    background: #dbeafe;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
}}
.eg-badge.alt {{
    background: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
}}
.eg-badge.out {{
    background: #fee2e2;
    color: #991b1b;
    border: 1px solid #fecaca;
}}

.eg-cn {{
    font-size: 12.5px;
    font-weight: 500;
    color: #0f172a;
    line-height: 1.4;
    margin-bottom: 6px;
    min-height: 30px;
}}
.eg-chr {{
    height: 1px;
    background: #e2e8f0;
    margin: 8px 0;
}}
.eg-cp {{
    font-size: 15px;
    font-weight: 700;
    color: #2563eb;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.02em;
}}
.eg-cr {{
    font-size: 9px;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}

/* ========================================================
   CHAT INPUT
   ======================================================== */
[data-testid="stBottomBlockContainer"],
section[data-testid="stBottom"],
[data-testid="stChatFloatingInputContainer"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
}}

[data-testid="stChatInput"] {{
    background: #ffffff !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 16px !important;
    padding: 4px 6px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    width: 100% !important;
    max-width: 680px !important;
    margin: 0 auto 20px auto !important;
    transition: all 0.15s !important;
}}
[data-testid="stChatInput"]:focus-within {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1), 0 2px 12px rgba(0,0,0,0.06) !important;
}}
[data-testid="stChatInput"] textarea {{
    background: transparent !important;
    border: none !important;
    color: #0f172a !important;
    font-size: 14.5px !important;
    padding: 12px 16px !important;
    min-height: 48px !important;
    font-family: 'Inter', sans-serif !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: #94a3b8 !important;
}}
[data-testid="stChatInput"] button {{
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border-radius: 12px !important;
    color: #fff !important;
    margin: 4px !important;
    min-width: 40px !important;
    min-height: 40px !important;
    transition: all 0.15s !important;
}}
[data-testid="stChatInput"] button:hover {{
    transform: scale(1.05) !important;
    box-shadow: 0 2px 12px rgba(37, 99, 235, 0.3) !important;
}}

/* Reset button */
.eg-reset-row {{
    background: transparent;
    padding: 0 20px 12px;
    display: flex;
    justify-content: center;
    flex-shrink: 0;
}}
.eg-reset-row .stButton > button {{
    background: transparent !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    color: #64748b !important;
    font-size: 12.5px !important;
    padding: 8px 20px !important;
    box-shadow: none !important;
    transition: all 0.15s !important;
}}
.eg-reset-row .stButton > button:hover {{
    background: #f8fafc !important;
    border-color: #94a3b8 !important;
    color: #0f172a !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────
if "chat" not in st.session_state:
    with st.spinner(""):
        st.session_state.chat = ChatManager()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "started" not in st.session_state:
    st.session_state.started = False

# ── Helpers ───────────────────────────────────────────────────
def product_cards_html(products: list) -> str:
    if not products:
        return ""
    cards = []
    for p in products[:4]:
        m        = p.get("metadata", {})
        nom      = esc(m.get("nom", "Produit"))
        prix     = m.get("prix", "—")
        stock    = str(m.get("statut_stock", ""))
        ref      = esc(p.get("id", ""))
        replaced = p.get("status") == "REPLACED"

        if "rupture" in stock.lower():
            cls, bc, bt = "out", "out", "Rupture"
        elif replaced:
            cls, bc, bt = "alt", "alt", "Alternative"
        else:
            cls, bc, bt = "ok",  "ok",  "Disponible"

        try:
            prix_fmt = f"{float(prix):,.0f}".replace(",", "\u202f") + " DA"
        except Exception:
            prix_fmt = f"{esc(str(prix))} DA"

        cards.append(
            f'<div class="eg-card {cls}">'
            f'<span class="eg-badge {bc}">{bt}</span>'
            f'<div class="eg-cn">{nom}</div>'
            f'<div class="eg-chr"></div>'
            f'<div class="eg-cp">{prix_fmt}</div>'
            f'<div class="eg-cr">Ref. {ref}</div>'
            f'</div>'
        )
    return '<div class="eg-cards">' + "".join(cards) + "</div>"

def render_message(msg: dict):
    role     = msg["role"]
    content  = esc(msg["content"]).replace("\n", "<br>")
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
        av_content = logo_img("22px", "50%") if LOGO_URI else "E"
        cards = product_cards_html(products)
        md(f"""
        <div class="eg-msg">
            <div class="eg-av ai">{av_content}</div>
            <div class="eg-bc">
                <div class="eg-bub ai">{content}{cards}</div>
                <div class="eg-mt">Energical · {t}</div>
            </div>
        </div>""")

# ══════════════════════════════════════════════════════════════
#  LANDING PAGE
# ══════════════════════════════════════════════════════════════
if not st.session_state.started:
    logo_content = LOGO_SM if LOGO_URI else "E"
    logo_content_lg = LOGO_LG if LOGO_URI else "E"

    md(f"""
    <div class="eg-topbar">
        <div class="eg-brand">
            <div class="eg-logo">{logo_content}</div>
            <span class="eg-brand-name">Energical</span>
            <div class="eg-vsep"></div>
            <span class="eg-brand-role">Conseiller produits</span>
        </div>
        <div class="eg-right">
            <div class="eg-online"><div class="eg-dot"></div>En ligne</div>
            <span class="eg-lang">FR · DZ · AR</span>
        </div>
    </div>
    """)

    md(f"""
    <div class="eg-landing">
        <div class="eg-landing-badge">
            <div class="eg-landing-badge-dot"></div>
            Assistant intelligent · Energical
        </div>
        <div class="eg-landing-icon">{logo_content_lg}</div>
        <div class="eg-landing-title">
            Trouvez le bon produit,<br><span>instantanement.</span>
        </div>
        <div class="eg-landing-sub">
            Posez votre question en français, darija ou arabe —
            chaudières, robinetterie, électricité, sanitaire.
            Je vous guide vers la meilleure référence Energical.
        </div>
        <div class="eg-features">
            <div class="eg-feat">Chaudières</div>
            <div class="eg-feat">Robinetterie</div>
            <div class="eg-feat">Électricité</div>
            <div class="eg-feat">Climatisation</div>
        </div>
    </div>
    """)

    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        if st.button("Commencer la conversation →", key="start_btn", use_container_width=True):
            st.session_state.started = True
            st.rerun()

# ══════════════════════════════════════════════════════════════
#  CHAT PAGE
# ══════════════════════════════════════════════════════════════
else:
    md('<div class="eg-chat-page">')

    # ── Empty state ──
    if not st.session_state.messages:
        logo_content_md = LOGO_MD if LOGO_URI else "E"

        md(f"""
        <div class="eg-empty-wrap">
            <div class="eg-empty-icon">{logo_content_md}</div>
            <div class="eg-empty-title">Quel produit recherchez-vous ?</div>
            <div class="eg-empty-sub">
                Choisissez une suggestion ou décrivez votre besoin ci-dessous.
            </div>
        </div>
        """)

        starters = [
            ("Chaudière gaz", "bghit chaudiere dial gaz"),
            ("Mitigeur lavabo", "je cherche un mitigeur lavabo chromé"),
            ("Disjoncteur 32A", "khasni disjoncteur 32A"),
        ]
        cols = st.columns(3)
        for col, (label, query) in zip(cols, starters):
            with col:
                if st.button(label, key=f"s_{query}", use_container_width=True):
                    t = time_label()
                    with st.spinner(""):
                        result = st.session_state.chat.send_message(query)
                    st.session_state.messages.append({"role": "user", "content": query, "time": t})
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["llm_answer"],
                        "products": result.get("retrieved_products", []) if result.get("allow_recommendation") else [],
                        "time": time_label(),
                    })
                    st.rerun()

    # ── Messages ──
    else:
        md('<div class="eg-scroll"><div class="eg-ci">')
        md('<div class="eg-divider">Aujourd\'hui</div>')
        for msg in st.session_state.messages:
            render_message(msg)
        md('</div></div>')

    md('</div>')

    # ── Input bar ──
    user_input = st.chat_input("Écrivez votre message...")

    if user_input:
        t = time_label()
        st.session_state.messages.append({"role": "user", "content": user_input, "time": t})
        with st.spinner(""):
            result = st.session_state.chat.send_message(user_input)
        st.session_state.messages.append({
            "role": "assistant",
            "content": result["llm_answer"],
            "products": result.get("retrieved_products", []) if result.get("allow_recommendation") else [],
            "time": time_label(),
        })
        st.rerun()

    # ── Reset button ──
    md('<div class="eg-reset-row">')
    if st.button("↺ Nouvelle conversation", key="reset"):
        del st.session_state["chat"]
        del st.session_state["messages"]
        st.session_state.started = False
        st.rerun()
    md('</div>')