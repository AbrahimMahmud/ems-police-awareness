# GitHub Repository Setup Guide

Your project is ready to be pushed to GitHub! Follow these steps:

## Option 1: Using GitHub Web Interface (Recommended)

### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. **Repository name**: Choose a name (e.g., `ems-police-awareness` or `nyc-ems-mental-health`)
3. **Description**: "MIT UROP: Effect of police shooting awareness on mental health EMS calls in NYC"
4. **Visibility**: Choose Public or Private
5. **IMPORTANT**: Do NOT check any boxes (no README, .gitignore, or license - we already have these)
6. Click **"Create repository"**

### Step 2: Push Your Code

After creating the repository, GitHub will show you commands. Use these instead:

```bash
# Add the remote (replace YOUR_USERNAME and REPO_NAME with your actual values)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

Or use the helper script:
```bash
./setup_github.sh https://github.com/YOUR_USERNAME/REPO_NAME.git
```

## Option 2: Using GitHub CLI (if installed)

If you have GitHub CLI (`gh`) installed:

```bash
# Create repository and push in one command
gh repo create ems-police-awareness --public --source=. --remote=origin --push
```

## Option 3: Manual Git Commands

If you already have a repository URL:

```bash
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

## Authentication

If you're prompted for credentials:
- **Username**: Your GitHub username
- **Password**: Use a Personal Access Token (not your password)
  - Create one at: https://github.com/settings/tokens
  - Select scope: `repo` (full control of private repositories)

## Verify

After pushing, visit your repository URL to confirm all files are there:
```
https://github.com/YOUR_USERNAME/REPO_NAME
```

## What's Included

The repository includes:
- ✅ All Python analysis scripts
- ✅ Documentation (README, diagnosis files)
- ✅ Requirements file
- ✅ Project structure
- ❌ Data files (excluded via .gitignore - too large)
- ❌ Output files (excluded via .gitignore - generated files)

## Next Steps

1. Add a license file (if desired)
2. Set up GitHub Actions for CI/CD (optional)
3. Add collaborators (if working with a team)
4. Create issues for future work items

