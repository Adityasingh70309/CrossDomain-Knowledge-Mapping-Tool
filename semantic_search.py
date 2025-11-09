import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from math import sqrt
import plotly.graph_objects as go
import re
from collections import defaultdict

# Set page configuration
st.set_page_config(
    page_title="Agri-Climate Semantic Search",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #2E8B57, #3CB371, #20B2AA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #555;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #2E8B57;
    }
    .status-item {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid #e0e0e0;
    }
    .status-value {
        color: #2E8B57;
        font-weight: bold;
    }
    .stButton button {
        background-color: #2E8B57;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #3CB371;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Agriculture-Climate Knowledge Base
KNOWLEDGE_BASE = {
    # Agriculture concepts
    "sustainable agriculture": {
        "description": "Farming practices that meet current needs without compromising future generations",
        "group": "agriculture",
        "related": ["climate change", "carbon sequestration", "soil health", "crop rotation", "organic farming"]
    },
    "crop rotation": {
        "description": "Practice of growing different crops sequentially on the same land",
        "group": "agriculture", 
        "related": ["soil health", "sustainable agriculture", "biodiversity"]
    },
    "soil health": {
        "description": "Capacity of soil to function as a vital living ecosystem",
        "group": "agriculture",
        "related": ["sustainable agriculture", "carbon sequestration", "water conservation", "biodiversity"]
    },
    "organic farming": {
        "description": "Agricultural system without synthetic pesticides and fertilizers",
        "group": "agriculture",
        "related": ["sustainable agriculture", "biodiversity", "soil health"]
    },
    "precision agriculture": {
        "description": "Farming management concept using technology to optimize returns",
        "group": "technology",
        "related": ["sustainable agriculture", "water conservation", "climate resilience"]
    },
    "food security": {
        "description": "Availability and access to sufficient, safe, nutritious food",
        "group": "agriculture", 
        "related": ["climate change", "sustainable agriculture", "biodiversity"]
    },
    
    # Climate concepts
    "climate change": {
        "description": "Long-term shifts in temperatures and weather patterns",
        "group": "climate",
        "related": ["sustainable agriculture", "greenhouse gases", "food security", "drought resistance"]
    },
    "greenhouse gases": {
        "description": "Gases that trap heat in the atmosphere",
        "group": "climate",
        "related": ["climate change", "carbon sequestration", "renewable energy"]
    },
    "climate resilience": {
        "description": "Capacity to anticipate and respond to climate change impacts", 
        "group": "climate",
        "related": ["sustainable agriculture", "drought resistance", "water conservation"]
    },
    
    # Environment concepts
    "carbon sequestration": {
        "description": "Process of capturing and storing atmospheric carbon dioxide",
        "group": "environment",
        "related": ["sustainable agriculture", "soil health", "climate change", "agroforestry"]
    },
    "water conservation": {
        "description": "Preservation and efficient use of water resources",
        "group": "environment",
        "related": ["sustainable agriculture", "soil health", "drought resistance"]
    },
    "biodiversity": {
        "description": "Variety of life in a particular habitat or ecosystem",
        "group": "environment", 
        "related": ["sustainable agriculture", "soil health", "organic farming"]
    },
    "renewable energy": {
        "description": "Energy from sources that are naturally replenishing",
        "group": "environment",
        "related": ["sustainable agriculture", "climate change", "greenhouse gases"]
    },
    
    # Additional concepts
    "drought resistance": {
        "description": "Ability of crops to withstand dry conditions",
        "group": "agriculture",
        "related": ["climate change", "water conservation", "climate resilience"]
    },
    "agroforestry": {
        "description": "Integration of trees and shrubs into farming systems",
        "group": "agriculture", 
        "related": ["carbon sequestration", "biodiversity", "sustainable agriculture"]
    },
    "regenerative agriculture": {
        "description": "Farming principles that rehabilitate the entire ecosystem",
        "group": "agriculture",
        "related": ["sustainable agriculture", "soil health", "carbon sequestration"]
    },
    "climate smart agriculture": {
        "description": "Agricultural practices that address climate change challenges",
        "group": "agriculture",
        "related": ["climate change", "sustainable agriculture", "climate resilience"]
    }
}

def expand_query_with_synonyms(query):
    """Expand search query with related terms"""
    synonyms = {
        "sustainable": ["eco-friendly", "green", "environmental"],
        "farming": ["agriculture", "cultivation", "agronomy"],
        "climate": ["weather", "atmosphere", "environmental"],
        "carbon": ["co2", "emissions", "greenhouse"],
        "water": ["irrigation", "hydric", "aquatic"],
        "soil": ["land", "earth", "ground"],
        "energy": ["power", "electricity", "renewables"]
    }
    
    expanded_terms = [query.lower()]
    for term, syn_list in synonyms.items():
        if term in query.lower():
            for syn in syn_list:
                expanded_terms.append(query.lower().replace(term, syn))
    
    return expanded_terms

def generate_dynamic_graph(search_query, selected_domain):
    """Generate a knowledge graph dynamically based on search query"""
    G = nx.Graph()
    
    # Expand search query
    search_terms = expand_query_with_synonyms(search_query)
    
    # Find matching concepts
    matching_concepts = []
    for concept, data in KNOWLEDGE_BASE.items():
        # Check if concept matches search or domain
        concept_matches_search = any(term in concept.lower() for term in search_terms) or any(term in data['description'].lower() for term in search_terms)
        domain_matches = (selected_domain == "All" or data['group'] == selected_domain.lower())
        
        if concept_matches_search and domain_matches:
            matching_concepts.append(concept)
    
    # Add matching concepts and their relationships
    added_concepts = set()
    
    def add_concept_with_relations(concept, depth=0, max_depth=2):
        if depth > max_depth or concept in added_concepts:
            return
        
        if concept in KNOWLEDGE_BASE:
            data = KNOWLEDGE_BASE[concept]
            G.add_node(concept, name=concept.title(), description=data['description'], group=data['group'])
            added_concepts.add(concept)
            
            # Add related concepts
            for related_concept in data['related']:
                if related_concept in KNOWLEDGE_BASE:
                    related_data = KNOWLEDGE_BASE[related_concept]
                    # Only add if it matches domain or is closely related to search
                    domain_ok = (selected_domain == "All" or related_data['group'] == selected_domain.lower())
                    search_related = any(term in related_concept.lower() for term in search_terms) or depth < 1
                    
                    if domain_ok and search_related:
                        G.add_node(related_concept, name=related_concept.title(), 
                                 description=related_data['description'], group=related_data['group'])
                        G.add_edge(concept, related_concept, weight=3 - depth)
                        add_concept_with_relations(related_concept, depth + 1, max_depth)
    
    # Start with matching concepts
    for concept in matching_concepts:
        add_concept_with_relations(concept)
    
    # If no matches found, show some default concepts
    if len(G.nodes()) == 0:
        default_concepts = ["sustainable agriculture", "climate change", "carbon sequestration"]
        for concept in default_concepts:
            if concept in KNOWLEDGE_BASE:
                data = KNOWLEDGE_BASE[concept]
                G.add_node(concept, name=concept.title(), description=data['description'], group=data['group'])
    
    return G

def create_enhanced_plotly_graph(G, title, search_query):
    """Create an enhanced interactive Plotly graph with white background and readable text"""
    if len(G.nodes()) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No matching concepts found. Try a different search term.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=20, color='#2E8B57')),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=700
        )
        return fig
    
    # Use different layout algorithm for better spacing
    if len(G.nodes()) <= 10:
        pos = nx.circular_layout(G)
    else:
        pos = nx.spring_layout(G, k=3, iterations=150, scale=2.5)
    
    # Define enhanced color mapping
    color_map = {
        'agriculture': '#2E8B57',  # Green
        'climate': '#4682B4',      # Steel Blue
        'environment': '#20B2AA',  # Light Sea Green
        'technology': '#DA70D6'    # Orchid
    }
    
    # Text color mapping for optimal contrast on white background
    text_color_map = {
        'agriculture': 'white',      # White on green
        'climate': 'white',          # White on blue  
        'environment': 'white',      # White on teal
        'technology': 'white'        # White on purple
    }
    
    # Create edge traces
    edge_x = []
    edge_y = []
    edge_weights = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_weights.append(G.edges[edge].get('weight', 1))
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2.5, color='#666666'),  # Dark gray edges for white background
        hoverinfo='none',
        mode='lines'
    )
    
    # Create node traces with optimized text display
    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_names = []
    text_colors = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_data = G.nodes[node]
        
        # Enhanced hover text
        hover_text = f"<b>{node_data['name']}</b><br>{node_data['description']}<br>Domain: {node_data['group'].title()}"
        node_text.append(hover_text)
        
        node_color.append(color_map.get(node_data['group'], '#999999'))
        text_colors.append(text_color_map.get(node_data['group'], 'white'))
        
        # Optimized node sizes for text fitting
        concept_name = node_data['name']
        text_length = len(concept_name)
        
        base_size = 40
        text_adjustment = min(text_length * 1.5, 20)
        degree = G.degree(node)
        degree_adjustment = degree * 6
        
        node_size.append(base_size + text_adjustment + degree_adjustment)
        
        # Shorten long names for better display
        if len(concept_name) > 20:
            words = concept_name.split()
            if len(words) >= 2:
                mid = len(words) // 2
                display_name = ' '.join(words[:mid]) + '<br>' + ' '.join(words[mid:])
            else:
                if len(concept_name) > 15:
                    display_name = concept_name[:15] + '<br>' + concept_name[15:]
                else:
                    display_name = concept_name
        else:
            display_name = concept_name
            
        node_names.append(display_name)
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_names,
        textposition="middle center",
        textfont=dict(
            color=text_colors, 
            size=11,
            family="Arial, sans-serif",
            weight="bold"
        ),
        marker=dict(
            color=node_color,
            size=node_size,
            line=dict(width=3, color='white'),
            opacity=0.95
        ),
        hovertemplate='<b>%{text}</b><br><br>%{customdata}<extra></extra>',
        customdata=node_text
    )
    
    # Create the figure with WHITE background and proper text colors
    fig = go.Figure(data=[edge_trace, node_trace],
                   layout=go.Layout(
                       title=dict(
                           text=title,
                           x=0.5,
                           font=dict(size=22, color='#2E8B57', family="Arial")
                       ),
                       showlegend=False,
                       hovermode='closest',
                       margin=dict(b=40, l=40, r=40, t=80),
                       annotations=[dict(
                           text="💡 Click and drag to explore • Scroll to zoom • Hover for details",
                           showarrow=False,
                           xref="paper", yref="paper",
                           x=0.5, y=-0.08,
                           xanchor='center',
                           font=dict(color='gray', size=11)
                       )],
                       xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                       plot_bgcolor='white',  # White background
                       paper_bgcolor='white',  # White background
                       height=750,
                       width=None
                   ))
    
    return fig

