# 🎭 Mascot Framework Quick Start Guide

## 🚀 **New Machine Setup - AI Assistant Onboarding**

When you open this repository on a new machine, follow these steps to get AI coding assistants (GitHub Copilot, Codex, etc.) familiar with your mascot framework:

### 1. **📋 Read the Core Documents First**

Open these files in your editor to load them into AI context:

```bash
# Essential mascot documentation
code docs/ARCHITECTURAL_MENAGERIE_GUIDE.md
code docs/MASCOT_HAPPINESS_REPORT.md
code docs/architecture/ENHANCED_MASCOT_FRAMEWORK.md
code mascots/README.md
```

### 2. **🎭 Load Mascot Personalities**

Open the agent prompt files to establish mascot personalities:

```bash
# Load each mascot's personality into AI context
code mascots/wendy/wendy_agent_prompt.txt
code mascots/kevin/kevin_agent_prompt.txt
# code mascots/bella/bella_agent_prompt.txt  # When created
# code mascots/oliver/oliver_agent_prompt.txt  # When created
```

### 3. **⚡ Quick Context Primer**

Copy and paste this into a new file or chat with your AI assistant to establish context:

```
MASCOT FRAMEWORK CONTEXT:
This codebase uses a mascot-driven architectural testing framework with 4 core mascots:

🐰 WENDY - Zero-Trust Security Bunny
- Domain: Security, OWASP compliance, Bobby Tables prevention
- Standards: NIST SP 800-53, zero-trust principles
- Focus: Input validation, mTLS, secrets management, injection prevention

🦙 KEVIN - Portability Llama  
- Domain: Platform independence, runtime abstraction
- Standards: 12-factor app, container runtime agnostic
- Focus: Environment config, multi-runtime support, vendor lock-in prevention

🐩 BELLA - Modularity Poodle
- Domain: Service separation, clean interfaces
- Standards: SOLID principles, dependency injection
- Focus: Loose coupling, high cohesion, plugin architecture

🦅 OLIVER - Anti-Pattern Eagle
- Domain: Code quality, architectural patterns
- Standards: Gang of Four, Clean Code, evidence-based decisions
- Focus: Anti-pattern detection, SOLID compliance, technical debt prevention

Bobby Tables is NOT a separate mascot - it's a vulnerability pattern under Wendy's security domain.

When reviewing code, consider which mascot's concerns are relevant and apply their standards.
```

### 4. **🔍 Test Framework Understanding**

Run this command to verify the AI understands the framework:

```bash
# Generate a mascot prompt to test AI understanding
python3 run_mascot_tests.py --generate-prompt wendy --context "onboarding test"
```

### 5. **📁 Key Files to Have Open**

Keep these files open in tabs for maximum AI context:

```
📂 Essential Files (always keep open):
├── docs/
│   ├── ARCHITECTURAL_MENAGERIE_GUIDE.md       # Your existing comprehensive guide
│   ├── MASCOT_HAPPINESS_REPORT.md             # Current mascot status
│   └── architecture/
│       └── ENHANCED_MASCOT_FRAMEWORK.md       # Enhanced capabilities
├── mascots/README.md                          # Framework overview
├── run_mascot_tests.py                        # Main orchestrator
└── mascots/wendy/wendy_agent_prompt.txt       # Security prompt template

📂 Test Files (for examples):
├── mascots/wendy/wendy_tests.py               # Security test patterns
├── mascots/kevin/kevin_tests.py               # Portability test patterns
└── demo_ai_integration.py                     # Integration examples
```

## 🤖 **AI Assistant Integration Patterns**

### **GitHub Copilot Setup**

Add this to your workspace `.vscode/settings.json`:

```json
{
  "github.copilot.advanced": {
    "debug.overrideEngine": "copilot-chat",
    "debug.testOverrideProxyUrl": "",
    "debug.overrideProxyUrl": ""
  },
  "github.copilot.editor.enableAutoCompletions": true,
  "github.copilot.enable": {
    "*": true,
    "yaml": true,
    "plaintext": true,
    "markdown": true,
    "python": true
  }
}
```

### **Context Establishment Commands**

Use these phrases when starting a new coding session:

