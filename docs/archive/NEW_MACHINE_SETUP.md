# 🎭 New Machine Setup - Quick Start

When you clone this repo on a new machine, here's how to get AI assistants (Copilot, etc.) to understand your mascot framework:

## ⚡ **1-Minute Setup**

```bash
# Run the automated context loader

./load_mascot_context.sh

# Or manually open these key files

code docs/ARCHITECTURAL_MENAGERIE_GUIDE.md
code mascots/README.md
code mascots/wendy/wendy_agent_prompt.txt
code mascots/kevin/kevin_agent_prompt.txt

```

## 🤖 **Tell Your AI Assistant**

Copy-paste this into chat with Copilot/Codex:

```text
This codebase uses a mascot-driven architecture framework:

🐰 WENDY - Security (OWASP, Bobby Tables prevention, NIST compliance)
🦙 KEVIN - Portability (runtime-agnostic, 12-factor app, no vendor lock-in)
🐩 BELLA - Modularity (service separation, clean interfaces, SOLID principles)
🦅 OLIVER - Anti-Patterns (code quality, Gang of Four patterns, technical debt)

Bobby Tables is a vulnerability pattern under Wendy's security domain, not a separate mascot.

When reviewing code, apply the relevant mascot's standards and concerns.
```

## 🎯 **Test AI Understanding**

Ask your AI assistant:

- "What would Wendy think about this SQL query construction?"

- "How would Kevin evaluate this Docker-specific code?"

- "Which mascot handles Bobby Tables attacks?" (Answer: Wendy)

## 📁 **VS Code Workspace**

Open `crank-platform-mascots.code-workspace` for:

- Pre-configured tasks for mascot testing
- Recommended extensions
- Integrated terminal commands

## 🐍 **Python Import Resolution**

The `crank.*` package lives under `src/`. Import resolution is already configured, but if you see Pylance errors like `"Import 'crank.capabilities.schema' could not be resolved"`:

**Quick Fix**: Restart the Python language server

- Command Palette → "Python: Restart Language Server"
- Or reload the VS Code window

**If that doesn't work**, verify these configurations exist:

1. `pyrightconfig.json` has `"extraPaths": ["src"]` (global + tests execution environment)
2. `.vscode/settings.json` has `"python.analysis.extraPaths": ["${workspaceFolder}/src"]`
3. Python interpreter is set to `.venv/bin/python` (check status bar)

**Runtime**: For running tests/scripts, either:

```bash
# Option A: Editable install (recommended)
uv pip install -e .

# Option B: PYTHONPATH export
export PYTHONPATH=src
pytest
```

See inline comments in `pyrightconfig.json` and `.vscode/settings.json` for why both configs are needed.

## ✅ **Success Indicators**

Your AI "gets it" when it:

- References mascots by name in code reviews

- Applies OWASP/NIST standards for Wendy

- Suggests environment variables for Kevin

- Identifies anti-patterns for Oliver

- Recommends service separation for Bella

---

📖 **Full details**: See `docs/development/AI_ASSISTANT_ONBOARDING.md`
