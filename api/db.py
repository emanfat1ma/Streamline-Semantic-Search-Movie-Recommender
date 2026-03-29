import os
import sqlite3

# This is a good function, keep it as is.
def get_db():
    """Get a database connection with row factory set to sqlite3.Row"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Path to the database in the root/data folder
    db_path = os.path.join(base_dir, "..", "data", "database.db")
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db()
    cursor = conn.cursor()

    # 1. USERS TABLE (No Change)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    
    # 2. PROFILES TABLE (New - Needed for Multi-Profile)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        avatar_color TEXT DEFAULT '#E50914',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, name) -- Prevents one user from having two profiles with the same name
    )
    """)
    
    # 3. USER LIKES/RATINGS TABLE (Renamed from user_movies to user_likes)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        liked INTEGER DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)
    
    # 4. WATCHLIST TABLE (New - Needed for Watchlist Management)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (profile_id) REFERENCES profiles(id),
        UNIQUE(profile_id, movie_id) -- Prevents adding the same movie twice
    );
    """)
    
    conn.commit()
    conn.close()
    

# Run once to create DB
if __name__ == "__main__":
    init_db()
    print("Database initialized successfully! All required tables created.")