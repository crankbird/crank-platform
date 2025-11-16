# ADR-0018: Use Docforge for Semantic Document Rendering

**Status**: Accepted
**Date**: 2025-11-16
**Deciders**: Platform Team, Docforge Team
**Technical Story**: [ADR Backlog 2025-11-16 – Documentation, Knowledge & Repo Structure](../planning/adr-backlog-2025-11-16.md#documentation-knowledge--repo-structure)

## Context and Problem Statement

Technical documentation needs to be rendered from markdown into various formats (HTML, PDF, presentations) while preserving semantic meaning and supporting advanced features like transclusion, templates, and multi-format output. How should we render documentation artifacts?

## Decision Drivers

- Semantic rendering: Preserve meaning not just layout
- Multi-format: HTML, PDF, PPTX, reveal.js
- Transclusion: Include sections from other docs
- Templates: Consistent styling
- Pandoc compatibility: Leverage existing tool
- Version control: Source files in Git

## Considered Options

- **Option 1**: Docforge (semantic Pandoc wrapper) - Accepted
- **Option 2**: Static site generator (MkDocs/Hugo)
- **Option 3**: Custom rendering pipeline

## Decision Outcome

**Chosen option**: "Docforge (semantic Pandoc wrapper)", because it provides semantic document rendering with Pandoc's multi-format capabilities while adding transclusion, templates, and intelligent section extraction.

### Positive Consequences

- Render to any format Pandoc supports
- Semantic transclusion (include specific sections)
- Template-based consistent styling
- Git-friendly source (plain markdown)
- Scriptable rendering
- Section extraction for AI context

### Negative Consequences

- Dependency on Pandoc
- Custom tool maintenance
- Learning curve for advanced features
- Build step required

## Pros and Cons of the Options

### Option 1: Docforge (Semantic Pandoc Wrapper)

Custom tool wrapping Pandoc with semantic features.

**Pros:**
- Semantic understanding
- Transclusion support
- Multi-format output
- Template system
- Section extraction
- Pandoc compatibility

**Cons:**
- Custom tool to maintain
- Pandoc dependency
- Build complexity
- Feature development needed

### Option 2: Static Site Generator (MkDocs/Hugo)

Purpose-built documentation generators.

**Pros:**
- Rich plugin ecosystem
- Built-in search
- Themes available
- Active communities

**Cons:**
- HTML-only (or limited formats)
- Less semantic features
- Template lock-in
- Not optimized for AI context extraction

### Option 3: Custom Rendering Pipeline

Build from scratch.

**Pros:**
- Full control
- Optimized for needs
- No external deps

**Cons:**
- Massive dev effort
- Reinventing Pandoc
- Maintenance burden
- Limited format support

## Links

- [Related to] ADR-0017 (Zettelkasten knowledge system)
- [Related to] ADR-0019 (Documentation layout standard)
- [Implements] Docforge tool (separate repository)

## Implementation Notes

**Docforge Architecture**:

```
docforge/
  src/
    docforge/
      parser.py          # Markdown + front-matter parsing
      transclude.py      # Section transclusion
      render.py          # Pandoc wrapper
      templates.py       # Template management
      section_extract.py # AI context extraction
```

**Transclusion Syntax**:

```markdown
# Main Document

## Overview

{{include: other-doc.md#installation}}

This transclude the "Installation" section from other-doc.md.

## Multi-Section

{{include: setup.md#prerequisites,installation,configuration}}
```

**Template Front-Matter**:

```yaml
---
title: "Crank Platform Architecture"
template: technical-report
output:
  html:
    css: styles/technical.css
  pdf:
    geometry: margin=1in
    toc: true
  pptx:
    reference-doc: templates/presentation.pptx
---
```

**Rendering Command**:

```bash
# Render single document
docforge render architecture.md --format html,pdf,pptx

# Render with template
docforge render --template technical-report architecture.md

# Extract sections for AI
docforge extract architecture.md --sections "Overview,Implementation"
```

**Section Extraction for AI Context**:

```python
# Used by agents to get focused context
from docforge import extract_sections

sections = extract_sections(
    "docs/architecture/CONTROLLER_WORKER_MODEL.md",
    ["Core Concepts", "Implementation"]
)

# Returns markdown snippets with semantic boundaries preserved
```

**Integration with Workflow**:

```yaml
# .github/workflows/docs.yml
name: Documentation

on:
  push:
    paths: ['docs/**']

jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Docforge
        run: pip install docforge
      - name: Render Documentation
        run: |
          docforge render docs/architecture/*.md --format html,pdf
          docforge render docs/reports/*.md --format pdf
      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: rendered-docs
          path: docs/rendered/
```

**Benefits for AI Agents**:

- **Section extraction**: Get focused context without full document
- **Transclusion resolution**: Follow includes to gather related content
- **Template awareness**: Understand document structure
- **Multi-format**: Generate presentations from markdown in code

## Review History

- 2025-11-16 - Initial decision (formalizing Docforge usage)
