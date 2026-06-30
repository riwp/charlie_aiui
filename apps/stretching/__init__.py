# apps/stretching/__init__.py
from apps.common.factory import create_app_blueprint

# Standardized: App namespace and default module view are now identical
stretching_blueprint = create_app_blueprint('stretching', default_module_key='stretching')