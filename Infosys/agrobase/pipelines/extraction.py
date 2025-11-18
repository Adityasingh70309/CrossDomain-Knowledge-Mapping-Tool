import spacy
import streamlit as st
from spacy.language import Language
from spacy.tokens import Doc, Token
from spacy.matcher import Matcher, DependencyMatcher
import pandas as pd
import os
import logging
import networkx as nx
from typing import Iterable, Tuple, List, Optional, Dict, Set
from pyvis.network import Network
import io
import csv

TRAINING_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'agri_climate_relations_1000.csv')

ENTITY_TYPE_LOOKUP: Dict[str, str] = {}
RELATION_LEMMAS: Set[str] = set()


def _load_training_csv(path: str) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        logging.warning(f"Failed to read training CSV: {e}")
        return None


def _prime_lookups_from_csv(df: pd.DataFrame):
    global ENTITY_TYPE_LOOKUP, RELATION_LEMMAS
    try:
        ENTITY_TYPE_LOOKUP.clear()
        RELATION_LEMMAS.clear()
        nlp_tmp = spacy.blank("en")
        lemmatizer = nlp_tmp.get_pipe("lemmatizer") if "lemmatizer" in nlp_tmp.pipe_names else None
        for _, row in df.iterrows():
            s = str(row.get("source", "")).strip()
            t = str(row.get("target", "")).strip()
            stype = str(row.get("source_type", "")).strip()
            ttype = str(row.get("target_type", "")).strip()
            if s and stype:
                ENTITY_TYPE_LOOKUP[s] = stype
            if t and ttype:
                ENTITY_TYPE_LOOKUP[t] = ttype
            rel = str(row.get("relation", "")).strip()
            if rel:
                # simple lemma: lower and split first token; robust enough here
                RELATION_LEMMAS.add(rel.lower())
    except Exception as e:
        logging.warning(f"Could not build lookups from CSV: {e}")


@st.cache_resource
def load_nlp_model() -> Optional[Language]:
    try:
        nlp = spacy.load("en_core_web_sm")
        logging.info("✅ spaCy model loaded.")
    except OSError:
        st.error("spaCy model not found. Install using:")
        st.code("pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1.tar.gz")
        return None

    # Load custom dictionaries from CSV
    df = _load_training_csv(TRAINING_DATA_PATH)
    if df is not None:
        _prime_lookups_from_csv(df)
        try:
            entities = {}
            for _, row in df.iterrows():
                if pd.notna(row.get('source')) and pd.notna(row.get('source_type')):
                    entities[str(row['source']).strip()] = str(row['source_type']).strip()
                if pd.notna(row.get('target')) and pd.notna(row.get('target_type')):
                    entities[str(row['target']).strip()] = str(row['target_type']).strip()

            patterns = [{"label": label.upper(), "pattern": ent} for ent, label in entities.items()]
            if "entity_ruler" not in nlp.pipe_names:
                ruler = nlp.add_pipe("entity_ruler", before="ner")
            else:
                ruler = nlp.get_pipe("entity_ruler")
            ruler.add_patterns(patterns)
            logging.info("✅ EntityRuler primed from CSV entities.")
        except Exception as e:
            st.warning(f"Entity data not loaded: {e}")

    return nlp


def _expand_to_chunk(token: Token) -> str:
    doc = token.doc
    # Prefer the noun chunk containing the token
    for chunk in doc.noun_chunks:
        if token.i >= chunk.start and token.i < chunk.end:
            return chunk.text
    # fallback: subtree span
    subtree = list(token.subtree)
    if subtree:
        return doc[subtree[0].i:subtree[-1].i+1].text
    return token.text


