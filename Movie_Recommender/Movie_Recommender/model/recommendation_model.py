import pickle
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .model_utils import get_model

# Load cleaned movie data
movies = pd.read_csv("data/movies_clean_with_posters.csv")

# Load embedding vectors
with open("data/movie_embeddings.pkl", "rb") as f:
    embeddings = pickle.load(f)

# Encoder model for user preferences (using shared cached model)
model = get_model()

# Simulated user likes dictionary (later can be a DB)
# e.g., {'user1': ['Tangled', 'Inception'], 'user2': ['Avatar']}
user_likes = {}

def cold_start_recommend(top_n=10):
    """
    Agent 1: Cold-start agent
    Used when user has no likes.
    """
    return top_rated_bayesian(top_n=top_n)

def preference_based_recommend(user_id, movies):
    """
    Agent 2: Preference-based agent
    """
    from user_model import get_liked_movies
    
    liked_movie_ids = get_liked_movies(user_id)
    if not liked_movie_ids:
        return []

    liked_titles = movies.loc[liked_movie_ids]["title"].tolist()
    return hybrid_recommend(liked_titles, top_n=10)

def recommend_manager(user_id, movies):
    """
    Multi-agent manager:
    Chooses which agent to call
    """
    from user_model import get_liked_movies

    liked_movies = get_liked_movies(user_id)

    if not liked_movies:
        # Cold start case
        return cold_start_recommend(top_n=10), "ColdStartAgent"
    else:
        # Normal case
        return preference_based_recommend(user_id, movies), "PreferenceAgent"


def hybrid_recommend(favorite_movies, top_n=5):
    """
    Hybrid recommendation:
    - Collaborative filtering for overlapping likes
    - Semantic similarity based on movie overviews
    """
    if not favorite_movies:
        return []

    # -------- Semantic similarity --------
    sims_total = np.zeros(len(movies))
    for fav in favorite_movies:
        match = movies[movies["title"].str.lower() == fav.lower()]
        if match.empty:
            continue
        idx = match.index[0]
        movie_emb = embeddings[idx].reshape(1, -1)
        sims = cosine_similarity(movie_emb, embeddings)[0]
        sims_series = pd.Series(sims, index=movies.index[:len(sims)])
        sims_aligned = sims_series.reindex(movies.index, fill_value=0).values
        sims_total += sims_aligned

    # -------- Collaborative filtering --------
    # Find movies liked by other users who liked the same favorites
    collab_scores = np.zeros(len(movies))
    for user, liked in user_likes.items():
        overlap = set(favorite_movies).intersection(set(liked))
        if overlap:
            for m in liked:
                match = movies[movies["title"].str.lower() == m.lower()]
                if not match.empty:
                    idx = match.index[0]
                    collab_scores[idx] += 1  # simple count score

    # Combine semantic + collaborative scores
    final_scores = sims_total + collab_scores

    # Pick top-N excluding already liked
    already_liked_idx = [movies[movies["title"].str.lower() == fav.lower()].index[0] 
                         for fav in favorite_movies if not movies[movies["title"].str.lower() == fav.lower()].empty]
    for idx in already_liked_idx:
        final_scores[idx] = -1  # exclude

    top_idx = np.argsort(final_scores)[::-1][:top_n]
    return movies.iloc[top_idx].to_dict(orient="records")

def top_rated_bayesian(top_n=50, m=50):
    """
    Returns top N movies using Bayesian average rating.
    Requires movies dataframe to have 'rating' and 'num_ratings' columns.
    """
    if "rating" not in movies.columns or "num_ratings" not in movies.columns:
        # fallback: just return first top_n movies
        return movies.head(top_n).to_dict(orient="records")
    
    C = movies["rating"].mean()  # global average rating
    movies["bayesian_score"] = (
        (movies["num_ratings"] / (movies["num_ratings"] + m)) * movies["rating"] +
        (m / (movies["num_ratings"] + m)) * C
    )
    top_movies = movies.sort_values(by="bayesian_score", ascending=False).head(top_n)
    return top_movies.to_dict(orient="records")

