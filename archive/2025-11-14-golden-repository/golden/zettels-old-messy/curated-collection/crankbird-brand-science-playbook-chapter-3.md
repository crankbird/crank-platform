---
title: "Crankbird Brand Science Playbook – Chapter 3"
author: "Ricky Martin / Crankbird"
version: "v1.0 RevA (Technical Edition)"
date: "2025-10-12"
---

# 3  Methodology and Experimental Design  

The following methodology outlines how to validate the Crankbird Brand Model through controlled, replicable experiments. Each construct—CEPs, DBAs, and Promise–Proof Loops—has measurable dependent variables that can be tested using mixed quantitative and qualitative approaches.  

---

## 3.1  Research Design Philosophy  

The framework follows the scientific principles articulated by Platt (1964) in his “strong inference” approach: generate multiple hypotheses, design critical tests, and iterate. Brand-building activities thus become a series of falsifiable experiments rather than subjective creative exercises.  

Statistically, experiments employ within-subject or between-subject designs with random assignment, analysed via mixed-effects models to account for repeated exposure and individual variance (Baayen et al., 2008).  

Dependent variables include:  
- **Recognition speed (ms)** — reaction-time measures from implicit association tests.  
- **Brand recall probability** — open-response brand recall following CEP prompts.  
- **Perceived trust (Likert 1–7)** — measured post-exposure.  
- **Behavioral engagement metrics** — conversion, retention, opt-out rates.  

---

## 3.2  CEP Validation Studies  

### Objective  
Test whether increasing the number and salience of Category Entry Points improves mental availability and purchase intent.  

### Method  
1. **Sample:** n ≥ 300 participants per experimental cell, recruited via online panels.  
2. **Design:** between-subjects; each participant exposed to one of two ad sets—control (generic messaging) vs. experimental (CEP-tied narratives).  
3. **Measures:**  
 - Unaided recall: “Which brands come to mind when you think about [cue]?”  
 - Recognition: binary yes/no brand identification.  
 - Intent: self-reported likelihood to consider the brand.  
4. **Analysis:** logistic regression predicting recall and intent from number of CEP exposures.  

### Expected Outcome  
Significant main effect of CEP exposure on recall (β > 0, p < .05).  

---

## 3.3  DBA Distinctiveness and Fluency Tests  

### Objective  
Quantify perceptual fluency and the fame/uniqueness of Distinctive Brand Assets.  

### Method  
1. **Asset recall test** — present assets (e.g., colour patch, shape, tagline) without logos; measure correct attribution rate (Romaniuk, 2018).  
2. **Recognition latency test** — measure reaction time to identify brand under visual noise conditions (Reber et al., 2004).  
3. **Processing fluency survey** — self-rated ease and likability (Graf et al., 2018).  
4. **Data analysis:** ANOVA comparing mean latency and likability across asset variants.  

### Expected Outcome  
High fluency (shorter RT) and distinctiveness (low confusion) predict stronger trust and preference ratings.  

---

## 3.4  Promise–Proof Loop Experiments  

### Objective  
Determine whether transparent feedback mechanisms increase trust and reduce uncertainty.  

### Method  
1. **Design:** within-subjects; same task completed under two UI conditions—opaque vs. transparent.  
2. **Manipulation:** display or hide visible receipts, BYOS toggles, and open pricing rules.  
3. **Measures:**  
 - Self-reported trust (Mayer, Davis, & Schoorman, 1995).  
 - Perceived integrity and benevolence subscales.  
 - Support request frequency (objective behavioral data).  
4. **Analysis:** paired t-tests and mediation models linking transparency → perceived integrity → trust.  

### Expected Outcome  
Statistically significant increase in trust and reduced support tickets in the transparent condition.  

---

## 3.5  Narrative Schema and Comprehension  

### Objective  
Test whether schema-consistent “micronarratives” yield better comprehension and retention than factual lists.  

### Method  
1. Participants read or view one of two message formats: narrative (problem → action → outcome) or factual (feature list).  
2. After a 24-hour delay, assess recall and comprehension (Graesser et al., 1997).  
3. Secondary measure: time-to-first-meaning via eye-tracking.  

