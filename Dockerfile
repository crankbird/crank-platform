FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY services/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy service files
COPY services/ ./services/

# Create necessary directories and set ownership
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "-m", "uvicorn", "services.gateway:app", "--host", "0.0.0.0", "--port", "8000"]