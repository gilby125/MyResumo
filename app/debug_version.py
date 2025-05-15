"""Debug script to verify version information.

This script prints version information to help debug issues with version display.
"""

import os
from app.version import __version__, VERSION, get_version_info

def debug_version():
    """Print version information for debugging."""
    print("\n===== VERSION DEBUG INFORMATION =====")
    print(f"__version__ from app.version: {__version__}")
    print(f"VERSION from app.version: {VERSION}")
    print(f"APP_VERSION environment variable: {os.environ.get('APP_VERSION', 'Not set')}")
    print(f"Version info: {get_version_info()}")
    print("=====================================\n")

# This will be imported and run at application startup
debug_version()
