import streamlit as st
import requests
import time
import logging
import os
from typing import Optional
from streamlit_option_menu import option_menu

BACKEND_URL = "http://127.0.0.1:5000"

# --- Helpers: API calls ---
def api_register(email: str, password: str) -> tuple[bool, str]:
    try:
        r = requests.post(f"{BACKEND_URL}/register", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 201:
            return True, "Registered successfully. Please login."
        return False, r.json().get("message", f"Registration failed ({r.status_code}).")
    except Exception as e:
        return False, f"Registration error: {e}"

def api_login(email: str, password: str) -> tuple[bool, Optional[str], str]:
    try:
        r = requests.post(f"{BACKEND_URL}/login", json={"email": email, "password": password}, timeout=10)
        if r.status_code == 200:
            token = r.json().get("token")
            return True, token, "Login successful."
        return False, None, r.json().get("message", f"Login failed ({r.status_code}).")
    except Exception as e:
        return False, None, f"Login error: {e}"

def api_profile(token: str) -> tuple[bool, str]:
    try:
        r = requests.get(f"{BACKEND_URL}/profile", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        if r.status_code == 200:
            return True, r.json().get("logged_in_as", "")
        return False, r.json().get("message", f"Profile failed ({r.status_code}).")
    except Exception as e:
        return False, f"Profile error: {e}"

def api_ingest(file_bytes: bytes, filename: str, token: str) -> tuple[bool, dict | str]:
    try:
        files = {"file": (filename, file_bytes)}
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.post(f"{BACKEND_URL}/ingest_data", files=files, headers=headers, timeout=60)
        if r.status_code == 200:
            return True, r.json()
        return False, r.json().get("message", f"Ingestion failed ({r.status_code}).")
    except Exception as e:
        return False, f"Ingest error: {e}"

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="KNOWMAP – AgriClimate Intelligence",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Load CSS (UTF-8 Safe) ---
def load_css(file_name="style.css"):
    try:
        base_dir = os.path.dirname(__file__)
        candidates = [
            os.path.join(base_dir, file_name),                 # same folder as this file
            os.path.join(base_dir, "..", file_name),          # parent folder (just in case)
        ]
        for path in candidates:
            if os.path.exists(path):
                with open(path, encoding="utf-8") as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
                return
        st.warning(f"CSS Load Error: file '{file_name}' not found near {base_dir}")
    except Exception as e:
        st.warning(f"CSS Load Error: {e}")

load_css("style.css")

# --- Session State ---
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "show_auth" not in st.session_state:
    st.session_state.show_auth = False
if "jwt_token" not in st.session_state:
    st.session_state.jwt_token = None
if "post_login_target" not in st.session_state:
    st.session_state.post_login_target = None

VALID_PAGES = ("Home", "Explore", "Analyze", "Ingest", "Search")
PAGE_TO_FILE = {
    "Explore": "pages/1_Explorer.py",
    "Analyze": "pages/2_Analyze.py",
    "Ingest": "pages/3_Data_Ingestion.py",
    "Search": "pages/4_Semantic_Search.py",
}

# --- Sync page with URL query params ---
try:
    params = st.query_params
    qp_page = params.get("page")
    if qp_page in VALID_PAGES:
        st.session_state.page = qp_page
except Exception:
    pass

def sync_query_params():
    try:
        st.query_params["page"] = st.session_state.page
    except Exception:
        pass

# --- Top Navigation (Option Menu + auth controls) ---
nav_left, nav_right = st.columns([5, 2])
with nav_left:
    selected = option_menu(
        menu_title=None,
        options=list(VALID_PAGES),
        icons=["house", "compass", "graph-up", "cloud-upload", "search"],
        orientation="horizontal",
        default_index=list(VALID_PAGES).index(st.session_state.page),
        styles={
            "container": {"padding": "1!important", "background-color": "#E7F6E7"},
            "nav-link": {"font-size": "14px", "margin":"0 8px", "padding":"6px 10px"},
            "nav-link-selected": {"background-color": "#2e7d32", "color": "white"},
        }
    )
    if selected != st.session_state.page:
        st.session_state.page = selected
        sync_query_params()
        # Navigate to multipage files for non-Home selections
        if selected == "Home":
            st.rerun()
        else:
            target = PAGE_TO_FILE.get(selected)
            if target:
                if not st.session_state.auth_token:
                    st.session_state.show_auth = True
                    st.session_state.post_login_target = target
                    st.info("Please sign in to continue.")
                else:
                    try:
                        st.switch_page(target)
                    except Exception:
                        st.warning("Unable to switch page. Ensure Streamlit multipage is enabled.")
                        st.rerun()
with nav_right:
    if st.session_state.auth_token:
        st.caption("Signed in as")
        st.write(f"✅ {st.session_state.user_email}")
        if st.button("Sign out", key="nav_signout"):
            st.session_state.auth_token = None
            st.session_state.user_email = None
            st.session_state.page = "Home"
            sync_query_params()
            st.success("Signed out.")
            st.rerun()
    else:
        if st.button("Sign In", key="nav_signin"):
            st.session_state.show_auth = True
            st.session_state.page = st.session_state.page
            sync_query_params()

# Note: The previous pure-HTML navbar looked nice but wasn't interactive
# in Streamlit. The Streamlit buttons above replace that behavior.

# --- Auth Panel (Sidebar) ---
with st.sidebar:
    st.header("Account")
    if st.session_state.auth_token:
        ok, who = api_profile(st.session_state.auth_token)
        if ok:
            st.success(f"Logged in as {who}")
        else:
            st.warning("Session might be invalid; please login again.")
        if st.button("Sign out", key="sidebar_signout"):
            st.session_state.auth_token = None
            st.session_state.user_email = None
            st.success("Signed out.")
    else:
        login_tab, register_tab = st.tabs(["Login", "Register"])
        with login_tab:
            email = st.text_input("Email", key="login_email")
            pwd = st.text_input("Password", type="password", key="login_pwd")
            if st.button("Login", key="login_btn"):
                ok, token, msg = api_login(email, pwd)
                if ok and token:
                    st.session_state.auth_token = token
                    st.session_state.jwt_token = token  # keep in sync for pages/
                    st.session_state.user_email = email
                    st.success("Login successful.")
                    # Navigate to intended page after login if any
                    target = st.session_state.post_login_target
                    st.session_state.post_login_target = None
                    if target:
                        try:
                            st.switch_page(target)
                        except Exception:
                            st.rerun()
                    else:
                        st.rerun()
                else:
                    st.error(msg)
        with register_tab:
            remail = st.text_input("Email", key="reg_email")
            rpwd = st.text_input("Password", type="password", key="reg_pwd")
            if st.button("Register", key="reg_btn"):
                ok, msg = api_register(remail, rpwd)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

if st.session_state.page == "Home":
    # (Hero HTML snippet removed by request)

    # --- Features Section ---
    st.markdown(
        """
        <div class="features">
            <h2>Why Choose KNOWMAP?</h2>
            <div class="feature-grid">
                <div class="feature-card">
                    <img src="https://cdn-icons-png.flaticon.com/512/4149/4149729.png" width="60">
                    <h4>Entity Extraction</h4>
                    <p>Automatically extract crops, soil factors, and environmental parameters using AI-powered NLP.</p>
                </div>
                <div class="feature-card">
                    <img src="https://cdn-icons-png.flaticon.com/512/2907/2907314.png" width="60">
                    <h4>Knowledge Graphs</h4>
                    <p>Visualize complex agricultural relationships with dynamic graph-based data visualization.</p>
                </div>
                <div class="feature-card">
                    <img src="https://cdn-icons-png.flaticon.com/512/2721/2721287.png" width="60">
                    <h4>Semantic Search</h4>
                    <p>Search across agriculture and climate datasets using meaning-based AI similarity models.</p>
                </div>
                <div class="feature-card">
                    <img src="https://cdn-icons-png.flaticon.com/512/4359/4359948.png" width="60">
                    <h4>Neo4j Integration</h4>
                    <p>All data stored securely in Neo4j for high-performance graph storage and retrieval.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# For non-Home pages, the app will switch to the multipage files via st.switch_page

# --- Footer ---
st.markdown(
    """
    <div class="footer">
        © 2025 KNOWMAP — Building Sustainable Intelligence for Agriculture 🌾
    </div>
    """,
    unsafe_allow_html=True
)
