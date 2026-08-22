import os
import json
import pandas as pd
import streamlit as st
import requests
import html as html_lib
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(
    page_title="LexAssist - AI Legal & Tax Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
API_URL = os.getenv("API_URL", "http://localhost:8000")
PAGE_SIZE = 10
MAX_QUERY_CHARS = 2000
TIMEOUT_SHORT = 10
TIMEOUT_MEDIUM = 30
TIMEOUT_LONG = 60

# --- Session State Initialization ---
for key, default in {
    "query_history": [], "logged_in": False, "user_id": None,
    "username": None, "token": None,
    "legal_messages": [], "tax_messages": [], "general_messages": [],
    "legal_prefill": "", "tax_prefill": "", "general_prefill": "",
    "history_page": 0, "history_filter": "All", "history_search": "",
    "auth_alert": None, "dark_mode": True,
    "legal_draft": "", "tax_draft": "", "general_draft": "",
    "current_page": "Home",
    "profile_alert": None,
    "chat_language": "English",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def auth_headers():
    return {"X-Auth-Token": st.session_state.token} if st.session_state.token else {}

def toast(msg: str, icon: str = "ℹ️"):
    st.toast(msg, icon=icon)

# ── Theme CSS ──────────────────────────────────────────────────────────────
def _build_theme_css(dark: bool) -> str:
    if dark:
        bg        = "#0e1117"
        bg2       = "#161b22"
        bg3       = "#1e2a3a"
        border    = "#2e4a6a"
        text      = "#fafafa"
        text2     = "#aaa"
        accent    = "#4da6ff"
        btn_bg    = "#1e2a3a"
        btn_text  = "#fafafa"
        btn_bdr   = "#2e4a6a"
        alert_bg  = "#1e2a3a"
        sb_bg     = "#111827"
        sb_bdr    = "#1f2d3d"
        sb_text   = "#9ca3af"
        sb_hover  = "#1e2a3a"
        sb_active = "#1d4ed8"
        hdr_color = "#4da6ff"
        disc_bg   = "#2a2200"
        disc_text = "#ffe082"
        rag_bg    = "#1a3a2a"
        rag_bdr   = "#28a745"
        rag_text  = "#66bb6a"
        resp_bg   = "#1e2a3a"
        resp_text = "#e8f4ff"
        resp_bdr  = "#2e4a6a"
        resp_shad = "0 4px 16px rgba(0,0,0,0.4)"
        scrl_bg   = "#0e1117"
        scrl_thm  = "#2e4a6a"
        tab_color = "#aaa"
        warn_clr  = "#ffc107"
        over_clr  = "#f44336"
        file_bg   = "#1e2a3a"
        chat_bg   = "#161b22"
        chat_text = "#e5e7eb"
    else:
        bg        = "#f5f7fa"
        bg2       = "#ffffff"
        bg3       = "#eaf1fb"
        border    = "#cce0ff"
        text      = "#111111"
        text2     = "#555555"
        accent    = "#1f77b4"
        btn_bg    = "#ffffff"
        btn_text  = "#111111"
        btn_bdr   = "#cce0ff"
        alert_bg  = "#e8f4ff"
        sb_bg     = "#1e293b"
        sb_bdr    = "#334155"
        sb_text   = "#94a3b8"
        sb_hover  = "#273549"
        sb_active = "#2563eb"
        hdr_color = "#1f77b4"
        disc_bg   = "#fff3cd"
        disc_text = "#7c4a00"
        rag_bg    = "#d4edda"
        rag_bdr   = "#28a745"
        rag_text  = "#155724"
        resp_bg   = "#ffffff"
        resp_text = "#111111"
        resp_bdr  = "#cce0ff"
        resp_shad = "0 2px 8px rgba(0,0,0,0.08)"
        scrl_bg   = "#f5f7fa"
        scrl_thm  = "#cce0ff"
        tab_color = "#555555"
        warn_clr  = "#e65100"
        over_clr  = "#c62828"
        file_bg   = "#ffffff"
        chat_bg   = "#f0f4f8"
        chat_text = "#111111"

    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    header[data-testid="stHeader"]   {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}

    html, body, [data-testid="stAppViewContainer"], .block-container, p, span, li, td, th, label, input, textarea, select {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    h1, h2, h3, h4, h5, h6, .main-header, .la-brand-name, .la-feat-title {{
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif !important;
        letter-spacing: -0.02em;
    }}

    html, body {{ background-color: {bg} !important; color: {text} !important; }}
    .stApp, .stApp > div,
    [data-testid="stAppViewContainer"],
    [data-testid="stToolbar"],
    [data-testid="stBottom"],
    [data-testid="stDecoration"],
    [data-testid="stChatInput"],
    [data-testid="stChatInputContainer"],
    .stChatFloatingInputContainer,
    .stChatInputContainer,
    .block-container, .main {{
        background-color: {bg} !important;
        color: {text} !important;
    }}

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"],
    section[data-testid="stSidebar"] > div {{
        background-color: {sb_bg} !important;
        border-right: 1px solid {sb_bdr} !important;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        width: 100% !important;
        text-align: left !important;
        background: transparent !important;
        color: {sb_text} !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        transition: background 0.15s, color 0.15s !important;
        margin-bottom: 2px !important;
        justify-content: flex-start !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: {sb_hover} !important;
        color: #e5e7eb !important;
        border: none !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: {sb_active} !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: none !important;
    }}
    [data-testid="stSidebar"] .la-logout .stButton > button {{
        color: #ef4444 !important;
        border: 1px solid #7f1d1d !important;
        background: transparent !important;
    }}
    [data-testid="stSidebar"] .la-logout .stButton > button:hover {{
        background: #7f1d1d !important;
        color: #fff !important;
        border-color: #ef4444 !important;
    }}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {{
        color: {sb_text} !important;
    }}

    input, textarea, select,
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    .stTextInput input, .stSelectbox select,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="select"] div {{
        background-color: {bg3} !important;
        color: {text} !important;
        border-color: {border} !important;
    }}
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputContainer"] textarea {{
        background-color: {bg3} !important;
        color: {text} !important;
    }}

    [data-testid="stFileUploader"] {{
        background-color: {file_bg} !important;
        border-color: {border} !important;
        color: {text} !important;
    }}
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p {{
        color: {text} !important;
    }}

    [data-testid="stChatMessage"] {{
        background-color: {chat_bg} !important;
        color: {chat_text} !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {{
        color: {chat_text} !important;
    }}

    p, span, li, td, th, label, div {{
        color: {text};
    }}
    h1, h2, h3, h4, h5, h6 {{ color: {text} !important; }}
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span {{
        color: {text} !important;
    }}

    [data-testid="stExpander"] {{
        background-color: {bg2} !important;
        border-color: {border} !important;
    }}
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {{
        color: {text} !important;
    }}
    [data-testid="stExpander"] p,
    [data-testid="stExpander"] div {{
        color: {text} !important;
    }}

    .block-container .stButton > button {{
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        border-color: {btn_bdr} !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease !important;
        border-radius: 8px !important;
    }}
    .block-container .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(96, 165, 250, 0.3) !important;
    }}
    .block-container .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 600 !important;
    }}
    .block-container .stButton > button[kind="primary"]:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.45) !important;
    }}

    [data-testid="stSidebar"] .stButton > button {{
        transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        transform: translateX(4px) !important;
    }}

    [data-testid="stTabs"] [role="tab"] {{
        color: {tab_color} !important;
        transition: color 0.2s ease, border-bottom-color 0.2s ease !important;
    }}
    [data-testid="stTabs"] [role="tab"]:hover {{
        color: {accent} !important;
    }}
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
        color: {accent} !important;
        border-bottom-color: {accent} !important;
    }}
    [data-testid="stTabs"] {{ background-color: {bg} !important; }}

    [data-testid="stMetric"] {{ background-color: {bg2} !important; }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: {text} !important; }}

    [data-testid="stAlert"] {{
        background-color: {alert_bg} !important;
        color: {text} !important;
    }}
    [data-testid="stAlert"] p {{ color: {text} !important; }}

    [data-baseweb="popover"] ul,
    [data-baseweb="menu"] {{
        background-color: {bg2} !important;
        color: {text} !important;
    }}
    [data-baseweb="menu"] li {{ color: {text} !important; }}
    [data-baseweb="menu"] li:hover {{ background-color: {bg3} !important; }}

    [data-testid="stProgress"] > div {{ background-color: {border} !important; }}
    [data-testid="stProgress"] > div > div {{ background-color: {accent} !important; }}

    table {{ background-color: {bg2} !important; color: {text} !important; }}
    th {{ background-color: {bg3} !important; color: {text} !important; }}
    td {{ color: {text} !important; border-color: {border} !important; }}

    ::-webkit-scrollbar {{ background: {scrl_bg}; }}
    ::-webkit-scrollbar-thumb {{ background: {scrl_thm}; border-radius: 4px; }}

    .main-header {{
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa 0%, #c084fc 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1.2rem;
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em;
    }}
    .sub-header {{ font-size: 1.2rem; color: {text2}; text-align: center; margin-bottom: 2rem; }}
    .disclaimer-box {{
        background: rgba(42, 34, 0, 0.7) !important;
        border-left: 5px solid #ffc107;
        padding: 1rem; margin: 1rem 0; border-radius: 8px;
        color: {disc_text} !important;
        backdrop-filter: blur(10px);
    }}
    .disclaimer-box strong {{ color: {disc_text} !important; }}
    .rag-badge {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.18), rgba(59, 130, 246, 0.18));
        border: 1px solid rgba(52, 211, 153, 0.4);
        padding: 0.35rem 0.9rem; border-radius: 20px;
        color: #34d399; font-size: 0.85rem; display: inline-block; margin-bottom: 1rem;
        font-weight: 600;
        backdrop-filter: blur(8px);
    }}
    .auth-divider {{ text-align: center; color: {text2}; margin: 1rem 0; font-size: 0.85rem; }}
    .response-box {{
        background: rgba(30, 42, 58, 0.75) !important;
        color: {resp_text} !important;
        padding: 1.5rem; border-radius: 14px;
        border: 1px solid rgba(96, 165, 250, 0.25);
        margin: 1rem 0; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(12px);
    }}
    [data-testid="stMetric"] {{
        background: rgba(22, 27, 34, 0.75) !important;
        border: 1px solid rgba(96, 165, 250, 0.2) !important;
        border-radius: 14px !important;
        padding: 0.8rem 1rem !important;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }}
    [data-testid="stExpander"] {{
        background: rgba(22, 27, 34, 0.7) !important;
        border: 1px solid rgba(96, 165, 250, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
    }}
    .char-counter {{ font-size: 0.78rem; color: #888; text-align: right; margin-top: -0.5rem; margin-bottom: 0.5rem; }}
    .char-counter.warn {{ color: {warn_clr}; }}
    .char-counter.over  {{ color: {over_clr}; }}
</style>
"""

st.markdown(_build_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)
st.markdown('<a name="top" style="display:none"></a>', unsafe_allow_html=True)

def _char_counter_html(text: str) -> str:
    n = len(text)
    cls = "over" if n > MAX_QUERY_CHARS else "warn" if n > int(MAX_QUERY_CHARS * 0.85) else ""
    return f'<div class="char-counter {cls}">{n} / {MAX_QUERY_CHARS}</div>'

def _copy_button(text: str, key: str):
    escaped = html_lib.escape(text, quote=True)
    components.html(
        f"""
        <textarea id="cb_{key}" style="position:absolute;left:-9999px;">{escaped}</textarea>
        <button onclick="
            var t=document.getElementById('cb_{key}');t.select();t.setSelectionRange(0,99999);
            navigator.clipboard.writeText(t.value).then(function(){{
                this.innerText='\u2705 Copied!';var b=this;
                setTimeout(function(){{b.innerText='\U0001f4cb Copy';}},1500);
            }}.bind(this)).catch(function(){{
                document.execCommand('copy');
                this.innerText='\u2705 Copied!';var b=this;
                setTimeout(function(){{b.innerText='\U0001f4cb Copy';}},1500);
            }}.bind(this));"
                style="background:#1f77b4;color:#fff;border:none;padding:4px 12px;border-radius:6px;cursor:pointer;font-size:0.8rem;margin-top:4px">
            \U0001f4cb Copy
        </button>
        """,
        height=44,
    )

def show_login_page():
    dark = st.session_state.dark_mode
    card_bg     = "#161b22" if dark else "#ffffff"
    card_bdr    = "#2e4a6a" if dark else "#dde6f0"
    card_shadow = "0 8px 32px rgba(0,0,0,0.45)" if dark else "0 4px 24px rgba(0,0,0,0.10)"
    feat_bg     = "#1e2a3a" if dark else "#f0f6ff"
    feat_bdr    = "#2e4a6a" if dark else "#cce0ff"
    feat_text   = "#e5e7eb" if dark else "#1a2a3a"
    feat_sub    = "#9ca3af" if dark else "#4a6080"
    page_bg     = "#0e1117" if dark else "#f0f4f8"

    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }}
    .stApp, [data-testid="stAppViewContainer"], .main {{
        background: {page_bg} !important;
    }}
    .la-login-wrap {{
        background: {card_bg};
        border: 1px solid {card_bdr};
        border-radius: 18px;
        box-shadow: {card_shadow};
        padding: 2.2rem 2rem 1.8rem;
        margin-top: 0;
    }}
    .la-brand-icon {{ text-align: center; display: flex; justify-content: center; margin-bottom: 0.4rem; }}
    .la-brand-name {{
        text-align: center; font-size: 1.9rem; font-weight: 800;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }}
    .la-brand-sub {{
        text-align: center; color: {feat_sub}; font-size: 0.88rem; margin-bottom: 1.4rem;
    }}
    .la-feat-card {{
        background: {feat_bg}; border: 1px solid {feat_bdr};
        border-radius: 14px; padding: 1.1rem 1rem;
        text-align: center; height: 100%;
        transition: transform 0.15s;
    }}
    .la-feat-card:hover {{ transform: translateY(-3px); }}
    .la-feat-title {{ font-size: 0.95rem; font-weight: 700; color: {feat_text}; margin-bottom: 0.25rem; }}
    .la-feat-desc  {{ font-size: 0.8rem; color: {feat_sub}; line-height: 1.5; }}
    .la-trust {{
        text-align: center; color: {feat_sub}; font-size: 0.78rem;
        margin-top: 1rem; padding-top: 0.9rem;
        border-top: 1px solid {card_bdr};
    }}
    .la-trust span {{ margin: 0 0.5rem; }}
    </style>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(
            '<div class="la-login-wrap">'
            '<div class="la-brand-icon">'
            '<svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M12 3L3 7l9 4 9-4-9-4z"/><path d="M3 12l9 4 9-4"/><path d="M3 17l9 4 9-4"/>'
            '</svg></div>'
            '<div class="la-brand-name">LexAssist</div>'
            '<div class="la-brand-sub">AI-powered legal &amp; tax assistant for Indian law</div>',
            unsafe_allow_html=True
        )

        tab1, tab2 = st.tabs(["Sign In", "Create Account"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

            if submit:
                if username.strip() and password.strip():
                    with st.spinner("Signing you in..."):
                        try:
                            response = requests.post(
                                f"{API_URL}/login",
                                json={"username": username.strip(), "password": password},
                                timeout=TIMEOUT_SHORT
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.logged_in = True
                                st.session_state.user_id = data["user_id"]
                                st.session_state.username = data["username"]
                                st.session_state.token = data["token"]
                                st.rerun()
                            elif response.status_code == 429:
                                st.session_state.auth_alert = ("error", "Too many login attempts. Please wait a minute and try again.")
                                st.rerun()
                            else:
                                st.session_state.auth_alert = ("error", "That username or password doesn't look right. Please try again.")
                                st.rerun()
                        except requests.exceptions.ConnectionError:
                            st.session_state.auth_alert = ("error", "Could not reach the server. Please try again shortly.")
                            st.rerun()
                else:
                    st.session_state.auth_alert = ("warning", "Please fill in both your username and password.")
                    st.rerun()

        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Choose a username", placeholder="Pick something you'll remember")
                new_password = st.text_input("Choose a password", type="password", placeholder="At least 6 characters")
                confirm_password = st.text_input("Confirm your password", type="password", placeholder="Type it again")
                submit_reg = st.form_submit_button("Create Account →", type="primary", use_container_width=True)

            if submit_reg:
                if new_username.strip() and new_password.strip() and confirm_password.strip():
                    if len(new_password) < 6:
                        st.session_state.auth_alert = ("error", "Password should be at least 6 characters long.")
                        st.rerun()
                    elif new_password != confirm_password:
                        st.session_state.auth_alert = ("error", "The passwords you entered don't match. Please try again.")
                        st.rerun()
                    else:
                        with st.spinner("Creating your account..."):
                            try:
                                response = requests.post(
                                    f"{API_URL}/register",
                                    json={"username": new_username.strip(), "password": new_password},
                                    timeout=TIMEOUT_SHORT
                                )
                                if response.status_code == 200:
                                    login_resp = requests.post(
                                        f"{API_URL}/login",
                                        json={"username": new_username.strip(), "password": new_password},
                                        timeout=TIMEOUT_SHORT
                                    )
                                    if login_resp.status_code == 200:
                                        data = login_resp.json()
                                        st.session_state.logged_in = True
                                        st.session_state.user_id = data["user_id"]
                                        st.session_state.username = data["username"]
                                        st.session_state.token = data["token"]
                                        st.rerun()
                                    else:
                                        st.session_state.auth_alert = ("success", "Account created! Head over to Sign In to get started.")
                                        st.rerun()
                                else:
                                    st.session_state.auth_alert = ("error", "That username is already taken. Try a different one.")
                                    st.rerun()
                            except requests.exceptions.ConnectionError:
                                st.session_state.auth_alert = ("error", "Could not reach the server. Please try again shortly.")
                                st.rerun()
                else:
                    st.session_state.auth_alert = ("warning", "Please fill in all three fields to create your account.")
                    st.rerun()

        st.markdown(
            '<div class="la-trust">'
            '<span>Secure</span><span>Indian Law</span><span>AI-Powered</span><span>Document Analysis</span>'
            '</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _, c1, c2, c3, c4, _ = st.columns([0.5, 1, 1, 1, 1, 0.5])
    features = [
        (c1, "Legal Questions", "Ask anything about IPC, Constitution, or CrPC in plain language."),
        (c2, "Tax Guidance", "Understand Income Tax, GST, and deductions without the jargon."),
        (c3, "Document Analysis", "Upload any legal document and get a simple explanation."),
        (c4, "Contract Risks", "Detect risky clauses and missing terms in any contract."),
    ]
    for col, title, desc in features:
        with col:
            st.markdown(
                f'<div class="la-feat-card">'
                f'<div class="la-feat-title">{title}</div>'
                f'<div class="la-feat-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

def show_chat_page(category: str, page_title: str):
    messages_key = f"{category}_messages"
    prefill_key = f"{category}_prefill"
    draft_key = f"{category}_draft"

    def _do_ask(query: str):
        st.session_state[messages_key].append({"role": "user", "content": query})
        with st.spinner("Generating answer..."):
            try:
                history_to_send = st.session_state[messages_key][:-1]
                resp = requests.post(
                    f"{API_URL}/ask",
                    json={"query": query, "category": category,
                          "history": [{"role": m["role"], "content": m["content"]} for m in history_to_send],
                          "language": st.session_state.chat_language},
                    headers=auth_headers(),
                    timeout=TIMEOUT_LONG
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state[messages_key].append({
                        "role": "assistant",
                        "content": data["response"],
                        "suggestions": data.get("suggested_questions", []),
                        "sources": data.get("sources", []),
                    })
                    st.session_state.query_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": query, "category": category
                    })
                    toast("Answer ready!", "✅")
                elif resp.status_code == 400:
                    toast("Invalid query — please rephrase.", "⚠️")
                    st.session_state[messages_key].append({"role": "assistant", "content": "Invalid query. Please rephrase your question."})
                else:
                    toast("Something went wrong. Please try again.", "❌")
                    st.session_state[messages_key].append({"role": "assistant", "content": "Something went wrong. Please try again."})
            except Exception:
                toast("Could not reach the server.", "❌")
                st.session_state[messages_key].append({"role": "assistant", "content": "Could not reach the server. Please try again shortly."})

    # Auto-execute captured voice query if passed via query params or prefill
    vq_param = st.query_params.get("voice_query", "")
    if vq_param and vq_param.strip():
        try:
            del st.query_params["voice_query"]
        except Exception:
            pass
        _do_ask(vq_param.strip())
        st.rerun()

    prefill_query = st.session_state.get(prefill_key, "")
    if prefill_query:
        st.session_state[prefill_key] = ""
        _do_ask(prefill_query)
        st.rerun()

    st.markdown(f'<div class="main-header">{page_title}</div>', unsafe_allow_html=True)

    ctrl_col, lang_col = st.columns([3, 1])
    with lang_col:
        language = st.selectbox(
            "🌐 Language",
            ["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Marathi", "Gujarati"],
            index=["English", "Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali", "Marathi", "Gujarati"].index(
                st.session_state.chat_language
            ),
            key=f"{category}_lang"
        )
        if language != st.session_state.chat_language:
            st.session_state.chat_language = language
            st.rerun()
    with ctrl_col:
        st.markdown('<div class="rag-badge">RAG-Enhanced answers from Indian legal documents</div>', unsafe_allow_html=True)

    components.html(
        f"""
        <style>
        @keyframes pulse-ring_{category} {{
          0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }}
          70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }}
          100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
        }}
        .mic-active_{category} {{
          animation: pulse-ring_{category} 1.5s infinite !important;
          background: linear-gradient(135deg, #b91c1c, #ef4444) !important;
          border-color: #f87171 !important;
          color: #ffffff !important;
        }}
        </style>
        <div style="margin:4px 0; display:flex; align-items:center; gap:12px;">
          <button id="voiceBtn_{category}" onclick="startVoice_{category}()"
            style="background:linear-gradient(135deg, #1e293b, #0f172a); color:#60a5fa;
                   border:1px solid rgba(96,165,250,0.4); padding:8px 18px; border-radius:24px;
                   cursor:pointer; font-size:0.88rem; font-weight:600; font-family:sans-serif;
                   display:inline-flex; align-items:center; gap:8px; box-shadow:0 4px 14px rgba(0,0,0,0.3); transition:all 0.2s ease;">
            <span id="micIcon_{category}" style="font-size:1.1rem">🎙️</span>
            <span id="btnText_{category}">Ask with Voice</span>
          </button>
          <span id="voiceStatus_{category}" style="color:#9ca3af; font-size:0.82rem; font-family:sans-serif;"></span>
        </div>
        <script>
        function fixSpokenNumbers(text) {{
          if (!text) return text;
          var t = text.trim();
          t = t.replace(/\\b(section|sec|u\\/s|under section)\\s+(\\d+)\\s+([a-z])\\b/gi, function(m, p1, p2, p3) {{
            return 'Section ' + p2 + p3.toUpperCase();
          }});
          t = t.replace(/\\beighty\\s*c\\b/gi, '80C');
          t = t.replace(/\\b80\\s*c\\b/gi, '80C');
          t = t.replace(/\\b80\\s*d\\b/gi, '80D');
          t = t.replace(/\\bfour\\s*hundred\\s*twenty\\b/gi, '420');
          t = t.replace(/\\bfour\\s*twenty\\b/gi, '420');
          t = t.replace(/\\bthree\\s*hundred\\s*two\\b/gi, '302');
          t = t.replace(/\\bthree\\s*zero\\s*two\\b/gi, '302');
          t = t.replace(/\\bthree\\s*hundred\\s*seventy\\b/gi, '370');
          t = t.replace(/\\bthree\\s*seventy\\b/gi, '370');
          return t;
        }}

        function startVoice_{category}() {{
          if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
            document.getElementById('voiceStatus_{category}').innerText = '⚠️ Speech recognition not supported in this browser.';
            return;
          }}
          var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          var rec = new SR();
          rec.lang = 'en-IN';
          rec.continuous = false;
          rec.interimResults = false;
          rec.maxAlternatives = 3;
          
          var btn = document.getElementById('voiceBtn_{category}');
          btn.classList.add('mic-active_{category}');
          document.getElementById('micIcon_{category}').innerText = '🔴';
          document.getElementById('btnText_{category}').innerText = 'Listening...';
          document.getElementById('voiceStatus_{category}').innerText = 'Speak your legal or tax question clearly...';
          btn.disabled = true;

          rec.onresult = function(e) {{
            var rawTranscript = e.results[0][0].transcript;
            var cleanTranscript = fixSpokenNumbers(rawTranscript);
            
            document.getElementById('btnText_{category}').innerText = 'Answering...';
            document.getElementById('voiceStatus_{category}').innerHTML = '⚡ <b>Answering:</b> "' + cleanTranscript + '"';
            
            // Auto-submit speech query directly to Streamlit app
            var url = new URL(window.parent.location.href);
            url.searchParams.set('voice_query', cleanTranscript);
            window.parent.location.href = url.toString();
          }};

          rec.onerror = function(e) {{
            document.getElementById('voiceStatus_{category}').innerText = 'Error: ' + e.error;
            btn.classList.remove('mic-active_{category}');
            document.getElementById('micIcon_{category}').innerText = '🎙️';
            document.getElementById('btnText_{category}').innerText = 'Ask with Voice';
            btn.disabled = false;
          }};

          rec.onend = function() {{
            if (document.getElementById('btnText_{category}').innerText === 'Listening...') {{
              document.getElementById('voiceStatus_{category}').innerText = 'No speech detected. Click to try again.';
              btn.classList.remove('mic-active_{category}');
              document.getElementById('micIcon_{category}').innerText = '🎙️';
              document.getElementById('btnText_{category}').innerText = 'Ask with Voice';
              btn.disabled = false;
            }}
          }};

          rec.start();
        }}
        </script>
        """,
        height=65,
    )

    for idx, msg in enumerate(st.session_state[messages_key]):
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                _copy_button(msg["content"], key=f"{category}_copy_{idx}")
                components.html(
                    f"""
                    <button onclick="
                        var w=window.open('','_blank');
                        w.document.write('<html><head><title>LexAssist Response</title>'
                            +'<style>body{{font-family:Arial,sans-serif;padding:2rem;max-width:800px;margin:auto}}'
                            +'h3{{color:#1f77b4}}pre{{white-space:pre-wrap;word-wrap:break-word}}</style></head>'
                            +'<body><h3>LexAssist Response</h3><pre>'+{json.dumps(msg['content'])}+'</pre></body></html>');
                        w.document.close();w.print();"
                        style="background:#374151;color:#d1d5db;border:none;padding:4px 12px;
                               border-radius:6px;cursor:pointer;font-size:0.8rem;margin-top:4px;margin-left:6px">
                        🖨️ Print / PDF
                    </button>
                    """,
                    height=44,
                )
                if msg.get("sources"):
                    with st.expander(f"📚 Sources ({len(msg['sources'])} chunks used)", expanded=False):
                        for si, src in enumerate(msg["sources"], 1):
                            st.markdown(f"**{si}.** {src}")
                if msg.get("suggestions"):
                    st.markdown("**Suggested follow-up questions:**")
                    for i, s in enumerate(msg["suggestions"]):
                        if st.button(s, key=f"{category}_sugg_{idx}_{i}", use_container_width=True):
                            st.session_state[prefill_key] = s
                            st.rerun()

    last_draft = st.session_state.get(draft_key, "")
    if last_draft:
        st.markdown(_char_counter_html(last_draft), unsafe_allow_html=True)

    user_input = st.chat_input(f"Ask a {category} question... (max {MAX_QUERY_CHARS} chars)")
    if user_input:
        stripped = user_input.strip()
        if stripped:
            if len(stripped) > MAX_QUERY_CHARS:
                st.session_state[draft_key] = stripped
                toast(f"Query too long — max {MAX_QUERY_CHARS} characters.", "⚠️")
                st.rerun()
            else:
                st.session_state[draft_key] = stripped
                _do_ask(stripped)
                st.session_state[draft_key] = ""
        st.rerun()

    if st.session_state[messages_key]:
        if st.button("Clear conversation", key=f"{category}_clear"):
            st.session_state[messages_key] = []
            toast("Conversation cleared.", "🗑️")
            st.rerun()

def show_home_page():
    st.markdown('<div class="main-header">Welcome to LexAssist</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Your AI-Powered Legal and Tax Assistant for Indian Law</div>', unsafe_allow_html=True)
    st.markdown('<div class="rag-badge">RAG-Enhanced: Answers grounded in real Indian legal documents</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    features = [
        (col1, "Legal Assistance", "IPC sections, Constitutional articles, and legal rights.", "Ask Legal Question"),
        (col2, "Tax Guidance", "Income Tax Act, GST, deductions, and filing rules.", "Tax Assistant"),
        (col3, "General Assistant", "Ask any civic or legal query about Indian governance.", "General Assistant"),
        (col4, "Doc Analysis", "Upload legal documents for plain-language explanations.", "Document Explanation"),
        (col5, "Contract Risks", "Detect risky clauses & missing terms in agreements.", "Contract Risk Analyzer")
    ]
    for col, title, desc, page_target in features:
        with col:
            st.markdown(f"### {title}")
            st.write(desc)
            if st.button(f"Open →", key=f"hp_nav_{page_target}", use_container_width=True):
                st.session_state.current_page = page_target
                st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Quick Sample Questions — Click to Ask")
    q_col1, q_col2, q_col3 = st.columns(3)
    sample_queries = [
        (q_col1, "What are the legal rights of an arrested person under CrPC?", "legal", "Ask Legal Question"),
        (q_col2, "How is Section 80C deduction calculated under Income Tax?", "tax", "Tax Assistant"),
        (q_col3, "What is the legal procedure for filing a Consumer Complaint in India?", "general", "General Assistant")
    ]
    for q_col, query_text, cat, target_page in sample_queries:
        with q_col:
            if st.button(f"❓ {query_text}", key=f"sq_{cat}", use_container_width=True):
                st.session_state[f"{cat}_prefill"] = query_text
                st.session_state.current_page = target_page
                st.rerun()

    st.markdown("---")
    st.markdown('<div class="disclaimer-box"><strong>Disclaimer:</strong> LexAssist provides general information only and is not a substitute for professional legal or tax advice.</div>', unsafe_allow_html=True)

def show_contract_risk_analyzer():
    st.markdown('<div class="main-header">⚠️ Contract Risk Analyzer</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(30,42,58,0.6);border:1px solid rgba(96,165,250,0.25);border-radius:12px;padding:1.2rem;margin-bottom:1.2rem;backdrop-filter:blur(10px)">
        <h4 style="margin:0 0 0.4rem 0;color:#60a5fa">🛡️ Automated Legal Clause Risk Audit</h4>
        <p style="margin:0;font-size:0.88rem;color:#9ca3af">
            Upload any agreement, NDA, vendor contract, or lease (PDF, TXT, or DOCX). Our RAG engine scans the document under the <b>Indian Contract Act 1872</b> to detect risky clauses, hidden liabilities, missing terms, and generate actionable risk mitigation recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a contract document", type=["pdf", "txt", "docx"], key="contract_upload")
    if uploaded_file:
        st.info(f"📄 **File Selected:** `{uploaded_file.name}` ({uploaded_file.size:,} bytes)")
        if st.button("🔍 Analyze Contract Risks", type="primary", use_container_width=True):
            with st.spinner("Analyzing contract clauses under Indian Contract Act..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_URL}/analyze-contract", files=files, headers=auth_headers(), timeout=TIMEOUT_LONG)
                    if response.status_code == 200:
                        data = response.json()["analysis"]

                        score = data.get("risk_score", 0)
                        color = "🟢 Low Risk" if score <= 3 else "🟡 Moderate Risk" if score <= 6 else "🔴 High Risk"
                        
                        st.markdown("---")
                        c_score, c_summary = st.columns([1, 2])
                        with c_score:
                            st.markdown(f"### {color}")
                            st.markdown(f"<h2 style='color:#60a5fa;margin:0'>Score: {score}/10</h2>", unsafe_allow_html=True)
                            st.progress(score / 10)
                        with c_summary:
                            st.markdown("### 📋 Executive Audit Summary")
                            st.write(data.get('summary', 'N/A'))

                        risks = data.get("risks", [])
                        if risks:
                            st.markdown("---\n### 🚨 Identified Clause Risks")
                            for r in risks:
                                sev = r.get("severity", "Medium")
                                badge = "🔴 High Severity" if sev == "High" else "🟡 Medium Severity" if sev == "Medium" else "🟢 Low Severity"
                                with st.expander(f"{badge} — {r.get('clause', 'Clause')}", expanded=True):
                                    st.markdown(f"**Risk Analysis:** {r.get('risk', '')}")

                        missing = data.get("missing_clauses", [])
                        if missing:
                            st.markdown("---\n### 📋 Essential Missing Clauses")
                            for m in missing:
                                st.markdown(f"- 🔴 **Missing:** {m}")

                        recs = data.get("recommendations", [])
                        if recs:
                            st.markdown("---\n### ✅ Actionable Recommendations")
                            for rec in recs:
                                st.markdown(f"- 💡 {rec}")

                        st.markdown('<div class="disclaimer-box"><strong>Disclaimer:</strong> This contract analysis is AI-assisted and provided for informational review only. Always consult a licensed advocate before signing.</div>', unsafe_allow_html=True)
                        toast("Contract analysis complete!", "✅")
                    else:
                        toast("Could not analyze the contract. Please try again.", "❌")
                except Exception:
                    toast("Could not reach the server. Please try again shortly.", "❌")

def show_compare_contracts():
    st.markdown('<div class="main-header">📊 Compare Contracts</div>', unsafe_allow_html=True)
    st.write("Upload two contracts to compare them side by side — clauses, differences, and recommendations.")
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.file_uploader("Contract 1", type=["pdf", "txt", "docx"], key="compare_file1")
    with col2:
        file2 = st.file_uploader("Contract 2", type=["pdf", "txt", "docx"], key="compare_file2")
    if file1 and file2:
        if st.button("Compare Contracts", type="primary"):
            with st.spinner("Comparing contracts..."):
                try:
                    files = {
                        "file1": (file1.name, file1.getvalue(), file1.type),
                        "file2": (file2.name, file2.getvalue(), file2.type),
                    }
                    resp = requests.post(f"{API_URL}/compare-contracts", files=files, headers=auth_headers(), timeout=TIMEOUT_LONG)
                    if resp.status_code == 200:
                        data = resp.json()["comparison"]
                        st.markdown(f"**Summary:** {data.get('summary', '')}")
                        st.markdown(f"**Recommendation:** {data.get('recommendation', '')}")
                        st.markdown("---")
                        d1, d2, d3 = st.columns(3)
                        with d1:
                            st.markdown("### 🔄 Common Clauses")
                            for c in data.get("common_clauses", []):
                                st.markdown(f"- {c}")
                        with d2:
                            st.markdown(f"### 📄 Only in {file1.name}")
                            for c in data.get("unique_to_contract1", []):
                                st.markdown(f"- {c}")
                        with d3:
                            st.markdown(f"### 📄 Only in {file2.name}")
                            for c in data.get("unique_to_contract2", []):
                                st.markdown(f"- {c}")
                        diffs = data.get("key_differences", [])
                        if diffs:
                            st.markdown("---\n### ⚠️ Key Differences")
                            diff_rows = [{"Aspect": d["aspect"], file1.name: d["contract1"], file2.name: d["contract2"]} for d in diffs]
                            st.table(diff_rows)
                        toast("Comparison complete!", "✅")
                    else:
                        toast("Could not compare contracts. Please try again.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")
    elif file1 or file2:
        st.info("Please upload both contracts to compare.")

def show_case_law_search():
    st.markdown('<div class="main-header">🔍 Case Law Search</div>', unsafe_allow_html=True)
    st.write("Search relevant Supreme Court and High Court judgments on any Indian legal topic.")
    query = st.text_input("Enter your legal query", placeholder="e.g. right to privacy, bail conditions, dowry harassment")
    if st.button("Search Case Law", type="primary", disabled=not query.strip()):
        with st.spinner("Searching case law..."):
            try:
                resp = requests.post(f"{API_URL}/case-law-search", json={"query": query.strip()}, headers=auth_headers(), timeout=TIMEOUT_LONG)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        st.success(f"Found {len(results)} relevant cases")
                        for case in results:
                            court_badge = "🔵" if "Supreme" in case.get("court", "") else "🟢"
                            with st.expander(f"{court_badge} {case.get('case_name', 'Unknown')} ({case.get('year', '')})"):
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"**Court:** {case.get('court', 'N/A')}")
                                    st.markdown(f"**Citation:** {case.get('citation', 'N/A')}")
                                with c2:
                                    st.markdown(f"**Year:** {case.get('year', 'N/A')}")
                                st.markdown(f"**Summary:** {case.get('summary', '')}")
                                st.markdown(f"**Relevance:** {case.get('relevance', '')}")
                    else:
                        st.info("No cases found. Try a different query.")
                else:
                    toast("Search failed. Please try again.", "❌")
            except Exception:
                toast("Could not reach the server.", "❌")

def show_draft_document():
    st.markdown('<div class="main-header">📝 Draft Document</div>', unsafe_allow_html=True)
    st.write("Generate professional legal document drafts based on your details.")
    doc_type = st.selectbox("Document Type", [
        "Rent Agreement", "Non-Disclosure Agreement (NDA)", "Employment Offer Letter",
        "Legal Notice", "Affidavit", "Partnership Deed", "Sale Agreement",
        "Power of Attorney", "Cease and Desist Letter", "Demand Notice"
    ])
    st.markdown("#### Fill in the details")
    details = {}
    if doc_type == "Rent Agreement":
        c1, c2 = st.columns(2)
        with c1:
            details["Landlord Name"] = st.text_input("Landlord Name")
            details["Tenant Name"] = st.text_input("Tenant Name")
            details["Property Address"] = st.text_input("Property Address")
        with c2:
            details["Monthly Rent"] = st.text_input("Monthly Rent (₹)")
            details["Security Deposit"] = st.text_input("Security Deposit (₹)")
            details["Lease Duration"] = st.text_input("Lease Duration (months)")
        details["Start Date"] = st.text_input("Start Date")
    elif doc_type == "Non-Disclosure Agreement (NDA)":
        c1, c2 = st.columns(2)
        with c1:
            details["Disclosing Party"] = st.text_input("Disclosing Party")
            details["Receiving Party"] = st.text_input("Receiving Party")
        with c2:
            details["Purpose"] = st.text_input("Purpose of Disclosure")
            details["Duration"] = st.text_input("Confidentiality Duration")
    elif doc_type == "Legal Notice":
        c1, c2 = st.columns(2)
        with c1:
            details["Sender Name"] = st.text_input("Sender Name")
            details["Recipient Name"] = st.text_input("Recipient Name")
        with c2:
            details["Subject"] = st.text_input("Subject of Notice")
            details["Relief Sought"] = st.text_input("Relief Sought")
        details["Facts"] = st.text_area("Brief Facts", height=80)
    elif doc_type == "Affidavit":
        details["Deponent Name"] = st.text_input("Deponent Name")
        details["Purpose"] = st.text_input("Purpose of Affidavit")
        details["Facts"] = st.text_area("Facts to be stated", height=80)
        details["Place"] = st.text_input("Place")
    else:
        c1, c2 = st.columns(2)
        with c1:
            details["Party 1"] = st.text_input("Party 1 Name")
            details["Party 2"] = st.text_input("Party 2 Name")
        with c2:
            details["Date"] = st.text_input("Date")
            details["Jurisdiction"] = st.text_input("Jurisdiction/City")
        details["Additional Details"] = st.text_area("Additional Details", height=80)

    if st.button("Generate Draft", type="primary"):
        if not any(v.strip() for v in details.values() if isinstance(v, str)):
            toast("Please fill in at least some details.", "⚠️")
        else:
            with st.spinner("Drafting document..."):
                try:
                    resp = requests.post(f"{API_URL}/draft-document",
                        json={"doc_type": doc_type, "details": details},
                        headers=auth_headers(), timeout=TIMEOUT_LONG)
                    if resp.status_code == 200:
                        draft = resp.json().get("draft", "")
                        st.markdown("---")
                        st.markdown(f"### 📄 {doc_type} Draft")
                        st.text_area("Generated Draft", value=draft, height=400)
                        st.download_button("⬇ Download as TXT", data=draft,
                            file_name=f"{doc_type.replace(' ', '_')}_draft.txt",
                            mime="text/plain")
                        toast("Draft generated!", "✅")
                    else:
                        toast("Could not generate draft. Please try again.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")

# --- Helper views for auxiliary modules ---
def show_section_lookup():
    st.markdown('<div class="main-header">📌 Section Lookup</div>', unsafe_allow_html=True)
    st.write("Search details regarding specific IPC sections, Income Tax sections, or Constitutional articles.")
    c1, c2 = st.columns([2, 1])
    with c1:
        act = st.text_input("Act Name", value="Indian Penal Code (IPC)", placeholder="e.g. Indian Penal Code, Income Tax Act, Constitution of India")
    with c2:
        section = st.text_input("Section / Article Number", placeholder="e.g. 302, 80C, 21")

    if st.button("Lookup Section", type="primary", disabled=not (act.strip() and section.strip())):
        with st.spinner("Looking up section..."):
            try:
                resp = requests.post(
                    f"{API_URL}/section-lookup",
                    json={"act": act.strip(), "section": section.strip()},
                    headers=auth_headers(),
                    timeout=TIMEOUT_MEDIUM
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.markdown(f"### 📜 {data.get('act', act)} — Section {data.get('section', section)}")
                    if data.get("title"):
                        st.markdown(f"#### {data.get('title')}")
                    if data.get("text"):
                        st.info(f"**Statutory Text:**\n{data.get('text')}")
                    if data.get("explanation"):
                        st.markdown(f"**Explanation:**\n{data.get('explanation')}")
                    if data.get("punishment"):
                        st.warning(f"**Punishment / Penalty:** {data.get('punishment')}")
                    if data.get("related_sections"):
                        st.markdown(f"**Related Sections:** {', '.join(data.get('related_sections'))}")
                    if data.get("landmark_cases"):
                        st.markdown(f"**Landmark Cases:** {', '.join(data.get('landmark_cases'))}")
                else:
                    st.info("Section details not found or error looking up section.")
            except Exception:
                toast("Could not reach the server.", "❌")

def show_legal_timeline():
    st.markdown('<div class="main-header">🗓️ Legal Timeline</div>', unsafe_allow_html=True)
    st.write("Generate a step-by-step legal procedure timeline for any legal scenario or case under Indian law.")
    situation = st.text_area("Describe your legal situation / procedure needed", placeholder="e.g. Filing a cheque bounce case under Section 138 of NI Act, or registering a private limited company", height=100)
    if st.button("Build Legal Timeline", type="primary", disabled=not situation.strip()):
        with st.spinner("Generating legal process timeline..."):
            try:
                resp = requests.post(
                    f"{API_URL}/legal-timeline",
                    json={"situation": situation.strip()},
                    headers=auth_headers(),
                    timeout=TIMEOUT_LONG
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.markdown(f"### 📍 {data.get('title', 'Legal Process Timeline')}")
                    if data.get("overview"):
                        st.markdown(f"**Overview:** {data.get('overview')}")
                    if data.get("total_estimated_time"):
                        st.info(f"⏱️ **Total Estimated Time:** {data.get('total_estimated_time')}")

                    steps = data.get("steps", [])
                    if steps:
                        st.markdown("### 📋 Procedure Steps")
                        
                        # Render visual Mermaid diagram
                        try:
                            mermaid_nodes = []
                            for idx, s in enumerate(steps):
                                s_title = s.get("title", f"Step {idx+1}").replace('"', '')
                                node_id = chr(65 + (idx % 26)) + (str(idx // 26) if idx >= 26 else "")
                                mermaid_nodes.append((node_id, f"Step {idx+1}: {s_title}"))
                            
                            diagram_lines = ["graph TD"]
                            for i in range(len(mermaid_nodes)):
                                nid, nlabel = mermaid_nodes[i]
                                diagram_lines.append(f'    {nid}["{nlabel}"]')
                                if i < len(mermaid_nodes) - 1:
                                    next_id, _ = mermaid_nodes[i+1]
                                    diagram_lines.append(f'    {nid} --> {next_id}')
                            
                            mermaid_code = "\n".join(diagram_lines)
                            components.html(
                                f"""
                                <script type="module">
                                  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                                  mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
                                </script>
                                <div class="mermaid" style="text-align:center">
                                {mermaid_code}
                                </div>
                                """,
                                height=200,
                            )
                        except Exception:
                            pass

                        for step in steps:
                            st_num = step.get("step", "")
                            st_title = step.get("title", "")
                            st_desc = step.get("description", "")
                            st_dur = step.get("duration", "")
                            st_docs = step.get("documents_needed", [])
                            with st.expander(f"Step {st_num}: {st_title} ({st_dur})", expanded=True):
                                st.write(st_desc)
                                if st_docs:
                                    st.markdown(f"📄 **Documents Needed:** {', '.join(st_docs)}")

                    notes = data.get("important_notes", [])
                    if notes:
                        st.markdown("---")
                        st.markdown("### ⚠️ Important Notes")
                        for note in notes:
                            st.markdown(f"- {note}")
                else:
                    toast("Failed to generate legal timeline.", "❌")
            except Exception:
                toast("Could not reach the server.", "❌")

def show_penalty_calculator():
    st.markdown('<div class="main-header">⚖️ Penalty Calculator</div>', unsafe_allow_html=True)
    st.write("Calculate tax late-filing interest or estimate legal penalties under IPC/BNS sections.")

    tab1, tab2 = st.tabs(["Criminal Penalties (IPC / BNS)", "Tax Interest & Late Fee"])

    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            sec_num = st.text_input("IPC / BNS Section Number", placeholder="e.g. 302, 420, 379")
        with c2:
            circ = st.text_input("Specific Circumstances (Optional)", placeholder="e.g. first-time offence, attempt only")
        if st.button("Calculate / Estimate Penalty", type="primary", disabled=not sec_num.strip()):
            with st.spinner("Estimating penalty..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/penalty-calculator",
                        json={"section": sec_num.strip(), "circumstances": circ.strip()},
                        headers=auth_headers(),
                        timeout=TIMEOUT_MEDIUM
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.markdown(f"### ⚖️ IPC/BNS Section {data.get('section', sec_num)}")
                        if data.get("offence"):
                            st.markdown(f"**Offence:** {data.get('offence')}")

                        b1, b2 = st.columns(2)
                        with b1:
                            bail = "🟢 Bailable" if data.get("is_bailable") else "🔴 Non-Bailable"
                            st.markdown(f"**Bail Status:** {bail}")
                        with b2:
                            cog = "🔴 Cognizable" if data.get("is_cognizable") else "🟢 Non-Cognizable"
                            st.markdown(f"**Cognizable Status:** {cog}")

                        st.markdown(f"**Minimum Punishment:** {data.get('minimum_punishment', 'N/A')}")
                        st.markdown(f"**Maximum Punishment:** {data.get('maximum_punishment', 'N/A')}")
                        if data.get("fine"):
                            st.markdown(f"**Fine:** {data.get('fine')}")
                        if data.get("estimated_sentence"):
                            st.info(f"**Estimated Sentence:** {data.get('estimated_sentence')}")

                        agg = data.get("aggravating_factors", [])
                        if agg:
                            st.markdown(f"**Aggravating Factors:** {', '.join(agg)}")
                        mit = data.get("mitigating_factors", [])
                        if mit:
                            st.markdown(f"**Mitigating Factors:** {', '.join(mit)}")
                        if data.get("disclaimer"):
                            st.caption(f"⚠️ {data.get('disclaimer')}")
                    else:
                        toast("Failed to estimate penalty.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")

    with tab2:
        st.write("Calculate approximate interest and penalties under Income Tax / GST acts.")
        tax_type = st.selectbox("Category", ["Income Tax (Sec 234A/B/C)", "GST Late Filing", "General Late Interest"])
        amount = st.number_input("Tax Due Amount (₹)", min_value=0.0, value=10000.0)
        delay_months = st.number_input("Delay (Months)", min_value=1, value=3)
        if st.button("Calculate Tax Penalty", type="primary"):
            calc = (amount * 0.01) * delay_months
            st.success(f"Estimated Interest Penalty under {tax_type}: ₹{calc:,.2f}")

def show_legal_glossary():
    st.markdown('<div class="main-header">📖 Legal Glossary</div>', unsafe_allow_html=True)
    st.write("Search any legal term or legal maxim in Indian jurisprudence for an AI explanation.")

    term_input = st.text_input("Search Legal Term / Maxim", placeholder="e.g. Quo Warranto, Mens Rea, Suo Motu, Estoppel")
    if st.button("Define Term", type="primary", disabled=not term_input.strip()):
        with st.spinner("Looking up legal term..."):
            try:
                resp = requests.post(
                    f"{API_URL}/glossary",
                    json={"term": term_input.strip()},
                    headers=auth_headers(),
                    timeout=TIMEOUT_MEDIUM
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.markdown(f"### 📖 {data.get('term', term_input)}")
                    if data.get("pronunciation"):
                        st.caption(f"🗣️ Pronunciation: {data.get('pronunciation')}")
                    if data.get("definition"):
                        st.markdown(f"**Plain Definition:** {data.get('definition')}")
                    if data.get("legal_definition"):
                        st.info(f"**Formal Legal Definition:** {data.get('legal_definition')}")
                    if data.get("origin"):
                        st.markdown(f"**Origin:** {data.get('origin')}")
                    if data.get("example"):
                        st.markdown(f"**Example Usage:** {data.get('example')}")
                    if data.get("used_in"):
                        st.markdown(f"**Used in:** {', '.join(data.get('used_in'))}")
                    if data.get("related_terms"):
                        st.markdown(f"**Related Terms:** {', '.join(data.get('related_terms'))}")
                else:
                    toast("Could not define term.", "❌")
            except Exception:
                toast("Could not reach the server.", "❌")

    st.markdown("---")
    st.markdown("### 📚 Popular Legal Maxims & Terms")
    st.markdown("""
    - **Amicus Curiae**: Friend of the court; a neutral legal advisor.
    - **Bail**: Temporary release of an accused person awaiting trial.
    - **Habeas Corpus**: A writ requiring a person under arrest to be brought before a judge or court.
    - **Mens Rea**: The intention or knowledge of wrongdoing that constitutes part of a crime.
    - **Prima Facie**: Based on the first impression; accepted as correct until proven otherwise.
    """)

def show_main_app():
    page = st.session_state.current_page
    dark = st.session_state.dark_mode

    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:1.2rem 0 0.5rem'>"
            "<span style='font-size:2rem'>⚖️</span><br>"
            "<span style='color:#60a5fa;font-size:1.3rem;font-weight:700;letter-spacing:0.5px;font-family:Outfit,sans-serif'>LexAssist</span><br>"
            "<span style='color:#6b7280;font-size:0.75rem'>AI Legal & Tax Assistant</span>"
            "<div style='display:flex;justify-content:center;gap:6px;margin-top:0.6rem;flex-wrap:wrap;'>"
            "<span style='background:rgba(16,185,129,0.15);border:1px solid rgba(52,211,153,0.4);color:#34d399;padding:2px 8px;border-radius:12px;font-size:0.7rem;font-weight:600;'>🟢 FAISS RAG Active</span>"
            "<span style='background:rgba(59,130,246,0.15);border:1px solid rgba(96,165,250,0.4);color:#60a5fa;padding:2px 8px;border-radius:12px;font-size:0.7rem;font-weight:600;'>⚡ Groq LLaMA 3.1</span>"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )
        st.markdown("<hr style='border-color:#1f2d3d;margin:0.8rem 0'>", unsafe_allow_html=True)

        NAV_ITEMS = [
            ("🏠  Home",                   "Home"),
            ("⚖️  Ask Legal Question",      "Ask Legal Question"),
            ("💰  Tax Assistant",           "Tax Assistant"),
            ("💬  General Assistant",       "General Assistant"),
            ("📄  Document Explanation",    "Document Explanation"),
            ("⚠️  Contract Risk Analyzer",  "Contract Risk Analyzer"),
            ("📊  Compare Contracts",       "Compare Contracts"),
            ("🔍  Case Law Search",         "Case Law Search"),
            ("📝  Draft Document",          "Draft Document"),
            ("📌  Section Lookup",          "Section Lookup"),
            ("🗓️  Legal Timeline",         "Legal Timeline"),
            ("⚖️  Penalty Calculator",     "Penalty Calculator"),
            ("📖  Legal Glossary",          "Legal Glossary"),
            ("⭐  Bookmarks",               "Bookmarks"),
            ("📜  Query History",           "Query History"),
            ("📈  My Stats",                "My Stats"),
            ("📊  Admin Analytics",          "Admin Analytics"),
            ("👤  Profile",                 "Profile"),
            ("ℹ️  About",                   "About"),
        ]
        for label, target in NAV_ITEMS:
            if st.button(label, key=f"nav_{target}", use_container_width=True,
                         type="primary" if page == target else "secondary"):
                st.session_state.current_page = target
                st.rerun()

        st.markdown("<hr style='border-color:#1f2d3d;margin:0.8rem 0'>", unsafe_allow_html=True)

        username = st.session_state.get("username", "")
        if username:
            st.markdown(
                f"<div style='color:#6b7280;font-size:0.78rem;padding:0 4px 6px'>👤 {username}</div>",
                unsafe_allow_html=True
            )

        if st.button("🌞  Light mode" if dark else "🌙  Dark mode", key="nav_theme", use_container_width=True):
            st.session_state.dark_mode = not dark
            st.rerun()

        st.markdown('<div class="la-logout">', unsafe_allow_html=True)
        if st.button("🚪  Logout", key="nav_logout", use_container_width=True):
            try:
                requests.post(f"{API_URL}/logout", headers=auth_headers(), timeout=TIMEOUT_SHORT)
            except Exception:
                pass
            for k in ["logged_in", "user_id", "username", "token", "query_history",
                      "legal_messages", "tax_messages", "general_messages"]:
                if k == "logged_in":
                    st.session_state[k] = False
                elif k in ("query_history", "legal_messages", "tax_messages", "general_messages"):
                    st.session_state[k] = []
                else:
                    st.session_state[k] = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # Dispatch views directly via page state
    if page == "Home":
        show_home_page()
    elif page == "Ask Legal Question":
        show_chat_page("legal", "Ask Legal Question")
    elif page == "Tax Assistant":
        show_chat_page("tax", "Tax Assistant")
    elif page == "General Assistant":
        show_chat_page("general", "General Assistant")
    elif page == "Document Explanation":
        st.markdown('<div class="main-header">Document Explanation</div>', unsafe_allow_html=True)
        st.write("Upload a legal or tax document (PDF, TXT, or DOCX) and get a simplified explanation.")
        uploaded_file = st.file_uploader("Choose a document", type=["pdf", "txt", "docx"])
        if uploaded_file:
            st.info(f"File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
            if st.button("Explain Document", type="primary"):
                with st.spinner("Analyzing document..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(f"{API_URL}/explain-document", files=files, headers=auth_headers(), timeout=TIMEOUT_LONG)
                        if response.status_code == 200:
                            data = response.json()
                            c1, c2, c3, c4 = st.columns(4)
                            with c1:
                                st.metric("Filename", data["filename"])
                            with c2:
                                st.metric("Characters", f"{data['text_length']:,}")
                            with c3:
                                st.metric("Word Count", f"{data.get('word_count', 0):,}")
                            with c4:
                                st.metric("Reading Time", f"{data.get('reading_time_minutes', 1)} min")
                            with st.expander("Extracted Text (Preview)"):
                                st.text(data["extracted_text"])
                            st.markdown(f'<div class="response-box"><h3>AI Explanation</h3>{data["explanation"]}</div>', unsafe_allow_html=True)
                            toast("Document explained successfully!", "✅")
                        else:
                            toast("Could not process the document. Please try again.", "❌")
                    except Exception:
                        toast("Could not reach the server. Please try again shortly.", "❌")
    elif page == "Contract Risk Analyzer":
        show_contract_risk_analyzer()
    elif page == "Compare Contracts":
        show_compare_contracts()
    elif page == "Case Law Search":
        show_case_law_search()
    elif page == "Draft Document":
        show_draft_document()
    elif page == "Section Lookup":
        show_section_lookup()
    elif page == "Legal Timeline":
        show_legal_timeline()
    elif page == "Penalty Calculator":
        show_penalty_calculator()
    elif page == "Legal Glossary":
        show_legal_glossary()
    elif page == "Admin Analytics":
        show_admin_analytics()
    elif page == "Query History":
        st.markdown('<div class="main-header">Query History</div>', unsafe_allow_html=True)
        try:
            col_search, col_filter = st.columns([3, 1])
            with col_search:
                search_input = st.text_input(
                    "🔍 Search queries",
                    value=st.session_state.history_search,
                    placeholder="Type a keyword to search...",
                    key="history_search_input"
                )
            with col_filter:
                filter_category = st.selectbox(
                    "Filter by category:",
                    ["All", "legal", "tax", "general", "document"],
                    index=["All", "legal", "tax", "general", "document"].index(st.session_state.history_filter)
                )

            if search_input != st.session_state.history_search or filter_category != st.session_state.history_filter:
                st.session_state.history_page = 0
                st.session_state.history_search = search_input
                st.session_state.history_filter = filter_category
                st.rerun()

            offset = st.session_state.history_page * PAGE_SIZE
            params = {"limit": PAGE_SIZE, "offset": offset}
            if st.session_state.history_search:
                params["search"] = st.session_state.history_search
            if st.session_state.history_filter and st.session_state.history_filter != "All":
                params["category"] = st.session_state.history_filter

            resp = requests.get(
                f"{API_URL}/history",
                params=params,
                headers=auth_headers(), timeout=TIMEOUT_SHORT
            )
            if resp.status_code == 200:
                data = resp.json()
                history = data["history"]
                total = data["total"]
                total_pages = max(1, -(-total // PAGE_SIZE))

                col_info, col_export = st.columns([3, 1])
                with col_info:
                    label = f"Found {total} quer{'y' if total == 1 else 'ies'}"
                    if st.session_state.history_search:
                        label += f" matching \"{st.session_state.history_search}\""
                    st.info(f"{label} | Page {st.session_state.history_page + 1} of {total_pages}")
                with col_export:
                    export_resp = requests.get(f"{API_URL}/history/export", headers=auth_headers(), timeout=TIMEOUT_MEDIUM)
                    if export_resp.status_code == 200:
                        st.download_button(
                            label="⬇ Download CSV",
                            data=export_resp.content,
                            file_name="lexassist_history.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                if history:
                    bk_resp = requests.get(f"{API_URL}/bookmarks", headers=auth_headers(), timeout=TIMEOUT_SHORT)
                    bookmarked_ids = {b["id"] for b in bk_resp.json().get("bookmarks", [])} if bk_resp.status_code == 200 else set()

                    for item in history:
                        if filter_category != "All" and item["category"] != filter_category:
                            continue
                        is_bookmarked = item["id"] in bookmarked_ids
                        star = "⭐" if is_bookmarked else "☆"
                        with st.expander(f"{item['timestamp']} - {item['category'].upper()}"):
                            col_q, col_bk, col_del = st.columns([5, 1, 1])
                            with col_q:
                                st.markdown(f"**Query:** {item['query']}")
                            with col_bk:
                                if st.button(f"{star} Bookmark", key=f"bk_{item['id']}"):
                                    toggle_resp = requests.post(
                                        f"{API_URL}/bookmarks/toggle",
                                        json={"query_id": item["id"]},
                                        headers=auth_headers(), timeout=TIMEOUT_SHORT
                                    )
                                    if toggle_resp.status_code == 200:
                                        action = "Bookmarked" if toggle_resp.json().get("bookmarked") else "Removed bookmark"
                                        toast(f"{action}!", "⭐")
                                        st.rerun()
                            with col_del:
                                if st.button("🗑️ Delete", key=f"del_{item['id']}"):
                                    del_resp = requests.delete(
                                        f"{API_URL}/history/{item['id']}",
                                        headers=auth_headers(), timeout=TIMEOUT_SHORT
                                    )
                                    if del_resp.status_code == 200:
                                        toast("Entry deleted.", "🗑️")
                                        st.rerun()
                            st.markdown("---")
                            st.write(item["response"])

                    st.markdown("---")
                    prev_col, page_col, next_col, top_col = st.columns([1, 2, 1, 1])
                    with prev_col:
                        if st.session_state.history_page > 0:
                            if st.button("← Previous", use_container_width=True):
                                st.session_state.history_page -= 1
                                st.rerun()
                    with page_col:
                        st.markdown(f"<div style='text-align:center;padding-top:0.5rem'>Page {st.session_state.history_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
                    with next_col:
                        if st.session_state.history_page + 1 < total_pages:
                            if st.button("Next →", use_container_width=True):
                                st.session_state.history_page += 1
                                st.rerun()
                    with top_col:
                        st.markdown("<a href='#top' style='display:block;text-align:center;padding-top:0.4rem;text-decoration:none;font-size:0.9rem'>⬆️ Top</a>", unsafe_allow_html=True)
                else:
                    if st.session_state.history_search:
                        st.info(f"No queries found matching \"{st.session_state.history_search}\".")
                    else:
                        st.info("No queries yet. Start asking questions!")
            else:
                toast("Failed to load history.", "❌")
        except Exception:
            toast("Could not reach the server. Please try again shortly.", "❌")
    elif page == "Bookmarks":
        st.markdown('<div class="main-header">Bookmarks</div>', unsafe_allow_html=True)
        try:
            resp = requests.get(f"{API_URL}/bookmarks", headers=auth_headers(), timeout=TIMEOUT_SHORT)
            if resp.status_code == 200:
                data = resp.json()
                bookmarks = data["bookmarks"]
                if bookmarks:
                    st.info(f"You have {data['count']} bookmarked queries.")
                    for item in bookmarks:
                        note = item.get("bookmark_note", "") or ""
                        label = f"⭐ {item['timestamp']} - {item['category'].upper()}"
                        if note:
                            label += f" — {note[:40]}"
                        with st.expander(label):
                            col_q, col_rm = st.columns([5, 1])
                            with col_q:
                                st.markdown(f"**Query:** {item['query']}")
                            with col_rm:
                                if st.button("Remove", key=f"rm_bk_{item['id']}"):
                                    toggle_resp = requests.post(
                                        f"{API_URL}/bookmarks/toggle",
                                        json={"query_id": item["id"]},
                                        headers=auth_headers(), timeout=TIMEOUT_SHORT
                                    )
                                    if toggle_resp.status_code == 200:
                                        toast("Bookmark removed.", "🗑️")
                                        st.rerun()
                            new_note = st.text_input(
                                "📝 Note", value=note,
                                placeholder="Add a label or note for this bookmark...",
                                key=f"note_input_{item['id']}"
                            )
                            if st.button("Save Note", key=f"save_note_{item['id']}"):
                                nr = requests.patch(
                                    f"{API_URL}/bookmarks/{item['id']}/note",
                                    json={"note": new_note},
                                    headers=auth_headers(), timeout=TIMEOUT_SHORT
                                )
                                if nr.status_code == 200:
                                    toast("Note saved!", "✅")
                                    st.rerun()
                            st.markdown("---")
                            st.write(item["response"])
                else:
                    st.info("No bookmarks yet. Star queries in Query History to save them here.")
            else:
                toast("Failed to load bookmarks.", "❌")
        except Exception:
            toast("Could not reach the server. Please try again shortly.", "❌")
    elif page == "My Stats":
        st.markdown('<div class="main-header">📈 My Stats</div>', unsafe_allow_html=True)
        try:
            resp = requests.get(f"{API_URL}/stats", headers=auth_headers(), timeout=TIMEOUT_SHORT)
            if resp.status_code == 200:
                s = resp.json()
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Total Queries", s.get("total_queries", 0))
                with c2:
                    st.metric("Bookmarks", s.get("bookmarks_count", 0))
                with c3:
                    most = s.get("most_active_day", "—") or "—"
                    st.metric("Most Active Day", most)

                st.markdown("---")
                by_cat = s.get("by_category", {})
                if by_cat:
                    st.markdown("### Queries by Category")
                    cat_cols = st.columns(len(by_cat))
                    for col, (cat, count) in zip(cat_cols, by_cat.items()):
                        with col:
                            st.metric(cat.capitalize(), count)

                by_day = s.get("by_day", {})
                if by_day:
                    st.markdown("---")
                    st.markdown("### Activity — Last 30 Days")
                    df = pd.DataFrame(list(by_day.items()), columns=["Date", "Queries"])
                    df["Date"] = pd.to_datetime(df["Date"])
                    df = df.sort_values("Date")
                    st.bar_chart(df.set_index("Date")["Queries"])
            else:
                toast("Failed to load stats.", "❌")
        except Exception:
            toast("Could not reach the server.", "❌")
    elif page == "Profile":
        st.markdown('<div class="main-header">👤 Profile</div>', unsafe_allow_html=True)
        st.markdown(f"**Username:** {st.session_state.get('username', '')}")
        st.markdown("---")
        st.markdown("### Change Password")
        with st.form("change_password_form"):
            old_pw = st.text_input("Current password", type="password")
            new_pw = st.text_input("New password", type="password")
            confirm_pw = st.text_input("Confirm new password", type="password")
            submitted = st.form_submit_button("Update Password", type="primary")
        if submitted:
            if not old_pw or not new_pw or not confirm_pw:
                toast("Please fill in all fields.", "⚠️")
            elif len(new_pw) < 6:
                toast("New password must be at least 6 characters.", "⚠️")
            elif new_pw != confirm_pw:
                toast("New passwords do not match.", "⚠️")
            else:
                try:
                    resp = requests.post(
                        f"{API_URL}/change-password",
                        json={"old_password": old_pw, "new_password": new_pw},
                        headers=auth_headers(), timeout=TIMEOUT_SHORT
                    )
                    if resp.status_code == 200:
                        toast("Password updated successfully!", "✅")
                    else:
                        toast("Current password is incorrect.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")
    elif page == "Admin Analytics":
        st.markdown('<div class="main-header">📊 Admin Analytics Dashboard</div>', unsafe_allow_html=True)
        st.write("System performance analytics, query category distributions, and real-time user feedback logs.")
        try:
            resp = requests.get(f"{API_URL}/admin/analytics", headers=auth_headers(), timeout=TIMEOUT_SHORT)
            if resp.status_code == 200:
                data = resp.json()
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Total Users", data.get("total_users", 0))
                with c2:
                    st.metric("Total Queries", data.get("total_queries", 0))
                with c3:
                    st.metric("Positive Ratings 👍", data.get("positive_feedback", 0))
                with c4:
                    st.metric("Negative Ratings 👎", data.get("negative_feedback", 0))
                
                st.markdown("---")
                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown("### 🏷️ Queries by Category")
                    by_cat = data.get("by_category", {})
                    if by_cat:
                        df_cat = pd.DataFrame(list(by_cat.items()), columns=["Category", "Count"])
                        st.bar_chart(df_cat.set_index("Category"))
                with c_right:
                    st.markdown("### 📈 Daily Activity (14 Days)")
                    daily = data.get("daily_activity", {})
                    if daily:
                        df_daily = pd.DataFrame(list(daily.items()), columns=["Date", "Queries"])
                        df_daily["Date"] = pd.to_datetime(df_daily["Date"])
                        st.line_chart(df_daily.sort_values("Date").set_index("Date"))
                
                st.markdown("---")
                st.markdown("### 💬 Recent User Feedback")
                recent = data.get("recent_feedback", [])
                if recent:
                    for f in recent:
                        icon = "👍" if f.get("rating", 0) > 0 else "👎"
                        st.markdown(f"**{icon} User `{f.get('username')}`**: *\"{f.get('query', '')[:100]}\"*")
                        if f.get("comment"):
                            st.caption(f"Note: {f['comment']}")
                else:
                    st.info("No feedback submitted yet.")
            else:
                toast("Failed to load admin analytics.", "❌")
        except Exception:
            toast("Could not reach the server.", "❌")

    elif page == "About":
        st.markdown('<div class="main-header">About LexAssist</div>', unsafe_allow_html=True)
        st.markdown("""
        ### What is LexAssist?
        LexAssist is an AI-powered legal and tax assistant for Indian law, built with RAG to ground answers in real legal documents.

        ### Knowledge Base
        - Indian Penal Code (IPC)
        - Constitution of India
        - CRPC (Code of Criminal Procedure)
        - Income Tax Bill 2025
        - IndicLegalQA Dataset (10K Q&A pairs)
        - Legal Contract Clauses

        ### Technology Stack
        - Frontend: Streamlit
        - Backend: FastAPI
        - AI: Groq (llama-3.1-8b-instant)
        - RAG: FAISS + fastembed
        - Database: SQLite

        ### Disclaimer
        LexAssist is an informational tool only. Always consult a qualified attorney or tax professional.
        """)
    else:
        show_home_page()

if not st.session_state.logged_in:
    if st.session_state.auth_alert:
        kind, msg = st.session_state.auth_alert
        st.session_state.auth_alert = None
        toast(msg, "✅" if kind == "success" else "⚠️" if kind == "warning" else "❌")
    show_login_page()
else:
    show_main_app()