# CI/CD Pipeline Overview

This repository uses **GitHub Actions** for automated continuous integration and deployment.

## 🔄 Pipeline Stages

### 1. **Lint & Test** (Every commit)
- ✅ Run full pytest test suite
- ✅ Linting with Ruff
- ⏱️ ~3 minutes

### 2. **Deploy Documentation** (Main branch only)
- ✅ Build MkDocs site from `/docs` directory
- ✅ Deploy to GitHub Pages
- ⏱️ ~2 minutes

### 3. **Summary** (After all stages)
- ✅ Generate deployment summary
- ✅ Report pipeline status

## 🎯 Workflow Triggers

The pipeline runs automatically on:
- `push` to `main` branch
- `pull_request` to `main` branch
- Manual trigger via `workflow_dispatch`

## 📊 What Gets Deployed

- **Documentation Hub**: [docs/README.md](../docs/README.md)
- **4 Learning Sections**: 01-foundations through 04-multi-agent
- **Reference Materials**: AGENTMAP, Ecosystem Map, etc.
- **30+ Test Suites**: Full test coverage

## 🔗 Links

- **GitHub Pages**: https://pristley.github.io/ai-architecture-blueprints
- **Repository**: https://github.com/pristley/ai-architecture-blueprints
- **Actions Tab**: https://github.com/pristley/ai-architecture-blueprints/actions

## 📝 Recent Updates

- Simplified CI/CD pipeline from 368 lines to ~120 lines
- Updated file paths to reference new `/docs` structure
- Removed redundant documentation update scripts
- Consolidated multiple deployment jobs into single clean workflow

## ✨ Quick Reference

| Stage | Triggers | Duration |
|-------|----------|----------|
| Lint & Test | Every push/PR | ~3 min |
| Deploy | Main push only | ~2 min |
| **Total** | - | **~5 min** |

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
