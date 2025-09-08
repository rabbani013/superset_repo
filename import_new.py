import os
import requests
import io
import zipfile
import subprocess

# =============================
# SCRIPT: IMPORT JSON DASHBOARDS TO PRODUCTION
# =============================

# --- CONFIGURATION ---
PROD_URL = "https://5750dff529b5.ngrok-free.app"
USERNAME = "admin"
PASSWORD = "admin"
JSON_DASHBOARDS_DIR = "./superset_exports/json_dashboards"  # Directory containing JSON dashboards

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

def create_zip_from_json(json_file_path):
    """
    Wraps a single JSON file in a zip buffer for Superset import.
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        file_name = os.path.basename(json_file_path)
        zip_file.write(json_file_path, file_name)
    zip_buffer.seek(0)
    return zip_buffer

def import_json_dashboard(session, url, json_file_path):
    print(f"⬆️ Importing JSON dashboard: {json_file_path}")
    zip_buffer = create_zip_from_json(json_file_path)
    if not zip_buffer:
        return False

    files = {
        'formData': (os.path.basename(json_file_path).replace(".json", ".zip"), zip_buffer, 'application/zip'),
        'overwrite': (None, 'true')
    }

    # Superset expects JSON inside a zip; use format=json
    resp = session.post(f"{url}/api/v1/dashboard/import/?format=json", files=files)
    if resp.status_code != 200:
        print(f"❌ Failed to import. Status: {resp.status_code}")
        try:
            print(f"Response: {resp.text}")
        except Exception:
            pass
        return False

    print(f"✅ Successfully imported {os.path.basename(json_file_path)}")
    return True

def find_changed_json_dashboards(root_dir):
    """
    Detects changed or untracked JSON dashboards via Git and returns a set of file paths.
    """
    changed_files = set()
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"], cwd=root_dir, text=True)
        for line in output.splitlines():
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            file_path = parts[1]
            if file_path.endswith(".json"):
                abs_path = os.path.join(root_dir, file_path)
                changed_files.add(abs_path)
    except Exception as e:
        print(f"❌ Git error: {e}")
    return changed_files

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("--- Starting Production JSON Dashboard Import ---")

    changed_dashboards = find_changed_json_dashboards(JSON_DASHBOARDS_DIR)
    if not changed_dashboards:
        print("✅ No JSON dashboard changes detected.")
        exit()

    print(f"Found {len(changed_dashboards)} changed dashboard(s).")

    session = login_superset(PROD_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    csrf = get_csrf_token(session, PROD_URL)
    if not csrf:
        exit()
    session.headers.update({"X-CSRFToken": csrf})

    for json_dashboard in changed_dashboards:
        import_json_dashboard(session, PROD_URL, json_dashboard)

    print("--- Production JSON Dashboard Import Complete ---")
