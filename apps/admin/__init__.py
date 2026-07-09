import os
import sys
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from apps.common.factory import create_app_blueprint

# 1. Dynamically discover folder context
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(CURRENT_DIR)
DEFAULT_KEY = "admin_main_config"

# 2. Instantiate the blueprint using the common factory framework
admin_blueprint = create_app_blueprint(APP_NAME, default_module_key=DEFAULT_KEY)

# --- BACKWARD-COMPATIBLE ROUTE HANDLING FOR EXPLICIT admin.html ---
@admin_blueprint.route('/page/admin', methods=['GET'], strict_slashes=False)
@admin_blueprint.route('/page/admin/', methods=['GET'], strict_slashes=False)
def legacy_admin_redirect():
    """Gracefully forwards any old legacy browser bookmarks to the new layout structure."""
    return redirect(url_for('admin_app.generic_list_view', module_key='admin_main_config'))


# --- ADMINISTRATIVE DATABASE MANAGEMENT INTERFACE ENDPOINTS ---

@admin_blueprint.route('/api/config', methods=['GET'])
def get_main_config():
    """Reads the root global system config.json layout matrix."""
    try:
        root_dir = os.path.dirname(os.path.dirname(CURRENT_DIR))
        config_path = os.path.join(root_dir, 'config.json')
        
        if not os.path.exists(config_path):
            return jsonify({"status": "error", "message": "Global system config file not found"}), 404
            
        with open(config_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Read failure: {str(e)}"}), 500


@admin_blueprint.route('/api/config', methods=['POST'])
def save_main_config():
    """Overwrites the root global system config.json layout matrix."""
    try:
        root_dir = os.path.dirname(os.path.dirname(CURRENT_DIR))
        config_path = os.path.join(root_dir, 'config.json')
        
        payload = request.get_json()
        if not payload:
            return jsonify({"status": "error", "message": "Invalid configuration payload data"}), 400
            
        with open(config_path, 'w') as f:
            json.dump(payload, f, indent=4)
            
        return jsonify({"status": "success", "message": "System layout committed to disk successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Write failure: {str(e)}"}), 500


@admin_blueprint.route('/api/apps/list', methods=['GET'])
def list_system_subapps():
    """Scans the directory tree to find editable target apps containing config.json."""
    try:
        apps_dir = os.path.dirname(CURRENT_DIR)
        sub_apps = []
        
        for item in os.listdir(apps_dir):
            item_path = os.path.join(apps_dir, item)
            # Skip common utilities and administrative modules
            if os.path.isdir(item_path) and item not in ['common', 'admin', '__pycache__']:
                conf_file = os.path.join(item_path, 'config.json')
                if os.path.exists(conf_file):
                    sub_apps.append(item)
                    
        return jsonify({"status": "success", "apps": sorted(sub_apps)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@admin_blueprint.route('/api/config/<target_app>', methods=['GET', 'POST'])
def manage_individual_app_config(target_app):
    """Fetches or overwrites the internal config.json file of a chosen sub-app."""
    try:
        apps_dir = os.path.dirname(CURRENT_DIR)
        target_path = os.path.join(apps_dir, target_app, 'config.json')
        
        # Security Guardrail: Prevent escaping directory space bounds
        if not os.path.abspath(target_path).startswith(apps_dir):
            return jsonify({"status": "error", "message": "Access Violation: Target outside scope boundary."}), 403
            
        if request.method == 'GET':
            if not os.path.exists(target_path):
                return jsonify({"status": "error", "message": f"Configuration file not found for app '{target_app}'"}), 404
            with open(target_path, 'r') as f:
                return jsonify(json.load(f))
                
        elif request.method == 'POST':
            payload = request.get_json()
            if not payload:
                return jsonify({"status": "error", "message": "Empty or malformed payload schema."}), 400
                
            with open(target_path, 'w') as f:
                json.dump(payload, f, indent=4)
            return jsonify({"status": "success", "message": f"Configuration for '{target_app}' updated successfully!"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# 4. Export assignments cleanly so your startup scripts can auto-register the hooks
admin_app_blueprint = admin_blueprint
target_variable_name = f"{APP_NAME}_blueprint"
setattr(sys.modules[__name__], target_variable_name, admin_blueprint)