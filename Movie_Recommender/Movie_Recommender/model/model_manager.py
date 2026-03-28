# model_manager.py

import pandas as pd
# Import the specialized agents (functions)
from .search_model import semantic_search
from .recommendation_model import hybrid_recommend
from .user_model import get_liked_movies # To check user history

# Global Data (will be passed from app.py)
# NOTE: The 'movies' DataFrame should be passed to the manager function 
# from app.py to avoid redundant loading.

# --- Heuristic Rule Engine ---
# Updated decide_agent function

def decide_agent(query, user_id, movies):
    """
    Decides whether to perform a Search (Semantic or Item-to-Item), 
    provide Recommendations (Hybrid/Personalized), or return Top Rated.
    """
    import numpy as np # Needed for numpy operations if not imported globally
    from .search_model import semantic_search
    from .recommendation_model import hybrid_recommend, top_rated_bayesian # Ensure this is available
    from .user_model import get_liked_movies # Using the corrected function name
    
    query_lower = query.strip().lower()

    # --- 1. Top Rated Intent ---
    if any(keyword in query_lower for keyword in ["top rated", "best movies", "popular"]):
        agent_name = "Top Rated Agent (Bayesian)"
        # NOTE: top_rated_bayesian may not need the 'movies' argument if it uses the global one.
        results = top_rated_bayesian(top_n=20) 
        return agent_name, results

    # --- 2. Item-to-Item Recommendation Intent (e.g., "movies like The Matrix") ---
    # We use Semantic Search for similarity to a given title.
    if "like " in query_lower or "similar to " in query_lower:
        
        agent_name_prefix = "Search Agent (Item-to-Item"
        target_title = None

        # Extract the target movie title
        for phrase in ["like ", "similar to "]:
            if phrase in query_lower:
                # Get everything after the trigger phrase
                target_title = query_lower.split(phrase, 1)[-1].strip()
                break

        if target_title:
            results = semantic_search(target_title, movies, top_n=20)
            if results:
                return f"{agent_name_prefix} based on: {target_title.title()})", results
            else:
                return f"{agent_name_prefix})", []
        
    # --- 3. Personalized Recommendation Intent (e.g., "recommend movies for me") ---
    if any(keyword in query_lower for keyword in ["recommend", "my taste", "for me", "favorite"]):
        
        # Get user's liked movie titles
        liked_movie_ids = get_liked_movies(user_id) 
        
        favorite_titles = []
        if liked_movie_ids and not movies.empty:
            try:
                # Assuming the movies DataFrame is indexed by movie_id
                favorite_titles = movies.loc[liked_movie_ids]['title'].tolist()
            except KeyError:
                print("Warning: One or more liked movie IDs not found in DataFrame index.")

        if favorite_titles:
            agent_name = "Recommendation Agent (Hybrid)"
            results = hybrid_recommend(favorite_titles, top_n=20)
            return agent_name, results
        else:
            # FALLBACK: If user has no liked movies for personalization
            print("Warning: User has no likes. Falling back to Top-Rated Bayesian.")
            results = top_rated_bayesian(top_n=20)
            return "Recommendation Agent (Fallback: Top-Rated)", results
            
    # --- 4. Default Semantic Search ---
    elif query_lower:
        agent_name = "Search Agent (Semantic)"
        results = semantic_search(query, movies, top_n=20)
        return agent_name, results
        
    else:
        agent_name = "Default"
        return agent_name, []
    
def manage_model_call(query, user_id, movies):
    """Entry point for the multi-agent system."""
    agent, results = decide_agent(query, user_id, movies)
    
    # You can log or add extra logic here based on which agent was called
    print(f"--- Manager Orchestration: Called {agent} ---")
    
    return results