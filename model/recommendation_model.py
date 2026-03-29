import os
import pickle
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .model_utils import get_model

# --- FIX 1: Use absolute paths for everything ---
base_dir = os.path.dirname(os.path.abspath(__file__))
# Data path (going up one level to root, then into data)
data_path = os.path.join(base_dir, "..", "data", "movies_clean_with_posters.csv")
# Embedding path
embedding_path = os.path.join(base_dir, "..", "data", "movie_embeddings.pkl")

movies = pd.read_csv(data_path)

# Load embedding vectors using the absolute path
with open(embedding_path, "rb") as f:
    embeddings = pickle.load(f)

model = get_model()
user_likes = {}

# --- FIX 2: Prevent Circular Imports ---
# Move imports inside functions if the other file (user_model) also imports this one.
def preference_based_recommend(user_id, movies):
    from user_model import get_liked_movies # Kept inside to prevent crash
    
    liked_movie_ids = get_liked_movies(user_id)
    if not liked_movie_ids:
        return []

    # Logic fix: verify indices exist before slicing
    valid_ids = [i for i in liked_movie_ids if i in movies.index]
    liked_titles = movies.loc[valid_ids]["title"].tolist()
    return hybrid_recommend(liked_titles, top_n=10)

def recommend_manager(user_id, movies):
    from user_model import get_liked_movies # Kept inside

    liked_movies = get_liked_movies(user_id)
    if not liked_movies:
        return cold_start_recommend(top_n=10), "ColdStartAgent"
    else:
        return preference_based_recommend(user_id, movies), "PreferenceAgent"

def hybrid_recommend(favorite_movies, top_n=5):
    if not favorite_movies:
        return []

    sims_total = np.zeros(len(movies))
    for fav in favorite_movies:
        match = movies[movies["title"].str.lower() == fav.lower()]
        if match.empty:
            continue
        idx = match.index[0]
        
        # --- FIX 3: Indexing Safety ---
        # Ensure embeddings index matches DataFrame index
        movie_emb = embeddings[idx].reshape(1, -1)
        sims = cosine_similarity(movie_emb, embeddings)[0]
        
        # Align lengths in case of mismatch
        if len(sims) == len(sims_total):
            sims_total += sims
        else:
            # Fallback if indices shifted
            sims_series = pd.Series(sims, index=movies.index[:len(sims)])
            sims_aligned = sims_series.reindex(movies.index, fill_value=0).values
            sims_total += sims_aligned

    collab_scores = np.zeros(len(movies))
    for user, liked in user_likes.items():
        overlap = set(favorite_movies).intersection(set(liked))
        if overlap:
            for m in liked:
                match = movies[movies["title"].str.lower() == m.lower()]
                if not match.empty:
                    idx = match.index[0]
                    collab_scores[idx] += 1 

    final_scores = sims_total + collab_scores

    # Clean exclusion logic
    for fav in favorite_movies:
        match = movies[movies["title"].str.lower() == fav.lower()]
        if not match.empty:
            final_scores[match.index[0]] = -1 

    top_idx = np.argsort(final_scores)[::-1][:top_n]
    return movies.iloc[top_idx].to_dict(orient="records")

def top_rated_bayesian(top_n=50, m=50):
    if "rating" not in movies.columns or "num_ratings" not in movies.columns:
        return movies.head(top_n).to_dict(orient="records")
    
    C = movies["rating"].mean()
    # Calculate score without modifying original df permanently to avoid warnings
    v = movies["num_ratings"]
    R = movies["rating"]
    score = (v / (v + m) * R) + (m / (v + m) * C)
    
    top_indices = score.sort_values(ascending=False).head(top_n).index
    return movies.loc[top_indices].to_dict(orient="records")