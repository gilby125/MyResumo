# Direct Fix for Swagger Documentation to Show PROMPTS Endpoints

## Problem

The Swagger UI was not showing the PROMPTS endpoints in the OpenAPI schema. This was likely due to a combination of issues:

1. **Prefix Duplication**: The prompts router was defined with a prefix in its own file, and then included with the same prefix in the main app, causing the endpoints to be registered at an incorrect path.

2. **Schema Caching**: FastAPI caches the OpenAPI schema for performance reasons, so even if the router was correctly included, the schema might not have been regenerated.

## Changes Made

We've made several targeted changes to fix the issue:

### 1. Fixed Router Inclusion

In `app/main.py`, we removed the duplicate prefix when including the prompts router:

```python
# Before:
app.include_router(
    prompts_router, 
    include_in_schema=True,
    prefix="/api/prompts",  # This was duplicating the prefix
    tags=["Prompts"]
)

# After:
app.include_router(
    prompts_router, 
    include_in_schema=True
)
```

This ensures that the endpoints are registered at the correct path (`/api/prompts/...`) instead of a duplicated path (`/api/prompts/api/prompts/...`).

### 2. Cleared OpenAPI Schema Cache

We added code to clear the OpenAPI schema cache at several key points:

1. **During Application Startup**:
   ```python
   async def startup_logic(app: FastAPI) -> None:
       try:
           # Clear the OpenAPI schema to ensure it's regenerated with all routes
           app.openapi_schema = None
           print("OpenAPI schema cleared for regeneration")
           
           # Rest of the startup logic...
   ```

2. **When Serving the Swagger UI**:
   ```python
   @app.get("/docs", include_in_schema=False)
   async def custom_swagger_ui_html():
       try:
           # Clear the OpenAPI schema to force regeneration
           app.openapi_schema = None
           
           # Rest of the function...
   ```

3. **Added Verification**:
   ```python
   # Verify that prompts endpoints are included in the schema
   openapi_schema = app.openapi()
   has_prompts = False
   for path in openapi_schema.get("paths", {}):
       if path.startswith("/api/prompts"):
           has_prompts = True
           print(f"Found prompts endpoint: {path}")
           
   if not has_prompts:
       print("WARNING: No prompts endpoints found in the OpenAPI schema!")
   ```

### 3. Added Debug Endpoint

We added a debug endpoint to view the OpenAPI schema directly:

```python
@app.get("/api/schema", tags=["Development"], summary="Get OpenAPI Schema", include_in_schema=False)
async def get_openapi_schema():
    """Get the OpenAPI schema directly as JSON."""
    # Force regeneration of the OpenAPI schema
    app.openapi_schema = None
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
```

### 4. Added Schema Refresh Endpoint

We added an endpoint to force refresh the OpenAPI schema:

```python
@app.get("/api/refresh-schema", tags=["Development"], summary="Refresh OpenAPI Schema", include_in_schema=False)
async def refresh_openapi_schema():
    """Force refresh the OpenAPI schema and redirect to the Swagger UI."""
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
```

## How to Verify the Fix

After applying these changes and restarting the application, you can verify the fix by:

1. Accessing the Swagger UI at `/docs`
2. Looking for the "Prompts" tag in the list of endpoints
3. If the prompts endpoints still don't appear, check the application logs for any warnings or errors
4. You can also access the `/api/schema` endpoint to see if the prompts endpoints are included in the schema
5. As a last resort, you can use the `/api/refresh-schema` endpoint to force a refresh of the schema

## Why This Approach Works

This approach addresses the root causes of the issue:

1. **Fixing the Router Inclusion**: By removing the duplicate prefix, we ensure the endpoints are registered at the correct path.
2. **Clearing the Schema Cache**: By clearing the cache at key points, we ensure the schema is regenerated with all routes.
3. **Adding Verification**: By verifying that the prompts endpoints are included in the schema, we can detect if there are still issues.
4. **Providing Debug Tools**: By adding debug endpoints, we make it easier to diagnose and fix any remaining issues.

These changes should ensure that all endpoints, including the PROMPTS endpoints, are properly displayed in the Swagger UI without requiring manual refreshes.
