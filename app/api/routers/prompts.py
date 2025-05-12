"""Prompts API router module for managing system prompts.

This module implements the API endpoints for prompt-related functionality including
prompt retrieval, updating, and management. It provides an interface for administrators
to view and modify the prompts used by the AI components of the system.
"""

import logging
from typing import Dict, List, Optional, Union
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.database.models.prompt import PromptTemplate, PromptUpdate
from app.database.repositories.prompt_repository import PromptRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Request and response models
class PromptResponse(BaseModel):
    """Schema for prompt response."""

    id: str = Field(..., description="Unique identifier for the prompt")
    name: str = Field(..., description="Name of the prompt")
    description: str = Field(..., description="Description of the prompt")
    template: str = Field(..., description="The prompt template text")
    component: str = Field(..., description="Component that uses this prompt")
    variables: List[str] = Field(..., description="Variables used in the template")
    is_active: bool = Field(..., description="Whether the prompt is active")
    version: int = Field(..., description="Version number of the prompt")


class PromptListResponse(BaseModel):
    """Schema for list of prompts response."""

    prompts: List[PromptResponse] = Field(..., description="List of prompts")


class CreatePromptRequest(BaseModel):
    """Schema for creating a new prompt."""

    name: str = Field(..., description="Name of the prompt")
    description: str = Field(..., description="Description of the prompt")
    template: str = Field(..., description="The prompt template text")
    component: str = Field(..., description="Component that uses this prompt")
    variables: List[str] = Field(..., description="Variables used in the template")


class UpdatePromptRequest(BaseModel):
    """Schema for updating an existing prompt."""

    description: Optional[str] = Field(None, description="Updated description")
    template: Optional[str] = Field(None, description="Updated template text")
    variables: Optional[List[str]] = Field(None, description="Updated variables")
    is_active: Optional[bool] = Field(None, description="Updated active status")


# Create router
prompts_router = APIRouter(
    prefix="/api/prompts",
    tags=["Prompts"],
    include_in_schema=True,  # Explicitly include in OpenAPI schema
    generate_unique_id_function=lambda route: f"prompts_{route.name}"  # Ensure unique operation IDs
)


async def get_prompt_repository() -> PromptRepository:
    """Dependency for getting the prompt repository instance.

    Returns:
    -------
        PromptRepository: An instance of the prompt repository
    """
    try:
        repo = PromptRepository()
        # Test connection by making a simple query
        await repo.get_all_prompts()
        return repo
    except Exception as e:
        logger.error(f"Failed to initialize prompt repository: {str(e)}")
        # Return the repository anyway to allow the API to be documented
        # Operations will fail at runtime but will be included in the OpenAPI schema
        return PromptRepository()


@prompts_router.get(
    "/",
    response_model=PromptListResponse,
    summary="Get all prompts",
    response_description="List of all prompts",
)
async def get_all_prompts(
    include_inactive: bool = False,
    component: Optional[str] = None,
    repo: PromptRepository = Depends(get_prompt_repository),
):
    """Get all prompt templates.

    Args:
        include_inactive: Whether to include inactive prompts
        component: Filter by component
        repo: Prompt repository instance

    Returns:
    -------
        PromptListResponse: List of prompts
    """
    try:
        if component:
            prompts = await repo.get_prompts_by_component(component)
        else:
            prompts = await repo.get_all_prompts(include_inactive)

        # Format response
        formatted_prompts = []
        for prompt in prompts:
            prompt["id"] = prompt.get("id")  # Ensure ID is a string
            formatted_prompts.append(PromptResponse(**prompt))

        return {"prompts": formatted_prompts}
    except Exception as e:
        logger.error(f"Error retrieving prompts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving prompts: {str(e)}",
        )


@prompts_router.get(
    "/{prompt_id}",
    response_model=PromptResponse,
    summary="Get a prompt by ID",
    response_description="Prompt details",
)
async def get_prompt(
    prompt_id: Union[str, UUID],
    repo: PromptRepository = Depends(get_prompt_repository),
):
    """Get a specific prompt by ID.

    Args:
        prompt_id: ID of the prompt to retrieve
        repo: Prompt repository instance

    Returns:
    -------
        PromptResponse: Prompt details

    Raises:
    ------
        HTTPException: If the prompt is not found
    """
    prompt = await repo.get_prompt_by_id(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found",
        )
    return PromptResponse(**prompt)


@prompts_router.get(
    "/component/{component}",
    response_model=PromptListResponse,
    summary="Get prompts by component",
    response_description="List of prompts for a component",
)
async def get_prompts_by_component(
    component: str,
    repo: PromptRepository = Depends(get_prompt_repository),
):
    """Get all prompts for a specific component.

    Args:
        component: The component to get prompts for
        repo: Prompt repository instance

    Returns:
    -------
        PromptListResponse: List of prompts for the component
    """
    prompts = await repo.get_prompts_by_component(component)
    formatted_prompts = [PromptResponse(**prompt) for prompt in prompts]
    return {"prompts": formatted_prompts}


@prompts_router.put(
    "/{prompt_id}",
    response_model=Dict[str, bool],
    summary="Update a prompt",
    response_description="Prompt updated successfully",
)
async def update_prompt(
    prompt_id: Union[str, UUID],
    update_data: UpdatePromptRequest = Body(...),
    repo: PromptRepository = Depends(get_prompt_repository),
):
    """Update a specific prompt by ID.

    Args:
        prompt_id: ID of the prompt to update
        update_data: Data to update in the prompt
        repo: Prompt repository instance

    Returns:
    -------
        Dict indicating success status

    Raises:
    ------
        HTTPException: If the prompt is not found or update fails
    """
    # Check if prompt exists
    prompt = await repo.get_prompt_by_id(prompt_id)
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt with ID {prompt_id} not found",
        )

    # Convert to PromptUpdate model
    prompt_update = PromptUpdate(**update_data.model_dump(exclude_unset=True))

    # Update prompt
    success = await repo.update_prompt(prompt_id, prompt_update)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prompt",
        )

    return {"success": True}


@prompts_router.post(
    "/initialize",
    response_model=Dict[str, bool],
    summary="Initialize default prompts",
    response_description="Default prompts initialized successfully",
)
async def initialize_default_prompts(
    repo: PromptRepository = Depends(get_prompt_repository),
):
    """Initialize the database with default prompts.

    Args:
        repo: Prompt repository instance

    Returns:
    -------
        Dict indicating success status
    """
    try:
        await repo.initialize_default_prompts()
        return {"success": True}
    except Exception as e:
        logger.error(f"Error initializing default prompts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing default prompts: {str(e)}",
        )
