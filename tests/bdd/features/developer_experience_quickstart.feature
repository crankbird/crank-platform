# language: en
@principle(Empathy) @principle(Efficiency) @principle(Culture) @phase(4) @issue(31) @component(devx) @component(security)
Feature: Developer experience for starting and testing services

  As a developer
  I want a predictable quick start to set up env, certificates, and run tests
  So that contributing a worker is straightforward and consistent

  Background:
    Given Python 3.11+, Docker, and OpenSSL are installed
    And the developer runs the setup script

  Scenario: CRNK-DVX-001 — Editable install resolves imports
    Given the developer runs "uv pip install -e ."
    When VS Code resolves imports for the test suite
    Then the "crank.*" packages import without errors

  Scenario: CRNK-DVX-002 — Certificates initialized for local testing
    Given the developer runs "python scripts/initialize-certificates.py"
    When the controller and a sample worker start
    Then TLS handshakes succeed using the generated certificates
