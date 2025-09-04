import os
import requests
import zipfile
import io
from urllib.parse import quote_plus

# =============================
# SCRIPT: EXPORT ALL SUPERSET DASHBOARDS
# =============================

# --- CONFIGURATION ---
LOCAL_URL = "http://localhost:8090"  # Your Superset URL
USERNAME = "admin"                    # Your Superset username
PASSWORD = "admin"                    # Your Superset password
OUTPUT_DIRECTORY = "./superset_exports/dashboards"  # Base directory for dashboards

# Files that should not be overwritten if already exist
IGNORE_FILES = ["USA_Births_Names_2.yaml", "metadata.yaml"]

# --- HELPERS ---
def login_superset(url, username, password):
    print(f"🔑 Logging in to Superset at {url} as {username}")
    session = requests.Session()
    login_resp = session.post(f"{url}/api/v1/security/login", json={
        "username": username,
        "password": password,
        "provider": "db",
        "refresh": True
    })

    if login_resp.status_code != 200:
        print(f"❌ Login failed: {login_resp.status_code}")
        print(f"Response: {login_resp.text}")
        return None
        
    token = login_resp.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Login successful")
    return session

def get_all_dashboards(session, url):
    dashboards = []
    page = 0
    page_size = 100
    print("📋 Fetching dashboards list from Superset...")
    while True:
        resp = session.get(f"{url}/api/v1/dashboard/?q={{\"page\":{page},\"page_size\":{page_size}}}")
        if resp.status_code != 200:
            print(f"❌ Failed to fetch dashboards: {resp.status_code}")
            return []

        data = resp.json()
        results = data.get("result", [])
        dashboards.extend(results)
        
        if len(results) < page_size:
            break
        page += 1
        
    print(f"✅ Total dashboards fetched: {len(dashboards)}")
    for d in dashboards:
        print(f"  - ID: {d['id']}, Name: {d['dashboard_title']}")
    return dashboards

def export_dashboard_to_json(session, url, dashboard_id, output_dir):
    print(f"\n⬆️ Exporting dashboard {dashboard_id}...")

    query_payload = f"!({dashboard_id})"
    encoded_query = quote_plus(query_payload)
    export_url = f"{url}/api/v1/dashboard/export/?q={encoded_query}"

    resp = session.get(export_url)
    if resp.status_code != 200:
        print(f"❌ Failed to export dashboard {dashboard_id}: {resp.text}")
        return False

    dashboard_folder = os.path.join(output_dir, f"dashboard_{dashboard_id}")
    os.makedirs(dashboard_folder, exist_ok=True)

    updated_files = 0

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        # Detect top-level folder in zip
        top_level = None
        for name in z.namelist():
            if "/" in name:
                top_level = name.split("/")[0]
                break

        for filename in z.namelist():
            # Strip top-level folder if exists
            if top_level and filename.startswith(top_level + "/"):
                filename_to_save = filename[len(top_level)+1:]
            else:
                filename_to_save = filename

            if not filename_to_save:  # skip empty folder entries
                continue

            file_path = os.path.join(dashboard_folder, filename_to_save)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Skip if file is in IGNORE_FILES and already exists
            if os.path.basename(filename_to_save) in IGNORE_FILES and os.path.exists(file_path):
                print(f"ℹ️ Ignored existing file: {filename_to_save}")
                continue

            file_content = z.read(filename).decode('utf-8')

            # Only write if file doesn't exist or content changed
            if not os.path.exists(file_path) or open(file_path).read() != file_content:
                with open(file_path, 'w') as f:
                    f.write(file_content)
                updated_files += 1
                print(f"✅ File updated: {filename_to_save}")

    if updated_files:
        print(f"✅ Updated {updated_files} file(s) for dashboard {dashboard_id}")
    else:
        print(f"ℹ️ No changes for dashboard {dashboard_id}")

    return True

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    session = login_superset(LOCAL_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    dashboards = get_all_dashboards(session, LOCAL_URL)
    if not dashboards:
        print("No dashboards found to export.")
        exit()

    for dashboard in dashboards:
        export_dashboard_to_json(session, LOCAL_URL, dashboard['id'], OUTPUT_DIRECTORY)

    print("\n--- Dashboard Export Complete ---")
