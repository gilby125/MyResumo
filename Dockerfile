
# Use Python 3.11 slim variant to reduce image size
FROM python:3.13-slim AS builder

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
FROM python:3.13-slim   

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    API_BASE="" \
    PYTHONPATH=/code

# Install LaTeX and other required packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra \
    curl \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY ./app /code/app

# Copy the start script and set permissions BEFORE switching users
COPY ./scripts/start.sh /code/scripts/start.sh
RUN chmod +x /code/scripts/start.sh

# Create a non-root user and switch to it for security
RUN addgroup --system app && \
    adduser --system --group app && \
    chown -R app:app /code
USER app

# Expose the port the app runs on
EXPOSE 8080

# Add healthcheck to ensure the application is responsive
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Use sh to run the script explicitly
CMD ["sh", "/code/scripts/start.sh"]
