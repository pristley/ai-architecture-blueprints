# CI/CD Pipeline Documentation

## Overview

This repository uses GitHub Actions for automated continuous integration and deployment. Every commit to `main` triggers a pipeline that lints, tests, updates documentation, and deploys to GitHub Pages.

## Pipeline Stages

### 1. Lint & Test

**Runs on:** Every push and pull request  
**Duration:** ~2-3 minutes

- ✅ **Python linting** with Ruff (checks code quality)
- ✅ **Syntax validation** for all Python examples
- ✅ **Example execution** (validates all examples run without errors)
- ✅ **Markdown link validation** (checks all internal links are valid)

### 2. Update Documentation

**Runs on:** Push to `main` only  
**Duration:** ~1 minute

- 📊 **Generate statistics** (line counts, file sizes)
- 📝 **Update AGENTMAP.md** with current repository stats
- 🔖 **Update README.md** with CI badge and timestamp
- 💾 **Auto-commit** documentation changes (with `[skip ci]` to prevent loops)

### 3. Deploy

**Runs on:** Push to `main` only  
**Duration:** ~2 minutes

- 📦 **Generate static site** with MkDocs Material theme
- 🚀 **Deploy to GitHub Pages** at `https://<username>.github.io/<repo>`
- 🌐 **Optional custom domain** support

### 4. Notify

**Runs on:** After all stages complete  
**Duration:** <1 minute

- 📋 **Generate deployment summary** in GitHub Actions UI
- ✅ **Report status** of each stage

## Workflow Triggers

```yaml
on:
  push:
    branches: [main]       # Auto-deploy on every commit to main
  pull_request:
    branches: [main]       # Run tests on PRs (but don't deploy)
  workflow_dispatch:       # Manual trigger from GitHub UI
```

## Auto-Documentation Updates

The pipeline automatically updates two files on every commit:

### AGENTMAP.md

Added at the end of the file:

```markdown
---

**Repository Statistics** (auto-generated)

- 📄 Documentation: 4,500 lines across 5 files
- 💻 Examples: 3,800 lines across 3 files
- 📊 Total: 8,300 lines
- 🕒 Last updated: 2026-06-24 04:45 UTC
```

### README.md

- **CI/CD Badge**: Added below the title
  ```markdown
  ![CI/CD Status](https://github.com/pristley/ai-architecture-blueprints/workflows/...)
  ```

- **Timestamp**: Updated in footer
  ```markdown
  **Last Updated:** 2026-06-24
  ```

## Local Testing

Test the pipeline components locally before pushing:

```bash
# Lint Python code
pip install ruff
ruff check . --select E,F,W,C,N --ignore E501

# Test examples
python examples_1_2.py
python examples_1_3.py
python examples_1_4.py

# Run documentation update script
python .github/scripts/update_docs.py

# Build documentation site locally
pip install mkdocs mkdocs-material
mkdocs serve  # View at http://localhost:8000
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/ci-cd.yml` | Main pipeline definition |
| `.github/scripts/update_docs.py` | Auto-documentation script |
| `mkdocs.yml` | Documentation site configuration (auto-generated) |
| `.gitignore` | Exclude build artifacts and caches |

## Pipeline Permissions

The workflow requires:

```yaml
permissions:
  contents: write        # To commit documentation updates
  pull-requests: write   # To comment on PRs (future feature)
```

## Skipping CI

To push changes without triggering the pipeline:

```bash
git commit -m "docs: Minor typo fix [skip ci]"
```

The `[skip ci]` tag prevents the workflow from running.

## Deployment Target

The static documentation site is deployed to:
- **URL**: `https://<username>.github.io/<repo-name>`
- **Branch**: `gh-pages` (auto-created by the pipeline)
- **Custom domain**: Configure in workflow under `deploy` → `cname`

## Monitoring

View pipeline execution:
1. Go to **Actions** tab in GitHub
2. Click on latest workflow run
3. Expand each job to see detailed logs
4. Check the **Summary** for deployment status

## Troubleshooting

### Pipeline fails on "Update Documentation"

**Cause**: Missing permissions  
**Fix**: Ensure `contents: write` permission is set in workflow

### Examples fail with API key error

**Expected**: Examples gracefully skip tests requiring `OPENAI_API_KEY`  
**Action**: No fix needed; this is normal for public CI

### Deployment fails

**Cause**: GitHub Pages not enabled  
**Fix**: Go to **Settings** → **Pages** → Enable GitHub Pages from `gh-pages` branch

## Future Enhancements

- 🧪 Add pytest integration for proper unit testing
- 📊 Generate coverage reports
- 🤖 AI-powered PR review comments
- 📈 Track documentation growth over time
- 🔔 Slack/Discord deployment notifications
- 🌍 Multi-language documentation support

---

**Last Updated:** 2026-06-24
