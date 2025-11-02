import streamlit as st
import time

# Function to load CSS from a file
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Page Configuration ---
st.set_page_config(
    page_title="Knowmap - Login",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Load Custom CSS ---
load_css("style.css")

# --- Authentication Logic (Stub) ---
# In a real app, you'd hash passwords and check against a database.
def check_login(email, password):
    """A simple login stub."""
    if email and password: # Simple check: are fields non-empty?
        return True
    return False

# --- Main App ---

# Check if user is already authenticated
if st.session_state.get("authenticated", False):
    st.success(f"Welcome back, {st.session_state.get('email', 'user')}!")
    st.page_link("pages/_Dataset_Selection.py", label="Go to App Dashboard", icon="➡️")
    
    if st.button("Logout", type="secondary"):
        st.session_state["authenticated"] = False
        st.rerun()
else:
    # --- Login Form ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### User Authentication")
    
    email = st.text_input("Email", placeholder="user@example.com")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.checkbox("Remember me")
    with col2:
        # Streamlit doesn't have a link button, so we use markdown
        st.markdown(
            '<a href="#" class="forgot-password-link">Forgot password?</a>', 
            unsafe_allow_html=True
        )
    
    st.write("") # Spacer
    
    if st.button("Sign In", type="primary", use_container_width=True):
        if check_login(email, password):
            st.session_state["authenticated"] = True
            st.session_state["email"] = email
            with st.spinner("Logging in..."):
                time.sleep(1)
            st.rerun()
        else:
            st.error("Please enter both email and password.")
            
    if st.button("Create Account", type="secondary", use_container_width=True):
        st.info("Create Account functionality is not yet implemented.")
        
    st.markdown('</div>', unsafe_allow_html=True)
