import pickle
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .model_utils import get_model

def semantic_search(query, movies, top_n=50):
    """Return top-N semantically similar movies based on query."""
    if not query or not query.strip():
        return []
    
    # Load precomputed embeddings
    with open("data/movie_embeddings.pkl", "rb") as f:
        embeddings = pickle.load(f)
    
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
