---
name: "📊 Computer Vision Type Checking Optimization"
about: "Quarterly review and optimization of relaxed type checking for CV libraries"
title: "Optimize Computer Vision Library Type Checking Relaxations"
labels: ["enhancement", "technical-debt", "medium-priority", "type-checking"]
assignees: []
---

## 🎯 Objective

Review and optimize the relaxed type checking configuration for computer vision libraries in `services/relaxed-checking/` to gradually tighten type safety as the ecosystem matures.

## 📋 Current State

**Module:** `services/relaxed-checking/crank_image_classifier.py`

**Libraries Affected:**

- OpenCV (cv2) - Dynamic method generation, missing type stubs
- NumPy - Generic array type complexity
- PIL/Pillow - Dynamic image processing methods
- FastAPI - Event handler registration patterns

**Relaxed Settings Applied:**

```json
"reportUnknownArgumentType": "none",
"reportUnknownMemberType": "none",
"reportAttributeAccessIssue": "none",
"reportPartiallyUnknownType": "none",
"reportMissingTypeArgument": "none"
```

## 🔍 Specific Issues Documented

### OpenCV Issues

- [ ] `cv2.SIFT_create()` - Method exists at runtime but not in type stubs
- [ ] Dynamic method generation in cv2 modules
- [ ] `cv2.cvtColor()` parameter type inference

### NumPy Issues

- [ ] `np.ndarray[Unknown, Unknown]` - Generic type specification complexity
- [ ] Array dtype and shape inference limitations
- [ ] Inter-operation with OpenCV arrays

### PIL Issues

- [ ] `image.getdata()` - Returns dynamic iterator types
- [ ] Color space conversion type inference
- [ ] Image manipulation method signatures

### FastAPI Issues

- [ ] Event handler registration as unknown callables
- [ ] Endpoint function type inference

## ✅ Tasks

### Quarterly Review (Due: Q1 2026)

- [ ] Check OpenCV type stub updates in opencv-python-stubs
- [ ] Review NumPy typing improvements in numpy>=1.24
- [ ] Test PIL/Pillow type stub enhancements
- [ ] Evaluate FastAPI typing updates

### Testing Protocol

- [ ] Create test branch with stricter checking
- [ ] Run image classifier with `reportUnknownMemberType: "warning"`
- [ ] Identify which relaxations can be tightened
- [ ] Document any new type stub discoveries

### Optimization Opportunities

- [ ] Add explicit type hints where possible (our code)
- [ ] Use `cast()` for known-safe dynamic operations
- [ ] Implement wrapper functions with proper typing
- [ ] Consider alternative libraries with better type support

### Success Metrics

- [ ] Reduce number of relaxed rules by 25%
- [ ] Maintain zero runtime errors
- [ ] Improve IDE autocomplete and error detection
- [ ] Document successful patterns for other modules

## 🔄 Migration Strategy

### Phase 1: Assessment (1 week)

```bash
# Test current strictness tolerance
cd services/relaxed-checking
cp pyrightconfig.json pyrightconfig.json.backup
# Gradually increase checking strictness
```

### Phase 2: Targeted Fixes (2 weeks)

- Fix issues that can be resolved with our code changes
- Add explicit type annotations where beneficial
- Implement type-safe wrappers for problematic library calls

### Phase 3: Configuration Optimization (1 week)

- Update pyrightconfig.json with tighter settings
- Document remaining legitimate relaxations
- Update README with new baseline

## 📝 Notes

**Priority:** Medium - Part of ongoing technical debt reduction
**Effort:** 1-2 sprints quarterly
**Risk:** Low - Changes are incremental with easy rollback

**Context:** Created during systematic codebase cleanup where image classifier was moved from 82 errors → 0 errors through combination of code quality fixes and appropriate library limitation accommodation.

**Philosophy:** "Fix what we can, tolerate what we must" - This issue focuses on the "fix what we can" aspect as library ecosystems mature.
