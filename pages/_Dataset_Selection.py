import streamlit as st
from streamlit_option_menu import option_menu # For the icons
import time
import pandas as pd  # <-- Correctly imported!

# Import all our pipeline functions
# Note: We assume pipelines/ and database.py are in the parent directory
import sys
import os # Import os to check file path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipelines.text_cleaner import clean_text
from pipelines.extraction import load_nlp_model, extract_triples_from_doc
from pipelines.neo4j_loader import store_triples_in_neo4j
from database import clear_database

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Knowmap - Ingestion")

# --- FIX 1: Corrected function definition ---
def load_css(file_name):
    """
    Function to load CSS from a file.
    'file_name' is the variable holding the path.
    """
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Use the 'file_name' variable in the error
        st.warning(f"CSS file not found: {file_name}. Styles will not be applied.")

# --- Auth Check ---
# Secure this page
if not st.session_state.get("authenticated", False):
    st.error("🔒 Please log in first to access this page.")
    st.page_link("streamlit_app.py", label="Back to Login", icon="🏠")
    st.stop()

# --- Load CSS ---
# --- FIX 2: Corrected file path ---
# We just need "style.css" because Streamlit runs from the root folder
load_css("style.css")

# --- Load NLP Model ---
# This is cached, so it only loads once
nlp = load_nlp_model()

# --- Header ---
st.markdown(
    """
    <div class="header-bar">
        <span>Milestone 1: User Authentication & Dataset Selection</span>
        <span class="header-badge">Weeks 1-3</span>
    </div>
    """, 
    unsafe_allow_html=True
)
st.write("") # Spacer

# --- Main Page Layout ---
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Working Application Preview")
    
    # Use option_menu for the dataset selection with icons
    selected_source = option_menu(
        menu_title="Dataset Selection",
        options=["Wikipedia Articles", "Scientific Papers (ArXiv)", "News Articles", "Custom Upload"],
        icons=['wikipedia', 'book-fill', 'newspaper', 'cloud-upload-fill'], # From bootstrap-icons
        menu_icon="collection-fill",
        default_index=3, # Start with Custom Upload selected
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#f0f2f6"},
        }
    )

    st.write("") # Spacer

    # Input fields
    process_text = None
    if selected_source == "Custom Upload":
        uploaded_file = st.file_uploader("Upload a .txt file", type=["txt"])
        if uploaded_file:
            process_text = uploaded_file.read().decode("utf-8")
    else:
        text_input = st.text_area("Enter search query, article title, or URL:", 
                                    placeholder=f"e.g., Article titles for {selected_source}")
        if text_input:
            # In a real app, you'd fetch the data (e.g., from Wikipedia API)
            # For this demo, we'll just process the query text itself
            st.warning(f"Demo Mode: Processing the query text directly, not fetching from {selected_source}.")
            process_text = text_input

    if st.button("Process Selected Datasets", type="primary", use_container_width=True):
        
        # Run the pipeline
        if process_text and nlp:
            with st.spinner("Running NLP Pipeline... This may take a moment."):
                
                # 1. Clean the text
                cleaned_text = clean_text(process_text)
                
                # 2. Process with spaCy
                doc = nlp(cleaned_text)
                
                # 3. Extract triples
                triples = extract_triples_from_doc(doc)
                
                # 4. Store in Neo4j
                store_triples_in_neo4j(triples)
                
            st.success("Pipeline finished! The Knowledge Graph is updated.")
            
            if triples:
                st.write(f"Found {len(triples)} structured triples:")
                # --- THIS IS THE FIX ---
                # 1. Convert the list of tuples into a pandas DataFrame
                df_triples = pd.DataFrame(
                    triples, 
                    columns=["Subject", "Relation", "Object"]
                )
                # 2. Display the DataFrame
                st.dataframe(df_triples, use_container_width=True)
                # -----------------------
            else:
                st.warning("No triples were extracted from this input.")
        
        elif not nlp:
             st.error("NLP Model is not loaded. Cannot process text.")
        else:
            st.error("Please provide some input before processing.")
            
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # --- Sidebar Info (from image) ---
    st.markdown('<div class="card">', unsafe_allow_html=True)
    with st.expander("Authentication Features", expanded=True):
        st.markdown("- JWT security implementation")
        st.markdown("- Secure password hashing")
        st.markdown("- Session management system")

    with st.expander("Dataset Management", expanded=True):
        st.markdown("- Multiple source support")
        st.markdown("- Custom upload functionality")
        st.markdown("- Format validation for data")

    with st.expander("Expected Outcome", expanded=True):
        st.markdown("- Complete user auth system")
        st.markdown("- Dataset selection interface")
        st.markdown("- Profile management for graphs")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Admin Utility ---
st.divider()
if st.button("⚠️ Clear Entire Database (Admin)"):
    with st.spinner("Deleting all nodes and relationships..."):
        clear_database()
    st.success("Database cleared.")

