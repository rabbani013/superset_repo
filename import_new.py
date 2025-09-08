import os
import requests
import io
import zipfile

# =============================
# SCRIPT: DIRECT IMPORT OF JSON DASHBOARDS TO PRODUCTION
# =============================

# --- CONFIGURATION ---
PROD_URL = "https://5750dff529b5.ngrok-free.app"  # Production Superset URL
USERNAME = "admin"
PASSWORD = "admin"
JSON_DASHBOARDS_DIR = os.path.expanduser("~/superset_repo/superset_exports/json_dashboards")

# --- HELPERS ---
def login_superset(url, username, password):
    print(f"🔑 Logging in to Superset at {url} as {username}")
    session = requests.Session()
    resp = session.post(f"{url}/api/v1/security/login", json={
        "username": username,
        "password": password,
        "provider": "db",
        "refresh": True
    })
    if resp.status_code != 200:
        print(f"❌ Login failed: {resp.status_code} {resp.text}")
        return None
    token = resp.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Login successful")
    return session

def get_csrf_token(session, url):
    resp = session.get(f"{url}/api/v1/security/csrf_token/")
    if resp.status_code != 200:
        print(f"❌ Failed to get CSRF token: {resp.text}")
        return None
    return resp.json().get("result")

def create_zip_from_json(json_path):
    """Wrap a single JSON file into a zip for import"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(json_path, os.path.basename(json_path))
    zip_buffer.seek(0)
    return zip_buffer

def import_json_dashboard(session, url, json_file_path):
    print(f"⬆️ Importing JSON dashboard: {json_file_path}")
    zip_buffer = create_zip_from_json(json_file_path)

    files = {
        'formData': (os.path.basename(json_file_path) + ".zip", zip_buffer, 'application/zip'),
        'overwrite': (None, 'true')
    }

    resp = session.post(f"{url}/api/v1/dashboard/import/?format=json", files=files)
    if resp.status_code != 200:
        print(f"❌ Failed to import. Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        return False

    print(f"✅ Successfully imported {os.path.basename(json_file_path)}")
    return True

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("--- Starting Direct JSON Dashboard Import ---")

    # Find all JSON files in the folder
    json_files = [os.path.join(JSON_DASHBOARDS_DIR, f) for f in os.listdir(JSON_DASHBOARDS_DIR) if f.endswith(".json")]
    if not json_files:
        print(f"❌ No JSON dashboards found in {JSON_DASHBOARDS_DIR}")
        exit()

    session = login_superset(PROD_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    csrf = get_csrf_token(session, PROD_URL)
    if not csrf:
        exit()
    session.headers.update({"X-CSRFToken": csrf})

    for json_file in json_files:
        import_json_dashboard(session, PROD_URL, json_file)

    print("--- Direct JSON Dashboard Import Complete ---")
