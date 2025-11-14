# AI Agent Deployment & Operational Patterns

**Version**: 1.0
**Date**: November 14, 2025
**Purpose**: Critical deployment lessons learned from unified Sonnet+Codex worker analysis

## 🚨 **Deployment Anti-Patterns (Learned the Hard Way)**

### **1. The Stranded Endpoint Problem**

**Issue**: Refactoring worker capabilities without updating downstream dependencies

**Example**: Splitting `EMAIL_CLASSIFICATION` capability into separate `EMAIL_SPAM_DETECTION`, `EMAIL_BILL_DETECTION` capabilities without migration strategy.

**Solution Pattern**:

```python
# ALWAYS implement backward compatibility shims
@router.post("/classify")  # Legacy endpoint
async def legacy_classify_endpoint(request: dict) -> dict:
    """Migration shim - delegates to new capability-specific endpoints."""
    operation = request.get("type", "spam")  # Default assumption

    if operation == "spam":
        return await spam_detection_endpoint(SpamRequest(**request))
    elif operation == "bill":
        return await bill_detection_endpoint(BillRequest(**request))
    else:
        raise HTTPException(400, "Unknown classification type")

# Test matrix to prove backward compatibility
def test_legacy_endpoint_compatibility():
    # Prove old clients still work
    assert legacy_classify_endpoint({"text": "hello", "type": "spam"})
    assert legacy_classify_endpoint({"text": "invoice", "type": "bill"})
```

**Deployment Checklist**:

- [ ] Controller routing tables updated for new capability IDs
- [ ] Plugin YAML manifests declare new capabilities
- [ ] Migration shim tested with existing client calls
- [ ] Capability retirement plan with timeline
- [ ] Monitoring alerts for deprecated endpoint usage

### **2. The Missing Dependency Problem**

**Issue**: Universal `--test` modes that fail inconsistently across environments

**Example**: Document converter that requires Pandoc but worker doesn't handle missing dependencies gracefully.

**Solution Pattern**:

```python
# Use the IMPLEMENTED crank.testing helper
from crank.testing import ensure_dependency

class DocumentConverterWorker(WorkerApplication):
    def test_worker(self) -> bool:
        """Standard testing pattern with environment-specific skips."""

        # Use standard helper for consistent messaging
        ensure_dependency("pandoc",
                         skip_message="Pandoc not available, skipping conversion tests",
                         install_hint="brew install pandoc")

        ensure_dependency("libreoffice",
                         skip_message="LibreOffice not available, skipping office tests",
                         install_hint="Download from https://libreoffice.org")

        # Run actual tests only if dependencies available
        return self._run_core_tests()

class GPUImageClassifier(WorkerApplication):
    def test_worker(self) -> bool:
        ensure_dependency("torch.cuda",
                         skip_message="CUDA not available, skipping GPU tests",
                         install_hint="Install PyTorch with CUDA support")

        ensure_dependency("nvidia-ml-py",
                         skip_message="NVIDIA-ML not available, skipping GPU monitoring",
                         install_hint="pip install nvidia-ml-py")

        return self._run_gpu_tests()
```

**Standard Helper Implementation**:

The `crank.testing.ensure_dependency` helper is IMPLEMENTED in `src/crank/testing/dependency_checker.py` with support for:

- Python modules (`torch`, `torch.cuda`, `transformers`)
- System executables (`pandoc`, `libreoffice`, `ffmpeg`)
- Special cases (NVIDIA GPU detection, etc.)
- Consistent skip messaging and install hints

### **3. The Deployment Artifact Lag Problem**

**Issue**: Code refactored successfully but deployment configurations not updated

**Example**: Image classifiers migrated to WorkerApplication but Docker builds, CI jobs, and plugin manifests still reference old patterns.

**Solution Pattern**:

**Worker Migration Checklist Template**:

Use the IMPLEMENTED template at `deployment/worker-migration-checklist.yml`:

```bash
# Copy template for each worker migration
cp deployment/worker-migration-checklist.yml deployment/migration-{worker-name}-{date}.yml

# Example:
cp deployment/worker-migration-checklist.yml deployment/migration-image-classifier-2025-11-14.yml
```

The template includes comprehensive tracking for:

- Code implementation changes (WorkerApplication adoption, capability updates, testing)
- Deployment artifact updates (Docker, CI, plugin configs)
- Infrastructure updates (routing, monitoring, alerting)
- Migration strategy (backward compatibility, rollback plan)
- Validation steps (end-to-end testing, performance regression)

### **4. The Repository/Metadata Inconsistency Problem**

**Issue**: Worker conversion creates artifacts with inconsistent metadata schema

**Example**: Document converter outputs files without standardized front-matter, breaking downstream publication pipelines.

**Solution Pattern**:

