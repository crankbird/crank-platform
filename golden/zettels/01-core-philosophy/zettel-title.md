# Crankbird Zettel Front-Matter Reference

This document summarises the recommended front-matter schema and usage conventions for **Crankbird Zettels** (Obsidian + Drafts workflow).

---

## ✅ Core Schema

```yaml
---
id: zkYYYYMMDD-XXX
title: "Zettel Title"
slug: zettel-title
date: YYYY-MM-DD
context: "Misc inquiries – DD Mon YY"
summary: >
  One-line essence or thesis of the note; useful for search and embedding metadata.
tags: [tag1, tag2, tag3]
type: "insight"   # insight | framework | reference | workflow
status: "draft"   # draft | published | evergreen
collections: ["Brand Science", "Operational Systems"]

attribution:
  human_author: "Richard Martin (Crankbird)"
  ai_author: "ChatGPT (GPT-5 Thinking)"
  provenance:
    sources:
      human: 0.50
      ai: 0.45
      external: 0.05
  notes: >
    Brief note on influences, quotations, or synthesis.

links:
  mentions: ["zk20251018-004", "zk20250912-002"]
  urls: ["https://example.com/paper"]

related_people: ["Tulving", "Kahneman"]
---
```

---

## 🧩 Notes on Design Choices

| Element | Why It’s Useful |
|----------|----------------|
| **id** | Deterministic unique key for backlinks and referencing. |
| **slug** | Keeps filenames and URLs predictable. |
| **summary** | Enables AI, search, and Dataview to surface notes intelligently. |
| **type** | Distinguishes insights, frameworks, references, and workflows. |
| **status** | Tracks lifecycle of ideas from draft to evergreen. |
| **collections** | Logical grouping for projects or research themes. |
| **attribution** | Captures authorship and provenance transparency. |
| **links** | Explicit backlinks and external references. |
| **related_people / sources** | Supports later auto-bibliography generation. |

---

## 📚 Example

```yaml
---
id: zk20251019-001
title: "Crankbird Morning Ops Protocol"
slug: crankbird-morning-ops-protocol
date: 2025-10-19
context: "Misc inquiries – 19 Oct 25"
summary: >
  Morning routine designed to replace cortisol-driven urgency with calm dopaminergic activation.
tags: [routine, adhd, executive_function, ops]
type: "workflow"
status: "draft"
collections: ["Brand Science", "Operational Systems"]

attribution:
  human_author: "Richard Martin (Crankbird)"
  ai_author: "ChatGPT (GPT-5 Thinking)"
  provenance:
    sources:
      human: 0.50
      ai: 0.45
      external: 0.05
  notes: >
    Synthesised from self-observation and GPT-assisted analysis of executive function.

links:
  mentions: ["zk20251018-004", "zk20250912-002"]
  urls: ["https://artisanal-intelligence.info/"]

related_people: ["Tulving", "Kahneman"]
---
```

---

## 🧠 Implementation Notes

- Use **ISO 8601** dates for sorting and compatibility (`YYYY-MM-DD`).
- Keep **keys lowercase** for YAML/JSON consistency.
- The **provenance** block supports numeric ratios for better data parsing.
- Maintain a canonical order of fields for readability and predictable parsing.

**Recommended order:**

```
id:
title:
slug:
date:
context:
summary:
tags:
type:
status:
collections:
attribution:
links:
related_people:
```

---

## 🪶 Practical Tips

1. Keep the YAML front matter above the first `---` separator.
2. Turn on *Readable Line Length* in Obsidian preferences.
3. Store templates in `/Templates/ZK_template.md` for quick creation.
4. Use `[[links]]` internally to build a semantic network across notes.
5. Maintain a weekly curation ritual to move captures from Drafts → Obsidian.

---

© 2025 Richard Martin (Crankbird) — created collaboratively with ChatGPT (GPT‑5 Thinking).
