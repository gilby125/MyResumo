"""Prompt repository module.

This module provides the PromptRepository class for managing prompt templates
in the database, including CRUD operations and version management.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Union
from uuid import UUID

from bson import ObjectId
from fastapi import HTTPException, status

from app.database.models.prompt import PromptTemplate, PromptUpdate
from app.database.repositories.base_repo import BaseRepository


class PromptRepository(BaseRepository):
    """Repository for handling prompt-related database operations.

    This class extends BaseRepository to provide specific methods for
    working with prompt templates in the database.
    """

    def __init__(
        self,
        db_name: str = os.getenv("DB_NAME", "myresumo"),
        collection_name: str = "prompts",
    ):
        """Initialize the prompt repository with database and collection names.

        Args:
            db_name (str): Name of the database. Defaults to environment variable or "myresumo".
            collection_name (str): Name of the collection. Defaults to "prompts".
        """
        super().__init__(db_name, collection_name)

    async def create_prompt(self, prompt: PromptTemplate) -> str:
        """Create a new prompt template in the database.

        Args:
            prompt (PromptTemplate): The prompt template to create.

        Returns:
            str: The ID of the created prompt.
        """
        # Convert UUID to string for MongoDB
        prompt_dict = prompt.model_dump()
        prompt_dict["id"] = str(prompt_dict["id"])

        # Insert into database
        result = await self.insert_one(prompt_dict)
        return str(result)

    async def get_prompt_by_id(self, prompt_id: Union[str, UUID]) -> Optional[Dict]:
        """Get a prompt template by its ID.

        Args:
            prompt_id (Union[str, UUID]): The ID of the prompt to retrieve.

        Returns:
            Optional[Dict]: The prompt template data, or None if not found.
        """
        prompt_id_str = str(prompt_id)
        return await self.find_one({"id": prompt_id_str})

    async def get_prompt_by_name(self, name: str) -> Optional[Dict]:
        """Get a prompt template by its name.

        Args:
            name (str): The name of the prompt to retrieve.

        Returns:
            Optional[Dict]: The prompt template data, or None if not found.
        """
        return await self.find_one({"name": name, "is_active": True})

    async def get_prompts_by_component(self, component: str) -> List[Dict]:
        """Get all prompt templates for a specific component.

        Args:
            component (str): The component to get prompts for.

        Returns:
            List[Dict]: List of prompt templates for the component.
        """
        return await self.find({"component": component, "is_active": True})

    async def get_all_prompts(self, include_inactive: bool = False) -> List[Dict]:
        """Get all prompt templates.

        Args:
            include_inactive (bool): Whether to include inactive prompts.

        Returns:
            List[Dict]: List of all prompt templates.
        """
        query = {} if include_inactive else {"is_active": True}
        return await self.find(query)

    async def update_prompt(self, prompt_id: Union[str, UUID], update_data: PromptUpdate) -> bool:
        """Update a prompt template.

        Args:
            prompt_id (Union[str, UUID]): The ID of the prompt to update.
            update_data (PromptUpdate): The data to update.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        prompt_id_str = str(prompt_id)

        # Get the current prompt
        current_prompt = await self.get_prompt_by_id(prompt_id_str)
        if not current_prompt:
            return False

        # Prepare update data
        update_dict = update_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now()

        # Increment version if template is changed
        if "template" in update_dict:
            update_dict["version"] = current_prompt.get("version", 1) + 1

        # Update in database
        result = await self.update_one({"id": prompt_id_str}, {"$set": update_dict})
        return result.modified_count > 0

    async def delete_prompt(self, prompt_id: Union[str, UUID]) -> bool:
        """Delete a prompt template.

        Args:
            prompt_id (Union[str, UUID]): The ID of the prompt to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        prompt_id_str = str(prompt_id)
        result = await self.delete_one({"id": prompt_id_str})
        return result.deleted_count > 0

    async def initialize_default_prompts(self) -> None:
        """Initialize the database with default prompts if they don't exist.

        This method ensures that the system has the necessary prompt templates
        for its core functionality.
        """
        # Check if we already have prompts
        existing_prompts = await self.get_all_prompts(include_inactive=True)
        if existing_prompts:
            return

        # Define default prompts
        from app.services.ai.ats_scoring import ATSScorerLLM
        from app.services.ai.model_ai import AtsResumeOptimizer

        # Create a temporary instance to get the prompt templates
        ats_scorer = ATSScorerLLM.__new__(ATSScorerLLM)
        ats_scorer.setup_prompts()

        # Get the resume optimization template
        # We need to extract the template from the method since it's dynamically generated
        resume_optimizer = AtsResumeOptimizer.__new__(AtsResumeOptimizer)
        # Extract the base template without the missing skills section
        resume_template = resume_optimizer._get_prompt_template().template

        # ATS Scoring prompts
        default_prompts = [
            PromptTemplate(
                name="resume_analysis",
                description="Prompt for extracting skills and qualifications from a resume",
                template=ats_scorer.resume_prompt.template,
                component="ats_scoring",
                variables=["resume_text", "format_instructions"],
            ),
            PromptTemplate(
                name="job_analysis",
                description="Prompt for extracting requirements from a job description",
                template=ats_scorer.job_prompt.template,
                component="ats_scoring",
                variables=["job_text", "format_instructions"],
            ),
            PromptTemplate(
                name="matching_analysis",
                description="Prompt for analyzing the match between resume and job requirements",
                template=ats_scorer.matching_prompt.template,
                component="ats_scoring",
                variables=["resume_skills", "job_requirements"],
            ),
            PromptTemplate(
                name="resume_optimization",
                description="Prompt for optimizing a resume based on a job description",
                template=resume_template,
                component="resume_optimization",
                variables=["job_description", "resume", "recommended_skills_section"],
            ),
        ]

        # Insert default prompts
        for prompt in default_prompts:
            await self.create_prompt(prompt)
