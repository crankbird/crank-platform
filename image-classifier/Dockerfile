# Dockerfile for Crank Image Classifier
FROM python:3.11-slim

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-dev \
    libglib2.0-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    httpx==0.25.2 \
    pydantic==2.5.0 \
    opencv-python-headless==4.8.1.78 \
    Pillow==10.1.0 \
    scikit-learn==1.3.2 \
    numpy==1.25.2 \
    webcolors==1.13 \
    python-multipart==0.0.6 \
    PyYAML==6.0.1

# Create plugin metadata inline
RUN echo "name: crank-image-classifier" > plugin.yaml && \
    echo "version: 1.0.0" >> plugin.yaml && \
    echo "description: Computer vision ML classification for image analysis and object detection" >> plugin.yaml && \
    echo "author: Crank Platform Team" >> plugin.yaml && \
    echo "capabilities:" >> plugin.yaml && \
    echo "  - object_detection" >> plugin.yaml && \
    echo "  - scene_classification" >> plugin.yaml && \
    echo "  - content_safety" >> plugin.yaml && \
    echo "  - image_quality" >> plugin.yaml && \
    echo "  - dominant_colors" >> plugin.yaml && \
    echo "  - text_detection" >> plugin.yaml && \
    echo "health_endpoint: /health" >> plugin.yaml && \
    echo "separation_ready: true" >> plugin.yaml

# Copy the application code
COPY ./services/crank_image_classifier.py .
COPY ./services/security_config.py .

# Create certificate directory
RUN mkdir -p /etc/certs

# Expose ports (both HTTP and HTTPS)
EXPOSE 8005 8443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8005/health || exit 1

# Start the service
CMD ["python", "crank_image_classifier.py"]