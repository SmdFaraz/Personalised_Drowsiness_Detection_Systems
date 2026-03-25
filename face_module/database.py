import sqlite3
import os

DB_PATH = "driver_db/drivers.db"


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    os.makedirs("driver_db", exist_ok=True)

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        id TEXT PRIMARY KEY,
        name TEXT,
        embedding BLOB,
        ear_threshold REAL,
        mar_threshold REAL,
        face_image BLOB
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_name TEXT,
        timestamp TEXT,
        blinks INTEGER,
        yawns INTEGER,
        avg_ear REAL,
        avg_mar REAL,
        drowsy_count INTEGER
    )
    """)

    conn.commit()
    conn.close()