### Expected Outcome  
Narrative structure leads to higher delayed recall and lower time-to-first-meaning, confirming schema congruence effects (Bartlett, 1932; Schank & Abelson, 1977).  

---

## 3.6  Autonomy and Behavioral Architecture  

### Objective  
Evaluate how user autonomy influences engagement and satisfaction.  

### Method  
1. Compare task performance between fixed-path and self-directed onboarding flows.  
2. Manipulate reversibility (undo options) and data control visibility.  
3. Measure completion, dropout, and perceived autonomy using the Self-Determination Index (Deci & Ryan, 2000).  
4. Analyze via two-way ANOVA (flow × reversibility).  

### Expected Outcome  
Higher perceived autonomy and task satisfaction in reversible, self-directed flows, even with slightly lower efficiency—supporting ethical design alignment.  

---

## 3.7  Longitudinal Brand Lift  

### Objective  
Integrate short-term activation with long-term brand equity, per Binet and Field (2013).  

### Method  
1. Run quarterly brand-lift surveys: top-of-mind awareness, association with brand values (transparency, autonomy).  
2. Track asset fame, CEP coverage, and trust metrics over time.  
3. Model longitudinal effects using linear mixed models across campaigns.  

### Expected Outcome  
Consistent increases in asset fame and CEP coverage predict parallel increases in long-term brand trust and preference.  

---

## 3.8  Data Management and Ethics  

All experiments follow open-science standards: pre-registration, anonymised data, and reproducible analysis scripts (Wilkinson et al., 2016). Data are stored in open formats (CSV, JSON, YAML) to allow external audit and alignment with Crankbird’s transparency ethos.  

---

## References  

- Baayen, R. H., Davidson, D. J., & Bates, D. M. (2008). Mixed-effects modeling with crossed random effects for subjects and items. *Journal of Memory and Language, 59*(4), 390–412. https://doi.org/10.1016/j.jml.2007.12.005  
- Bartlett, F. C. (1932). *Remembering: A Study in Experimental and Social Psychology.* Cambridge University Press.  
- Binet, L., & Field, P. (2013). *The Long and the Short of It: Balancing Short and Long-Term Marketing Strategies.* IPA (Institute of Practitioners in Advertising).  
- Deci, E. L., & Ryan, R. M. (2000). The “what” and “why” of goal pursuits: Human needs and the self-determination of behavior. *Psychological Inquiry, 11*(4), 227–268. https://doi.org/10.1207/S15327965PLI1104_01  
- Graf, L. K. M., Mayer, S., & Landwehr, J. R. (2018). A dual-process perspective on fluency-based aesthetics: Hedonic and amplification effects of processing fluency. *Journal of Experimental Social Psychology, 75,* 202–216. https://doi.org/10.1016/j.jesp.2017.11.009  
- Graesser, A. C., Millis, K. K., & Zwaan, R. A. (1997). Discourse comprehension. *Annual Review of Psychology, 48,* 163–189. https://doi.org/10.1146/annurev.psych.48.1.163  
- Hohwy, J. (2013). *The Predictive Mind.* Oxford University Press.  
- Mayer, R. C., Davis, J. H., & Schoorman, F. D. (1995). An integrative model of organizational trust. *Academy of Management Review, 20*(3), 709–734. https://doi.org/10.5465/amr.1995.9508080335  
- Platt, J. R. (1964). Strong inference. *Science, 146*(3642), 347–353. https://doi.org/10.1126/science.146.3642.347  
- Reber, R., Schwarz, N., & Winkielman, P. (2004). Processing fluency and aesthetic pleasure: Is beauty in the perceiver’s processing experience? *Personality and Social Psychology Review, 8*(4), 364–382. https://doi.org/10.1207/s15327957pspr0804_3  
- Romaniuk, J. (2018). *Building Distinctive Brand Assets.* Oxford University Press.  
- Schank, R. C., & Abelson, R. P. (1977). *Scripts, Plans, Goals, and Understanding: An Inquiry into Human Knowledge Structures.* Lawrence Erlbaum.  
- Wilkinson, M. D., et al. (2016). The FAIR Guiding Principles for scientific data management and stewardship. *Scientific Data, 3,* 160018. https://doi.org/10.1038/sdata.2016.18  

---

*(end of Chapter 3 – next: Application to Crankbird Automation)*
