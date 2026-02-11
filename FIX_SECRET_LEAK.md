# Secret Leak Fix Guide

## Problem
GitHub detected Azure secrets in git history. Files with exposed credentials:
- `.env.azure`, `.env.hybrid`, `.env.offline`, `.env.test_azure_di`
- `envs/.env.hybrid`

## Fix Steps

### 1. Remove from Git History (Choose One)

**BFG Repo-Cleaner (Fastest)**
```bash
# Install: https://rtyley.github.io/bfg-repo-cleaner/
bfg --delete-files .env.azure
bfg --delete-files .env.hybrid
bfg --delete-files .env.offline
bfg --delete-files .env.test_azure_di
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

**git filter-repo (Modern)**
```bash
# Install: pip install git-filter-repo
git filter-repo --path .env.azure --invert-paths
git filter-repo --path .env.hybrid --invert-paths
git filter-repo --path .env.offline --invert-paths
git filter-repo --path .env.test_azure_di --invert-paths
git push --force
```

### 2. Rotate Compromised Secrets

**All exposed secrets must be regenerated:**

1. **Azure AD Application Secret**
   - Portal → App Registrations → Certificates & secrets → Regenerate

2. **Azure Search Admin Key**
   - Portal → Azure AI Search → Keys → Regenerate

3. **Storage Account Keys**
   - Portal → Storage Account → Access keys → Rotate both keys

### 3. Update Local Files
Replace old secrets with new ones in your local `.env` files.

### 4. Verify & Push
```bash
# Verify ignored
git add .env.azure  # Should fail with "ignored" message

# Push
git push --force
```

## Prevention
- `.gitignore` now blocks all `.env.*` files (except `.example`)
- Only commit `.env.example` templates
- Never commit actual credentials