```python
# Follow zettel worker pattern for all artifact storage
class DocumentConverter(WorkerApplication):
    def _store_conversion_artifact(self,
                                  original: bytes,
                                  converted: bytes,
                                  conversion_plan: ConversionPlan) -> str:
        """Store with standardized metadata."""

        # Standard YAML front-matter pattern
        metadata = {
            "source_format": conversion_plan.input_format,
            "target_format": conversion_plan.output_format,
            "conversion_timestamp": datetime.utcnow().isoformat(),
            "conversion_parameters": conversion_plan.options,
            "original_hash": hashlib.sha256(original).hexdigest(),
            "worker_version": self._get_version()
        }

        # Standard storage pattern
        content_with_frontmatter = f"""---
{yaml.dump(metadata)}
---
{converted.decode('utf-8')}"""

        return self._storage.store(content_with_frontmatter)

    def _get_conversion_metadata(self, artifact_id: str) -> dict:
        """Retrieve standardized metadata for publication pipeline."""
        content = self._storage.retrieve(artifact_id)
        frontmatter, content = extract_frontmatter(content)
        return frontmatter
```

## 🎯 **Operational Testing Patterns**

### **Concurrency/Backpressure Testing (Streaming Workers)**

**CONCEPTUAL PATTERN**: The following shows design patterns for streaming worker testing.
See `src/crank/testing/conceptual_patterns.py` for complete example implementations.

```python
# CONCEPTUAL: Adapt this pattern to your StreamingCoordinator implementation
class MockStreamingHarness:
    """Test harness for streaming without live connections."""

    def __init__(self, max_connections: int = 100):
        self.mock_connections = []
        self.max_connections = max_connections

    async def test_backpressure_handling(self):
        """Test stream behavior under load without live sockets."""
        # Your actual StreamingCoordinator implementation would be tested here
        coordinator = YourStreamingCoordinator()  # Replace with actual class

        # Simulate max connections
        connections = [MockWebSocket() for _ in range(self.max_connections)]

        # Test graceful degradation
        overflow_connection = MockWebSocket()
        result = await coordinator.handle_new_connection(overflow_connection)

        assert result.status == "backpressure_applied"
        assert "connection limit" in result.message
```

### **GPU Service Testing Patterns**

**CONCEPTUAL PATTERN**: Design framework for GPU testing across environments.
See `src/crank/testing/conceptual_patterns.py` for complete example implementations.

```python
# CONCEPTUAL: Adapt this pattern to your GPU inference service
class GPUTestStrategy:
    @staticmethod
    def get_test_strategy() -> str:
        """Determine testing approach based on environment."""
        if torch.cuda.is_available():
            return "full_gpu"
        elif "CI" in os.environ:
            return "mock_gpu"
        else:
            return "cpu_fallback"

    @staticmethod
    def run_inference_test(strategy: str, model_path: str):
        """Run inference test with appropriate strategy."""
        if strategy == "full_gpu":
            return YourGPUInferenceService().classify_image(test_image)  # Replace with actual
        elif strategy == "mock_gpu":
            return YourMockGPUService().classify_image(test_image)       # Replace with actual
        else:
            return YourCPUFallbackService().classify_image(test_image)   # Replace with actual
```

**Key Implementation Notes**:

- Replace `YourStreamingCoordinator`, `YourGPUInferenceService`, etc. with your actual service classes
- Adapt mock connection patterns to your specific WebSocket/SSE implementation
- Use the IMPLEMENTED `crank.testing.ensure_dependency` for environment checks## 📋 **AI Agent Implementation Checklist**

When implementing workers, AI agents should verify:

### **Pre-Implementation**

- [ ] Read unified refactoring plan for current platform status
- [ ] Identify deployment dependencies (Docker, CI, plugin configs)
- [ ] Plan backward compatibility strategy for capability changes
- [ ] Design standardized metadata schema for artifacts

### **Implementation**

- [ ] Follow established dependency checking patterns
- [ ] Implement comprehensive testing with environment detection
- [ ] Design extension hooks vs schema fields appropriately
- [ ] Plan migration shims for endpoint changes

### **Post-Implementation**

- [ ] Update all deployment artifact configurations
- [ ] Test migration/compatibility scenarios
- [ ] Verify monitoring and alerting coverage
- [ ] Document rollback procedures

## 🚀 **Success Criteria**

A production-ready worker must demonstrate:

- ✅ **Zero deployment surprises** - All artifacts updated consistently
- ✅ **Environment portability** - Works across dev/CI/prod with appropriate skips
- ✅ **Backward compatibility** - Existing clients continue working during migration
- ✅ **Operational observability** - Monitoring, alerting, and debugging support
- ✅ **Rollback readiness** - Can safely revert changes if issues arise

**Remember**: Code that works locally but breaks in deployment is worse than no code at all. Always think end-to-end! 🎯
