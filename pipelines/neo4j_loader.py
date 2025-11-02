from py2neo import Node, Relationship
from database import get_neo4j_connection # Import from our root database.py file

def store_triples_in_neo4j(triples):
    """
    Stores a list of (Subject, Relation, Object) triples in Neo4j.
    Uses MERGE to avoid creating duplicate nodes and relationships.
    """
    graph = get_neo4j_connection()
    if not graph:
        print("❌ Cannot store triples. No Neo4j connection.")
        return
    
    print(f"Storing {len(triples)} triples in Neo4j...")
    for subj, rel, obj in triples:
        
        # 1. Create or find the Subject node
        subj_node = Node("Entity", name=subj)
        graph.merge(subj_node, "Entity", "name")
        
        # 2. Create or find the Object node
        obj_node = Node("Entity", name=obj)
        graph.merge(obj_node, "Entity", "name")
        
        # 3. Create the Relationship
        # Format the relation type to be valid for Neo4j (UPPERCASE, no spaces)
        rel_type = rel.upper().replace(" ", "_")
        rel_edge = Relationship(subj_node, rel_type, obj_node)
        graph.merge(rel_edge)
        
    print("✅ Storage complete.")