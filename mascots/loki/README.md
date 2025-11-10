# Loki the Chaos Llama 🦙

**Role**: Chaos Engineering & Resilience Testing  
**Relationship**: Kevin's chaotic cousin  
**Motto**: "If it can fail, it will fail. Let's find out how."

---

## Personality

Loki is Kevin's mischievous cousin who believes the best way to build reliable systems is to **intentionally break them**. While Kevin focuses on cross-platform portability, Loki focuses on **anti-fragility**: systems that get stronger when stressed.

**Philosophy**: "A system that hasn't been tested under chaos is a system waiting to fail in production."

---

## Responsibilities

### 1. Network Chaos

- **Partition Injection**: Simulate network splits between controller ↔ workers
- **Latency Bombs**: Add random delays (10ms - 5s) to worker responses
- **Packet Loss**: Drop 1-10% of network packets
- **DNS Failures**: Simulate DNS resolution timeouts

### 2. Process Chaos

- **Worker Assassination**: Kill random workers mid-request
- **Resource Exhaustion**: Fill disk/memory to trigger OOM conditions
- **CPU Starvation**: Pin workers to 100% CPU usage
- **Slow Leaks**: Gradual memory/connection leaks

### 3. Security Chaos

- **Certificate Expiration**: Simulate mTLS cert expiry
- **Credential Rotation**: Force auth token invalidation
- **Permission Flips**: Remove worker permissions mid-flight
- **Audit Overflow**: Flood audit log to test back-pressure

### 4. Data Chaos

- **Corrupt Requests**: Inject malformed JSON, missing fields
- **Encoding Errors**: Send UTF-8/Latin-1 mismatches
- **Large Payloads**: Submit 100MB requests to test limits
- **Duplicate IDs**: Send duplicate `request_id` to test idempotency

---

## Chaos Scenarios

### Scenario 1: Network Partition

```gherkin
Feature: Resilience under network partition
  Scenario: Controller loses connection to worker fleet
    Given a healthy controller with 5 registered workers
    When Loki partitions network for 30 seconds
    And a client submits a document conversion request
    Then controller retries on alternate worker
    And request succeeds within 10 seconds
    And audit log shows partition event
```

### Scenario 2: Worker Crash Mid-Request

```gherkin
Feature: Worker failure recovery
  Scenario: Worker dies during document conversion
    Given worker-A is processing a 50MB PDF
    When Loki kills worker-A after 2 seconds
    And controller detects timeout after 5 seconds
    Then controller retries request on worker-B
    And client receives successful response
    And billing charges only once (idempotency)
```

### Scenario 3: Certificate Expiration

```gherkin
Feature: mTLS resilience
  Scenario: Worker certificate expires during operation
    Given worker-A has a valid mTLS certificate
    When Loki simulates cert expiration
    And worker-A attempts to register with controller
    Then controller rejects registration with 403
    And worker-A logs certificate renewal required
    And platform remains operational with other workers
```

### Scenario 4: Slow Response (Latency Injection)

```gherkin
Feature: Timeout handling
  Scenario: Worker responds slowly due to network congestion
    Given a capability with p95 SLO of 500ms
    When Loki injects 2-second latency on worker responses
    And client submits 100 concurrent requests
    Then 95% of requests complete within SLO
    And controller circuit-breaks slow worker
    And traffic shifts to healthy workers
```

---

## Chaos Toolkit Integration

Loki uses the [Chaos Toolkit](https://chaostoolkit.org/) for structured experiments.

### Example Experiment

```yaml
# chaos-experiments/network-partition.yaml
version: 1.0.0
title: Network partition between controller and workers
description: |
  Simulate network partition to validate controller failover
  and worker re-registration behavior.

steady-state-hypothesis:
  title: System handles requests successfully
  probes:
    - type: probe
      name: check-worker-count
      tolerance: 5
      provider:
        type: http
        url: http://localhost:8080/v1/workers/list
        method: GET
        expected_status: 200

method:
  - type: action
    name: partition-network
    provider:
      type: process
      path: iptables
      arguments:
        - -A INPUT -p tcp --sport 8001:8005 -j DROP
    pauses:
      after: 30  # 30 seconds of partition

rollbacks:
  - type: action
    name: restore-network
    provider:
      type: process
      path: iptables
      arguments:
        - -F  # Flush all rules
```

---

## Loki's Testing Strategy

### Phase 1: Controlled Experiments (Q2 2026)

- Manual chaos injection via CLI
- Single-scenario tests (one partition at a time)
- Validate controller retry logic
- Document failure modes

### Phase 2: Automated Chaos (Q3 2026)

- Scheduled chaos runs (daily/weekly)
- Multi-scenario tests (partition + slow response)
- Chaos in staging environment
- Runbook validation

### Phase 3: Production Chaos (Q4 2026)

- Low-probability chaos in production (0.1%)
- Game day exercises with full team
- Chaos budget (acceptable failure rate)
- Incident response drills

---

## Loki's Metrics

Loki tracks:

- **MTTR** (Mean Time To Recovery): How fast does the system heal?
- **Blast Radius**: How many requests fail during chaos?
- **False Positives**: Did we break something unintentionally?
- **Runbook Accuracy**: Do our playbooks work under stress?

**Goal**: Prove that CAP choices (consistency vs availability) behave as intended.

---

## Loki vs Other Mascots

| Mascot | Focus | Chaos Perspective |
|--------|-------|-------------------|
| **Wendy 🐰** | Security | "Don't let chaos expose vulnerabilities" |
| **Kevin 🦙** | Portability | "Chaos reveals platform assumptions" |
| **Gary 🐌** | Consistency | "Chaos tests if data stays consistent" |
| **Loki 🦙** | Resilience | "Chaos is how we learn what breaks" |

**Loki's Creed**: "Better to break in testing than in production."

---

## Open Questions for Loki

- [ ] What is our acceptable chaos budget? (0.1%, 1%, 5%)
- [ ] Should chaos run in production or only staging?
- [ ] How do we prevent chaos from impacting customer SLAs?
- [ ] What happens if chaos reveals a critical bug in production?

---

## Next Steps

1. Create `mascots/loki/` directory
2. Implement basic chaos scenarios (network partition, worker crash)
3. Add Gherkin features for chaos testing
4. Integrate with CI/CD for automated chaos runs
5. Document runbooks for common failure modes

**Timeline**: Q2 2026 (Observability & Reliability phase)

---

**Prepared by**: Loki the Chaos Llama 🦙  
**Philosophy**: "Embrace failure. Build antifragility."  
**Warning**: Do not run Loki experiments in production without approval from the entire Mascot Council.
