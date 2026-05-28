import os
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

if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'legal_prefill' not in st.session_state:
    st.session_state.legal_prefill = ""
if 'tax_prefill' not in st.session_state:
    st.session_state.tax_prefill = ""
if 'legal_last_response' not in st.session_state:
    st.session_state.legal_last_response = ""
if 'legal_last_suggestions' not in st.session_state:
    st.session_state.legal_last_suggestions = []
if 'tax_last_response' not in st.session_state:
    st.session_state.tax_last_response = ""
if 'tax_last_suggestions' not in st.session_state:
    st.session_state.tax_last_suggestions = []

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; text-align: center; margin-bottom: 1rem; }
    .sub-header { font-size: 1.2rem; color: #666; text-align: center; margin-bottom: 2rem; }
    .disclaimer-box { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 1rem; margin: 1rem 0; border-radius: 5px; color: #000000; }
    .response-box { background-color: #1e2a3a; color: #e8f4ff; padding: 1.5rem; border-radius: 12px; border: 1px solid #2e4a6a; margin: 1rem 0; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
    .suggestion-box { background-color: #1a3a5c; color: #e8f4ff; padding: 0.9rem 1.2rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #4a9eff; font-size: 0.92rem; font-weight: 500; transition: background 0.2s; }
    .suggestion-box:hover { background-color: #1e4a7a; cursor: pointer; }
    .rag-badge { background-color: #d4edda; border: 1px solid #28a745; padding: 0.3rem 0.8rem; border-radius: 20px; color: #155724; font-size: 0.85rem; display: inline-block; margin-bottom: 1rem; }
    .auth-card {
        background: white;
        padding: 2.5rem 2rem;
        border-radius: 16px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        max-width: 420px;
        margin: 0 auto;
    }
    .auth-logo {
        text-align: center;
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .auth-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.3rem;
    }
    .auth-subtitle {
        text-align: center;
        color: #888;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .auth-divider {
        text-align: center;
        color: #aaa;
        margin: 1rem 0;
        font-size: 0.85rem;
    }
    .feature-row {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 2rem;
        flex-wrap: wrap;
    }
    .feature-item {
        text-align: center;
        color: #555;
        font-size: 0.9rem;
        max-width: 120px;
    }
    .feature-icon {
        font-size: 1.8rem;
        margin-bottom: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)


def show_login_page():
    _, center, _ = st.columns([1, 2, 1])

    with center:
        st.markdown('<div class="auth-logo">⚖</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">LexAssist</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Your personal legal and tax assistant for Indian law</div>', unsafe_allow_html=True)

        st.markdown("")

        tab1, tab2 = st.tabs(["Sign In", "Create Account"])

        with tab1:
            st.markdown("")
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                st.markdown("")
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
                                st.success(f"Welcome back, {data['username']}! Taking you in...")
                                st.rerun()
                            else:
                                st.error("That username or password doesn't look right. Please try again.")
                        except requests.exceptions.ConnectionError:
                            st.error("Could not reach the server. Make sure the backend is running.")
                else:
                    st.warning("Please fill in both your username and password.")

        with tab2:
            st.markdown("")
            with st.form("register_form"):
                new_username = st.text_input("Choose a username", placeholder="Pick something you'll remember")
                new_password = st.text_input("Choose a password", type="password", placeholder="At least 6 characters")
                confirm_password = st.text_input("Confirm your password", type="password", placeholder="Type it again")
                st.markdown("")
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
                                st.error("Could not reach the server. Make sure the backend is running.")
                else:
                    st.warning("Please fill in all three fields to create your account.")

        st.markdown("")
        st.markdown('<div class="auth-divider">Trusted by law students, professionals, and everyday citizens</div>', unsafe_allow_html=True)

    st.markdown("")
    st.markdown("---")
    _, c1, c2, c3, _ = st.columns([1, 1, 1, 1, 1])
    with c1:
        st.markdown("**Legal Questions**\n\nAsk anything about IPC, Constitution, or CRPC in plain language.")
    with c2:
        st.markdown("**Tax Guidance**\n\nUnderstand Income Tax, GST, and deductions without the jargon.")
    with c3:
        st.markdown("**Document Analysis**\n\nUpload any legal document and get a simple explanation.")


def show_main_app():
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/000000/law.png", width=80)
        st.title("LexAssist")
        st.markdown(f"Logged in as **{st.session_state.username}**")
        st.markdown("---")
        page = st.radio(
            "Navigation",
            ["Home", "Ask Legal Question", "Tax Assistant", "Document Explanation", "Query History", "About"]
        )
        st.markdown("---")
        st.markdown("### Quick Stats")
        st.metric("Queries This Session", len(st.session_state.query_history))
        st.markdown("---")
        st.markdown('<div class="rag-badge">RAG Enabled</div>', unsafe_allow_html=True)
        st.caption("Powered by Indian legal documents: IPC, Constitution, CRPC, Income Tax Act")
        st.markdown("---")
        st.markdown("### Important Notice")
        st.info("This is an AI assistant and does NOT provide legal advice. Always consult a qualified professional.")
        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.query_history = []
            st.rerun()

    if page == "Home":
        st.markdown('<div class="main-header">Welcome to LexAssist</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Your AI-Powered Legal and Tax Assistant for Indian Law</div>', unsafe_allow_html=True)
        st.markdown('<div class="rag-badge">RAG-Enhanced: Answers grounded in real Indian legal documents</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("### Legal Assistance")
            st.write("Get simplified explanations of IPC sections, Constitutional articles, and your rights under Indian law.")
        with col2:
            st.markdown("### Tax Guidance")
            st.write("Understand Income Tax Act sections, GST, deductions, and filing requirements.")
        with col3:
            st.markdown("### Document Analysis")
            st.write("Upload legal documents and get easy-to-understand explanations.")

        st.markdown("---")
        st.markdown("### Knowledge Base")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Legal Documents:**")
            st.write("- Indian Penal Code (IPC)")
            st.write("- Constitution of India")
            st.write("- CRPC (Code of Criminal Procedure)")
            st.write("- IndicLegalQA Dataset (10K Q&A)")
        with col2:
            st.markdown("**Tax Documents:**")
            st.write("- Income Tax Bill 2025")
            st.write("- Legal Contract Clauses")
            st.write("- 217 processed text chunks")
            st.write("- 13 cleaned legal documents")

        st.markdown("---")
        st.markdown("### Getting Started")
        st.write("1. Choose a service from the sidebar")
        st.write("2. Ask your question or upload a document")
        st.write("3. Get instant AI-powered insights grounded in Indian law")
        st.markdown('<div class="disclaimer-box"><strong>Disclaimer:</strong> LexAssist provides general information only and is not a substitute for professional legal or tax advice.</div>', unsafe_allow_html=True)

    elif page == "Ask Legal Question":
        st.markdown('<div class="main-header">Legal Question Assistant</div>', unsafe_allow_html=True)
        st.markdown('<div class="rag-badge">Answers grounded in IPC, Constitution and CRPC documents</div>', unsafe_allow_html=True)
        st.write("Ask any legal question and get a simplified explanation based on Indian law. Press Ctrl+Enter or click Ask.")

        # Auto-submit if a suggestion was clicked
        if st.session_state.legal_prefill:
            query = st.session_state.legal_prefill
            st.session_state.legal_prefill = ""
            with st.spinner("Searching legal documents and generating answer..."):
                try:
                    response = requests.post(
                        f"{API_URL}/ask",
                        json={"query": query, "category": "legal", "user_id": st.session_state.user_id},
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.legal_last_response = data["response"]
                        st.session_state.legal_last_suggestions = data.get("suggested_questions", [])
                        st.session_state.query_history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "query": query,
                            "category": "legal"
                        })
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        with st.form(key="legal_question_form", enter_to_submit=True):
            query = st.text_area(
                "Enter your legal question:",
                height=100,
                placeholder="Example: What is Section 302 IPC? What are my rights under Article 21?",
                key="legal_query_input"
            )
            submit_button = st.form_submit_button("Ask", type="primary")

        if submit_button:
            if query and query.strip():
                with st.spinner("Searching legal documents and generating answer..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/ask",
                            json={"query": query, "category": "legal", "user_id": st.session_state.user_id},
                            timeout=30
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.legal_last_response = data["response"]
                            st.session_state.legal_last_suggestions = data.get("suggested_questions", [])
                            st.session_state.query_history.append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "query": query,
                                "category": "legal"
                            })
                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a question before submitting.")

        if st.session_state.get("legal_last_response"):
            st.markdown(f'<div class="response-box"><h3>Response</h3>{st.session_state.legal_last_response}</div>', unsafe_allow_html=True)
            if st.session_state.get("legal_last_suggestions"):
                st.markdown("### Suggested Follow-up Questions")
                for i, suggestion in enumerate(st.session_state.legal_last_suggestions):
                    if st.button(suggestion, key=f"legal_sugg_{i}", use_container_width=True):
                        st.session_state.legal_prefill = suggestion
                        st.rerun()

    elif page == "Tax Assistant":
        st.markdown('<div class="main-header">Tax Assistant</div>', unsafe_allow_html=True)
        st.markdown('<div class="rag-badge">Answers grounded in Income Tax Bill 2025 and tax documents</div>', unsafe_allow_html=True)
        st.write("Get help with Indian tax-related questions. Press Ctrl+Enter or click Ask.")

        # Auto-submit if a suggestion was clicked
        if st.session_state.tax_prefill:
            query = st.session_state.tax_prefill
            st.session_state.tax_prefill = ""
            with st.spinner("Searching tax documents and generating answer..."):
                try:
                    response = requests.post(
                        f"{API_URL}/ask",
                        json={"query": query, "category": "tax", "user_id": st.session_state.user_id},
                        timeout=30
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.tax_last_response = data["response"]
                        st.session_state.tax_last_suggestions = data.get("suggested_questions", [])
                        st.session_state.query_history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "query": query,
                            "category": "tax"
                        })
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

        with st.form(key="tax_question_form", enter_to_submit=True):
            query = st.text_area(
                "Enter your tax question:",
                height=100,
                placeholder="Example: What deductions can I claim under Section 80C? What is GST?",
                key="tax_query_input"
            )
            submit_button = st.form_submit_button("Ask", type="primary")

        if submit_button:
            if query and query.strip():
                with st.spinner("Searching tax documents and generating answer..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/ask",
                            json={"query": query, "category": "tax", "user_id": st.session_state.user_id},
                            timeout=30
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.tax_last_response = data["response"]
                            st.session_state.tax_last_suggestions = data.get("suggested_questions", [])
                            st.session_state.query_history.append({
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "query": query,
                                "category": "tax"
                            })
                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a question before submitting.")

        if st.session_state.get("tax_last_response"):
            st.markdown(f'<div class="response-box"><h3>Response</h3>{st.session_state.tax_last_response}</div>', unsafe_allow_html=True)
            if st.session_state.get("tax_last_suggestions"):
                st.markdown("### Suggested Follow-up Questions")
                for i, suggestion in enumerate(st.session_state.tax_last_suggestions):
                    if st.button(suggestion, key=f"tax_sugg_{i}", use_container_width=True):
                        st.session_state.tax_prefill = suggestion
                        st.rerun()

    elif page == "Document Explanation":
        st.markdown('<div class="main-header">Document Explanation</div>', unsafe_allow_html=True)
        st.write("Upload a legal or tax document (PDF or TXT) and get a simplified explanation.")

        uploaded_file = st.file_uploader("Choose a document", type=['pdf', 'txt'])

        if uploaded_file:
            st.info(f"File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
            if st.button("Explain Document", type="primary"):
                with st.spinner("Analyzing document..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(f"{API_URL}/explain-document", files=files, timeout=60)
                        if response.status_code == 200:
                            data = response.json()
                            st.markdown("### Document Information")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Filename", data['filename'])
                            with col2:
                                st.metric("Text Length", f"{data['text_length']} characters")
                            st.markdown("---")
                            with st.expander("Extracted Text (Preview)"):
                                st.text(data['extracted_text'])
                            st.markdown(f'<div class="response-box"><h3>AI Explanation</h3>{data["explanation"]}</div>', unsafe_allow_html=True)
                            if st.button("Copy Explanation", key="copy_doc"):
                                st.code(data['explanation'], language=None)
                                st.success("Explanation ready to copy!")
                            st.success("Document analyzed successfully!")
                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to backend. Make sure the FastAPI server is running on http://localhost:8000")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    elif page == "Query History":
        st.markdown('<div class="main-header">Query History</div>', unsafe_allow_html=True)
        try:
            response = requests.get(
                f"{API_URL}/history",
                params={"user_id": st.session_state.user_id},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                history = data['history']
                if history:
                    st.info(f"Total queries: {data['count']}")
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        filter_category = st.selectbox("Filter by category:", ["All", "legal", "tax"])
                    for item in history:
                        if filter_category == "All" or item['category'] == filter_category:
                            with st.expander(f"{item['timestamp']} - {item['category'].upper()}"):
                                st.markdown(f"**Query:** {item['query']}")
                                st.markdown("---")
                                st.markdown("**Response:**")
                                st.write(item['response'])
                                if st.button("Copy", key=f"copy_{item['id']}"):
                                    st.code(item['response'], language=None)
                                    st.success("Ready to copy!")
                else:
                    st.info("No queries yet. Start asking questions!")
            else:
                st.error("Failed to load history")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to backend. Make sure the server is running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    elif page == "About":
        st.markdown('<div class="main-header">About LexAssist</div>', unsafe_allow_html=True)
        st.markdown("""
        ### What is LexAssist?
        LexAssist is an AI-powered legal and tax assistant designed to help users understand complex Indian legal and tax concepts in simple, easy-to-understand language.

        ### RAG Enhancement
        This version uses Retrieval-Augmented Generation (RAG) to ground answers in real Indian legal documents:
        - 217 text chunks from processed legal documents
        - Indian Penal Code (IPC) - sections and definitions
        - Constitution of India - articles and rights
        - CRPC - criminal procedure
        - Income Tax Bill 2025 - latest tax provisions
        - IndicLegalQA Dataset - 10,000 legal Q&A pairs
        - Legal Contract Clauses - contract terminology

        ### Features
        - Legal Question Assistant: Ask any legal question grounded in Indian law
        - Tax Assistant: Get help with Indian tax queries
        - Document Explanation: Upload legal or tax documents for plain-language explanations
        - Query History: Each user sees only their own past queries
        - Suggested Questions: Get relevant follow-up question suggestions

        ### Technology Stack
        - Frontend: Streamlit
        - Backend: FastAPI
        - AI: Groq (llama-3.1-8b-instant)
        - RAG: FAISS vector search with sentence-transformers embeddings
        - Database: SQLite

        ### Important Disclaimer
        LexAssist is an informational tool only. Responses are AI-generated and should not be considered professional legal or tax advice. Always consult a qualified attorney or tax professional.
        """)


if not st.session_state.logged_in:
    show_login_page()
else:
    show_main_app()
