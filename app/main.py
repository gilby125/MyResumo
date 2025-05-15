"""Main application entry point for MyResumo.

This module initializes the FastAPI application, configures routers, middleware,
and handles application startup and shutdown events. It serves as the central
coordination point for the entire application.
"""

import os
import pathlib
from datetime import datetime

# Import version information
from app.version import __version__, get_version_info

# Import debug script
import app.debug_version

# Load environment variables from .env.local if it exists (for local development)
env_local_path = pathlib.Path(__file__).parent.parent / '.env.local'
if env_local_path.exists():
    print(f"Loading environment variables from {env_local_path}")
    from dotenv import load_dotenv
    load_dotenv(env_local_path)

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers.resume import resume_router
from app.api.routers.token_usage import router as token_usage_router
from app.api.routers.prompts import prompts_router
from app.database.connector import MongoConnectionManager
from app.web.core import core_web_router
from app.web.dashboard import web_router

# Initialize Jinja2 templates for HTML rendering
# Setup templates with custom context processor
class CustomTemplates(Jinja2Templates):
    def TemplateResponse(self, name, context, *args, **kwargs):
        # Add current_year and version to context if not already present
        request = context.get("request")
        if request and hasattr(request, "state"):
            if "current_year" not in context and hasattr(request.state, "current_year"):
                context["current_year"] = request.state.current_year
            if "version" not in context and hasattr(request.state, "version"):
                context["version"] = request.state.version
        return super().TemplateResponse(name, context, *args, **kwargs)

templates = CustomTemplates(directory="app/templates")


async def startup_logic(app: FastAPI) -> None:
    """Execute startup logic for the FastAPI application.

    Initialize database connections and other resources needed by the application.

    Args:
        app: The FastAPI application instance

    Raises:
    ------
        Exception: If any startup operation fails
    """
    try:
        # Clear the OpenAPI schema to ensure it's regenerated with all routes
        app.openapi_schema = None
        print("OpenAPI schema cleared for regeneration")

        # Initialize database connection
        connection_manager = MongoConnectionManager()
        app.state.mongo = connection_manager
        print("MongoDB connection manager initialized")

        # Initialize default prompts
        try:
            from app.database.repositories.prompt_repository import PromptRepository
            # Create repository with connection string from environment
            mongodb_url = os.getenv("MONGODB_URL")
            prompt_repo = PromptRepository(connection_string=mongodb_url)
            print(f"MongoDB URL: {prompt_repo.connection_string}")

            # Test MongoDB connection
            try:
                # Try a simple operation to test the connection
                await prompt_repo.get_all_prompts()
                print("MongoDB connection test successful")
            except Exception as conn_err:
                print(f"MongoDB connection test failed: {conn_err}")

            # Try to initialize default prompts
            try:
                await prompt_repo.initialize_default_prompts()
                print("Default prompts initialized successfully")
            except Exception as prompt_err:
                print(f"Failed to initialize default prompts: {prompt_err}")
                # Continue anyway - we'll handle errors in the API endpoints
        except Exception as repo_err:
            print(f"Error initializing prompt repository: {repo_err}")
    except Exception as e:
        print(f"Error during startup: {e}")
        # Don't raise the exception - let the application start anyway
        # We'll handle errors in the API endpoints


async def shutdown_logic(app: FastAPI) -> None:
    """Execute shutdown logic for the FastAPI application.

    Properly close database connections and clean up resources.

    Args:
        app: The FastAPI application instance
    """
    try:
        await app.state.mongo.close_all()
        print("Successfully closed all database connections")
    except Exception as e:
        print(f"Error during shutdown: {e}")
    finally:
        print("Shutting down background tasks.")


