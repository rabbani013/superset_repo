import os
import requests

# -------------------------------
# CONFIGURATION
# -------------------------------
PROD_URL = "https://5750dff529b5.ngrok-free.app"  # Production Superset URL
USERNAME = "admin"
PASSWORD = "admin"

ZIPS_DIR = "./superset_exports/zips"  # Folder containing dashboard zip files

# -------------------------------
# HELPERS
# -------------------------------

def login_superset(url, username, password):
    """Logs in to Superset and returns a session with the access token."""
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
    return session

def get_csrf_token(session, url):
    """Fetches CSRF token from Superset API."""
    try:
        resp = session.get(f"{url}/api/v1/security/csrf_token/")
        resp.raise_for_status()
        return resp.json().get("result")
    except Exception as e:
        print(f"❌ Failed to get CSRF token: {e}")
        return None

def import_zip(session, zip_path):
    """Imports a dashboard zip to Superset and deletes the zip if import succeeds."""
    zip_name = os.path.basename(zip_path)
    print(f"⬆️ Importing {zip_name} ...")
    
    try:
        with open(zip_path, 'rb') as f:
            files = {
                'formData': (zip_name, f, 'application/zip'),
                'overwrite': (None, 'true')
            }
            resp = session.post(f"{PROD_URL}/api/v1/dashboard/import/?format=json", files=files)
        
        if resp.status_code == 200:
            print(f"✅ Successfully imported {zip_name}")
            # Delete the zip file after successful import
            try:
                os.remove(zip_path)
                print(f"🗑️ Deleted zip file: {zip_name}")
                return True, True  # import success, delete success
            except Exception as e:
                print(f"❌ Failed to delete zip file {zip_name}: {e}")
                return True, False  # import success, delete failed
        else:
            print(f"❌ Failed to import {zip_name}: {resp.status_code}")
            print(resp.text)
            return False, False
    except Exception as e:
        print(f"❌ Error importing {zip_name}: {e}")
        return False, False

# -------------------------------
# MAIN EXECUTION
# -------------------------------
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
    total_files = len(zip_files)

    if total_files == 0:
        print("✅ No zip files found to import.")
        exit()

    imported_count = 0
    deleted_count = 0
    failed_imports = []

    for zip_file in zip_files:
        zip_path = os.path.join(ZIPS_DIR, zip_file)
        success_import, success_delete = import_zip(session, zip_path)
        if success_import:
            imported_count += 1
        else:
            failed_imports.append(zip_file)
        if success_delete:
            deleted_count += 1

    # -------------------------------
    # SUMMARY LOG
    # -------------------------------
    print("\n--- Dashboard ZIP Import Summary ---")
    print(f"Total zip files found: {total_files}")
    print(f"Successfully imported: {imported_count}")
    print(f"Zip files deleted: {deleted_count}")
    print(f"Failed imports: {len(failed_imports)}")
    if failed_imports:
        print("Failed zip files:")
        for f in failed_imports:
            print(f" - {f}")
    print("--- Import Process Complete ---")
