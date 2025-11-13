# language: en
@principle(Integrity) @principle(Legitimacy) @phase(2) @issue(29) @issue(31) @component(worker) @component(security)
Feature: Worker sandboxing and restricted execution

  As the platform
  I want workers to operate in a restricted sandbox independent of container strategy
  So that blast radius is reduced and least privilege is enforced

  Background:
    Given a shared worker runtime with a sandbox policy
      | policy_key        | value                  |
      | fs.readonly       | true                   |
      | net.egress.allow  | allowlist: controller  |
      | proc.limits       | cpu=2;mem=2Gi          |

  Scenario: CRNK-SBX-001 — Deny unauthorized egress
    Given a worker attempts to open an outbound connection to "https://random.example.com"
    When the sandbox policy is evaluated
    Then the connection is blocked
    And an audit event is recorded with the denied host

  Scenario: CRNK-SBX-002 — Enforce read-only filesystem by default
    Given a worker attempts to write to "/var/app/config.yaml"
    When the sandbox policy is evaluated
    Then the write is denied
    And the worker receives an EPERM error