app = FastAPI(
    title="MyResumo API",
    summary="",
    description="""
    MyResumo is an AI-backed resume generator designed to tailor your resume and skills based on a given job description. This innovative tool leverages the latest advancements in AI technology to provide you with a customized resume that stands out.
    """,
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    version=__version__,
    docs_url=None,
    # Ensure all routes are included in the OpenAPI schema
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Hide schemas section by default
        "displayOperationId": True,      # Show operation IDs
        "filter": True,                  # Enable filtering
        "showExtensions": True,          # Show vendor extensions
        "showCommonExtensions": True     # Show common extensions
    },
)


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom exception handler for HTTP exceptions.

    Renders the 404.html template for 404 errors.
    For other HTTP errors, renders a basic error page or returns JSON for API routes.

    Args:
        request: The incoming request
        exc: The HTTP exception that was raised

    Returns:
    -------
        An appropriate response based on the request type and error
    """
    if exc.status_code == 404:
        # Check if this is an API request or a web page request
        if request.url.path.startswith("/api"):
            return JSONResponse(
                status_code=404, content={"detail": "Resource not found"}
            )
        # For web requests, render our custom 404 page
        return templates.TemplateResponse(
            "404.html", {"request": request}, status_code=404
        )

    # For API routes, return JSON error
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code, content={"detail": str(exc.detail)}
        )

    # For other errors on web routes, show a simple error page
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "status_code": exc.status_code, "detail": str(exc.detail)},
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom exception handler for request validation errors.

    Args:
        request: The incoming request
        exc: The validation error that was raised

    Returns:
    -------
        JSON response for API routes or template response for web routes
    """
    # For API routes, return JSON error
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    # For web routes, show an error page with validation details
    return templates.TemplateResponse(
        "404.html",
        {
            "request": request,
            "status_code": 422,
            "detail": "Validation Error: Please check your input data.",
        },
        status_code=422,
    )


@app.middleware("http")
async def add_response_headers(request: Request, call_next):
    """Middleware to add response headers and handle flashed messages.

    Args:
        request: The incoming request
        call_next: The next middleware or route handler

    Returns:
    -------
        The response with added security headers
    """
    # Store the current year in the request state for templates
    request.state.current_year = datetime.now().year
    request.state.version = __version__

    response = await call_next(request)

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response


# Add middleware and static file mounts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/templates", StaticFiles(directory="app/templates"), name="templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Serve custom Swagger UI HTML for API documentation.

    Returns:
    -------
        HTMLResponse: Custom Swagger UI HTML

    Raises:
    ------
        FileNotFoundError: If the custom Swagger template is not found
    """
    try:
        # Clear the OpenAPI schema to force regeneration
        app.openapi_schema = None

        with open("app/templates/custom_swagger.html") as f:
            template = f.read()

        # Force reload the OpenAPI schema by adding a timestamp parameter
        import time
        timestamp = int(time.time())
        openapi_url = f"/openapi.json?t={timestamp}"

        # Log that we're serving the Swagger UI
        print(f"Serving Swagger UI with OpenAPI schema URL: {openapi_url}")

        # Ensure all routers are included in the schema
        # This is a workaround for FastAPI sometimes not including all routers
        for router in app.routes:
            if hasattr(router, "include_in_schema"):
                router.include_in_schema = True

        # Verify that prompts endpoints are included in the schema
        openapi_schema = app.openapi()
        has_prompts = False
        for path in openapi_schema.get("paths", {}):
            if path.startswith("/api/prompts"):
                has_prompts = True
                print(f"Found prompts endpoint: {path}")

        if not has_prompts:
            print("WARNING: No prompts endpoints found in the OpenAPI schema!")

        return HTMLResponse(
            template.replace("{{ title }}", "MyResumo API Documentation").replace(
                "{{ openapi_url }}", openapi_url
            )
        )
    except FileNotFoundError:
        return HTMLResponse(
            content="Custom Swagger template not found", status_code=500
        )
    except Exception as e:
        print(f"Error loading Swagger documentation: {str(e)}")
        return HTMLResponse(
            content=f"Error loading documentation: {str(e)}", status_code=500
        )


@app.get("/health", tags=["Health"], summary="Health Check")
async def health_check():
    """Health check endpoint for monitoring and container orchestration.

    Returns:
    -------
        JSONResponse: Status information about the application.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "version": __version__,
            "service": "myresumo",
            "version_info": get_version_info()
        }
    )


