# language: en
@principle(Integrity) @principle(Legitimacy) @phase(0) @issue(27) @issue(31) @component(capability-schema) @component(controller)
Feature: Capability schema validation

  As a controller
  I want to validate worker capability manifests against a versioned schema
  So that routing is correct and auditable

  Background:
    Given a capability schema version "v0.1" with required fields:
      | field        |
      | capability   |
      | version      |
      | constraints  |
      | signature    |

  Scenario: CRNK-SCHEMA-001 — Reject invalid manifest signature
    Given a worker submits a manifest with an invalid signature
    When the controller validates the manifest
    Then the manifest is rejected
    And the worker is not activated

  Scenario: CRNK-SCHEMA-002 — Accept manifest that conforms to schema
    Given a worker submits a manifest that conforms to schema v0.1 and has a valid signature
    When the controller validates the manifest
    Then the manifest is accepted
    And the worker’s capabilities are advertised to the mesh
