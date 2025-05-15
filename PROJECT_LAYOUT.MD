# MyResumo Project Layout

## Project Structure

```
/home/gilby/Code/MyResumo/
├── .env                      # Environment variables
├── .env.example              # Example environment variables
├── .env.local                # Local environment variables (not committed to git)
├── .gitignore                # Git ignore file
├── .dockerignore             # Docker ignore file
├── docker-compose.yml        # Main Docker Compose configuration
├── docker-compose.override.yml # Docker Compose override configuration
├── Dockerfile                # Docker build configuration
├── package.json              # Node.js package configuration
├── package-lock.json         # Node.js package lock file
├── playwright.config.ts      # Playwright test configuration
├── pyproject.toml            # Python project configuration
├── pytest.ini                # Pytest configuration
├── requirements.txt          # Python dependencies
├── version.txt               # Application version file
├── app/                      # Main application code
│   ├── main.py               # Application entry point
│   ├── api/                  # API endpoints
│   ├── models/               # Data models
│   ├── repositories/         # Data access layer
│   ├── services/             # Business logic
│   ├── static/               # Static files (CSS, JS, images)
│   ├── templates/            # HTML templates
│   └── utils/                # Utility functions
├── e2e/                      # End-to-end tests using Playwright
│   ├── advanced-mcp.spec.ts  # Advanced MCP functionality tests
│   ├── create-resume.spec.ts # Resume creation tests
│   ├── dashboard.spec.ts     # Dashboard page tests
│   ├── example.spec.ts       # Example test
│   ├── home.spec.ts          # Home page tests
│   ├── mcp-test.spec.ts      # Basic MCP functionality tests
│   ├── prompts-editor.spec.ts # Prompts editor tests
│   └── resume_download.spec.ts # Resume download tests
├── playwright-report/        # Playwright test reports
├── portainer-mcp/            # Portainer MCP tools
│   ├── internal/
│   │   ├── mcp/              # MCP implementation
│   │   └── tooldef/          # Tool definitions
│   │       └── tools.yaml    # MCP tools configuration
│   ├── pkg/
│   │   ├── portainer/        # Portainer client
│   │   └── toolgen/          # Tool generation
│   └── tests/
│       └── integration/      # MCP integration tests
├── scripts/                  # Utility scripts
│   ├── lint.sh               # Linting script
│   ├── post_install_check.py # Post-installation check
│   ├── setup_dev.sh          # Development setup script
│   └── start.sh              # Application startup script
├── services/                 # Application services
│   └── resume/               # Resume service
│       └── latex_templates/  # LaTeX templates for resume generation
├── tests/                    # Python tests
│   ├── test_latex_generator.py # LaTeX generator tests
│   ├── test_prompts_api.py     # Prompts API tests
│   ├── test_resume_download.py # Resume download tests
│   └── test_resume_router.py   # Resume router tests
└── docs/                     # Documentation
    ├── index.md              # Documentation index
    ├── overview.md           # Project overview
    ├── setup.md              # Setup guide
    └── contributing.md       # Contributing guide
```

## Key Components

1. **Application Core**: Located in the `app/` directory, this contains the main application code including APIs, services, and utilities.

2. **End-to-End Tests**: Located in the `e2e/` directory, these tests use Playwright to test the application from a user's perspective.

3. **Portainer MCP**: Located in the `portainer-mcp/` directory, this provides Model Control Protocol tools for interacting with Portainer.

4. **Services**: Located in the `services/` directory, these contain the core application functionality.

5. **Tests**: Located in the `tests/` directory, these contain Python unit tests for the application.

## Configuration Files

1. **Docker Configuration**:
   - `Dockerfile`: Defines the container image build process
   - `docker-compose.yml`: Main Docker Compose configuration
   - `docker-compose.override.yml`: Override configuration for development

2. **Environment Variables**:
   - `.env`: Main environment variables
   - `.env.example`: Example environment variables
   - `.env.local`: Local environment variables (not committed to git)

3. **Version Control**:
   - `.gitignore`: Specifies files to ignore in Git
   - `.dockerignore`: Specifies files to ignore in Docker builds

## Application Information

- The application is running remotely through Portainer at 192.168.7.10
- The web port increments each time the app is started (currently at port 32811)
- MongoDB server is located at 192.168.7.10:27017

## Main Workflows

1. **Resume Creation**: User uploads a resume PDF, which is processed and stored in MongoDB
2. **Resume Optimization**: AI analyzes the resume against a job description and generates an optimized version
3. **ATS Scoring**: AI scores the resume against a job description for ATS compatibility
4. **PDF Generation**: Optimized resume is converted to a professional PDF using LaTeX templates
5. **Resume Download**: User can download the optimized resume in various formats (PDF, LaTeX)
