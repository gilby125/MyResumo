# Swagger Documentation Fix for PROMPTS Endpoints

## Problem

The Swagger UI was not showing all endpoints, specifically the PROMPTS endpoints were missing from the OpenAPI schema.

## Changes Made

We've made several changes to fix the Swagger documentation and ensure the prompts API endpoints are properly displayed:

### 1. Enhanced the Custom Swagger UI Template

In `app/templates/custom_swagger.html`:
- Added timestamp to the OpenAPI URL to force a fresh load of the schema
- Added additional configuration options to show more details in the Swagger UI:
  - `showExtensions: true` - Show vendor extensions
  - `showCommonExtensions: true` - Show common extensions

```javascript
window.onload = function() {
    // Force a fresh load of the OpenAPI schema with a timestamp
    const timestamp = new Date().getTime();
    const openapi_url = "{{ openapi_url }}".includes("?") 
        ? "{{ openapi_url }}&t=" + timestamp 
        : "{{ openapi_url }}?t=" + timestamp;
        
    const ui = SwaggerUIBundle({
        url: openapi_url,
        // ... other options ...
        showExtensions: true,  // Show vendor extensions
        showCommonExtensions: true  // Show common extensions
    });
    window.ui = ui;
}
```

### 2. Updated FastAPI Configuration

In `app/main.py`:
- Enhanced the FastAPI app configuration with additional Swagger UI parameters:

```python
app = FastAPI(
    # ... other options ...
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Hide schemas section by default
        "displayOperationId": True,      # Show operation IDs
        "filter": True,                  # Enable filtering
        "showExtensions": True,          # Show vendor extensions
        "showCommonExtensions": True     # Show common extensions
    },
)
```

### 3. Improved Router Registration

In `app/main.py`:
- Updated how the prompts router is included in the main app to ensure it's properly included in the schema:

```python
app.include_router(
    prompts_router, 
    include_in_schema=True,
    prefix="/api/prompts",  # Ensure prefix is set correctly
    tags=["Prompts"]        # Ensure tag is set correctly
)
```

### 4. Enhanced Swagger UI HTML Generation

In `app/main.py`:
- Updated the `custom_swagger_ui_html` function to ensure all routes are included in the schema:

```python
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    # ... existing code ...
    
    # Ensure all routers are included in the schema
    # This is a workaround for FastAPI sometimes not including all routers
    for router in app.routes:
        if hasattr(router, "include_in_schema"):
            router.include_in_schema = True
    
    # ... rest of the function ...
```

### 5. Added Debug Endpoint

In `app/main.py`:
- Added a new endpoint to view the OpenAPI schema directly for debugging purposes:

```python
@app.get("/api/schema", tags=["Development"], summary="Get OpenAPI Schema", include_in_schema=False)
async def get_openapi_schema():
    """Get the OpenAPI schema directly as JSON."""
    # Force regeneration of the OpenAPI schema
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

## How to Verify the Fix

After applying these changes and restarting the application, you can verify the fix by:

1. Accessing the Swagger UI at `/docs`
2. Looking for the "Prompts" tag in the list of endpoints
3. If the prompts endpoints still don't appear, check the debug endpoint at `/api/schema` to see if they're included in the OpenAPI schema

## Troubleshooting

If the prompts API endpoints still don't appear after applying these changes:

1. Check the application logs for any errors during startup
2. Try using the refresh button in the Swagger UI to reload the OpenAPI schema
3. Access the `/api/schema` endpoint to see if the prompts endpoints are included in the schema
4. Ensure MongoDB is accessible from the application container
5. Check if the prompts router is being properly registered by examining the OpenAPI schema

## Additional Notes

- The changes made are non-invasive and should not affect the functionality of the application
- The fix addresses multiple potential causes of the issue to ensure it's resolved
- The debug endpoint provides a way to verify that the prompts endpoints are included in the schema
