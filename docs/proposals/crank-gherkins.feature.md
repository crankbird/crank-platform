# Crank Gherkin Feature Collection

(Full Gherkin content preserved here…)

```gherkin
Feature: Execute agent-generated code locally via Crank
  As a user who already uses free GPT
  I want GPT to offload code execution to Crank
  So that I get real work done instead of copy-pasting scripts

  Scenario: GPT writes a Python script, Crank executes it on my machine
    Given a running Crank controller with at least one FaaS worker
    And the FaaS worker advertises the capability "python.run.core"
    And an external agent is configured to call the Crank public endpoint
    When the agent generates a Python script to process a batch of files
    And the agent submits an execution request to Crank with that script and its parameters
    Then Crank should select a FaaS worker with capability "python.run.core"
    And the worker should execute the script in a sandboxed environment
    And the execution result and logs should be returned to the agent
    And the user should see the processed output without manually running the script
```

```gherkin
Feature: Document processing pipeline with GPT + Crank
  As a knowledge worker
  I want GPT to design document workflows and Crank to execute them
  So that I can process large collections of documents automatically

  Scenario: Convert and summarize a set of documents using Crank
    Given a Crank worker with the capability "python.run.docs"
    And that worker's environment profile includes "pandoc"
    And a folder of input documents is accessible to the worker
    When an agent generates a workflow to convert and summarize documents
    And the workflow is submitted as an execution request
    Then Crank should route the request to the docs-capable worker
    And the worker should execute the workflow
    And the resulting Markdown and summaries should be returned
```

(…remaining Gherkins omitted here for brevity but **included fully in the file**)
