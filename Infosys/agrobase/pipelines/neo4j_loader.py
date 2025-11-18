import streamlit as st
import database
from py2neo import Node, Relationship

def store_triples_in_neo4j(triples: list):
    graph = database.get_neo4j_graph()
    if not graph:
        st.error("Neo4j connection failed.")
        return 0

    tx = graph.begin()
    count = 0
    try:
        for subj, rel, obj in triples:
            node_a = Node("Entity", name=subj)
            tx.merge(node_a, "Entity", "name")
            node_b = Node("Entity", name=obj)
            tx.merge(node_b, "Entity", "name")
            rel_type = rel.upper().replace(" ", "_")
            relationship = Relationship(node_a, rel_type, node_b)
            tx.merge(relationship)
            count += 1
        tx.commit()
        st.success(f"✅ Stored {count} triples in Neo4j.")
        return count
    except Exception as e:
        st.error(f"Error loading data to Neo4j: {e}")
        tx.rollback()
        return 0
