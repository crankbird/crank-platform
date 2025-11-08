# Pylance ML Configuration Documentation

**Updated**: 2025-11-08
**Review Date**: 2026-05-01 (Check every 6 months)
**Status**: Active - ML Library Type Limitations Workaround

## Overview

This document explains our Pylance type checking configuration overrides and the rationale for each setting. These overrides are **intentional engineering decisions** to separate genuine code problems from known ML library type system limitations.

## Why We Override Pylance Defaults

### The Problem
Machine Learning libraries in Python have fundamental incompatibilities with static type checking:

1. **sklearn**: No `py.typed` marker, dynamic model attributes after `.fit()`
2. **NLTK**: Academic software predating modern type hints
3. **PyTorch/TensorFlow**: Runtime-determined tensor shapes and types
4. **Container patterns**: Import fallbacks for development vs production

### The Solution
Configure Pylance to be ML-aware while preserving detection of real code issues.

## Configuration Details

### Suppressions (Warnings Only)

| Setting | Reason | Example Issue |
|---------|--------|---------------|
| `reportOptionalMemberAccess: "none"` | sklearn models gain attributes after `.fit()` | `model.predict_proba()` after `model = None` initialization |
| `reportGeneralTypeIssues: "warning"` | ML data shapes determined at runtime | `numpy.ndarray` type complexity |
| `reportUnknownMemberType: "none"` | NLTK lacks comprehensive stubs | `nltk.download()` return types |
| `reportUnknownArgumentType: "none"` | ML function signatures are complex/dynamic | sklearn fit() parameters |
| `reportUnknownVariableType: "none"` | Data types determined by runtime data | Model predictions, feature arrays |
| `reportAttributeAccessIssue: "none"` | ML models gain methods after training | `.classes_`, `.predict_proba()` post-fit |
| `reportUnknownParameterType: "none"` | sklearn/ML parameter types complex | Pipeline parameter inference |
| `reportOptionalOperand: "warning"` | Import fallback patterns | `SecureCertificateStore = None` fallbacks |
| `reportPossiblyUnboundVariable: "warning"` | Model attributes exist after fit | Variables set in ML training loops |

### Kept as ERRORS (Real Problems)

These remain as errors because they indicate actual code quality issues:

- `reportPrivateUsage: "error"` - Accessing private members
- `reportIncompatibleMethodOverride: "error"` - Inheritance problems
- `reportUninitializedInstanceVariable: "error"` - Missing initialization
- `reportConstantRedefinition: "error"` - Constant mutation

## Monitoring and Review Process

### Automated Checks

Create these GitHub issue reminders:

1. **6-month library review** (May 1, 2026):
   - Check if sklearn added `py.typed` marker
   - Verify if NLTK has official type stubs
   - Test if newer Pylance versions handle ML better

2. **Annual configuration audit** (November 8, 2026):
   - Review suppression necessity
   - Compare with industry ML best practices
   - Update documentation

### What Would Change Our Approach

**Remove overrides when:**
- sklearn ships with `py.typed` marker
- Official NLTK type stubs available via `types-nltk`
- Pylance adds ML-specific type inference
- Microsoft/Python community standardizes ML typing patterns

**Evidence to check:**
```bash
# Check for sklearn typing improvements
find .venv -name "py.typed" | grep sklearn

# Check for NLTK stubs
pip show types-nltk 2>/dev/null || echo "Not available"

# Check community adoption
# Review: python/typing discussions, sklearn issues, PyData conference talks
```

## Impact Assessment

### Benefits
- **Real issues visible**: No more noise from ML library limitations
- **Faster development**: Developers focus on actual problems
- **Consistent patterns**: Clear distinction between design and bugs

### Risks
- **Potential blind spots**: Might miss some type-related issues
- **Configuration complexity**: Need to maintain overrides
- **Team knowledge**: New developers must understand rationale

### Mitigation
- **Comprehensive documentation** (this file)
- **Regular review cycle** (scheduled above)
- **Ruff still active**: Catches style/logic issues Pylance misses
- **CI/CD testing**: Runtime behavior validation remains unchanged

## Testing the Configuration

After applying changes, verify effectiveness:

```bash
# Should show dramatically fewer errors
code services/crank_email_classifier.py
# Check Problems panel - should see mostly real issues, not ML library noise

# Verify ruff still catches real problems
uv run ruff check services/crank_email_classifier.py
# Should remain at 0 errors
```

## Related Documentation

- `docs/development/python-environment.md` - Python setup
- `docs/development/code-quality.md` - Linting and formatting
- `tests/README.md` - How we validate ML functionality without types

## Emergency Rollback

If this configuration causes problems:

1. **Immediate**: Set `"python.analysis.typeCheckingMode": "strict"` in `.vscode/settings.json`
2. **Remove**: All `diagnosticSeverityOverrides` entries
3. **Document**: What went wrong in this file
4. **Plan**: Alternative approach

---

**Principle**: We optimize for **detecting real problems** while acknowledging that ML development inherently conflicts with static typing assumptions.
