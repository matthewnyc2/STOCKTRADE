# Jules AI Coding Agent Complete Guide

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

## API Usage (CRITICAL FOR ORCHESTRATORS)
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

### Send Feedback to Session
When a session is "Awaiting User Feedback":
```bash
curl 'https://jules.googleapis.com/v1alpha/sessions/<session_id>:sendMessage' \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-Goog-Api-Key: $JULES_API_KEY" \
  -d '{"prompt": "Continue with the fix, ignore test X"}'
```

## Best Practices for Orchestrators
### 1. Always Push Branch First
Jules clones from GitHub remote, not your local filesystem. If your branch isn't pushed, Jules defaults to `main`.

### 2. Use API for Branch Control
The CLI infers branch from remote. For guaranteed branch targeting, use the API with `startingBranch`.

### 3. Scope Tasks Narrowly
**Bad:** "Fix all the tests"
**Good:** "Fix test_get_user_by_id in backend/tests/test_user_service.py"

### 4. Avoid Overlapping Tasks
Don't run multiple sessions that modify the same files - you'll get merge conflicts.

### 5. Monitor Session States
| State | Meaning |
|-------|---------|
| `PLANNING` | Jules is analyzing the task |
| `IN_PROGRESS` | Jules is coding |
| `AWAITING_USER_FEEDBACK` | Jules needs your input |
| `AWAITING_PLAN_APPROVAL` | Review and approve the plan |
| `COMPLETED` | Done - pull results |

## Automation Modes
| Mode | Behavior |
|------|----------|
| `AUTO_CREATE_PR` | Automatically creates PR when done |
| `MANUAL` | Requires manual review at each step |
