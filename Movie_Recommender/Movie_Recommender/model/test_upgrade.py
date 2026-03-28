# test_upgrade.py
import sqlite3

conn = sqlite3.connect("data/database.db")
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:", [t[0] for t in tables])

# Check profiles
cursor.execute("SELECT * FROM profiles LIMIT 3")
print("\nSample profiles:", cursor.fetchall())

conn.close()