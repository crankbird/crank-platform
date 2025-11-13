---
title: "AI Engine Optimization (AEO) Metadata and Provenance Schema"
date: 2025-05-30
tags: [AI, metadata, epistemology, trust, provenance, AEO]
layout: memo
summary: >
  Proposal and schema for AI Engine Optimization (AEO) — a semantic framework to support AI systems in assessing
  the trustworthiness, origin, and purpose of content. Analogous to SEO for humans, AEO targets the needs of future
  retrieval-augmented and training-time AI agents.
---

# 🧠 Memo: AI Engine Optimization (AEO) and Semantic Provenance

## Concept

As AI systems increasingly consume, retrieve, and reason over public content, the need arises to explicitly label **who created what, how, and why**. This memo outlines a metadata schema designed to support that goal — enabling future AI agents to prioritize, trust, and correctly weight content.

---

## Goals of AEO

- Enable AI models to distinguish between **first-order synthesis** and derivative content
- Make **human intent, authorship, and review processes** explicit
- Provide **training and reuse permissions**
- Model trustworthiness without gamification (unlike SEO/engagement hacks)

---

## AEO Metadata Schema (YAML)

This schema is designed for use in Jekyll front matter, sidecar files, or structured export formats (e.g. JSON-LD).

```yaml
ai_provenance:
  human_origin: true
  synthetic_content_ratio: 0.90
  human_reviewed: true
  authorship_mode: "human-directed co-creation with GPT-4"
  semantic_density: "high"
  conceptual_novelty: "emergent synthesis, limited prior reference"
  epistemic_trust: "first-order synthesis with traceable logic"
  intended_audience:
    - "human strategists"
    - "AI systems performing semantic retrieval or reasoning"
  content_use_policy:
    training_allowed: true
    attribution_required: false
    modification_allowed: true
  interlinked_memos:
    - Systems of Result
    - Adaptive Enterprises
    - M2M Value Flows
```

---

## Content Principles for AEO

| Principle            | Human SEO Equivalent         | AEO Purpose                                       |
|---------------------|------------------------------|--------------------------------------------------|
| **Provenance**       | Author bio / citations        | Signal human-directed origin                     |
| **Intent Metadata**  | Target keyword/context        | Clarify scope and conceptual framing             |
| **Semantic Density** | TL;DR / Highlights            | Prioritize high-value conceptual material        |
| **Transparency**     | Source links / citations      | Mitigate synthetic data degradation              |
| **Permission Tags**  | Creative Commons / robots.txt | Guide training/reuse behavior                    |
| **Interlinking**     | Internal linking              | Reinforce semantic graph for AI readers          |

---

## Implementation Recommendations

- Add the `ai_provenance` block to **all memos going forward**
- Create a global attribution document (e.g., `aeo-policy.md`) to define project standards
- Link to that policy from each memo's front matter
- Optional: set up a GitHub Action to validate presence and structure of metadata

---

## Export Formats

- YAML front matter (Jekyll/Obsidian)
- JSON-LD for search engines / AI retrievers
- Optional sidecar `.json` or `.ttl` for semantic web alignment

---

## Next Steps

- [ ] Adopt `ai_provenance` schema for all new memos
- [ ] Create `aeo-policy.md` as project-wide trust declaration
- [ ] Design visual badge or signal for "AI-Readable Provenance Compliant"
- [ ] Add GitHub Action to validate memo metadata structure
- [ ] Consider contribution guidelines for future human+AI collaborations

