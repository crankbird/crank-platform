---
name: 🔄 API Endpoint Naming Consistency Review
about: Investigate and standardize endpoint naming across all services
title: "[API] Standardize endpoint naming convention across all services"
labels: ["enhancement", "api-design", "consistency", "breaking-change"]
assignees: []
---

## 🔍 Problem Identified

During email classifier testing, discovered **inconsistent endpoint naming** across services that violates the **principle of least surprise**:

### Current Inconsistencies Observed
- **Email Classifier**: `/classify` (generic)
- **Expected Pattern**: `/classify_email` (service-specific)
- **Potential Others**: `/classify_image`, `/parse_email`, etc.

## 🎯 Investigation Required

### 1. Audit All Service Endpoints
- [ ] Email Classifier: Document actual endpoints
- [ ] Email Parser: Document actual endpoints
- [ ] Image Classifier (CPU): Document actual endpoints
- [ ] Image Classifier (GPU): Document actual endpoints
- [ ] Document Converter: Document actual endpoints
- [ ] Streaming Service: Document actual endpoints
- [ ] Platform Service: Document actual endpoints

### 2. Identify Patterns
- [ ] Generic patterns: `/classify`, `/parse`, `/convert`
- [ ] Service-specific patterns: `/classify_email`, `/parse_email`
- [ ] Resource-based patterns: `/emails/classify`, `/images/classify`
- [ ] Action-based patterns: `/classification`, `/parsing`

## 💭 Design Considerations

### Option A: Service-Specific Endpoints
```
/classify_email     # Email classifier
/classify_image     # Image classifier
/parse_email        # Email parser
/convert_document   # Document converter
```
**Pros**: Clear, unambiguous, follows service naming
**Cons**: Longer URLs, potential redundancy

### Option B: Generic Endpoints (Current)
```
/classify          # All classifiers
/parse             # All parsers
/convert           # All converters
```
**Pros**: Shorter, consistent across service types
**Cons**: Ambiguous, doesn't follow principle of least surprise

### Option C: Resource-Based RESTful
```
/emails/classify   # Email operations
/images/classify   # Image operations
/documents/convert # Document operations
```
**Pros**: RESTful, scalable, resource-centric
**Cons**: Larger breaking change

### Option D: Hybrid Approach
```
/classify          # Primary endpoint (backward compatibility)
/classify_email    # Explicit alias for clarity
```
**Pros**: Backward compatible, clear intent
**Cons**: Multiple endpoints for same function

## 🚨 Impact Assessment

### Breaking Changes
- [ ] Determine client dependencies on current endpoints
- [ ] Assess Docker compose configurations
- [ ] Review integration tests and scripts
- [ ] Check documentation and examples

### Migration Strategy
- [ ] Version migration path (v1/v2)
- [ ] Deprecation timeline
- [ ] Backward compatibility period
- [ ] Client notification process

## ✅ Acceptance Criteria

- [ ] **Consistency**: All services follow same naming convention
- [ ] **Clarity**: Endpoint names follow principle of least surprise
- [ ] **Documentation**: All endpoints clearly documented
- [ ] **Migration**: Clear path for existing integrations
- [ ] **Testing**: All endpoint changes validated

## 🔗 Context

**Discovered During**: Email classifier cleanup and testing (November 7, 2025)
**Root Cause**: Incremental development without overall design review
**Priority**: Medium (affects developer experience and API usability)

## 📋 Action Items

1. **Week 1**: Complete service endpoint audit
2. **Week 2**: Design review and decision on naming convention
3. **Week 3**: Implementation plan and breaking change assessment
4. **Week 4**: Implementation with backward compatibility
5. **Week 5**: Documentation update and client notification

---

**Reporter**: AI Assistant (GitHub Copilot)
**Date**: November 7, 2025
**Context**: Email classifier exemplar cleanup project