# Direct API endpoints for prompts management
@app.get("/api/prompts-direct", tags=["Prompts"], summary="Get all prompts (direct)")
async def get_all_prompts_direct():
    """Get all prompt templates directly.

    This endpoint bypasses the router to ensure it's included in the OpenAPI schema.

    Returns:
    -------
        JSONResponse: List of all prompts
    """
    try:
        print("Retrieving all prompts directly...")
        from app.database.repositories.prompt_repository import PromptRepository

        # Create repository with connection string from environment
        mongodb_url = os.getenv("MONGODB_URL")
        print(f"Using MongoDB URL: {mongodb_url}")

        repo = PromptRepository(connection_string=mongodb_url)

        # First check if we have any prompts
        prompts = await repo.get_all_prompts(include_inactive=True)

        # If no prompts found, initialize default prompts
        if not prompts:
            print("No prompts found, initializing default prompts...")
            await repo.initialize_default_prompts()
            prompts = await repo.get_all_prompts(include_inactive=True)

        print(f"Retrieved {len(prompts)} prompts from database")

        # Debug: Print the raw prompts
        print(f"Raw prompts: {prompts}")

        # Format response
        from app.api.routers.prompts import PromptResponse
        formatted_prompts = []

        # Debug: Check if prompts is empty
        if not prompts:
            print("WARNING: No prompts found in the database!")
            # Return an empty list instead of raising an exception
            return {"prompts": []}

        for prompt in prompts:
            print(f"Processing prompt: {prompt}")

            # Ensure ID is a string
            if "id" not in prompt or prompt["id"] is None:
                prompt["id"] = str(prompt.get("_id", "unknown"))
                print(f"Using _id as ID: {prompt['id']}")
            else:
                prompt["id"] = str(prompt["id"])
                print(f"Using existing ID: {prompt['id']}")

            # Handle any missing fields with defaults
            if "description" not in prompt:
                prompt["description"] = ""
            if "template" not in prompt:
                prompt["template"] = ""
            if "component" not in prompt:
                prompt["component"] = "unknown"
            if "variables" not in prompt:
                prompt["variables"] = []
            if "is_active" not in prompt:
                prompt["is_active"] = True
            if "version" not in prompt:
                prompt["version"] = 1

            try:
                # Convert to dict to avoid serialization issues
                prompt_response = PromptResponse(**prompt)
                formatted_prompts.append(prompt_response.model_dump())
            except Exception as prompt_err:
                print(f"Error formatting prompt: {str(prompt_err)}, prompt: {prompt}")
                # Add a simplified version if full conversion fails
                formatted_prompts.append({
                    "id": str(prompt.get("id", "unknown")),
                    "name": prompt.get("name", "Unknown"),
                    "description": prompt.get("description", ""),
                    "template": prompt.get("template", ""),
                    "component": prompt.get("component", "unknown"),
                    "variables": prompt.get("variables", []),
                    "is_active": prompt.get("is_active", True),
                    "version": prompt.get("version", 1)
                })

        return {"prompts": formatted_prompts}
    except Exception as e:
        print(f"Error retrieving prompts: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error retrieving prompts: {str(e)}"}
        )


