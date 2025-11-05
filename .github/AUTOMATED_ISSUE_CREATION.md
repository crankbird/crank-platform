# 🤖 Automated Issue Creation from Smoke Tests

This repository includes automated GitHub Actions workflows that create issues from smoke test warnings. This helps maintain code quality and ensures warnings don't get forgotten.

## 🎯 How It Works

### Option 1: Push-Based Automation (Currently Active)

**Workflow**: `.github/workflows/smoke-test-and-issues.yml`

- **Trigger**: Every push to `main` branch
- **Process**:
  1. Runs smoke tests automatically
  2. Parses warnings from test results
  3. Creates GitHub issues for each unique warning
  4. Labels issues with `enhancement`, `smoke-test-warning`, `automated`

**Benefits**:

- ✅ Simple - works with current push-based workflow
- ✅ Immediate feedback on main branch issues
- ✅ No workflow changes needed

### Option 2: Pull Request Automation (Enhanced)

**Workflow**: `.github/workflows/pr-smoke-test.yml`

- **Trigger**: Pull request creation/updates
- **Process**:
  1. Runs smoke tests on PR code
  2. Comments on PR with test results
  3. Creates issues for warnings only if PR is merged
  4. Assigns issues to PR author

**Benefits**:

- ✅ Prevents warnings from entering main branch
- ✅ Better attribution (issues assigned to change author)
- ✅ PR-level visibility of test results
- ✅ No noise from experimental branches

## 🏗️ Generated Issue Structure

Issues created from warnings include:

### 📋 Automatic Content

- **Title**: Descriptive title based on warning type
- **Labels**: `enhancement`, `smoke-test-warning`, `automated`
- **Mascot Assignment**: Auto-assigns relevant mascot based on warning
- **Context**: Commit SHA, test time, full warning details

### 🎮 Mascot Mapping

- **GPU warnings** → 🦙 Kevin (Portability)
- **API endpoint warnings** → 🎭 Bella (Modularity)
- **Performance warnings** → 🐢 Gary (Testing)

### 📊 Issue Lifecycle

- **Auto-creation**: From smoke test warnings
- **Auto-deduplication**: Prevents duplicate issues
- **Manual resolution**: Developer investigation and fixes
- **Auto-closing**: Issues close when warnings resolve (future enhancement)

## 🔧 Configuration

### Environment Variables

```bash
GITHUB_TOKEN    # Provided by GitHub Actions automatically
GITHUB_REPOSITORY  # Repository name (owner/repo)
GITHUB_SHA      # Commit hash for context
```

### Customization

- **Warning filters**: Edit `.github/scripts/create_warning_issues.py`
- **Issue templates**: Modify issue body generation
- **Mascot mapping**: Update mascot assignment logic
- **Labels**: Change default labels for created issues

## 🚀 Activation

The system is ready to use! Just:

1. **For Push-based**: Already active on pushes to `main`
2. **For PR-based**: Enable by switching primary workflow

## 📈 Benefits for Development

- **🔍 No Lost Warnings**: Every warning becomes trackable
- **📊 Quality Metrics**: Trend analysis of warning types
- **🎯 Focused Work**: Issues provide clear action items
- **🤖 AI Context**: Issues help AI agents understand platform state
- **👥 Team Coordination**: Clear ownership through mascot assignment

## 🎭 Mascot-Driven Issue Management

Each issue is automatically assigned to the most relevant mascot:

- **🐰 Wendy**: Security-related warnings
- **🦙 Kevin**: GPU/portability warnings
- **🎭 Bella**: API/modularity warnings
- **🦉 Oliver**: Code quality warnings
- **🐢 Gary**: Testing/performance warnings

This creates natural workstreams and helps with issue prioritization.
