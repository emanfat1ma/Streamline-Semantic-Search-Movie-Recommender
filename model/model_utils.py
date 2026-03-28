from sentence_transformers import SentenceTransformer
import os

MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "sbert_model")

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(
            MODEL_NAME,
            cache_folder=MODEL_PATH
        )
    return _model

