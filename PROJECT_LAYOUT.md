# MyResumo Project Layout

## Directory Structure

```
MyResumo/
├── app/                        # Main application directory
│   ├── api/                    # API endpoints and routers
│   │   └── routers/            # FastAPI router modules
│   │       ├── prompts.py      # Prompts management API
│   │       ├── resume.py       # Resume management API
│   │       └── token_usage.py  # Token usage tracking API
│   ├── database/               # Database related code
│   │   ├── connector.py        # MongoDB connection management
│   │   ├── models/             # Pydantic models for database entities
│   │   │   ├── prompt.py       # Prompt template models
│   │   │   └── resume.py       # Resume data models
│   │   └── repositories/       # Repository pattern implementations
│   │       ├── base_repo.py    # Base repository with common operations
│   │       ├── prompt_repository.py  # Prompt-specific repository
│   │       └── resume_repository.py  # Resume-specific repository
│   ├── main.py                 # Application entry point
│   ├── services/               # Business logic services
│   │   ├── ai/                 # AI-related services
│   │   │   ├── ats_scoring.py  # ATS scoring logic
│   │   │   └── model_ai.py     # Resume optimization AI
│   │   └── resume/             # Resume processing services
│   │       └── latex_generator.py  # LaTeX PDF generation
│   ├── static/                 # Static assets (CSS, JS, images)
│   ├── templates/              # Jinja2 HTML templates
│   ├── utils/                  # Utility functions
│   │   └── file_handling.py    # File operations utilities
│   └── web/                    # Web UI routes
│       ├── core.py             # Core web routes
│       └── dashboard.py        # Dashboard web routes
├── .env                        # Environment variables (not in version control)
├── .env.example                # Example environment variables template
└── PROJECT_LAYOUT.md           # This file - project structure documentation
```

## Key Components

### API Layer
- **api/routers/**: Contains FastAPI router modules that define API endpoints
  - **resume.py**: Handles resume creation, optimization, and retrieval
  - **prompts.py**: Manages AI prompt templates
  - **token_usage.py**: Tracks AI token usage

### Database Layer
- **database/connector.py**: Manages MongoDB connections using the singleton pattern
- **database/models/**: Pydantic models for data validation
- **database/repositories/**: Repository pattern implementations for database operations

### Service Layer
- **services/ai/**: AI-related services for resume optimization and scoring
- **services/resume/**: Resume processing services including PDF generation

### Web UI
- **web/**: Web UI routes for the frontend application
- **templates/**: Jinja2 HTML templates for rendering web pages
- **static/**: Static assets like CSS, JavaScript, and images

### Configuration
- **.env**: Environment variables for configuration (not in version control)
- **.env.example**: Template for required environment variables

## Environment Variables

The application uses the following environment variables:

- **API_KEY**: API key for the AI service
- **API_BASE**: Base URL for the AI service API
- **MODEL_NAME**: Name of the AI model to use
- **MONGODB_URL**: MongoDB connection string
- **DB_NAME**: MongoDB database name (defaults to "myresumo")

## Main Workflows

1. **Resume Creation**: User uploads a resume PDF, which is processed and stored in MongoDB
2. **Resume Optimization**: AI analyzes the resume against a job description and generates an optimized version
3. **ATS Scoring**: AI scores the resume against a job description for ATS compatibility
4. **PDF Generation**: Optimized resume is converted to a professional PDF using LaTeX templates
