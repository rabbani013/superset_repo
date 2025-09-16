import os
import subprocess
from utils.utils import (
    detect_changed_object_and_create_zip,
    login_superset,
    get_csrf_token,
    import_zip
)

# =============================
# CONFIGURATION
# =============================
DEV_URL = os.environ.get("SUPERSET_DEV_URL", "http://localhost:8090")
USERNAME = os.environ.get("SUPERSET_ADMIN_USER", "admin")
PASSWORD = os.environ.get("SUPERSET_ADMIN_PASS", "admin")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORTS_DIR = os.path.join(REPO_ROOT, "superset_exports")   # folders with exported objects
ZIPS_DIR = os.path.join(REPO_ROOT, ".tmp_zips")             # temporary folder for zips

# Keep folder names plural, map to API singular names
RESOURCE_API_MAP = {
    "datasets": "dataset",
    "charts": "chart",
    "dashboards": "dashboard"
}

# =============================
# MAIN EXECUTION
# =============================
if __name__ == "__main__":
    print("🟢 Git → Dev Sync Started ---\n")

    # Step 0: Pull latest changes from Git
    try:
        print("🔄 Running git pull ...")
        subprocess.check_call(["git", "pull", "origin", "main"], cwd=REPO_ROOT)
        print("✅ Git pull complete")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git pull failed: {e}")
        exit(1)

    # Step 1: Detect new/changed objects and create zips
    for folder_name in RESOURCE_API_MAP.keys():
        detect_changed_object_and_create_zip(
            repo_root=REPO_ROOT,
            exports_dir=os.path.join(EXPORTS_DIR, folder_name),
            zips_dir=os.path.join(ZIPS_DIR, folder_name),
            object_type=folder_name,
            workflow="pull"  # detect changes after git pull
        )

    # Step 2: Login to Superset Dev
    session = login_superset(DEV_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    csrf_token = get_csrf_token(session, DEV_URL)
    if not csrf_token:
        exit()
    session.headers.update({"X-CSRFToken": csrf_token})

    # Step 3: Import zips into Dev
    for folder_name, api_resource_name in RESOURCE_API_MAP.items():
        resource_dir = os.path.join(ZIPS_DIR, folder_name)
        if not os.path.exists(resource_dir):
            continue

        zip_files = [f for f in os.listdir(resource_dir) if f.endswith(".zip")]
        if not zip_files:
            print(f"🟠 No {folder_name} zips found.")
            continue

        for zip_file in zip_files:
            print(f"⬆️ Importing {folder_name}: {zip_file}")
            import_zip(session, DEV_URL, os.path.join(resource_dir, zip_file), resource=api_resource_name)

    print("\n✅ Git → Dev Sync Complete ---")










# import os
# from utils.utils import detect_changed_object_and_create_zip , login_superset, get_csrf_token, import_zip

# # =============================
# # CONFIGURATION
# # =============================
# DEV_URL = os.environ.get("SUPERSET_DEV_URL", "http://localhost:8090")
# USERNAME = os.environ.get("SUPERSET_ADMIN_USER", "admin")
# PASSWORD = os.environ.get("SUPERSET_ADMIN_PASS", "admin")

# REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# EXPORTS_DIR = os.path.join(REPO_ROOT, "superset_exports")   # repo folders
# ZIPS_DIR = os.path.join(REPO_ROOT, ".tmp_zips")             # zips temp

# # =============================
# # MAIN EXECUTION
# # =============================
# if __name__ == "__main__":
#     print("--- Git → Dev Sync Started ---")

#     # Step 1: Detect new/changed objects and create zips
#     resources = [
#         "databases", 
#         "datasets", 
#         "charts", 
#         "dashboards"
#     ]

#     for resource in resources:
#         detect_changed_object_and_create_zip(
#             repo_root=REPO_ROOT,
#             exports_dir=os.path.join(EXPORTS_DIR, resource),
#             zips_dir=os.path.join(ZIPS_DIR, resource),
#             object_type=resource,
#             workflow="pull"  # detect changes after git pull
#         )


#     # Step 2: Login to Superset Dev
#     session = login_superset(DEV_URL, USERNAME, PASSWORD)
#     if not session:
#         exit()

#     csrf_token = get_csrf_token(session, DEV_URL)
#     if not csrf_token:
#         exit()
#     session.headers.update({"X-CSRFToken": csrf_token})

#     # Step 3: Import zips into Dev
#     for resource in resources:
#         resource_dir = os.path.join(ZIPS_DIR, resource)
#         if not os.path.exists(resource_dir):
#             continue

#         zip_files = [f for f in os.listdir(resource_dir) if f.endswith(".zip")]
#         if not zip_files:
#             print(f"✅ No {resource} zips found.")
#             continue

#         for zip_file in zip_files:
#             print(f"⬆️ Importing {resource}: {zip_file}")
#             import_zip(session, DEV_URL, os.path.join(resource_dir, zip_file), resource=resource)

#     print("--- Git → Dev Sync Complete ---")
