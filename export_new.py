import os
import zipfile
import io
import yaml
import json
import requests
from urllib.parse import quote_plus

# =============================
# CONFIGURATION
# =============================
LOCAL_URL = "http://localhost:8090"  # Superset URL
USERNAME = "admin"
PASSWORD = "admin"
DASHBOARD_IDS = [9]  # List of dashboard IDs to export
OUTPUT_DIR = "./superset_exports/json_dashboards"

# =============================
# LOGIN
# =============================
def login_superset(url, username, password):
    print(f"🔑 Logging in to Superset at {url} as {username}")
    session = requests.Session()
    resp = session.post(
        f"{url}/api/v1/security/login",
        json={
            "username": username,
            "password": password,
            "provider": "db",
            "refresh": True
        },
    )
    if resp.status_code != 200:
        raise Exception(f"Login failed: {resp.text}")
    token = resp.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Login successful")
    return session

# =============================
# EXPORT DASHBOARD ZIP
# =============================
def export_dashboard_zip(session, url, dashboard_id):
    print(f"\n⬆️ Exporting dashboard {dashboard_id} as ZIP...")
    query_payload = f"!({dashboard_id})"
    encoded_query = quote_plus(query_payload)
    export_url = f"{url}/api/v1/dashboard/export/?q={encoded_query}"
    resp = session.get(export_url)
    if resp.status_code != 200:
        raise Exception(f"Failed to export dashboard {dashboard_id}: {resp.text}")
    return io.BytesIO(resp.content)

# =============================
# CONVERT YAML TO JSON
# =============================
def yaml_zip_to_json(zip_bytes):
    with zipfile.ZipFile(zip_bytes) as z:
        data = {"dashboard": None, "charts": [], "datasets": []}
        for fname in z.namelist():
            if fname.endswith(".yaml"):
                content = z.read(fname).decode("utf-8")
                y = yaml.safe_load(content)
                if y is None:
                    continue
                # Detect type
                if "dashboard_title" in y:
                    data["dashboard"] = y
                elif "slice_name" in y or "chart_name" in y:
                    data["charts"].append(y)
                elif "table_name" in y or "dataset_name" in y:
                    data["datasets"].append(y)
                else:
                    # Other YAMLs (metadata, examples) can be skipped or merged
                    pass
        return data

# =============================
# SAVE JSON
# =============================
def save_json(data, output_dir, dashboard_name):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"{dashboard_name}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Saved JSON: {file_path}")
    return file_path

# =============================
# MAIN
# =============================
if __name__ == "__main__":
    session = login_superset(LOCAL_URL, USERNAME, PASSWORD)

    for dashboard_id in DASHBOARD_IDS:
        try:
            zip_bytes = export_dashboard_zip(session, LOCAL_URL, dashboard_id)
            json_data = yaml_zip_to_json(zip_bytes)

            # Use dashboard title or fallback
            dashboard_name = json_data["dashboard"].get("dashboard_title", f"dashboard_{dashboard_id}")
            save_json(json_data, OUTPUT_DIR, dashboard_name)

        except Exception as e:
            print(f"❌ Error exporting dashboard {dashboard_id}: {e}")

    print("\n--- All dashboards exported as JSON ✅ ---")




# import os
# import requests
# import zipfile
# import io
# from urllib.parse import quote_plus

# # =============================
# # SCRIPT: EXPORT ALL SUPERSET DASHBOARDS
# # =============================

# # --- CONFIGURATION ---
# LOCAL_URL = "http://localhost:8090"  # Your Superset URL
# USERNAME = "admin"                    # Your Superset username
# PASSWORD = "admin"                    # Your Superset password
# OUTPUT_DIRECTORY = "./superset_exports/dashboards"  # Base directory for dashboards

# # Files that should not be overwritten if already exist
# IGNORE_FILES = ["USA_Births_Names_2.yaml", "metadata.yaml"]

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

# def get_all_dashboards(session, url):
#     dashboards = []
#     page = 0
#     page_size = 100
#     print("📋 Fetching dashboards list from Superset...")
#     while True:
#         resp = session.get(f"{url}/api/v1/dashboard/?q={{\"page\":{page},\"page_size\":{page_size}}}")
#         if resp.status_code != 200:
#             print(f"❌ Failed to fetch dashboards: {resp.status_code}")
#             return []

#         data = resp.json()
#         results = data.get("result", [])
#         dashboards.extend(results)
        
#         if len(results) < page_size:
#             break
#         page += 1
        
#     print(f"✅ Total dashboards fetched: {len(dashboards)}")
#     for d in dashboards:
#         print(f"  - ID: {d['id']}, Name: {d['dashboard_title']}")
#     return dashboards

# def export_dashboard_to_json(session, url, dashboard_id, output_dir):
#     print(f"\n⬆️ Exporting dashboard {dashboard_id}...")

#     query_payload = f"!({dashboard_id})"
#     encoded_query = quote_plus(query_payload)
#     export_url = f"{url}/api/v1/dashboard/export/?q={encoded_query}"

#     resp = session.get(export_url)
#     if resp.status_code != 200:
#         print(f"❌ Failed to export dashboard {dashboard_id}: {resp.text}")
#         return False

#     dashboard_folder = os.path.join(output_dir, f"dashboard_{dashboard_id}")
#     os.makedirs(dashboard_folder, exist_ok=True)

#     updated_files = 0

#     with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
#         # Detect top-level folder in zip
#         top_level = None
#         for name in z.namelist():
#             if "/" in name:
#                 top_level = name.split("/")[0]
#                 break

#         for filename in z.namelist():
#             # Strip top-level folder if exists
#             if top_level and filename.startswith(top_level + "/"):
#                 filename_to_save = filename[len(top_level)+1:]
#             else:
#                 filename_to_save = filename

#             if not filename_to_save:  # skip empty folder entries
#                 continue

#             file_path = os.path.join(dashboard_folder, filename_to_save)
#             os.makedirs(os.path.dirname(file_path), exist_ok=True)

#             # Skip if file is in IGNORE_FILES and already exists
#             if os.path.basename(filename_to_save) in IGNORE_FILES and os.path.exists(file_path):
#                 print(f"ℹ️ Ignored existing file: {filename_to_save}")
#                 continue

#             file_content = z.read(filename).decode('utf-8')

#             # Only write if file doesn't exist or content changed
#             if not os.path.exists(file_path) or open(file_path).read() != file_content:
#                 with open(file_path, 'w') as f:
#                     f.write(file_content)
#                 updated_files += 1
#                 print(f"✅ File updated: {filename_to_save}")

#     if updated_files:
#         print(f"✅ Updated {updated_files} file(s) for dashboard {dashboard_id}")
#     else:
#         print(f"ℹ️ No changes for dashboard {dashboard_id}")

#     return True

# # --- MAIN EXECUTION ---
# if __name__ == "__main__":
#     os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

#     session = login_superset(LOCAL_URL, USERNAME, PASSWORD)
#     if not session:
#         exit()

#     dashboards = get_all_dashboards(session, LOCAL_URL)
#     if not dashboards:
#         print("No dashboards found to export.")
#         exit()

#     for dashboard in dashboards:
#         export_dashboard_to_json(session, LOCAL_URL, dashboard['id'], OUTPUT_DIRECTORY)

#     print("\n--- Dashboard Export Complete ---")
