#!/usr/bin/env python3
"""
Create GitHub issues from smoke test warnings.
"""

import hashlib
import json
import os
import sys
from datetime import datetime

import requests


def create_issue_title(warning):
    """Create a concise issue title from warning."""
    # Extract key parts of the warning
    if "GPU allocated but not detected" in warning:
        return "[ENHANCEMENT] GPU runtime libraries missing"
    if "Expected endpoint" in warning and "not available" in warning:
        # Extract endpoint from warning
        import re

        endpoint_match = re.search(r"Expected endpoint (/\S+)", warning)
        endpoint = endpoint_match.group(1) if endpoint_match else "unknown"
        return f"[ENHANCEMENT] Add missing endpoint: {endpoint}"
    if "Slow response" in warning:
        return "[PERFORMANCE] Service response time optimization"
    # Generic title for unknown warning types
    return "[ENHANCEMENT] Smoke test warning resolution"


def create_issue_body(warning, test_time, commit_sha):
    """Create detailed issue body from warning."""

    # Determine mascot involvement
    mascot_section = ""
    if "GPU" in warning:
        mascot_section = "- [x] 🦙 Kevin (Portability/GPU Configuration)"
    elif "endpoint" in warning:
        mascot_section = "- [x] 🎭 Bella (Modularity/API Standards)"
    elif "response" in warning:
        mascot_section = "- [x] 🐢 Gary (Testing/Performance)"
    else:
        mascot_section = "- [ ] 🎭 Bella (Modularity)\n- [ ] 🐢 Gary (Testing)"

    return f"""## 🚨 Smoke Test Warning

**Warning Details:**
```
{warning}
```

**Detection Context:**
- **Test Time:** {test_time}
- **Commit:** {commit_sha}
- **Source:** Automated smoke test pipeline

## 🎮 Affected Mascots

{mascot_section}

## 🔍 Analysis Needed

This warning was automatically detected during smoke testing. The issue requires investigation to determine:

1. **Root Cause:** Why is this warning occurring?
2. **Impact Assessment:** Does this affect functionality or just observability?
3. **Resolution Strategy:** Should this be fixed, documented, or suppressed?

## 📋 Acceptance Criteria

- [ ] Warning root cause identified
- [ ] Impact on platform functionality assessed
- [ ] Resolution implemented OR
- [ ] Warning documented as expected behavior OR
- [ ] Warning suppressed with justification

## 🏗️ Technical Context

This issue was automatically created from smoke test pipeline warnings. The smoke tests validate:
- Container health and responsiveness
- Expected API endpoints
- Resource allocation (GPU/CPU)
- Performance baselines

## 📊 Priority

- [ ] High (Affects core functionality)
- [x] Medium (Enhancement opportunity)
- [ ] Low (Nice to have)

*This issue will auto-close if the warning is resolved in future smoke tests.*"""


def get_existing_issues(headers, repo_owner, repo_name):
    """Get existing open issues with smoke-test-warning label."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    params = {
        "state": "open",
        "labels": "smoke-test-warning,enhancement",
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Failed to fetch existing issues: {response.status_code}")
    return []


def create_github_issue(warning, headers, repo_owner, repo_name, test_time, commit_sha):
    """Create a GitHub issue for a warning."""

    title = create_issue_title(warning)
    body = create_issue_body(warning, test_time, commit_sha)

    # Create a hash of the warning to avoid duplicates
    hashlib.md5(warning.encode()).hexdigest()[:8]

    issue_data = {
        "title": title,
        "body": body,
        "labels": ["enhancement", "smoke-test-warning", "automated"],
        "assignees": [],
    }

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

    response = requests.post(url, headers=headers, json=issue_data)

    if response.status_code == 201:
        issue = response.json()
        print(f"✅ Created issue #{issue['number']}: {title}")
        return issue
    print(f"❌ Failed to create issue: {response.status_code} - {response.text}")
    return None


def main():
    # Get environment variables
    github_token = os.environ.get("GITHUB_TOKEN")
    github_repository = os.environ.get("GITHUB_REPOSITORY", "crankbird/crank-platform")
    github_sha = os.environ.get("GITHUB_SHA", "unknown")

    if not github_token:
        print("ERROR: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    repo_owner, repo_name = github_repository.split("/")

    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "crank-platform-smoke-test-bot",
    }

    # Load warnings
    try:
        with open("warnings.json") as f:
            warnings = json.load(f)
    except FileNotFoundError:
        print("No warnings.json file found")
        return

    if not warnings:
        print("No warnings to process")
        return

    test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Get existing issues to avoid duplicates
    existing_issues = get_existing_issues(headers, repo_owner, repo_name)
    existing_titles = [issue["title"] for issue in existing_issues]

    print(f"Processing {len(warnings)} warnings...")
    created_count = 0

    for warning in warnings:
        title = create_issue_title(warning)

        # Check if similar issue already exists
        if any(title in existing_title for existing_title in existing_titles):
            print(f"⏭️  Skipping duplicate: {title}")
            continue

        issue = create_github_issue(warning, headers, repo_owner, repo_name, test_time, github_sha)
        if issue:
            created_count += 1

    print(f"📊 Summary: Created {created_count} new issues from {len(warnings)} warnings")


if __name__ == "__main__":
    main()
