import os
import requests
import zipfile
import logging
import json
import yaml
import io

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =============================
# CONFIGURATION
# =============================
SUPERSET_URL = "https://5750dff529b5.ngrok-free.app"
USERNAME = "admin"
PASSWORD = "admin"
INPUT_DIRECTORY = "./superset_exports"

# =============================
# FUNCTIONS
# =============================
def login_superset(url, username, password):
    """Logs in and returns an authenticated session object."""
    logging.info(f"🔑 Logging in to Superset at {url} as {username}")
    session = requests.Session()
    try:
        resp = session.post(
            f"{url}/api/v1/security/login",
            json={
                "username": username,
                "password": password,
                "provider": "db",
                "refresh": True
            },
            timeout=10
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        logging.info("✅ Login successful")
        return session
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Login failed: {e}")
        return None

def create_zip_from_dir(directory):
    """Creates an in-memory ZIP file from a local directory's contents."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, directory)
                zf.write(file_path, arcname=rel_path)
    buffer.seek(0)
    return buffer

def import_dashboard_zip(session, url, zip_bytes, overwrite=True):
    """Imports a dashboard from an in-memory ZIP file using the authenticated session."""
    import_url = f"{url}/api/v1/dashboard/import/"
    
    files = {'file': ('dashboard_import.zip', zip_bytes, 'application/zip')}
    data = {
        "overwrite": str(overwrite).lower(),
        "import_on_find": "true"
    }
    
    try:
        resp = session.post(import_url, files=files, data=data, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 401:
            logging.error(f"❌ Authentication failed during import. The session might be invalid.")
        else:
            logging.error(f"❌ Failed to import dashboard with HTTP error: {e}")
        logging.error(f"Response: {resp.text}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Request error during import: {e}")
        return None

# =============================
# MAIN EXECUTION
# =============================
if __name__ == "__main__":
    if not os.path.isdir(INPUT_DIRECTORY):
        logging.error(f"❌ Input directory not found: {INPUT_DIRECTORY}")
        exit()

    session = login_superset(SUPERSET_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    dashboard_folders = [f for f in os.listdir(INPUT_DIRECTORY) if os.path.isdir(os.path.join(INPUT_DIRECTORY, f))]

    if not dashboard_folders:
        logging.warning("No dashboard folders found to import.")
        exit()
        
    for folder_name in dashboard_folders:
        folder_path = os.path.join(INPUT_DIRECTORY, folder_name)
        
        # Check if the folder is a valid dashboard directory by looking for a dashboard.yaml file.
        if "dashboard.yaml" in os.listdir(folder_path):
            logging.info(f"\n📦 Preparing to import dashboard from folder: {folder_path}")
            
            zip_buffer = create_zip_from_dir(folder_path)
            
            result = import_dashboard_zip(session, SUPERSET_URL, zip_buffer)
            if result:
                logging.info(f"✅ Successfully imported dashboard from {folder_name}.")
            else:
                logging.error(f"❌ Failed to import dashboard from {folder_name}.")
        else:
            logging.warning(f"⚠️ Skipping folder '{folder_name}' as it does not contain a dashboard.yaml file.")

    logging.info("\n--- All dashboards imported. ✅ ---")