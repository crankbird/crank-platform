---
id: zk20251020-CTX
title: "Context Taxonomy (v0.1)"
slug: context-taxonomy
date: 2025-10-20
context:
  - timezone: "Australia/Sydney"
  - thread: "Misc inquiries – 20 Oct 25"
  - creation_context: "Reflective travel / implied journal"
  - mood: "pensive, unhurried, observational"
  - utc: "2025-10-20T00:00:00Z"
summary: >
  Defines the controlled vocabulary for contextual metadata across Zettels to reduce ambiguity in ‘context’ fields.
tags: [taxonomy, metadata, zettelkasten, context]
type: "framework"
status: "draft"
collections: ["Crankbird Knowledge System"]

attribution:
  human_author: "Richard Martin (Crankbird)"
  ai_author: "ChatGPT (GPT-5 Thinking)"
  provenance:
    sources:
      human: 0.60
      ai: 0.35
      external: 0.05
  notes: >
    Drafted collaboratively; formatted to schema v1.1.

links:
  mentions: []
  urls: []

related_people: []
---
## Purpose
To disambiguate and standardize how contextual metadata is recorded within Zettels.
Prevents overloading of terms like *context*, *environment*, and *creation_context* by giving each a defined scope and data type.

## Core Categories (abridged)
- `thread`: conversation/session where the note emerged.
- `creation_context`: immediate situational environment of formation.
- `mood`: affective tone influencing cognition (controlled vocabulary).
- `environment`: physical/sensory setting (e.g., transit, office, cafe).
- `medium`: input channel or device (e.g., iPhone Notes, Obsidian).
- `occasion`: event catalyst (e.g., after workshop).

## Governance Rules
- Include `thread` and `date` in every note.
- Others are optional and additive.
- Context values are not hierarchical; analytics may group them later.

## Future Work
- Define controlled vocabularies for `mood` and `medium`.
- Integrate validation into a harmoniser workflow.

---
**Linked Zettels:**
- [[zk20251020-101]]
- [[zk20251020-102]]
- [[zk20251020-103]]
- [[zk20251020-104]]
