# AI/ML Development Environment with Hybrid Package Management
# Based on validated Azure testing with 41x speed improvement

FROM nvidia/cuda:11.8-devel-ubuntu22.04

LABEL maintainer="AI/ML Development Team"
LABEL description="Hybrid conda+uv environment for GPU-accelerated AI/ML development"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV CONDA_ALWAYS_YES=true

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy our validated setup script
COPY scripts/setup_hybrid_environment_gpu.sh /tmp/setup_hybrid_environment_gpu.sh

# Make script executable and run setup
RUN chmod +x /tmp/setup_hybrid_environment_gpu.sh && \
    bash /tmp/setup_hybrid_environment_gpu.sh

# Set up environment activation
ENV PATH="/root/miniconda3/bin:$PATH"
ENV CONDA_AUTO_ACTIVATE_BASE=false

# Create activation script for container startup
RUN echo '#!/bin/bash' > /usr/local/bin/activate-aiml && \
    echo 'source /root/miniconda3/etc/profile.d/conda.sh' >> /usr/local/bin/activate-aiml && \
    echo 'conda activate aiml-hybrid-gpu' >> /usr/local/bin/activate-aiml && \
    echo 'echo "🚀 AI/ML hybrid environment activated"' >> /usr/local/bin/activate-aiml && \
    echo 'echo "📦 Conda packages: $(conda list | wc -l) packages"' >> /usr/local/bin/activate-aiml && \
    echo 'echo "⚡ uv packages: $(uv pip list | tail -n +3 | wc -l) packages"' >> /usr/local/bin/activate-aiml && \
    echo 'echo "🎮 GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo "Not available")"' >> /usr/local/bin/activate-aiml && \
    chmod +x /usr/local/bin/activate-aiml

# Default command starts with environment activated
CMD ["/bin/bash", "-c", "source /usr/local/bin/activate-aiml && exec /bin/bash"]

# Expose common ports for Jupyter, TensorBoard, etc.
EXPOSE 8888 6006 8080