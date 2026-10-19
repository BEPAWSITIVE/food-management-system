import sqlite3
import os
import json
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "foods_manager.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT,
        role TEXT NOT NULL CHECK(role IN ('admin', 'kitchen', 'employee')),
        department TEXT DEFAULT 'General',
        dietary_preference TEXT DEFAULT 'Regular',
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Meal Slots table (Default timings: Breakfast at 8:45, Lunch at 1:00 PM, Dinner at 7:00 PM)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS meal_slots (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        serving_time TEXT NOT NULL,
        cutoff_time TEXT NOT NULL,
        icon TEXT NOT NULL,
        display_order INTEGER NOT NULL
    )
    ''')

    # Insert default meal slots if not present
    cursor.execute('SELECT COUNT(*) FROM meal_slots')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO meal_slots (id, name, serving_time, cutoff_time, icon, display_order)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            ('breakfast', 'Breakfast', '08:45', '08:00', 'sun', 1),
            ('lunch', 'Lunch', '13:00', '12:00', 'sun', 2),
            ('dinner', 'Dinner', '19:00', '18:00', 'moon', 3)
        ])

    # Menus table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS menus (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        meal_slot TEXT NOT NULL,
        main_items TEXT NOT NULL,
        side_items TEXT DEFAULT '',
        beverage TEXT DEFAULT '',
        dietary_tags TEXT DEFAULT '',
        special_note TEXT DEFAULT '',
        image_url TEXT DEFAULT '',
        prep_status TEXT DEFAULT 'Not Started',
        cooking_state TEXT DEFAULT 'Not Started',
        updated_by TEXT DEFAULT 'Kitchen Staff',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(date, meal_slot),
        FOREIGN KEY (meal_slot) REFERENCES meal_slots(id)
    )
    ''')

    # Safe migration for existing databases
    existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(menus)").fetchall()]
    if 'image_url' not in existing_cols:
        cursor.execute("ALTER TABLE menus ADD COLUMN image_url TEXT DEFAULT ''")
    if 'prep_status' not in existing_cols:
        cursor.execute("ALTER TABLE menus ADD COLUMN prep_status TEXT DEFAULT 'Not Started'")
    if 'cooking_state' not in existing_cols:
        cursor.execute("ALTER TABLE menus ADD COLUMN cooking_state TEXT DEFAULT 'Not Started'")

    # Attendance table (Default is attending/coming)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        meal_slot TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('attending', 'not_attending')),
        note TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, date, meal_slot),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (meal_slot) REFERENCES meal_slots(id)
    )
    ''')

    # System Settings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    ''')

    cursor.execute('INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)',
                   ('app_title', 'Food Manager'))
    cursor.execute('INSERT OR IGNORE INTO system_settings (key, value) VALUES (?, ?)',
                   ('cutoff_minutes_before', '45'))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at", DB_PATH)
