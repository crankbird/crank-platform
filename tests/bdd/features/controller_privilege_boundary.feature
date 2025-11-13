# language: en
@principle(Integrity) @phase(3) @issue(30) @issue(31) @component(controller) @component(security)
Feature: Controller as the only privileged component

  As an operator
  I want only the controller to hold privileged permissions while workers remain unprivileged
  So that the trust boundary is clear and enforceable

  Background:
    Given a controller with permission to register, approve, and revoke workers
    And workers with no permission to mutate controller state directly

  Scenario: CRNK-CTRL-001 — Worker cannot elevate privileges
    Given a worker attempts to call an admin-only endpoint
    When the controller authorizes the request
    Then the request is denied with HTTP 403
    And the event is included in the security audit log

  Scenario: CRNK-CTRL-002 — Controller revokes a compromised worker
    Given a worker has been marked as compromised
    When the controller revokes the worker certificate
    Then subsequent connection attempts by that worker are rejected during TLS handshake
