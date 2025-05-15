"""Test script for UUID fix.

This script tests the fix for the UUID encoding issue with MongoDB.
It creates a TokenUsage object and tries to save it to MongoDB.
"""

import asyncio
import os
import uuid
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.database.models.token_usage import TokenUsage
from app.database.repositories.token_usage_repository import TokenUsageRepository


async def test_token_usage_repository():
    """Test the TokenUsageRepository with a UUID field."""
    print("Testing TokenUsageRepository with UUID field...")

    # Set the MongoDB URL directly
    mongodb_url = "mongodb://192.168.7.10:27017/myresumo"
    print(f"MongoDB URL: {mongodb_url}")

    # Create a TokenUsage object with a UUID field
    token_usage = TokenUsage(
        id=uuid.uuid4(),
        timestamp=datetime.now(),
        endpoint="test_endpoint",
        llm_model="gpt-4",
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        request_id="test_request_id",
        user_id="test_user_id",
        feature="test_feature",
        status="success",
        cost_usd=0.01,
        metadata={"test": "metadata"}
    )

    # Create a repository with the direct URL
    repo = TokenUsageRepository(connection_string=mongodb_url)

    # Try to save the TokenUsage object
    try:
        result = await repo.create_token_usage(token_usage)
        print(f"Successfully saved TokenUsage with ID: {result}")

        # Try to retrieve the TokenUsage object by MongoDB _id
        print(f"Trying to retrieve TokenUsage with result ID: {result}")

        # Try to find the document using a query
        all_records = await repo.find({})
        print(f"Found {len(all_records)} records")

        if all_records:
            print(f"First record: {all_records[0]}")

        return True
    except Exception as e:
        print(f"Error saving TokenUsage: {str(e)}")
        return False


async def main():
    """Run the tests."""
    success = await test_token_usage_repository()
    if success:
        print("All tests passed!")
    else:
        print("Tests failed!")


if __name__ == "__main__":
    asyncio.run(main())
