import os
import sys
from apps.common.factory import create_app_blueprint
from apps.common.config import load_app_json_config

# 1. Dynamically discover folder name ("charlie")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(CURRENT_DIR)

# 2. Dynamically extract the first available key from MODULE_PAGES
try:
    config = load_app_json_config(APP_NAME)
    module_pages = config.get("MODULE_PAGES", {})
    default_key = list(module_pages.keys())[0] if module_pages else 'items'
except Exception:
    default_key = 'items'

# 3. Instantiate the blueprint
generated_blueprint = create_app_blueprint(APP_NAME, default_module_key=default_key)

# 4. Inject variable matching your system's expectation (e.g., charlie_blueprint)
target_variable_name = f"{APP_NAME}_blueprint"
setattr(sys.modules[__name__], target_variable_name, generated_blueprint)