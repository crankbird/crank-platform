# AI/ML Development Environment - CPU Only
# Lightweight version for general development without GPU requirements

FROM ubuntu:22.04

LABEL maintainer="AI/ML Development Team" 
LABEL description="Hybrid conda+uv environment for CPU-based AI/ML development"

# Prevent interactive prompts
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

# Copy CPU version of setup script
COPY scripts/setup_hybrid_environment.sh /tmp/setup_hybrid_environment.sh

# Run setup
RUN chmod +x /tmp/setup_hybrid_environment.sh && \
    bash /tmp/setup_hybrid_environment.sh

# Set up environment
ENV PATH="/root/miniconda3/bin:$PATH"
ENV CONDA_AUTO_ACTIVATE_BASE=false

# Create activation script
RUN echo '#!/bin/bash' > /usr/local/bin/activate-aiml && \
    echo 'source /root/miniconda3/etc/profile.d/conda.sh' >> /usr/local/bin/activate-aiml && \
    echo 'conda activate aiml-hybrid' >> /usr/local/bin/activate-aiml && \
    echo 'echo "🚀 AI/ML hybrid environment activated (CPU)"' >> /usr/local/bin/activate-aiml && \
    echo 'echo "📦 Conda packages: $(conda list | wc -l) packages"' >> /usr/local/bin/activate-aiml && \
    echo 'echo "⚡ uv packages: $(uv pip list | tail -n +3 | wc -l) packages"' >> /usr/local/bin/activate-aiml && \
    chmod +x /usr/local/bin/activate-aiml

CMD ["/bin/bash", "-c", "source /usr/local/bin/activate-aiml && exec /bin/bash"]

EXPOSE 8888 6006 8080