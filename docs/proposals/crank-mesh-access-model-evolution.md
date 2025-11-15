# Proposal: Evolution of Access Models in Crank-Mesh (RBAC → ABAC → Capabilities)

## Context / Purpose
This proposal is intentionally *not* a plan or set of issues.  
It is a conceptual foundation for future work — something an agent can absorb and turn into an actionable architecture roadmap when needed.

Crank-Mesh is evolving into a distributed, sovereign, zero-trust system. As part of that evolution, it makes sense to examine how traditional access models (RBAC, ABAC) give way to capability-based models that better fit distributed machine-to-machine architectures.

This document frames that evolution and outlines the direction Crank-Mesh should take.

---

## 1. Background: RBAC → ABAC
Historically:

- **RBAC** ties permissions to *roles*  
- **ABAC** ties permissions to *attributes*  
- Both assume a centralized policy enforcement model  
- Both rely on out-of-band permission lookups and human-oriented semantics

These models break down in:

- distributed systems  
- multi-node meshes  
- offline or edge computing  
- machine-to-machine interactions  
- dynamic capability discovery  
- cross-domain contexts  
- environments requiring sovereignty and portability

Crank-Mesh already operates in a space where RBAC/ABAC are insufficient.

---

## 2. Capability-Based Security (CBS)
The next natural model is **capability-based security**, where:

- authority is conveyed by *holding* a capability  
- a capability is an unforgeable token (certificate, JWT, handle)  
- capabilities express *what can be done* rather than *who you are*  
- no global ACLs or roles are needed for enforcement  
- the system becomes naturally least-privilege  
- delegation becomes explicit and controlled  
- distributed systems can make local decisions with no central lookup

Crank-Mesh already contains most primitives needed for CBS:

- Workers advertise “capabilities”  
- Controller performs capability-based routing  
- Cert-server issues short-lived identities  
- All trust is cryptographic and zero-trust  
- No ambient authority exists between components

This positions the platform to adopt a true capability model with minimal architectural change.

---

## 3. SPIFFE Identity Alignment
SPIFFE provides a clean, portable identity model for workloads:

- `spiffe://trust-domain/worker/<id>`  
- Identity appears in X.509 SAN  
- Short-lived certs  
- Trust bundles  
- No dependency on SPIRE’s runtime

By aligning Crank-Mesh with SPIFFE at the identity layer, we gain:

- industry-recognized identity semantics  
- tooling compatibility  
- credibility with security reviewers  
- standardized trust primitives  
- a strong base for capability tokens  

The cert-server remains sovereign and lightweight.

---

## 4. Capabilities as First-Class Concepts
Capabilities in Crank-Mesh should evolve from “metadata workers expose” into **first-class authorization objects**.

A capability token could be:

- an mTLS certificate  
- a short-lived JWT signed by our CA  
- a small object with embedded restrictions  
- delegatable under controlled conditions  
- revocable via short TTL or trust-bundle update  

This future model:

- avoids role/attribute complexity  
- scales across nodes and clouds  
- supports edge and offline operation  
- aligns with Zero Trust and object-capability thinking  
- positions Crank-Mesh as a foundation for the machine-to-machine economy

---

## 5. Object-Capability Trajectory (Future)
Long-term, Crank-Mesh may naturally fit an **OCap** model:

- capabilities are objects  
- invocation is explicit  
- no ambient network authority  
- meshes become secure-by-default  
- each worker acts as a capability-bearing actor  

This is a direction, not a near-term requirement.  
The core idea is simply: **keep the architecture compatible with OCap evolution.**

---

## 6. Why This Matters / Intended Use
This proposal clarifies:

- why RBAC and ABAC are not end states  
- what Crank-Mesh should evolve *toward*  
- how our identity plane (SPIFFE-aligned) supports that  
- how cert-server + controller naturally model capabilities  
- why capability-based access is the right match for distributed agents  

It is NOT:

- a plan  
- a sprint breakdown  
- a set of implementation tasks  

It *is* a framing document for agents (and future me) to derive:

- roadmap items  
- architecture updates  
- cert server improvements  
- controller design enhancements  
- security milestones  
- mesh evolution work  

Agents given this context should be able to produce:

- actionable implementation plans  
- GitHub issues  
- incremental designs  
- or formal architecture docs on request

---

## 7. Next Steps (For future planning, not this proposal)

- Capability token design (JWT or cert-derived)  
- Lightweight delegation model  
- Trust bundle expansion  
- Capability registry formalization  
- Enforcing capability-based authorization in the controller  
- Mapping capabilities to identity (SPIFFE IDs)  
- Optional OCap integration patterns  

These are **not** part of this proposal; they are simply the areas this direction eventually unlocks.

---

## End Note
This proposal is deliberately compact and conceptual.  
It is meant to **inform** later planning, not dictate it.

Place it in `/proposals/` as contextual guidance for future issue generation and architectural thinking.
