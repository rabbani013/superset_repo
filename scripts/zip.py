import os
from utils.utils import detect_changed_object_and_create_zip

# =============================
# CONFIGURATION
# =============================
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORTS_BASE_DIR = os.path.join(REPO_ROOT, "superset_exports")
ZIPS_BASE_DIR = os.path.join(REPO_ROOT, ".tmp_zips")

# Map object types to their folders
OBJECTS = {
    # "databases": "databases",
    "datasets": "datasets",
    "charts": "charts",
    "dashboards": "dashboards"
}

# =============================
# MAIN EXECUTION
# =============================
if __name__ == "__main__":
    print("--- Starting Superset Change Detection & ZIP Creation ---\n")

    for object_type, folder_name in OBJECTS.items():
        print(f"--- Processing {object_type} ---")
        # detect_changed_object_and_create_zip(
        #     repo_root=REPO_ROOT,
        #     exports_dir=os.path.join(EXPORTS_BASE_DIR, folder_name),
        #     zips_dir=os.path.join(ZIPS_BASE_DIR, folder_name),
        #     object_type=object_type
        # )
        detect_changed_object_and_create_zip(
            repo_root=REPO_ROOT,
            exports_dir=os.path.join(EXPORTS_BASE_DIR, folder_name),
            zips_dir=os.path.join(ZIPS_BASE_DIR, folder_name),
            object_type=object_type,
            workflow="local"  # optional, default is "local"
        )


    print("\n--- Superset ZIP Creation Complete ---")
