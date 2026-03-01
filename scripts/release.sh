#!/bin/bash
# Release Script for PostNow REST-API
# Usage: ./scripts/release.sh [patch|minor|major]
#
# This script:
# 1. Updates VERSION file
# 2. Creates a git tag
# 3. Optionally pushes to remote

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Read current version
CURRENT_VERSION=$(cat VERSION 2>/dev/null || echo "0.0.0")
echo -e "${YELLOW}Current version: v${CURRENT_VERSION}${NC}"

# Parse version components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Determine new version based on argument
RELEASE_TYPE="${1:-patch}"

case $RELEASE_TYPE in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    *)
        echo -e "${RED}Invalid release type: $RELEASE_TYPE${NC}"
        echo "Usage: $0 [patch|minor|major]"
        exit 1
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
echo -e "${GREEN}New version: v${NEW_VERSION}${NC}"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
    echo -e "${YELLOW}Warning: Not on main branch (current: $CURRENT_BRANCH)${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Check for uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
    echo -e "${RED}Error: Uncommitted changes detected. Please commit or stash first.${NC}"
    exit 1
fi

# Update VERSION file
echo "$NEW_VERSION" > VERSION
echo -e "${GREEN}Updated VERSION file${NC}"

# Create commit and tag
git add VERSION
git commit -m "chore(release): :bookmark: v${NEW_VERSION}"
git tag -a "v${NEW_VERSION}" -m "Release v${NEW_VERSION}"

echo -e "${GREEN}Created tag v${NEW_VERSION}${NC}"

# Ask to push
read -p "Push to remote? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin "$CURRENT_BRANCH"
    git push origin "v${NEW_VERSION}"
    echo -e "${GREEN}Pushed to remote${NC}"
fi

echo -e "${GREEN}Release v${NEW_VERSION} complete!${NC}"
