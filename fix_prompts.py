#!/usr/bin/env python3
"""
Script to fix the resume_optimization prompt in the database.

This script updates the resume_optimization prompt in the database to ensure
it uses the correct format for the recommended_skills_section placeholder.
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.repositories.prompt_repository import PromptRepository


async def fix_resume_optimization_prompt():
    """Fix the resume_optimization prompt in the database."""
    print("Starting prompt fix script...")

    # Set the MongoDB URL directly
    mongodb_url = "mongodb://192.168.7.10:27017/myresumo"
    print(f"Using MongoDB URL: {mongodb_url}")

    repo = PromptRepository(connection_string=mongodb_url)

    # Get the resume_optimization prompt
    prompt = await repo.get_prompt_by_name("resume_optimization")

    if not prompt:
        print("Resume optimization prompt not found in database.")
        return

    print(f"Found resume_optimization prompt with ID: {prompt.get('id')}")

    # Check if the template contains the problematic placeholder
    template = prompt.get("template", "")

    if "{recommended_skills_section}" in template:
        print("Found problematic placeholder in template. Fixing...")

        # Replace the placeholder with double curly braces
        fixed_template = template.replace("{recommended_skills_section}", "{{recommended_skills_section}}")

        # Update the prompt in the database
        from app.database.models.prompt import PromptUpdate

        update_data = PromptUpdate(
            template=fixed_template,
            # Update the variables list to remove recommended_skills_section
            variables=["job_description", "resume"],
            # Update the timestamp and version
            updated_at=datetime.now(),
            version=prompt.get("version", 1) + 1
        )

        success = await repo.update_prompt(prompt.get("id"), update_data)

        if success:
            print("Successfully updated resume_optimization prompt.")
        else:
            print("Failed to update resume_optimization prompt.")
    else:
        print("Template does not contain the problematic placeholder. No fix needed.")


if __name__ == "__main__":
    asyncio.run(fix_resume_optimization_prompt())
