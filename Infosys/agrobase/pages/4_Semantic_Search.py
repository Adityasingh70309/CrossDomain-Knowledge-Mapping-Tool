# pages/4_SemanticSearch.py

import streamlit as st
import pandas as pd
import networkx as nx
import os
import sys
import requests
import importlib
import streamlit.components.v1 as components
from pyvis.network import Network

# --- [PATH CONFIG] ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- [IMPORT DEPENDENCIES] ---
database = importlib.import_module("database")
page_1_explorer = importlib.import_module("pages.1_Explorer")  # for graph visualization reuse

# --- [CONFIG] ---
BACKEND_URL = "http://127.0.0.1:5000"
TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'agri_climate_relations_1000.csv')

# --- [JWT AUTH VALIDATION] ---
def get_user_from_jwt():
    """Validates JWT token by calling Flask /profile endpoint."""
    token = st.session_state.get("jwt_token")
    if not token:
        return None
    try:
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BACKEND_URL}/profile", headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            st.session_state.pop("jwt_token", None)
            return None
    except Exception:
        st.session_state.pop("jwt_token", None)
        return None

# --- [AUTH CHECK] ---
user_info = get_user_from_jwt()
if not user_info:
    st.error("🔒 Please log in first to access this page.")
    st.page_link("streamlit_app.py", label="Back to Login", icon="🏠")
    st.stop()

# --- [PAGE CONFIG] ---
st.markdown(
    """
    <div class="header">
        <div class="title">🔍 Semantic Search</div>
        <div class="subtitle">Find intelligent connections in agriculture and climate knowledge</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- [STYLES] ---
def load_css(file_name):
    """Load global style.css from root directory."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), '..', file_name)
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ CSS file '{file_name}' not found.")

load_css("style.css")

# --- [HEADER] ---
st.markdown(
    f"""
    <div class="header">
        <div class="title">🔍 Semantic Search & Knowledge Query</div>
        <div class="subtitle">Logged in as: {user_info.get('logged_in_as')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- [SIDEBAR ACCOUNT] ---
st.sidebar.title("Account")
st.sidebar.info(f"User: **{user_info.get('logged_in_as')}**")
if st.sidebar.button("Logout 🚪"):
    st.session_state.pop("jwt_token", None)
    st.rerun()

# --- [LOAD SEMANTIC MODEL] ---
@st.cache_resource
def load_sentence_model():
    """Loads the sentence transformer model for semantic similarity."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        return model
    except ImportError:
        st.error("`sentence-transformers` not installed. Run: pip install sentence-transformers")
        return None

@st.cache_data
def load_knowledge_base(csv_path):
    """Loads and encodes concepts from the knowledge base CSV."""
    try:
        df = pd.read_csv(csv_path)
        concepts = pd.concat([df['source'], df['target']]).dropna().unique().astype(str).tolist()

        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')

        with st.spinner("Encoding knowledge base..."):
            from sentence_transformers import util
            embeddings = model.encode(concepts, convert_to_tensor=True)
        return concepts, embeddings, model

    except Exception as e:
        st.error(f"Error loading knowledge base: {e}")
        return None, None, None

# --- [LOAD MODELS & DATA] ---
concepts, concept_embeddings, model = load_knowledge_base(TRAINING_DATA_PATH)

# --- [SEARCH INTERFACE] ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 💬 Enter your semantic query")

query = st.text_input("Ask something related to agriculture or climate:", 
                      placeholder="e.g., How does drought affect farming?")

if query and model and concepts:
    try:
        from sentence_transformers import util

        query_embedding = model.encode(query, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(query_embedding, concept_embeddings)
        results = sorted(list(zip(concepts, cosine_scores[0].tolist())), key=lambda x: x[1], reverse=True)

        st.markdown("---")
        st.markdown("### 🔎 Top Related Concepts")
        top_node_names = []

        for text, score in results[:5]:
            st.markdown(f"- **{text}**  (Similarity: {score:.2f})")
            top_node_names.append(text)

        st.markdown("---")
        st.markdown("### 🌐 Generated Knowledge Subgraph")

        if st.button("Generate Knowledge Subgraph", type="primary"):
            with st.spinner("Querying Neo4j for related relationships..."):
                triples = database.get_subgraph_by_names(top_node_names)

                if not triples:
                    st.warning("No related nodes found in Neo4j for these concepts.")
                else:
                    st.info(f"Found {len(triples)} relationships.")
                    G = nx.Graph()
                    for s, r, t in triples:
                        G.add_node(s, label=s, type="Entity")
                        G.add_node(t, label=t, type="Entity")
                        G.add_edge(s, t, relation=r)

                    html = page_1_explorer.pyvis_from_nx(G, highlight=top_node_names)
                    components.html(html, height=550, scrolling=True)

    except Exception as e:
        st.error(f"Error performing semantic search: {e}")

st.markdown('</div>', unsafe_allow_html=True)
