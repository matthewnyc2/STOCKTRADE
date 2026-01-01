# Jules AI Coding Agent Guide

> A comprehensive guide for using Google's Jules autonomous coding agent with MailShield.

## Overview

Jules is Google's asynchronous AI coding agent that can work on coding tasks in the background. It clones your repository, makes changes, and creates pull requests automatically.

## Setup

### 1. Install Jules CLI

```bash
npm install -g @google/jules
```

### 2. Login

```bash
jules login
```

This opens a browser for Google OAuth authentication.

### 3. Get API Key

1. Go to https://jules.google.com
2. Navigate to Settings
3. Generate an API key
4. Add to `.env`: `JULES_API_KEY=your_key_here`

## CLI Commands

### List Sessions

```bash
jules remote list --session    # List all sessions
jules remote list --repo       # List connected repos
```

### Create Session (Basic)

```bash
jules new "Fix the login bug"
jules new --repo owner/repo "Add unit tests"
jules new --parallel 3 "Refactor authentication"  # 3 parallel sessions
```

### Pull Results

```bash
jules remote pull --session <session_id>          # View patch
jules remote pull --session <session_id> --apply  # Apply locally
```

### Interactive TUI

```bash
jules  # Opens terminal UI for managing sessions
```

In TUI:
- `Enter` - Select session
- `Ctrl+D` - Delete session
- `Ctrl+R` - Refresh
- `Ctrl+C` - Quit

## API Usage

The CLI has limitations. Use the API for full control.

### Create Session on Specific Branch

**Critical:** The CLI doesn't have a `--branch` flag. To work on a specific branch, use the API:

```bash
curl 'https://jules.googleapis.com/v1alpha/sessions' \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: $JULES_API_KEY" \
  -d '{
    "prompt": "Fix test failures in test_billing_service.py",
    "sourceContext": {
      "source": "sources/github/OWNER/REPO",
      "githubRepoContext": {
        "startingBranch": "your-branch-name"
      }
    },
    "automationMode": "AUTO_CREATE_PR",
    "title": "Fix billing tests"
  }'
```

### List Sessions

```bash
curl 'https://jules.googleapis.com/v1alpha/sessions' \
  -H "X-Goog-Api-Key: $JULES_API_KEY"
```

### Delete Session

```bash
curl -X DELETE "https://jules.googleapis.com/v1alpha/sessions/<session_id>" \
  -H "X-Goog-Api-Key: $JULES_API_KEY"
```

### Send Feedback to Session

When a session is "Awaiting User Feedback":

```bash
curl 'https://jules.googleapis.com/v1alpha/sessions/<session_id>:sendMessage' \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: $JULES_API_KEY" \
  -d '{"prompt": "Continue with the fix, ignore test X"}'
```

## PowerShell Examples

### Create Session on Branch

```powershell
$apiKey = $env:JULES_API_KEY
$headers = @{
    "Content-Type" = "application/json"
    "X-Goog-Api-Key" = $apiKey
}

$body = @{
    prompt = "Fix failing tests"
    sourceContext = @{
        source = "sources/github/matthewnyc2/mailshield"
        githubRepoContext = @{
            startingBranch = "my-feature-branch"
        }
    }
    automationMode = "AUTO_CREATE_PR"
    title = "Fix tests"
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "https://jules.googleapis.com/v1alpha/sessions" `
    -Headers $headers -Method Post -Body $body
```

### Delete Multiple Sessions

```powershell
$sessionsToDelete = @("id1", "id2", "id3")

foreach ($id in $sessionsToDelete) {
    Invoke-RestMethod -Uri "https://jules.googleapis.com/v1alpha/sessions/$id" `
        -Headers $headers -Method Delete
    Write-Host "Deleted: $id"
}
```

### Batch Create from File

```powershell
Get-Content tasks.txt | ForEach-Object {
    jules new $_
}
```

## Best Practices

### 1. Always Push Branch First

Jules clones from GitHub remote, not your local filesystem. If your branch isn't pushed, Jules defaults to `main`.

```bash
# WRONG - branch not pushed, Jules uses main
git checkout my-feature
jules new "Fix bug"

# CORRECT - push first
git checkout my-feature
git push origin my-feature
jules new "Fix bug"
```

### 2. Use API for Branch Control

The CLI infers branch from remote. For guaranteed branch targeting, use the API with `startingBranch`.

### 3. Scope Tasks Narrowly

**Bad:** "Fix all the tests"
**Good:** "Fix test_get_user_by_id in backend/tests/test_user_service.py"

### 4. Avoid Overlapping Tasks

Don't run multiple sessions that modify the same files - you'll get merge conflicts.

**Bad:**
- Session 1: "Fix backend tests"
- Session 2: "Refactor backend services"

**Good:**
- Session 1: "Fix test_billing_service.py"
- Session 2: "Fix test_mail_service.py"

### 5. Monitor Session States

| State | Meaning |
|-------|---------|
| `PLANNING` | Jules is analyzing the task |
| `IN_PROGRESS` | Jules is coding |
| `AWAITING_USER_FEEDBACK` | Jules needs your input |
| `AWAITING_PLAN_APPROVAL` | Review and approve the plan |
| `COMPLETED` | Done - pull results |

### 6. Pull and Test Before Merging

```bash
# Pull the patch
jules remote pull --session <id> --apply

# Test locally
pytest backend/tests/

# If good, commit
git add .
git commit -m "fix: Apply Jules fixes"
git push
```

## Automation Modes

When creating via API, set `automationMode`:

| Mode | Behavior |
|------|----------|
| `AUTO_CREATE_PR` | Automatically creates PR when done |
| `MANUAL` | Requires manual review at each step |

## Troubleshooting

### Patches Don't Apply

**Cause:** Session was created against different branch than you're trying to apply to.

**Fix:** 
1. Check which branch the session used
2. Either checkout that branch, or
3. Delete session and recreate with correct `startingBranch`

### Session Stuck on "Awaiting Feedback"

Use the `sendMessage` API endpoint to provide guidance:

```bash
curl 'https://jules.googleapis.com/v1alpha/sessions/<id>:sendMessage' \
  -X POST \
  -H "X-Goog-Api-Key: $JULES_API_KEY" \
  -d '{"prompt": "Proceed with the suggested approach"}'
```

### Can't Delete via CLI

Use the API:

```bash
curl -X DELETE "https://jules.googleapis.com/v1alpha/sessions/<id>" \
  -H "X-Goog-Api-Key: $JULES_API_KEY"
```

## Resources

- [Jules Home](https://jules.google)
- [Jules Docs](https://jules.google/docs)
- [CLI Reference](https://jules.google/docs/cli/reference)
- [API Reference](https://developers.google.com/jules/api)
- [Practical Examples](https://jules.google/docs/cli/examples)

---

*Last Updated: 2025-11-29*