@app.put("/api/prompts-direct/{prompt_id}", tags=["Prompts"], summary="Update a prompt (direct)")
async def update_prompt_direct(prompt_id: str, update_data: dict):
    """Update a specific prompt by ID directly.

    This endpoint bypasses the router to ensure it's included in the OpenAPI schema.

    Args:
        prompt_id: ID of the prompt to update
        update_data: Data to update in the prompt

    Returns:
    -------
        JSONResponse: Success status
    """
    try:
        from app.database.repositories.prompt_repository import PromptRepository
        from app.database.models.prompt import PromptUpdate

        # Log the update request
        print(f"Updating prompt {prompt_id} with data: {update_data}")

        repo = PromptRepository()

        # Check if prompt exists
        prompt = await repo.get_prompt_by_id(prompt_id)
        if not prompt:
            error_msg = f"Prompt with ID {prompt_id} not found"
            print(error_msg)
            return JSONResponse(
                status_code=404,
                content={"detail": error_msg}
            )

        # Validate the update data
        if not isinstance(update_data, dict):
            error_msg = f"Invalid update data: {update_data}"
            print(error_msg)
            return JSONResponse(
                status_code=400,
                content={"detail": error_msg}
            )

        # Ensure required fields are present
        for field in ["description", "template", "variables", "is_active"]:
            if field not in update_data:
                error_msg = f"Missing required field: {field}"
                print(error_msg)
                return JSONResponse(
                    status_code=400,
                    content={"detail": error_msg}
                )

        # Ensure variables is a list
        if not isinstance(update_data["variables"], list):
            error_msg = "Variables must be a list"
            print(error_msg)
            return JSONResponse(
                status_code=400,
                content={"detail": error_msg}
            )

        try:
            # Convert to PromptUpdate model
            try:
                # Print the update data for debugging
                print(f"Creating PromptUpdate with data: {update_data}")

                # Create the PromptUpdate model with explicit field assignments
                # to ensure proper validation and type conversion
                prompt_update = PromptUpdate(
                    description=update_data.get("description"),
                    template=update_data.get("template"),
                    variables=update_data.get("variables", []),
                    is_active=update_data.get("is_active")
                )

                # Print the created model for debugging
                print(f"Created PromptUpdate model: {prompt_update.model_dump()}")
            except Exception as validation_error:
                error_msg = f"Invalid prompt data: {str(validation_error)}"
                print(error_msg)
                return JSONResponse(
                    status_code=400,
                    content={"detail": error_msg}
                )

            # Update prompt
            try:
                # Call the update_prompt method and handle the result
                try:
                    success = await repo.update_prompt(prompt_id, prompt_update)
                    if not success:
                        error_msg = "Failed to update prompt - no document was modified"
                        print(error_msg)
                        return JSONResponse(
                            status_code=500,
                            content={"detail": error_msg}
                        )

                    print(f"Successfully updated prompt {prompt_id}")
                    return {"success": True}
                except AttributeError as attr_error:
                    # Handle the specific error we're seeing
                    error_msg = f"Attribute error during update: {str(attr_error)}"
                    print(error_msg)
                    return JSONResponse(
                        status_code=500,
                        content={"detail": error_msg}
                    )
            except Exception as update_error:
                error_msg = f"Database error while updating prompt: {str(update_error)}"
                print(error_msg)
                return JSONResponse(
                    status_code=500,
                    content={"detail": error_msg}
                )
        except Exception as model_error:
            error_msg = f"Error processing prompt update: {str(model_error)}"
            print(error_msg)
            return JSONResponse(
                status_code=400,
                content={"detail": error_msg}
            )
    except Exception as e:
        error_msg = f"Error updating prompt: {str(e)}"
        print(error_msg)
        return JSONResponse(
            status_code=500,
            content={"detail": error_msg}
        )


