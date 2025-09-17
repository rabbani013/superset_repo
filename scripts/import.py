import os
from utils.utils import login_superset, get_csrf_token, import_zip

# =============================
# CONFIGURATION
# =============================
PROD_URL = os.environ.get("SUPERSET_PROD_URL", "https://5750dff529b5.ngrok-free.app/")
USERNAME = os.environ.get("SUPERSET_ADMIN_USER", "admin")
PASSWORD = os.environ.get("SUPERSET_ADMIN_PASS", "admin")

OUTPUT_BASE_DIR = "./.tmp_zips"  # Folder containing exported zips

# =============================
# HELPER FUNCTION
# =============================
def import_zips_for_resource(session, url, resource_dir, resource_name):
    """Import all zip files in a folder for a given resource type"""
    if not os.path.exists(resource_dir):
        print(f"❌ {resource_name.capitalize()} directory does not exist: {resource_dir}")
        return

    zip_files = [f for f in os.listdir(resource_dir) if f.endswith(".zip")]
    if not zip_files:
        print(f"🟠 No {resource_name} zips found.")
        return

    for zip_file in zip_files:
        print(f"⬆️ Importing {resource_name}: {zip_file}")
        import_zip(session, url, os.path.join(resource_dir, zip_file), resource=resource_name)
    print(f"✅ {resource_name.capitalize()} import complete.\n")

# =============================
# MAIN EXECUTION
# =============================
if __name__ == "__main__":
    print("--- Starting Superset Universal Import ---")

    session = login_superset(PROD_URL, USERNAME, PASSWORD)
    if not session:
        exit()

    csrf_token = get_csrf_token(session, PROD_URL)
    if not csrf_token:
        exit()
    session.headers.update({"X-CSRFToken": csrf_token})

    # Import order: databases -> datasets -> charts -> dashboards
    items_sequence = [
        # ("database", os.path.join(OUTPUT_BASE_DIR, "databases")),
        ("dataset", os.path.join(OUTPUT_BASE_DIR, "datasets")),
        ("chart", os.path.join(OUTPUT_BASE_DIR, "charts")),
        ("dashboard", os.path.join(OUTPUT_BASE_DIR, "dashboards")),
    ]

    for resource_name, folder_path in items_sequence:
        import_zips_for_resource(session, PROD_URL, folder_path, resource_name)

    print("--- Superset Universal Import Complete ---")
