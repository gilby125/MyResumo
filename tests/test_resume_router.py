"""Test cases for the resume router."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routers.resume import resume_router
from app.database.models.resume import ResumeData
from app.services.ai.ats_scoring import ATSScorerLLM
from unittest.mock import AsyncMock, MagicMock, patch

# Test setup
app = FastAPI()
app.include_router(resume_router)
client = TestClient(app)

def test_router_initialization():
    """Test that the router is properly initialized."""
    assert hasattr(resume_router, "prefix")
    assert resume_router.prefix == "/api/resume"
    assert "Resume" in resume_router.tags

@pytest.mark.asyncio
async def test_create_resume_endpoint():
    """Test the resume creation endpoint."""
    with patch("app.api.routers.resume.ResumeRepository") as mock_repo:
        mock_repo.return_value.create_resume = AsyncMock(return_value="test_id")
        
        test_file = ("test.pdf", b"test content", "application/pdf")
        response = client.post(
            "/api/resume/",
            files={"file": test_file},
            data={
                "title": "Test Resume",
                "job_description": "Test Job",
                "user_id": "test_user"
            }
        )
        
        assert response.status_code == 200
        assert response.json() == {"id": "test_id"}

@pytest.mark.asyncio
async def test_get_resume_endpoint():
    """Test the resume retrieval endpoint."""
    with patch("app.api.routers.resume.ResumeRepository") as mock_repo:
        mock_repo.return_value.get_resume_by_id = AsyncMock(return_value={
            "_id": "test_id",
            "title": "Test Resume",
            "original_content": "Test content"
        })
        
        response = client.get("/api/resume/test_id")
        assert response.status_code == 200
        assert "id" in response.json()

@pytest.mark.asyncio
async def test_optimize_resume_endpoint():
    """Test the resume optimization endpoint."""
    with patch("app.api.routers.resume.ResumeRepository") as mock_repo, \
         patch("app.api.routers.resume.ATSScorerLLM") as mock_scorer, \
         patch("app.api.routers.resume.AtsResumeOptimizer") as mock_optimizer:
        
        # Setup mocks
        mock_repo.return_value.get_resume_by_id = AsyncMock(return_value={
            "_id": "test_id",
            "title": "Test Resume",
            "original_content": "Test content"
        })
        mock_repo.return_value.update_optimized_data = AsyncMock(return_value=True)
        
        mock_scorer.return_value.compute_match_score.return_value = {
            "final_score": 75,
            "matching_skills": ["Python"],
            "missing_skills": ["SQL"],
            "recommendation": "Test recommendation"
        }
        
        mock_optimizer.return_value.generate_ats_optimized_resume_json.return_value = {
            "skills": ["Python"],
            "experience": [{"title": "Test"}]
        }
        
        response = client.post(
            "/api/resume/test_id/optimize",
            json={"job_description": "Test Job"}
        )
        
        assert response.status_code == 200
        assert "optimized_data" in response.json()

def test_all_endpoints_have_dependencies():
    """Verify all endpoints have required dependencies."""
    for route in resume_router.routes:
        # Check for at least one dependency (repo or other)
        has_depends = False
        for param in route.dependant.dependencies:
            if hasattr(param.call, "__name__") and param.call.__name__ == "get_resume_repository":
                has_depends = True
                break
        
        assert has_depends, f"Endpoint {route.path} missing required dependencies"

def test_route_parameters_match_expected():
    """Test that route parameters match expected types."""
    route_params = {
        "/": {
            "methods": ["POST"],
            "params": ["file", "title", "job_description", "user_id"]
        },
        "/{resume_id}": {
            "methods": ["GET", "PUT", "DELETE"],
            "params": ["resume_id"]
        },
        "/{resume_id}/optimize": {
            "methods": ["POST"],
            "params": ["resume_id", "job_description"]
        }
    }
    
    for route in resume_router.routes:
        if route.path in route_params:
            assert route.methods == set(route_params[route.path]["methods"])
            for param in route_params[route.path]["params"]:
                assert any(p.name == param for p in route.dependant.path_params), \
                    f"Missing expected parameter {param} in {route.path}"