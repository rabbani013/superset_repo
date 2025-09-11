# superset_utils.py
import os
import subprocess
import zipfile
import requests

# ------------------------------
# Git / File Handling Functions
# ------------------------------

def find_changed_objects(repo_root, base_dir):
    """
    Uses Git to find which directories have changed inside base_dir.
    Returns a set of unique directory names (e.g., dashboard_9, chart_42).
    """
    changed_dirs = set()
    try:
        git_status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            text=True
        )

        abs_base_dir = os.path.abspath(base_dir)

        for line in git_status_output.splitlines():
            parts = line.strip().split()
            if len(parts) > 1:
                file_path = parts[1]
                abs_file_path = os.path.abspath(os.path.join(repo_root, file_path))

                # Check if the changed file is under the base directory
                if abs_file_path.startswith(abs_base_dir + os.sep):
                    # Get the top-level folder name under base_dir
                    rel_path = os.path.relpath(abs_file_path, abs_base_dir)
                    obj_folder = rel_path.split(os.sep)[0]
                    changed_dirs.add(obj_folder)

    except Exception as e:
        print(f"❌ Git command failed: {e}")

    return changed_dirs


def create_zip_from_dir(object_path, output_path):
    """
    Creates a zip archive from the given object directory,
    keeping the top-level folder (e.g., dashboard_9/ or chart_12/).
    """
    if not os.path.isdir(object_path):
        print(f"❌ Directory not found: {object_path}")
        return None

    base_dir = os.path.dirname(object_path)

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(object_path):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                # Keep dashboard_x/ or chart_x/ prefix in the zip
                arcname = os.path.relpath(full_path, base_dir)
                zip_file.write(full_path, arcname)

    return output_path


def detect_changed_object_and_create_zip(repo_root, exports_dir, zips_dir, object_type):
    """
    Detects changed Superset objects (dashboards/charts), 
    and creates zip archives for each changed one.
    """
    print(f"--- {object_type.capitalize()}'s Zipping Process Started ---")

    objects_root = exports_dir   # exports_dir should be absolute
    output_root = zips_dir       # zips_dir should be absolute
    os.makedirs(output_root, exist_ok=True)

    changed_objects = find_changed_objects(repo_root, objects_root)

    if not changed_objects:
        print(f"✅ No {object_type} changes detected.")
    else:
        print(f"📝 Found {len(changed_objects)} changed {object_type}:")
        for obj in changed_objects:
            print(f"  - {obj}")
            object_path = os.path.join(objects_root, obj)
            output_zip = os.path.join(output_root, f"{obj}.zip")
            zip_file = create_zip_from_dir(object_path, output_zip)
            if zip_file:
                print(f"📦 Created zip: {zip_file}")

    print(f"--- {object_type.capitalize()}'s Zipping Process Completed ---\n")


# ------------------------------
# Superset API Functions
# ------------------------------

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


def import_zip(session, prod_url, zip_path, resource="dashboard"):
    """
    Imports a Superset object (dashboard/chart) zip file to Superset
    and deletes the zip if import succeeds.
    """
    zip_name = os.path.basename(zip_path)
    print(f"⬆️ Importing {zip_name} as {resource} ...")

    endpoint = f"{prod_url}/api/v1/{resource}/import/?format=json"

    try:
        with open(zip_path, 'rb') as f:
            files = {
                'formData': (zip_name, f, 'application/zip'),
                'overwrite': (None, 'true')
            }
            resp = session.post(endpoint, files=files)

        if resp.status_code == 200:
            print(f"✅ Successfully imported {zip_name}")
            try:
                os.remove(zip_path)
                print(f"🗑️ Deleted zip file: {zip_name}")
                return True, True
            except Exception as e:
                print(f"❌ Failed to delete zip file {zip_name}: {e}")
                return True, False
        else:
            print(f"❌ Failed to import {zip_name}: {resp.status_code}")
            print(resp.text)
            return False, False
    except Exception as e:
        print(f"❌ Error importing {zip_name}: {e}")
        return False, False
