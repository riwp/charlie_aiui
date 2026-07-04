from flask import Blueprint, redirect, url_for, request, jsonify, render_template
from apps.common.config import get_json_data_path, load_json_file, save_json_file
import json
import os
from apps.common.config import load_app_json_config
from apps.common.lists import handle_generic_list, handle_edit_item, handle_delete_item
from apps.common.collections import (
    handle_generic_collection, 
    handle_edit_collection, 
    handle_delete_collection, 
    handle_reorder_collection,
    handle_reorder_collection_items
)
from apps.common.notes import handle_generic_note

def create_app_blueprint(app_name, default_module_key='items'):
    """
    Dynamically generates a functional Flask Blueprint based on a configuration key.
    """
    blueprint_id = f"{app_name}_app"
    blueprint = Blueprint(blueprint_id, __name__, url_prefix=f"/{app_name}")

    @blueprint.context_processor
    def inject_context():
        cfg = load_app_json_config(app_name)
        raw_nav_links = cfg.get("NAV_LINKS", [])
        
        dynamic_nav_links = []
        for link in raw_nav_links:
            raw_url = link.get("url", "").lstrip('/')
            dynamic_nav_links.append({
                "name": link.get("name"),
                "url": f"/{app_name}/{raw_url}"
            })

        return dict(nav_links=dynamic_nav_links, app_title=cfg.get("APP_TITLE"))

    @blueprint.route('/')
    def home():
        return redirect(url_for(f"{blueprint_id}.generic_list_view", module_key=default_module_key))

    @blueprint.route('/page/<module_key>', methods=['GET', 'POST'])
    def generic_list_view(module_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("MODULE_PAGES", {}).get(module_key)
        if not conf: 
            return redirect('/')
            
        # --- FIXED FORWARD SAFETY LAYER ---
        # If the page configuration does not point to an internal JSON database backing matrix,
        # fallback cleanly to rendering a custom template matching the target page key entry name.
        if "db_file" not in conf and "data_file" not in conf:
            # This handles custom templates like admin.html natively while remaining 100% generic
            return render_template(f"{module_key}.html", conf=conf)
            
        return handle_generic_list(module_key, conf, f"{blueprint_id}.generic_list_view")

    @blueprint.route('/page/<module_key>/reorder', methods=['POST'], strict_slashes=False)
    @blueprint.route('/page/<module_key>/reorder/', methods=['POST'], strict_slashes=False)
    def reorder_list_items_view(module_key):
        print(f"💥 HIT DETECTED! Module: {module_key} | App: {app_name}")
        
        cfg = load_app_json_config(app_name)
        conf = cfg.get("MODULE_PAGES", {}).get(module_key)
        if not conf:
            print(f"❌ CONFIG ERROR: Could not find '{module_key}' inside MODULE_PAGES configuration dictionary.")
            return jsonify({"status": "error", "message": "Configuration mismatch profiles."}), 404
            
        raw_filename = conf.get('data_file') or conf.get('db_file')
        if not raw_filename:
            print(f"❌ CONFIG ERROR: Missing 'data_file' or 'db_file' key entry for module '{module_key}'.")
            return jsonify({"status": "error", "message": "No data file string found in config."}), 404

        data_file_path = get_json_data_path(raw_filename)
        print(f"🔍 DEBUG PATH ANALYSIS: Python is looking for your file at:\n👉 {data_file_path}")
        
        if not os.path.exists(data_file_path):
            print(f"❌ DISK FILE MISSING: File does not exist at the resolved absolute path above.")
            return jsonify({"status": "error", "message": f"Target data storage file missing at: {raw_filename}"}), 404

        payload = request.get_json() or {}
        ordered_ids = payload.get('order', [])
        if not ordered_ids:
            return jsonify({"status": "error", "message": "No item sort order layout array provided."}), 400

        try:
            items = load_json_file(raw_filename)
            items_by_id = {str(item.get('id')): item for item in items if item.get('id') is not None}
            
            reordered_list = []
            for item_id in ordered_ids:
                str_id = str(item_id)
                if str_id in items_by_id:
                    reordered_list.append(items_by_id[str_id])
            
            for item in items:
                if str(item.get('id')) not in ordered_ids:
                    reordered_list.append(item)
                    
            save_json_file(raw_filename, reordered_list)
            print(f"✨ SUCCESS: List elements reordered and saved for module '{module_key}'!")
            
            return jsonify({"status": "success", "message": "Items reordered successfully."})
            
        except Exception as e:
            print(f"❌ WRITE ERROR: Could not reorder items payload correctly. Details: {str(e)}")
            return jsonify({"status": "error", "message": f"Server failed to write update: {str(e)}"}), 500        

    @blueprint.route('/page/<module_key>/edit', methods=['POST'])
    def edit_list_item_view(module_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("MODULE_PAGES", {}).get(module_key)
        if conf: 
            handle_edit_item(module_key, conf)
        return redirect(url_for(f"{blueprint_id}.generic_list_view", module_key=module_key))

    @blueprint.route('/page/<module_key>/delete', methods=['POST'])
    def delete_list_item_view(module_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("MODULE_PAGES", {}).get(module_key)
        if conf: 
            handle_delete_item(module_key, conf)
        return redirect(url_for(f"{blueprint_id}.generic_list_view", module_key=module_key))

    @blueprint.route('/collection/<collection_key>', methods=['GET', 'POST'])
    def generic_collection_view(collection_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("COLLECTION_PAGES", {}).get(collection_key)
        if not conf: 
            return redirect('/')
        source_conf = cfg.get("MODULE_PAGES", {}).get(conf.get("source_module"))
        return handle_generic_collection(collection_key, conf, source_conf, f"{blueprint_id}.generic_collection_view")

    @blueprint.route('/collection/<collection_key>/edit', methods=['POST'])
    def edit_collection_view(collection_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("COLLECTION_PAGES", {}).get(collection_key)
        if conf: 
            handle_edit_collection(collection_key, conf)
        return redirect(url_for(f"{blueprint_id}.generic_collection_view", collection_key=collection_key))

    @blueprint.route('/collection/<collection_key>/delete', methods=['POST'])
    def delete_collection_view(collection_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("COLLECTION_PAGES", {}).get(collection_key)
        if conf: 
            handle_delete_collection(collection_key, conf)
        return redirect(url_for(f"{blueprint_id}.generic_collection_view", collection_key=collection_key))

    @blueprint.route('/collection/<collection_key>/reorder', methods=['POST'])
    def reorder_collection_view(collection_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("COLLECTION_PAGES", {}).get(collection_key)
        if not conf:
            return {"status": "error", "message": "Configuration mismatch profiles."}, 404
        return handle_reorder_collection(collection_key, conf)

    @blueprint.route('/collection/<collection_key>/items/reorder', methods=['POST'])
    def reorder_collection_items_view(collection_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("COLLECTION_PAGES", {}).get(collection_key)
        if not conf:
            return {"status": "error", "message": "Configuration mismatch profiles."}, 404
        return handle_reorder_collection_items(collection_key, conf)

    @blueprint.route('/manage/<pagetype>', methods=['GET', 'POST'])
    def manage_notes_view(pagetype):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("NOTE_PAGES", {}).get(pagetype.lower())
        if not conf: 
            return redirect('/')
        return handle_generic_note(pagetype, conf, f"{blueprint_id}.manage_notes_view")

    return blueprint