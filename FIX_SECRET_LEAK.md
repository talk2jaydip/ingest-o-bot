# CRITICAL: Fix Secret Leak in Git History

## ⚠️ SECURITY ISSUE
GitHub blocked your push because these files contain **real Azure secrets**:
- `.env.azure` - Contains Azure AD Application Secret, Search Admin Key, Storage Keys
- `.env.hybrid` - Contains same secrets
- `.env.offline` - May contain secrets
- `.env.test_azure_di` - May contain secrets
- `envs/.env.hybrid` - Contains secrets

## 🔴 IMMEDIATE ACTIONS REQUIRED

### Step 1: Remove Files from Git History

You need to remove these files from **ALL** commits in your git history.

**Option A: Using BFG Repo-Cleaner (Recommended - Fastest)**
```bash
# Download BFG: https://rtyley.github.io/bfg-repo-cleaner/
# Or: brew install bfg (Mac) / choco install bfg (Windows)

# Backup your repo first!
cd ..
cp -r ingest-o-bot ingest-o-bot-backup

cd ingest-o-bot

# Remove the secret files from history
bfg --delete-files .env.azure
bfg --delete-files .env.hybrid
bfg --delete-files .env.offline
bfg --delete-files .env.test_azure_di

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (this rewrites history)
git push --force origin feature/pluggable-architecture
```

**Option B: Using git filter-repo (Modern Alternative)**
```bash
# Install: pip install git-filter-repo

# Backup first!
cd ..
cp -r ingest-o-bot ingest-o-bot-backup
cd ingest-o-bot

# Remove files from history
git filter-repo --path .env.azure --invert-paths
git filter-repo --path .env.hybrid --invert-paths
git filter-repo --path .env.offline --invert-paths
git filter-repo --path .env.test_azure_di --invert-paths
git filter-repo --path envs/.env.hybrid --invert-paths

# Force push
git push --force origin feature/pluggable-architecture
```

**Option C: Manual git filter-branch (Slowest)**
```bash
# Backup first!
cd ..
cp -r ingest-o-bot ingest-o-bot-backup
cd ingest-o-bot

# Remove files from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env.azure .env.hybrid .env.offline .env.test_azure_di envs/.env.hybrid" \
  --prune-empty --tag-name-filter cat -- --all

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push --force origin feature/pluggable-architecture
```

### Step 2: Rotate ALL Exposed Secrets ⚠️

Since these secrets were in commit `7d16a4f`, they are now **COMPROMISED**.
You MUST rotate/regenerate ALL these credentials immediately:

1. **Azure Active Directory Application Secret** (.env.azure:38, envs/.env.hybrid:25)
   - Go to Azure Portal → App Registrations → Your App
   - Go to "Certificates & secrets"
   - Delete the old secret
   - Create a new secret
   - Update your local .env.azure and .env.hybrid

2. **Azure Search Admin Key** (.env.azure:59, envs/.env.hybrid:43)
   - Go to Azure Portal → Azure AI Search → Your service
   - Go to "Keys"
   - Regenerate the admin key
   - Update your local files

3. **Azure Storage Account Access Keys** (.env.azure:97-98, envs/.env.hybrid:63-64)
   - Go to Azure Portal → Storage Account → Your account
   - Go to "Access keys"
   - Click "Rotate key" for both key1 and key2
   - Update your local files

### Step 3: Verify Files Are Ignored

After removing from history, verify the files are now ignored:

```bash
# These should show as ignored
git status --ignored | grep -E "\.env\.(azure|hybrid|offline|test)"

# Try to add them (should fail)
git add .env.azure
# Should output: "The following paths are ignored by one of your .gitignore files"
```

### Step 4: Verify Clean Push

```bash
# After rotating secrets and cleaning history, try pushing again
git push --force origin feature/pluggable-architecture

# Should succeed without secret scanning errors
```

## 📋 Checklist

- [ ] Backup repository before cleaning
- [ ] Remove secret files from git history (use one of the options above)
- [ ] Force push to update remote history
- [ ] Rotate Azure AD Application Secret
- [ ] Rotate Azure Search Admin Key
- [ ] Rotate Azure Storage Account Access Keys (both key1 and key2)
- [ ] Update local .env files with new credentials
- [ ] Verify .gitignore is working (try `git add .env.azure` - should be ignored)
- [ ] Verify push succeeds without GitHub secret scanning errors

## 🛡️ Prevention

The `.gitignore` has been updated to prevent this in the future. These patterns now block:
- `.env.*` (except .example files)
- `envs/.env*` (except .example files)
- All secret-containing env file variants

**NEVER** commit actual .env files - only commit .env.example templates.

## 📚 Resources

- BFG Repo-Cleaner: https://rtyley.github.io/bfg-repo-cleaner/
- git-filter-repo: https://github.com/newren/git-filter-repo
- GitHub Secret Scanning: https://docs.github.com/code-security/secret-scanning
- Azure Key Rotation: https://learn.microsoft.com/azure/key-vault/secrets/secrets-rotation

## ❓ Need Help?

If you encounter issues:
1. Check the GitHub error message for specific file locations
2. Verify secrets are actually removed: `git log --all --full-history -- .env.azure`
3. Contact your security team if secrets may have been exposed
