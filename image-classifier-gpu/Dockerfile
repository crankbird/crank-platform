# GPU-Accelerated Image Classifier Dockerfile
# Requires NVIDIA Docker runtime and CUDA-capable GPU

FROM python:3.11-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install PyTorch with CUDA support first (will use host GPU drivers)
RUN pip install --no-cache-dir \
    torch==2.1.1 \
    torchvision==0.16.1 \
    --index-url https://download.pytorch.org/whl/cu121

# Install core dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    httpx==0.25.2 \
    pydantic==2.5.0 \
    python-multipart==0.0.6

# Install computer vision and ML libraries
RUN pip install --no-cache-dir \
    ultralytics==8.0.206 \
    opencv-python==4.8.1.78 \
    Pillow==10.1.0 \
    numpy==1.25.2 \
    scikit-learn==1.3.2 \
    scipy==1.11.4

# Install CLIP and transformers
RUN pip install --no-cache-dir \
    transformers==4.35.2 \
    git+https://github.com/openai/CLIP.git \
    sentence-transformers==2.2.2

# Install additional utilities
RUN pip install --no-cache-dir \
    albumentations==1.3.1 \
    imagehash==4.3.1 \
    webcolors==1.13 \
    PyYAML==6.0.1 \
    tqdm==4.66.1 \
    psutil==5.9.6 \
    GPUtil==1.4.0

# Create plugin metadata inline
RUN echo "name: crank-image-classifier-gpu" > plugin.yaml && \
    echo "version: 1.0.0" >> plugin.yaml && \
    echo "description: GPU-accelerated computer vision ML classification with YOLOv8, CLIP, and modern deep learning" >> plugin.yaml && \
    echo "author: Crank Platform Team" >> plugin.yaml && \
    echo "capabilities:" >> plugin.yaml && \
    echo "  - yolo_object_detection" >> plugin.yaml && \
    echo "  - clip_image_understanding" >> plugin.yaml && \
    echo "  - advanced_scene_analysis" >> plugin.yaml && \
    echo "  - image_embeddings" >> plugin.yaml && \
    echo "  - batch_processing" >> plugin.yaml && \
    echo "requirements:" >> plugin.yaml && \
    echo "  gpu: required" >> plugin.yaml && \
    echo "  vram_min: 4GB" >> plugin.yaml && \
    echo "health_endpoint: /health" >> plugin.yaml && \
    echo "separation_ready: true" >> plugin.yaml

# Copy the application code
COPY ./services/crank_image_classifier_gpu.py .

# Create certificate directory
RUN mkdir -p /etc/certs

# Pre-download models to reduce startup time
RUN python -c "\
import torch; \
from ultralytics import YOLO; \
import clip; \
print('Pre-downloading models...'); \
try: \
    yolo = YOLO('yolov8n.pt'); \
    print('✅ YOLOv8n downloaded'); \
    clip_model, _ = clip.load('ViT-B/32', device='cpu'); \
    print('✅ CLIP ViT-B/32 downloaded'); \
except Exception as e: \
    print(f'Model download error: {e}'); \
"

# Expose ports (both HTTP and HTTPS)
EXPOSE 8007 8443

# Health check (accounting for longer GPU model initialization)
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
  CMD curl -f http://localhost:8007/health || exit 1

# Set GPU-optimized environment
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Start the service
CMD ["python", "crank_image_classifier_gpu.py"]