import os
import zipfile
import io
from urllib.parse import quote_plus
from utils.utils import login_superset

# =============================
# SCRIPT: UNIVERSAL SUPERSET EXPORT
# =============================

# --- CONFIGURATION ---
LOCAL_URL = "http://localhost:8090"  # Your Superset URL
USERNAME = "admin"
PASSWORD = "admin"

OUTPUT_BASE_DIR = "./superset_exports"

IGNORE_FILES = ["metadata.yaml"]

# =============================
# HELPER FUNCTIONS
# =============================

def get_superset_items(session, url, endpoint):
    """Fetch items from Superset API with pagination"""
    items = []
    page = 0
    page_size = 100
    print(f"📋 Fetching {endpoint} list from Superset...")
    while True:
        resp = session.get(f"{url}/api/v1/{endpoint}/?q={{\"page\":{page},\"page_size\":{page_size}}}")
        if resp.status_code != 200:
            print(f"❌ Failed to fetch {endpoint}: {resp.status_code}")
            return []
        data = resp.json()
        results = data.get("result", [])
        items.extend(results)
        if len(results) < page_size:
            break
        page += 1
    print(f"✅ Total {endpoint} fetched: {len(items)}")
    return items

def export_item(session, url, endpoint, item_id, output_dir, item_name=None):
    """Export a Superset item to JSON/zip"""
    display_name = item_name or f"{endpoint}_{item_id}"
    print(f"\n⬆️ Exporting {display_name}...")

    query_payload = f"!({item_id})"
    encoded_query = quote_plus(query_payload)
    export_url = f"{url}/api/v1/{endpoint}/export/?q={encoded_query}"

    resp = session.get(export_url)
    if resp.status_code != 200:
        print(f"❌ Failed to export {display_name}: {resp.text}")
        return False

    folder_path = os.path.join(output_dir, f"{endpoint}_{item_id}")
    os.makedirs(folder_path, exist_ok=True)
    updated_files = 0

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        top_level = None
        for name in z.namelist():
            if "/" in name:
                top_level = name.split("/")[0]
                break
        for filename in z.namelist():
            if top_level and filename.startswith(top_level + "/"):
                filename_to_save = filename[len(top_level)+1:]
            else:
                filename_to_save = filename
            if not filename_to_save:
                continue

            file_path = os.path.join(folder_path, filename_to_save)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            if os.path.basename(filename_to_save) in IGNORE_FILES and os.path.exists(file_path):
                print(f"ℹ️ Ignored existing file: {filename_to_save}")
                continue

            file_content = z.read(filename).decode('utf-8')
            if not os.path.exists(file_path) or open(file_path).read() != file_content:
                with open(file_path, 'w') as f:
                    f.write(file_content)
                updated_files += 1
                print(f"✅ File updated: {filename_to_save}")

    if updated_files:
        print(f"✅ Updated {updated_files} file(s) for {display_name}")
    else:
        print(f"ℹ️ No changes for {display_name}")
    return True

# =============================
# MAIN EXECUTION
# =============================
if __name__ == "__main__":
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

    session = login_superset(LOCAL_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    # Export order: databases -> datasets -> charts -> dashboards
    items_sequence = [
        # ("database", "databases"),
        ("dataset", "datasets"),
        ("chart", "charts"),
        ("dashboard", "dashboards")
    ]

    for endpoint, dir_name in items_sequence:
        output_dir = os.path.join(OUTPUT_BASE_DIR, dir_name)
        os.makedirs(output_dir, exist_ok=True)
        items = get_superset_items(session, LOCAL_URL, endpoint)
        for item in items:
            # Determine human-readable name if available
            if endpoint == "database":
                name = item.get("database_name")
            elif endpoint == "dataset":
                name = item.get("table_name")
            elif endpoint == "chart":
                name = item.get("slice_name")
            elif endpoint == "dashboard":
                name = item.get("dashboard_title")
            else:
                name = None
            export_item(session, LOCAL_URL, endpoint, item['id'], output_dir, name)
    
    print("\n--- Superset Universal Export Complete ---")
