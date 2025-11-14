# Implementation Status: Deployment Patterns

**Date**: November 14, 2025  
**Purpose**: Clarify what's implemented vs conceptual in deployment pattern documentation

## ✅ **IMPLEMENTED Components**

### **Dependency Testing Helper**

- **Location**: `src/crank/testing/dependency_checker.py`
- **Status**: ✅ FULLY IMPLEMENTED
- **Usage**: `from crank.testing import ensure_dependency`
- **Features**:
  - Python module detection (`torch`, `torch.cuda`, `transformers`)
  - System executable detection (`pandoc`, `libreoffice`)
  - GPU availability checking (CUDA, NVIDIA-ML)
  - Consistent skip messaging for pytest
  - Install hints for missing dependencies

### **Worker Migration Checklist**  

- **Location**: `deployment/worker-migration-checklist.yml`
- **Status**: ✅ IMPLEMENTED TEMPLATE
- **Usage**: Copy template for each worker migration
- **Features**:
  - Code implementation tracking
  - Deployment artifact coordination  
  - Infrastructure update checklist
  - Migration strategy planning
  - Validation and rollback procedures

## 🎯 **CONCEPTUAL Patterns (Not Implemented)**

### **Streaming Test Harnesses**

- **Location**: `src/crank/testing/conceptual_patterns.py` (examples only)
- **Status**: ⚠️ CONCEPTUAL PATTERNS
- **Purpose**: Design guidance for workers implementing streaming
- **Note**: Replace `YourStreamingCoordinator` with actual implementations

### **GPU Testing Strategies**

- **Location**: `src/crank/testing/conceptual_patterns.py` (examples only)
- **Status**: ⚠️ CONCEPTUAL PATTERNS
- **Purpose**: Framework for GPU testing across environments
- **Note**: Replace `YourGPUInferenceService` with actual implementations

### **Mock Connection Classes**

- **Examples**: `MockWebSocket`, `MockSSEConnection`, `MockGPUService`
- **Status**: ⚠️ CONCEPTUAL PATTERNS  
- **Purpose**: Show design patterns for testing without live connections
- **Note**: Workers should implement similar mocks for their specific needs

## 📋 **AI Agent Usage Guidelines**

### **Use IMPLEMENTED Components**

```python
# ✅ CORRECT: Use the implemented dependency helper
from crank.testing import ensure_dependency

def test_worker():
    ensure_dependency("pandoc", "Pandoc not available", "brew install pandoc")
    # Rest of test logic...
```

### **Adapt CONCEPTUAL Patterns**  

```python
# ⚠️ CONCEPTUAL: Adapt to your specific implementation
class YourStreamingCoordinator:  # Replace with your actual class
    async def handle_new_connection(self, connection):
        # Your actual implementation here
        pass

# Use the conceptual patterns as design guidance
harness = MockStreamingHarness()  # From conceptual_patterns.py
result = await harness.test_backpressure_handling()  # Adapt to your coordinator
```

### **Reference TEMPLATE Files**

```bash
# ✅ CORRECT: Use the implemented template
cp deployment/worker-migration-checklist.yml deployment/migration-my-worker-2025-11-14.yml

# Edit the copied file for your specific worker migration
```

## 🚨 **What NOT to Import**

```python
# ❌ INCORRECT: These don't exist as importable modules
from crank.streaming import StreamingCoordinator  # Does not exist
from crank.gpu import GPUInferenceService        # Does not exist  
from crank.mock import MockWebSocket             # Does not exist

# ✅ CORRECT: Use conceptual patterns as design guidance
# See src/crank/testing/conceptual_patterns.py for examples
# Implement your own classes based on these patterns
```

## 🎯 **Summary for AI Assistants**

1. **ALWAYS use** `crank.testing.ensure_dependency` - it's implemented and ready
2. **ALWAYS use** `deployment/worker-migration-checklist.yml` template for tracking
3. **ADAPT conceptual patterns** from `src/crank/testing/conceptual_patterns.py`
4. **NEVER import** `StreamingCoordinator`, `GPUInferenceService`, etc. - they're examples
5. **CREATE your own** mock classes and test harnesses based on conceptual patterns

The deployment patterns documentation now clearly distinguishes between working code and design guidance! 🚀
