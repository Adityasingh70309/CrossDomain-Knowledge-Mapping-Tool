import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import networkx as nx
import tempfile
import os
import sys
from pyvis.network import Network
import plotly.graph_objects as go
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
        <div class="title">🌾 KNOWMAP Explorer</div>
        <div class="subtitle">Visualize knowledge graphs across agriculture and climate domains</div>
    </div>
    """,
    unsafe_allow_html=True,
)


def load_css(file_name):
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
        <div class="title">🧭 KNOWMAP: Knowledge Explorer</div>
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

# --- 3. UTILITY FUNCTIONS ---
# ... (All your graph functions: COLOR_BY_TYPE, load_sample_graph, etc.) ...
COLOR_BY_TYPE = {
    "Crop": "#ff7f50", "Soil": "#8bd46f", "Water": "#38bdf8", "Pest": "#ffb86b",
    "Climate": "#7c3aed", "Emission": "#f97316", "Policy": "#06b6d4",
    "Practice": "#f472b6", "Default": "#94a3b8",
}

def color_for(t):
    return COLOR_BY_TYPE.get(t, COLOR_BY_TYPE["Default"])

@st.cache_data
def load_sample_graph(domain="Agriculture"):
    G = nx.Graph()
    if domain == "Agriculture":
        nodes = [
            ("Wheat", "Crop"), ("Corn", "Crop"), ("Soil pH", "Soil"),
            ("Irrigation", "Practice"), ("Pesticide X", "Pest"),
            ("Yield", "Practice"), ("Rainfall", "Water")
        ]
        edges = [
            ("Wheat", "Soil pH", "affected_by"), ("Wheat", "Rainfall", "depends_on"),
            ("Corn", "Irrigation", "needs"), ("Pesticide X", "Wheat", "impacts"),
            ("Yield", "Wheat", "determines"), ("Yield", "Soil pH", "correlates"),
        ]
    else:  # Climate Change
        nodes = [
            ("CO2 Levels", "Emission"), ("Global Temp", "Climate"),
            ("Sea Level", "Climate"), ("Deforestation", "Practice"),
            ("Methane", "Emission"), ("Policy A", "Policy")
        ]
        edges = [
            ("CO2 Levels", "Global Temp", "drives"), ("Methane", "Global Temp", "drives"),
            ("Deforestation", "CO2 Levels", "contributes"), ("Policy A", "Deforestation", "mediates"),
            ("Global Temp", "Sea Level", "raises"),
        ]
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
        rel = row.get("relation") or row.get("Relation") or ""
        s_type = row.get("source_type") or row.get("Source_Type") or row.get("sourceType") or "Default"
        t_type = row.get("target_type") or row.get("Target_Type") or row.get("targetType") or "Default"
        if not s or not t:
            continue
        G.add_node(s, label=s, type=s_type)
        G.add_node(t, label=t, type=t_type)
        G.add_edge(s, t, relation=rel)
    return G

def pyvis_from_nx(G, height="650px", width="100%", notebook=False, highlight=None):
    net = Network(height=height, width=width, bgcolor="#071126", font_color="#E6EEF3", notebook=notebook)
    net.force_atlas_2based()
    for n, d in G.nodes(data=True):
        ntype = d.get("type", "Default")
        net.add_node(n, label=d.get("label", n), title=f"{n} — {ntype}", color=color_for(ntype), value=2)
    for a, b, d in G.edges(data=True):
        net.add_edge(a, b, title=d.get("relation", ""))
    if highlight:
        for node in net.nodes:
            if node["id"] in highlight:
                node["size"] = 28
                node["color"] = "#ffffff"
    
    html_string = net.generate_html()
    return html_string


def pyvis_hierarchical_from_nx(G, height="650px", width="100%", highlight=None, direction="UD"):
    """Render a hierarchical layout using vis.js hierarchical option via pyvis.
    direction: 'UD' (top-down), 'DU' (bottom-up), 'LR' (left-right), 'RL' (right-left)
    """
    net = Network(height=height, width=width, bgcolor="#071126", font_color="#E6EEF3", directed=True)
    # add nodes
    for n, d in G.nodes(data=True):
        ntype = d.get("type", "Default")
        net.add_node(n, label=d.get("label", n), title=f"{n} — {ntype}", color=color_for(ntype), value=2)
    for a, b, d in G.edges(data=True):
        net.add_edge(a, b, title=d.get("relation", ""))
    if highlight:
        for node in net.nodes:
            if node["id"] in highlight:
                node["size"] = 28
                node["color"] = "#ffffff"

    import json
    opts = {
        "layout": {
            "hierarchical": {
                "enabled": True,
                "levelSeparation": 150,
                "nodeSpacing": 100,
                "treeSpacing": 200,
                "direction": direction,
                "sortMethod": "directed"
            }
        },
        "physics": {
            "hierarchicalRepulsion": {
                "centralGravity": 0.0,
                "springLength": 100,
                "springConstant": 0.01,
                "nodeDistance": 120
            }
        }
    }
    net.set_options(json.dumps(opts))
    return net.generate_html()

def plotly_network(G, highlight=None):
    pos = nx.spring_layout(G, seed=42)
    edge_x = []
    edge_y = []
    for e in G.edges():
        x0, y0 = pos[e[0]]
        x1, y1 = pos[e[1]]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    for n, d in G.nodes(data=True):
        x, y = pos[n]
        node_x.append(x); node_y.append(y)
        node_text.append(f"{n} — {d.get('type','')}")
        typ = d.get("type", "Default")
        node_color.append(color_for(typ))
        node_size.append(18 if not highlight or n not in highlight else 34)
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="#3b4450"), hoverinfo="none")
    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text", text=[n for n in G.nodes()],
        marker=dict(color=node_color, size=node_size, line=dict(color="#02121a", width=1)),
        textposition="top center", hovertext=node_text, hoverinfo="text"
    )
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        paper_bgcolor="#071126", plot_bgcolor="#071126",
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False, height=650,
        font_color='white'
    )
    return fig

# --- 4. EXPLORER PAGE LAYOUT ---
st.markdown('<div class="card">', unsafe_allow_html=True)
left, right = st.columns([1.2, 2])

with left:
    st.markdown("#### Dataset")
    ds_choice = st.radio("Select dataset", ("Neo4j: Current DB", "Preloaded: Agriculture", "Preloaded: Climate Change", "Upload CSV"))
    uploaded_file = None
    if ds_choice == "Upload CSV":
        uploaded_file = st.file_uploader("Upload edges CSV (columns: source,target,relation,source_type,target_type)", type=["csv"])
    elif ds_choice == "Neo4j: Current DB":
        # Load the entire graph edges from Neo4j
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
                    st.markdown(f"Loaded from Neo4j: **{len(G.nodes())} nodes**, **{len(G.edges())} edges**")
        except Exception as e:
            st.error(f"Neo4j query failed: {e}")
            G = load_sample_graph("Agriculture")
    
    st.markdown("#### Node Filters")
    if ds_choice.startswith("Preloaded"):
        domain = "Agriculture" if "Agriculture" in ds_choice else "Climate Change"
        G = load_sample_graph(domain)
        st.markdown(f"Loaded sample: **{domain}**")
    elif uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            G = graph_from_dataframe(df)
            st.markdown(f"Uploaded dataset with **{len(G.nodes())} nodes** and **{len(G.edges())} edges**")
        except Exception as e:
            st.error("Failed to parse CSV. Ensure it has 'source' and 'target' columns.")
            st.stop()
    else:
        st.info("Upload a CSV to visualize your own data, or choose a preloaded dataset.")
        G = load_sample_graph("Agriculture")
    
    all_types = sorted({d.get("type", "Default") for _, d in G.nodes(data=True)})
    selected_types = st.multiselect("Show node types", options=all_types, default=all_types)
    
    st.markdown("#### Search Entities")
    search = st.text_input("Search node by name")
    highlight_nodes = []
    if search:
        highlight_nodes = [n for n in G.nodes() if search.lower() in n.lower()]
        st.caption(f"Matches: {len(highlight_nodes)}")
    
    st.write("")
    st.markdown("#### Export / Controls")
    if st.button("Download visible subgraph as CSV"):
        sub_nodes = [n for n, d in G.nodes(data=True) if d.get("type", "Default") in selected_types]
        sub_edges = [(a, b, G.edges[a, b].get("relation", "")) for a, b in G.edges() if a in sub_nodes and b in sub_nodes]
        df_out = pd.DataFrame(sub_edges, columns=["source", "target", "relation"])
        st.download_button("Download CSV", df_out.to_csv(index=False), file_name="knowmap_subgraph.csv", mime="text/csv")
    
    st.markdown('<div class="footer">Tip: CSV columns: source,target,relation,source_type,target_type</div>', unsafe_allow_html=True)

with right:
    st.markdown("#### Interactive Graph")
    H = nx.Graph()
    for n, d in G.nodes(data=True):
        if d.get("type", "Default") in selected_types:
            H.add_node(n, **d)
    for a, b, d in G.edges(data=True):
        if a in H.nodes() and b in H.nodes():
            H.add_edge(a, b, **d)
            
    if len(H.nodes()) == 0:
        st.warning("No nodes match the selected filters.")
    else:
        try:
            layout = st.selectbox("Layout", ["Force-Directed", "Hierarchical - Top Down", "Hierarchical - Left to Right"], index=0)
            if layout.startswith("Hierarchical"):
                direction = "UD" if "Top Down" in layout else "LR"
                html = pyvis_hierarchical_from_nx(H, highlight=highlight_nodes, direction=direction)
            else:
                html = pyvis_from_nx(H, highlight=highlight_nodes)
            components.html(html, height=700, scrolling=True)
        except Exception as e:
            st.error(f"Pyvis render failed: {e}. Falling back to Plotly.")
            try:
                fig = plotly_network(H, highlight=highlight_nodes)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e2:
                st.error(f"Plotly fallback also failed. Error: {e2}")

    st.markdown("#### Entity Details")
    if highlight_nodes:
        for n in highlight_nodes[:6]:
            if n in H.nodes():
                dtype = H.nodes[n].get("type", "")
                st.markdown(f"- <span class='filter-pill'>{n}</span> <span style='color:#9CCFD9; margin-left:10px;'>{dtype}</span>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='small'>PyVis nodes are interactive. Hover to see info.</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)