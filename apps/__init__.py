import os
import importlib
from flask import Flask, render_template
from apps.common.config import load_global_config


def debug_display_route_info(app):
    print("--- REGISTERED FLASK ROUTES ---")
    for rule in app.url_map.iter_rules():
        print(f"Path: {rule.rule} -> Endpoint: {rule.endpoint}")
    print("--------------------------------")

def debug_display_additional_info(app):
    # Place this right before app.run() or at the bottom of your main file
    with app.app_context():
        print("\n🔍 --- SHOWING ALL DYNAMIC BLUEPRINT ROUTES ---")
        for rule in app.url_map.iter_rules():
            if 'reorder' in str(rule):
                print(f"👉 MATCH FOUND: {rule.endpoint} | Path: {rule} | Methods: {list(rule.methods)}")
        print("-----------------------------------------------\n")


def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

    # DYNAMIC BLUEPRINT REGISTRATION ENGINE
    # Reads apps from NAV_LINKS and imports them cleanly on the fly
    config = load_global_config()
    for link in config.get("NAV_LINKS", []):
        # FIX: Clean and isolate the base root module name if a sub-path exists
        raw_url = link.get("url", "").strip("/")
        url_route = raw_url.split('/')[0] if '/' in raw_url else raw_url
        
        if not url_route:
            continue
            
        module_name = f"apps.{url_route}"
        
        blueprint_var_name = f"{url_route}_blueprint"
        
        try:
            imported_module = importlib.import_module(module_name)
            blueprint_object = getattr(imported_module, blueprint_var_name)
            app.register_blueprint(blueprint_object)
            print(f"✅ Successfully registered blueprint: {blueprint_var_name} from {module_name}")
        except Exception as e:
            print(f"⚠️ Warning: Could not auto-register blueprint for folder '{url_route}': {e}")

    #debug_display_route_info(app)
    debug_display_additional_info(app)


    @app.context_processor
    def inject_navigation_utilities():
        global_config = load_global_config()
        return dict(
            nav_links=global_config.get("NAV_LINKS", []),
            app_title=global_config.get("APP_TITLE", "Workspace Hub")
        )

    @app.route('/')
    def index():
        global_config = load_global_config()
        page_title = global_config.get("INDEX_TITLE", "Home Dashboard")
        description = global_config.get("INDEX_DESCRIPTION", "Select an isolated subsystem workspace module.")
        
        # Pull cards array directly out of the JSON file safely with a fallback default array
        cards = global_config.get("DASHBOARD_CARDS", [])
        
        return render_template('index.html', index_title=page_title, description=description, cards=cards)

    return app