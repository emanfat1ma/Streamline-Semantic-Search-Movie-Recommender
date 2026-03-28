import pandas as pd
import requests

API_KEY = "e2d74035cb9ebf881437c3b4b3905a2c"

SEARCH_MOVIE = "https://api.themoviedb.org/3/search/movie"
SEARCH_TV = "https://api.themoviedb.org/3/search/tv"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

movies_file = "data/movies_clean_with_posters.csv"
movies = pd.read_csv(movies_file)

def get_poster(title):
    # try movie search first, then TV search
    for url in [SEARCH_MOVIE, SEARCH_TV]:
        r = requests.get(url, params={"api_key": API_KEY, "query": title})
        if r.status_code != 200:
            continue

        data = r.json()
        for item in data.get("results", []):
            poster_path = item.get("poster_path")
            if poster_path:
                return f"{IMAGE_BASE}{poster_path}"

    return "None"

# update posters only where missing
for idx, row in movies.iterrows():
    poster = row.get("poster_url")

    if pd.isna(poster) or poster == "" or poster == "None":
        title = row["title"]
        poster_url = get_poster(title)
        movies.at[idx, "poster_url"] = poster_url
        print(f"{title}: Updated poster_url: {poster_url}")

# save once at end
movies.to_csv(movies_file, index=False)
