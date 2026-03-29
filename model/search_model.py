import os
import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .model_utils import get_model

# Get the absolute path to the data folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBEDDINGS_PATH = os.path.join(BASE_DIR, 'data', 'movie_embeddings.pkl')

def semantic_search(query, movies, top_n=50):
    """Return top-N semantically similar movies based on query."""
    if not query or not query.strip():
        return []
    
    # 1. Safety Check: Verify if the file exists before opening
    if not os.path.exists(EMBEDDINGS_PATH):
        print(f"CRITICAL ERROR: Search file not found at {EMBEDDINGS_PATH}")
        return []

    # 2. Load precomputed embeddings using the absolute path
    try:
        with open(EMBEDDINGS_PATH, "rb") as f:
            embeddings = pickle.load(f)
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        return []
    
    # Encode user query
    model = get_model()
    query_emb = model.encode([query])
    
    # Compute similarity
    sims = cosine_similarity(query_emb, embeddings)[0]
    
    # Top N matches
    top_idx = np.argsort(sims)[::-1][:top_n]
    
    # Return movie rows as dictionaries
    results = movies.iloc[top_idx][["title", "overview", "poster_url"]].to_dict(orient="records")
    for movie in results:
        if not isinstance(movie.get("overview"), str):
            movie["overview"] = "No description available"
            
    return results