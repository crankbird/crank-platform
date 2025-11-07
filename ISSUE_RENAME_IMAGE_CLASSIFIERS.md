# Issue: Rename Image Classifier Services to Reflect Capability Split

## Problem Statement

We currently have two image classifier services with confusing and inconsistent naming that doesn't reflect their distinct capabilities and requirements:

### Current Naming Issues:
1. **`services/crank_image_classifier.py`** - Lightweight service but generic name suggests it's the main/only classifier
2. **`archive/legacy-services/crank_image_classifier_gpu.py`** - Advanced service but "legacy" path suggests it's deprecated when it's actually more capable

### Service Capability Analysis:

| Current Name | Capabilities | Dependencies | Environment |
|--------------|--------------|--------------|-------------|
| `services/crank_image_classifier.py` | • Basic object detection<br>• Scene classification<br>• Color analysis<br>• Basic content analysis | • OpenCV<br>• scikit-learn<br>• Basic ML libraries | • CPU-friendly<br>• Low memory<br>• Edge deployments |
| `archive/legacy-services/crank_image_classifier_gpu.py` | • YOLOv8 object detection<br>• CLIP image-text understanding<br>• Advanced scene classification<br>• Image embeddings<br>• Sentence transformers | • PyTorch + GPU<br>• ultralytics<br>• CLIP<br>• transformers<br>• Heavy ML stack | • GPU acceleration required<br>• High memory<br>• Datacenter deployments |

## Proposed Solution

Rename both services to clearly reflect their capabilities and deployment requirements:

### New Service Names:
1. **`services/crank_image_classifier_basic.py`**
   - **Role**: Lightweight, CPU-friendly image classification for edge/constrained environments
   - **Capabilities**: Essential image analysis functions that work well on CPU
   - **Target**: IoT devices, edge computing, cost-conscious deployments

2. **`services/crank_image_classifier_advanced.py`**
   - **Role**: GPU-accelerated advanced computer vision with modern deep learning models
   - **Capabilities**: State-of-the-art image understanding, embeddings, complex analysis
   - **Target**: GPU-enabled servers, high-performance computing environments

### Alternative Naming Options:
- `crank_image_classifier_{light|heavy}`
- `crank_image_classifier_{cpu|gpu}`
- `crank_image_classifier_{edge|datacenter}`
- `crank_image_classifier_{essential|professional}`

## Acceptance Criteria

### ✅ Service File Renaming
- [ ] Rename `services/crank_image_classifier.py` → `services/crank_image_classifier_basic.py`
- [ ] Move `archive/legacy-services/crank_image_classifier_gpu.py` → `services/crank_image_classifier_advanced.py`
- [ ] Update service class names and internal identifiers
- [ ] Update service metadata and health endpoints

### ✅ Docker Infrastructure Updates
- [ ] Rename `image-classifier/Dockerfile` → `image-classifier-basic/Dockerfile`
- [ ] Rename `image-classifier-gpu/Dockerfile` → `image-classifier-advanced/Dockerfile`
- [ ] Update `docker-compose.development.yml` service names
- [ ] Update Docker build manifests and scripts
- [ ] Update container registry references

### ✅ Configuration Updates
- [ ] Update plugin configuration files (`.plugin.yaml`)
- [ ] Update environment variable references (`CRANK_IMAGE_CLASSIFIER_*`)
- [ ] Update service discovery names in networking
- [ ] Update certificate configurations for new service names

### ✅ Documentation Updates
- [ ] Update README.md service listings and descriptions
- [ ] Update architectural documentation mentioning the services
- [ ] Update deployment guides and examples
- [ ] Update API documentation and OpenAPI specs
- [ ] Update troubleshooting guides

### ✅ Testing and Validation Updates
- [ ] Update test files referencing the old service names
- [ ] Update dependency checker (`scripts/check-service-dependencies.py`)
- [ ] Update regression tests and CI configurations
- [ ] Update integration test service endpoints

### ✅ Migration Strategy
- [ ] Create migration documentation for existing deployments
- [ ] Consider providing symlinks/aliases during transition period
- [ ] Update service registration and discovery mechanisms
- [ ] Plan communication to users about the naming change

## Implementation Priority

### Phase 1: Core Service Renaming ✅
- Rename service files and update internal references
- Update service classes and metadata
- Basic functionality validation

### Phase 2: Infrastructure Updates ✅
- Update Docker configurations and builds
- Update docker-compose files
- Update networking and service discovery

### Phase 3: Documentation and Integration ✅
- Comprehensive documentation updates
- Test suite updates
- Migration guides and communication

## Benefits

1. **🎯 Clear Purpose**: Names immediately convey capability level and deployment target
2. **🏗️ Better Architecture**: Removes "legacy" stigma from advanced service
3. **📚 Improved Documentation**: Clearer guidance on when to use which service
4. **🔧 Easier Deployment**: DevOps teams can choose appropriate service based on name
5. **🚀 Future Growth**: Clear naming pattern for additional specialized services

## Risks and Mitigation

### Risk: Breaking Changes for Existing Deployments
**Mitigation**:
- Provide clear migration documentation
- Consider maintaining aliases during transition period
- Coordinate with deployment teams

### Risk: Confusion During Transition
**Mitigation**:
- Update all documentation simultaneously
- Clear communication about the change
- Comprehensive testing of new configurations

## Related Issues

- **Issue #20**: UniversalGPUManager Integration (COMPLETED) - This naming clarification builds on the GPU capability work
- **Future**: Additional specialized classifiers (video, medical imaging, etc.) can follow this naming pattern

## Definition of Done

- [ ] All service files renamed and functional
- [ ] All Docker configurations updated and tested
- [ ] All documentation updated and accurate
- [ ] All tests passing with new names
- [ ] Migration documentation created
- [ ] No broken references or dead links
- [ ] Services deploy and register correctly with new names

---

**Priority**: Medium-High (improves clarity and maintainability)
**Effort**: Medium (requires systematic updates across multiple components)
**Impact**: High (affects how developers and operators understand the system)
