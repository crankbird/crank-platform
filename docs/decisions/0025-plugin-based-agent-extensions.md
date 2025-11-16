# ADR-0025: Plugin-Based Extension Model for Agent13/Agent14

**Status**: Proposed
**Date**: 2025-11-16
**Deciders**: Platform Team, Agent Development Team
**Technical Story**: [ADR Backlog 2025-11-16 – Platform Services / Extensions](../planning/adr-backlog-2025-11-16.md#platform-services--extensions)

## Context and Problem Statement

Agent13 (Codex) and Agent14 (Sonnet) are AI assistants that evolve new capabilities over time. Hard-coding capabilities into agent codebases creates coupling and deployment friction. How should agents discover and load new capabilities?

## Decision Drivers

- Extensibility: Add capabilities without agent redeployment
- Isolation: Plugin failures don't crash agent
- Discovery: Agents find available plugins
- Versioning: Plugins evolve independently
- Local-first: Works offline
- Git-friendly: Plugins versioned with code

## Considered Options

- **Option 1**: Plugin-based extensions with manifest files - Proposed
- **Option 2**: Monolithic agent with all capabilities built-in
- **Option 3**: Microservices with agent orchestration

## Decision Outcome

**Chosen option**: "Plugin-based extensions with manifest files", because it provides extensibility without coupling while maintaining local-first operation and Git compatibility. Plugins are Python modules with YAML manifests describing capabilities.

### Positive Consequences

- Add capabilities without agent changes
- Plugin isolation (failures contained)
- Version plugins independently
- Git-based plugin distribution
- Local development friendly
- Automatic capability discovery

### Negative Consequences

- Plugin API surface to maintain
- Version compatibility challenges
- Debugging across plugin boundaries
- Security review for plugins

## Pros and Cons of the Options

### Option 1: Plugin-Based Extensions with Manifest Files

Plugins are Python modules + YAML manifests loaded at runtime.

**Pros:**
- Extensible
- Isolated
- Git-versioned
- Local-first
- Independent evolution
- Auto-discovery

**Cons:**
- API maintenance
- Version compatibility
- Debugging complexity
- Security concerns

### Option 2: Monolithic Agent with Built-In Capabilities

All capabilities in agent codebase.

**Pros:**
- Simple deployment
- Single version
- Easy debugging
- No plugin overhead

**Cons:**
- Tight coupling
- Redeploy for new capabilities
- Large codebase
- Hard to test capabilities independently

### Option 3: Microservices with Agent Orchestration

Each capability is a separate service.

**Pros:**
- Full isolation
- Independent scaling
- Language diversity

**Cons:**
- Network overhead
- Complex deployment
- Service discovery needed
- Not local-first

## Links

- [Related to] ADR-0004 (Local-first execution)
- [Related to] ADR-0006 (Verb/capability registry)
- [Related to] ADR-0023 (Capability publishing protocol)
- [Related to] Agent13/Agent14 repositories
- [Related to] Worker plugin architecture

## Implementation Notes

**Plugin Architecture**:

```
~/.crank/
  agents/
    agent13/
      plugins/
        email-analyzer/
          plugin.yaml       # Manifest
          __init__.py       # Plugin entry point
          analyzer.py       # Implementation
        document-qa/
          plugin.yaml
          __init__.py
          qa_engine.py
    agent14/
      plugins/
        code-reviewer/
          plugin.yaml
          __init__.py
          reviewer.py
```

**Plugin Manifest** (`plugin.yaml`):

```yaml
# ~/.crank/agents/agent13/plugins/email-analyzer/plugin.yaml
name: email-analyzer
version: 1.2.0
description: "Analyze email content for sentiment, urgency, and categorization"
author: Platform Team
license: Proprietary

# Agent compatibility
compatible_agents:
  - agent13-codex
  - agent14-sonnet

# Capabilities provided
capabilities:
  - name: analyze_email
    verb: analyze
    input_schema:
      type: object
      properties:
        email_text:
          type: string
        headers:
          type: object
    output_schema:
      type: object
      properties:
        sentiment:
          type: string
          enum: [positive, neutral, negative]
        urgency:
          type: string
          enum: [low, medium, high, critical]
        category:
          type: string

# Dependencies
dependencies:
  python:
    - transformers>=4.30.0
    - torch>=2.0.0
  workers:
    - crank_email_classifier  # Requires this worker

# Configuration
config:
  model_path: ~/.crank/models/email-sentiment
  max_email_length: 10000
  confidence_threshold: 0.7

# Lifecycle hooks
hooks:
  on_load: initialize_model
  on_unload: cleanup_resources
```

**Plugin Entry Point** (`__init__.py`):

```python
# ~/.crank/agents/agent13/plugins/email-analyzer/__init__.py
from typing import Any
from crank.plugin_api import Plugin, PluginContext

class EmailAnalyzerPlugin(Plugin):
    """Email analysis plugin for Agent13."""

    def __init__(self, context: PluginContext):
        self.context = context
        self.model = None

    async def initialize_model(self):
        """Hook: Load model on plugin load."""
        model_path = self.context.config["model_path"]
        # Load transformers model
        from transformers import pipeline
        self.model = pipeline("sentiment-analysis", model=model_path)

    async def cleanup_resources(self):
        """Hook: Cleanup on plugin unload."""
        if self.model:
            del self.model

    async def analyze_email(
        self,
        email_text: str,
        headers: dict[str, str]
    ) -> dict[str, Any]:
        """Capability: analyze_email"""
        # Use local model
        sentiment_result = self.model(email_text[:1000])[0]

        # Call worker for classification
        classification = await self.context.call_worker(
            worker="crank_email_classifier",
            capability="classify_email",
            input={"text": email_text}
        )

        return {
            "sentiment": sentiment_result["label"].lower(),
            "urgency": self._determine_urgency(headers, email_text),
            "category": classification["category"],
            "confidence": sentiment_result["score"]
        }

    def _determine_urgency(self, headers: dict, text: str) -> str:
        # Urgency logic
        if "urgent" in text.lower() or headers.get("Priority") == "high":
            return "high"
        return "medium"

# Export plugin
def create_plugin(context: PluginContext) -> Plugin:
    return EmailAnalyzerPlugin(context)
```

**Plugin API** (`src/crank/plugin_api.py`):

```python
# Base classes for plugin development
from abc import ABC, abstractmethod
from typing import Any, Callable
from pydantic import BaseModel

class PluginContext:
    """Context provided to plugins by agent runtime."""

    def __init__(self, agent_id: str, config: dict, worker_client: Any):
        self.agent_id = agent_id
        self.config = config
        self._worker_client = worker_client

    async def call_worker(
        self,
        worker: str,
        capability: str,
        input: dict
    ) -> dict:
        """Call a Crank worker from plugin."""
        return await self._worker_client.call(
            worker=worker,
            capability=capability,
            input=input
        )

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get plugin configuration value."""
        return self.config.get(key, default)

class Plugin(ABC):
    """Base class for agent plugins."""

    @abstractmethod
    def __init__(self, context: PluginContext):
        """Initialize plugin with context."""
        pass
```

**Plugin Loader** (Agent Runtime):

```python
# Agent loads plugins at startup
import importlib.util
import yaml
from pathlib import Path

class PluginLoader:
    def __init__(self, agent_id: str, plugin_dir: Path):
        self.agent_id = agent_id
        self.plugin_dir = plugin_dir
        self.plugins: dict[str, Plugin] = {}

    async def load_plugins(self):
        """Discover and load all plugins."""
        for plugin_path in self.plugin_dir.iterdir():
            if not plugin_path.is_dir():
                continue

            manifest_path = plugin_path / "plugin.yaml"
            if not manifest_path.exists():
                continue

            # Load manifest
            with open(manifest_path) as f:
                manifest = yaml.safe_load(f)

            # Check compatibility
            if self.agent_id not in manifest["compatible_agents"]:
                continue

            # Import plugin module
            spec = importlib.util.spec_from_file_location(
                manifest["name"],
                plugin_path / "__init__.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Create plugin instance
            context = PluginContext(
                agent_id=self.agent_id,
                config=manifest.get("config", {}),
                worker_client=self.worker_client
            )
            plugin = module.create_plugin(context)

            # Call lifecycle hook
            if hasattr(plugin, manifest["hooks"]["on_load"]):
                hook = getattr(plugin, manifest["hooks"]["on_load"])
                await hook()

            # Register capabilities
            self.plugins[manifest["name"]] = plugin
            self._register_capabilities(manifest, plugin)

    def _register_capabilities(self, manifest: dict, plugin: Plugin):
        """Register plugin capabilities with agent."""
        for cap in manifest["capabilities"]:
            handler = getattr(plugin, cap["name"])
            self.capability_registry.register(
                verb=cap["verb"],
                name=cap["name"],
                handler=handler,
                input_schema=cap["input_schema"],
                output_schema=cap["output_schema"]
            )
```

**Agent Usage**:

```python
# Agent13 uses plugin capabilities
from agent13 import Agent13

agent = Agent13(agent_id="agent13-codex")

# Plugins auto-loaded from ~/.crank/agents/agent13/plugins/
await agent.load_plugins()

# Call plugin capability
result = await agent.execute_capability(
    verb="analyze",
    capability="analyze_email",
    input={
        "email_text": "...",
        "headers": {"From": "..."}
    }
)

print(result["sentiment"])  # "positive"
print(result["urgency"])    # "high"
```

**Plugin Distribution**:

```bash
# Plugins distributed via Git
cd ~/.crank/agents/agent13/plugins/
git clone https://github.com/crank-platform/plugin-email-analyzer.git email-analyzer

# Agent auto-loads on next startup
```

**Future: Plugin Marketplace**:

```bash
# Install plugin via CLI
crank plugin install email-analyzer --agent agent13

# List available plugins
crank plugin list --marketplace

# Update plugins
crank plugin update --all
```

## Review History

- 2025-11-16 - Initial proposal (Agent13/Agent14 extensibility)
