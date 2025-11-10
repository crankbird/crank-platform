Feature: Document conversion via MCP (crank-doc-converter)
  As a customer agent
  I want predictable, verifiable PDF→DOCX conversion
  So that I can provide a synchronous UX with auditability

  Background:
    Given an MCP client is connected to the "crank-doc-converter" server
    And the MCP tool "convert_document" is available

  @sync @small @latency
  Scenario: Small document returns synchronously with hash and audit
    Given a 5MB PDF named "sample-5mb.pdf"
    When I invoke MCP tool "convert_document" with:
      | input_path | sample-5mb.pdf |
      | target     | docx           |
    Then the MCP result status is "ok"
    And a file artifact "sample-5mb.docx" is produced
    And the artifact includes a "sha256" field of length 64
    And the elapsed time is <= 3 seconds (p95 budget)
    And an audit event is recorded with fields:
      | request_id | tool             | status | duration_ms |
      |            | convert_document | ok     |             |

  @async @large @progress
  Scenario: Large document falls back to async with progress and callback
    Given a 50MB PDF named "sample-50mb.pdf"
    When I invoke MCP tool "convert_document" with:
      | input_path | sample-50mb.pdf |
      | target     | docx            |
    Then I receive an "accepted" response with a "job_id"
    And progress events emit at least every 2 seconds
    And a callback payload is delivered with:
      | job_id | status | artifact_path | sha256 |
    And the total elapsed time is <= 120 seconds
    And an audit event is recorded with status "ok"
