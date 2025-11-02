import spacy
import streamlit as st

@st.cache_resource
def load_nlp_model():
    """
    Loads the spaCy Transformer model.
    Uses st.cache_resource to only load this large model once.
    """
    print("Loading NLP model (en_core_web_trf)...")
    try:
        nlp = spacy.load("en_core_web_trf")
        print("✅ NLP model loaded.")
        return nlp
    except OSError:
        print("❌ Model 'en_core_web_trf' not found.")
        st.error("Model 'en_core_web_trf' not found. Please run: python -m spacy download en_core_web_trf")
        return None

def extract_triples_from_doc(doc):
    """
    Extracts (Subject, Relation, Object) triples from a spaCy Doc.
    
    --- THIS IS THE UPDATED LOGIC ---
    This version is smarter, capturing the full noun phrases for 
    subjects and objects, not just the head token.
    """
    triples = []

    # 1. Merge entities into single tokens for easier processing
    # (e.g., "Albert Einstein" becomes one token)
    with doc.retokenize() as retokenizer:
        for ent in doc.ents:
            retokenizer.merge(ent)
            
    # 2. Iterate through sentences
    for sent in doc.sents:
        for token in sent:
            # 3. Check if the token is a verb (a potential relation)
            if token.pos_ == "VERB":
                relation = token.lemma_  # Get the base form (e.g., "working" -> "work")
                
                subject = None
                obj = None
                
                # 4. Find the subject (nsubj)
                for child in token.lefts:
                    if child.dep_ == "nsubj":
                        subject = child
                        break
                
                # 5. Find the object (dobj or pobj)
                for child in token.rights:
                    if child.dep_ in ("dobj", "pobj"):
                        obj = child
                        break
                
                # 6. If we found a full triple...
                if subject and obj:
                    
                    # --- THE FIX ---
                    # Instead of just `subject.text` or `obj.text`, we find the
                    # full span of the noun phrase by getting its edges.
                    
                    # Get the full subject phrase
                    subj_span = doc[subject.left_edge.i : subject.right_edge.i + 1]
                    
                    # Get the full object phrase
                    obj_span = doc[obj.left_edge.i : obj.right_edge.i + 1]
                    
                    triples.append((subj_span.text, relation, obj_span.text))
                    
    return triples
