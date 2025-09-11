import os
from utils.utils import login_superset, get_csrf_token, import_zip

PROD_URL = os.environ.get("SUPERSET_PROD_URL")
USERNAME = os.environ.get("SUPERSET_ADMIN_USER")
PASSWORD = os.environ.get("SUPERSET_ADMIN_PASS")

ZIPS_DIR = "./.tmp_zips/dashboards/"

if __name__ == "__main__":
    print("--- Starting Dashboard ZIP Import ---")

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
        print("✅ No dashboard zips found.")
        exit()

    for zip_file in zip_files:
        import_zip(session, PROD_URL, os.path.join(ZIPS_DIR, zip_file), resource="dashboard")

    print("--- Dashboard ZIP Import Complete ---")


