# language: en
@principle(Integrity) @principle(Legitimacy) @principle(Resilience) @phase(4) @issue(31) @component(security) @component(controller) @component(worker)
Feature: Trust fabric and mutual TLS

  As a controller or worker
  I want all service-to-service traffic to use HTTPS with mutual TLS (mTLS)
  So that identities are verified and the trust boundary is enforced

  Background:
    Given a platform PKI with a root CA and intermediate CAs
    And a controller certificate signed by the platform CA
    And a worker certificate signed by the platform CA

  Scenario: CRNK-SEC-001 — Controller rejects worker without valid client certificate
    Given a worker attempts to register without presenting a client certificate
    When the controller verifies the TLS handshake
    Then the TLS connection is terminated
    And the registration is not persisted

  Scenario: CRNK-SEC-002 — Worker rejects controller without valid server certificate
    Given a controller presents an invalid or untrusted server certificate
    When the worker initiates a TLS session
    Then the worker aborts the connection
    And logs an authentication failure with reason "untrusted-certificate"

  Scenario: CRNK-SEC-003 — Certificate rotation without downtime (anti-fragile mTLS)
    Given the controller and workers have certificates expiring within 24 hours
    When new certificates are provisioned and hot-reloaded
    Then existing connections continue until completion
    And new connections use the rotated certificates
