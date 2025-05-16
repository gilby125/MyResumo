#!/usr/bin/env python3
"""
Integration test for the resume optimization process.

This script tests the complete resume optimization flow, including:
1. Loading a prompt from the database
2. Processing the prompt template with the recommended skills section
3. Generating an optimized resume
4. Updating the resume in the database
"""

import asyncio
import json
import os
import sys
import traceback
from uuid import uuid4

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.models.prompt import PromptTemplate
from app.database.models.resume import Resume, ResumeData
from app.database.repositories.prompt_repository import PromptRepository
from app.database.repositories.resume_repository import ResumeRepository
from app.services.ai.model_ai import AtsResumeOptimizer


# Sample data for testing
SAMPLE_RESUME = """
John Doe
Software Developer
john.doe@example.com

SUMMARY
Experienced software developer with 5 years of experience in web development.

SKILLS
- Python, JavaScript, HTML, CSS
- React, Node.js, Express
- MongoDB, PostgreSQL
- Git, Docker

EXPERIENCE
Software Developer, ABC Company
2018 - Present
- Developed web applications using React and Node.js
- Implemented RESTful APIs
- Worked with MongoDB and PostgreSQL databases
- Collaborated with cross-functional teams

Junior Developer, XYZ Inc.
2016 - 2018
- Assisted in developing web applications
- Fixed bugs and implemented new features
- Participated in code reviews

EDUCATION
Bachelor of Science in Computer Science
University of Technology
2012 - 2016
"""

SAMPLE_JOB_DESCRIPTION = """
Senior Software Developer

We are looking for a Senior Software Developer to join our team. The ideal candidate will have experience with:

- Python, Django, and FastAPI
- JavaScript, React, and Vue.js
- PostgreSQL and MongoDB
- Docker and Kubernetes
- AWS or Azure cloud services
- CI/CD pipelines

Responsibilities:
- Develop and maintain web applications
- Design and implement RESTful APIs
- Work with databases and optimize queries
- Collaborate with cross-functional teams
- Mentor junior developers

Requirements:
- 5+ years of experience in software development
- Strong knowledge of Python and JavaScript
- Experience with React or Vue.js
- Familiarity with Docker and containerization
- Good understanding of database design and optimization
- Excellent problem-solving skills
"""


async def create_test_prompt():
    """Create a test prompt in the database."""
    print("\n=== Creating Test Prompt ===")

    # Set the MongoDB URL directly
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://192.168.7.10:27017/myresumo")
    # Fix any escaping issues in the URL
    mongodb_url = mongodb_url.replace("\\x3a", ":")
    print(f"Using MongoDB URL: {mongodb_url}")

    repo = PromptRepository(connection_string=mongodb_url)

    # Check if the resume_optimization prompt already exists
    existing_prompt = await repo.get_prompt_by_name("resume_optimization")
    if existing_prompt:
        print(f"Found existing resume_optimization prompt with ID: {existing_prompt.get('id')}")
        return existing_prompt

    # Create a new prompt with the problematic placeholder format
    test_prompt = PromptTemplate(
        name="resume_optimization",
        description="Test prompt for resume optimization",
        template="""
        # ROLE: Expert ATS Resume Optimization Specialist
        You are an expert ATS (Applicant Tracking System) Resume Optimizer with specialized knowledge in resume writing, keyword optimization, and applicant tracking systems. Your task is to transform the candidate's existing resume into a highly optimized version tailored specifically to the provided job description, maximizing the candidate's chances of passing through ATS filters while maintaining honesty and accuracy.

        ## INPUT DATA:

        ### JOB DESCRIPTION:
        {{job_description}}

        ### CANDIDATE'S CURRENT RESUME:
        {{resume}}

        {recommended_skills_section}

        ## OPTIMIZATION PROCESS:
        1. **ANALYZE THE JOB DESCRIPTION**
            - Identify key requirements, skills, and qualifications
            - Note specific technologies, tools, and methodologies mentioned
            - Identify industry-specific terminology and keywords
            - Determine the most important qualifications for this role

        2. **ANALYZE THE CURRENT RESUME**
            - Assess how well the current resume matches the job requirements
            - Identify relevant experience and skills that should be highlighted
            - Note any missing keywords or skills that should be incorporated
            - Evaluate the current structure and organization

        3. **CREATE AN ATS-OPTIMIZED RESUME**
            - Use a clean, ATS-friendly format with standard section headings
            - Include the candidate's name, contact information, and professional profiles
            - Create a targeted professional summary highlighting relevant qualifications
            - Incorporate exact keywords and phrases from the job description throughout the resume
            - Prioritize and emphasize experiences most relevant to the target position
            - Reorder content to place most relevant experiences and skills first
            - Use industry-standard terminology that ATS systems recognize
            - Quantify achievements with metrics where possible (numbers, percentages, dollar amounts)
            - Remove irrelevant information that doesn't support this application

        4. **RETURN THE OPTIMIZED RESUME IN JSON FORMAT**
            - Format the resume as a JSON object with the following structure:
            ```json
            {
              "user_information": {
                "name": "Candidate's Name",
                "main_job_title": "Target Position Title",
                "profile_description": "Professional summary tailored to the job",
                "email": "candidate@example.com",
                "linkedin": "linkedin profile URL",
                "github": "github profile URL",
                "experiences": [
                  {
                    "job_title": "Position Title",
                    "company": "Company Name",
                    "start_date": "Start Date",
                    "end_date": "End Date or Present",
                    "location": "Location",
                    "four_tasks": [
                      "Achievement 1 with metrics",
                      "Achievement 2 with metrics",
                      "Achievement 3 with metrics",
                      "Achievement 4 with metrics"
                    ]
                  }
                ],
                "education": [
                  {
                    "degree": "Degree Name",
                    "university": "University Name",
                    "start_date": "Start Date",
                    "end_date": "End Date",
                    "location": "Location"
                  }
                ],
                "skills": {
                  "hard_skills": ["Skill 1", "Skill 2", "Skill 3"],
                  "soft_skills": ["Soft Skill 1", "Soft Skill 2"]
                },
                "hobbies": ["Hobby 1", "Hobby 2"]
              },
              "projects": [],
              "certificate": [],
              "extra_curricular_activities": [],
              "optimization_summary": {
                "changes_made": ["Change 1", "Change 2", "Change 3"],
                "keywords_added": ["Keyword 1", "Keyword 2", "Keyword 3"],
                "skills_emphasized": ["Skill 1", "Skill 2", "Skill 3"],
                "content_reorganized": ["Reorganization 1", "Reorganization 2"],
                "achievements_quantified": ["Achievement 1", "Achievement 2"],
                "overall_strategy": "Brief description of the optimization strategy"
              }
            }
            ```
        """,
        component="resume_optimization",
        variables=["job_description", "resume", "recommended_skills_section"],
    )

    try:
        prompt_id = await repo.create_prompt(test_prompt)
        print(f"Created test prompt with ID: {prompt_id}")
        return await repo.get_prompt_by_id(prompt_id)
    except Exception as e:
        print(f"Error creating test prompt: {e}")
        return None


