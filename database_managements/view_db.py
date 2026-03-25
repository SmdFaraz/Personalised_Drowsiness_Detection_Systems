from face_module.profile_manager import load_profiles

profiles = load_profiles()

for p in profiles:
    print("\n--- DRIVER ---")
    print("ID:", p["id"])
    print("EAR:", p["ear"])
    print("MAR:", p["mar"])