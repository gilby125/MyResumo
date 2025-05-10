# Use Python 3.11 slim variant to reduce image size
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install only the needed packages and clean cache to keep image size down
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-distutils \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Multi-stage build for a smaller final image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    MONGODB_URI=mongodb://mongodb:27017/myresumo


WORKDIR /code

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY ./app /code/app
COPY data/sample_latex_templates /app/data/sample_latex_templates

# Create a non-root user and switch to it for security
RUN addgroup --system app && \
    adduser --system --group app && \
    chown -R app:app /code
USER app

# Expose the port the app runs on
EXPOSE 8080

# Add healthcheck to ensure the application is responsive
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use uvicorn for production deployment
# Expose the port before running the command

# Run post-install checks (continue even if checks fail)
RUN python scripts/post_install_check.py || echo "Post-install checks completed (some warnings may exist)"

# Use uvicorn for production deployment with environment variable
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
