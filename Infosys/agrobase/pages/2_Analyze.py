import streamlit as st
import pandas as pd
import networkx as nx
import os
import sys
import plotly.express as px
import requests  # <-- Import requests
import importlib

# --- Config ---
BACKEND_URL = "http://127.0.0.1:5000"  # Your Flask server address
database = importlib.import_module("database")

# --- 1. AUTHENTICATION CHECK ---
def get_user_from_jwt():
    """
    Validates the JWT token by calling the backend /profile route.
    """
    token = st.session_state.get("jwt_token")
    if not token:
        return None
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BACKEND_URL}/profile", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.session_state.pop("jwt_token", None)
            return None
    except Exception:
        st.session_state.pop("jwt_token", None)
        return None

user_info = get_user_from_jwt()
if not user_info:
    st.error("🔒 Please log in first to access this page.")
    st.page_link("streamlit_app.py", label="Back to Login", icon="🏠")
    st.stop()

# --- 2. PAGE CONFIG AND STYLES ---
st.markdown(
    """
    <div class="header">
        <div class="title">📊 Graph Analytics</div>
        <div class="subtitle">Understand patterns in agricultural relationships</div>
    </div>
    """,
    unsafe_allow_html=True,
)


def load_css(file_name):
    """Loads the CSS file from the root directory."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), '..', file_name)
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"CSS file '{file_name}' not found.")

load_css("style.css")

# Page Header
st.markdown(
    f"""
    <div class="header">
        <div class="title">📊 Graph Analytics & Metrics</div>
        <div class="subtitle">Logged in as: {user_info.get('logged_in_as')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar Logout
st.sidebar.title("Account")
st.sidebar.info(f"User: **{user_info.get('logged_in_as')}**")
if st.sidebar.button("Logout"):
    st.session_state.pop("jwt_token", None) # Use 'jwt_token'
    st.rerun()

# --- 3. UTILITY FUNCTIONS (Copied from Explorer) ---
@st.cache_data
def load_sample_graph(domain="Agriculture"):
    G = nx.Graph()
    if domain == "Agriculture":
        nodes = [("Wheat", "Crop"), ("Corn", "Crop"), ("Soil pH", "Soil"), ("Irrigation", "Practice"), ("Pesticide X", "Pest"), ("Yield", "Practice"), ("Rainfall", "Water")]
        edges = [("Wheat", "Soil pH", "affected_by"), ("Wheat", "Rainfall", "depends_on"), ("Corn", "Irrigation", "needs"), ("Pesticide X", "Wheat", "impacts"), ("Yield", "Wheat", "determines"), ("Yield", "Soil pH", "correlates")]
    else:
        nodes = [("CO2 Levels", "Emission"), ("Global Temp", "Climate"), ("Sea Level", "Climate"), ("Deforestation", "Practice"), ("Methane", "Emission"), ("Policy A", "Policy")]
        edges = [("CO2 Levels", "Global Temp", "drives"), ("Methane", "Global Temp", "drives"), ("Deforestation", "CO2 Levels", "contributes"), ("Policy A", "Deforestation", "mediates"), ("Global Temp", "Sea Level", "raises")]
    for n, t in nodes:
        G.add_node(n, label=n, type=t)
    for a, b, rel in edges:
        G.add_edge(a, b, relation=rel)
    return G

@st.cache_data
def graph_from_dataframe(df):
    G = nx.Graph()
    for _, row in df.iterrows():
        s = str(row.get("source") or row.get("Source"))
        t = str(row.get("target") or row.get("Target"))
        if not s or not t:
            continue
        G.add_node(s, label=s, type=row.get("source_type", "Default"))
        G.add_node(t, label=t, type=row.get("target_type", "Default"))
        G.add_edge(s, t, relation=row.get("relation", ""))
    return G

# --- 4. ANALYTICS PAGE LAYOUT ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.write("Choose Neo4j or local datasets to compute metrics.")

col1, col2 = st.columns([1, 2])
with col1:
    ds_choice = st.selectbox("Dataset", ("Neo4j: Current DB", "Preloaded: Agriculture", "Preloaded: Climate Change", "Upload CSV for analysis"))
    uploaded_file = None
    if ds_choice == "Upload CSV for analysis":
        uploaded_file = st.file_uploader("Upload edges CSV (source,target,...)", type=["csv"])
    
    if ds_choice == "Neo4j: Current DB":
        try:
            graph = database.get_neo4j_graph()
            if graph is None:
                st.error("Neo4j not connected. Configure credentials in .env.")
                G = load_sample_graph("Agriculture")
            else:
                query = """
                MATCH (a)-[r]-(b)
                RETURN a.name AS source, type(r) AS relation, b.name AS target
                """
                rows = graph.run(query).to_data_frame()
                if rows is None or rows.empty:
                    st.info("No data in Neo4j yet. Ingest on the Ingestion page.")
                    G = load_sample_graph("Agriculture")
                else:
                    G = graph_from_dataframe(rows)
        except Exception as e:
            st.error(f"Neo4j query failed: {e}")
            G = load_sample_graph("Agriculture")
    elif ds_choice.startswith("Preloaded"):
        domain = "Agriculture" if "Agriculture" in ds_choice else "Climate Change"
        G = load_sample_graph(domain)
    elif uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            G = graph_from_dataframe(df)
        except Exception:
            st.error("Failed to parse CSV.")
            st.stop()
    else:
        G = load_sample_graph("Agriculture") # Default

with col2:
    st.markdown("#### Quick Metrics")
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Nodes", len(G.nodes()))
    m_col2.metric("Edges", len(G.edges()))
    degs = dict(G.degree())
    avg_deg = sum(degs.values()) / max(len(degs), 1)
    m_col3.metric("Avg Degree", f"{avg_deg:.2f}")

st.write("")
st.divider()

# --- Charts ---
a_col1, a_col2 = st.columns(2)
with a_col1:
    # Degree distribution
    deg_values = list(degs.values()) if degs else []
    if deg_values:
        fig = px.histogram(deg_values, nbins=10, title="Degree Distribution", labels={"value": "Degree", "count": "Count"})
        fig.update_layout(paper_bgcolor="#071126", plot_bgcolor="#071126", font_color="#E6EEF3", height=320)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("#### Top Central Nodes (by degree)")
    top = sorted(degs.items(), key=lambda x: x[1], reverse=True)[:8]
    for n, dv in top:
        st.markdown(f"- <span class='filter-pill'>{n}</span> <span style='color:#9CCFD9; margin-left:10px;'>degree: {dv}</span>", unsafe_allow_html=True)

with a_col2:
    # Node type composition
    types = {}
    for _, d in G.nodes(data=True):
        t = d.get("type", "Default")
        types[t] = types.get(t, 0) + 1
    if types:
        pie = px.pie(names=list(types.keys()), values=list(types.values()), title="Node Types", hole=0.3)
        pie.update_layout(paper_bgcolor="#071126", legend_font_color="#E6EEF3", font_color="#E6EEF3", height=320)
        st.plotly_chart(pie, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)