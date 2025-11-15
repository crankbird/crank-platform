# Master Zettel Vault: The Definitive Collection

**Purpose**: Single source of truth for all zettel knowledge, ending the chaos of scattered collections and fueling future Gherkin scenarios.

## 🎯 Anti-Chaos Principles

1. **One Vault, One Truth**: This is THE zettel collection. All others are archives.
2. **Clear Provenance**: Every zettel shows its journey through the analysis process
3. **Structured Navigation**: Thematic organization with clear purpose
4. **Working System**: Ready for Obsidian with proper graph visualization

## 📁 Vault Structure

```
MASTER-ZETTEL-VAULT/
├── 01-core-philosophy/        # Foundational worldview zettels
├── 02-business-systems/       # Strategy, RevOps, investment thinking  
├── 03-cognitive-science/      # Memory, AI-human interaction
├── 04-brand-science/          # Brand theory, cognitive mapping
├── 05-technical-systems/      # Harmoniser, technical architecture
├── 06-personas/              # Business strategy personas
├── 07-coordination/          # Project evolution, meta-analysis
├── .obsidian/               # Optimized graph visualization
└── MASTER-ZETTEL.md         # Central hub with navigation
```

### Directory Contents at a Glance

- `philosophy/`, `business/`, `cognitive-science/`, `brand-science/` — High-signal theories that inform platform positioning
- `technical/` — Architecture notes, historical refactors, algorithm sketches
- `personas/` — Stakeholder narratives and mascot perspectives
- `coordination/` — Meta-work on process, decision logs, and evolution of the team
- `zettels/` — Raw imports that still need cross-linking; treat as staging
- `INDEX.md` — Curated entry point with backlinks to the most referenced zettels

## 🔍 Content Provenance

- **Total Zettels**: 162 unique pieces of intellectual property
- **Source**: Curated from 7 scattered collections into single authoritative vault
- **Deduplication**: Systematic removal of redundant copies
- **Enhancement**: Standardized frontmatter, cross-links, thematic coherence

## 🚀 Usage

1. **Open in Obsidian**: File → Open Vault → MASTER-ZETTEL-VAULT
2. **Start with**: MASTER-ZETTEL.md (central navigation hub)
3. **Explore**: Follow thematic directories and cross-links
4. **Graph View**: Color-coded by domain (philosophy=purple, business=green, etc.)

## 🧪 Feeding BDD & Gherkin Work

- **Harvest** candidate scenarios by scanning `technical/` and `coordination/` for decisions with explicit inputs/outputs.
- **Traceability**: Reference the originating zettel slug inside `docs/proposals/` or `docs/planning/` when converting knowledge to requirements.
- **Curation Loop**:
  1. Highlight promising passages in the zettel.
  2. Create a planning note summarizing assumptions + open questions.
  3. Promote the distilled requirement into a Gherkin under `docs/proposals/` or the relevant repo directory.

This keeps the vault as the "rich source of Gherkins" without letting partially formed ideas leak directly into specs.

## ✍️ Contribution Workflow

1. **Draft in `zettels/`** with minimal structure.
2. **Annotate provenance** (source conversation, research link).
3. **Promote** into the appropriate thematic folder once cross-linked.
4. **Update `INDEX.md`** or another navigation file if the concept should be discoverable by agents.

When removing or superseding a zettel, leave a short pointer instead of deleting outright so lineage stays intact.

## ⚡ Integration Ready

- **Development Pipeline**: Gherkin extraction scripts included
- **Content Generation**: Jekyll pipeline for web publishing  
- **Analysis Tools**: Philosophical authenticity markers
- **Business Framework**: Complete persona and strategy system

---

*This vault replaces all scattered zettel collections. Other directories are preserved as archives but should not be used for active work.*
