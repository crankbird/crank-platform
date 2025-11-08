---
name: Pylance ML Configuration Review
about: Periodic review of ML library type checking overrides
title: 'Pylance ML Config Review - [DATE]'
labels: ['technical-debt', 'type-checking', 'ml-libraries']
assignees: ''
---

## Review Checklist

**Review Period**: [Insert Date Range]
**Configuration File**: `docs/pylance-ml-configuration.md`
**Last Updated**: 2025-11-08

### Library Status Check

- [ ] **sklearn** - Check for `py.typed` marker
  ```bash
  find .venv -name "py.typed" | grep sklearn || echo "Still no py.typed"
  ```
- [ ] **NLTK** - Check for official type stubs
  ```bash
  pip show types-nltk 2>/dev/null || echo "Still no official stubs"
  ```
- [ ] **PyTorch** - Review typing improvements in latest version
- [ ] **Community standards** - Check Python typing PEPs and ML community discussions

### Current Error Count Assessment

- [ ] Run error count before config: `# TODO: Add baseline count`
- [ ] Run error count with config:
  ```bash
  # Open email classifier in VS Code, count Problems panel
  ```
- [ ] Verify ruff still at 0 errors:
  ```bash
  uv run ruff check services/crank_email_classifier.py
  ```

### Decision Matrix

| Library | Current Status | Action Required | Evidence |
|---------|---------------|-----------------|----------|
| sklearn | No py.typed | Keep override | [Link to sklearn typing status] |
| NLTK | No stubs | Keep override | [Link to types-nltk availability] |
| PyTorch | Partial typing | Monitor | [Version and typing status] |

### Recommendations

- [ ] **Keep current config** - Libraries still lack full typing
- [ ] **Modify config** - Some improvements available (specify which)
- [ ] **Remove overrides** - Libraries now fully typed (specify which)

### Actions

- [ ] Update configuration if needed
- [ ] Update documentation with new review date
- [ ] Schedule next review (6 months from completion)
- [ ] Update baseline error counts in documentation

### Notes

[Add any observations, changes in ML typing landscape, or other relevant findings]

---

**Auto-close conditions**:
- All ML libraries we use have comprehensive type stubs
- Pylance adds ML-specific inference
- Community consensus on better ML typing patterns
