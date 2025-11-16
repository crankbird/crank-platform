---
id: zk20251020-104
title: "Harmoniser — User Stories & Acceptance Tests (v0.1)"
slug: harmoniser-user-stories-tests
date: 2025-10-20
context: "Misc inquiries – 20 Oct 25"
summary: >
  Minimal story set with Gherkin-style acceptance criteria to seed TDD.
tags: [tdd, user-stories, tests, harmoniser]
type: "workflow"
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
    Start small; grow coverage as rules and vocabulary stabilise.
---

## Story 1 — Normalise Mood Synonyms
**As** an Author-Curator  
**I want** “thoughtful” to resolve to “pensive”  
**So that** analytics treat them as one mood

**Acceptance (Gherkin)**

```
Given a note with context mood: "thoughtful"
When I run the harmoniser with the default vocabulary
Then the mood value is "pensive"
And a change record explains the mapping rule
And no other fields change
```

## Story 2 — Validate Required Keys
**As** an Automation Agent  
**I want** notes missing `context` to be flagged  
**So that** downstream tools don’t break

**Acceptance**

```
Given a note missing the context field
When I run the harmoniser
Then it exits with code 0
And emits a WARNING stating "context missing"
And suggests a minimal example snippet
```

## Story 3 — Preserve YAML Shape (Round-Trip Safety)
**As** a Collaborator  
**I want** comments and ordering preserved  
**So that** diffs remain human-readable

**Acceptance**

```
Given a note whose front-matter includes comments and custom ordering
When I run the harmoniser
Then the output preserves comment lines and key order
And only target fields are changed
```

## Story 4 — Project Overrides
**As** an Author-Curator  
**I want** a local overrides file  
**So that** I can use custom moods without forking the core vocab

**Acceptance**

```
Given a project with ctx-overrides.yml extending mood mappings
When I run the harmoniser
Then local mappings take precedence
And the report lists which rules came from overrides
```

**Related:** Purpose [[zk20251020-101]] · Personas [[zk20251020-102]] · JTBD [[zk20251020-103]]
