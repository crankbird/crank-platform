#!/usr/bin/env python3
"""
Create PR comment with smoke test results.
"""
import json
import os
import requests

def create_pr_comment():
    """Create a comment on the PR with smoke test results."""
    
    github_token = os.environ.get('GITHUB_TOKEN')
    pr_number = os.environ.get('PR_NUMBER')
    github_repository = os.environ.get('GITHUB_REPOSITORY', 'crankbird/crank-platform')
    
    if not all([github_token, pr_number]):
        print("Missing required environment variables")
        return
    
    try:
        with open('smoke_test_results.json', 'r') as f:
            results = json.load(f)
    except FileNotFoundError:
        print("No smoke test results found")
        return
    
    # Format the comment
    summary = results.get('summary', {})
    warnings = results.get('warnings', [])
    
    comment_body = f"""## 🧪 Smoke Test Results

### 📊 Summary
- **Total Services**: {summary.get('total_services', 0)}
- **Healthy Services**: {summary.get('healthy_services', 0)}
- **Failed Services**: {len(summary.get('failed_services', []))}
- **GPU Services**: {summary.get('gpu_services', 0)}
- **Warnings**: {len(warnings)}

"""

    if summary.get('failed_services'):
        comment_body += "### ❌ Failed Services\n"
        for service in summary['failed_services']:
            comment_body += f"- `{service}`\n"
        comment_body += "\n"

    if warnings:
        comment_body += "### ⚠️ Warnings\n"
        for i, warning in enumerate(warnings[:5], 1):  # Limit to first 5
            comment_body += f"{i}. {warning}\n"
        
        if len(warnings) > 5:
            comment_body += f"\n... and {len(warnings) - 5} more warnings\n"
        
        comment_body += "\n🤖 **Automated issues will be created for these warnings if this PR is merged.**\n"
    else:
        comment_body += "### ✅ No Warnings\nAll smoke tests passed without warnings!\n"

    comment_body += "\n---\n*Smoke test results generated automatically by GitHub Actions*"

    # Post the comment
    repo_owner, repo_name = github_repository.split('/')
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_number}/comments"
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json',
    }
    
    comment_data = {'body': comment_body}
    
    response = requests.post(url, headers=headers, json=comment_data)
    
    if response.status_code == 201:
        print("✅ PR comment created successfully")
    else:
        print(f"❌ Failed to create PR comment: {response.status_code}")

if __name__ == '__main__':
    create_pr_comment()