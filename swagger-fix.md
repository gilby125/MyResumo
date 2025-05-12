# Swagger Documentation Fix

## Changes Made

We've made several changes to fix the Swagger documentation and ensure the prompts API endpoints are properly displayed:

### 1. Modified the Prompts Router

In `app/api/routers/prompts.py`:
- Added a unique operation ID generator to ensure each endpoint has a unique ID
- This helps prevent conflicts with other routers that might have similar endpoint names

```python
prompts_router = APIRouter(
    prefix="/api/prompts",
    tags=["Prompts"],
    include_in_schema=True,  # Explicitly include in OpenAPI schema
    generate_unique_id_function=lambda route: f"prompts_{route.name}"  # Ensure unique operation IDs
)
```

### 2. Updated Router Registration in Main App

In `app/main.py`:
- Explicitly set `include_in_schema=True` when including the prompts router
- Added `swagger_ui_parameters` to improve the Swagger UI display

```python
app.include_router(prompts_router, include_in_schema=True)
```

### 3. Enhanced the Custom Swagger UI Template

In `app/templates/custom_swagger.html`:
- Changed `docExpansion` from "none" to "list" to show all endpoints by default
- Added sorting for tags and operations to make the documentation more organized
- Added a refresh button to allow users to reload the OpenAPI schema without refreshing the page
- Added JavaScript function to refresh the Swagger UI

## How to Apply Changes

To apply these changes, restart the FastAPI application:

```bash
# If running directly
docker-compose restart web

# Or if you need to rebuild
docker-compose down
docker-compose up -d
```

## Verifying the Fix

After restarting, access the Swagger documentation at:
```
http://192.168.7.10:32780/docs
```

You should now see the prompts API endpoints listed under the "Prompts" tag.

## Troubleshooting

If the prompts API endpoints still don't appear:

1. Check the application logs for any errors during startup:
   ```bash
   docker-compose logs web
   ```

2. Try using the refresh button in the Swagger UI to reload the OpenAPI schema

3. Ensure MongoDB is accessible from the application container:
   ```bash
   docker-compose exec web ping mongodb
   ```

4. Check if the prompts router is being properly registered by examining the OpenAPI schema:
   ```
   http://192.168.7.10:32780/openapi.json
   ```
   Look for paths starting with "/api/prompts" in the response.
