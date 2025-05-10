#!/usr/bin/env python3
"""Post-install environment validation script for MyResumo."""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    imports = [
        'app.main',
        'app.services.resume.latex_generator',
        'fastapi',
        'pymongo'
    ]
    
    logger.info("Checking Python imports")
    for imp in imports:
        try:
            __import__(imp)
            logger.info(f"Import successful: {imp}")
        except ImportError as e:
            raise SystemExit(f"Import failed for {imp}: {str(e)}")

def check_env_vars():
    """Verify required environment variables are set."""
    required_vars = [
        'MONGODB_URI',
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
        logger.info("Starting MyResumo post-install validation")
        check_directory_structure()
        check_template_files()
        check_python_imports()
        check_env_vars()
        logger.info("All post-install checks passed successfully")
    except Exception as e:
        logger.error(f"Post-install validation failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()