# Implementation Guide: GitHub Actions CI Optimization for AstraGuard-AI

## Overview

This guide explains how to migrate from the failing CI setup to the optimized workflow that fixes disk space exhaustion and improves pipeline speed.

## Key Changes

### 1. Workflow Strategy Change

**OLD:** Single `tests.yml` running 3-version Python matrix with full dependencies
**NEW:** Two-tier approach:
- Primary: Single Python 3.11 on every push (fast, gated)
- Extended: Python 3.9 & 3.12 only on PRs and develop branch (optional)

### 2. Dependency Installation Optimization

**OLD:**
```bash
pip install -r requirements.txt              # All 27 packages
pip install pytest pytest-cov ...            # Redundant, in requirements.txt
```

**NEW:**
```bash
# For linting/security jobs: minimal
pip install black flake8 mypy pylint        # ~50MB

# For testing: targeted
pip install -r requirements.txt              # Runtime deps (torch, etc.)
pip install -r requirements-test.txt         # Test-only deps (pytest, etc.)
```

### 3. Dependency Cleanup

**Before test suite:** Pip cache is cached by setup-python
**After test suite:** Explicit cleanup prevents cache bloat

```bash
pip cache purge
rm -rf ~/.cache/pip/*
```

## Migration Steps

### Step 1: Replace Workflow Files

1. **Backup current workflows:**
   ```bash
   cp .github/workflows/tests.yml .github/workflows/tests.yml.bak
   cp .github/workflows/ci-cd.yml .github/workflows/ci-cd.yml.bak
   ```

2. **Use optimized workflows:**
   ```bash
   # Option A: Replace completely (RECOMMENDED for fresh start)
   cp .github/workflows/tests-optimized.yml .github/workflows/tests.yml
   cp .github/workflows/ci-cd-optimized.yml .github/workflows/ci-cd.yml
   
   # Option B: Manual migration (see detailed sections below)
   ```

### Step 2: Update Dependency Files

1. **Verify requirements.txt** (updated with comments)
   - Already updated in this commit
   - Removed Streamlit/Altair (unused in backend)
   - Added production/dev markers

2. **Create requirements-test.txt** (new file)
   - Already created
   - ~20MB total, installs in <10s

3. **Update requirements-dev.txt** (reorganized)
   - Already updated
   - Removed heavy deps like Sphinx (optional now)
   - Kept only CI-required tools

### Step 3: Verify Locally

```bash
# Test the new workflow locally (recommended)

# Install main deps
pip install -r requirements.txt

# Install test deps
pip install -r requirements-test.txt

# Run tests
pytest tests/ -v --tb=short

# Run linting (quick check)
black --check anomaly classifier memory_engine state_machine
flake8 anomaly classifier memory_engine state_machine
```

### Step 4: Commit and Push

```bash
git add .github/workflows/tests.yml
git add .github/workflows/ci-cd.yml
git add requirements.txt
git add requirements-dev.txt
git add requirements-test.txt

git commit -m "ci: optimize GitHub Actions workflows for disk space constraints

- Split workflows: linting/security (minimal deps) vs testing (full stack)
- Change test matrix: Python 3.11 on every push, 3.9/3.12 only on PRs
- Add disk cleanup steps to prevent cache bloat
- Create requirements-test.txt for lightweight test-only installs
- Update requirements files with better organization and comments
- Expected improvement: 10+ min faster CI on main, reliable on ubuntu-latest"

git push origin main
```

## Validation

After migration, verify:

1. **First push to main:** Watch the GitHub Actions run
   - Should see ~8-10 min total (was 15+ min before)
   - No out-of-disk failures
   - All 3 jobs (lint, security, test) pass

2. **Pull request:** Verify test-matrix job runs (Python 3.9, 3.12)
   - Should be conditional based on PR trigger
   - Adds ~5 min for extended matrix

3. **Check coverage reports:** 
   - Codecov upload should work
   - HTML coverage report should appear in artifacts

## Rollback Plan

If issues occur:
```bash
git checkout .github/workflows/tests.yml.bak
git checkout .github/workflows/ci-cd.yml.bak
git push origin main
```

## Future Enhancements (Optional)

1. **Docker-based tests:** Pre-build test image with all deps
2. **Split integration tests:** Use docker-compose.ci.yml for optional jobs
3. **Matrix selective:** Only test pull requests on multiple Python versions
4. **Slack notifications:** Alert on CI failures

---

For questions or issues, refer to the debug context in this repository.
