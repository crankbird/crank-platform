# language: en
# feature_id: F-CAPABILITY-ROUTING
# adr_refs: [0001, 0006, 0023]
# personas: [zk20251112-002_upn-systems-architect]
# proposals: [P-2025-11-faas-worker-spec]
# strategic_context: Situated intelligence - compute where meaning lives (local-first routing)

@principle(Integrity) @principle(Efficiency) @phase(1) @issue(28) @issue(31) @component(controller) @component(worker) @component(capability-schema)
Feature: Capability-driven routing

  As a controller
  I want to use declared capabilities as the source of truth for routing
  So that jobs are sent to workers that can actually perform them

  Background:
    Given a worker with a signed capability manifest
      | capability       | version | constraints         |
      | image.classify   | 1.2.0   | gpu=true, arch=x64  |
      | document.convert | 0.9.1   | cpu=true            |
    And the worker is registered and healthy

  Scenario: CRNK-ROUTE-001 — Route by exact capability key
    Given a job with capability "image.classify" and requires gpu=true
    When the controller selects a worker
    Then the job is routed to the worker advertising "image.classify" with gpu=true

  Scenario: CRNK-ROUTE-002 — Reject when capability not advertised
    Given a job with capability "certificate.sign"
    When the controller selects a worker
    Then no worker is selected
    And the job is marked "unsatisfied-capability"