async def create_test_resume():
    """Create a test resume in the database."""
    print("\n=== Creating Test Resume ===")

    # Set the MongoDB URL directly
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://192.168.7.10:27017/myresumo")
    # Fix any escaping issues in the URL
    mongodb_url = mongodb_url.replace("\\x3a", ":")
    print(f"Using MongoDB URL: {mongodb_url}")

    repo = ResumeRepository(connection_string=mongodb_url)

    # Create a new resume
    test_resume = Resume(
        user_id=str(uuid4()),
        title="Test Resume",
        original_content=SAMPLE_RESUME,
        job_description=SAMPLE_JOB_DESCRIPTION,
    )

    try:
        resume_id = await repo.create_resume(test_resume)
        print(f"Created test resume with ID: {resume_id}")
        return await repo.get_resume_by_id(resume_id)
    except Exception as e:
        print(f"Error creating test resume: {e}")
        return None


async def test_resume_optimization():
    """Test the resume optimization process."""
    print("\n=== Testing Resume Optimization ===")

    # Create test data
    test_prompt = await create_test_prompt()
    if not test_prompt:
        print("Failed to create test prompt. Aborting test.")
        return

    test_resume = await create_test_resume()
    if not test_resume:
        print("Failed to create test resume. Aborting test.")
        return

    resume_id = str(test_resume.get("_id"))
    resume_content = test_resume.get("original_content")
    job_description = test_resume.get("job_description")

    # Set up the optimizer
    api_key = os.getenv("API_KEY")
    api_base = os.getenv("API_BASE")
    model_name = os.getenv("MODEL_NAME")

    if not api_key or not api_base or not model_name:
        print("Missing API configuration. Please set API_KEY, API_BASE, and MODEL_NAME environment variables.")
        return

    print(f"Using model: {model_name}")
    optimizer = AtsResumeOptimizer(
        model_name=model_name,
        resume=resume_content,
        api_key=api_key,
        api_base=api_base,
        temperature=0.0,
    )

    # Generate optimized resume
    try:
        print("\nGenerating optimized resume...")
        result = await optimizer.generate_ats_optimized_resume_json(job_description)

        if "error" in result:
            print(f"Error generating optimized resume: {result.get('error')}")
            return

        print("\nOptimized resume generated successfully!")
        print(f"Result keys: {list(result.keys())}")

        # Update the resume in the database
        print("\nUpdating resume in database...")
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://192.168.7.10:27017/myresumo")
        # Fix any escaping issues in the URL
        mongodb_url = mongodb_url.replace("\\x3a", ":")
        print(f"Using MongoDB URL for update: {mongodb_url}")
        repo = ResumeRepository(connection_string=mongodb_url)

        # Test with the result directly (should be a dictionary)
        update_result = await repo.update_optimized_data(
            resume_id,
            result,
            85,
            original_ats_score=75,
            matching_skills=["Python", "JavaScript", "React"],
            missing_skills=["Django", "FastAPI", "Kubernetes"],
            score_improvement=10,
            recommendation="Great improvement!",
            optimization_summary=result.get("optimization_summary", {})
        )

        print(f"Update result: {update_result}")

        # Verify the update
        updated_resume = await repo.get_resume_by_id(resume_id)
        if updated_resume and updated_resume.get("optimized_data"):
            print("\nResume updated successfully!")
            print(f"ATS score: {updated_resume.get('ats_score')}")
            print(f"Score improvement: {updated_resume.get('score_improvement')}")
            return True
        else:
            print("\nFailed to update resume or retrieve updated data.")
            return False

    except Exception as e:
        print(f"\nError in resume optimization test: {e}")
        print(traceback.format_exc())
        return False


async def main():
    """Run the integration test."""
    print("Starting resume optimization integration test...")

    success = await test_resume_optimization()

    if success:
        print("\n✅ Resume optimization test PASSED!")
    else:
        print("\n❌ Resume optimization test FAILED!")

    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(main())
