import os
import io
import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="LexAssist - AI Legal & Tax Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

PAGE_SIZE = 10

for key, default in {
    "query_history": [], "logged_in": False, "user_id": None,
    "username": None, "token": None,
    "legal_messages": [], "tax_messages": [], "general_messages": [],
    "legal_prefill": "", "tax_prefill": "", "general_prefill": "",
    "history_page": 0, "history_filter": "All",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def auth_headers():
    return {"X-Auth-Token": st.session_state.token} if st.session_state.token else {}

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 1rem; }
    .sub-header { font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem; }
    .disclaimer-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 1rem; margin: 1rem 0; border-radius: 5px; color: #000000; }
    .rag-badge { background-color: #d4edda; border: 1px solid #28a745; padding: 0.3rem 0.8rem; border-radius: 20px; color: #155724; font-size: 0.85rem; display: inline-block; margin-bottom: 1rem; }
    .auth-divider { text-align: center; color: #aaa; margin: 1rem 0; font-size: 0.85rem; }
    .response-box { background-color: #1e2a3a; color: #e8f4ff; padding: 1.5rem; border-radius: 12px; border: 1px solid #2e4a6a; margin: 1rem 0; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
</style>
""", unsafe_allow_html=True)


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
                                timeout=10
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.logged_in = True
                                st.session_state.user_id = data["user_id"]
                                st.session_state.username = data["username"]
                                st.session_state.token = data["token"]
                                st.success(f"Welcome back, {data['username']}!")
                                st.rerun()
                            elif response.status_code == 429:
                                st.error("Too many login attempts. Please wait a minute and try again.")
                            else:
                                st.error("That username or password doesn't look right. Please try again.")
                        except requests.exceptions.ConnectionError:
                            st.error("Could not reach the server. Please try again shortly.")
                else:
                    st.warning("Please fill in both your username and password.")

        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Choose a username", placeholder="Pick something you'll remember")
                new_password = st.text_input("Choose a password", type="password", placeholder="At least 6 characters")
                confirm_password = st.text_input("Confirm your password", type="password", placeholder="Type it again")
                submit_reg = st.form_submit_button("Create Account", type="primary", use_container_width=True)

            if submit_reg:
                if new_username.strip() and new_password.strip() and confirm_password.strip():
                    if len(new_password) < 6:
                        st.error("Password should be at least 6 characters long.")
                    elif new_password != confirm_password:
                        st.error("The passwords you entered don't match. Please try again.")
                    else:
                        with st.spinner("Creating your account..."):
                            try:
                                response = requests.post(
                                    f"{API_URL}/register",
                                    json={"username": new_username.strip(), "password": new_password},
                                    timeout=10
                                )
                                if response.status_code == 200:
                                    st.success("Account created! Head over to Sign In to get started.")
                                else:
                                    st.error("That username is already taken. Try a different one.")
                            except requests.exceptions.ConnectionError:
                                st.error("Could not reach the server. Please try again shortly.")
                else:
                    st.warning("Please fill in all three fields to create your account.")

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
        timeout=30
    )


def show_chat_page(category: str, page_title: str):
    messages_key = f"{category}_messages"
    prefill_key = f"{category}_prefill"

    st.markdown(f'<div class="main-header">{page_title}</div>', unsafe_allow_html=True)
    st.markdown('<div class="rag-badge">RAG-Enhanced answers from Indian legal documents</div>', unsafe_allow_html=True)

    # Render existing conversation
    for msg in st.session_state[messages_key]:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("suggestions"):
                st.markdown("**Suggested follow-up questions:**")
                for i, s in enumerate(msg["suggestions"]):
                    if st.button(s, key=f"{category}_sugg_{len(st.session_state[messages_key])}_{i}", use_container_width=True):
                        st.session_state[prefill_key] = s
                        st.rerun()

    # Handle prefill from suggestion click
    prefill_query = st.session_state.get(prefill_key, "")
    if prefill_query:
        st.session_state[prefill_key] = ""
        st.session_state[messages_key].append({"role": "user", "content": prefill_query})
        with st.spinner("Generating answer..."):
            try:
                resp = ask_api(prefill_query, category)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state[messages_key].append({
                        "role": "assistant",
                        "content": data["response"],
                        "suggestions": data.get("suggested_questions", [])
                    })
                    st.session_state.query_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": prefill_query, "category": category
                    })
                else:
                    st.session_state[messages_key].append({"role": "assistant", "content": "Something went wrong. Please try again."})
            except Exception:
                st.session_state[messages_key].append({"role": "assistant", "content": "Could not reach the server. Please try again shortly."})
        st.rerun()

    # Chat input
    user_input = st.chat_input(f"Ask a {category} question...")
    if user_input and user_input.strip():
        st.session_state[messages_key].append({"role": "user", "content": user_input.strip()})
        with st.spinner("Generating answer..."):
            try:
                resp = ask_api(user_input.strip(), category)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state[messages_key].append({
                        "role": "assistant",
                        "content": data["response"],
                        "suggestions": data.get("suggested_questions", [])
                    })
                    st.session_state.query_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": user_input.strip(), "category": category
                    })
                elif resp.status_code == 400:
                    st.session_state[messages_key].append({"role": "assistant", "content": "Invalid query. Please rephrase your question."})
                else:
                    st.session_state[messages_key].append({"role": "assistant", "content": "Something went wrong. Please try again."})
            except Exception:
                st.session_state[messages_key].append({"role": "assistant", "content": "Could not reach the server. Please try again shortly."})
        st.rerun()

    if st.session_state[messages_key]:
        if st.button("Clear conversation", key=f"{category}_clear"):
            st.session_state[messages_key] = []
            st.rerun()


def show_main_app():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/law.png", width=80)
        st.title("LexAssist")
        st.markdown(f"Logged in as **{st.session_state.username}**")
        st.markdown("---")
        page = st.radio("Navigation", [
            "Home", "Ask Legal Question", "Tax Assistant", "General Assistant",
            "Document Explanation", "Query History", "Bookmarks", "About"
        ])
        st.markdown("---")
        st.markdown("### Quick Stats")
        st.metric("Queries This Session", len(st.session_state.query_history))
        st.markdown("---")
        st.markdown('<div class="rag-badge">RAG Enabled</div>', unsafe_allow_html=True)
        st.caption("Powered by Indian legal documents: IPC, Constitution, CRPC, Income Tax Act")
        st.markdown("---")
        st.info("This is an AI assistant and does NOT provide legal advice. Always consult a qualified professional.")
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            for key in ["logged_in", "user_id", "username", "token", "query_history",
                        "legal_messages", "tax_messages", "general_messages"]:
                if key == "logged_in":
                    st.session_state[key] = False
                elif key in ("query_history", "legal_messages", "tax_messages", "general_messages"):
                    st.session_state[key] = []
                else:
                    st.session_state[key] = None
            st.rerun()

    if page == "Home":
        st.markdown('<div class="main-header">Welcome to LexAssist</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Your AI-Powered Legal and Tax Assistant for Indian Law</div>', unsafe_allow_html=True)
        st.markdown('<div class="rag-badge">RAG-Enhanced: Answers grounded in real Indian legal documents</div>', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
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
        st.markdown("---")
        st.markdown('<div class="disclaimer-box"><strong>Disclaimer:</strong> LexAssist provides general information only and is not a substitute for professional legal or tax advice.</div>', unsafe_allow_html=True)

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
                        response = requests.post(f"{API_URL}/explain-document", files=files, headers=auth_headers(), timeout=60)
                        if response.status_code == 200:
                            data = response.json()
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Filename", data["filename"])
                            with col2:
                                st.metric("Text Length", f"{data['text_length']} characters")
                            with st.expander("Extracted Text (Preview)"):
                                st.text(data["extracted_text"])
                            st.markdown(f'<div class="response-box"><h3>AI Explanation</h3>{data["explanation"]}</div>', unsafe_allow_html=True)
                        else:
                            st.error("Could not process the document. Please try again.")
                    except Exception:
                        st.error("Could not reach the server. Please try again shortly.")

    elif page == "Query History":
        st.markdown('<div class="main-header">Query History</div>', unsafe_allow_html=True)
        try:
            offset = st.session_state.history_page * PAGE_SIZE
            resp = requests.get(
                f"{API_URL}/history",
                params={"limit": PAGE_SIZE, "offset": offset},
                headers=auth_headers(), timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                history = data["history"]
                total = data["total"]
                total_pages = max(1, -(-total // PAGE_SIZE))  # ceiling division

                col_info, col_export = st.columns([3, 1])
                with col_info:
                    st.info(f"Total queries: {total} | Page {st.session_state.history_page + 1} of {total_pages}")
                with col_export:
                    export_resp = requests.get(f"{API_URL}/history/export", headers=auth_headers(), timeout=15)
                    if export_resp.status_code == 200:
                        st.download_button(
                            label="⬇ Download CSV",
                            data=export_resp.content,
                            file_name="lexassist_history.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                if history:
                    filter_category = st.selectbox(
                        "Filter by category:",
                        ["All", "legal", "tax", "general", "document"],
                        index=["All", "legal", "tax", "general", "document"].index(st.session_state.history_filter)
                    )
                    st.session_state.history_filter = filter_category

                    # Fetch bookmarked IDs for this user
                    bk_resp = requests.get(f"{API_URL}/bookmarks", headers=auth_headers(), timeout=10)
                    bookmarked_ids = {b["id"] for b in bk_resp.json().get("bookmarks", [])} if bk_resp.status_code == 200 else set()

                    for item in history:
                        if filter_category != "All" and item["category"] != filter_category:
                            continue
                        is_bookmarked = item["id"] in bookmarked_ids
                        star = "⭐" if is_bookmarked else "☆"
                        with st.expander(f"{item['timestamp']} - {item['category'].upper()}"):
                            col_q, col_bk = st.columns([5, 1])
                            with col_q:
                                st.markdown(f"**Query:** {item['query']}")
                            with col_bk:
                                if st.button(f"{star} Bookmark", key=f"bk_{item['id']}"):
                                    toggle_resp = requests.post(
                                        f"{API_URL}/bookmarks/toggle",
                                        json={"query_id": item["id"]},
                                        headers=auth_headers(), timeout=10
                                    )
                                    if toggle_resp.status_code == 200:
                                        st.rerun()
                            st.markdown("---")
                            st.write(item["response"])

                    # Pagination controls
                    st.markdown("---")
                    prev_col, page_col, next_col = st.columns([1, 2, 1])
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
                else:
                    st.info("No queries yet. Start asking questions!")
            else:
                st.error("Failed to load history.")
        except Exception:
            st.error("Could not reach the server. Please try again shortly.")

    elif page == "Bookmarks":
        st.markdown('<div class="main-header">Bookmarks</div>', unsafe_allow_html=True)
        try:
            resp = requests.get(f"{API_URL}/bookmarks", headers=auth_headers(), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                bookmarks = data["bookmarks"]
                if bookmarks:
                    st.info(f"You have {data['count']} bookmarked queries.")
                    for item in bookmarks:
                        with st.expander(f"⭐ {item['timestamp']} - {item['category'].upper()}"):
                            col_q, col_rm = st.columns([5, 1])
                            with col_q:
                                st.markdown(f"**Query:** {item['query']}")
                            with col_rm:
                                if st.button("Remove", key=f"rm_bk_{item['id']}"):
                                    toggle_resp = requests.post(
                                        f"{API_URL}/bookmarks/toggle",
                                        json={"query_id": item["id"]},
                                        headers=auth_headers(), timeout=10
                                    )
                                    if toggle_resp.status_code == 200:
                                        st.rerun()
                            st.markdown("---")
                            st.write(item["response"])
                else:
                    st.info("No bookmarks yet. Star queries in Query History to save them here.")
            else:
                st.error("Failed to load bookmarks.")
        except Exception:
            st.error("Could not reach the server. Please try again shortly.")

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
    show_login_page()
else:
    show_main_app()
