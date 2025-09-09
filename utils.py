# superset_utils.py
import os
import subprocess
import zipfile

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
        
        for line in git_status_output.splitlines():
            parts = line.strip().split()
            if len(parts) > 1:
                file_path = parts[1]
                if file_path.startswith(base_dir + "/"):
                    path_parts = file_path.split(os.sep)
                    if len(path_parts) >= 3:  # superset_exports/<type>/<object_x>/...
                        obj_folder = path_parts[2]
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

    objects_root = os.path.join(repo_root, exports_dir)
    output_root = os.path.join(repo_root, zips_dir)
    os.makedirs(output_root, exist_ok=True)

    changed_objects = find_changed_objects(repo_root, exports_dir)

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
