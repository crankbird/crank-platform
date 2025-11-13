---
id: zk20251020-CTX
title: "Context Taxonomy (v0.1)"
slug: context-taxonomy
date: 2025-10-20
summary: >
  Defines the controlled vocabulary for contextual metadata fields used across Zettels,
  ensuring semantic consistency and reducing ambiguity between overlapping terms.
tags: [taxonomy, metadata, zettelkasten, context]
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
    Developed collaboratively to support structured metadata across the Crankbird knowledge ecosystem.
---

## Purpose
To disambiguate and standardize how contextual metadata is recorded within Zettels.  
Prevents overloading of terms like *context*, *environment*, and *creation_context* by giving each a defined scope and data type.

## Core Categories

### 1. `thread`
**Definition:** Logical conversation or working session in which the note emerged.  
**Examples:** `"Misc inquiries – 20 Oct 25"`, `"Brand Engineering overview"`.  
**Type:** String (short).

### 2. `creation_context`
**Definition:** Immediate situational or environmental conditions under which the thought was formed.  
**Examples:** `"On public transport from Jindabyne to Sydney"`, `"Late-night coding session"`.  
**Type:** String (medium).

### 3. `mood`
**Definition:** Subjective affective state or tone influencing cognition during note creation.  
**Examples:** `"pensive"`, `"energised"`, `"melancholic"`, `"analytical"`.  
**Type:** Controlled vocabulary (optional multi-value).

### 4. `environment`
**Definition:** Physical or sensory setting in which creation occurred.  
**Examples:** `"quiet study"`, `"outdoors"`, `"urban transit"`, `"conference room"`.  
**Type:** String (short).

### 5. `medium`
**Definition:** Input channel or device used.  
**Examples:** `"iPhone Notes"`, `"MacBook Pro (Obsidian)"`, `"voice dictation"`.  
**Type:** Enum (controlled).

### 6. `occasion`
**Definition:** External event or catalyst for note creation.  
**Examples:** `"after NetApp workshop"`, `"during coffee with collaborator"`.  
**Type:** String (optional).

---

## Governance Rules
- Each Zettel **must** include at least `thread` and `date`.  
- Other context fields are **optional** and additive.  
- Context values are **not hierarchical**, but may be grouped in analytics layers (e.g., by mood/environment correlation).  
- Future schemas (v1.2+) may include temporal subfields like `circadian_window` or `cognitive_state`.

---

## Future Work
- Define controlled vocabularies for `mood` and `medium`.  
- Integrate taxonomy validation into harmoniser script.  
- Cross-map with *Crankbird Brand Science* affective-state lexicon (planned).