def extract_triples_from_doc(doc: Doc) -> List[Tuple[str, str, str]]:
    triples: List[Tuple[str, str, str]] = []

    # 1) Dependency-based SVO
    dep_matcher = DependencyMatcher(doc.vocab)
    pattern_svo = [
        {"RIGHT_ID": "verb", "RIGHT_ATTRS": {"POS": {"IN": ["VERB", "AUX"]}}},
        {"LEFT_ID": "verb", "REL_OP": ">", "RIGHT_ID": "subj", "RIGHT_ATTRS": {"DEP": {"IN": ["nsubj", "nsubjpass"]}}},
        {"LEFT_ID": "verb", "REL_OP": ">", "RIGHT_ID": "obj", "RIGHT_ATTRS": {"DEP": {"IN": ["dobj", "pobj", "attr", "dative", "oprd"]}}},
    ]
    dep_matcher.add("SVO", [pattern_svo])
    for match_id, token_ids in dep_matcher(doc):
        verb = doc[token_ids[0]]
        subj = doc[token_ids[1]]
        obj = doc[token_ids[2]]
        rel = verb.lemma_.lower()
        # If we have learned relation lemmas, prefer those; otherwise keep all
        if RELATION_LEMMAS and rel not in RELATION_LEMMAS:
            pass  # not filtered yet; we will still include but lower priority
        triples.append((_expand_to_chunk(subj), rel, _expand_to_chunk(obj)))

    # 2) Pattern-based fallback with Matcher (prepositional relations etc.)
    matcher = Matcher(doc.vocab)
    pattern1 = [{"DEP": "nsubj"}, {"POS": {"IN": ["VERB", "AUX"]}}, {"DEP": {"IN": ["dobj", "pobj", "attr"]}}]
    pattern2 = [{"DEP": "nsubj"}, {"POS": {"IN": ["VERB", "AUX"]}}, {"LOWER": {"IN": ["to", "with", "on", "in", "by"]}}, {"DEP": "pobj"}]
    pattern3 = [{"DEP": "nsubj"}, {"LOWER": {"IN": ["is", "are", "was", "were"]}}, {"DEP": "attr"}]
    matcher.add("SVO_FALLBACK", [pattern1, pattern2, pattern3])
    for _, start, end in matcher(doc):
        span = doc[start:end]
        subj_tok, verb_tok, obj_tok = None, None, None
        for token in span:
            if token.dep_ == "nsubj" and subj_tok is None:
                subj_tok = token
            elif token.pos_ in ("VERB", "AUX") and verb_tok is None:
                verb_tok = token
            elif token.dep_ in ("dobj", "pobj", "attr") and obj_tok is None:
                obj_tok = token
        if subj_tok and verb_tok and obj_tok:
            rel = verb_tok.lemma_.lower()
            triples.append((_expand_to_chunk(subj_tok), rel, _expand_to_chunk(obj_tok)))

    # Deduplicate
    uniq = list({(s.strip(), r.strip(), o.strip()) for (s, r, o) in triples if s and r and o})
    return uniq


def extract_triples(text_or_doc: Iterable[str] | str | Doc, nlp: Optional[Language] = None) -> List[Tuple[str, str, str]]:
    if isinstance(text_or_doc, Doc):
        return extract_triples_from_doc(text_or_doc)
    if nlp is None:
        nlp = load_nlp_model()
    if nlp is None:
        return []
    if isinstance(text_or_doc, str):
        doc = nlp(text_or_doc)
        return extract_triples_from_doc(doc)
    # Iterable of sentences/lines
    out: List[Tuple[str, str, str]] = []
    for t in text_or_doc:
        if not t:
            continue
        doc = nlp(str(t))
        out.extend(extract_triples_from_doc(doc))
    return list({t for t in out})


def triples_to_graph(triples: List[Tuple[str, str, str]]) -> nx.Graph:
    G = nx.Graph()
    for s, r, o in triples:
        s_type = ENTITY_TYPE_LOOKUP.get(s, "Entity")
        o_type = ENTITY_TYPE_LOOKUP.get(o, "Entity")
        if not G.has_node(s):
            G.add_node(s, label=s, type=s_type)
        if not G.has_node(o):
            G.add_node(o, label=o, type=o_type)
        G.add_edge(s, o, relation=r)
    return G


def graph_to_pyvis_html(G: nx.Graph, height: str = "650px", width: str = "100%") -> str:
    net = Network(height=height, width=width, bgcolor="#071126", font_color="#E6EEF3")
    net.force_atlas_2based()
    for n, d in G.nodes(data=True):
        ntype = d.get("type", "Entity")
        net.add_node(n, label=d.get("label", n), title=f"{n} — {ntype}", value=2)
    for a, b, d in G.edges(data=True):
        net.add_edge(a, b, title=d.get("relation", ""))
    return net.generate_html()


def extract_triples_from_file(file_bytes: bytes, filename: str, nlp: Optional[Language] = None) -> List[Tuple[str, str, str]]:
    if nlp is None:
        nlp = load_nlp_model()
    if nlp is None:
        return []
    name = filename.lower()
    text = ""
    try:
        if name.endswith(".csv"):
            # Decode to text and parse CSV; concatenate cells
            s = file_bytes.decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(s))
            rows = [" ".join(r) for r in reader]
            text = " ".join(rows)
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        text = str(file_bytes)
    return extract_triples(text, nlp)


__all__ = [
    "load_nlp_model",
    "extract_triples_from_doc",
    "extract_triples",
    "triples_to_graph",
    "graph_to_pyvis_html",
    "extract_triples_from_file",
]
