# Image Classifier Architecture

## Two Distinct Image Classification Services

The platform provides **TWO SEPARATE** image classification services with different capabilities and deployment requirements:

### 1. Basic CPU Image Classifier
**File**: `services/relaxed-checking/crank_image_classifier.py`

**Capabilities:**
- Basic object detection using OpenCV
- Scene classification
- Color analysis
- Basic content analysis

**Dependencies:**
- OpenCV
- PIL/Pillow
- NumPy
- scikit-learn
- Basic ML libraries

**Deployment:**
- CPU-friendly
- Low memory footprint
- Edge deployments
- IoT devices
- Cost-conscious environments

**Type Checking**: Uses relaxed checking for CV library limitations

### 2. Advanced GPU Image Classifier
**File**: `services/crank_image_classifier_advanced.py`

**Capabilities:**
- YOLOv8 object detection
- CLIP image-text understanding
- Advanced scene classification
- Image embeddings
- Sentence transformers
- GPU-accelerated processing

**Dependencies:**
- PyTorch + CUDA
- ultralytics (YOLOv8)
- OpenAI CLIP
- transformers
- sentence-transformers
- Heavy ML stack

**Deployment:**
- GPU acceleration required
- High memory requirements
- Datacenter deployments
- NVIDIA CUDA support
- WSL2/Linux environments

## Docker Architecture Decision

**Important**: Due to Docker's limitations with GPU access on macOS, we maintain **separate CPU and GPU implementations** rather than auto-detection within containers.

## Development Notes

### Package Management
**CRITICAL**: Always use `uv` for package management, not `pip`
```bash
uv pip install package-name
uv pip list
uv pip freeze > requirements.txt
```

### Service Naming History
- Originally planned: lightweight/heavyweight with auto GPU detection
- Current reality: Separate CPU/GPU implementations due to Docker/Mac limitations
- CPU version: Basic, edge-friendly
- GPU version: Advanced, datacenter-grade

## Build Configurations

### CPU Classifier
- Container: `image-classifier/`
- Build file: Standard Python container
- Requirements: `services/requirements-crank-image-classifier.txt`

### GPU Classifier
- Container: `image-classifier-gpu/`
- Build file: `services/Dockerfile.crank-image-classifier-gpu`
- Requirements: `services/requirements-universal-gpu.txt`
- CUDA base image required

## Type Checking Strategy

Both classifiers use graduated type checking:
- **CPU Version**: In `relaxed-checking/` due to OpenCV/PIL limitations
- **GPU Version**: May need similar relaxed checking for PyTorch/CLIP/ML libraries

## Testing Strategy

- **CPU**: Runs on all platforms including macOS
- **GPU**: Requires NVIDIA GPU, tested on WSL2/Linux
- **Smoke Tests**: Include both versions with environment detection
