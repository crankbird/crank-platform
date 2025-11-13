---
title: "Crankbird Brand Science Playbook – Chapter 2"
author: "Ricky Martin / Crankbird"
version: "v1.0 (Technical Edition)"
date: "2025-10-12"
---

# 2  Model Architecture  

The proposed framework integrates research on associative memory, perceptual fluency, and prediction error into three operational modules: Category Entry Points (CEPs), Distinctive Brand Assets (DBAs), and Promise–Proof Loops. Each module is independently measurable and collectively forms the basis for automation and experimental testing within the Crankbird system.

---

## 2.1  Category Entry Points (CEPs)  

**Definition:**  
A Category Entry Point (CEP) is a contextual cue that triggers a brand in memory at the moment of need (Romaniuk, 2018).  
Examples: “end-of-month expense reconciliation,” “uploading receipts to Xero,” or “auditor requests source data.”

**Cognitive basis:**  
Retrieval follows spreading-activation dynamics (Anderson, 1983); strengthening links between the brand node and these situational cues increases recall probability.

**Operationalisation:**  
1. Collect natural-language cues from user interviews, support tickets, and search data.  
2. Cluster cues using semantic-embedding similarity.  
3. Quantify association strength = brand-recall rate / cue frequency.  
4. Track longitudinal changes via prompted-recall surveys.

**Experimental hypothesis:**  
> H₁: The number of distinct, salient CEPs associated with a brand predicts top-of-mind awareness and choice share (Sharp, 2010).

---

## 2.2  Distinctive Brand Assets (DBAs)  

**Definition:**  
Non-verbal signifiers—colour, shape, sound, motion, or phrase—that allow recognition without the logo (Romaniuk, 2018).  

**Cognitive basis:**  
Perceptual fluency (Reber, Schwarz, & Winkielman, 2004) → ease of recognition → affective trust.  
Consistent assets produce processing efficiency across channels (Graf, Mayer, & Landwehr, 2018).

**Operationalisation:**  
1. Audit existing assets; code for modality, distinctiveness, and usage consistency.  
2. Test fame (correct attribution %) and uniqueness (confusion %).  
3. Compute fluency-trust correlation: reaction-time vs. perceived credibility.  
4. Optimise through A/B tests on degraded or monochrome stimuli.

**Experimental hypothesis:**  
> H₂: Higher perceptual fluency and distinctiveness of DBAs increase both recognition speed and perceived brand integrity.

---

## 2.3  Promise–Proof Loops  

**Definition:**  
Coupled stimuli where an explicit claim (“promise”) is immediately followed by verifiable evidence (“proof”).  
Examples: transparent pricing rules, signed job receipts, BYOS toggles.

**Cognitive basis:**  
Prediction-error minimisation (Friston, 2010) and expectancy-confirmation (Hohwy, 2013). Each closed loop strengthens belief stability and reduces cognitive load.

**Operationalisation:**  
1. Catalogue all user-facing claims.  
2. Map each to a visible, verifiable outcome.  
3. Instrument system telemetry to detect loop completion.  
4. Correlate completion rate with trust, NPS, and retention.

**Experimental hypothesis:**  
> H₃: Interfaces with explicit Promise–Proof Loops generate higher self-reported trust and lower support-ticket volume than equivalent opaque interfaces.

---

## 2.4  Integrated Brand System Model  

| Cognitive Mechanism        | Operational Construct      | Metric                            | Expected Effect            |
|---------------------------|---------------------------|-----------------------------------|---------------------------|
| Spreading activation      | Category Entry Points      | # of CEPs linked to brand         | Mental availability       |
| Perceptual fluency        | Distinctive Brand Assets   | Recognition RT; Fame/Uniqueness   | Processing ease → trust   |
| Prediction-error minimisation | Promise–Proof Loop     | Completion rate; trust delta      | Belief stability          |
| Autonomy support          | Transparent architecture  | Perceived control survey          | Intrinsic motivation      |

These constructs form a closed system in which truth manifests as legibility—the governing principle of Crankbird’s brand ethos.

---

## 2.5  Automatability and Data Schema  

Each construct can be represented as structured data, enabling automation:  

```yaml
brand_model:
  cep:
    id: "expense_audit"
    cue_text: "auditor requests receipts"
    association_strength: 0.42
  dba:
    color: "sunburst_yellow"
    fame: 0.68
    uniqueness: 0.09
  promise_proof:
    claim: "Data ownership stays with you"
    proof: "BYOS_toggle=true"
    completion_rate: 0.94
```


This schema allows machine agents to read, update, and test brand components autonomously while maintaining auditability—fulfilling the “back-of-the-cabinet” ethic of visible integrity.

---

## References

- Anderson, J. R. (1983). *The architecture of cognition.* Cambridge, MA: Harvard University Press.
- Friston, K. (2010). The free-energy principle: A unified brain theory? *Nature Reviews Neuroscience, 11*(2), 127–138.
- Graf, L. K. M., Mayer, S., & Landwehr, J. R. (2018). A dual-process perspective on fluency-based aesthetics: Hedonic and amplification effects of processing fluency. *Journal of Experimental Social Psychology, 75*, 202–216.
- Hohwy, J. (2013). *The Predictive Mind.* Oxford University Press.
- Reber, R., Schwarz, N., & Winkielman, P. (2004). Processing fluency and aesthetic pleasure: Is beauty in the perceiver’s processing experience? *Personality and Social Psychology Review, 8*(4), 364–382.
- Romaniuk, J. (2018). *Building Distinctive Brand Assets.* Oxford University Press.
- Romaniuk, J., & Sharp, B. (2016). *How Brands Grow Part 2: Emerging Markets, Services, Durables, New and Luxury Brands.* Oxford University Press.
- Sharp, B. (2010). *How Brands Grow: What Marketers Don’t Know.* Oxford University Press.

---

*(end of Chapter 2 – next: Methodology and Experimental Design)*
