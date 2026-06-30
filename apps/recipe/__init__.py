# apps/recipe/__init__.py
from apps.common.factory import create_app_blueprint

# Instantiates all recipe and cookbook routing modules automatically!
recipe_blueprint = create_app_blueprint('recipe', default_module_key='recipes')