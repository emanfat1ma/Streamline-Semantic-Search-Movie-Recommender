import db
print("Functions in db module:", dir(db))

try:
    from db import get_db
    print("Successfully imported get_db")
except ImportError as e:
    print(f"Import error: {e}")