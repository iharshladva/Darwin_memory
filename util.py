from sentence_transformers import SentenceTransformer
import re, numpy as np


_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text: str):
    """Return a normalized vector embedding for the input text."""
    vec = _model.encode([text])[0]
    return vec / np.linalg.norm(vec)

def extract_keywords(text: str):
    """Simple lowercase token extraction for keyword indexing."""
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    uniq = []
    for w in words:
        if len(w) > 2 and w not in uniq:
            uniq.append(w)
    return uniq[:8]
