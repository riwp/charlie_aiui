from flask import Blueprint, redirect, url_for
from apps.common.config import load_app_json_config
from apps.common.lists import handle_generic_list, handle_edit_item, handle_delete_item
from apps.common.collections import (
    handle_generic_collection, 
    handle_edit_collection, 
    handle_delete_collection, 
    handle_reorder_collection
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
        return dict(nav_links=cfg.get("NAV_LINKS", []), app_title=cfg.get("APP_TITLE"))

    @blueprint.route('/')
    def home():
        return redirect(url_for(f"{blueprint_id}.generic_list_view", module_key=default_module_key))

    @blueprint.route('/page/<module_key>', methods=['GET', 'POST'])
    def generic_list_view(module_key):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("MODULE_PAGES", {}).get(module_key)
        if not conf: 
            return redirect('/')
        return handle_generic_list(module_key, conf, f"{blueprint_id}.generic_list_view")

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

    @blueprint.route('/manage/<pagetype>', methods=['GET', 'POST'])
    def manage_notes_view(pagetype):
        cfg = load_app_json_config(app_name)
        conf = cfg.get("NOTE_PAGES", {}).get(pagetype.lower())
        if not conf: 
            return redirect('/')
        return handle_generic_note(pagetype, conf, f"{blueprint_id}.manage_notes_view")

    return blueprint