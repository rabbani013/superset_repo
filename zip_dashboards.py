import os
from utils import detect_changed_object_and_create_zip

REPO_ROOT = os.path.abspath(".")

if __name__ == "__main__":
    detect_changed_object_and_create_zip(
        REPO_ROOT,
        exports_dir="superset_exports/dashboards",
        zips_dir="superset_imports/zips/dashboards",
        object_type="dashboards"
    )
