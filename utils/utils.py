# superset_utils.py
import os
import subprocess
import zipfile
import requests
import re
import json

# ------------------------------
# Git / File Handling Functions
# ------------------------------

def find_changed_objects(repo_root, base_dir):
    """
    Uses Git to find which directories have changed or are newly added inside base_dir.
    Returns a set of unique directory names (e.g., dashboard_9, chart_42).
    """
    changed_dirs = set()
    try:
        abs_base_dir = os.path.abspath(base_dir)

        # 1. Get modified/changed files (staged or unstaged)
        git_status_output = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            text=True
        )

        for line in git_status_output.splitlines():
            parts = line.strip().split()
            if len(parts) > 1:
                file_path = parts[-1]  # last element is always the file path
                abs_file_path = os.path.abspath(os.path.join(repo_root, file_path))

                if abs_file_path.startswith(abs_base_dir + os.sep):
                    rel_path = os.path.relpath(abs_file_path, abs_base_dir)
                    obj_folder = rel_path.split(os.sep)[0]
                    changed_dirs.add(obj_folder)

        # 2. Get untracked (new) files
        git_untracked_output = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=repo_root,
            text=True
        )

        for file_path in git_untracked_output.splitlines():
            abs_file_path = os.path.abspath(os.path.join(repo_root, file_path))

            if abs_file_path.startswith(abs_base_dir + os.sep):
                rel_path = os.path.relpath(abs_file_path, abs_base_dir)
                obj_folder = rel_path.split(os.sep)[0]
                changed_dirs.add(obj_folder)

    except Exception as e:
        print(f"❌ Git command failed: {e}")

    return changed_dirs


def find_objects_changed_after_pull(repo_root, base_dir):
    """
    Detect directories newly added or changed after the last git pull.
    """
    changed_dirs = set()
    try:
        abs_base_dir = os.path.abspath(base_dir)

        # Get all files changed since the previous HEAD (before pull)
        git_diff_output = subprocess.check_output(
            ["git", "log", "HEAD@{1}..HEAD", "--name-only", "--pretty=format:"],
            cwd=repo_root,
            text=True
        )

        for file_path in git_diff_output.splitlines():
            if not file_path.strip():
                continue
            abs_file_path = os.path.abspath(os.path.join(repo_root, file_path))

            if abs_file_path.startswith(abs_base_dir + os.sep):
                rel_path = os.path.relpath(abs_file_path, abs_base_dir)
                obj_folder = rel_path.split(os.sep)[0]
                changed_dirs.add(obj_folder)

    except Exception as e:
        print(f"❌ Git command failed: {e}")

    return changed_dirs


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


# def detect_changed_object_and_create_zip(repo_root, exports_dir, zips_dir, object_type):
#     """
#     Detects changed Superset objects (dashboards/charts), 
#     and creates zip archives for each changed one.
#     """
#     print(f"--- {object_type.capitalize()}'s Zipping Process Started ---")

#     objects_root = exports_dir   # exports_dir should be absolute
#     output_root = zips_dir       # zips_dir should be absolute
#     os.makedirs(output_root, exist_ok=True)

#     changed_objects = find_changed_objects(repo_root, objects_root)

#     if not changed_objects:
#         print(f"✅ No {object_type} changes detected.")
#     else:
#         print(f"📝 Found {len(changed_objects)} changed {object_type}:")
#         for obj in changed_objects:
#             print(f"  - {obj}")
#             object_path = os.path.join(objects_root, obj)
#             output_zip = os.path.join(output_root, f"{obj}.zip")
#             zip_file = create_zip_from_dir(object_path, output_zip)
#             if zip_file:
#                 print(f"📦 Created zip: {zip_file}")

#     print(f"--- {object_type.capitalize()}'s Zipping Process Completed ---\n")

def detect_changed_object_and_create_zip(
    repo_root, exports_dir, zips_dir, object_type, workflow="local"
):
    """
    Detects changed Superset objects (dashboards/charts) and creates zip archives.
    
    Args:
        repo_root (str): Root of the Git repo.
        exports_dir (str): Absolute path to Superset exports folder (dashboards/charts/datasets).
        zips_dir (str): Absolute path to store generated zip files.
        object_type (str): Type of object ("dashboards", "charts", "datasets", etc.)
        workflow (str): "local" for local changes, "pull" for changes after git pull.
    """
    print(f"--- {object_type.capitalize()}'s Zipping Process Started ---")

    objects_root = exports_dir
    output_root = zips_dir
    os.makedirs(output_root, exist_ok=True)

    # Decide which function to use based on workflow
    if workflow == "pull":
        # from utils.git_utils import find_objects_changed_after_pull
        changed_objects = find_objects_changed_after_pull(repo_root, objects_root)
    else:
        # from utils.git_utils import find_changed_objects
        changed_objects = find_changed_objects(repo_root, objects_root)

    if not changed_objects:
        print(f"🟠 No {object_type} changes detected.")
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

    # http://localhost:8090/api/v1/charts/import/?format=json

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


