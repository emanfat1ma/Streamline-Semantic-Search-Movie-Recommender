# upgrade_database.py
import sqlite3
import sys

def upgrade_database():
    conn = sqlite3.connect("data/database.db")
    cursor = conn.cursor()
    
    print("Starting database upgrade...")
    
    # 1. Rename old table for clarity (optional but recommended)
    try:
        cursor.execute("ALTER TABLE user_movies RENAME TO user_likes")
        print("✓ Renamed 'user_movies' to 'user_likes'")
    except sqlite3.OperationalError as e:
        print(f"- Note: Could not rename table (might not exist or already renamed): {e}")
    
    # 2. Create 'profiles' table for multiple profiles per account
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            avatar_color TEXT DEFAULT '#E50914',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(user_id, name)
        )
    """)
    print("✓ Created 'profiles' table")
    
    # 3. Create 'watchlist' table for "My List" (separate from likes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE,
            UNIQUE(profile_id, movie_id)  -- Prevent duplicate entries
        )
    """)
    print("✓ Created 'watchlist' table")
    
    # 4. (Optional) Migrate existing 'liked' movies to a default profile for each user
    # This assumes you want to keep old data. We'll do it step-by-step.
    print("\nMigrating existing user likes to default profiles...")
    
    # Get all unique users from the old 'user_likes' or 'user_movies' table
    try:
        cursor.execute("SELECT DISTINCT user_id FROM user_likes")
    except sqlite3.OperationalError:
        # Try the original table name if rename didn't happen
        cursor.execute("SELECT DISTINCT user_id FROM user_movies")
    
    users = cursor.fetchall()
    
    for (user_id,) in users:
        # Create a default profile for each user
        cursor.execute(
            "INSERT OR IGNORE INTO profiles (user_id, name) VALUES (?, ?)",
            (user_id, "Default")
        )
        cursor.execute("SELECT id FROM profiles WHERE user_id=? AND name=?", (user_id, "Default"))
        profile_id = cursor.fetchone()[0]
        
        # Get user's liked movies
        try:
            cursor.execute("SELECT movie_id FROM user_likes WHERE user_id=?", (user_id,))
        except sqlite3.OperationalError:
            cursor.execute("SELECT movie_id FROM user_movies WHERE user_id=?", (user_id,))
        
        liked_movies = cursor.fetchall()
        
        # Add each liked movie to the default profile's watchlist (optional)
        for (movie_id,) in liked_movies:
            cursor.execute(
                "INSERT OR IGNORE INTO watchlist (profile_id, movie_id) VALUES (?, ?)",
                (profile_id, movie_id)
            )
    
    conn.commit()
    conn.close()
    print("\n✅ Database upgrade completed successfully!")
    print("   - Added support for multiple user profiles")
    print("   - Created separate 'watchlist' for My List")
    print("\n⚠️  Important: Update your app.py to use session['profile_id'] instead of user_id for watchlist operations.")

if __name__ == "__main__":
    # Safety check
    response = input("This will modify your database schema. Backup your data first. Continue? (y/N): ")
    if response.lower() == 'y':
        upgrade_database()
    else:
        print("Upgrade cancelled.")