"""Base repository module for database operations.

This module provides the BaseRepository class which implements the repository pattern
for database operations, offering common CRUD methods that other repository classes
can inherit and extend.
"""

import os
from typing import Dict, List, Optional

from app.database.connector import MongoConnectionManager


class BaseRepository:
    """Base repository class for database operations.

    This class implements common database operations like finding, inserting,
    updating, and deleting documents. It uses the MongoDB connection manager
    to handle database connections and provides a consistent interface for
    all repositories in the application.

    Attributes:
        db_name: The name of the database to use
        collection_name: The name of the collection to use
        connection_manager: Instance of MongoDB connection manager
    """

    def __init__(
        self,
        db_name: str,
        collection_name: str,
        connection_string: str = None
    ):
        """Initialize the BaseRepository with database and collection names.

        Args:
            db_name (str): The name of the database.
            collection_name (str): The name of the collection.
            connection_string (str, optional): MongoDB connection string. Defaults to None.
        """
        self.db_name = db_name or os.getenv("DB_NAME", "myresumo")
        self.collection_name = collection_name
        self.connection_manager = MongoConnectionManager(connection_string=connection_string)

    async def find_one(self, query: Dict) -> Optional[Dict]:
        """Find a single document matching the query.

        Args:
            query (Dict): The query to match documents.

        Returns:
        -------
            Optional[Dict]: The matched document or None if not found.
        """
        try:
            # Process the query to handle UUIDs and other special types
            processed_query = self._process_document_for_mongodb(query)

            # Use context manager to handle connection lifecycle
            async with self.connection_manager.get_collection(
                self.db_name, self.collection_name
            ) as collection:
                # Execute query and convert MongoDB ObjectId to string
                document = await collection.find_one(processed_query)
                if document:
                    document["_id"] = str(document["_id"])
                return document
        except Exception as e:
            print(f"Error in find_one: {str(e)}")
            return None

    async def find(self, query: Dict) -> List[Dict]:
        """Find all documents matching the query.

        Args:
            query (Dict): The query to match documents.

        Returns:
        -------
            List[Dict]: A list of matched documents.
        """
        try:
            # Process the query to handle UUIDs and other special types
            processed_query = self._process_document_for_mongodb(query)

            # Establish database connection and execute query
            async with self.connection_manager.get_collection(
                self.db_name, self.collection_name
            ) as collection:
                cursor = collection.find(processed_query)
                documents = await cursor.to_list(length=None)
                # Convert MongoDB ObjectIds to strings for all documents
                for doc in documents:
                    doc["_id"] = str(doc["_id"])
                return documents
        except Exception as e:
            print(f"Error in find: {str(e)}")
            return []

    async def find_many(
        self, query: Dict, sort: Optional[List[tuple]] = None
    ) -> List[Dict]:
        """Find multiple documents matching the query with optional sorting.

        Args:
            query (Dict): The query to match documents.
            sort (Optional[List[tuple]]): Sorting criteria.

        Returns:
        -------
            List[Dict]: A list of matched documents.
        """
        try:
            # Process the query to handle UUIDs and other special types
            processed_query = self._process_document_for_mongodb(query)

            async with self.connection_manager.get_collection(
                self.db_name, self.collection_name
            ) as collection:
                cursor = collection.find(processed_query)
                if sort:
                    cursor.sort(sort)
                documents = await cursor.to_list(length=None)
                for doc in documents:
                    doc["_id"] = str(doc["_id"])
                return documents
        except Exception as e:
            print(f"Error in find_many: {str(e)}")
            return []

    async def insert_one(self, document: Dict) -> str:
        """Insert a single document into the collection.

        Args:
            document (Dict): The document to insert.

        Returns:
        -------
            str: The ID of the inserted document.
        """
        try:
            # Process the document to handle UUIDs and other special types
            processed_document = self._process_document_for_mongodb(document)

            async with self.connection_manager.get_collection(
                self.db_name, self.collection_name
            ) as collection:
                result = await collection.insert_one(processed_document)
                return str(result.inserted_id)
        except Exception as e:
            print(f"Error in insert_one: {str(e)}")
            return ""

    def _process_document_for_mongodb(self, document: Dict) -> Dict:
        """Process a document to make it compatible with MongoDB.

        Converts UUIDs to strings and handles other special types.

        Args:
            document (Dict): The document to process.

        Returns:
            Dict: The processed document.
        """
        processed = {}

        for key, value in document.items():
            # Handle UUIDs
            if hasattr(value, 'hex') and callable(getattr(value, 'hex')):
                processed[key] = str(value)
            # Handle nested dictionaries
            elif isinstance(value, dict):
                processed[key] = self._process_document_for_mongodb(value)
            # Handle lists of dictionaries
            elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
                processed[key] = [self._process_document_for_mongodb(item) for item in value]
            # Handle other types
            else:
                processed[key] = value

        return processed

    async def update_one(self, query: Dict, update: Dict) -> bool:
        """Update a single document matching the query.

        Args:
            query (Dict): The query to match documents.
            update (Dict): The update to apply.

        Returns:
        -------
            bool: True if the update was successful, False otherwise.
        """
        try:
            # Process the query and update to handle UUIDs and other special types
            processed_query = self._process_document_for_mongodb(query)

            # Process the update document
            processed_update = {}
            for operator, value in update.items():
                if isinstance(value, dict):
                    processed_update[operator] = self._process_document_for_mongodb(value)
                else:
                    processed_update[operator] = value

            async with self.connection_manager.get_collection(
                self.db_name, self.collection_name
            ) as collection:
                result = await collection.update_one(processed_query, processed_update)
                return result.modified_count > 0
        except Exception as e:
            print(f"Error in update_one: {str(e)}")
            return False

    async def delete_one(self, query: Dict) -> bool:
        """Delete a single document matching the query.

        Args:
            query (Dict): The query to match documents for deletion.

        Returns:
        -------
            bool: True if deletion was successful, False otherwise.
        """
        try:
            # Process the query to handle UUIDs and other special types
            processed_query = self._process_document_for_mongodb(query)

            async with self.connection_manager.get_collection(
                self.db_name, self.collection_name
            ) as collection:
                result = await collection.delete_one(processed_query)
                return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
