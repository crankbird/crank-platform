# language: en
@principle(Efficiency) @principle(Resilience) @phase(3) @issue(30) @issue(31) @component(mesh) @component(controller)
Feature: Mesh coordinates state, not execution

  As a controller
  I want the mesh to share capability/health/load state while keeping work local by default
  So that network overhead is minimized and locality is preserved

  Background:
    Given a cluster with three controllers A, B, and C
    And each controller periodically exchanges state snapshots

  Scenario: CRNK-MESH-001 — Prefer local execution
    Given controller A receives a job for "document.convert"
    And worker W on node A advertises "document.convert" and is healthy
    When the controller selects a worker
    Then controller A assigns the job to worker W (local execution)

  Scenario: CRNK-MESH-002 — Route to remote only when explicitly allowed
    Given controller A receives a job with route=any
    And no local workers satisfy the capability
    When the controller selects a worker
    Then the job may be routed to a remote controller’s worker
    And the decision is recorded with reason "no-local-satisfier"
