function promptsEditor() {
    return {
        loading: true,
        error: null,
        success: null,
        prompts: [],
        currentPrompt: null,
        newVariable: '',
        mongodbUrl: 'Loading...',
        newMongodbUrl: '',
        expandEditor: false,
        showPreview: false,
        sampleValues: {},
        searchQuery: '',
        componentFilter: '',
        statusFilter: '',
        testResult: null,
        testLoading: false,

        init() {
            this.fetchMongodbConfig();
            this.fetchPrompts();
        },

        // Computed property for unique components
        get uniqueComponents() {
            if (!this.prompts || this.prompts.length === 0) return [];

            // Extract unique component values
            const components = [...new Set(this.prompts.map(prompt => prompt.component))];
            return components.sort();
        },

        // Computed property for filtered prompts
        get filteredPrompts() {
            if (!this.prompts) return [];

            return this.prompts.filter(prompt => {
                // Filter by search query
                const searchLower = this.searchQuery.toLowerCase();
                const matchesSearch = searchLower === '' ||
                    prompt.name.toLowerCase().includes(searchLower) ||
                    prompt.description.toLowerCase().includes(searchLower) ||
                    prompt.component.toLowerCase().includes(searchLower);

                // Filter by component
                const matchesComponent = this.componentFilter === '' ||
                    prompt.component === this.componentFilter;

                // Filter by status
                const matchesStatus = this.statusFilter === '' ||
                    (this.statusFilter === 'active' && prompt.is_active) ||
                    (this.statusFilter === 'inactive' && !prompt.is_active);

                return matchesSearch && matchesComponent && matchesStatus;
            });
        },

        fetchMongodbConfig() {
            // Get the base URL from the current window location
            const baseUrl = window.location.origin;
            console.log('Base URL:', baseUrl);

            fetch(`${baseUrl}/api/config/mongodb`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    this.mongodbUrl = data.mongodb_url || 'Not configured';
                    if (data.is_default || !data.mongodb_url) {
                        this.newMongodbUrl = 'mongodb://192.168.7.10:27017';
                        // Show a warning if MongoDB is not configured
                        if (data.is_default) {
                            this.error = 'MongoDB connection is not configured. Please set a valid MongoDB URL.';
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching MongoDB config:', error);
                    this.mongodbUrl = 'Error loading configuration';
                    this.error = `Failed to load MongoDB configuration: ${error.message}. Please check your server logs.`;
                });
        },

        updateMongodbConfig() {
            if (!this.newMongodbUrl) {
                this.error = 'Please enter a MongoDB URL';
                return;
            }

            // Validate MongoDB URL format
            if (!this.newMongodbUrl.startsWith('mongodb://') && !this.newMongodbUrl.startsWith('mongodb+srv://')) {
                this.error = 'Invalid MongoDB URL format. URL should start with mongodb:// or mongodb+srv://';
                return;
            }

            this.loading = true;
            this.error = null;
            this.success = null;

            const baseUrl = window.location.origin;

            // Show a message while testing connection
            this.mongodbUrl = 'Testing connection...';

            fetch(`${baseUrl}/api/config/mongodb`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    mongodb_url: this.newMongodbUrl
                })
            })
            .then(response => {
                if (!response.ok) {
                    // Parse the error response if possible
                    return response.json().then(errorData => {
                        throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
                    }).catch(() => {
                        // If we can't parse the JSON, just throw the HTTP error
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.success = data.message || 'MongoDB configuration updated successfully';
                    this.mongodbUrl = this.newMongodbUrl;
                    this.newMongodbUrl = '';
                    // Refresh prompts after updating MongoDB config
                    this.fetchPrompts();
                } else if (data.detail) {
                    throw new Error(data.detail);
                } else {
                    throw new Error('Update failed without specific error message');
                }
            })
            .catch(error => {
                console.error('MongoDB update error:', error);
                this.error = `Failed to update MongoDB configuration: ${error.message}`;
                this.mongodbUrl = 'Connection failed';
                this.loading = false;
            });
        },

        fetchPrompts() {
            this.loading = true;
            // Don't clear existing MongoDB connection errors
            if (!this.error || !this.error.includes('MongoDB')) {
                this.error = null;
            }

            const baseUrl = window.location.origin;
            console.log('Fetching prompts from:', `${baseUrl}/api/prompts-direct`);
            fetch(`${baseUrl}/api/prompts-direct`)
                .then(response => {
                    if (!response.ok) {
                        // Check for specific error status codes
                        if (response.status === 500) {
                            throw new Error('Server error: The server encountered an error. This might be due to a MongoDB connection issue.');
                        } else if (response.status === 404) {
                            throw new Error('API endpoint not found. The prompts API might not be properly configured.');
                        } else {
                            throw new Error(`HTTP error! Status: ${response.status}`);
                        }
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Prompts data received:', data);
                    if (data && Array.isArray(data.prompts)) {
                        console.log(`Received ${data.prompts.length} prompts`);
                        this.prompts = data.prompts;

                        // If we have no prompts, show a helpful message
                        if (data.prompts.length === 0) {
                            this.error = 'No prompts found in the database. You may need to initialize the database with default prompts.';
                        }
                    } else if (data && data.detail) {
                        // If the server returned an error message
                        console.error('Server error:', data.detail);
                        this.error = `Server error: ${data.detail}`;
                    } else {
                        console.error('No prompts array in response:', data);
                        this.error = 'Invalid response format: No prompts array found in the server response.';
                    }
                    this.loading = false;

                    // If we successfully loaded prompts, clear any success message after 5 seconds
                    if (this.success) {
                        setTimeout(() => {
                            this.success = null;
                        }, 5000);
                    }
                })
                .catch(error => {
                    console.error('Error fetching prompts:', error);
                    this.error = `Failed to load prompts: ${error.message}`;
                    this.loading = false;

                    // Add a helpful suggestion if it might be a MongoDB issue
                    if (error.message.includes('MongoDB') || error.message.includes('connection')) {
                        this.error += ' Please check your MongoDB connection settings.';
                    }
                });
        },

        editPrompt(prompt) {
            // Create a deep copy to avoid modifying the original
            this.currentPrompt = JSON.parse(JSON.stringify(prompt));
        },

        addVariable() {
            if (this.newVariable.trim() === '') return;

            if (!this.currentPrompt.variables) {
                this.currentPrompt.variables = [];
            }

            if (!this.currentPrompt.variables.includes(this.newVariable)) {
                this.currentPrompt.variables.push(this.newVariable);
            }

            this.newVariable = '';
        },

        removeVariable(index) {
            this.currentPrompt.variables.splice(index, 1);
        },

        savePrompt() {
            this.loading = true;
            this.error = null;

            // Validate the data before sending
            if (!this.currentPrompt.template) {
                this.error = "Template cannot be empty";
                this.loading = false;
                return;
            }

            if (!Array.isArray(this.currentPrompt.variables) || this.currentPrompt.variables.length === 0) {
                this.error = "At least one variable is required";
                this.loading = false;
                return;
            }

            const updateData = {
                description: this.currentPrompt.description || "",
                template: this.currentPrompt.template,
                variables: this.currentPrompt.variables,
                is_active: this.currentPrompt.is_active
            };

            const baseUrl = window.location.origin;
            console.log('Saving prompt to:', `${baseUrl}/api/prompts-direct/${this.currentPrompt.id}`);
            fetch(`${baseUrl}/api/prompts-direct/${this.currentPrompt.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updateData)
            })
            .then(response => {
                console.log('Save prompt response status:', response.status);
                if (!response.ok) {
                    // Try to get the error details from the response
                    return response.json().then(errorData => {
                        throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
                    }).catch(() => {
                        // If we can't parse the JSON, just throw the HTTP error
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Save prompt response data:', data);
                if (data.success) {
                    // Update was successful, refresh the prompts list
                    this.success = 'Prompt saved successfully';
                    this.fetchPrompts();
                    this.currentPrompt = null;
                } else if (data.detail) {
                    throw new Error(data.detail);
                } else {
                    throw new Error('Update failed without specific error message');
                }
            })
            .catch(error => {
                console.error('Error saving prompt:', error);
                this.error = `Failed to save prompt: ${error.message}`;
                this.loading = false;
            });
        },

        togglePromptStatus() {
            this.currentPrompt.is_active = !this.currentPrompt.is_active;
        },

        // Preview functionality
        get previewTemplate() {
            if (!this.currentPrompt || !this.currentPrompt.template) return '';

            // Replace variables with sample values
            let preview = this.currentPrompt.template;
            if (this.currentPrompt.variables && this.currentPrompt.variables.length > 0) {
                this.currentPrompt.variables.forEach(variable => {
                    // Create a regular expression to find all instances of the variable
                    const regex = new RegExp(`{{\\s*${variable}\\s*}}`, 'g');
                    // Replace with sample value or placeholder
                    const value = this.sampleValues[variable] || `[${variable}]`;
                    preview = preview.replace(regex, value);
                });
            }
            return preview;
        },

        setSampleValue(variable, value) {
            this.sampleValues[variable] = value;
        },

        // Initialize default prompts
        initializeDefaultPrompts() {
            this.loading = true;
            this.error = null;
            this.success = null;

            const baseUrl = window.location.origin;
            fetch(`${baseUrl}/api/prompts-direct/initialize`, {
                method: 'POST'
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
                    }).catch(() => {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    this.success = 'Default prompts initialized successfully';
                    this.fetchPrompts();
                } else if (data.detail) {
                    throw new Error(data.detail);
                } else {
                    throw new Error('Initialization failed without specific error message');
                }
            })
            .catch(error => {
                console.error('Error initializing prompts:', error);
                this.error = `Failed to initialize default prompts: ${error.message}`;
                this.loading = false;
            });
        },

        // Test a prompt with sample values
        testPrompt() {
            if (!this.currentPrompt) return;

            this.testLoading = true;
            this.testResult = null;
            this.error = null;

            // Prepare test data
            const testData = {
                prompt_id: this.currentPrompt.id,
                variables: {}
            };

            // Add sample values for each variable
            this.currentPrompt.variables.forEach(variable => {
                testData.variables[variable] = this.sampleValues[variable] || `[${variable}]`;
            });

            const baseUrl = window.location.origin;
            fetch(`${baseUrl}/api/prompts-direct/test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(testData)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
                    }).catch(() => {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                this.testLoading = false;
                if (data.result) {
                    this.testResult = data.result;
                } else if (data.detail) {
                    throw new Error(data.detail);
                } else {
                    throw new Error('Test failed without specific error message');
                }
            })
            .catch(error => {
                console.error('Error testing prompt:', error);
                this.error = `Failed to test prompt: ${error.message}`;
                this.testLoading = false;
            });
        }
    };
}