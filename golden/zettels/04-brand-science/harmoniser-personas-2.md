---
id: zk20251020-102
title: "Harmoniser Personas (v0.1)"
slug: harmoniser-personas
date: 2025-10-20
context: "Misc inquiries – 20 Oct 25"
summary: >
  Three pragmatic personas to anchor design decisions for the harmoniser.
tags: [personas, ux, harmoniser]
type: "framework"
status: "draft"
collections: ["Crankbird Knowledge System"]

attribution:
  human_author: "Richard Martin (Crankbird)"
  ai_author: "ChatGPT (GPT-5 Thinking)"
  provenance:
    sources:
      human: 0.55
      ai: 0.40
      external: 0.05
  notes: >
    Lightweight personas grounded in current workflows; evolve via usage data.
---

## P1 — The Author-Curator (“R”)
- **Goal:** Write fast, keep metadata tidy without thinking about it.
- **Frictions:** Naming drift, inconsistent tags, schema anxiety mid-flow.
- **Must-haves:** Non-destructive suggestions; one-click apply; clear diffs.

## P2 — The Collaborator (“C”)
- **Goal:** Contribute notes without memorising house style.
- **Frictions:** PR churn from formatting nits; unclear violations.
- **Must-haves:** Pre-commit checks with human-readable guidance.

## P3 — The Automation Agent (Agent13/14)
- **Goal:** Depend on predictable metadata for downstream tasks.
- **Frictions:** Edge-case schema variants; brittle parsers.
- **Must-haves:** Machine-readable report; stable enums; versioned vocab.

## Design Implications
- Ship with **explainable rules** and **soft enforcement**.
- Provide **CLI + pre-commit hook** and **NDJSON report**.
- Support **project overrides** without forking the core vocabulary.

**Related:** Purpose [[zk20251020-101]] · JTBD [[zk20251020-103]] · Stories [[zk20251020-104]]
