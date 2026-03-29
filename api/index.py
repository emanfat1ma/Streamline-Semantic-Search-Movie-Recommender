import os
import sqlite3
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.db import get_db
from model.search_model import semantic_search
from model.recommendation_model import hybrid_recommend, top_rated_bayesian, user_likes
from model.user_model import like_movie as like_movie_db, get_favorite_movie_for_user
from model.user_model import get_liked_movies
from model.model_manager import manage_model_call
from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import pandas as pd
import hashlib
from model.user_model import get_user_profiles, switch_active_profile, get_watchlist, add_to_watchlist, remove_from_watchlist, is_in_watchlist, create_profile

base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(base_dir, '..', 'templates'),
            static_folder=os.path.join(base_dir, '..', 'static'))
app.secret_key = "supersecretkey"   # change in real project

db_path = os.path.join(base_dir, "..", "data", "database.db")
data_csv_path = os.path.abspath(os.path.join(base_dir, "..", "data", "movies_clean_with_posters.csv"))

movies = pd.read_csv(data_csv_path)

def get_db_connection():
    """Connects to the database and sets row_factory for column access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

# ---------- AUTH HELPERS ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def user_logged_in():
    return "user_id" in session

def get_user_likes(user_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT movie_id FROM user_likes WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    liked_titles = []
    for (movie_id,) in rows:
        try:
            # Handle bytes conversion properly
            if isinstance(movie_id, bytes):
                # Convert bytes to int using int.from_bytes
                movie_id_int = int.from_bytes(movie_id, byteorder='big', signed=False)
            else:
                movie_id_int = int(movie_id)
            
            # Get title from movies DataFrame
            if 0 <= movie_id_int < len(movies):
                title = movies.iloc[movie_id_int]['title']
                liked_titles.append(title)
                
        except Exception as e:
            print(f"Error processing movie_id {movie_id}: {e}")
            # Try alternative conversion
            try:
                if isinstance(movie_id, bytes):
                    # Try little endian
                    movie_id_int = int.from_bytes(movie_id, byteorder='little', signed=False)
                    if 0 <= movie_id_int < len(movies):
                        title = movies.iloc[movie_id_int]['title']
                        liked_titles.append(title)
            except:
                continue
    
    return liked_titles

# Add this helper function after your existing helper functions
def get_active_profile_id(user_id):
    """Get the active profile ID for a user, create default if none exists"""
    profiles = get_user_profiles(user_id)
    
    if not profiles:
        # Create default profile
        create_profile(user_id, "Default")
        profiles = get_user_profiles(user_id)
    
    # Find active profile or use first one
    active_profile = next((p for p in profiles if p['is_active']), profiles[0])
    return active_profile['id']

# ---------- ROUTES ------------
@app.route("/")
def home():
    if not user_logged_in():
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # 1. get active profile
    profiles = get_user_profiles(user_id)
    active_profile = next((p for p in profiles if p["is_active"]), None)

    profile_id = active_profile["id"] if active_profile else None
    movies_sorted = movies.set_index('id').sort_index()

    # 2. watchlist MUST use profile_id
    watchlist_movies = get_watchlist(profile_id, movies) if profile_id else []

    # 3. likes may be empty (normal for new users)
    liked_movie_ids = get_liked_movies(user_id)
    favorite_titles = movies_sorted.loc[liked_movie_ids, "title"].tolist() if liked_movie_ids else []
    if liked_movie_ids:
        recommended = hybrid_recommend(favorite_titles, top_n=10)
        personalized = True
    else:
        recommended = []  # fallback
        personalized = False

    top_rated = top_rated_bayesian(top_n=10)
    new_releases = movies.sort_values("release_date", ascending=False).head(10)
    hero_movie = recommended[0] if recommended else (top_rated[0] if top_rated else new_releases.iloc[0])
    
    return render_template(
    "home.html",
    recommended=recommended,
    top_rated=top_rated,
    popular=top_rated if not recommended else recommended[:10],
    hero_movie=hero_movie,
    watchlist_movies=watchlist_movies,
    new_releases=new_releases,
    personalized=bool(liked_movie_ids)
)



@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = hash_password(request.form["password"])

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                        (username, email, password))
            conn.commit()
            return redirect(url_for("login"))
        except:
            return redirect(url_for("signup", error="User already exists! Please try a different email."))
    
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        email = request.form["email"]
        password = hash_password(request.form["password"])

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            
            # Set active profile
            active_profile_id = get_active_profile_id(user["id"])
            session["profile_id"] = active_profile_id
            
            return redirect(url_for("home"))
        else:
            return redirect(url_for("login", error="Invalid email or password. Please try again."))
    
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/search", methods=["GET", "POST"])
def search():
    if not user_logged_in():
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    results = []
    query = ""
    agent_called = ""
    error = None

    if request.method == "POST":
        query = request.form.get("query", "").strip()
        if query:
            try:
                results = manage_model_call(query, user_id, movies)
                agent_called = "Manager Orchestrated Result"
            except Exception as e:
                error = "An error occurred while processing the request."
                print(f"Manager error: {e}")

    return render_template("search.html", results=results, query=query, agent_called=agent_called,error=error)

@app.route("/like_movie", methods=["POST"])
def like_movie():
    if not user_logged_in():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": "Not logged in"}), 401
        return redirect(url_for("login"))

    user_id = session["user_id"]
    movie_title = request.form.get("movie_title", "")

    # Get movie ID from title 
    match = movies[movies["title"].str.lower() == movie_title.lower()] 
    if match.empty:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": "Movie not found"}), 404
        return redirect(request.referrer) # movie not found 
    
    # Check if already liked (prevent duplicates)
    liked_titles = get_user_likes(user_id)
    if movie_title in liked_titles:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": True, "message": "Already liked", "already_liked": True}), 200
        return redirect(request.referrer)
    
    # Use index as movie_id since there's no id column
    movie_id = match.index[0]
    like_movie_db(user_id, movie_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"success": True, "message": "Movie liked successfully"}), 200
    
    favorite_titles = get_user_likes(user_id) 
    recommendations = hybrid_recommend(favorite_titles, top_n=5)
    session["recommendations"] = recommendations 
    return redirect(request.referrer)

@app.route("/top_rated")
def top_rated():
    recommended = top_rated_bayesian(top_n=8)
    return render_template("home.html", recommended=recommended, tab="top_rated")

# Fixed and optimized @app.route("/profile")

@app.route("/profile")
def profile_dashboard():
    if not user_logged_in():
        return redirect(url_for("login"))
    
    user_id = session["user_id"]
    profile_id = session.get("profile_id") # Use one variable
    profiles = get_user_profiles(user_id)
    
    watchlist_items = []
    
    if profile_id:
        # Assumes get_watchlist (in user_model.py) now returns a list of dictionaries 
        # with full movie details, not just movie IDs.
        try:
            watchlist_items = get_watchlist(profile_id, movies)
        except Exception as e:
            print(f"Error fetching watchlist: {e}")
            # watchlist_items remains [] on error
            
    return render_template("profile.html", 
                           profiles=profiles,
                           watchlist=watchlist_items, # Pass the clean list
                           active_profile_id=profile_id) # Use the clean variable

@app.route("/switch_profile", methods=["POST"])
def switch_profile():
    if not user_logged_in():
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    profile_id = request.form.get("profile_id")
    user_id = session["user_id"]
    
    # Verify profile belongs to user
    profiles = get_user_profiles(user_id)
    profile_ids = [p['id'] for p in profiles]
    
    if int(profile_id) not in profile_ids:
        return jsonify({"success": False, "error": "Invalid profile"}), 400
    
    switch_active_profile(user_id, profile_id)
    session["profile_id"] = profile_id
    
    return jsonify({"success": True, "message": "Profile switched"})

@app.route("/add_profile", methods=["POST"])
def add_profile():
    if not user_logged_in():
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    profile_name = request.form.get("profile_name", "").strip()
    if not profile_name:
        return jsonify({"success": False, "error": "Profile name required"}), 400
    
    user_id = session["user_id"]
    new_profile_id = create_profile(user_id, profile_name)
    
    if new_profile_id:
        return jsonify({"success": True, "profile_id": new_profile_id})
    else:
        return jsonify({"success": False, "error": "Profile name already exists"}), 400

@app.route("/toggle_watchlist", methods=["POST"])
def toggle_watchlist():
    if not user_logged_in():
        return jsonify({"success": False, "error": "Not logged in"}), 401
    
    movie_title = request.form.get("movie_title", "")
    profile_id = session.get("profile_id")
    
    if not profile_id:
        return jsonify({"success": False, "error": "No active profile"}), 400
    
    # Get movie ID
    match = movies[movies["title"].str.lower() == movie_title.lower()]
    if match.empty:
        return jsonify({"success": False, "error": "Movie not found"}), 404
    
    movie_id = match.index[0]
    
    # Check if already in watchlist
    if is_in_watchlist(profile_id, movie_id):
        remove_from_watchlist(profile_id, movie_id)
        return jsonify({"success": True, "action": "removed", "message": "Removed from My List"})
    else:
        add_to_watchlist(profile_id, movie_id)
        return jsonify({"success": True, "action": "added", "message": "Added to My List"})

@app.route("/toggle_like", methods=["POST"])
def toggle_like():
    try:
        data = request.get_json(silent=True)
        movie_val = data.get("movie_id")
        movie_title = data.get("movie_title", "")
        user_id = session.get("user_id")
        
        if not user_id:
            return jsonify({"error": "User not logged in"}), 401
        if not movie_val:
            return jsonify({"error": "Invalid movie"}), 400

        # Resolve movie ID and title
        movie_id = None
        if isinstance(movie_val, str):
            match = movies[movies["title"].str.lower() == movie_val.lower()]
            if match.empty:
                return jsonify({"error": "Movie not found"}), 400
            movie_id = int(match.iloc[0]["id"])
            movie_title = match.iloc[0]["title"]
        else:
            try:
                movie_id = int(movie_val)
                match = movies[movies["id"] == movie_id]
                if match.empty:
                    return jsonify({"error": "Movie not found"}), 400
                movie_title = match.iloc[0]["title"]
            except:
                return jsonify({"error": "Invalid movie ID"}), 400

        # Database connection
        conn = get_db()
        cur = conn.cursor()

        # Check if user already liked this movie
        cur.execute(
            "SELECT liked FROM user_likes WHERE user_id=? AND movie_id=?",
            (user_id, movie_id)
        )
        row = cur.fetchone()

        if row:
            # Toggle like/unlike
            new_like = 0 if row["liked"] else 1
            cur.execute(
                "UPDATE user_likes SET liked=? WHERE user_id=? AND movie_id=?",
                (new_like, user_id, movie_id)
            )
            liked = bool(new_like)
        else:
            # Insert new like
            cur.execute(
                "INSERT INTO user_likes (user_id, movie_id, liked) VALUES (?, ?, 1)",
                (user_id, movie_id)
            )
            liked = True

        conn.commit()

        # Optional: update in-memory dict for session-based fast access
        if user_id not in user_likes:
            user_likes[user_id] = []
        if liked and movie_title not in user_likes[user_id]:
            user_likes[user_id].append(movie_title)
        elif not liked and movie_title in user_likes[user_id]:
            user_likes[user_id].remove(movie_title)

        return jsonify({"liked": liked})

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
if __name__ == "__main__":
    app.run(debug=True)
  
