# apps/common/__init__.py

"""
Common Utilities Package Namespace Configuration.
Exposes global shared services like the Gemini API client and HTML scrapers 
to all isolated application workspace blueprints cleanly.
"""

from .gemini_helper import gemini_bot
from .fetch_html import fetch_html

# Explicitly define what gets exported when using 'from apps.common import *'
__all__ = [
    'gemini_bot',
    'fetch_html'
]
