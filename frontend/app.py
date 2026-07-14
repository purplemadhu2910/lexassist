import os
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
        sb_user   = "#6b7280"
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
        sb_user   = "#64748b"
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
    /* ── Hide Streamlit chrome ── */
    header[data-testid="stHeader"]   {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}

    /* ── Main background & text ── */
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

    /* ── Sidebar ── */
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

    /* ── Inputs / textareas / selects ── */
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

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {{
        background-color: {file_bg} !important;
        border-color: {border} !important;
        color: {text} !important;
    }}
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p {{
        color: {text} !important;
    }}

    /* ── Chat messages ── */
    [data-testid="stChatMessage"] {{
        background-color: {chat_bg} !important;
        color: {chat_text} !important;
    }}
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] div {{
        color: {chat_text} !important;
    }}

    /* ── Markdown / general text ── */
    p, span, li, td, th, label, div {{
        color: {text};
    }}
    h1, h2, h3, h4, h5, h6 {{ color: {text} !important; }}
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span {{
        color: {text} !important;
    }}

    /* ── Expanders ── */
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

    /* ── Buttons (main content) ── */
    .block-container .stButton > button {{
        background-color: {btn_bg} !important;
        color: {btn_text} !important;
        border-color: {btn_bdr} !important;
    }}
    .block-container .stButton > button[kind="primary"] {{
        background-color: #1f77b4 !important;
        color: #ffffff !important;
        border-color: #1f77b4 !important;
    }}

    /* ── Tabs ── */
    [data-testid="stTabs"] [role="tab"] {{ color: {tab_color} !important; }}
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
        color: {accent} !important;
        border-bottom-color: {accent} !important;
    }}
    [data-testid="stTabs"] {{ background-color: {bg} !important; }}

    /* ── Metrics ── */
    [data-testid="stMetric"] {{ background-color: {bg2} !important; }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{ color: {text} !important; }}

    /* ── Alerts / info boxes ── */
    [data-testid="stAlert"] {{
        background-color: {alert_bg} !important;
        color: {text} !important;
    }}
    [data-testid="stAlert"] p {{ color: {text} !important; }}

    /* ── Selectbox dropdown ── */
    [data-baseweb="popover"] ul,
    [data-baseweb="menu"] {{
        background-color: {bg2} !important;
        color: {text} !important;
    }}
    [data-baseweb="menu"] li {{ color: {text} !important; }}
    [data-baseweb="menu"] li:hover {{ background-color: {bg3} !important; }}

    /* ── Progress bar ── */
    [data-testid="stProgress"] > div {{ background-color: {border} !important; }}
    [data-testid="stProgress"] > div > div {{ background-color: {accent} !important; }}

    /* ── Table ── */
    table {{ background-color: {bg2} !important; color: {text} !important; }}
    th {{ background-color: {bg3} !important; color: {text} !important; }}
    td {{ color: {text} !important; border-color: {border} !important; }}

    /* ── Scrollbar ── */
    ::-webkit-scrollbar {{ background: {scrl_bg}; }}
    ::-webkit-scrollbar-thumb {{ background: {scrl_thm}; border-radius: 4px; }}

    /* ── Custom classes ── */
    .main-header {{ font-size: 2.5rem; font-weight: bold; color: {hdr_color}; text-align: center; margin-bottom: 1rem; }}
    .sub-header {{ font-size: 1.2rem; color: {text2}; text-align: center; margin-bottom: 2rem; }}
    .disclaimer-box {{
        background-color: {disc_bg} !important;
        border-left: 5px solid #ffc107;
        padding: 1rem; margin: 1rem 0; border-radius: 5px;
        color: {disc_text} !important;
    }}
    .disclaimer-box strong {{ color: {disc_text} !important; }}
    .rag-badge {{
        background-color: {rag_bg}; border: 1px solid {rag_bdr};
        padding: 0.3rem 0.8rem; border-radius: 20px;
        color: {rag_text}; font-size: 0.85rem; display: inline-block; margin-bottom: 1rem;
    }}
    .auth-divider {{ text-align: center; color: {text2}; margin: 1rem 0; font-size: 0.85rem; }}
    .response-box {{
        background-color: {resp_bg} !important; color: {resp_text} !important;
        padding: 1.5rem; border-radius: 12px; border: 1px solid {resp_bdr};
        margin: 1rem 0; box-shadow: {resp_shad};
    }}
    .response-box h3 {{ color: {accent} !important; }}
    .char-counter {{ font-size: 0.78rem; color: #888; text-align: right; margin-top: -0.5rem; margin-bottom: 0.5rem; }}
    .char-counter.warn {{ color: {warn_clr}; }}
    .char-counter.over  {{ color: {over_clr}; }}
</style>
"""

st.markdown(_build_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)

# Back-to-top anchor
st.markdown('<a name="top"></a>', unsafe_allow_html=True)


def _char_counter_html(text: str) -> str:
    n = len(text)
    cls = "over" if n > MAX_QUERY_CHARS else "warn" if n > int(MAX_QUERY_CHARS * 0.85) else ""
    return f'<div class="char-counter {cls}">{n} / {MAX_QUERY_CHARS}</div>'

def _copy_button(text: str, key: str):
    """Renders a copy-to-clipboard button. Passes text via a hidden textarea to avoid JS escaping issues."""
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
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown('<div style="text-align:center;font-size:3rem">⚖</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-size:1.8rem;font-weight:700;color:#1f77b4">LexAssist</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#888;margin-bottom:1.5rem">Your personal legal and tax assistant for Indian law</div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Sign In", "Create Account"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Sign In", type="primary", use_container_width=True)

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
                submit_reg = st.form_submit_button("Create Account", type="primary", use_container_width=True)

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
                                    # Auto sign-in after registration
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

        st.markdown('<div class="auth-divider">Trusted by law students, professionals, and everyday citizens</div>', unsafe_allow_html=True)

    st.markdown("---")
    _, c1, c2, c3, _ = st.columns([1, 1, 1, 1, 1])
    with c1:
        st.markdown("**Legal Questions**\n\nAsk anything about IPC, Constitution, or CRPC in plain language.")
    with c2:
        st.markdown("**Tax Guidance**\n\nUnderstand Income Tax, GST, and deductions without the jargon.")
    with c3:
        st.markdown("**Document Analysis**\n\nUpload any legal document and get a simple explanation.")


def ask_api(query, category):
    return requests.post(
        f"{API_URL}/ask",
        json={"query": query, "category": category},
        headers=auth_headers(),
        timeout=TIMEOUT_LONG
    )


def show_chat_page(category: str, page_title: str):
    messages_key = f"{category}_messages"
    prefill_key = f"{category}_prefill"
    draft_key = f"{category}_draft"

    st.markdown(f'<div class="main-header">{page_title}</div>', unsafe_allow_html=True)

    # ── Top controls: language selector + voice input ──
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

    # ── Voice input ──
    components.html(
        f"""
        <div style="margin:6px 0">
          <button id="voiceBtn_{category}" onclick="startVoice_{category}()"
            style="background:#1e2a3a;color:#9ca3af;border:1px solid #2e4a6a;padding:6px 14px;
                   border-radius:8px;cursor:pointer;font-size:0.82rem">
            🎤 Voice Input
          </button>
          <span id="voiceStatus_{category}" style="color:#6b7280;font-size:0.78rem;margin-left:8px"></span>
          <input id="voiceResult_{category}" type="text" readonly
            style="display:none;width:100%;margin-top:6px;padding:6px;background:#1e2a3a;
                   color:#e5e7eb;border:1px solid #2e4a6a;border-radius:6px;font-size:0.85rem">
        </div>
        <script>
        function startVoice_{category}() {{
          if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
            document.getElementById('voiceStatus_{category}').innerText = 'Not supported in this browser.';
            return;
          }}
          var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          var rec = new SR();
          rec.lang = 'en-IN';
          rec.interimResults = false;
          document.getElementById('voiceStatus_{category}').innerText = '🔴 Listening...';
          document.getElementById('voiceBtn_{category}').disabled = true;
          rec.onresult = function(e) {{
            var transcript = e.results[0][0].transcript;
            var box = document.getElementById('voiceResult_{category}');
            box.style.display = 'block';
            box.value = transcript;
            document.getElementById('voiceStatus_{category}').innerText = '✅ Captured! Copy the text below into the chat.';
            document.getElementById('voiceBtn_{category}').disabled = false;
          }};
          rec.onerror = function(e) {{
            document.getElementById('voiceStatus_{category}').innerText = 'Error: ' + e.error;
            document.getElementById('voiceBtn_{category}').disabled = false;
          }};
          rec.onend = function() {{
            if (document.getElementById('voiceStatus_{category}').innerText === '🔴 Listening...')
              document.getElementById('voiceStatus_{category}').innerText = 'No speech detected.';
            document.getElementById('voiceBtn_{category}').disabled = false;
          }};
          rec.start();
        }}
        </script>
        """,
        height=90,
    )

    # Render existing conversation
    for idx, msg in enumerate(st.session_state[messages_key]):
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant":
                # Copy-to-clipboard button
                _copy_button(msg["content"], key=f"{category}_copy_{idx}")
                # Print / PDF export
                components.html(
                    f"""
                    <button onclick="
                        var w=window.open('','_blank');
                        w.document.write('<html><head><title>LexAssist Response</title>'
                            +'<style>body{{font-family:Arial,sans-serif;padding:2rem;max-width:800px;margin:auto}}'
                            +'h3{{color:#1f77b4}}pre{{white-space:pre-wrap;word-wrap:break-word}}</style></head>'
                            +'<body><h3>LexAssist Response</h3><pre>'+{repr(msg['content'])}+'</pre></body></html>');
                        w.document.close();w.print();"
                        style="background:#374151;color:#d1d5db;border:none;padding:4px 12px;
                               border-radius:6px;cursor:pointer;font-size:0.8rem;margin-top:4px;margin-left:6px">
                        🖨️ Print / PDF
                    </button>
                    """,
                    height=44,
                )
                # RAG sources
                if msg.get("sources"):
                    with st.expander(f"📚 Sources ({len(msg['sources'])} chunks used)", expanded=False):
                        for si, src in enumerate(msg["sources"], 1):
                            st.markdown(f"**{si}.** {src}")
                # Suggested follow-ups
                if msg.get("suggestions"):
                    st.markdown("**Suggested follow-up questions:**")
                    for i, s in enumerate(msg["suggestions"]):
                        if st.button(s, key=f"{category}_sugg_{idx}_{i}", use_container_width=True):
                            st.session_state[prefill_key] = s
                            st.rerun()

    def _do_ask(query: str):
        st.session_state[messages_key].append({"role": "user", "content": query})
        with st.spinner("Generating answer..."):
            try:
                # Build history excluding the just-appended user message
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

    # Handle prefill from suggestion click
    prefill_query = st.session_state.get(prefill_key, "")
    if prefill_query:
        st.session_state[prefill_key] = ""
        _do_ask(prefill_query)
        st.rerun()

    # Character counter — shows length of last submitted input
    last_draft = st.session_state.get(draft_key, "")
    if last_draft:
        st.markdown(_char_counter_html(last_draft), unsafe_allow_html=True)

    # Chat input
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



def show_main_app():
    page = st.session_state.current_page
    dark = st.session_state.dark_mode

    # ── Left Sidebar Navigation ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<div style='text-align:center;padding:1.2rem 0 0.5rem'>"
            "<span style='font-size:2rem'>⚖️</span><br>"
            "<span style='color:#60a5fa;font-size:1.3rem;font-weight:700;letter-spacing:0.5px'>LexAssist</span><br>"
            "<span style='color:#6b7280;font-size:0.75rem'>AI Legal & Tax Assistant</span>"
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
            ("⭐  Bookmarks",               "Bookmarks"),
            ("📜  Query History",           "Query History"),
            ("📈  My Stats",                "My Stats"),
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

    if page == "Home":
        st.markdown('<div class="main-header">Welcome to LexAssist</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Your AI-Powered Legal and Tax Assistant for Indian Law</div>', unsafe_allow_html=True)
        st.markdown('<div class="rag-badge">RAG-Enhanced: Answers grounded in real Indian legal documents</div>', unsafe_allow_html=True)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown("### Legal Assistance")
            st.write("Get simplified explanations of IPC sections, Constitutional articles, and your rights under Indian law.")
        with col2:
            st.markdown("### Tax Guidance")
            st.write("Understand Income Tax Act sections, GST, deductions, and filing requirements.")
        with col3:
            st.markdown("### General Assistant")
            st.write("Ask any general legal or civic question about Indian law and governance.")
        with col4:
            st.markdown("### Document Analysis")
            st.write("Upload PDF, TXT, or DOCX legal documents and get easy-to-understand explanations.")
        with col5:
            st.markdown("### ⚠️ Contract Risks")
            st.write("Upload any contract to detect risks, missing clauses, and get actionable recommendations.")
        st.markdown("---")
        st.markdown('<div class="disclaimer-box"><strong>Disclaimer:</strong> LexAssist provides general information only and is not a substitute for professional legal or tax advice.</div>', unsafe_allow_html=True)

    elif page == "Ask Legal Question":
        show_chat_page("legal", "Ask Legal Question")

    elif page == "Tax Assistant":
        show_chat_page("tax", "Tax Assistant")

    elif page == "General Assistant":
        show_chat_page("general", "General Assistant")

    elif page == "Contract Risk Analyzer":
        st.markdown('<div class="main-header">⚠️ Contract Risk Analyzer</div>', unsafe_allow_html=True)
        st.write("Upload a contract (PDF, TXT, or DOCX) to identify risks, missing clauses, and get recommendations under Indian contract law.")
        uploaded_file = st.file_uploader("Choose a contract document", type=["pdf", "txt", "docx"], key="contract_upload")
        if uploaded_file:
            st.info(f"File: {uploaded_file.name} ({uploaded_file.size} bytes)")
            if st.button("Analyze Contract Risks", type="primary"):
                with st.spinner("Analyzing contract for risks..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(f"{API_URL}/analyze-contract", files=files, headers=auth_headers(), timeout=TIMEOUT_LONG)
                        if response.status_code == 200:
                            data = response.json()["analysis"]

                            # Risk Score
                            score = data.get("risk_score", 0)
                            color = "🟢" if score <= 3 else "🟡" if score <= 6 else "🔴"
                            st.markdown(f"### {color} Overall Risk Score: **{score}/10**")
                            st.progress(score / 10)

                            st.markdown(f"**Summary:** {data.get('summary', 'N/A')}")

                            # Identified Risks
                            risks = data.get("risks", [])
                            if risks:
                                st.markdown("---\n### 🚨 Identified Risks")
                                for r in risks:
                                    sev = r.get("severity", "Medium")
                                    badge = "🔴" if sev == "High" else "🟡" if sev == "Medium" else "🟢"
                                    with st.expander(f"{badge} {sev} — {r.get('clause', 'Clause')}"):
                                        st.write(r.get("risk", ""))

                            # Missing Clauses
                            missing = data.get("missing_clauses", [])
                            if missing:
                                st.markdown("---\n### 📋 Missing Clauses")
                                for m in missing:
                                    st.markdown(f"- {m}")

                            # Recommendations
                            recs = data.get("recommendations", [])
                            if recs:
                                st.markdown("---\n### ✅ Recommendations")
                                for rec in recs:
                                    st.markdown(f"- {rec}")

                            st.markdown('<div class="disclaimer-box"><strong>Disclaimer:</strong> This analysis is AI-generated and not a substitute for professional legal advice.</div>', unsafe_allow_html=True)
                            toast("Contract analysis complete!", "✅")
                        else:
                            toast("Could not analyze the contract. Please try again.", "❌")
                    except Exception:
                        toast("Could not reach the server. Please try again shortly.", "❌")

    elif page == "Compare Contracts":
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

    elif page == "Query History":
        st.markdown('<div class="main-header">Query History</div>', unsafe_allow_html=True)
        try:
            # ── Search + filter controls ──────────────────────────────────
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

            # Reset page when search or filter changes
            if search_input != st.session_state.history_search or filter_category != st.session_state.history_filter:
                st.session_state.history_page = 0
                st.session_state.history_search = search_input
                st.session_state.history_filter = filter_category
                st.rerun()

            offset = st.session_state.history_page * PAGE_SIZE
            params = {"limit": PAGE_SIZE, "offset": offset}
            if st.session_state.history_search:
                params["search"] = st.session_state.history_search

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
                    # Fetch bookmarked IDs for this user
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

                    # Pagination controls
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
                            # Note editor
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
                    import pandas as pd
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


if not st.session_state.logged_in:
    if st.session_state.auth_alert:
        kind, msg = st.session_state.auth_alert
        st.session_state.auth_alert = None
        toast(msg, "✅" if kind == "success" else "⚠️" if kind == "warning" else "❌")
    show_login_page()
else:
    show_main_app()
