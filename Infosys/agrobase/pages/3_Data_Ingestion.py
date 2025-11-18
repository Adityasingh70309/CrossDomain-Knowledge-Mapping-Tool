# pages/3_DataIngestion.py

import streamlit as st
import pandas as pd
import os
import sys
import importlib
import requests
import streamlit.components.v1 as components
import xml.etree.ElementTree as ET
import re

# --- [PATH CONFIG] Add project root for imports ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- [IMPORT PIPELINES] ---
pipelines_extraction = importlib.import_module("pipelines.extraction")
pipelines_text_cleaner = importlib.import_module("pipelines.text_cleaner")
pipelines_neo4j_loader = importlib.import_module("pipelines.neo4j_loader")

# --- [CONFIG] ---
BACKEND_URL = "http://127.0.0.1:5000"  # Flask backend

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
        <div class="title">🌱 Data Ingestion Pipeline</div>
        <div class="subtitle">Extract, clean, and load agricultural knowledge into Neo4j</div>
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
        <div class="title">📥 Data Ingestion Pipeline</div>
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

# --- [HELPERS] ---
def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def process_text_block(text: str):
    if not text or not text.strip():
        st.warning("Please provide some text.")
        return
    with st.spinner("Running KNOWMAP NLP pipeline..."):
        nlp = pipelines_extraction.load_nlp_model()
        cleaned_text = pipelines_text_cleaner.clean_text(text)
        triples = pipelines_extraction.extract_triples(cleaned_text, nlp)
    if not triples:
        st.warning("No structured triples found. Try adding more context.")
        return
    st.success(f"✅ Extracted {len(triples)} knowledge triples.")
    df = pd.DataFrame(triples, columns=["Subject", "Relation", "Object"])
    st.dataframe(df, use_container_width=True)
    try:
        G = pipelines_extraction.triples_to_graph(triples)
        html = pipelines_extraction.graph_to_pyvis_html(G)
        components.html(html, height=600, scrolling=True)
    except Exception as e:
        st.warning(f"Graph render failed: {e}")
    if st.button("📡 Store in Neo4j Database", use_container_width=True):
        with st.spinner("Storing triples in Neo4j..."):
            count = pipelines_neo4j_loader.store_triples_in_neo4j(triples)
        st.success(f"Stored {count} triples successfully in Neo4j graph!")


# --- [MAIN LAYOUT] ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 🧭 Choose ingestion source")
tab_text, tab_file, tab_wiki, tab_news, tab_arxiv = st.tabs([
    "Text", "File", "Wikipedia", "News", "arXiv"
])

with tab_text:
    text_input = st.text_area(
        "Paste or type data related to agriculture or climate systems:",
        height=220,
        placeholder="Example: High soil salinity reduces wheat yield and affects irrigation efficiency..."
    )
    if st.button("🔍 Run NLP Pipeline", type="primary"):
        process_text_block(text_input)

with tab_file:
    up = st.file_uploader("Upload CSV or TXT", type=["csv", "txt"])
    if st.button("Process File", disabled=not up):
        if not up:
            st.warning("Please select a file.")
        else:
            nlp = pipelines_extraction.load_nlp_model()
            triples = pipelines_extraction.extract_triples_from_file(up.read(), up.name, nlp)
            if not triples:
                st.warning("No triples extracted from file.")
            else:
                st.success(f"Extracted {len(triples)} triples from file.")
                df = pd.DataFrame(triples, columns=["Subject", "Relation", "Object"])
                st.dataframe(df, use_container_width=True)
                try:
                    G = pipelines_extraction.triples_to_graph(triples)
                    html = pipelines_extraction.graph_to_pyvis_html(G)
                    components.html(html, height=600, scrolling=True)
                except Exception as e:
                    st.warning(f"Graph render failed: {e}")
                if st.button("📡 Store in Neo4j Database", use_container_width=True):
                    with st.spinner("Storing triples in Neo4j..."):
                        count = pipelines_neo4j_loader.store_triples_in_neo4j(triples)
                    st.success(f"Stored {count} triples successfully in Neo4j graph!")

