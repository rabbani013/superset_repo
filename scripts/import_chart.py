import os
from utils.utils import login_superset, get_csrf_token, import_zip

PROD_URL = "https://5750dff529b5.ngrok-free.app"
USERNAME = "admin"
PASSWORD = "admin"
ZIPS_DIR = "./superset_imports/zips/charts/"

if __name__ == "__main__":
    print("--- Starting Chart ZIP Import ---")

    if not os.path.exists(ZIPS_DIR):
        print(f"❌ Zips directory does not exist: {ZIPS_DIR}")
        exit()

    session = login_superset(PROD_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    csrf_token = get_csrf_token(session, PROD_URL)
    if not csrf_token:
        exit()
    session.headers.update({"X-CSRFToken": csrf_token})

    zip_files = [f for f in os.listdir(ZIPS_DIR) if f.endswith(".zip")]

    if not zip_files:
        print("✅ No chart zips found.")
        exit()

    for zip_file in zip_files:
        import_zip(session, PROD_URL, os.path.join(ZIPS_DIR, zip_file), resource="chart")

    print("--- Chart ZIP Import Complete ---")