@app.post("/api/prompts-direct/initialize", tags=["Prompts"], summary="Initialize default prompts (direct)")
async def initialize_default_prompts_direct():
    """Initialize the database with default prompts directly.

    This endpoint bypasses the router to ensure it's included in the OpenAPI schema.

    Returns:
    -------
        JSONResponse: Success status
    """
    try:
        print("Starting initialization of default prompts")
        from app.database.repositories.prompt_repository import PromptRepository
        from app.database.models.prompt import PromptTemplate
        from uuid import uuid4

        # Create repository with connection string from environment
        mongodb_url = os.getenv("MONGODB_URL")
        print(f"Using MongoDB URL: {mongodb_url}")

        repo = PromptRepository(
            connection_string=mongodb_url
        )

        # Test connection
        try:
            print(f"Testing MongoDB connection to {repo.connection_string}")
            await repo.get_all_prompts()
            print("MongoDB connection test successful")
        except Exception as conn_err:
            error_msg = f"MongoDB connection test failed: {str(conn_err)}"
            print(error_msg)
            return JSONResponse(
                status_code=500,
                content={"detail": error_msg}
            )

        # Initialize default prompts
        try:
            print("Initializing default prompts")

            # Check if we already have prompts
            existing_prompts = await repo.get_all_prompts(include_inactive=True)
            print(f"Found {len(existing_prompts)} existing prompts")

            # Debug: Print the existing prompts
            for i, prompt in enumerate(existing_prompts):
                print(f"Existing prompt {i+1}: {prompt.get('name', 'Unknown')} (ID: {prompt.get('id', 'Unknown')})")

            if existing_prompts:
                print(f"Found {len(existing_prompts)} existing prompts, skipping initialization")
                return {"success": True, "message": f"Found {len(existing_prompts)} existing prompts, skipping initialization"}

            print("No existing prompts found, creating default prompts manually")

            # Create default prompts manually with string IDs
            default_prompts = [
                PromptTemplate(
                    id=str(uuid4()),  # Convert UUID to string
                    name="resume_optimization",
                    description="Prompt for optimizing a resume based on a job description",
                    template="You are an expert resume optimizer. Your task is to optimize the following resume based on the job description provided.\n\nJob Description:\n{{job_description}}\n\nResume:\n{{resume}}\n\nRecommended Skills Section:\n{{recommended_skills_section}}\n\nPlease provide an optimized version of the resume that highlights relevant skills and experience for this job.",
                    component="resume_optimization",
                    variables=["job_description", "resume", "recommended_skills_section"],
                    is_active=True,
                    version=1
                ),
                PromptTemplate(
                    id=str(uuid4()),  # Convert UUID to string
                    name="ats_scoring",
                    description="Prompt for scoring a resume against a job description",
                    template="You are an ATS (Applicant Tracking System) expert. Your task is to score the following resume against the job description provided.\n\nJob Description:\n{{job_description}}\n\nResume:\n{{resume}}\n\nPlease provide a score from 0-100 indicating how well the resume matches the job description, along with a list of matching skills and missing skills.",
                    component="ats_scoring",
                    variables=["job_description", "resume"],
                    is_active=True,
                    version=1
                ),
                PromptTemplate(
                    id=str(uuid4()),  # Convert UUID to string
                    name="skills_extraction",
                    description="Prompt for extracting skills from a job description",
                    template="You are a skills extraction expert. Your task is to extract all the skills mentioned in the following job description.\n\nJob Description:\n{{job_description}}\n\nPlease provide a list of all technical skills, soft skills, and qualifications mentioned in the job description.",
                    component="skills_extraction",
                    variables=["job_description"],
                    is_active=True,
                    version=1
                )
            ]

            # Insert default prompts
            for prompt in default_prompts:
                try:
                    # Convert the model to a dictionary
                    prompt_dict = prompt.model_dump()

                    # Ensure the ID is a string
                    prompt_dict["id"] = str(prompt_dict["id"])

                    # Debug: Print the prompt dictionary before insertion
                    print(f"Inserting prompt: {prompt.name}")
                    print(f"ID type: {type(prompt_dict['id'])}")

                    # Insert the document
                    result = await repo.insert_one(prompt_dict)
                    print(f"Created prompt: {prompt.name} with ID: {result}")
                except Exception as e:
                    print(f"Error creating prompt {prompt.name}: {str(e)}")

            print("Default prompts created successfully")
            return {"success": True, "message": "Default prompts created successfully"}

        except Exception as init_err:
            error_msg = f"Error during prompt initialization: {str(init_err)}"
            print(error_msg)
            return JSONResponse(
                status_code=500,
                content={"detail": error_msg}
            )
    except Exception as e:
        error_msg = f"Error initializing default prompts: {str(e)}"
        print(error_msg)
        return JSONResponse(
            status_code=500,
            content={"detail": error_msg}
        )


