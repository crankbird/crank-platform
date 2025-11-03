# 🎭 New Machine Setup - Quick Start

When you clone this repo on a new machine, here's how to get AI assistants (Copilot, etc.) to understand your mascot framework:

## ⚡ **1-Minute Setup**

```bash
# Run the automated context loader
./load_mascot_context.sh

# Or manually open these key files:
code docs/ARCHITECTURAL_MENAGERIE_GUIDE.md
code mascots/README.md  
code mascots/wendy/wendy_agent_prompt.txt
code mascots/kevin/kevin_agent_prompt.txt
```

## 🤖 **Tell Your AI Assistant**

Copy-paste this into chat with Copilot/Codex:

```
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

## ✅ **Success Indicators**

Your AI "gets it" when it:
- References mascots by name in code reviews
- Applies OWASP/NIST standards for Wendy
- Suggests environment variables for Kevin
- Identifies anti-patterns for Oliver
- Recommends service separation for Bella

---

📖 **Full details**: See `docs/development/AI_ASSISTANT_ONBOARDING.md`