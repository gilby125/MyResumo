"""Test cases for resume download functionality."""
import json
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.routers.resume import resume_router
from app.services.resume.latex_generator import LaTeXGenerator

# Test setup
app = FastAPI()
app.include_router(resume_router)
client = TestClient(app)

# Sample resume data for testing
SAMPLE_RESUME_DATA = {
    "_id": "test_resume_id",
    "title": "Test Resume",
    "original_content": "Test resume content",
    "optimized_data": {
        "user_information": {
            "name": "John Doe",
            "main_job_title": "Software Engineer",
            "profile_description": "Experienced software engineer with a passion for building scalable applications.",
            "email": "john.doe@example.com",
            "linkedin": "linkedin.com/in/johndoe",
            "github": "github.com/johndoe",
            "experiences": [
                {
                    "job_title": "Senior Software Engineer",
                    "company": "Tech Company",
                    "start_date": "2020-01",
                    "end_date": "Present",
                    "location": "New York, NY",
                    "four_tasks": [
                        "Developed scalable backend services using Python and FastAPI",
                        "Implemented CI/CD pipelines for automated testing and deployment",
                        "Optimized database queries resulting in 30% performance improvement",
                        "Mentored junior developers and conducted code reviews"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "university": "University of Technology",
                    "start_date": "2012-09",
                    "end_date": "2016-05",
                    "location": "Boston, MA",
                    "gpa": "3.8/4.0"
                }
            ],
            "skills": {
                "hard_skills": ["Python", "JavaScript", "SQL", "Docker", "AWS"],
                "soft_skills": ["Communication", "Leadership", "Problem Solving"]
            },
            "hobbies": ["Hiking", "Reading", "Photography"]
        },
        "projects": [],
        "certificate": [],
        "extra_curricular_activities": []
    }
}

def test_download_resume_pdf_endpoint():
    """Test the PDF resume download endpoint."""
    with patch("app.api.routers.resume.ResumeRepository") as mock_repo, \
         patch("app.api.routers.resume.LaTeXGenerator") as mock_generator, \
         patch("app.api.routers.resume.create_temporary_pdf") as mock_create_pdf:

        # Setup mocks
        mock_repo.return_value.get_resume_by_id = AsyncMock(return_value=SAMPLE_RESUME_DATA)
        mock_generator.return_value.generate_from_template.return_value = "Sample LaTeX content"
        mock_create_pdf.return_value = "/tmp/test_resume.pdf"

        # Test the endpoint
        response = client.get("/api/resume/test_resume_id/download?use_optimized=true")

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]

        # Verify mocks were called correctly
        mock_repo.return_value.get_resume_by_id.assert_called_once_with("test_resume_id")
        mock_generator.return_value.generate_from_template.assert_called_once()
        mock_create_pdf.assert_called_once_with("Sample LaTeX content")

def test_download_resume_latex_endpoint():
    """Test the LaTeX resume download endpoint."""
    with patch("app.api.routers.resume.ResumeRepository") as mock_repo, \
         patch("app.api.routers.resume.LaTeXGenerator") as mock_generator:

        # Setup mocks
        mock_repo.return_value.get_resume_by_id = AsyncMock(return_value=SAMPLE_RESUME_DATA)
        mock_generator.return_value.generate_from_template.return_value = "Sample LaTeX content"

        # Test the endpoint
        response = client.get("/api/resume/test_resume_id/download-latex")

        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-latex"
        assert "attachment" in response.headers["content-disposition"]
        assert response.content == b"Sample LaTeX content"

        # Verify mocks were called correctly
        mock_repo.return_value.get_resume_by_id.assert_called_once_with("test_resume_id")
        mock_generator.return_value.generate_from_template.assert_called_once()

def test_download_resume_invalid_id():
    """Test resume download with invalid ID."""
    with patch("app.api.routers.resume.ResumeRepository") as mock_repo:
        # Setup mock to return None (resume not found)
        mock_repo.return_value.get_resume_by_id = AsyncMock(return_value=None)

        # Test PDF endpoint
        response_pdf = client.get("/api/resume/invalid_id/download?use_optimized=true")
        assert response_pdf.status_code == 404

        # Test LaTeX endpoint
        response_latex = client.get("/api/resume/invalid_id/download-latex")
        assert response_latex.status_code == 404

def test_download_resume_no_optimized_data():
    """Test resume download with no optimized data."""
    with patch("app.api.routers.resume.ResumeRepository") as mock_repo:
        # Setup mock to return resume without optimized data
        resume_data = SAMPLE_RESUME_DATA.copy()
        resume_data.pop("optimized_data")
        mock_repo.return_value.get_resume_by_id = AsyncMock(return_value=resume_data)

        # Test PDF endpoint
        response_pdf = client.get("/api/resume/test_resume_id/download?use_optimized=true")
        assert response_pdf.status_code == 400

        # Test LaTeX endpoint
        response_latex = client.get("/api/resume/test_resume_id/download-latex")
        assert response_latex.status_code == 400

def test_download_resume_latex_generation_error():
    """Test resume download with LaTeX generation error."""
    with patch("app.api.routers.resume.ResumeRepository") as mock_repo, \
         patch("app.api.routers.resume.LaTeXGenerator") as mock_generator:

        # Setup mocks
        mock_repo.return_value.get_resume_by_id = AsyncMock(return_value=SAMPLE_RESUME_DATA)
        mock_generator.return_value.generate_from_template.return_value = False  # Simulate generation failure

        # Test PDF endpoint
        response_pdf = client.get("/api/resume/test_resume_id/download?use_optimized=true")
        assert response_pdf.status_code == 500

        # Test LaTeX endpoint
        response_latex = client.get("/api/resume/test_resume_id/download-latex")
        assert response_latex.status_code == 500
