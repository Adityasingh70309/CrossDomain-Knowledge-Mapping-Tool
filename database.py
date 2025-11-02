import streamlit as st
from py2neo import Graph
import config  # <-- This is the absolute import fix

# Use Streamlit's cache to only connect to Neo4j once
@st.cache_resource
def get_neo4j_connection():
    """
    Establishes and returns a connection to the Neo4j database.
    Uses st.cache_resource to maintain a singleton connection.
    """
    try:
        graph = Graph(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
        # Test the connection
        graph.run("RETURN 1")
        print("✅ Successfully connected to Neo4j.")
        return graph
    except Exception as e:
        # We also clear the cache if the connection fails
        st.cache_resource.clear() 
        st.error(f"Failed to connect to Neo4j. Is it running? Error: {e}")
        return None

# A simple function to clear the graph for demos
def clear_database():
    """
    Clears all nodes and relationships from the Neo4j database.
    """
    graph = get_neo4j_connection()
    if graph:
        try:
            graph.delete_all()
            print("🗑️ Cleared all nodes and relationships from Neo4j.")
        except Exception as e:
            st.error(f"Failed to clear database. Error: {e}")
    else:
        st.error("Cannot clear database. No Neo4j connection.")

