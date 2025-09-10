import os
import requests
import zipfile
import io
from urllib.parse import quote_plus
from utils import login_superset

# =============================
# SCRIPT: EXPORT ALL SUPERSET CHARTS
# =============================

# --- CONFIGURATION ---
LOCAL_URL = "http://localhost:8090"  # Your Superset URL
USERNAME = "admin"                    # Your Superset username
PASSWORD = "admin"                    # Your Superset password
OUTPUT_DIRECTORY = "./superset_exports/charts"  # Base directory for charts

# Files that should not be overwritten if already exist
IGNORE_FILES = ["metadata.yaml"]

# # --- HELPERS ---
# def login_superset(url, username, password):
#     print(f"🔑 Logging in to Superset at {url} as {username}")
#     session = requests.Session()
#     login_resp = session.post(f"{url}/api/v1/security/login", json={
#         "username": username,
#         "password": password,
#         "provider": "db",
#         "refresh": True
#     })

#     if login_resp.status_code != 200:
#         print(f"❌ Login failed: {login_resp.status_code}")
#         print(f"Response: {login_resp.text}")
#         return None
        
#     token = login_resp.json()["access_token"]
#     session.headers.update({"Authorization": f"Bearer {token}"})
#     print("✅ Login successful")
#     return session

def get_all_charts(session, url):
    charts = []
    page = 0
    page_size = 100
    print("📋 Fetching charts list from Superset...")
    while True:
        resp = session.get(f"{url}/api/v1/chart/?q={{\"page\":{page},\"page_size\":{page_size}}}")
        if resp.status_code != 200:
            print(f"❌ Failed to fetch charts: {resp.status_code}")
            return []

        data = resp.json()
        results = data.get("result", [])
        charts.extend(results)
        
        if len(results) < page_size:
            break
        page += 1
        
    print(f"✅ Total charts fetched: {len(charts)}")
    for c in charts:
        print(f"  - ID: {c['id']}, Name: {c['slice_name']}")
    return charts

def export_chart_to_json(session, url, chart_id, output_dir):
    print(f"\n⬆️ Exporting chart {chart_id}...")

    query_payload = f"!({chart_id})"
    encoded_query = quote_plus(query_payload)
    export_url = f"{url}/api/v1/chart/export/?q={encoded_query}"

    resp = session.get(export_url)
    if resp.status_code != 200:
        print(f"❌ Failed to export chart {chart_id}: {resp.text}")
        return False

    chart_folder = os.path.join(output_dir, f"chart_{chart_id}")
    os.makedirs(chart_folder, exist_ok=True)

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

            file_path = os.path.join(chart_folder, filename_to_save)
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
        print(f"✅ Updated {updated_files} file(s) for chart {chart_id}")
    else:
        print(f"ℹ️ No changes for chart {chart_id}")

    return True

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

    session = login_superset(LOCAL_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    charts = get_all_charts(session, LOCAL_URL)
    if not charts:
        print("No charts found to export.")
        exit()

    for chart in charts:
        export_chart_to_json(session, LOCAL_URL, chart['id'], OUTPUT_DIRECTORY)

    print("\n--- Chart Export Complete ---")
