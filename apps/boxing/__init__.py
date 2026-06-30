# apps/boxing/__init__.py
from apps.common.factory import create_app_blueprint

# Instantiates all list, collection, and note routes automatically!
boxing_blueprint = create_app_blueprint('boxing', default_module_key='drills')