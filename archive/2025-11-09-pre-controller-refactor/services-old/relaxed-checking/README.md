# Relaxed Type Checking Directory

This directory contains modules that require relaxed type checking due to legitimate limitations in third-party library type systems, particularly in academic and computer vision libraries.

## Philosophy: "Fix What We Can, Tolerate What We Must"

Code in this directory follows a graduated approach:

- Real code quality issues are still fixed (missing return types, parameter annotations, etc.)

- Type checking is relaxed only for documented library limitations

- Maintains error detection for genuine problems while accommodating ecosystem realities

## Current Relaxations and Rationale

### Computer Vision Libraries (OpenCV, PIL, NumPy)

**Modules Affected:** `crank_image_classifier.py`

**Relaxed Checking:**

- `reportUnknownArgumentType: none` - OpenCV functions have dynamic signatures

- `reportUnknownMemberType: none` - cv2.SIFT_create() not recognized by type checker

- `reportAttributeAccessIssue: none` - OpenCV methods generated dynamically

- `reportPartiallyUnknownType: none` - NumPy arrays with unknown generic parameters

- `reportMissingTypeArgument: none` - np.ndarray generic specification issues

**Specific Issues Documented:**

1. **OpenCV cv2.SIFT_create()**: Method exists at runtime but not in type stubs

2. **NumPy Array Generics**: `ndarray[Unknown, Unknown]` due to dtype/shape complexity

3. **PIL getdata()**: Returns dynamic iterator types not captured in stubs

4. **FastAPI Handler Registration**: Event handlers treated as unknown callables

**What's Still Checked:**

- Missing imports and undefined variables

- Constant redefinition and unreachable code

- Private member access and basic logic errors

- Parameter and return type annotations where possible

## Review and Optimization Strategy

**Medium Priority GitHub Issue Created**: #TBD

- Regular review of upstream library type improvements

- Gradual tightening of relaxations as ecosystems mature

- Quarterly assessment of CV library type stub quality

- Migration plan for modules as libraries improve type support

## Usage Guidelines

### When to Add Modules Here

- Academic libraries without comprehensive type stubs

- Computer vision libraries with dynamic method generation

- Scientific computing libraries with complex generic types

- Libraries where type checking impedance outweighs benefits

### When NOT to Use

- General Python code quality issues (fix these normally)

- Missing annotations in our own code (add them)

- Standard library or well-typed third-party libraries

- Business logic that can be properly typed

## Configuration Details

The `pyrightconfig.json` in this directory:

- Maintains strict checking for critical errors

- Relaxes type inference for known problematic patterns

- Preserves warnings for borderline cases

- Documents rationale for each relaxation

## Migration Path

As computer vision and academic libraries improve type support:

1. Monitor upstream type stub quality quarterly

2. Test modules with stricter checking annually

3. Graduate modules back to main services/ when possible

4. Document successful migrations as success patterns
