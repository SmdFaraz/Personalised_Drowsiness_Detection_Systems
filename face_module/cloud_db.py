from supabase import create_client
import json
from datetime import datetime


SUPABASE_URL = "https://bzpyeomaadytqfsytgjf.supabase.co"
SUPABASE_KEY = "sb_publishable_3PLrhilz0HleWi4UT9--5g_3z-c6jlZ"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------- PROFILES --------

def save_profile_cloud(name, embedding, ear, mar, image):

    data = {
        "name": name,
        "embedding": json.dumps(embedding.tolist()),
        "ear": ear,
        "mar": mar,
        "image": ""
    }

    supabase.table("profiles").insert(data).execute()


def load_profiles_cloud():

    response = supabase.table("profiles").select("*").execute()
    profiles = response.data

    for p in profiles:
        p["embedding"] = json.loads(p["embedding"])

    return profiles


# -------- SESSIONS --------

def save_session_cloud(summary, driver_name):

    data = {
        "driver_name": driver_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "blinks": summary["blinks"],
        "yawns": summary["yawns"],
        "avg_ear": summary["ear"],
        "avg_mar": summary["mar"],
        "drowsy_count": summary["drowsy"]
    }

    supabase.table("sessions").insert(data).execute()