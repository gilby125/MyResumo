#!/usr/bin/env python3
"""
Test script to verify the model_dump fix.

This script tests the model_dump handling in the resume repository
without requiring a connection to the AI service.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from uuid import uuid4

# Add the parent directory to the path so we can import the app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.models.resume import ResumeData
from app.database.repositories.resume_repository import ResumeRepository


# Sample optimized data for testing
SAMPLE_OPTIMIZED_DATA = {
    "user_information": {
        "name": "John Doe",
        "main_job_title": "Senior Software Developer",
        "profile_description": "Experienced software developer with 5+ years of experience in web development.",
        "email": "john.doe@example.com",
        "linkedin": "linkedin.com/in/johndoe",
        "github": "github.com/johndoe",
        "experiences": [
            {
                "job_title": "Software Developer",
                "company": "ABC Company",
                "start_date": "2018",
                "end_date": "Present",
                "location": "New York, NY",
                "four_tasks": [
                    "Developed web applications using React and Node.js",
                    "Implemented RESTful APIs",
                    "Worked with MongoDB and PostgreSQL databases",
                    "Collaborated with cross-functional teams"
                ]
            },
            {
                "job_title": "Junior Developer",
                "company": "XYZ Inc.",
                "start_date": "2016",
                "end_date": "2018",
                "location": "Boston, MA",
                "four_tasks": [
                    "Assisted in developing web applications",
                    "Fixed bugs and implemented new features",
                    "Participated in code reviews",
                    "Learned new technologies and frameworks"
                ]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "university": "University of Technology",
                "start_date": "2012",
                "end_date": "2016",
                "location": "Boston, MA"
            }
        ],
        "skills": {
            "hard_skills": ["Python", "JavaScript", "React", "Node.js", "MongoDB", "PostgreSQL", "Git", "Docker"],
            "soft_skills": ["Communication", "Teamwork", "Problem Solving", "Time Management"]
        },
        "hobbies": ["Reading", "Hiking", "Photography"]
    },
    "projects": [],
    "certificate": [],
    "extra_curricular_activities": [],
    "optimization_summary": {
        "changes_made": [
            "Enhanced professional summary to highlight relevant experience",
            "Added keywords from job description to skills section",
            "Quantified achievements in experience section",
            "Reorganized content to prioritize relevant experience"
        ],
        "keywords_added": ["Python", "Django", "FastAPI", "React", "Vue.js", "Docker", "Kubernetes"],
        "skills_emphasized": ["Python", "JavaScript", "React", "MongoDB", "PostgreSQL"],
        "content_reorganized": [
            "Moved most relevant experience to the top",
            "Prioritized technical skills relevant to the job"
        ],
        "achievements_quantified": [
            "Added metrics to project outcomes",
            "Included team size and project scope"
        ],
        "overall_strategy": "Optimized resume to highlight relevant skills and experience for a Senior Software Developer position."
    }
}


class MockResumeData:
    """Mock ResumeData class with model_dump method."""
    
    def __init__(self, data):
        self.data = data
    
    def model_dump(self):
        """Mock model_dump method."""
        return self.data


async def test_model_dump_handling():
    """Test the model_dump handling in the resume repository."""
    print("\n=== Testing model_dump Handling ===")
    
    # Set the MongoDB URL directly
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://192.168.7.10:27017/myresumo")
    # Fix any escaping issues in the URL
    mongodb_url = mongodb_url.replace("\\x3a", ":")
    print(f"Using MongoDB URL: {mongodb_url}")
    
    repo = ResumeRepository(connection_string=mongodb_url)
    
    # Create a test resume
    from app.database.models.resume import Resume
    test_resume = Resume(
        user_id=str(uuid4()),
        title="Test Resume for model_dump",
        original_content="Test content",
        job_description="Test job description",
    )
    
    try:
        resume_id = await repo.create_resume(test_resume)
        print(f"Created test resume with ID: {resume_id}")
        
        # Test with a dictionary
        print("\nTesting with a dictionary...")
        dict_result = await repo.update_optimized_data(
            resume_id,
            SAMPLE_OPTIMIZED_DATA,
            85,
            original_ats_score=75,
            matching_skills=["Python", "JavaScript", "React"],
            missing_skills=["Django", "FastAPI", "Kubernetes"],
            score_improvement=10,
            recommendation="Great improvement!",
            optimization_summary=SAMPLE_OPTIMIZED_DATA.get("optimization_summary", {})
        )
        print(f"Dictionary update result: {dict_result}")
        
        # Test with a mock ResumeData object
        print("\nTesting with a mock ResumeData object...")
        mock_data = MockResumeData(SAMPLE_OPTIMIZED_DATA)
        mock_result = await repo.update_optimized_data(
            resume_id,
            mock_data,
            90,
            original_ats_score=75,
            matching_skills=["Python", "JavaScript", "React"],
            missing_skills=["Django", "FastAPI", "Kubernetes"],
            score_improvement=15,
            recommendation="Excellent improvement!",
            optimization_summary=SAMPLE_OPTIMIZED_DATA.get("optimization_summary", {})
        )
        print(f"Mock object update result: {mock_result}")
        
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
        print(f"Error in test: {e}")
        import traceback
        print(traceback.format_exc())
        return False


async def main():
    """Run the test."""
    print("Starting model_dump fix test...")
    
    success = await test_model_dump_handling()
    
    if success:
        print("\n✅ model_dump fix test PASSED!")
    else:
        print("\n❌ model_dump fix test FAILED!")
    
    print("\nTest completed.")


if __name__ == "__main__":
    asyncio.run(main())
