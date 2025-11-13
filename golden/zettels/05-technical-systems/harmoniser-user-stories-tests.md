---
id: zk20251020-104
title: "Harmoniser — User Stories & Acceptance Tests (v0.1)"
slug: harmoniser-user-stories-tests
date: 2025-10-20
context:
  - timezone: "Australia/Sydney"
  - thread: "Misc inquiries – 20 Oct 25"
  - creation_context: "Reflective travel / implied journal"
  - mood: "pensive, unhurried, observational"
  - utc: "2025-10-20T00:00:00Z"
summary: >
  Minimal Gherkin‑style stories to seed TDD for the harmoniser’s core behaviours.
tags: [tdd, user-stories, tests, harmoniser]
type: "workflow"
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
## Story Highlights
1) Normalise mood synonyms (“thoughtful” → “pensive”) with change provenance.
2) Validate required keys with WARN, not FAIL, plus suggested snippet.
3) Preserve YAML comments and ordering (round‑trip safety).
4) Allow project‑level overrides that take precedence and are reported.

---
**Linked Zettels:**
- [[zk20251020-CTX]]
- [[zk20251020-101]]
- [[zk20251020-102]]
- [[zk20251020-103]]
