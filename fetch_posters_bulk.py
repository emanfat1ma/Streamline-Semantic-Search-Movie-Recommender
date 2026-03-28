import pandas as pd
import requests
import time

API_KEY = "e2d74035cb9ebf881437c3b4b3905a2c"
BASE_URL = "https://api.themoviedb.org/3/search/movie"

movies = pd.read_csv("data/movies_clean.csv")

poster_urls = []

for title in movies["title"]:
    params = {
        "api_key": API_KEY,
        "query": title,
    }

    try:
        r = requests.get(BASE_URL, params=params)
        data = r.json()

        if data["results"]:
            poster_path = data["results"][0].get("poster_path", None)
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            else:
                poster_url = None
        else:
            poster_url = None

        poster_urls.append(poster_url)

    except:
        poster_urls.append(None)

    time.sleep(0.20)   # avoid rate limit

movies["poster_url"] = poster_urls
movies.to_csv("data/movies_clean_with_posters.csv", index=False)

print("Done! Posters saved.")
