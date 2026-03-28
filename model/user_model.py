from flask import current_app
from db import get_db
from sqlite3 import IntegrityError

def like_movie(user_id, movie_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Check if already exists
    cur.execute(
        "SELECT id FROM user_likes WHERE user_id=? AND movie_id=?",
        (user_id, movie_id)
    )
    exists = cur.fetchone()
    
    if not exists:
        cur.execute(
            "INSERT INTO user_likes (user_id, movie_id, liked) VALUES (?, ?, 1)",
            (user_id, movie_id)
        )
    conn.commit()

def get_liked_movies(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT movie_id FROM user_likes WHERE user_id=? AND liked=1",
        (user_id,)
    )
    rows = cur.fetchall()
    # Ensure we return integers
    return [int(row["movie_id"]) for row in rows]

def get_favorite_movie_for_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT movie_id FROM user_likes WHERE user_id=? AND liked=1 ORDER BY id DESC LIMIT 1",
        (user_id,)
    )
    row = cur.fetchone()
    return int(row["movie_id"]) if row else None

# Add these new functions to your existing model/user_model.py

def create_profile(user_id, profile_name, avatar_color="#E50914"):
    """Create a new profile for a user"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO profiles (user_id, name, avatar_color) VALUES (?, ?, ?)",
            (user_id, profile_name, avatar_color)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None  # Profile name already exists for this user
    finally:
        conn.close()

def get_user_profiles(user_id):
    """Get all profiles for a user"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, avatar_color, is_active FROM profiles WHERE user_id=? ORDER BY is_active DESC, id",
        (user_id,)
    )
    profiles = [dict(row) for row in cur.fetchall()]
    conn.close()
    return profiles

def switch_active_profile(user_id, profile_id):
    """Switch a user's active profile"""
    conn = get_db()
    cur = conn.cursor()
    # Set all profiles inactive first
    cur.execute("UPDATE profiles SET is_active=0 WHERE user_id=?", (user_id,))
    # Set the selected profile active
    cur.execute("UPDATE profiles SET is_active=1 WHERE id=? AND user_id=?", (profile_id, user_id))
    conn.commit()
    conn.close()

def add_to_watchlist(profile_id, movie_id):
    """
    Adds a movie to the profile's watchlist.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO watchlist (profile_id, movie_id) VALUES (?, ?)",
            (profile_id, movie_id)
        )
        conn.commit()
        return True
    except IntegrityError as e:
        # Handle case where movie_id or profile_id doesn't exist (due to foreign keys)
        current_app.logger.warning(f"Integrity Error adding to watchlist: {e}")
        return False
    finally:
        conn.close()

def remove_from_watchlist(profile_id, movie_id):
    """
    Removes a movie from the profile's watchlist.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM watchlist WHERE profile_id = ? AND movie_id = ?",
        (profile_id, movie_id)
    )
    
    rows_deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    # Returns True if at least one row was deleted
    return rows_deleted > 0

def get_watchlist(profile_id, movies):
    """
    Retrieves the full list of movie details for a given profile's watchlist.
    It returns movie IDs from SQLite and joins their details from the global Pandas DataFrame.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Get all movie_ids for the active profile
    cursor.execute(
        "SELECT movie_id FROM watchlist WHERE profile_id = ?",
        (profile_id,)
    )
    movie_ids = []
    for row in cursor.fetchall():
        movie_id = row['movie_id']
        try:
            if isinstance(movie_id, bytes):
            # Convert bytes to an integer (assuming it's little-endian, a common SQLite format)
            # This is the line needed to handle b'\x04...' correctly
                movie_id_int = int.from_bytes(movie_id, byteorder='little', signed=False) 
            else:
            # Handle standard integer or string representation
                movie_id_int = int(movie_id)
            
            movie_ids.append(movie_id_int)
        except (ValueError, TypeError):
            # Skip any corrupt or un-parsable IDs
            print(f"Warning: Corrupt movie ID found in watchlist: {row['movie_id']}")
            continue
    conn.close()
    
    if not movie_ids:
        return []
    
    # 2. Look up movie details in the Pandas DataFrame
    # IMPORTANT: This assumes the 'movies' DataFrame is correctly indexed by 'movie_id'
    try:
        # Use .loc to select rows by their index (movie_id)
        watchlist_movies_df = movies.loc[movie_ids]
        
        # Convert the results back to a list of Python dictionaries for the Jinja template
        return watchlist_movies_df.to_dict('records')
        
    except KeyError:
        print("Error: One or more movie IDs from the watchlist are missing from the movies DataFrame.")
        return []

def is_in_watchlist(profile_id, movie_id):
    """
    Checks if a movie is in the profile's watchlist, using the database structure:
    watchlist(id, profile_id, movie_id, added_at)
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id FROM watchlist WHERE profile_id = ? AND movie_id = ?",
        (profile_id, movie_id)
    )
    
    # If fetchone returns a row, it's in the watchlist
    is_present = cursor.fetchone() is not None
    conn.close()
    return is_present