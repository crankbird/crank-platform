# language: en
@principle(Efficiency) @principle(Culture) @principle(Resilience) @phase(4) @issue(31) @component(controller) @component(worker) @component(mesh)
Feature: Post-refactor deployment models

  As a platform operator
  I want standard deployment models validated by acceptance criteria
  So that we can run across diverse environments reliably

  Scenario Outline: CRNK-DEP-001 — Containerized deployment (Windows/Linux/Cloud)
    Given a node with Docker and the controller+worker containers
    When the stack starts
    Then the controller is reachable over mTLS
    And workers register and advertise capabilities
    And a sample job "<capability>" runs to completion

    Examples:
      | capability         |
      | document.convert   |
      | image.classify     |

  Scenario: CRNK-DEP-002 — Hybrid macOS deployment (GPU native, CPU in containers)
    Given a macOS node with Metal-capable GPU
    And GPU workers run natively while CPU workers run in containers
    When a GPU job "image.classify" is submitted
    Then the job is executed by a native GPU worker
    And results are returned via the controller over mTLS

  Scenario: CRNK-DEP-003 — Embedded deployment (iOS/Android libraries)
    Given a mobile application embedding controller+worker libraries
    When the app launches the local controller
    Then a sandboxed worker can process a local job without external network access
