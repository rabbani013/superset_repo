import os
from superset_utils import package_changed_objects

REPO_ROOT = os.path.abspath(".")

if __name__ == "__main__":
    package_changed_objects(
        REPO_ROOT,
        exports_dir="superset_exports/charts",
        zips_dir="superset_zips/charts",
        object_type="charts"
    )
