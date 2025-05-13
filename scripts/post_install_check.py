#!/usr/bin/env python3
"""Post-install environment validation script for MyResumo."""

import os
import sys
import logging
from pathlib import Path
import importlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logs go to stdout for Docker build logs
)
logger = logging.getLogger(__name__)

def log_system_state():
    logger.info(f"Current Working Directory: {os.getcwd()}")
    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    logger.info(f"sys.path: {sys.path}")

    logger.info("Listing /code directory:")
    code_dir = Path("/code")
    if code_dir.exists() and code_dir.is_dir():
        for item in os.listdir(code_dir):
            logger.info(f"  - /code/{item}")
    else:
        logger.error("/code directory does not exist or is not a directory.")

    logger.info("Listing /code/app directory:")
    app_dir = Path("/code/app")
    if app_dir.exists() and app_dir.is_dir():
        for item in os.listdir(app_dir):
            logger.info(f"  - /code/app/{item}")
    else:
        logger.error("/code/app directory does not exist or is not a directory.")

def check_template_files():
    """Verify LaTeX template files exist and are accessible."""
    required_templates = [
        'resume_template.tex',
        'simple_resume_template.tex'
    ]
    template_dir = Path('/code/app/services/resume/latex_templates')

    logger.info(f"Checking template files in {template_dir}")
    missing = []
    for template in required_templates:
        path = template_dir / template
        if not path.exists():
            missing.append(str(path))
            logger.error(f"Missing template: {path}")

    if missing:
        raise SystemExit(f"Error: Missing template files: {', '.join(missing)}")
    logger.info("All template files present")

def check_python_imports():
    """Verify critical Python imports work."""
    imports_to_check = {
        'app.main': "Main application module",
        'app.services.resume.latex_generator': "LaTeX generator service",
        'fastapi': "FastAPI framework",
        'pymongo': "PyMongo MongoDB driver"
    }

    logger.info("Checking Python imports...")
    all_imports_successful = True
    for module_name, description in imports_to_check.items():
        try:
            importlib.import_module(module_name)
            logger.info(f"  Successfully imported '{module_name}' ({description})")
        except ImportError as e:
            logger.error(f"  FAILED to import '{module_name}' ({description}): {e}")
            all_imports_successful = False

    if not all_imports_successful:
        raise SystemExit("One or more critical Python imports failed during build time.")
    logger.info("All critical Python imports successful.")

def check_env_vars():
    """Verify required environment variables are set."""
    required_vars = [
        'MONGODB_URL',
        'API_KEY',
        'PYTHONPATH'
    ]

    logger.info("Checking environment variables")
    missing = []
    for var in required_vars:
        if var not in os.environ:
            missing.append(var)
            logger.error(f"Missing environment variable: {var}")

    if missing:
        raise SystemExit(f"Error: Missing environment variables: {', '.join(missing)}")
    logger.info("All required environment variables present")

def check_directory_structure():
    """Verify critical directory structure exists."""
    required_dirs = [
        '/code/app',
        '/code/app/services/resume/latex_templates',
        '/code/data'
    ]

    logger.info("Checking directory structure")
    missing = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing.append(dir_path)
            logger.error(f"Missing directory: {dir_path}")

    if missing:
        raise SystemExit(f"Error: Missing directories: {', '.join(missing)}")
    logger.info("Directory structure valid")

def main():
    try:
        logger.info("===== Starting MyResumo Post-Install Validation (Build Time) =====")
        log_system_state()
        check_directory_structure()
        check_template_files()
        check_python_imports() # This will try to import app.main
        check_env_vars()
        logger.info("===== MyResumo Post-Install Validation (Build Time) PASSED =====")
    except Exception as e:
        logger.error(f"===== MyResumo Post-Install Validation (Build Time) FAILED: {e} =====")
        sys.exit(1) # Ensure build fails if checks don't pass

if __name__ == '__main__':
    main()