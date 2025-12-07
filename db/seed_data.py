# db/seed_data.py
# Initializes the DB and seeds basic sample data for testing.
# Structure suggesed by chatGPT (2025-12).
# Some text automatically corrected by copilot (2025-12).

import sqlite3
import os
import json

DB_DIR = 'db'
DB_PATH = os.path.join(DB_DIR, 'campusconnect.db')

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create external_events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS external_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        date TEXT,
        time TEXT,
        location TEXT,
        description TEXT,
        source TEXT,
        url TEXT,
        weather_forecast TEXT
    )
    ''')

    # Create api_data table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        date TEXT,
        provider TEXT,
        temp_max REAL,
        temp_min REAL,
        weather_code INTEGER,
        weather_text TEXT,
        raw_json TEXT,
        FOREIGN KEY(event_id) REFERENCES external_events(id)
    )
    ''')

    # Seed a sample external_event if none exist
    cursor.execute('SELECT COUNT(*) FROM external_events')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO external_events (title, date, time, location, description, source, url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Sample Campus Event', '2025-12-02', '11:00 am - 12:00 pm',
            'Campus Quad', 'This is a sample seeded event for testing', 'seed', ''
        ))

    # Seed a sample api_data row (optional)
    cursor.execute('SELECT COUNT(*) FROM api_data')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO api_data (event_id, date, provider, temp_max, temp_min, weather_code, weather_text, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (1, '2025-12-02', 'open-meteo', 58.0, 42.0, 0, 'Clear', json.dumps({"sample":"data"})))

    conn.commit()
    conn.close()
    print("Database initialized and seeded at:", DB_PATH)

if __name__ == '__main__':
    init_db()
