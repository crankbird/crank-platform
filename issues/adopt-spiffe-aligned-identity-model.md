## **Title:**  
Adopt SPIFFE-Aligned Identity Model for Crank-Mesh (Without SPIRE Dependency)

---

## **Summary:**  
Crank-Platform already implements a private PKI and trust fabric for the crank-mesh vision. To increase interoperability, security assurance, and long-term credibility, we should evolve the identity model to be **SPIFFE-aligned** at the certificate and naming level—without adopting SPIRE’s runtime, agents, or operational complexity.

This issue outlines the design, goals, and incremental steps required.

---

## **Motivation:**  
We want Crank-Platform to:

- Follow Zero-Trust and Security-by-Design principles  
- Maintain a **sovereign, cloud-neutral identity plane**  
- Be compatible with standard zero-trust workloads  
- Support external validation using existing SPIFFE tooling  
- Reduce friction with security architects and auditors  
- Future-proof the system for cross-mesh federation  

SPIFFE provides the right **identity format** and **X.509 profile**.  
SPIRE (runtime) is intentionally *not* adopted.

---

## **Scope of This Issue:**  
Implement SPIFFE-compatible **identity semantics**, including:

### **1. SPIFFE ID Format**
Define a URI structure for crank identities, e.g.: