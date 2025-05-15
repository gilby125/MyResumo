"""Resume API router module for resume management operations.

This module implements the API endpoints for resume-related functionality including
resume creation, retrieval, optimization, PDF generation and deletion. It handles
the interface between HTTP requests and the resume repository, and coordinates
AI-powered resume optimization services.
"""
import json
import logging
import os
import secrets
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, EmailStr, Field

from app.database.models.resume import Resume, ResumeData
from app.database.repositories.resume_repository import ResumeRepository
from app.services.ai.ats_scoring import ATSScorerLLM
from app.services.ai.model_ai import AtsResumeOptimizer
from app.services.resume.latex_generator import LaTeXGenerator
from app.utils.file_handling import create_temporary_pdf, extract_text_from_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Request and response models
class CreateResumeRequest(BaseModel):
    """Schema for creating a new resume."""

    user_id: str = Field(..., description="Unique identifier for the user")
    title: str = Field(..., description="Title of the resume")
    original_content: str = Field(..., description="Original content of the resume")
    job_description: str = Field(
        ..., description="Job description to tailor the resume for"
    )


class OptimizeResumeRequest(BaseModel):
    """Schema for optimizing an existing resume."""

    job_description: str = Field(
        ..., description="Job description to tailor the resume for"
    )
    temperature: float = Field(
        0.0, description="Temperature setting for the LLM (0.0-1.0) to control creativity", ge=0.0, le=1.0
    )


class ResumeSummary(BaseModel):
    """Schema for resume summary information."""

    id: str = Field(..., description="Unique identifier for the resume")
    title: str = Field(..., description="Title of the resume")
    ats_score: Optional[int] = Field(
        None, description="ATS score of the resume if optimized"
    )
    created_at: datetime = Field(..., description="When the resume was created")
    updated_at: datetime = Field(..., description="When the resume was last updated")


class OptimizationSummary(BaseModel):
    """Schema for optimization summary."""

    changes_made: List[str] = Field([], description="List of changes made to the resume")
    keywords_added: List[str] = Field([], description="Keywords added from the job description")
    skills_emphasized: List[str] = Field([], description="Skills that were emphasized in the resume")
    content_reorganized: List[str] = Field([], description="How content was reorganized")
    achievements_quantified: List[str] = Field([], description="Achievements that were quantified")
    overall_strategy: str = Field("", description="Overall optimization strategy")


class OptimizationResponse(BaseModel):
    """Schema for resume optimization response."""

    resume_id: str = Field(
        ..., description="Unique identifier for the optimized resume"
    )
    original_ats_score: int = Field(..., description="ATS score before optimization")
    optimized_ats_score: int = Field(..., description="ATS score after optimization")
    score_improvement: int = Field(
        ..., description="Score improvement after optimization"
    )
    matching_skills: List[str] = Field(
        [], description="Skills that match the job description"
    )
    missing_skills: List[str] = Field([], description="Skills missing from the resume")
    recommendation: str = Field("", description="AI recommendation for improvement")
    optimization_summary: Optional[OptimizationSummary] = Field(None, description="Summary of optimization changes")
    optimized_data: Dict[str, Any] = Field(..., description="Optimized resume data")


class ContactFormRequest(BaseModel):
    """Schema for contact form submission."""

    name: str = Field(..., description="Full name of the person reaching out")
    email: EmailStr = Field(..., description="Email address for return communication")
    subject: str = Field(..., description="Subject of the contact message")
    message: str = Field(..., description="Detailed message content")


class ContactFormResponse(BaseModel):
    """Schema for contact form response."""

    success: bool = Field(..., description="Whether the message was sent successfully")
    message: str = Field(..., description="Status message")


class ScoreResumeRequest(BaseModel):
    """Schema for scoring an existing resume."""

    job_description: str = Field(
        ..., description="Job description to score the resume against"
    )
    temperature: float = Field(
        0.0, description="Temperature setting for the LLM (0.0-1.0) to control creativity", ge=0.0, le=1.0
    )


class ResumeScoreResponse(BaseModel):
    """Schema for resume score response."""

    resume_id: str = Field(..., description="Unique identifier for the resume")
    ats_score: int = Field(..., description="ATS compatibility score (0-100)")
    matching_skills: List[str] = Field(
        [], description="Skills that match the job description"
    )
    missing_skills: List[str] = Field([], description="Skills missing from the resume")
    recommendation: str = Field("", description="AI recommendation for improvement")
    resume_skills: List[str] = Field([], description="Skills extracted from the resume")
    job_requirements: List[str] = Field(
        [], description="Requirements extracted from the job description"
    )
    optimization_success: bool = Field(
        False, description="Whether the optimization was successful"
    )
    optimized_score: Optional[int] = Field(
        None, description="ATS score of the optimized resume"
    )
    score_improvement: int = Field(
        0, description="Score improvement after optimization"
    )
    optimization_summary: Optional[OptimizationSummary] = Field(
        None, description="Summary of optimization changes"
    )


resume_router = APIRouter(prefix="/api/resume", tags=["Resume"])


async def get_resume_repository(request: Request) -> ResumeRepository:
    """Dependency for getting the resume repository instance.

    Args:
        request: The incoming request

    Returns:
    -------
        ResumeRepository: An instance of the resume repository
    """
    # Get MongoDB URL from environment variable
    mongodb_url = os.getenv("MONGODB_URL")
    logger.info(f"Creating ResumeRepository with MongoDB URL: {mongodb_url}")

    # Create repository with connection string from environment
    return ResumeRepository(connection_string=mongodb_url)


@resume_router.post(
    "/",
    response_model=Dict[str, str],
    summary="Create a resume",
    response_description="Resume created successfully",
)
async def create_resume(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    job_description: str = Form(...),
    user_id: str = Form(...),
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Create a new resume from a PDF file.

    This endpoint accepts a PDF file upload, extracts the text content,
    and creates a new resume entry in the database.

    Args:
        request: The incoming request
        file: Uploaded PDF resume file
        title: Title for the resume
        job_description: Job description to tailor the resume for
        user_id: ID of the user creating the resume
        repo: Resume repository instance

    Returns:
    -------
        Dict containing the ID of the created resume

    Raises:
    ------
        HTTPException: If the resume creation fails
    """
    try:
        pdf_content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        try:
            resume_text = extract_text_from_pdf(temp_file_path)
        finally:
            os.unlink(temp_file_path)

        new_resume = Resume(
            user_id=user_id,
            title=title,
            original_content=resume_text,
            job_description=job_description,
        )

        resume_id = await repo.create_resume(new_resume)
        if not resume_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create resume",
            )
        return {"id": resume_id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating resume: {str(e)}",
        )


@resume_router.get(
    "/{resume_id}",
    response_model=Dict[str, Any],
    summary="Get a resume",
    response_description="Resume retrieved successfully",
)
async def get_resume(
    resume_id: str,
    request: Request,
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Get a specific resume by ID.

    Args:
        resume_id: ID of the resume to retrieve
        request: The incoming request
        repo: Resume repository instance

    Returns:
    -------
        Dict containing the resume data

    Raises:
    ------
        HTTPException: If the resume is not found or ID is invalid
    """
    # Check if resume_id is "undefined" or invalid
    if resume_id == "undefined" or not resume_id:
        logger.error(f"Invalid resume ID: {resume_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID. Please provide a valid resume ID.",
        )

    try:
        resume_data = await repo.get_resume_by_id(resume_id)
        if not resume_data:
            logger.warning(f"Resume with ID {resume_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found",
            )
        resume_data["id"] = str(resume_data.pop("_id"))
        return resume_data
    except Exception as e:
        logger.error(f"Error retrieving resume with ID {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving resume: {str(e)}",
        )


@resume_router.get(
    "/user/{user_id}",
    response_model=List[ResumeSummary],
    summary="Get all resumes for a user",
    response_description="Resumes retrieved successfully",
)
async def get_user_resumes(
    user_id: str,
    request: Request,
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Get all resumes for a specific user.

    Args:
        user_id: ID of the user whose resumes to retrieve
        request: The incoming request
        repo: Resume repository instance

    Returns:
    -------
        List of resume summaries for the specified user
    """
    resumes = await repo.get_resumes_by_user_id(user_id)
    formatted_resumes = []
    for resume in resumes:
        formatted_resumes.append(
            {
                "id": str(resume.get("_id")),
                "title": resume.get("title"),
                "ats_score": resume.get("ats_score"),
                "created_at": resume.get("created_at"),
                "updated_at": resume.get("updated_at"),
            }
        )
    return formatted_resumes


@resume_router.put(
    "/{resume_id}",
    response_model=Dict[str, bool],
    summary="Update a resume",
    response_description="Resume updated successfully",
)
async def update_resume(
    resume_id: str,
    update_data: Dict[str, Any] = Body(...),
    request: Request = None,
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Update a specific resume by ID.

    Args:
        resume_id: ID of the resume to update
        update_data: Data to update in the resume
        request: The incoming request
        repo: Resume repository instance

    Returns:
    -------
        Dict indicating success status

    Raises:
    ------
        HTTPException: If the resume is not found or update fails
    """
    resume = await repo.get_resume_by_id(resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found",
        )
    success = await repo.update_resume(resume_id, update_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resume",
        )
    return {"success": True}


@resume_router.delete(
    "/{resume_id}",
    response_model=Dict[str, bool],
    summary="Delete a resume",
    response_description="Resume deleted successfully",
)
async def delete_resume(
    resume_id: str,
    request: Request = None,
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Delete a specific resume by ID.

    Args:
        resume_id: ID of the resume to delete
        request: The incoming request
        repo: Resume repository instance

    Returns:
    -------
        Dict indicating success status

    Raises:
    ------
        HTTPException: If the resume is not found or deletion fails
    """
    resume = await repo.get_resume_by_id(resume_id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found",
        )
    success = await repo.delete_resume(resume_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume",
        )
    return {"success": True}


@resume_router.post(
    "/{resume_id}/optimize",
    response_model=OptimizationResponse,
    summary="Optimize a resume with AI",
    response_description="Resume optimized successfully",
)
async def optimize_resume(
    resume_id: str,
    optimization_request: OptimizeResumeRequest,
    request: Request,
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Optimize a resume using AI based on a job description.

    This endpoint uses AI to analyze the original resume and job description,
    then generates an optimized version that's tailored to the job requirements.
    It also compares the ATS scores before and after optimization.

    Args:
        resume_id: ID of the resume to optimize
        optimization_request: Contains the job description for optimization
        request: The incoming request
        repo: Resume repository instance

    Returns:
    -------
        OptimizationResponse: Contains the optimized data, before/after ATS scores, and skill analysis

    Raises:
    ------
        HTTPException: If the resume is not found or optimization fails
    """
    logger.info(f"Starting resume optimization for resume_id: {resume_id}")

    # Check if resume_id is "undefined" or invalid
    if resume_id == "undefined" or not resume_id:
        logger.error(f"Invalid resume ID for optimization: {resume_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID. Please provide a valid resume ID.",
        )

    # 1. Retrieve resume
    logger.info(f"Retrieving resume with ID: {resume_id}")
    try:
        resume = await repo.get_resume_by_id(resume_id)
        if not resume:
            logger.warning(f"Resume not found with ID: {resume_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found",
            )
    except Exception as e:
        logger.error(f"Error retrieving resume with ID {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving resume: {str(e)}",
        )
    logger.info(f"Successfully retrieved resume: {resume.get('title', 'Untitled')}")

    # 2. Get API configuration
    logger.info("Retrieving API configuration")
    api_key = os.getenv("API_KEY")
    api_base_url = os.getenv("API_BASE")
    model_name = os.getenv("MODEL_NAME")

    logger.info(f"API configuration - model_name: {model_name or 'Not set'}")
    logger.info(f"API configuration - api_base_url: {api_base_url or 'Not set'}")
    logger.info(f"API Key present: {bool(api_key)}")

    if not api_key:
        logger.warning(
            "API key not found in environment variables, attempting to get from app state"
        )
        try:
            api_key = request.app.state.config.AI_API_KEY
            logger.info("Successfully retrieved API key from app state")
        except Exception as config_error:
            logger.error(
                f"Failed to retrieve API key from app state: {str(config_error)}"
            )
            logger.error(f"Config error details: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI API key not configured",
            )

    # 3. Initialize ATS scorer
    logger.info("Initializing ATSScorerLLM for pre-optimization scoring")
    ats_scorer = ATSScorerLLM(
        model_name=model_name,
        api_key=api_key,
        api_base=api_base_url,
    )

    # 4. Get job description
    job_description = optimization_request.job_description or resume.get(
        "job_description", ""
    )
    logger.info(f"Job description length: {len(job_description)} characters")

    if not job_description:
        logger.warning("Job description is empty")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description is required for optimization",
        )

    try:
        # 5. Score the original resume
        logger.info("Scoring original resume against job description")
        original_score_result = await ats_scorer.compute_match_score(
            resume["original_content"], job_description
        )
        original_ats_score = int(original_score_result["final_score"])
        logger.info(f"Original resume ATS score: {original_ats_score}")

        # Extract missing skills to be addressed in optimization
        missing_skills = original_score_result.get("missing_skills", [])
        logger.info(f"Identified missing skills: {missing_skills}")

        # 6. Initialize optimizer and generate optimized resume
        logger.info(f"Initializing AtsResumeOptimizer with temperature: {optimization_request.temperature}")
        optimizer = AtsResumeOptimizer(
            model_name=model_name,
            resume=resume["original_content"],
            api_key=api_key,
            api_base=api_base_url,
            temperature=optimization_request.temperature,
        )

        logger.info("Calling AI service to generate optimized resume")
        result = await optimizer.generate_ats_optimized_resume_json(job_description)
        # Note: The optimizer now automatically incorporates missing skills into the prompt

        # 7. Check for errors in result
        if "error" in result:
            logger.error(f"AI service returned an error: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI optimization error: {result['error']}",
            )

        # 8. Log the structure of the result (without exposing sensitive data)
        logger.info("AI service returned result successfully")
        logger.info(
            f"Result keys: {list(result.keys() if isinstance(result, dict) else [])}"
        )

        # 9. Parse and validate result
        logger.info("Parsing result into ResumeData model")
        try:
            # Check if the result contains raw_text_response, which indicates it's a fallback structured response
            if "raw_text_response" in result:
                logger.warning("Using fallback structured response from text. This may not contain all expected data.")
                # We'll still try to validate it, but we'll log a warning

            optimized_data = ResumeData.model_validate(result)
            logger.info("Successfully validated result through Pydantic model")

            # If this is a fallback response, add a note to the profile description
            if "raw_text_response" in result:
                # Add a note to the profile description
                original_profile = optimized_data.user_information.profile_description
                note = "\n\nNote: This resume was generated from a text response and may not be fully structured. Please review and edit as needed."
                optimized_data.user_information.profile_description = original_profile + note

        except Exception as validation_error:
            logger.error(
                f"Failed to parse result into ResumeData model: {str(validation_error)}"
            )
            logger.error(f"Validation error details: {traceback.format_exc()}")
            logger.debug(f"Problematic data: {result}")

            # Check if we have a raw text response we can use
            if isinstance(result, dict) and "raw_text_response" in result:
                logger.warning("Validation failed but raw text response is available. Creating minimal valid structure.")

                # Create a minimal valid structure that will pass validation
                minimal_result = {
                    "user_information": {
                        "name": "",
                        "main_job_title": "Generated from Text Response",
                        "profile_description": "The AI generated a text response instead of structured data. Here's the beginning of that response:\n\n" +
                                              result.get("raw_text_response", "")[:500] +
                                              "\n\n(Note: This resume was generated from a text response and may not be fully structured. Please review and edit as needed.)",
                        "email": "",
                        "linkedin": "",
                        "github": "",
                        "experiences": [
                            {
                                "job_title": "See Profile Description",
                                "company": "Text Response",
                                "start_date": "",
                                "end_date": "",
                                "location": "",
                                "four_tasks": [
                                    "Please see the profile description for the full text response.",
                                    "The AI generated a text response instead of structured data.",
                                    "You may want to try optimizing again with different settings.",
                                    "Or you can manually extract information from the text response."
                                ]
                            }
                        ],
                        "education": [],
                        "skills": {
                            "hard_skills": result.get("user_information", {}).get("skills", {}).get("hard_skills", []),
                            "soft_skills": []
                        },
                        "hobbies": []
                    },
                    "projects": [],
                    "certificate": [],
                    "extra_curricular_activities": []
                }

                # Add ATS metrics if available
                if "ats_metrics" in result:
                    minimal_result["ats_metrics"] = result["ats_metrics"]

                try:
                    optimized_data = ResumeData.model_validate(minimal_result)
                    logger.info("Successfully created and validated minimal structure from raw text response")
                except Exception as second_validation_error:
                    logger.error(f"Failed to create minimal valid structure: {str(second_validation_error)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Error parsing AI response: {str(validation_error)}",
                    )
            else:
                # If we don't have a raw text response, raise the original error
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error parsing AI response: {str(validation_error)}",
                )

        # 10. Score the optimized resume
        logger.info("Generating JSON text representation of the optimized resume")
        optimized_resume_text = json.dumps(result)

        logger.info("Scoring optimized resume against job description")
        optimized_score_result = await ats_scorer.compute_match_score(
            optimized_resume_text, job_description
        )
        optimized_ats_score = int(optimized_score_result["final_score"])
        logger.info(f"Optimized resume ATS score: {optimized_ats_score}")

        score_improvement = optimized_ats_score - original_ats_score
        logger.info(f"Score improvement: {score_improvement}")

        # 11. Update database
        logger.info(f"Updating resume {resume_id} with optimized data")
        try:
            # Extract optimization summary if available
            optimization_summary = None
            if isinstance(result, dict) and "optimization_summary" in result:
                optimization_summary = result["optimization_summary"]
                logger.info("Found optimization summary in result")

            await repo.update_optimized_data(
                resume_id, optimized_data, optimized_ats_score,
                original_ats_score=original_ats_score,
                matching_skills=optimized_score_result.get("matching_skills", []),
                missing_skills=optimized_score_result.get("missing_skills", []),
                score_improvement=score_improvement,
                recommendation=optimized_score_result.get("recommendation", ""),
                optimization_summary=optimization_summary
            )
            logger.info("Successfully updated resume with optimized data")
        except Exception as db_error:
            logger.error(f"Database error during update: {str(db_error)}")
            logger.error(f"Database error details: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error during update: {str(db_error)}",
            )

        # 12. Return success response with both scores and skill analysis
        logger.info(
            f"Resume optimization completed successfully for resume_id: {resume_id}"
        )

        # Extract optimization summary if available
        optimization_summary = None
        if isinstance(result, dict) and "optimization_summary" in result:
            optimization_summary = result["optimization_summary"]

        return {
            "resume_id": resume_id,
            "original_ats_score": original_ats_score,
            "optimized_ats_score": optimized_ats_score,
            "score_improvement": score_improvement,
            "matching_skills": optimized_score_result.get("matching_skills", []),
            "missing_skills": optimized_score_result.get("missing_skills", []),
            "recommendation": optimized_score_result.get("recommendation", ""),
            "optimization_summary": optimization_summary,
            "optimized_data": result,
        }

    except HTTPException:
        # Re-raise HTTP exceptions as they're already properly formatted
        raise
    except Exception as e:
        # Log the full stack trace for any other exception
        logger.error(f"Unexpected error during resume optimization: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")

        # Check for specific error types to provide better error messages
        if "API key" in str(e).lower() or "authentication" in str(e).lower():
            logger.error("AI service authentication error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error authenticating with AI service. Please check API configuration.",
            )
        elif "timeout" in str(e).lower() or "time" in str(e).lower():
            logger.error("AI service timeout error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service request timed out. Please try again later.",
            )
        elif "json" in str(e).lower() or "extract" in str(e).lower() or "parse" in str(e).lower():
            logger.error("JSON extraction error from AI response")

            # Try to extract the first part of the response for debugging
            error_msg = str(e)
            response_preview = ""
            if "Could not extract valid JSON from response:" in error_msg:
                response_preview = error_msg.split("Could not extract valid JSON from response:", 1)[1].strip()[:100]
                if response_preview:
                    response_preview = f" Response starts with: '{response_preview}...'"

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"The AI service returned a response that could not be processed as JSON. Please try again with a lower temperature setting (0.0 recommended).{response_preview}",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during resume optimization: {str(e)}",
            )


