import pandas as pd
import pickle
from model.model_utils import get_model
import ast  # to parse keywords lists

# Load CSV
movies = pd.read_csv("data/tmdb_5000_movies.csv")

# Parse the "keywords" JSON-like list
def extract_keywords(x):
    try:
        items = ast.literal_eval(x)
        return " ".join([d['name'] for d in items])
    except:
        return ""

movies["keywords_text"] = movies["keywords"].apply(extract_keywords)

movies["text"] = (                            # Build text for embedding
    movies["overview"].fillna("") + " " +
    movies["keywords_text"].fillna("")
)

# Load sentence transformer model (using shared cached model)
model = get_model()

# Generate embeddings
embeddings = model.encode(movies["text"].tolist(), convert_to_numpy=True)

# Save embeddings
with open("data/movie_embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)

# Save filtered movies (so indices match)
movies[["title", "overview", "keywords_text"]].to_csv("data/movies_clean.csv", index=False)

print("Done! Embeddings + cleaned movies saved.")
