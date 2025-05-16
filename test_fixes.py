#!/usr/bin/env python3
"""
Test script to verify the fixes for the prompt template and model_dump issues.

This script tests:
1. The prompt template parsing with different placeholder formats
2. The model_dump handling in the resume repository
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.models.prompt import PromptTemplate
from app.database.models.resume import ResumeData
from app.database.repositories.prompt_repository import PromptRepository
from app.database.repositories.resume_repository import ResumeRepository
from langchain.prompts import PromptTemplate as LangchainPromptTemplate


async def test_prompt_template():
    """Test the prompt template parsing with different placeholder formats."""
    print("\n=== Testing Prompt Template Parsing ===")
    
    # Test with different placeholder formats
    templates = [
        "Test template with {recommended_skills_section} placeholder",
        "Test template with {{recommended_skills_section}} placeholder",
        "Test template with {{{recommended_skills_section}}} placeholder"
    ]
    
    recommended_skills_section = "RECOMMENDED SKILLS: Python, JavaScript, FastAPI"
    
    for i, template in enumerate(templates):
        print(f"\nTesting template format {i+1}: {template}")
        try:
            # Try with partial variables
            prompt = LangchainPromptTemplate.from_template(
                template=template,
                template_format="jinja2",
                partial_variables={"recommended_skills_section": recommended_skills_section}
            )
            result = prompt.format()
            print(f"Success with partial variables: {result}")
        except Exception as e:
            print(f"Error with partial variables: {e}")
            
            # Try with manual replacement
            try:
                if "{{recommended_skills_section}}" in template:
                    formatted = template.replace("{{recommended_skills_section}}", recommended_skills_section)
                elif "{{{recommended_skills_section}}}" in template:
                    formatted = template.replace("{{{recommended_skills_section}}}", recommended_skills_section)
                elif "{recommended_skills_section}" in template:
                    formatted = template.replace("{recommended_skills_section}", recommended_skills_section)
                
                prompt = LangchainPromptTemplate.from_template(
                    template=formatted,
                    template_format="jinja2"
                )
                result = prompt.format()
                print(f"Success with manual replacement: {result}")
            except Exception as e2:
                print(f"Error with manual replacement: {e2}")


async def test_model_dump_handling():
    """Test the model_dump handling in the resume repository."""
    print("\n=== Testing model_dump Handling ===")
    
    # Set the MongoDB URL directly
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://192.168.7.10:27017/myresumo")
    print(f"Using MongoDB URL: {mongodb_url}")
    
    repo = ResumeRepository(connection_string=mongodb_url)
    
    # Create a test resume ID
    test_id = str(uuid4())
    print(f"Test ID: {test_id}")
    
    # Test with a dictionary
    print("\nTesting with a dictionary...")
    dict_data = {
        "user_information": {
            "name": "Test User",
            "main_job_title": "Software Developer",
            "profile_description": "Test profile",
            "email": "test@example.com",
            "experiences": [],
            "education": [],
            "skills": {
                "hard_skills": ["Python", "JavaScript"],
                "soft_skills": ["Communication"]
            }
        }
    }
    
    try:
        # Convert ObjectId to string for testing
        result = await repo._process_document_for_mongodb({"_id": test_id})
        print(f"Processed document: {result}")
        
        # Test the update_optimized_data method with a dictionary
        result = await repo.update_optimized_data(
            test_id, dict_data, 85,
            original_ats_score=75,
            matching_skills=["Python", "JavaScript"],
            missing_skills=["TypeScript"],
            score_improvement=10,
            recommendation="Test recommendation",
            optimization_summary={"changes_made": ["Test change"]}
        )
        print(f"Result with dictionary: {result}")
    except Exception as e:
        print(f"Error with dictionary: {e}")
    
    # Test with a class that has model_dump
    print("\nTesting with a class that has model_dump...")
    
    class MockModel:
        def model_dump(self):
            return {"mock": "data"}
    
    try:
        mock_model = MockModel()
        result = await repo.update_optimized_data(
            test_id, mock_model, 85,
            original_ats_score=75
        )
        print(f"Result with mock model: {result}")
    except Exception as e:
        print(f"Error with mock model: {e}")
    
    # Test with a class that doesn't have model_dump
    print("\nTesting with a class that doesn't have model_dump...")
    
    class RegularClass:
        def __init__(self):
            self.data = {"regular": "class"}
    
    try:
        regular_class = RegularClass()
        result = await repo.update_optimized_data(
            test_id, regular_class, 85,
            original_ats_score=75
        )
        print(f"Result with regular class: {result}")
    except Exception as e:
        print(f"Error with regular class: {e}")


async def main():
    """Run all tests."""
    print("Starting tests...")
    
    await test_prompt_template()
    await test_model_dump_handling()
    
    print("\nTests completed.")


if __name__ == "__main__":
    asyncio.run(main())
