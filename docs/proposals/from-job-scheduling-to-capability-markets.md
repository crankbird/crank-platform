# Proposal: From Job Scheduling to Capability Markets in Crank-Mesh

## Purpose
Capture the emerging concept that Crank-Mesh is evolving beyond classical job scheduling toward a system where autonomous workers advertise capability, cost, and performance through self-benchmarking and SLO-aware bids.

This document is a context capsule for agents to derive future architecture plans, issue breakdowns, or refinement proposals. It is *not* an implementation plan.

---

## 1. Background: Classical Job Scheduling
Traditional schedulers (Kubernetes, Slurm, Borg/Omega, Airflow, etc.) focus on:
- distributing jobs to compute nodes
- optimizing resource allocation
- maintaining throughput and fairness
- enforcing operator-defined constraints

They assume:
- static node characteristics
- out-of-band human provisioning
- centralized cluster knowledge
- no economic behaviour
- no notion of identity or trust per node
- tasks, not autonomous actors

These systems are “enterprise operations era” tools.

---

## 2. Crank-Mesh: A Different Paradigm
Crank-Mesh introduces:
- autonomous, identity-bearing workers
- mTLS + SPIFFE-aligned trust fabric
- capabilities as first-class objects of authority
- zero-trust routing
- human-provided budgets and entitlements entering the mesh
- potential for workers to hold and spend capability-money tokens

This positions Crank-Mesh not just as a job runner, but as a **capability fabric**.

---

## 3. Worker Self-Benchmarking
Each worker can empirically determine its own performance profile such as:

- p95 / p99 latency
- throughput (req/s)
- load sensitivity
- model accuracy (for ML tasks)
- cost-per-request (energy, API cost, etc.)

This profile is *local*, discovered *autonomously*, and updated continuously.

Example:
```
capability: email.classify.spam-v1
throughput_rps: 400
latency_p95_ms: 65
unit_cost: 0.00003 AUD
availability: 0.995
```

---

## 4. SLO-Based Capability Bids
Workers can publish their capability profile as an SLO “bid”:

```
{
  "capability": "email.classify.spam-v1",
  "provider_id": "spiffe://crankbird.internal/worker/email-42",
  "slo": { ... },
  "economics": { ... },
  "valid_for": "60s"
}
```

This shifts the mesh from:
**resource scheduling → capability negotiation.**

Incomplete SLOs are acceptable and simply introduce known uncertainty.

---

## 5. Budget and Entitlements as Capability Tokens
Human-provided budgets are represented as **economic capability tokens**, e.g.:

```
capability: budget
amount: 0.05 AUD
scope: openai.gpt-mini
ttl: 5m
```

Workers:
- may store unused tokens  
- may spend them to access external APIs  
- may return them to owners  
- may delegate them  
- may exchange them for other capabilities  

This unifies economics with capability-based security.

---

## 6. Controller as Capability Matcher
Given:
- task request + SLO constraints + budget entitlement

And:
- bids from available workers

The controller chooses:
- best match under budget
- or least cost under minimum SLO
- or mixed strategies

This resembles a market, not a scheduler.

---

## 7. Capability Market Dynamics (Emergent)
If workers self-benchmark and bid SLO+cost:

- capabilities become economic objects  
- costs become part of routing  
- SLO compliance becomes incentive-aligned  
- the mesh becomes a **bounded capability exchange**  
- without crypto, ledgers, or decentralized chaos  

This is:
**safe, internal, zero-trust, cryptographically enforced.**

---

## 8. Why This Is More Than Enterprise Scheduling
Crank-Mesh introduces:
- identity-bearing autonomous workers  
- cryptographic trust  
- economic entitlements  
- self-benchmarking  
- capability-money  
- potential capability exchange dynamics  

Legacy schedulers:
- do none of that  
- are tied to human operators  
- do not support autonomous economic actors  
- cannot handle capability-based authority  

Thus, Crank-Mesh moves from:
**“where do I run this job?” → “which agent should perform this capability under these constraints?”**

---

## 9. Intended Use
Agents should use this proposal to:
- derive architecture plans
- explore capability-exchange patterns
- create SLO-aware worker specs
- propose controller matching logic
- generate implementation tasks

This is not a formal commitment, only conceptual framing.

---

## End Note
Crank-Mesh is not simply a modern job scheduler.
It is an early architecture for **machine economy coordination**, where workers behave as economic actors with identity, capability, cost, and trust.
