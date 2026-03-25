import getpass
from face_module.database import connect

PASSKEY = "72055027"

entered = getpass.getpass("Enter admin passkey: ")

if entered != PASSKEY:
    print("❌ Access Denied")
    exit()

conn = connect()
cursor = conn.cursor()

cursor.execute("DELETE FROM drivers")

conn.commit()
conn.close()

print("✅ All profiles deleted successfully")