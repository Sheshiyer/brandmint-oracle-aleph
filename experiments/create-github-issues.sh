#!/bin/bash
#
# Create GitHub issues for v4.4.1 Foundation Hardening milestone
#

set -euo pipefail

REPO="Sheshiyer/brandmint-oracle-aleph"
MILESTONE_TITLE="v4.4.1 Foundation Hardening"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Creating GitHub Issues ==="
echo "Repository: ${REPO}"
echo "Milestone: ${MILESTONE_TITLE}"
echo "Script Dir: ${SCRIPT_DIR}"
echo "Project Root: ${PROJECT_ROOT}"
echo

# Check if gh CLI is authenticated
if ! gh auth status >/dev/null 2>&1; then
    echo "Error: gh CLI not authenticated. Run: gh auth login"
    exit 1
fi

# Note: gh CLI doesn't have milestone create command in this version
# We'll create issues without milestone and add it manually via web UI
echo "Note: Milestone creation not supported in this gh CLI version."
echo "Please create milestone manually at: https://github.com/${REPO}/milestones/new"
echo "  Title: ${MILESTONE_TITLE}"
echo "  Due date: 2026-04-09"
echo "  Description: Foundation hardening with provider fallback and state validation. Target: 8.5/10 quality score."
echo
read -p "Press Enter after creating the milestone to continue..."

echo

# Issue #1: Provider Fallback Chain Integration
echo "Creating Issue #1: Provider Fallback Chain Integration"
gh issue create \
    --repo "${REPO}" \
    --title "Provider Fallback Chain Integration" \
    --label "enhancement,priority-high,resilience" \
    --assignee "Sheshiyer" \
    --body-file "${PROJECT_ROOT}/.github/issue-templates/issue-1-provider-fallback.md"

ISSUE_1=$?

echo

# Issue #2: State File Validation Integration
echo "Creating Issue #2: State File Validation Integration"
gh issue create \
    --repo "${REPO}" \
    --title "State File Validation Integration" \
    --label "enhancement,priority-high,resilience" \
    --assignee "Sheshiyer" \
    --body-file "${PROJECT_ROOT}/.github/issue-templates/issue-2-state-validation.md"

ISSUE_2=$?

echo

# Issue #3: Testing and Documentation
echo "Creating Issue #3: Testing and Documentation"
gh issue create \
    --repo "${REPO}" \
    --title "v4.4.1 Testing and Documentation" \
    --label "testing,documentation,release-prep" \
    --assignee "Sheshiyer" \
    --body-file "${PROJECT_ROOT}/.github/issue-templates/issue-3-testing-docs.md"

ISSUE_3=$?

echo
if [ $ISSUE_1 -eq 0 ] && [ $ISSUE_2 -eq 0 ] && [ $ISSUE_3 -eq 0 ]; then
    echo "=== Done! ==="
    echo
    echo "✅ All 3 issues created successfully"
    echo
    echo "Next steps:"
    echo "1. Go to GitHub and add issues to milestone: ${MILESTONE_TITLE}"
    echo "2. View issues: https://github.com/${REPO}/issues"
    echo "3. Create feature branches: git checkout -b feature/provider-fallback-v4.4.1"
    echo "4. Start with Issue #1 or #2 (can be done in parallel)"
    echo "5. Run tests before creating PRs"
else
    echo "=== Errors occurred ==="
    echo "Some issues may not have been created. Check output above."
    exit 1
fi
