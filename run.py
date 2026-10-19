import uvicorn
import sys
import os

# Add current folder to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, get_db
from app.seed import seed_data

if __name__ == '__main__':
    # Initialize database and seed if not existing
    init_db()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    if count == 0:
        print("First time setup: Seeding initial users and menus...")
        seed_data()
    
    port = 8050
    print(f"Starting Foods Manager server at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
