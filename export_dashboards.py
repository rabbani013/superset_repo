# recent================

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

# --- HELPERS ---
def login_superset(url, username, password):
    """
    Authenticates with Superset and returns a session object with an access token.
    """
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
    return session

def get_all_dashboards(session, url):
    """
    Fetches a list of all dashboards from the API.
    """
    dashboards = []
    page = 0
    page_size = 100
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
        
    return dashboards

def export_dashboard_to_json(session, url, dashboard_id, output_dir):
    """
    Exports a single dashboard and saves JSON files in dashboard_<id> folder.
    Ignores any top-level folder in the zip.
    Only updates files if content changed.
    """
    print(f"⬆️ Exporting dashboard {dashboard_id}...")

    query_payload = f"!({dashboard_id})"
    encoded_query = quote_plus(query_payload)
    export_url = f"{url}/api/v1/dashboard/export/?q={encoded_query}"

    resp = session.get(export_url)
    if resp.status_code != 200:
        print(f"❌ Failed to export dashboard {dashboard_id}: {resp.status_code}")
        return False

    # Folder for this dashboard
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
            # Strip the top-level folder if exists
            if top_level and filename.startswith(top_level + "/"):
                filename_to_save = filename[len(top_level)+1:]
            else:
                filename_to_save = filename

            if not filename_to_save:  # skip empty folder entries
                continue

            file_content = z.read(filename).decode('utf-8')
            file_path = os.path.join(dashboard_folder, filename_to_save)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Only write if file doesn't exist or content changed
            if not os.path.exists(file_path) or open(file_path).read() != file_content:
                with open(file_path, 'w') as f:
                    f.write(file_content)
                updated_files += 1

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

    print(f"Found {len(dashboards)} dashboards to export.")

    for dashboard in dashboards:
        export_dashboard_to_json(session, LOCAL_URL, dashboard['id'], OUTPUT_DIRECTORY)

    print("--- Dashboard Export Complete ---")



# ==========================




# import os
# import json
# import requests
# import zipfile
# import io

# # =============================
# # SCRIPT 1: EXPORT ALL SUPERSET DASHBOARDS
# # =============================

# # --- CONFIGURATION ---
# # IMPORTANT: Update these variables for your Superset instance
# LOCAL_URL = "http://localhost:8090"  # Your Superset URL
# USERNAME = "admin"                    # Your Superset username
# PASSWORD = "admin"                    # Your Superset password
# OUTPUT_DIRECTORY = "./superset_exports/dashboards" # Directory to save the exported files

# # --- HELPERS ---
# def login_superset(url, username, password):
#     """
#     Authenticates with Superset and returns a session object with an access token.
#     """
#     session = requests.Session()
#     login_resp = session.post(f"{url}/api/v1/security/login", json={
#         "username": username,
#         "password": password,
#         "provider": "db",
#         "refresh": True
#     })

#     if login_resp.status_code != 200:
#         print(f"❌ Login to {url} failed with status code: {login_resp.status_code}")
#         print(f"Response: {login_resp.text}")
#         return None
        
#     token = login_resp.json()["access_token"]
#     session.headers.update({"Authorization": f"Bearer {token}"})
#     return session

# def get_csrf_token(session, url):
#     """
#     Fetches the CSRF token from the Superset API.
#     """
#     try:
#         csrf_resp = session.get(f"{url}/api/v1/security/csrf_token/")
#         csrf_resp.raise_for_status()
#         return csrf_resp.json().get("result")
#     except requests.exceptions.RequestException as e:
#         print(f"❌ Failed to get CSRF token: {e}")
#         return None

# def get_all_dashboards(session, url):
#     """
#     Fetches a list of all dashboards from the API.
#     """
#     dashboards = []
#     page = 0
#     page_size = 100
#     while True:
#         resp = session.get(f"{url}/api/v1/dashboard/?q={{\"page\":{page},\"page_size\":{page_size}}}")
#         if resp.status_code != 200:
#             print(f"❌ Failed to fetch dashboard list: {resp.status_code}")
#             return []
        
#         data = resp.json()
#         results = data.get("result", [])
#         dashboards.extend(results)
        
#         if len(results) < page_size:
#             break
#         page += 1
        
#     return dashboards

# def export_dashboard_to_json(session, url, dashboard_id, output_dir):
#     """
#     Exports a single dashboard by ID, extracts the contents from the zip,
#     and saves them as JSON files.
#     """
#     print(f"⬆️ Exporting dashboard with ID {dashboard_id}...")
    
#     # The Superset API expects a rison-encoded list of dashboard IDs in the 'q' parameter.
#     # The format is a rison-encoded array, like: !(1,2,3)
#     query_payload = f"!({dashboard_id})"

#     # We need to URL-encode the Rison string for the GET request
#     from urllib.parse import quote_plus
#     encoded_query = quote_plus(query_payload)

#     export_url = f"{url}/api/v1/dashboard/export/?q={encoded_query}"
#     resp = session.get(export_url)

#     if resp.status_code != 200:
#         print(f"❌ Failed to export dashboard {dashboard_id}. Status: {resp.status_code}")
#         print(f"Response: {resp.text}")
#         return False

#     # Create a directory for this dashboard's files
#     dashboard_name = f"dashboard_{dashboard_id}"
#     output_path = os.path.join(output_dir, dashboard_name)
    
#     # Read the zip file from the response content in memory
#     with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
#         for filename in z.namelist():
#             file_content = z.read(filename).decode('utf-8')
#             file_path = os.path.join(output_path, filename)
            
#             # Ensure the directory exists before writing the file
#             os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
#             with open(file_path, 'w') as f:
#                 f.write(file_content)
    
#     print(f"✅ Successfully exported dashboard {dashboard_id} to {output_path}")
#     return True

# # --- MAIN EXECUTION ---
# if __name__ == "__main__":
#     print("--- Starting Superset Dashboards Export ---")
    
#     # Create the output directory if it doesn't exist
#     os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    
#     # Login to Superset
#     session = login_superset(LOCAL_URL, USERNAME, PASSWORD)
#     if not session:
#         exit()
        
#     print(f"✅ Logged into Superset at {LOCAL_URL}.")
    
#     # Fetch all dashboards
#     dashboards = get_all_dashboards(session, LOCAL_URL)
#     if not dashboards:
#         print("No dashboards found to export.")
#         exit()
        
#     print(f"Found {len(dashboards)} dashboards to export.")
    
#     # Export each dashboard
#     for dashboard in dashboards:
#         export_dashboard_to_json(session, LOCAL_URL, dashboard['id'], OUTPUT_DIRECTORY)
        
#     print("--- Dashboard Export Process Complete ---")