def main():
    # Header
    st.markdown('<div class="main-header">Dynamic Semantic Search & Knowledge Graph</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Agriculture & Climate/Environment Relationships</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'selected_domain' not in st.session_state:
        st.session_state.selected_domain = "All"
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'search_suggestion' not in st.session_state:
        st.session_state.search_suggestion = ""
    
    # Main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Search section
        st.subheader("🔍 Dynamic Semantic Search")
        st.write("Enter any agriculture or climate concept to generate a knowledge graph...")
        
        # Use the search suggestion if one was clicked, otherwise use empty string
        default_search = st.session_state.search_suggestion if st.session_state.search_suggestion else ""
        
        search_query = st.text_input(
            "Enter a concept (e.g., sustainable farming, carbon, water conservation)", 
            placeholder="Type your search term here...",
            value=default_search,
            key="search_input"
        )
        
        # Domain selection
        st.write("**Filter by Domain:**")
        domains = ["All", "Agriculture", "Climate", "Environment", "Technology"]
        
        domain_cols = st.columns(5)
        for i, domain in enumerate(domains):
            with domain_cols[i]:
                if st.button(domain, key=f"domain_{domain}"):
                    st.session_state.selected_domain = domain
        
        # Show active filters
        current_search = search_query if search_query else 'Enter a term to start'
        st.info(f"**Active Filters:** Search: '{current_search}' | Domain: {st.session_state.selected_domain}")
        
        # Generate graph based on search
        if search_query:
            with st.spinner("Generating dynamic knowledge graph..."):
                dynamic_G = generate_dynamic_graph(search_query, st.session_state.selected_domain)
                
                # Add to search history
                if search_query not in st.session_state.search_history:
                    st.session_state.search_history.append(search_query)
        else:
            # Show default graph
            dynamic_G = generate_dynamic_graph("sustainable agriculture", "All")
        
        # Create and display enhanced graph
        graph_title = f"Dynamic Knowledge Graph: {search_query if search_query else 'Agriculture-Climate'}"
        fig = create_enhanced_plotly_graph(dynamic_G, graph_title, search_query)
        st.plotly_chart(fig, use_container_width=True)
        
        # Subgraph info
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f0f8f0, #e0f0e0); padding: 20px; border-radius: 15px; border-left: 6px solid #2E8B57; margin-top: 20px;'>
            <h4 style='color: #2E8B57; margin-bottom: 10px;'>📊 Current Subgraph Analysis</h4>
            <p style='margin: 5px 0;'><strong>Search Context:</strong> "{search_query if search_query else 'General Agriculture-Climate'}"</p>
            <p style='margin: 5px 0;'><strong>Domain Focus:</strong> {st.session_state.selected_domain}</p>
            <p style='margin: 5px 0;'><strong>Concepts Discovered:</strong> {len(dynamic_G.nodes())} nodes, {len(dynamic_G.edges())} relationships</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Features section
        st.subheader("🌱 Enhanced Features")
        
        features = [
            "Dynamic Graph Generation",
            "White Background Graph", 
            "High Contrast Text",
            "Smart Text Wrapping",
            "Interactive Exploration",
            "Real-time Relationship Mapping"
        ]
        
        for feature in features:
            st.markdown(f"""
            <div class="feature-card">
                🚀 {feature}
            </div>
            """, unsafe_allow_html=True)
        
        # Search suggestions
        st.subheader("💡 Try These Searches")
        suggestions = [
            "sustainable farming",
            "carbon sequestration", 
            "water conservation",
            "climate resilience",
            "organic agriculture",
            "renewable energy"
        ]
        
        for suggestion in suggestions:
            if st.button(f"🔍 {suggestion}", key=f"sugg_{suggestion}"):
                # Store the suggestion in session state and rerun
                st.session_state.search_suggestion = suggestion
                st.rerun()
        
        # Statistics
        st.subheader("📈 Graph Insights")
        
        col_met1, col_met2 = st.columns(2)
        with col_met1:
            st.metric("Concepts", len(dynamic_G.nodes()), 
                     delta=f"+{len(dynamic_G.edges())} rels" if dynamic_G.edges() else "")
        with col_met2:
            avg_degree = sum(dict(dynamic_G.degree()).values()) / len(dynamic_G.nodes()) if dynamic_G.nodes() else 0
            st.metric("Connectivity", f"{avg_degree:.1f}", delta="avg links")
        
        # Domain distribution
        if dynamic_G.nodes():
            domain_counts = {}
            for node in dynamic_G.nodes():
                group = dynamic_G.nodes[node].get('group', 'unknown')
                domain_counts[group] = domain_counts.get(group, 0) + 1
            
            st.write("**Domain Distribution:**")
            for domain, count in domain_counts.items():
                st.write(f"• {domain.title()}: {count} concepts")
        
        # Recent searches
        if st.session_state.search_history:
            st.subheader("🕐 Recent Searches")
            for i, past_search in enumerate(reversed(st.session_state.search_history[-5:])):
                st.write(f"{i+1}. {past_search}")

if __name__ == "__main__":
    main()