@app.get("/api/prompts-direct/{prompt_id}", tags=["Prompts"], summary="Get a prompt by ID (direct)")
async def get_prompt_direct(prompt_id: str):
    """Get a specific prompt by ID directly.

    This endpoint bypasses the router to ensure it's included in the OpenAPI schema.

    Args:
        prompt_id: ID of the prompt to retrieve

    Returns:
    -------
        JSONResponse: Prompt details
    """
    try:
        print(f"Getting prompt with ID: {prompt_id}")
        from app.database.repositories.prompt_repository import PromptRepository
        from app.api.routers.prompts import PromptResponse

        # Create repository with connection string from environment
        repo = PromptRepository(
            connection_string=os.getenv("MONGODB_URL")
        )

        # Get the prompt
        prompt = await repo.get_prompt_by_id(prompt_id)

        if not prompt:
            error_msg = f"Prompt with ID {prompt_id} not found"
            print(error_msg)
            return JSONResponse(
                status_code=404,
                content={"detail": error_msg}
            )

        # Ensure all required fields are present
        if "id" not in prompt or prompt["id"] is None:
            prompt["id"] = str(prompt.get("_id", prompt_id))
        else:
            prompt["id"] = str(prompt["id"])

        # Handle any missing fields with defaults
        if "description" not in prompt:
            prompt["description"] = ""
        if "template" not in prompt:
            prompt["template"] = ""
        if "component" not in prompt:
            prompt["component"] = "unknown"
        if "variables" not in prompt:
            prompt["variables"] = []
        if "is_active" not in prompt:
            prompt["is_active"] = True
        if "version" not in prompt:
            prompt["version"] = 1
        if "name" not in prompt:
            prompt["name"] = f"Prompt {prompt_id}"

        try:
            response = PromptResponse(**prompt)
            print(f"Successfully retrieved prompt: {prompt['name']}")
            return response
        except Exception as format_err:
            error_msg = f"Error formatting prompt response: {str(format_err)}"
            print(error_msg)
            # Return a simplified response if formatting fails
            return {
                "id": str(prompt.get("id", prompt_id)),
                "name": prompt.get("name", f"Prompt {prompt_id}"),
                "description": prompt.get("description", ""),
                "template": prompt.get("template", ""),
                "component": prompt.get("component", "unknown"),
                "variables": prompt.get("variables", []),
                "is_active": prompt.get("is_active", True),
                "version": prompt.get("version", 1)
            }
    except Exception as e:
        error_msg = f"Error retrieving prompt: {str(e)}"
        print(error_msg)
        return JSONResponse(
            status_code=500,
            content={"detail": error_msg}
        )


@app.get("/api/config/mongodb", tags=["Configuration"], summary="Get MongoDB Configuration")
async def get_mongodb_config():
    """Get the current MongoDB configuration.

    Returns:
    -------
        JSONResponse: Current MongoDB configuration
    """
    mongodb_url = os.getenv("MONGODB_URL")

    # Mask password if present
    masked_url = mongodb_url
    if mongodb_url and "@" in mongodb_url:
        parts = mongodb_url.split("@")
        auth_part = parts[0]
        if ":" in auth_part:
            protocol_user = auth_part.split(":")
            masked_url = f"{protocol_user[0]}:****@{parts[1]}"

    return {
        "mongodb_url": masked_url,
        "is_default": mongodb_url is None
    }