@resume_router.post(
    "/{resume_id}/score",
    response_model=ResumeScoreResponse,
    summary="Score a resume against a job description",
    response_description="Resume scored successfully",
)
async def score_resume(
    resume_id: str,
    scoring_request: ScoreResumeRequest,
    request: Request,
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Score a resume against a job description and generate an optimized version in one step.

    This endpoint analyzes the resume against the provided job description,
    returns an ATS compatibility score, and also generates an optimized version
    of the resume tailored to the job description.

    Args:
        resume_id: ID of the resume to score
        scoring_request: Contains the job description to score against
        request: The incoming request
        repo: Resume repository instance

    Returns:
    -------
        ResumeScoreResponse: Contains the ATS score, skill analysis, and optimization status

    Raises:
    ------
        HTTPException: If the resume is not found or scoring fails
    """
    logger.info(f"Starting resume scoring for resume_id: {resume_id}")

    # Check if resume_id is "undefined" or invalid
    if resume_id == "undefined" or not resume_id:
        logger.error(f"Invalid resume ID for scoring: {resume_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID. Please provide a valid resume ID.",
        )

    # Retrieve resume
    logger.info(f"Retrieving resume with ID: {resume_id}")
    try:
        resume = await repo.get_resume_by_id(resume_id)
        if not resume:
            logger.warning(f"Resume not found with ID: {resume_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found",
            )
    except Exception as e:
        logger.error(f"Error retrieving resume with ID {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving resume: {str(e)}",
        )

    # Get API configuration
    api_key = os.getenv("API_KEY")
    api_base_url = os.getenv("API_BASE")
    model_name = os.getenv("MODEL_NAME")

    if not api_key:
        logger.warning(
            "API key not found in environment variables, attempting to get from app state"
        )
        try:
            api_key = request.app.state.config.AI_API_KEY
        except Exception as config_error:
            logger.error(
                f"Failed to retrieve API key from app state: {str(config_error)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI API key not configured",
            )

    # Initialize ATS scorer
    try:
        logger.info(f"Initializing ATSScorerLLM with temperature: {scoring_request.temperature}")
        ats_scorer = ATSScorerLLM(
            model_name=model_name,
            api_key=api_key,
            api_base=api_base_url,
            temperature=scoring_request.temperature,
        )

        # Get job description
        job_description = scoring_request.job_description
        if not job_description:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description is required for scoring",
            )

        # Get resume content
        resume_content = resume["original_content"]

        # 1. Score the original resume
        logger.info("Scoring original resume against job description")
        score_result = await ats_scorer.compute_match_score(
            resume_content, job_description
        )
        ats_score = int(score_result["final_score"])
        logger.info(f"Original resume ATS score: {ats_score}")

        # 2. Generate optimized version in the same step
        logger.info("Generating optimized resume version")

        # Initialize optimizer
        logger.info(f"Initializing AtsResumeOptimizer with temperature: {scoring_request.temperature}")
        optimizer = AtsResumeOptimizer(
            model_name=model_name,
            resume=resume_content,
            api_key=api_key,
            api_base=api_base_url,
            temperature=scoring_request.temperature,
        )

        # Generate optimized resume
        optimization_success = False
        optimized_data = None
        optimized_score = None
        score_improvement = 0

        try:
            # Generate optimized resume
            logger.info("Calling AI service to generate optimized resume")
            optimization_result = await optimizer.generate_ats_optimized_resume_json(job_description)

            # Check for errors in optimization result
            if "error" in optimization_result:
                logger.error(f"AI service returned an error during optimization: {optimization_result.get('error')}")
                # Continue with scoring only, don't fail the whole request
            else:
                # Parse the optimized data
                try:
                    optimized_data = ResumeData.model_validate(optimization_result)
                    logger.info("Successfully validated optimization result through Pydantic model")

                    # Score the optimized resume
                    logger.info("Scoring optimized resume")
                    optimized_resume_text = json.dumps(optimization_result)
                    optimized_score_result = await ats_scorer.compute_match_score(
                        optimized_resume_text, job_description
                    )
                    optimized_score = int(optimized_score_result["final_score"])
                    logger.info(f"Optimized resume ATS score: {optimized_score}")

                    # Calculate improvement
                    score_improvement = optimized_score - ats_score
                    logger.info(f"Score improvement: {score_improvement}")

                    # Extract optimization summary if available
                    optimization_summary = None
                    if isinstance(optimization_result, dict) and "optimization_summary" in optimization_result:
                        optimization_summary = optimization_result["optimization_summary"]

                    # Update database with optimized data
                    logger.info(f"Updating resume {resume_id} with optimized data")
                    await repo.update_optimized_data(
                        resume_id, optimized_data.model_dump(), optimized_score,
                        original_ats_score=ats_score,
                        matching_skills=score_result.get("matching_skills", []),
                        missing_skills=score_result.get("missing_skills", []),
                        score_improvement=score_improvement,
                        recommendation=score_result.get("recommendation", ""),
                        optimization_summary=optimization_summary
                    )
                    optimization_success = True
                except Exception as validation_error:
                    logger.error(f"Failed to process optimization result: {str(validation_error)}")
                    logger.error(f"Error details: {traceback.format_exc()}")
        except Exception as optimization_error:
            logger.error(f"Error during resume optimization: {str(optimization_error)}")
            logger.error(f"Error details: {traceback.format_exc()}")
            # Continue with scoring only, don't fail the whole request

        # Prepare enhanced recommendation
        recommendation = score_result.get("recommendation", "")
        if optimization_success and score_improvement > 0:
            recommendation += f"\n\nYour optimized resume scores {score_improvement} points higher ({optimized_score}%). The optimized version is now available in your dashboard."

        # Save the job description and temperature to the resume
        logger.info(f"Saving job description and temperature ({scoring_request.temperature}) to resume {resume_id}")
        await repo.update_resume(
            resume_id,
            {
                "job_description": job_description,
                "last_used_temperature": scoring_request.temperature
            }
        )

        # Prepare optimization summary for response
        response_optimization_summary = None
        if optimization_success and optimization_summary:
            response_optimization_summary = optimization_summary

        return {
            "resume_id": resume_id,
            "ats_score": ats_score,
            "matching_skills": score_result.get("matching_skills", []),
            "missing_skills": score_result.get("missing_skills", []),
            "recommendation": recommendation,
            "resume_skills": score_result.get("resume_skills", []),
            "job_requirements": score_result.get("job_requirements", []),
            "optimization_success": optimization_success,
            "optimized_score": optimized_score,
            "score_improvement": score_improvement if optimization_success else 0,
            "optimization_summary": response_optimization_summary
        }

    except Exception as e:
        logger.error(f"Error during resume scoring: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")

        # Check for specific error types
        if "API key" in str(e).lower() or "authentication" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error authenticating with AI service. Please check API configuration.",
            )
        elif "timeout" in str(e).lower() or "time" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service request timed out. Please try again later.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during resume scoring: {str(e)}",
            )


@resume_router.get(
    "/{resume_id}/download",
    summary="Download a resume as PDF",
    response_description="Resume downloaded successfully",
)
async def download_resume(
    resume_id: str,
    use_optimized: bool = True,
    template: str = "resume_template.tex",
    request: Request = None,
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Download a resume as a PDF file.

    This endpoint generates a PDF version of the resume using LaTeX templates.
    By default, it uses the optimized version of the resume.

    Args:
        resume_id: ID of the resume to download
        use_optimized: Whether to use the optimized version of the resume
        template: LaTeX template to use for generating the PDF
        request: The incoming request
        repo: Resume repository instance

    Returns:
    -------
        FileResponse: PDF file download

    Raises:
    ------
        HTTPException: If the resume is not found or PDF generation fails
    """
    # Check if resume_id is "undefined" or invalid
    if resume_id == "undefined" or not resume_id:
        logger.error(f"Invalid resume ID for download: {resume_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID. Please provide a valid resume ID.",
        )

    try:
        resume = await repo.get_resume_by_id(resume_id)
        if not resume:
            logger.warning(f"Resume not found with ID: {resume_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found",
            )
    except Exception as e:
        logger.error(f"Error retrieving resume with ID {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving resume: {str(e)}",
        )
    if use_optimized and not resume.get("optimized_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Optimized resume data not available. Please optimize the resume first.",
        )
    try:
        # Define the absolute path to the templates directory within the Docker container
        # This path corresponds to where the 'app/services/resume/latex_templates' directory
        # from the host is copied into the container via the Dockerfile (COPY ./app /code/app)
        # and the WORKDIR /code instruction.
        container_template_dir = "/code/app/services/resume/latex_templates"
        generator = LaTeXGenerator(container_template_dir)
        if use_optimized:
            json_data = resume["optimized_data"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Downloading original resume as PDF is not supported. Please optimize first.",
            )
        if isinstance(json_data, str):
            generator.parse_json_from_string(json_data)
        else:
            generator.json_data = json_data
        latex_content = generator.generate_from_template(template)
        if not latex_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate LaTeX content",
            )
        pdf_path = create_temporary_pdf(latex_content)
        if not pdf_path:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create PDF",
            )
        filename = f"{resume.get('title', 'resume')}_{secrets.token_hex(4)}.pdf"
        return FileResponse(
            path=pdf_path,
            filename=filename,
            media_type="application/pdf",
            background=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}",
        )


