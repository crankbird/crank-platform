# GPU-Accelerated Image Classifier Dockerfile
# Multi-stage build for optimization
# Requires NVIDIA Docker runtime and CUDA-capable GPU

# Stage 1: Base with Python and system dependencies
FROM python:3.11-bullseye as base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    ffmpeg \
    curl \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Python dependencies
FROM base as dependencies

# Set working directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA support first (critical for GPU)
RUN pip install torch==2.1.1 torchvision==0.16.1 torchaudio==2.1.1 \
    --index-url https://download.pytorch.org/whl/cu121

# Install core web framework dependencies
RUN pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    httpx==0.25.2 \
    pydantic==2.5.0 \
    python-multipart==0.0.6

# Install computer vision libraries
RUN pip install \
    opencv-python==4.8.1.78 \
    Pillow==10.1.0 \
    numpy==1.25.2

# Install ML and scientific computing
RUN pip install \
    scikit-learn==1.3.2 \
    scipy==1.11.4

# Install ultralytics (YOLOv8)
RUN pip install ultralytics==8.0.206

# Install transformers and NLP
RUN pip install \
    transformers==4.35.2 \
    tokenizers==0.15.0

# Install CLIP from OpenAI
RUN pip install git+https://github.com/openai/CLIP.git

# Install sentence transformers with compatible huggingface_hub
RUN pip install \
    sentence-transformers==2.2.2 \
    huggingface_hub==0.16.4

# Install additional utilities
RUN pip install \
    albumentations==1.3.1 \
    imagehash==4.3.1 \
    webcolors==1.13 \
    PyYAML==6.0.1 \
    tqdm==4.66.1 \
    psutil==5.9.6 \
    GPUtil==1.4.0

# Stage 3: Final application
FROM dependencies as final

# Copy the application code
COPY ./services/crank_image_classifier_gpu.py .
COPY ./services/security_config.py .

# Create plugin metadata
RUN cat > plugin.yaml << 'EOF'
name: crank-image-classifier-gpu
version: 1.0.0
description: GPU-accelerated computer vision ML classification with YOLOv8, CLIP, and modern deep learning
author: Crank Platform Team
capabilities:
  - yolo_object_detection
  - clip_image_understanding
  - advanced_scene_analysis
  - image_embeddings
  - batch_processing
requirements:
  gpu: required
  vram_min: 4GB
health_endpoint: /health
separation_ready: true
EOF

# Create certificate directory
RUN mkdir -p /etc/certs

# Pre-download essential models (optional - models will download on first use)
RUN python -c "print('Pre-downloading YOLOv8...')" && \
    python -c "from ultralytics import YOLO; yolo = YOLO('yolov8n.pt'); print('✅ YOLOv8n downloaded')" || echo "⚠️ YOLOv8 download skipped"

RUN python -c "print('Pre-downloading CLIP...')" && \
    python -c "import clip; clip_model, _ = clip.load('ViT-B/32', device='cpu'); print('✅ CLIP ViT-B/32 downloaded')" || echo "⚠️ CLIP download skipped"

# Skip sentence transformer pre-download to avoid compatibility issues
RUN echo "ℹ️ Sentence Transformer will download on first use"

# Expose ports (both HTTP and HTTPS)
EXPOSE 8007 8443

# Health check with longer timeout for GPU initialization
HEALTHCHECK --interval=60s --timeout=30s --start-period=180s --retries=3 \
  CMD curl -f http://localhost:8007/health || exit 1

# Set GPU-optimized environment variables
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Start the service
CMD ["python", "crank_image_classifier_gpu.py"]