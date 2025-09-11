import os
from utils.utils import detect_changed_object_and_create_zip

# Use the script's parent folder as the base, then go to repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if __name__ == "__main__":
    detect_changed_object_and_create_zip(
        REPO_ROOT,
        exports_dir=os.path.join(REPO_ROOT, "dashboards"),         # actual dashboards folder
        zips_dir=os.path.join(REPO_ROOT, ".tmp_zips", "dashboards"), # temp zip folder
        object_type="dashboards"
    )