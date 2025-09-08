import os
import requests
import zipfile
import io
from urllib.parse import quote_plus
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =============================
# CONFIGURATION
# =============================
SUPERSET_URL = "http://localhost:8090"
USERNAME = "admin"
PASSWORD = "admin"
OUTPUT_DIRECTORY = "./superset_exports"

# =============================
# FUNCTIONS
# =============================
def login_superset(url, username, password):
    """Logs in and returns an authenticated session object."""
    logging.info(f"🔑 Logging in to Superset at {url} as {username}")
    session = requests.Session()
    try:
        resp = session.post(
            f"{url}/api/v1/security/login",
            json={
                "username": username,
                "password": password,
                "provider": "db",
                "refresh": True
            },
            timeout=10
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        logging.info("✅ Login successful")
        return session
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Login failed: {e}")
        return None

def get_all_dashboards(session, url):
    """Fetches a list of all dashboards and returns their IDs."""
    dashboards = []
    page = 0
    page_size = 100
    logging.info("📋 Fetching dashboards list from Superset...")
    try:
        while True:
            resp = session.get(f"{url}/api/v1/dashboard/?q={{\"page\":{page},\"page_size\":{page_size}}}", timeout=30)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("result", [])
            dashboards.extend(results)
            if len(results) < page_size:
                break
            page += 1
        logging.info(f"✅ Total dashboards fetched: {len(dashboards)}")
        return dashboards
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Failed to fetch dashboards: {e}")
        return []

def export_dashboard_and_save(session, url, dashboard_id, dashboard_title, output_dir):
    """
    Exports a single dashboard and saves all its components as YAML files
    in a dedicated subdirectory.
    """
    logging.info(f"\n⬆️ Exporting dashboard '{dashboard_title}' (ID: {dashboard_id}) as ZIP...")
    query_payload = f"!({dashboard_id})"
    encoded_query = quote_plus(query_payload)
    export_url = f"{url}/api/v1/dashboard/export/?q={encoded_query}"
    
    try:
        resp = session.get(export_url, timeout=60)
        resp.raise_for_status()
        
        # Create a clean folder name for the dashboard
        safe_title = "".join([c for c in dashboard_title if c.isalnum() or c in (' ', '_')]).rstrip().replace(' ', '_')
        dashboard_folder = os.path.join(output_dir, f"{safe_title}_{dashboard_id}")
        os.makedirs(dashboard_folder, exist_ok=True)
        
        # Unzip the content directly into the new folder
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            z.extractall(dashboard_folder)
        
        logging.info(f"✅ Exported components saved to: {dashboard_folder}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Failed to export dashboard {dashboard_id}: {e}")
        return False
    except zipfile.BadZipFile as e:
        logging.error(f"❌ Received a corrupt ZIP file for dashboard {dashboard_id}: {e}")
        return False

# =============================
# MAIN EXECUTION
# =============================
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    
    session = login_superset(SUPERSET_URL, USERNAME, PASSWORD)
    if not session:
        exit()
    
    dashboards_list = get_all_dashboards(session, SUPERSET_URL)
    if not dashboards_list:
        logging.warning("No dashboards found to export.")
        exit()

    for dashboard in dashboards_list:
        export_dashboard_and_save(session, SUPERSET_URL, dashboard['id'], dashboard['dashboard_title'], OUTPUT_DIRECTORY)
        
    logging.info("\n--- All dashboards exported to YAML files. ✅ ---")