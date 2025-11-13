---
schema_version: "1.0"
source: "sonnet-second-pass/content/philosophical-tagging-schema.md"
last_updated: "2024-11-13"
purpose: "Canonical philosophical schema for unified knowledge base"
---

# Philosophical Schema Configuration

This directory contains the canonical philosophical schema and clustering outputs that drive both content organization and technical architecture decisions.

## Core Philosophy → Platform Mapping

The platform architecture follows the philosophical framework:

- **Intelligence Is Situated** → Context-sensitive service deployment
- **Space Has Meaning** → Local-first architecture, edge computing
- **Time Unevenly Distributed** → Temporal arbitrage features, future-sensing
- **Identity Is Plural** → Persona-driven interfaces, contextual adaptation
- **Agency Is Distributed** → Agent networks, M2M coordination  
- **Data Has Gravity** → Semantic-driven computation placement

## Schema Evolution

### Primary Markers (Core Principles)
- SHM: Space-Has-Meaning
- TUD: Time-Unevenly-Distributed  
- IIP: Identity-Is-Plural
- AID: Agency-Is-Distributed
- DHG: Data-Has-Gravity

### Secondary Themes (Applications)
- BIZ: Business-Systems
- TECH: Technical-Systems
- COG: Cognitive-Science
- STRAT: Strategic-Applications

## Coherence Scoring

- **5**: Very strong philosophical alignment across multiple principles
- **4**: Strong expression of core principles with clear applications
- **3**: Moderate philosophical content with some principle manifestation
- **2**: Weak philosophical content but supports themes
- **1**: Minimal philosophical content, preserved for completeness

## Content Pipeline Integration

### Publication Readiness Calculation
```yaml
factors:
  - title_present: 1.0
  - summary_present: 1.0  
  - attribution_present: 1.0
  - coherence_score >= 3.0: 1.0
  - coherence_score >= 4.0: 1.0
  - call_to_action_present: 1.0
max_score: 5.0
```

### Persona Mapping
```yaml
SHM: ["systems_architect", "field_decision_maker"]
TUD: ["future_sensing_executive", "distributed_researcher"] 
IIP: ["identity_fracturer", "context_aware_consumer"]
AID: ["systems_architect", "distributed_researcher"]
DHG: ["systems_architect", "field_decision_maker"]
```

## Technical Integration

### Theme Detection
- **Keyword Matching**: Frequency-based scoring with philosophical weight
- **Pattern Recognition**: Regex patterns for principle manifestation
- **Context Analysis**: Title + body content examination
- **Tag Integration**: Existing classification system preservation

### Cross-Reference Generation
- **Embedding Similarity**: Cosine similarity within philosophical themes
- **Reciprocal Linking**: Bidirectional relationship maintenance
- **Cluster Connectivity**: Theme-based connection suggestions

### Jekyll Pipeline
- **Category Mapping**: Philosophical themes → Jekyll categories
- **Navigation Order**: Coherence score → content sequence
- **Metadata Enrichment**: Schema-driven frontmatter generation

---

*This schema ensures that philosophical insights drive both content organization and technical implementation, maintaining coherence from worldview to platform architecture.*