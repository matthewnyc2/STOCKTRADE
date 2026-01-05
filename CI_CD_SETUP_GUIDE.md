# CI/CD Setup Guide for STOCKTRADE

## Overview

This project now has comprehensive CI/CD automation for PR reviews and code quality checks.

## What's Been Set Up

### 1. GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `pr-review.yml` | PR opened/updated | Triggers AI reviews, runs tests, checks code quality |
| `ci.yml` | Push to main/PR | Full CI pipeline with all checks |
| `merge-queue.yml` | PR opened | Validates merge readiness |

### 2. AI Review Configuration

- **GitHub Copilot Instructions**: `.github/copilot-instructions.md`
- **Amazon Q Instructions**: `.github/amazon-q-instructions.md`
- These guide the AI reviewers on what to look for

### 3. Branch Protection

- **CODEOWNERS**: `.github/CODEOWNERS` - Defines required reviewers
- **Setup Script**: `.github/branch-protection-setup.sh` - Automates protection rules

## Setup Instructions

### Step 1: Commit and Push the Workflows

```bash
git add .github/
git commit -m "Add CI/CD workflows for PR automation"
git push origin master
```

### Step 2: Enable GitHub Copilot (if not already)

1. Go to: https://github.com/features/copilot
2. Install Copilot for your account
3. Enable for this repository

### Step 3: Enable Amazon Q Developer (optional but recommended)

1. Install Amazon Q Developer extension
2. Configure with your AWS credentials
3. Enable GitHub integration

### Step 4: Configure Branch Protection

**Option A: Automated Script**
```bash
chmod +x .github/branch-protection-setup.sh
.github/branch-protection-setup.sh matthewnyc2 STOCKTRADE master
```

**Option B: Manual via GitHub UI**
1. Go to: Settings → Branches
2. Click "Add rule" for `master` branch
3. Configure:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1)
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
   - Select checks: "CI Pipeline", "PR Review Automation"

## How It Works

### When You Create a PR

1. **Automatic Actions**:
   - `@copilot` comment triggers GitHub Copilot review
   - `/q` comment triggers Amazon Q review
   - Test suite runs automatically
   - Code quality checks run (Ruff, Black, mypy)
   - Security scan runs (Bandit, TruffleHog)

2. **Review Comments Added**:
   ```
   ## 🔍 PR Review Triggered

   **Automated reviews have been requested:**
   - ✅ @copilot - GitHub Copilot review requested
   - ✅ /q - Amazon Q review requested
   ```

3. **Merge Check**:
   The workflow comments on whether the PR is ready to merge:
   - Has approval(s)
   - All checks passing
   - AI reviews completed

### If No AI Reviews

If neither Copilot nor Amazon Q has reviewed, a reminder comment is posted:

```
## ⚠️ Review Gap Detected

Neither Copilot nor Amazon Q have reviewed this PR yet.

**Manual Actions:**
- Comment @copilot to trigger GitHub Copilot review
- Comment /q to trigger Amazon Q review
```

## Manual Review Triggers

If automated reviews fail, you can manually trigger them:

```bash
# On any PR, comment:
@copilot please review for security and performance

# Or for Amazon Q:
/q review this pull request
```

## CI Checks Explained

| Check | Description | Failure Impact |
|-------|-------------|----------------|
| Backend Tests | Python pytest suite | Block merge |
| Frontend Tests | TypeScript/React tests | Block merge |
| Lint and Format | Ruff, Black, isort | Warning only |
| Security Scan | Bandit, TruffleHog | Warning only |
| Docker Build | Test container builds | Warning only |

## Branch Protection Rules

Once configured, the `master` branch will:

- ✅ Require PR for all changes
- ✅ Require at least 1 approval
- ✅ Require status checks to pass
- ✅ Require code owner approval
- ✅ Dismiss stale reviews on new commits
- ❌ Block force pushes
- ❌ Block branch deletion

## Workflow Files

```
.github/
├── workflows/
│   ├── pr-review.yml      # Main PR automation
│   ├── ci.yml             # Full CI pipeline
│   └── merge-queue.yml    # Merge validation
├── copilot-instructions.md   # Copilot review guidelines
├── amazon-q-instructions.md  # Amazon Q review guidelines
├── CODEOWNERS                # Code owner definitions
└── branch-protection-setup.sh # Setup automation
```

## Troubleshooting

### Workflows not running?
- Check Actions tab for errors
- Verify GitHub Actions is enabled for repo
- Check workflow syntax (YAML indentation)

### AI reviews not appearing?
- Verify Copilot/Q is installed
- Check if bot has permissions
- Try manual trigger with @copilot or /q

### Branch protection not working?
- Run the setup script with `gh auth login` first
- Check repo Settings → Branches → Rules
- Verify admin settings aren't overriding

### Tests failing in CI but passing locally?
- Check Python version (CI uses 3.14)
- Verify dependencies in requirements.txt
- Check environment variables

## Next Steps

1. **Push and create a test PR** to verify everything works
2. **Monitor the Actions tab** to see workflows in action
3. **Adjust review criteria** in the instructions files as needed
4. **Add more CODEOWNERS** for different project areas
