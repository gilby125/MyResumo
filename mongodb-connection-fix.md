# MongoDB Connection Fix

## Problem

The application was trying to connect to MongoDB on localhost (127.0.0.1), but the MongoDB server is actually located at 192.168.7.10. This was causing connection errors:

```
Error in find: localhost:27017: [Errno 111] Connection refused
```

## Solution

We've implemented a comprehensive solution to fix the MongoDB connection issue:

1. **Added MongoDB Configuration Endpoints**: Created API endpoints to view and update the MongoDB connection string
2. **Enhanced the Prompts Editor**: Added a MongoDB configuration section to the prompts editor
3. **Improved Error Handling**: Added better error handling and logging for MongoDB connection issues

## Changes Made

### 1. Added MongoDB Configuration Endpoints

In `app/main.py`, we added two new endpoints:

```python
@app.get("/api/config/mongodb", tags=["Configuration"], summary="Get MongoDB Configuration")
async def get_mongodb_config():
    """Get the current MongoDB configuration."""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    # Implementation...
    return {
        "mongodb_url": masked_url,
        "is_default": mongodb_url == "mongodb://localhost:27017"
    }

@app.post("/api/config/mongodb", tags=["Configuration"], summary="Set MongoDB Configuration")
async def set_mongodb_config(config: dict):
    """Set the MongoDB configuration."""
    # Implementation...
    # Set environment variable
    os.environ["MONGODB_URL"] = mongodb_url
    # Test the connection
    # ...
```

These endpoints allow viewing and updating the MongoDB connection string at runtime.

### 2. Enhanced the Prompts Editor

In `app/templates/prompts_editor.html`, we added a MongoDB configuration section:

```html
<!-- MongoDB Configuration -->
<div class="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
    <div class="px-4 py-5 sm:px-6">
        <h2 class="text-lg font-medium text-gray-900">MongoDB Configuration</h2>
        <p class="mt-1 text-sm text-gray-500">Configure the MongoDB connection for the prompts API.</p>
    </div>
    <div class="border-t border-gray-200 px-4 py-5 sm:p-0">
        <dl class="sm:divide-y sm:divide-gray-200">
            <div class="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt class="text-sm font-medium text-gray-500">Current MongoDB URL</dt>
                <dd class="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2" x-text="mongodbUrl"></dd>
            </div>
            <div class="py-4 sm:py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                <dt class="text-sm font-medium text-gray-500">New MongoDB URL</dt>
                <dd class="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">
                    <div class="flex">
                        <input type="text" x-model="newMongodbUrl" placeholder="mongodb://192.168.7.10:27017" class="flex-1 border border-gray-300 rounded-l-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm">
                        <button @click="updateMongodbConfig()" class="bg-primary-600 text-white rounded-r-md px-4 py-2 hover:bg-primary-700">
                            Update
                        </button>
                    </div>
                    <p class="mt-1 text-xs text-gray-500">Example: mongodb://192.168.7.10:27017</p>
                </dd>
            </div>
        </dl>
    </div>
</div>
```

And added the corresponding JavaScript functions:

```javascript
fetchMongodbConfig() {
    fetch('/api/config/mongodb')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            this.mongodbUrl = data.mongodb_url;
            if (data.is_default) {
                this.newMongodbUrl = 'mongodb://192.168.7.10:27017';
            }
        })
        .catch(error => {
            console.error('Error fetching MongoDB config:', error);
            this.mongodbUrl = 'Error loading configuration';
        });
},

updateMongodbConfig() {
    // Implementation...
}
```

### 3. Improved Error Handling

We've added better error handling and logging throughout the application:

- Added detailed error messages for MongoDB connection issues
- Added connection testing before attempting operations
- Added comprehensive logging to help diagnose issues

## How to Use

1. Navigate to `/prompts` in your browser
2. In the MongoDB Configuration section:
   - View the current MongoDB URL
   - Enter the correct MongoDB URL: `mongodb://192.168.7.10:27017`
   - Click "Update"
3. The application will test the connection and update the configuration
4. After updating the MongoDB URL, the prompts should load correctly

## Why This Approach Works

This approach works because:

1. **Runtime Configuration**: The MongoDB URL can be updated at runtime without restarting the application
2. **User-Friendly Interface**: The MongoDB configuration section provides a user-friendly way to update the connection string
3. **Immediate Feedback**: The application tests the connection and provides immediate feedback
4. **Persistent Configuration**: The MongoDB URL is stored in the environment variables, so it persists for the lifetime of the application

## Next Steps

After updating the MongoDB URL:

1. Try loading the prompts again
2. Try initializing the default prompts
3. Try editing a prompt

If you still encounter issues, check the application logs for any errors.
