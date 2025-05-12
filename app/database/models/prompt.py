"""Prompt models module.

This module defines the Pydantic data models for system prompts used in the
AI components of the application. These models are used for storing, retrieving,
and validating prompt templates.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import Field

from app.database.models.base import BaseSchema


class PromptTemplate(BaseSchema):
    """Model representing a prompt template used by the AI system.

    Attributes:
    ----------
        id (UUID): Unique identifier for the prompt template
        name (str): Name/identifier of the prompt template
        description (str): Description of what the prompt is used for
        template (str): The actual prompt template text
        component (str): The component that uses this prompt (e.g., "ats_scoring", "resume_optimization")
        variables (List[str]): List of variable names used in the template
        created_at (datetime): When the prompt was created
        updated_at (datetime): When the prompt was last updated
        is_active (bool): Whether this prompt is currently active
        version (int): Version number of the prompt
        metadata (Optional[Dict]): Additional metadata about the prompt
    """

    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    template: str
    component: str
    variables: List[str]
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    version: int = 1
    metadata: Optional[Dict] = None


class PromptUpdate(BaseSchema):
    """Model for updating a prompt template.

    This model is used for partial updates to prompt templates.

    Attributes:
    ----------
        description (Optional[str]): Updated description
        template (Optional[str]): Updated template text
        variables (Optional[List[str]]): Updated list of variables
        is_active (Optional[bool]): Updated active status
        metadata (Optional[Dict]): Updated metadata
    """

    description: Optional[str] = None
    template: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict] = None