@resume_router.get(
    "/{resume_id}/download-latex",
    summary="Download a resume as LaTeX source",
    response_description="LaTeX source file downloaded successfully",
)
async def download_resume_latex(
    resume_id: str,
    template: str = "resume_template.tex",
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Download a resume as a LaTeX source file.

    This endpoint generates LaTeX source code for the resume using LaTeX templates.
    It uses the optimized version of the resume.

    Args:
        resume_id: ID of the resume to download
        template: LaTeX template to use for generating the LaTeX source
        repo: Resume repository instance

    Returns:
    -------
        Response: LaTeX source file download

    Raises:
    ------
        HTTPException: If the resume is not found or LaTeX generation fails
    """
    # Check if resume_id is "undefined" or invalid
    if resume_id == "undefined" or not resume_id:
        logger.error(f"Invalid resume ID for LaTeX download: {resume_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resume ID. Please provide a valid resume ID.",
        )

    try:
        resume = await repo.get_resume_by_id(resume_id)
        if not resume:
            logger.warning(f"Resume not found with ID: {resume_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Resume with ID {resume_id} not found",
            )
    except Exception as e:
        logger.error(f"Error retrieving resume with ID {resume_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving resume: {str(e)}",
        )

    if not resume.get("optimized_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Optimized resume data not available. Please optimize the resume first.",
        )

    try:
        # Define the absolute path to the templates directory within the Docker container
        container_template_dir = "/code/app/services/resume/latex_templates"
        generator = LaTeXGenerator(container_template_dir)

        json_data = resume["optimized_data"]

        if isinstance(json_data, str):
            generator.parse_json_from_string(json_data)
        else:
            generator.json_data = json_data

        latex_content = generator.generate_from_template(template)
        if not latex_content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate LaTeX content",
            )

        filename = f"{resume.get('title', 'resume')}_{secrets.token_hex(4)}.tex"

        return Response(
            content=latex_content,
            media_type="application/x-latex",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating LaTeX: {str(e)}",
        )


@resume_router.get(
    "/{resume_id}/preview",
    summary="Preview a resume",
    response_description="Resume previewed successfully",
)
async def preview_resume(
    resume_id: str,
    request: Request,
    repo: ResumeRepository = Depends(get_resume_repository),
):
    """Preview a resume (not implemented).

    This endpoint is intended for previewing a resume, but it's not yet implemented.

    Args:
        resume_id: ID of the resume to preview
        request: The incoming request
        repo: Resume repository instance

    Raises:
    ------
        HTTPException: Always raises a 501 Not Implemented error
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume preview not implemented. Use the download endpoint to generate a PDF.",
    )


@resume_router.post(
    "/contact",
    response_model=ContactFormResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit contact form",
    response_description="Contact form submission status",
)
async def submit_contact_form(
    request: ContactFormRequest = Body(...),
) -> ContactFormResponse:
    """Submit a contact form.

    This endpoint processes contact form submissions from users wanting to reach out
    to the project maintainers, report issues, or ask questions.

    Args:
        request: The contact form data including name, email, subject, and message

    Returns:
    -------
        ContactFormResponse: Success status and confirmation message

    Raises:
    ------
        HTTPException: If there's an issue processing the form
    """
    try:
        # In a production environment, this would typically:
        # 1. Store the message in a database
        # 2. Send an email notification to administrators
        # 3. Potentially send an auto-response to the user

        # For now, we'll just return a success response
        # TODO: Implement actual email sending functionality

        return ContactFormResponse(
            success=True,
            message="Thank you for your message! We'll get back to you soon.",
        )
    except Exception as e:
        # Log the error in a production environment
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process your message: {str(e)}",
        )
