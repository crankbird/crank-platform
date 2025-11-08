# CRITICAL CONTEXT - ALWAYS REMEMBER

## Package Management
**ALWAYS USE UV, NEVER PIP**
```bash
uv pip install package-name
uv pip list
uv pip freeze > requirements.txt
```

## Image Classifier Architecture
**TWO SEPARATE CLASSIFIERS - NOT ONE**

### CPU Classifier (Basic)
- **File**: `services/relaxed-checking/crank_image_classifier.py`
- **Purpose**: Lightweight, CPU-friendly, edge deployments
- **Dependencies**: OpenCV, PIL, scikit-learn
- **Type Checking**: Relaxed (in relaxed-checking/ dir)

### GPU Classifier (Advanced)
- **File**: `services/crank_image_classifier_advanced.py`
- **Purpose**: Heavy ML, GPU-accelerated, datacenter deployments
- **Dependencies**: PyTorch, YOLO, CLIP, transformers
- **Type Checking**: May need relaxed for ML libraries

## Docker Architecture
- **Reason for separation**: Docker GPU access limitations on macOS
- **CPU version**: Runs everywhere
- **GPU version**: Requires NVIDIA CUDA, WSL2/Linux testing

## History
- Originally planned auto GPU detection
- Reverted to separate implementations due to Docker/Mac limitations
- GPU version was in archive/ but restored from commit c283152
- Both are production services, neither is "legacy"

## Error Handling Philosophy
- "Fix what we can, tolerate what we must"
- Graduated type checking for different service complexity levels
- Real functionality over perfect type checking
