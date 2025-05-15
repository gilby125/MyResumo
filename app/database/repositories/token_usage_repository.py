"""Token usage repository module.

This module provides the TokenUsageRepository class for managing token usage data
in the database, including storing, retrieving, and analyzing token consumption.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from uuid import UUID

from app.database.models.token_usage import TokenUsage, TokenUsageSummary
from app.database.repositories.base_repo import BaseRepository


class TokenUsageRepository(BaseRepository):
    """Repository for handling token usage data in the database.

    This class extends BaseRepository to provide specific methods for
    working with token usage records in the database.
    """

    def __init__(
        self,
        db_name: str = os.getenv("DB_NAME", "myresumo"),
        collection_name: str = "token_usage",
        connection_string: str = os.getenv("MONGODB_URL"),
    ):
        """Initialize the token usage repository with database and collection names.

        Args:
            db_name (str): Name of the database. Defaults to environment variable or "myresumo".
            collection_name (str): Name of the collection. Defaults to "token_usage".
            connection_string (str): MongoDB connection string. Defaults to environment variable.
        """
        # Store the connection string as an instance attribute so it can be accessed
        self.connection_string = connection_string

        # Pass the connection string to the base repository
        super().__init__(db_name, collection_name, connection_string=connection_string)

    async def create_token_usage(self, token_usage: TokenUsage) -> str:
        """Create a new token usage record in the database.

        Args:
            token_usage (TokenUsage): The token usage record to create.

        Returns:
            str: The ID of the created record.
        """
        # Convert the model to a dictionary
        token_usage_dict = token_usage.model_dump()

        # Insert into database
        result = await self.insert_one(token_usage_dict)
        return str(result)

    async def get_token_usage_by_id(self, token_usage_id: Union[str, UUID]) -> Optional[Dict]:
        """Retrieve a token usage record by its ID.

        Args:
            token_usage_id (Union[str, UUID]): The ID of the token usage record.

        Returns:
            Optional[Dict]: The token usage record if found, None otherwise.
        """
        token_usage_id_str = str(token_usage_id)
        return await self.find_one({"id": token_usage_id_str})

    async def get_token_usage_summary(
        self,
        days: int = 30,
        feature: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> TokenUsageSummary:
        """Generate a summary of token usage for the specified period.

        Args:
            days (int): Number of days to include in the summary.
            feature (Optional[str]): Filter by specific feature.
            user_id (Optional[str]): Filter by specific user.

        Returns:
            TokenUsageSummary: Summary of token usage statistics.
        """
        # Calculate the start date for the period
        period_start = datetime.utcnow() - timedelta(days=days)

        # Build the query
        query = {"timestamp": {"$gte": period_start}}
        if feature:
            query["feature"] = feature
        if user_id:
            query["user_id"] = user_id

        # Get all matching records
        records = await self.find(query)

        # Initialize counters
        total_api_calls = len(records)
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        total_cost_usd = 0.0
        usage_by_model = {}
        usage_by_feature = {}

        # Process records
        for record in records:
            # Update totals
            total_prompt_tokens += record.get("prompt_tokens", 0)
            total_completion_tokens += record.get("completion_tokens", 0)
            total_tokens += record.get("total_tokens", 0)
            total_cost_usd += record.get("cost_usd", 0.0)

            # Update model usage
            model = record.get("llm_model", "unknown")
            if model not in usage_by_model:
                usage_by_model[model] = {
                    "calls": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                }
            usage_by_model[model]["calls"] += 1
            usage_by_model[model]["prompt_tokens"] += record.get("prompt_tokens", 0)
            usage_by_model[model]["completion_tokens"] += record.get("completion_tokens", 0)
            usage_by_model[model]["total_tokens"] += record.get("total_tokens", 0)
            usage_by_model[model]["cost_usd"] += record.get("cost_usd", 0.0)

            # Update feature usage
            feature = record.get("feature", "unknown")
            if feature not in usage_by_feature:
                usage_by_feature[feature] = {
                    "calls": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                }
            usage_by_feature[feature]["calls"] += 1
            usage_by_feature[feature]["prompt_tokens"] += record.get("prompt_tokens", 0)
            usage_by_feature[feature]["completion_tokens"] += record.get("completion_tokens", 0)
            usage_by_feature[feature]["total_tokens"] += record.get("total_tokens", 0)
            usage_by_feature[feature]["cost_usd"] += record.get("cost_usd", 0.0)

        # Create and return the summary
        return TokenUsageSummary(
            total_api_calls=total_api_calls,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
            total_cost_usd=total_cost_usd,
            period_start=period_start,
            period_end=datetime.utcnow(),
            usage_by_model=usage_by_model,
            usage_by_feature=usage_by_feature,
        )
