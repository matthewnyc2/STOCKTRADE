#!/bin/bash

# Branch Protection Setup Script for STOCKTRADE
# This script configures GitHub branch protection rules

set -e

REPO_OWNER="${1:-matthewnyc2}"
REPO_NAME="${2:-STOCKTRADE}"
BRANCH="${3:-master}"

echo "Setting up branch protection for ${REPO_OWNER}/${REPO_NAME}:${BRANCH}"

# Check if gh is authenticated
if ! gh auth status &>/dev/null; then
    echo "Error: GitHub CLI not authenticated. Run: gh auth login"
    exit 1
fi

# Set branch protection rules
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "repos/${REPO_OWNER}/${REPO_NAME}/branches/${BRANCH}/protection" \
  -f required_status_checks='{"strict":true,"checks":[{"context":"CI Pipeline"},{"context":"PR Review Automation"}]}' \
  -f enforce_admins=true \
  -f required_pull_request_reviews='{"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
  -f restrictions=null \
  -f allow_force_pushes=false \
  -f allow_deletions=false

echo "✅ Branch protection configured successfully!"
echo ""
echo "Summary of protections applied:"
echo "  • Require PR reviews before merging (1 approval required)"
echo "  • Require status checks to pass (CI Pipeline, PR Review Automation)"
echo "  • Dismiss stale reviews when new commits are pushed"
echo "  • Require review from code owners"
echo "  • Enforce rules for administrators"
echo "  • Do not allow force pushes"
echo "  • Do not allow branch deletion"
echo ""
echo "Note: You may also need to configure the following manually:"
echo "  1. Install GitHub Copilot (https://github.com/features/copilot)"
echo "  2. Install Amazon Q Developer (https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/)"

# Also set up CODEOWNERS file if it doesn't exist
if [ ! -f ".github/CODEOWNERS" ]; then
    echo ""
    echo "Creating CODEOWNERS file..."
    cat > .github/CODEOWNERS << 'EOF'
# Default code owners
* @matthewnyc2

# API endpoints
/api/ @matthewnyc2

# Services (business logic)
/services/ @matthewnyc2

# Database
/core/ @matthewnyc2

# Frontend
/frontend/ @matthewnyc2
EOF
    echo "✅ CODEOWNERS file created. Edit to add more owners."
fi