@app.post("/api/config/mongodb", tags=["Configuration"], summary="Set MongoDB Configuration")
async def set_mongodb_config(config: dict):
    """Set the MongoDB configuration.

    Args:
        config: Configuration with mongodb_url

    Returns:
    -------
        JSONResponse: Success status
    """
    if "mongodb_url" not in config:
        return JSONResponse(
            status_code=400,
            content={"detail": "mongodb_url is required"}
        )

    mongodb_url = config["mongodb_url"]

    # Set environment variable
    os.environ["MONGODB_URL"] = mongodb_url

    # Test the connection
    try:
        from app.database.repositories.prompt_repository import PromptRepository
        repo = PromptRepository(connection_string=mongodb_url)
        await repo.get_all_prompts()
        return {"success": True, "message": "MongoDB configuration updated and connection tested successfully"}
    except Exception as e:
        error_msg = f"MongoDB connection test failed: {str(e)}"
        print(error_msg)
        return JSONResponse(
            status_code=500,
            content={"detail": error_msg}
        )


@app.get("/api/schema", tags=["Development"], summary="Get OpenAPI Schema", include_in_schema=False)
async def get_openapi_schema():
    """Get the OpenAPI schema directly as JSON.

    This is useful for debugging issues with the Swagger UI.

    Returns:
    -------
        JSONResponse: The complete OpenAPI schema
    """
    # Force regeneration of the OpenAPI schema
    app.openapi_schema = None  # Clear the cached schema
    openapi_schema = app.openapi()

    # Check if prompts endpoints are included
    has_prompts = False
    for path in openapi_schema.get("paths", {}):
        if path.startswith("/api/prompts"):
            has_prompts = True
            break

    # Add a debug field
    openapi_schema["_debug"] = {
        "has_prompts_endpoints": has_prompts,
        "generated_at": datetime.now().isoformat(),
        "app_version": app.version
    }

    return JSONResponse(content=openapi_schema)


@app.get("/api/refresh-schema", tags=["Development"], summary="Refresh OpenAPI Schema", include_in_schema=False)
async def refresh_openapi_schema():
    """Force refresh the OpenAPI schema and redirect to the Swagger UI.

    This is useful for fixing issues with the Swagger UI not showing all endpoints.

    Returns:
    -------
        RedirectResponse: Redirect to the Swagger UI
    """
    # Clear the cached schema to force regeneration
    app.openapi_schema = None

    # Log that we're refreshing the schema
    print("Manually refreshing OpenAPI schema")

    # Ensure all routers are included in the schema
    for router in app.routes:
        if hasattr(router, "include_in_schema"):
            router.include_in_schema = True

    # Redirect to the Swagger UI
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


# Include routers - These must come BEFORE the catch-all route
# API routers first to ensure they're included in the OpenAPI schema
# Explicitly set include_in_schema=True for all API routers

# Don't include the prompts router since we're using direct endpoints
# app.include_router(
#     prompts_router,
#     include_in_schema=True
# )  # Add prompts management API endpoints

app.include_router(resume_router, include_in_schema=True)
app.include_router(token_usage_router, include_in_schema=True)  # Add token usage tracking API endpoints

# Web routers
app.include_router(core_web_router)
app.include_router(web_router)

# Direct route for prompts editor
@app.get("/prompts", tags=["Web"], include_in_schema=False)
async def prompts_editor_page(request: Request):
    """Render the prompts editor page.

    This page allows administrators to view and edit the system prompts
    used by the AI components.

    Args:
        request: The incoming HTTP request

    Returns:
    -------
        HTMLResponse: The rendered prompts editor page
    """
    return templates.TemplateResponse("prompts_editor_new.html", {"request": request})


# Catch-all for not found pages - IMPORTANT: This must come AFTER including all routers
@app.get("/{path:path}", include_in_schema=False)
async def catch_all(request: Request, path: str):
    """Catch-all route handler for undefined paths.

    This must be defined AFTER all other routes to avoid intercepting valid routes.

    Args:
        request: The incoming request
        path: The path that was not matched by any other route

    Returns:
    -------
        Template response with 404 page
    """
    # Skip handling for paths that should be handled by other middleware/routers
    if path.startswith(("api/", "static/", "templates/", "docs")):
        # Let the normal routing handle these paths
        raise StarletteHTTPException(status_code=404)

    # For truly non-existent routes, render the 404 page
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
