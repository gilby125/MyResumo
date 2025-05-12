# Direct Access to Prompts Management

## Problem

The Swagger UI was not showing the PROMPTS endpoints in the OpenAPI schema, making it difficult to manage system prompts through the API.

## Solution

We've implemented a two-part solution:

1. **Direct API Endpoints**: Created direct API endpoints in the main app that bypass the router
2. **Web-based Prompts Editor**: Added a dedicated web page for managing prompts

## Changes Made

### 1. Added Direct API Endpoints

In `app/main.py`, we added direct API endpoints that bypass the router:

```python
@app.get("/api/prompts-direct", tags=["Prompts"], summary="Get all prompts (direct)")
async def get_all_prompts_direct():
    """Get all prompt templates directly."""
    # Implementation...

@app.put("/api/prompts-direct/{prompt_id}", tags=["Prompts"], summary="Update a prompt (direct)")
async def update_prompt_direct(prompt_id: str, update_data: dict):
    """Update a specific prompt by ID directly."""
    # Implementation...

@app.post("/api/prompts-direct/initialize", tags=["Prompts"], summary="Initialize default prompts (direct)")
async def initialize_default_prompts_direct():
    """Initialize the database with default prompts directly."""
    # Implementation...

@app.get("/api/prompts-direct/{prompt_id}", tags=["Prompts"], summary="Get a prompt by ID (direct)")
async def get_prompt_direct(prompt_id: str):
    """Get a specific prompt by ID directly."""
    # Implementation...
```

These endpoints are defined directly in the main app, ensuring they're included in the OpenAPI schema.

### 2. Created a Web-based Prompts Editor

We created a dedicated web page for managing prompts:

1. **Added a new template** in `app/templates/prompts_editor.html`:
   - Provides a user-friendly interface for viewing and editing prompts
   - Uses Alpine.js for reactive UI components
   - Communicates with the direct API endpoints

2. **Added a route** in `app/main.py` to access the prompts editor:
   ```python
   @app.get("/prompts", tags=["Web"], include_in_schema=False)
   async def prompts_editor_page(request: Request):
       """Render the prompts editor page."""
       return templates.TemplateResponse("prompts_editor.html", {"request": request})
   ```

## How to Use

### Option 1: Web-based Prompts Editor

1. Navigate to `/prompts` in your browser
2. You'll see a list of all available prompts
3. Click on a prompt to edit it
4. Make your changes and click "Save Changes"
5. You can also initialize default prompts by clicking the "Initialize Default Prompts" button

### Option 2: Direct API Endpoints

You can use the direct API endpoints:

- `GET /api/prompts-direct` - Get all prompts
- `GET /api/prompts-direct/{prompt_id}` - Get a specific prompt
- `PUT /api/prompts-direct/{prompt_id}` - Update a prompt
- `POST /api/prompts-direct/initialize` - Initialize default prompts

These endpoints should be visible in the Swagger UI at `/docs`.

## Why This Approach Works

This approach works because:

1. **Bypassing the Router**: By defining the endpoints directly in the main app, we ensure they're included in the OpenAPI schema.
2. **Web-based Interface**: The web-based interface provides a user-friendly way to manage prompts without relying on the Swagger UI.
3. **Direct Access**: The direct API endpoints provide a reliable way to access and manage prompts programmatically.

## Next Steps

After applying these changes:

1. Restart the application
2. Navigate to `/prompts` to access the web-based prompts editor
3. Check the Swagger UI at `/docs` to see if the direct API endpoints are visible
4. If needed, use the direct API endpoints to manage prompts programmatically
