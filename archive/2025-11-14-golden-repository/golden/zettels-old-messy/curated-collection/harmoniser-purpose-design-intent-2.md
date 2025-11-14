---
id: zk20251020-101
title: "Harmoniser — Purpose & Design Intent"
slug: harmoniser-purpose-design-intent
date: 2025-10-20
context: "Misc inquiries – 20 Oct 25"
summary: >
  Establishes the mission, success criteria, constraints, and guiding principles
  for a context/metadata harmoniser across the Crankbird knowledge ecosystem.
tags: [harmoniser, governance, metadata, design-intent]
type: "framework"
status: "draft"
collections: ["Crankbird Knowledge System"]

attribution:
  human_author: "Richard Martin (Crankbird)"
  ai_author: "ChatGPT (GPT-5 Thinking)"
  provenance:
    sources:
      human: 0.6
      ai: 0.35
      external: 0.05
  notes: >
    Drafted during a reflective travel session; emphasizes intent before execution.
---

## Mission
Create a *gentle* tool that reduces semantic drift in Zettel front-matter without overwriting authorial nuance.

## Problems It Solves
- Inconsistent field names/values (e.g., mood synonyms, medium/device variants).
- Accreting schema variants across projects/sessions.
- Lost analytic value from unnormalised context fields.

## Non-Goals
- **Not** an automatic editor of prose content.
- **Not** a rigid enforcer that blocks writing flow.
- **Not** a replacement for thoughtful taxonomy design.

## Principles
1. **Author-first**: prefer warnings and suggested diffs over silent rewrites.  
2. **Idempotent**: multiple runs produce stable results.  
3. **Transparent**: every change is explainable and reversible.  
4. **Provenant**: record what changed, why, and by which rule.  
5. **Minimal**: touch as little as necessary to achieve harmony.

## Success Criteria
- ≥95% reduction in context/mood/medium duplicates over 30 days.
- Round-trip safety: no loss of comments or ordering in YAML.
- Clear audit log per file; Git-friendly diffs.

## Scope (v0.1)
- Parse YAML front-matter; normalise `context`-related fields using controlled vocabulary.
- Validate required keys (`id`, `title`, `date`, `context`).
- Emit NDJSON summary for analytics.

## Stakeholders
- Primary: Note author/curator (see [[zk20251020-102]]).  
- Secondary: Agent13/14 automations; collaborators; future publishing pipeline.

## Open Questions
- Where to store rule exceptions per-note?
- How to model mood intensity without clutter?
- When to suggest schema upgrades vs. silently supporting legacy?

## Related
- Personas: [[zk20251020-102]]  
- JTBD: [[zk20251020-103]]  
- Stories & Tests: [[zk20251020-104]]
