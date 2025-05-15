#!/usr/bin/env python3
"""
Test script for the LaTeX download functionality.

This script tests the LaTeX download functionality by:
1. Getting a list of resumes from the dashboard
2. Selecting a resume that has been optimized
3. Downloading the resume in LaTeX format
4. Verifying that the LaTeX content is valid
"""

import requests
import sys
import re
import os
from pathlib import Path

# Configuration
BASE_URL = "http://192.168.7.10:32811"  # Update this with your server URL
DOWNLOAD_DIR = Path("./downloads")

def setup():
    """Set up the test environment."""
    # Create download directory if it doesn't exist
    DOWNLOAD_DIR.mkdir(exist_ok=True)
    print(f"Download directory: {DOWNLOAD_DIR.absolute()}")

def get_resumes():
    """Get a list of resumes from the dashboard."""
    try:
        response = requests.get(f"{BASE_URL}/dashboard")
        if response.status_code != 200:
            print(f"Failed to get dashboard: {response.status_code}")
            return None
        
        # Extract resume IDs from the HTML
        resume_ids = re.findall(r'data-resume-id="([^"]+)"', response.text)
        if not resume_ids:
            print("No resumes found on the dashboard")
            return None
        
        print(f"Found {len(resume_ids)} resumes: {resume_ids}")
        return resume_ids
    except Exception as e:
        print(f"Error getting resumes: {e}")
        return None

def get_resume_details(resume_id):
    """Get details for a specific resume."""
    try:
        response = requests.get(f"{BASE_URL}/api/resume/{resume_id}")
        if response.status_code != 200:
            print(f"Failed to get resume details: {response.status_code}")
            return None
        
        resume_data = response.json()
        has_optimized = "optimized_data" in resume_data and resume_data["optimized_data"]
        print(f"Resume {resume_id} - Title: {resume_data.get('title')}, Optimized: {has_optimized}")
        return resume_data
    except Exception as e:
        print(f"Error getting resume details: {e}")
        return None

def download_latex(resume_id):
    """Download the resume in LaTeX format."""
    try:
        response = requests.get(f"{BASE_URL}/api/resume/{resume_id}/download-latex")
        if response.status_code != 200:
            print(f"Failed to download LaTeX: {response.status_code}")
            return None
        
        # Check content type
        content_type = response.headers.get("content-type")
        if content_type != "application/x-latex":
            print(f"Unexpected content type: {content_type}")
            return None
        
        # Save the LaTeX content to a file
        filename = f"resume_{resume_id}.tex"
        file_path = DOWNLOAD_DIR / filename
        with open(file_path, "wb") as f:
            f.write(response.content)
        
        print(f"LaTeX file saved to {file_path}")
        return file_path
    except Exception as e:
        print(f"Error downloading LaTeX: {e}")
        return None

def verify_latex(file_path):
    """Verify that the LaTeX content is valid."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for basic LaTeX structure
        if not "\\documentclass" in content:
            print("LaTeX content is missing \\documentclass")
            return False
        
        if not "\\begin{document}" in content:
            print("LaTeX content is missing \\begin{document}")
            return False
        
        if not "\\end{document}" in content:
            print("LaTeX content is missing \\end{document}")
            return False
        
        print("LaTeX content appears to be valid")
        return True
    except Exception as e:
        print(f"Error verifying LaTeX: {e}")
        return False

def main():
    """Main function."""
    setup()
    
    # Get resumes
    resume_ids = get_resumes()
    if not resume_ids:
        print("No resumes found. Test failed.")
        return False
    
    # Find an optimized resume
    optimized_resume_id = None
    for resume_id in resume_ids:
        resume_data = get_resume_details(resume_id)
        if resume_data and "optimized_data" in resume_data and resume_data["optimized_data"]:
            optimized_resume_id = resume_id
            break
    
    if not optimized_resume_id:
        print("No optimized resumes found. Test failed.")
        return False
    
    # Download LaTeX
    latex_file = download_latex(optimized_resume_id)
    if not latex_file:
        print("Failed to download LaTeX. Test failed.")
        return False
    
    # Verify LaTeX
    if not verify_latex(latex_file):
        print("LaTeX verification failed. Test failed.")
        return False
    
    print("Test passed! LaTeX download functionality is working correctly.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