# ------------------------------
# YAML Normalization Functions
# ------------------------------

def deep_sort_json(obj):
    """Recursively sort all keys in a JSON object for consistent ordering"""
    if isinstance(obj, dict):
        return {k: deep_sort_json(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [deep_sort_json(item) for item in obj]
    else:
        return obj


def normalize_json_in_yaml(content):
    """Normalize JSON formatting within YAML content, particularly for query_context fields"""
    lines = content.splitlines()
    normalized_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a query_context field
        if re.match(r'^\s*query_context:\s*\'?\{', line):
            # Find the complete JSON string (may span multiple lines)
            json_lines = [line]
            
            # Check if the JSON is complete on this single line
            if re.search(r'\}\'?\s*$', line):
                # JSON is complete on this line
                pass
            else:
                # JSON spans multiple lines, collect them
                i += 1
                while i < len(lines):
                    current_line = lines[i]
                    json_lines.append(current_line)
                    
                    # Check if this line ends the JSON string
                    if re.search(r'\}\'?\s*$', current_line):
                        break
                    i += 1
            
            # Join the JSON lines and extract the JSON part
            json_text = '\n'.join(json_lines)
            
            # Extract the JSON string from the YAML line
            match = re.match(r'^(\s*query_context:\s*\'?)(.*?)(\'?\s*)$', json_text, re.DOTALL)
            if match:
                prefix = match.group(1)
                json_str = match.group(2)
                suffix = match.group(3)
                
                # Clean up the JSON string - remove any trailing quotes that might be part of the JSON
                if json_str.endswith("'}'"):
                    json_str = json_str[:-2] + "}"
                elif json_str.endswith("'}"):
                    json_str = json_str[:-1] + "}"
                
                try:
                    # Parse and reformat the JSON to ensure consistent formatting
                    json_obj = json.loads(json_str)
                    # Deep sort all keys recursively for consistent ordering
                    json_obj = deep_sort_json(json_obj)
                    # Use compact formatting for consistency
                    normalized_json = json.dumps(json_obj, separators=(',', ':'), sort_keys=True)
                    
                    # Reconstruct the line with normalized JSON
                    normalized_line = prefix + normalized_json + suffix
                    normalized_lines.append(normalized_line)
                except json.JSONDecodeError:
                    # If JSON parsing fails, keep the original
                    normalized_lines.extend(json_lines)
            else:
                # If regex doesn't match, keep the original
                normalized_lines.extend(json_lines)
        else:
            normalized_lines.append(line)
        
        i += 1
    
    return '\n'.join(normalized_lines)


def normalize_yaml_content(content):
    """Normalize YAML content to handle line break differences and Superset field changes"""
    if not content:
        return content
    
    # Remove trailing whitespace from each line
    lines = content.splitlines()
    normalized_lines = [line.rstrip() for line in lines]
    
    # Remove lines that are default empty fields commonly added by Superset
    fields_to_remove = [
        r'^\s*annotation_layers:\s*\[\]\s*$',
        r'^\s*adhoc_filters:\s*\[\]\s*$', 
        r'^\s*dashboards:\s*\[\]\s*$',
        r'^\s*extra_form_data:\s*\{\}\s*$'
    ]
    
    filtered_lines = []
    for line in normalized_lines:
        should_remove = False
        for pattern in fields_to_remove:
            if re.match(pattern, line):
                should_remove = True
                break
        if not should_remove:
            filtered_lines.append(line)
    
    # Join lines and normalize line endings
    normalized_content = '\n'.join(filtered_lines)
    
    # Normalize JSON formatting in query_context field
    # This handles cases where Superset exports JSON in different formats (compact vs pretty-printed)
    normalized_content = normalize_json_in_yaml(normalized_content)
    
    # Remove multiple consecutive empty lines (replace with single empty line)
    normalized_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', normalized_content)
    
    # Remove trailing empty lines (but keep one if the file had content)
    normalized_content = normalized_content.rstrip('\n')
    
    # Ensure file ends with single newline if it had any content
    if normalized_content:
        normalized_content += '\n'
    
    return normalized_content
