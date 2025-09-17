import os
from utils.utils import create_zip_from_dir, login_superset, get_csrf_token, import_zip

# =============================
# CONFIGURATION
# =============================
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORTS_BASE_DIR = os.path.join(REPO_ROOT, "superset_exports")
ZIPS_BASE_DIR = os.path.join(REPO_ROOT, ".tmp_zips")

# Superset connection settings
LOCAL_URL = "http://localhost:8090"
USERNAME = "admin"
PASSWORD = "admin"

# Map object types to their folders
OBJECTS = {
    "datasets": "datasets",
    "charts": "charts",
    "dashboards": "dashboards"
}

def zip_all_objects():
    """Create zip files for ALL objects regardless of git changes"""
    print("--- Starting Superset ALL Objects ZIP Creation ---\n")
    
    total_zipped = 0
    
    for object_type, folder_name in OBJECTS.items():
        print(f"--- Processing ALL {object_type} ---")
        
        exports_dir = os.path.join(EXPORTS_BASE_DIR, folder_name)
        zips_dir = os.path.join(ZIPS_BASE_DIR, folder_name)
        
        # Create zips directory if it doesn't exist
        os.makedirs(zips_dir, exist_ok=True)
        
        if not os.path.exists(exports_dir):
            print(f"⚠️  Exports directory not found: {exports_dir}")
            continue
        
        # Get all object directories
        object_dirs = []
        for item in os.listdir(exports_dir):
            item_path = os.path.join(exports_dir, item)
            if os.path.isdir(item_path):
                object_dirs.append(item)
        
        if not object_dirs:
            print(f"🟠 No {object_type} found in {exports_dir}")
        else:
            print(f"📝 Found {len(object_dirs)} {object_type}:")
            for obj_dir in sorted(object_dirs):
                print(f"  - {obj_dir}")
                
                # Create zip for this object
                object_path = os.path.join(exports_dir, obj_dir)
                output_zip = os.path.join(zips_dir, f"{obj_dir}.zip")
                
                zip_file = create_zip_from_dir(object_path, output_zip)
                if zip_file:
                    print(f"    📦 Created zip: {os.path.basename(zip_file)}")
                    total_zipped += 1
                else:
                    print(f"    ❌ Failed to create zip for {obj_dir}")
        
        print()  # Empty line for readability
    
    print("--- Superset ALL Objects ZIP Creation Complete ---")
    print(f"✅ Total zip files created: {total_zipped}")
    return total_zipped

def import_all_zips():
    """Import all zip files and clean them up after successful import"""
    print("\n--- Starting Superset Universal Import ---")
    
    # Login to Superset
    session = login_superset(LOCAL_URL, USERNAME, PASSWORD)
    if not session:
        print("❌ Failed to login to Superset")
        return False
    
    # Get CSRF token
    csrf_token = get_csrf_token(session, LOCAL_URL)
    if not csrf_token:
        print("❌ Failed to get CSRF token")
        return False
    session.headers.update({"X-CSRFToken": csrf_token})
    
    total_imported = 0
    total_failed = 0
    
    # Import order: datasets -> charts -> dashboards
    items_sequence = [
        ("dataset", os.path.join(ZIPS_BASE_DIR, "datasets")),
        ("chart", os.path.join(ZIPS_BASE_DIR, "charts")),
        ("dashboard", os.path.join(ZIPS_BASE_DIR, "dashboards")),
    ]
    
    for resource_name, folder_path in items_sequence:
        print(f"\n--- Importing {resource_name}s ---")
        
        if not os.path.exists(folder_path):
            print(f"⚠️  {resource_name.capitalize()} directory not found: {folder_path}")
            continue
        
        zip_files = [f for f in os.listdir(folder_path) if f.endswith(".zip")]
        if not zip_files:
            print(f"🟠 No {resource_name} zips found.")
            continue
        
        print(f"📝 Found {len(zip_files)} {resource_name} zip files")
        
        for zip_file in sorted(zip_files):
            zip_path = os.path.join(folder_path, zip_file)
            print(f"⬆️ Importing {resource_name}: {zip_file}")
            
            # Import the zip file
            success, deleted = import_zip(session, LOCAL_URL, zip_path, resource=resource_name)
            
            if success:
                total_imported += 1
                if deleted:
                    print(f"✅ Successfully imported and deleted: {zip_file}")
                else:
                    print(f"✅ Successfully imported: {zip_file}")
            else:
                total_failed += 1
                print(f"❌ Failed to import: {zip_file}")
    
    print("\n--- Superset Universal Import Complete ---")
    print(f"✅ Total successfully imported: {total_imported}")
    if total_failed > 0:
        print(f"❌ Total failed imports: {total_failed}")
    
    return total_failed == 0

def zip_and_import_all():
    """Main function: zip all objects, then import them, then clean up"""
    print("🚀 Starting Complete Zip & Import Process\n")
    
    # Step 1: Create zip files for all objects
    total_zipped = zip_all_objects()
    
    if total_zipped == 0:
        print("🟠 No objects found to zip. Exiting.")
        return
    
    # Step 2: Import all zip files
    import_success = import_all_zips()
    
    if import_success:
        print("\n🎉 Complete process finished successfully!")
        print("✅ All objects zipped, imported, and zip files cleaned up")
    else:
        print("\n⚠️  Import process completed with some failures")
        print("📁 Some zip files may still exist in .tmp_zips/")

# =============================
# MAIN EXECUTION
# =============================
if __name__ == "__main__":
    zip_and_import_all()
