import os
import sys
from apps.common.factory import create_app_blueprint
from apps.common.config import load_app_json_config
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import json

# 1. Dynamically discover folder name (e.g., "admin")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(CURRENT_DIR)

# 2. Hardcode or dynamically extract "admin" to align with MODULE_PAGES key
DEFAULT_KEY = "admin"

# 3. Instantiate the blueprint via common factory component
generated_blueprint = create_app_blueprint(APP_NAME, default_module_key=DEFAULT_KEY)

# 4. Inject variable matching your system's global system expectation
target_variable_name = f"{APP_NAME}_blueprint"
setattr(sys.modules[__name__], target_variable_name, generated_blueprint)

# Add these endpoints towards the bottom of apps/admin/__init__.py, right above your target_variable_name injection

@generated_blueprint.route('/api/config', methods=['GET'])
def get_main_config():
    """Reads the root global system config file."""
    try:
        # Navigate out of apps/admin/ up to the root folder level
        root_dir = os.path.dirname(os.path.dirname(CURRENT_DIR))
        config_path = os.path.join(root_dir, 'config.json')
        
        if not os.path.exists(config_path):
            return jsonify({"status": "error", "message": "Config file not found"}), 404
            
        with open(config_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@generated_blueprint.route('/api/config', methods=['POST'])
def save_main_config():
    """Overwrites the root global system config file safely."""
    try:
        root_dir = os.path.dirname(os.path.dirname(CURRENT_DIR))
        config_path = os.path.join(root_dir, 'config.json')
        
        payload = request.get_json()
        if not payload:
            return jsonify({"status": "error", "message": "Invalid configuration payload"}), 400
            
        with open(config_path, 'w') as f:
            json.dump(payload, f, indent=4)
            
        return jsonify({"status": "success", "message": "System configurations saved successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    