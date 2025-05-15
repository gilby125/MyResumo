"""MongoDB connection management module.

This module provides the MongoConnectionManager class which handles database connections
and implements the singleton pattern to ensure efficient connection reuse throughout
the application. It manages connection pooling and provides context managers for
safe database operations.
"""

import os
from contextlib import asynccontextmanager
from typing import Dict, Optional

import motor.motor_asyncio
from bson.codec_options import CodecOptions
from bson.binary import UuidRepresentation
from dotenv import load_dotenv

load_dotenv()

# Use MONGODB_URL as the standard environment variable name
MONGODB_URL = os.getenv("MONGODB_URL")


class MongoConnectionManager:
    """Singleton class for managing MongoDB connections.

    This class implements the singleton pattern to ensure only one instance of the
    connection manager exists. It manages connection pooling to MongoDB and provides
    methods for retrieving and closing connections.

    Attributes:
        _instance: Class-level singleton instance reference
        _clients: Dictionary of motor AsyncIOMotorClient instances
        url: MongoDB connection string
    """

    _instance: Optional["MongoConnectionManager"] = None
    _clients: Dict[str, motor.motor_asyncio.AsyncIOMotorClient] = {}

    MONGO_CONFIG = {
        "maxPoolSize": 1000,
        "minPoolSize": 50,
        "maxIdleTimeMS": 45000,
        "waitQueueTimeoutMS": 10000,
        "serverSelectionTimeoutMS": 10000,
        "retryWrites": True,
        "uuidRepresentation": "standard"  # Configure UUID representation at client level
    }

    def __new__(cls, connection_string=None):
        """Singleton implementation ensuring only one instance is created.

        Args:
            connection_string: Optional MongoDB connection string

        Returns:
            The singleton MongoConnectionManager instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Store the connection string for initialization
            cls._instance._init_connection_string = connection_string
        return cls._instance

    def __init__(self, connection_string=None):
        """Initialize the MongoConnectionManager with the connection string.

        Args:
            connection_string: Optional MongoDB connection string to override the default

        The initialization only happens once due to the singleton pattern.
        """
        # Only set the URL if it hasn't been set before or if a new connection string is provided
        if not hasattr(self, 'url') or connection_string:
            self.url = connection_string or MONGODB_URL

    async def get_client(self) -> motor.motor_asyncio.AsyncIOMotorClient:
        """Get the MongoDB client instance, creating it if it doesn't exist.

        Returns:
            AsyncIOMotorClient: MongoDB motor client for asynchronous operations
        """
        if "default" not in self._clients:
            self._clients["default"] = motor.motor_asyncio.AsyncIOMotorClient(
                self.url, **self.MONGO_CONFIG
            )
        return self._clients["default"]

    async def close_all(self):
        """Close all active MongoDB connections.

        This method should be called during application shutdown to properly
        release all database connections.
        """
        for client in self._clients.values():
            client.close()
        self._clients.clear()

    @asynccontextmanager
    async def get_collection(self, db_name: str, collection_name: str):
        """Get a MongoDB collection as an async context manager.

        Args:
            db_name: Name of the database
            collection_name: Name of the collection

        Yields:
            motor.motor_asyncio.AsyncIOMotorCollection: The requested collection

        Examples:
            ```python
            async with connection_manager.get_collection("mydb", "users") as collection:
                await collection.find_one({"email": "user@example.com"})
            ```
        """
        client = await self.get_client()
        try:
            # Configure the database with UUID representation
            codec_options = CodecOptions(uuid_representation=UuidRepresentation.STANDARD)
            db = client.get_database(db_name, codec_options=codec_options)
            collection = db[collection_name]
            yield collection
        finally:
            pass
