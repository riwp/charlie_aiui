import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_DIR = os.path.join(BASE_DIR, "json")
os.makedirs(JSON_DIR, exist_ok=True)

def load_app_json_config(app_name):
    target_path = os.path.join(BASE_DIR, "apps", app_name, "config.json")
    if os.path.exists(target_path):
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"APP_TITLE": f"{app_name.upper()} Hub", "NAV_LINKS": [], "MODULE_PAGES": {}, "COLLECTION_PAGES": {}, "NOTE_PAGES": {}}

def load_global_config():
    root_cfg = os.path.join(BASE_DIR, "config.json")
    if os.path.exists(root_cfg):
        with open(root_cfg, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"APP_TITLE": "Core Workspace Hub", "NAV_LINKS": []}

def get_json_data_path(filename):
    return os.path.join(JSON_DIR, filename)

def load_json_file(filename):
    target_path = get_json_data_path(filename)
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        if any(k in filename for k in ["note", "journal", "progress", "goals"]):
            return {}
        return []

def save_json_file(filename, data):
    target_path = get_json_data_path(filename)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)