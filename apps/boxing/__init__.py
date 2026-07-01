import os
import sys
from apps.common.factory import create_app_blueprint
from apps.common.config import load_app_json_config

# 1. Safely grab the app name from the directory structure
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = os.path.basename(CURRENT_DIR)

# 2. Hardcode or safely fallback for the default key during import time
# This stops file system/JSON parsing glitches from breaking blueprint registration!
try:
    config = load_app_json_config(APP_NAME)
    module_pages = config.get("MODULE_PAGES", {})
    default_key = list(module_pages.keys())[0] if module_pages else 'drills'
except Exception as e:
    print(f"⚠️ [Boxing Init] Warning loading config layout, falling back: {e}")
    default_key = 'drills'

# 3. Instantiate the blueprint safely
generated_blueprint = create_app_blueprint(APP_NAME, default_module_key=default_key)

# 4. Inject target variable name dynamically into the module space
target_variable_name = f"{APP_NAME}_blueprint"
setattr(sys.modules[__name__], target_variable_name, generated_blueprint)