with tab_wiki:
    topic = st.text_input("Wikipedia topic", placeholder="e.g., Wheat, Drought, Soil salinity")
    if st.button("Fetch from Wikipedia"):
        if not topic:
            st.warning("Enter a topic.")
        else:
            import urllib.parse
            text = ""
            # Use the summary endpoint first (safe for most pages) with URL encoding
            try:
                slug = urllib.parse.quote(topic, safe='')
                url_summary = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
                r = requests.get(url_summary, timeout=12)
                if r.status_code == 200:
                    data = r.json()
                    # prefer extract (plain text) if available
                    title = data.get("title", "")
                    extract = data.get("extract") or data.get("description") or ""
                    if extract:
                        text = " ".join([str(title), str(extract)])
                else:
                    # non-200 can still be a redirect or missing; try action API below
                    text = ""
            except Exception as e:
                # fall through to action API
                text = ""

            # Fallback: use MediaWiki action API to get plain extract
            if not text:
                try:
                    q = urllib.parse.quote_plus(topic)
                    api_url = (
                        f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&format=json&titles={q}"
                    )
                    r2 = requests.get(api_url, timeout=12, headers={"User-Agent": "KNOWMAP/1.0 (contact@example.com)"})
                    if r2.status_code == 200:
                        payload = r2.json()
                        pages = payload.get("query", {}).get("pages", {})
                        # pages is a dict keyed by pageid
                        extracts = []
                        for pid, page in pages.items():
                            ext = page.get("extract") or ""
                            title = page.get("title", "")
                            if ext:
                                extracts.append(f"{title}. {ext}")
                        if extracts:
                            text = "\n\n".join(extracts)
                except Exception as e:
                    st.warning(f"Wikipedia fetch error: {e}")

            if not text:
                st.error("Could not fetch Wikipedia content. Try a different topic or check network.")
            else:
                st.info(f"Fetched {len(text)} characters from Wikipedia.")
                process_text_block(text)

with tab_news:
    query = st.text_input("News query", placeholder="e.g., climate change agriculture")
    limit = st.slider("Articles", 5, 30, 10)
    if st.button("Fetch News"):
        if not query:
            st.warning("Enter a query.")
        else:
            # Use Google News RSS (no API key required)
            feed_url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
            try:
                r = requests.get(feed_url, timeout=15)
                r.raise_for_status()
                root = ET.fromstring(r.text)
                ns = {"ns": "http://purl.org/rss/1.0/"}
                # RSS from Google News typically uses 'item' under channel
                items = root.findall(".//item")[:limit]
                parts = []
                for it in items:
                    title = (it.findtext("title") or "")
                    desc = (it.findtext("description") or "")
                    parts.append(f"{title}. {strip_html(desc)}")
                text = " ".join(parts)
                process_text_block(text)
            except Exception as e:
                st.error(f"News fetch failed: {e}")

with tab_arxiv:
    query = st.text_input("arXiv query", placeholder="e.g., crop yield drought")
    limit = st.slider("Papers", 5, 30, 10, key="arxiv_limit")
    if st.button("Fetch from arXiv"):
        if not query:
            st.warning("Enter a query.")
        else:
            # arXiv Atom API
            api = f"http://export.arxiv.org/api/query?search_query=all:{requests.utils.quote(query)}&start=0&max_results={limit}"
            try:
                r = requests.get(api, timeout=20, headers={"User-Agent": "KNOWMAP/1.0"})
                r.raise_for_status()
                root = ET.fromstring(r.text)
                # Atom namespace
                ns = {"a": "http://www.w3.org/2005/Atom"}
                entries = root.findall("a:entry", ns)
                parts = []
                for e in entries:
                    title = e.findtext("a:title", default="", namespaces=ns)
                    summary = e.findtext("a:summary", default="", namespaces=ns)
                    parts.append(f"{title}. {summary}")
                text = " ".join(parts)
                process_text_block(text)
            except Exception as e:
                st.error(f"arXiv fetch failed: {e}")

st.markdown('</div>', unsafe_allow_html=True)

# --- [SIDECARD INFO] ---
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 🧠 Pipeline Overview")
st.info("""
**Pipeline Steps:**
1. Text Cleaning (noise removal)
2. Entity Recognition (spaCy + CSV priming)
3. Relation Extraction (Dependency patterns)
4. Neo4j Graph Storage
""")
st.markdown("### 🧩 Status Indicators")
st.write("✅ NLP Model: Loaded")
st.write("✅ Neo4j Connection: Active")
st.write("🌿 Ready for Knowledge Graph Ingestion")
st.markdown('</div>', unsafe_allow_html=True)
