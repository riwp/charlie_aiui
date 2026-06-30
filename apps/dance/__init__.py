# apps/recipe/__init__.py
from apps.common.factory import create_app_blueprint

# Instantiates all dance and dance routines routing modules automatically!
dance_blueprint = create_app_blueprint('dance', default_module_key='dance')