```bash
# In chat with AI assistant:
"This project uses a mascot-driven architecture with Wendy (security), Kevin (portability), Bella (modularity), and Oliver (anti-patterns). Bobby Tables attacks fall under Wendy's domain."

# When asking for code review:
"Please review this code from Wendy's security perspective, focusing on Bobby Tables prevention and OWASP compliance."

# When asking for architectural advice:
"Consider this from Kevin's portability perspective - ensure no Docker-specific dependencies."
```

## 🎯 **Quick Validation Test**

After setup, test AI understanding with:

```bash
# Ask your AI assistant:
"What would Wendy think about this SQL query construction?"
"How would Kevin evaluate this Docker-specific code?"
"Which mascot would be concerned about this hardcoded configuration?"
```

**Expected AI Response**: The AI should reference specific mascots, their domains, and architectural standards.

## 📋 **AI Assistant Prompts for Common Tasks**

### **Code Review Request**
```
Please review this code from our mascot framework perspective:
- Wendy: Security and Bobby Tables prevention
- Kevin: Platform independence and portability  
- Bella: Service separation and modularity
- Oliver: Anti-patterns and code quality

Focus on [specific mascot] concerns for this review.
```

### **Architecture Decision**
```
I need to make an architectural decision about [topic]. Please evaluate this from our mascot perspectives:
- What would Wendy say about security implications?
- How would Kevin assess portability concerns?
- What would Bella think about modularity impact?
- Would Oliver spot any anti-patterns?
```

### **Code Generation**
```
Generate code that would make our mascots happy:
- Wendy: Secure by default, input validation, parameterized queries
- Kevin: Environment-based config, runtime agnostic
- Bella: Clean interfaces, dependency injection
- Oliver: SOLID principles, no anti-patterns
```

## 🔧 **IDE Extensions for Enhanced Context**

### **VS Code Extensions**
```bash
# Install these for better mascot framework support:
code --install-extension ms-python.python
code --install-extension redhat.vscode-yaml
code --install-extension ms-vscode.vscode-json
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat
```

### **IntelliJ/PyCharm Plugins**
- GitHub Copilot Plugin
- YAML/Ansible Support
- Docker Integration
- Security Plugins (for Wendy's standards)

## 🎭 **Mascot-Specific Context Loading**

### **For Security Work (Wendy Focus)**
```bash
# Load Wendy's context
code mascots/wendy/wendy_tests.py
code mascots/wendy/wendy_agent_prompt.txt

# Review security standards
grep -r "OWASP\|NIST\|CWE" docs/
```

### **For Portability Work (Kevin Focus)**
```bash
# Load Kevin's context  
code mascots/kevin/kevin_tests.py
code mascots/kevin/kevin_agent_prompt.txt

# Review portability patterns
grep -r "runtime\|docker\|container" docs/
```

## ✅ **Verification Checklist**

After setup, verify AI understanding:

- [ ] AI can identify which mascot owns which concern
- [ ] AI knows Bobby Tables is under Wendy's domain
- [ ] AI references specific standards (OWASP, NIST, 12-factor)
- [ ] AI suggests mascot-appropriate solutions
- [ ] AI can generate mascot-style code reviews

## 🚨 **Common AI Misconceptions to Correct**

If your AI assistant makes these mistakes, correct them:

❌ **Wrong**: "Bobby Tables is a separate mascot"
✅ **Correct**: "Bobby Tables is a vulnerability pattern under Wendy's security domain"

❌ **Wrong**: "This is just a testing framework"  
✅ **Correct**: "This is an architectural philosophy with testing tools"

❌ **Wrong**: "Mascots are just cute names"
✅ **Correct**: "Mascots represent specific architectural concerns with defined standards"

## 🎉 **Success Indicators**

You'll know the AI "gets it" when it:
- References mascots by name in architectural discussions
- Applies specific standards (NIST, OWASP, 12-factor) correctly
- Suggests code that aligns with mascot principles
- Identifies cross-cutting concerns between mascots
- Proposes collaboration patterns for complex issues

---

**💡 Pro Tip**: Keep the mascot documentation open in pinned tabs. Most AI assistants use open files as primary context!