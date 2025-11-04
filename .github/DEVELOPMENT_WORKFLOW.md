# Crank Platform Development Workflow

## 🎯 Quick Issue Creation

Use these shortcuts to create properly categorized issues:

### 🐛 Bug Report
- Found something broken? Use the **Bug Report** template
- Includes environment details and affected mascots
- Automatic `bug` label assignment

### 💡 Feature Request  
- New functionality ideas? Use the **Feature Request** template
- Maps to mascot responsibilities
- Priority classification built-in

### 🗺️ Roadmap Item
- Strategic platform improvements? Use the **Roadmap Item** template
- Links to platform vision and goals
- Timeline and dependency tracking

## 📋 Recommended Labels

```
Priority:
- critical (Platform breaking, immediate fix needed)
- high (Major improvement, next sprint)
- medium (Nice to have, future sprint)
- low (Someday/maybe)

Type:
- bug (Something broken)
- enhancement (New feature)
- roadmap (Strategic item)
- documentation (Docs improvement)
- testing (Test coverage)

Mascot:
- wendy (Security/Certificates)
- kevin (Portability/Containers)  
- bella (Modularity/Services)
- oliver (Anti-patterns/Quality)
- gary (Testing/Methodical)

Status:
- in-progress (Actively working)
- blocked (Waiting on dependency)
- review (Ready for review)
```

## 🚀 GitHub Projects Integration

1. **Create Project Board**: Go to repository → Projects → New Project
2. **Choose Template**: Start with "Basic Kanban" 
3. **Add Columns**: 
   - 📥 Backlog
   - 🔄 In Progress  
   - 👀 Review
   - ✅ Done

4. **Link Issues**: Drag issues into appropriate columns
5. **Automation**: Set up auto-move rules for PR merges

## 🎮 Mascot-Based Development

Each mascot can have their own project view:
- **Wendy's Security Board**: Filter by `wendy` label
- **Kevin's Portability Tasks**: Filter by `kevin` label  
- **Bella's Architecture Items**: Filter by `bella` label

This creates focused workstreams while maintaining overall project visibility.