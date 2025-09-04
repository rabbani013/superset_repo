import os
import json
import requests
import zipfile
import io
import subprocess

# =============================
# SCRIPT 2: IMPORT CHANGED DASHBOARDS FROM GIT
# =============================

# --- CONFIGURATION ---
# IMPORTANT: Update these variables for your production Superset instance
PROD_URL = "https://5750dff529b5.ngrok-free.app"  # Your production Superset URL
USERNAME = "admin"                    # Your production Superset username
PASSWORD = "admin"                    # Your production Superset password
# The root directory containing your dashboard, chart, and dataset folders
SUPSET_EXPORTS_DIR = "./superset_exports/dashboards" 

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
        print(f"❌ Login to {url} failed with status code: {login_resp.status_code}")
        print(f"Response: {login_resp.text}")
        return None
        
    token = login_resp.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session

def get_csrf_token(session, url):
    """
    Fetches the CSRF token from the Superset API.
    """
    try:
        csrf_resp = session.get(f"{url}/api/v1/security/csrf_token/")
        csrf_resp.raise_for_status()
        return csrf_resp.json().get("result")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get CSRF token: {e}")
        return None

def create_zip_from_dir(directory_path):
    """
    Creates an in-memory zip file from the contents of a directory.
    Returns the BytesIO object containing the zip data.
    """
    if not os.path.isdir(directory_path):
        print(f"❌ Error: The directory at {directory_path} was not found.")
        return None

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(directory_path):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                # Create a relative path within the zip file
                zip_file.write(full_path, os.path.relpath(full_path, directory_path))
    
    zip_buffer.seek(0)
    return zip_buffer

def import_dashboard(session, url, directory_path):
    """
    Creates a zip from the directory and imports it into Superset.
    """
    print(f"⬆️ Attempting to import dashboard from directory: {directory_path}...")
    
    zip_buffer = create_zip_from_dir(directory_path)
    if not zip_buffer:
        return False
        
    # Superset's import API requires a multipart form-data request
    files = {
        'formData': (os.path.basename(directory_path) + ".zip", zip_buffer, 'application/zip'),
        'overwrite': (None, 'true')
    }
    
    resp = session.post(f"{url}/api/v1/dashboard/import/", files=files)
    
    if resp.status_code != 200:
        print(f"❌ Failed to import dashboard.")
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        return False
        
    print(f"✅ Successfully imported dashboard.")
    try:
        response_json = resp.json()
        print(f"Response Details: {json.dumps(response_json, indent=2)}")
    except json.JSONDecodeError:
        print("Response was not valid JSON.")
    
    return True

def find_changed_dashboards(superset_exports_dir):
    """
    Uses Git to find which dashboard directories have been changed.
    Returns a set of unique dashboard directory paths.
    """
    changed_dirs = set()
    try:
        # Get a list of all changed or untracked files
        git_status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=superset_exports_dir,
            text=True
        )
        
        for line in git_status_output.splitlines():
            # Extract the path from the git status output (e.g., ' M dashboards/sales_dashboard/dashboard.json')
            parts = line.strip().split()
            if len(parts) > 1:
                file_path = parts[1]
                # Check if the file is within a dashboard directory
                if file_path.startswith("dashboards/"):
                    # Extract the dashboard directory path
                    # e.g., 'dashboards/sales_dashboard'
                    path_parts = file_path.split(os.sep)
                    if len(path_parts) >= 2:
                        changed_dirs.add(os.path.join(superset_exports_dir, path_parts[0], path_parts[1]))

    except FileNotFoundError:
        print("❌ Git command not found. Please ensure Git is installed and in your PATH.")
        return changed_dirs
    except subprocess.CalledProcessError:
        print("❌ Git command failed. Please ensure you are running this script in a Git repository.")
        return changed_dirs
    
    return changed_dirs

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("--- Starting Production Dashboard Import ---")
    
    changed_dashboard_dirs = find_changed_dashboards(SUPSET_EXPORTS_DIR)
    
    if not changed_dashboard_dirs:
        print("✅ No dashboard changes detected. Nothing to import.")
        print("--- Production Import Process Complete ---")
        exit()
        
    print(f"Found {len(changed_dashboard_dirs)} dashboards with changes.")
    
    prod_session = login_superset(PROD_URL, USERNAME, PASSWORD)
    if not prod_session:
        exit()
        
    print(f"✅ Logged into production Superset at {PROD_URL}.")
    
    csrf_token = get_csrf_token(prod_session, PROD_URL)
    if not csrf_token:
        exit()
    
    prod_session.headers.update({"X-CSRFToken": csrf_token})
    print("✅ Fetched and set CSRF token.")
    
    for dashboard_dir in changed_dashboard_dirs:
        import_dashboard(prod_session, PROD_URL, dashboard_dir)
    
    print("--- Production Import Process Complete ---")
