import uuid
import pickle
from .database import connect
from .face_engine import compare_faces


def save_profile(embedding, ear, mar, face_img):

    profiles = load_profiles()
    driver_id = f"driver_{len(profiles) + 1}"
    name = driver_id  # default name

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO drivers VALUES (?, ?, ?, ?, ?, ?)
    """, (
        driver_id,
        name,
        pickle.dumps(embedding),
        float(ear),
        float(mar),
        pickle.dumps(face_img)
    ))

    conn.commit()
    conn.close()

    return driver_id

def load_profiles():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM drivers")
    rows = cursor.fetchall()

    conn.close()

    profiles = []

    for row in rows:
        profiles.append({
            "id": row[0],
            "name": row[1],
            "embedding": pickle.loads(row[2]),
            "ear": row[3],
            "mar": row[4],
            "image": pickle.loads(row[5])
        })

    return profiles


def find_matching_profile(embedding):

    profiles = load_profiles()

    if len(profiles) == 0:
        return None

    known_embeddings = [p["embedding"] for p in profiles]

    idx = compare_faces(known_embeddings, embedding)

    if idx is not None:
        return profiles[idx]

    return None

def delete_profile(driver_id):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM drivers WHERE id = ?", (driver_id,))

    conn.commit()
    conn.close()


def update_name(driver_id, new_name):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE drivers SET name=? WHERE id=?
    """, (new_name, driver_id))

    conn.commit()
    conn.close()