"""Version information for the MyResumo application.

This module contains the version information for the MyResumo application.
It is used by various parts of the application to display the version number.
"""

import os

# Get version from environment variable if available
__version__ = os.environ.get("APP_VERSION", "2.0.0")
"""The current version of the application."""

# Try to parse version components
try:
    version_parts = __version__.split('.')
    VERSION_MAJOR = int(version_parts[0]) if len(version_parts) > 0 else 2
    VERSION_MINOR = int(version_parts[1]) if len(version_parts) > 1 else 0
    VERSION_PATCH = int(version_parts[2]) if len(version_parts) > 2 else 0
except (ValueError, IndexError):
    # If parsing fails, use default values
    VERSION_MAJOR = 2
    VERSION_MINOR = 0
    VERSION_PATCH = 0

# Full version string
VERSION = __version__

# Build information - these will be populated by CI/CD
BUILD_DATE = None
GIT_COMMIT = None
GIT_BRANCH = None

def get_version_info():
    """Get the full version information as a dictionary.

    Returns:
        dict: A dictionary containing version information
    """
    return {
        "version": VERSION,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "build_date": BUILD_DATE,
        "git_commit": GIT_COMMIT,
        "git_branch": GIT_BRANCH
    }

def get_version_string():
    """Get the version as a string.

    Returns:
        str: The version string
    """
    return VERSION
