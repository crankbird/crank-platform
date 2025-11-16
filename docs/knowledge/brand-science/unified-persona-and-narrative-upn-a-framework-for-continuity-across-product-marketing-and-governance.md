---
title: "Unified Persona and Narrative (UPN): A Framework for Continuity Across Product, Marketing, and Governance"
author: "Ricky Martin / Crankbird"
version: "v0.1 (Working Paper)"
date: "2025-10-15"
---

## Abstract  
This paper proposes a *Unified Persona and Narrative* (UPN) model to resolve the persistent discontinuity between product-development personas and marketing personas in contemporary organizations. Drawing from design theory, cognitive psychology, and agile software practice, UPN reconceptualises personas not as static fictions but as **context-dependent cognitive frames**—“hats” that individuals adopt dynamically within socio-technical systems. The model integrates insights from schema theory (Bartlett, 1932), job-to-be-done (Christensen et al., 2016), and behavioural design (Thaler & Sunstein, 2008) to align user empathy, buyer motivation, and governance accountability within a single semantic schema.  

---

## 1. The Problem of Persona Fragmentation  
In many firms, “personas” diverge across silos: designers imagine empathetic users, marketers invent rational buyers, and governance teams represent abstract risk owners. This divergence produces *discontinuous empathy*—the same human is treated as multiple, incompatible entities. Academic critiques have noted that traditional personas often conflate demographic fiction with behavioural evidence (Cooper, 1999; Matthews, 2012). Meanwhile, “buyer persona” models in marketing emphasise procurement rationality over experiential context, reflecting what Homburg et al. (2017) describe as a split between *use value* and *exchange value*.  

---

## 2. From Person to Persona to Hat  
Building on interaction-design research (Norman, 2013) and role theory (Biddle, 1986), UPN distinguishes **archetypes**, **personas**, and **hats**.  
- *Archetypes* are enduring motivational patterns (e.g., “Technical Champion,” “Risk Controller”).  
- *Personas* are composites linking archetypes to situational constraints.  
- *Hats* are transient cognitive frames a real individual adopts in context (User, Buyer, Approver, Governor).  

A single actor may change hats repeatedly—even within a meeting—without ceasing to be the same person. Recognising these intra-personal frame shifts avoids conflating biography with behaviour.  

---

## 3. Semantic Unification  
The UPN schema encodes each persona as a node with horizon-specific facets—**Use**, **Buy**, and **Governance**—mirroring multi-time-scale maturity models such as *Magic Roundabout* (Martin, 2025). Each facet records goals, metrics, decision factors, and micro-narratives expressed as structured YAML for interoperability with product backlogs and marketing automation systems:

\`\`\`yaml
persona:
  id: sophie_system_architect
  archetype: Technical Champion
  horizons:
    use: { hats: ["User","Integrator"], jobs: ["Automate doc builds"] }
    buy: { hats: ["Influencer","Buyer"], decision_factors: ["TCO","Support"] }
    governance: { hats: ["Governor"], concerns: ["Data sovereignty"] }
\`\`\`

This unification allows product, marketing, and compliance functions to reference the same identifier while viewing domain-specific facets.  

---

## 4. Narrative Integration  
Every horizon links to a **Job to Be Done** (Christensen et al., 2016) and to **micronarratives**—short schema-consistent stories (Schank & Abelson, 1977) that reveal hat-switching in action. Agile-style *user stories* (“As a [hat], I want [goal] so that [outcome]”) are reinterpreted as **narrative atoms** within these larger scripts. This connects cognitive empathy to measurable work items, aligning with the *promise–proof* feedback logic articulated by Friston (2010) and operationalised in the *Crankbird Brand Science Playbook* (Martin, 2025).  

---

## 5. AI-Assisted Persona Ecology  
Artificial intelligence introduces a discontinuity in traditional practice: LLMs can now **synthesise personas** from data rather than fiction. Within UPN, AI agents (e.g., Agent 13/14) perform clustering of qualitative inputs, simulate stakeholder dialogues, and detect emergent hats in meeting transcripts—activities supported but verified by human researchers (Shneiderman, 2020). This hybrid workflow treats personas as *living datasets* subject to version control and telemetry, echoing open-science principles of transparency and reproducibility (Wilkinson et al., 2016).  

---

## 6. Implications for Brand Engineering  
By embedding personas, hats, and narratives into a single semantic layer, UPN extends the *Brand Science* paradigm in which “truth manifests as legibility” (Martin, 2025). It creates continuity of empathy across horizons: the story that motivates design is the same one that justifies purchase and satisfies audit. Conceptually, UPN reframes brand development as a **cognitive supply chain**—from perception to justification to governance—measurable, automatable, and ethically accountable.  

---

## References  
Aaker, D. A. (1991). *Managing Brand Equity.* Free Press.  
Bartlett, F. C. (1932). *Remembering: A Study in Experimental and Social Psychology.* Cambridge University Press.  
Biddle, B. J. (1986). Recent developments in role theory. *Annual Review of Sociology, 12*, 67–92. <https://doi.org/10.1146/annurev.so.12.080186.000435>  
Christensen, C. M., Hall, T., Dillon, K., & Duncan, D. S. (2016). *Competing Against Luck: The Story of Innovation and Customer Choice.* Harper Business.  
Cooper, A. (1999). *The Inmates Are Running the Asylum.* Sams.  
Friston, K. (2010). The free-energy principle: A unified brain theory? *Nature Reviews Neuroscience, 11*(2), 127–138. <https://doi.org/10.1038/nrn2787>  
Homburg, C., Jozić, D., & Kuehnl, C. (2017). Customer experience management: Toward implementing an evolving marketing concept. *Journal of the Academy of Marketing Science, 45*(3), 377–401. <https://doi.org/10.1007/s11747-015-0460-7>  
Martin, R. (2025). *Crankbird Brand Science Playbook – Technical Edition v1.0.* Crankbird Press.  
Matthews, T. (2012). Designing and evaluating personas. *Communications of the ACM, 55*(3), 19–21. <https://doi.org/10.1145/2093548.2093555>  
Norman, D. A. (2013). *The Design of Everyday Things (Rev. ed.).* Basic Books.  
Schank, R. C., & Abelson, R. P. (1977). *Scripts, Plans, Goals, and Understanding.* Lawrence Erlbaum.  
Shneiderman, B. (2020). *Human-Centered AI.* Oxford University Press.  
Thaler, R. H., & Sunstein, C. R. (2008). *Nudge: Improving Decisions About Health, Wealth, and Happiness.* Yale University Press.  
Wilkinson, M. D., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data, 3*, 160018. <https://doi.org/10.1038/sdata.2016.18>  
