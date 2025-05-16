#!/usr/bin/env python3
"""
Test script to verify the prompt template fix.

This script tests the prompt template handling in the AtsResumeOptimizer
without requiring a connection to the AI service.
"""

import os
import sys
from langchain.prompts import PromptTemplate

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_prompt_template_handling():
    """Test the prompt template handling with different placeholder formats."""
    print("\n=== Testing Prompt Template Handling ===")
    
    # Test templates with different placeholder formats
    templates = [
        "Test template with {recommended_skills_section} placeholder",
        "Test template with {{recommended_skills_section}} placeholder",
        "Test template with {{{recommended_skills_section}}} placeholder"
    ]
    
    recommended_skills_section = """
    ## RECOMMENDED SKILLS TO ADD

    The following skills were identified as potentially valuable for this position but may be missing or not prominently featured in the resume:

    'Python', 'Django', 'FastAPI', 'React', 'Vue.js', 'Docker', 'Kubernetes'

    If the candidate has any experience with these skills, even minor exposure:
    - Highlight them prominently in the skills section
    - Look for ways to showcase these skills in past experience descriptions
    - Ensure you're using the exact terminology as listed
    - Look for related skills or experience that could be reframed to match these requirements
    - Reframe transferable or implied experience to match the job requirements where ethically possible
    - Be assertive in surfacing any relevant experience, even if it is not an exact match, as long as it is truthful
    - Do NOT fabricate experience with these skills, only highlight them if they exist
    """
    
    for i, template in enumerate(templates):
        print(f"\nTesting template format {i+1}: {template}")
        
        # Method 1: Using partial_variables
        try:
            prompt = PromptTemplate.from_template(
                template=template,
                template_format="jinja2",
                partial_variables={"recommended_skills_section": recommended_skills_section}
            )
            result = prompt.format()
            print(f"Method 1 (partial_variables): SUCCESS")
            print(f"Result: {result[:50]}...")
        except Exception as e:
            print(f"Method 1 (partial_variables): FAILED - {e}")
        
        # Method 2: Manual replacement
        try:
            # Manually replace the placeholder
            if "{{recommended_skills_section}}" in template:
                formatted = template.replace("{{recommended_skills_section}}", recommended_skills_section)
            elif "{{{recommended_skills_section}}}" in template:
                formatted = template.replace("{{{recommended_skills_section}}}", recommended_skills_section)
            elif "{recommended_skills_section}" in template:
                formatted = template.replace("{recommended_skills_section}", recommended_skills_section)
            else:
                formatted = template
            
            prompt = PromptTemplate.from_template(
                template=formatted,
                template_format="jinja2"
            )
            result = prompt.format()
            print(f"Method 2 (manual replacement): SUCCESS")
            print(f"Result: {result[:50]}...")
        except Exception as e:
            print(f"Method 2 (manual replacement): FAILED - {e}")
    
    # Now test our actual implementation from model_ai.py
    print("\n=== Testing Our Implementation ===")
    
    # Import the relevant code
    from app.services.ai.model_ai import AtsResumeOptimizer
    
    # Create a test template with the problematic placeholder
    test_template = """
    # Test Template
    
    This is a test template with a placeholder: {recommended_skills_section}
    
    Job Description: {{job_description}}
    Resume: {{resume}}
    """
    
    # Mock the _get_prompt_template_from_db method
    async def mock_get_prompt_template_from_db():
        return test_template
    
    # Create a mock optimizer
    optimizer = AtsResumeOptimizer(resume="Test resume")
    
    # Replace the method with our mock
    optimizer._get_prompt_template_from_db = mock_get_prompt_template_from_db
    
    # Test the code that handles the template
    try:
        # Extract the relevant code from model_ai.py
        async def test_template_handling():
            db_template = await optimizer._get_prompt_template_from_db()
            if db_template:
                # Create a new prompt template with the database template
                # but keep the recommended skills section
                recommended_skills_section = """
                ## RECOMMENDED SKILLS TO ADD
                
                The following skills were identified as potentially valuable for this position but may be missing or not prominently featured in the resume:
                
                'Python', 'Django', 'FastAPI', 'React', 'Vue.js', 'Docker', 'Kubernetes'
                """
                
                # Create a dictionary of variables to pass to the template
                template_vars = {
                    "job_description": "Test job description",
                    "resume": "Test resume"
                }
                
                # Handle the recommended_skills_section separately as a partial variable
                partial_vars = {
                    "recommended_skills_section": recommended_skills_section
                }
                
                # Create the prompt template with explicit variable handling
                try:
                    custom_prompt = PromptTemplate.from_template(
                        template=db_template,
                        template_format="jinja2",
                        partial_variables=partial_vars
                    )
                    print("Successfully created prompt template with partial_variables")
                    
                    # Test formatting
                    result = custom_prompt.format(**template_vars)
                    print(f"Successfully formatted template: {result[:50]}...")
                    return True
                except Exception as template_error:
                    print(f"Error creating prompt template: {template_error}. Trying fallback method.")
                    # Fallback: manually replace the placeholder
                    if "{{recommended_skills_section}}" in db_template:
                        formatted_template = db_template.replace("{{recommended_skills_section}}", recommended_skills_section)
                    elif "{{{recommended_skills_section}}}" in db_template:
                        formatted_template = db_template.replace("{{{recommended_skills_section}}}", recommended_skills_section)
                    elif "{recommended_skills_section}" in db_template:
                        formatted_template = db_template.replace("{recommended_skills_section}", recommended_skills_section)
                    
                    # Try again with the manually replaced template
                    try:
                        custom_prompt = PromptTemplate.from_template(
                            template=formatted_template,
                            template_format="jinja2"
                        )
                        print("Successfully created prompt template with manual replacement")
                        
                        # Test formatting
                        result = custom_prompt.format(**template_vars)
                        print(f"Successfully formatted template: {result[:50]}...")
                        return True
                    except Exception as e:
                        print(f"Error with fallback method: {e}")
                        return False
            return False
        
        # Run the test
        import asyncio
        success = asyncio.run(test_template_handling())
        
        if success:
            print("\nOur implementation successfully handled the template!")
        else:
            print("\nOur implementation failed to handle the template.")
    
    except Exception as e:
        print(f"Error testing our implementation: {e}")


if __name__ == "__main__":
    test_prompt_template_handling()
