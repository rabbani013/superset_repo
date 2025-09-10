# import os
# import subprocess
# import zipfile

# # =============================
# # SCRIPT: PACKAGE CHANGED DASHBOARDS
# # =============================

# # Paths
# REPO_ROOT = os.path.abspath(".")  # repo root (~/superset_repo)
# DASHBOARDS_DIR = "superset_exports/dashboards"
# OUTPUT_ZIP_DIR = "superset_exports/zips"

# # --- HELPERS ---

# def find_changed_dashboards(repo_root, dashboards_dir):
#     """
#     Uses Git to find which dashboard directories have been changed.
#     Returns a set of unique dashboard directory names.
#     """
#     changed_dirs = set()
#     try:
#         git_status_output = subprocess.check_output(
#             ["git", "status", "--porcelain"],
#             cwd=repo_root,
#             text=True
#         )
        
#         for line in git_status_output.splitlines():
#             parts = line.strip().split()
#             if len(parts) > 1:
#                 file_path = parts[1]
#                 if file_path.startswith(dashboards_dir + "/"):
#                     path_parts = file_path.split(os.sep)
#                     if len(path_parts) >= 3:  # superset_exports/dashboards/dashboard_9/...
#                         dashboard_folder = path_parts[2]
#                         changed_dirs.add(dashboard_folder)
#     except Exception as e:
#         print(f"❌ Git command failed: {e}")
    
#     return changed_dirs


# def create_zip_from_dir(dashboard_path, output_path):
#     """
#     Creates a zip archive from the given dashboard directory,
#     keeping the top-level folder (e.g., dashboard_9/).
#     """
#     if not os.path.isdir(dashboard_path):
#         print(f"❌ Directory not found: {dashboard_path}")
#         return None

#     base_dir = os.path.dirname(dashboard_path)

#     with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
#         for root, _, files in os.walk(dashboard_path):
#             for file_name in files:
#                 full_path = os.path.join(root, file_name)
#                 # Keep dashboard_9/ prefix in the zip
#                 arcname = os.path.relpath(full_path, base_dir)
#                 zip_file.write(full_path, arcname)
#     return output_path



# # --- MAIN EXECUTION ---
# if __name__ == "__main__":
#     print("--- Packaging Changed Dashboards ---")

#     dashboards_root = os.path.join(REPO_ROOT, DASHBOARDS_DIR)
#     output_root = os.path.join(REPO_ROOT, OUTPUT_ZIP_DIR)
#     os.makedirs(output_root, exist_ok=True)

#     changed_dashboards = find_changed_dashboards(REPO_ROOT, DASHBOARDS_DIR)

#     if not changed_dashboards:
#         print("✅ No dashboard changes detected.")
#     else:
#         print(f"📝 Found {len(changed_dashboards)} changed dashboards:")
#         for d in changed_dashboards:
#             print(f"  - {d}")
#             dashboard_path = os.path.join(dashboards_root, d)
#             output_zip = os.path.join(output_root, f"{d}.zip")
#             zip_file = create_zip_from_dir(dashboard_path, output_zip)
#             if zip_file:
#                 print(f"📦 Created zip: {zip_file}")

#     print("--- Packaging Complete ---")


