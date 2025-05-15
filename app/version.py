"""Version information for the MyResumo application.

This module contains the version information for the MyResumo application.
It is used by various parts of the application to display the version number.
"""

__version__ = "2.0.0"
"""The current version of the application."""

# Version components
VERSION_MAJOR = 2
VERSION_MINOR = 0
VERSION_PATCH = 0

# Full version string
VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

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
