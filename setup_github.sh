#!/bin/bash
# Script to set up GitHub repository and push code
# 
# INSTRUCTIONS:
# 1. Go to https://github.com/new
# 2. Create a new repository (e.g., "ems-police-awareness" or "nyc-ems-mental-health")
# 3. DO NOT initialize with README, .gitignore, or license (we already have these)
# 4. Copy the repository URL (e.g., https://github.com/yourusername/repo-name.git)
# 5. Run this script with the repository URL as an argument:
#    ./setup_github.sh https://github.com/yourusername/repo-name.git

if [ -z "$1" ]; then
    echo "Usage: ./setup_github.sh <repository-url>"
    echo ""
    echo "Example: ./setup_github.sh https://github.com/yourusername/ems-police-awareness.git"
    echo ""
    echo "First, create the repository on GitHub:"
    echo "1. Go to https://github.com/new"
    echo "2. Choose a repository name"
    echo "3. Make it public or private"
    echo "4. DO NOT initialize with README, .gitignore, or license"
    echo "5. Click 'Create repository'"
    echo "6. Copy the repository URL and use it as the argument to this script"
    exit 1
fi

REPO_URL="$1"

echo "Setting up GitHub repository..."
echo "Repository URL: $REPO_URL"
echo ""

# Add remote
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

# Push to GitHub
echo "Pushing code to GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Successfully pushed to GitHub!"
    echo "View your repository at: $REPO_URL"
else
    echo ""
    echo "✗ Push failed. Common issues:"
    echo "  - Repository doesn't exist or URL is incorrect"
    echo "  - Authentication required (you may need to set up GitHub credentials)"
    echo "  - Try: git push -u origin main"
fi

