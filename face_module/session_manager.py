import sqlite3
from datetime import datetime

def save_session_to_db(summary, driver_name):

    conn = sqlite3.connect("driver_db/drivers.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO sessions (
        driver_name, timestamp, blinks, yawns, avg_ear, avg_mar, drowsy_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        driver_name,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary["blinks"],
        summary["yawns"],
        summary["ear"],
        summary["mar"],
        summary["drowsy"]
    ))

    conn.commit()
    conn.close()