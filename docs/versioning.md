# Versioning System

MyResumo uses semantic versioning (SemVer) for version management. This document explains how the versioning system works and how to use it.

## Semantic Versioning

We follow the [Semantic Versioning 2.0.0](https://semver.org/) specification. Version numbers are in the format of `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incremented for incompatible API changes
- **MINOR**: Incremented for new functionality in a backward-compatible manner
- **PATCH**: Incremented for backward-compatible bug fixes

## Version Files

The version is stored in multiple places to ensure consistency:

1. `app/version.py` - The central version file
2. `pyproject.toml` - Poetry package version
3. `app/__init__.py` - Python package version
4. `package.json` - Node.js package version

The `app/version.py` file is the source of truth for the application version.

## Automatic Version Bumping

We use GitHub Actions and python-semantic-release to automatically bump the version based on commit messages. The workflow is defined in `.github/workflows/version-bump.yml`.

### How It Works

1. When code is pushed to the `main` branch, the workflow checks the commit messages
2. Based on the commit messages, it determines whether to bump the major, minor, or patch version
3. It updates all version files and creates a new Git tag
4. It creates a GitHub release with the changelog

### Commit Message Format

We use the Angular commit message format to determine the version bump:

- `fix: ...` - Patch version bump (bug fixes)
- `feat: ...` - Minor version bump (new features)
- `feat!: ...` or `fix!: ...` or any commit with `BREAKING CHANGE:` in the body - Major version bump

Examples:
- `fix: correct typo in homepage` - Bumps patch version (e.g., 1.0.0 -> 1.0.1)
- `feat: add new resume template` - Bumps minor version (e.g., 1.0.1 -> 1.1.0)
- `feat!: redesign API endpoints` - Bumps major version (e.g., 1.1.0 -> 2.0.0)

## Manual Version Updates

In case you need to update the version manually:

1. Update `app/version.py`
2. Update `pyproject.toml`
3. Update `app/__init__.py`
4. Update `package.json`

Then commit with a message like `chore(release): update version to X.Y.Z`.

## Displaying the Version

The application version is displayed in the footer of every page. It's also available in the `/health` endpoint response.

## Version Information in Code

To access the version in code:

```python
from app.version import __version__, get_version_info

# Get the version string
print(__version__)  # e.g., "2.0.0"

# Get detailed version information
version_info = get_version_info()
print(version_info)  # Dictionary with version components
```
