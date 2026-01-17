# Open Source Software Readiness Report
## Fiscaliza - Portuguese Parliament Data Platform

**Report Date:** 2026-01-17
**Repository:** https://github.com/rfsbraz/parliament
**Current Status:** ⚠️ **NOT READY FOR PUBLIC RELEASE**

---

## Executive Summary

The Fiscaliza project is a well-structured Portuguese Parliament data analysis platform with solid technical foundations. However, it currently has **critical security vulnerabilities** and missing legal/community infrastructure that must be addressed before public open source release.

**Overall Readiness Score: 3/10**

---

## 🚨 CRITICAL BLOCKERS (Must Fix Before Release)

### 1. Exposed Production Credentials ⛔ SEVERITY: CRITICAL
**File:** `.env.production` (lines 1-6)

**Issue:** Production database credentials are committed to the repository in plaintext:
```env
PG_HOST=fiscaliza-prod-postgres.ckubn9xqxngq.eu-west-1.rds.amazonaws.com
PG_USER=parluser
PG_PASSWORD=$XR=N!9yrx_t)32fiv(cA?qe<M_]t0pi
```

**Impact:**
- Anyone with repository access has full production database access
- Database could be compromised, data stolen, or deleted
- Credentials are in git history and cannot be removed without rewriting history

**Required Actions:**
1. **IMMEDIATELY** rotate database password
2. Remove `.env.production` from repository: `git rm --cached .env.production`
3. Add `.env.production` to `.gitignore` (currently missing despite patterns existing)
4. Rewrite git history to remove credentials OR make repository private until fixed
5. Use AWS Secrets Manager (already implemented in code) for credential management
6. Document environment variable setup in README

### 2. Hardcoded Application Secret Key 🔐 SEVERITY: HIGH
**File:** `config/settings.py` (line 26)

**Issue:** Flask SECRET_KEY is hardcoded:
```python
"SECRET_KEY": "asdf#FGSgvasgf$5$WGT",
```

**Impact:**
- Session hijacking vulnerabilities
- CSRF token prediction
- Security token forgery

**Required Actions:**
1. Replace with environment variable:
   ```python
   "SECRET_KEY": os.environ.get("SECRET_KEY", "dev-key-change-in-production"),
   ```
2. Document SECRET_KEY requirement in `.env.example`
3. Generate secure production key using: `python -c 'import secrets; print(secrets.token_hex(32))'`

### 3. Missing LICENSE File ⚖️ SEVERITY: BLOCKER
**Issue:** No LICENSE file exists in the repository

**Impact:**
- Repository is technically "all rights reserved" by default
- Others cannot legally use, modify, or distribute the code
- Not actually open source without a license

**Required Actions:**
Choose and add an appropriate license. Recommendations:
- **MIT License** - Permissive, allows commercial use (most common for open source)
- **Apache 2.0** - Permissive with patent protection
- **GPL v3** - Copyleft, requires derivatives to be open source
- **AGPL v3** - Copyleft including network use

README mentions "educational and research purposes" which suggests MIT or Apache 2.0.

---

## ⚠️ HIGH PRIORITY ISSUES

### 4. Missing Community Guidelines

**Missing Files:**
- `CONTRIBUTING.md` - How to contribute to the project
- `CODE_OF_CONDUCT.md` - Community standards and behavior expectations
- `SECURITY.md` - How to report security vulnerabilities
- `.github/ISSUE_TEMPLATE/` - Structured issue reporting
- `.github/PULL_REQUEST_TEMPLATE.md` - PR guidelines

**Impact:**
- Contributors don't know how to participate
- No clear security disclosure process
- Inconsistent contribution quality

**Recommended Actions:**
1. Create `CONTRIBUTING.md` with:
   - Development setup instructions
   - Code style guidelines
   - Testing requirements
   - PR submission process
   - Import data guidelines (from CLAUDE.md)

2. Add `CODE_OF_CONDUCT.md` (use Contributor Covenant template)

3. Create `SECURITY.md` with:
   - Security vulnerability reporting process
   - Expected response time
   - Disclosure policy

4. Add GitHub templates for issues and PRs

### 5. No Continuous Integration / Testing Automation

**Issue:** No CI/CD pipeline configured

**Current State:**
- Tests exist in `tests/` directory (9 test files)
- Simple test runner (`run_tests.py`)
- No automated test execution
- No automated security scanning
- No automated dependency updates

**Recommended Actions:**
1. Add GitHub Actions workflow (`.github/workflows/ci.yml`):
   - Run tests on PR/push
   - Lint code (flake8, black, pylint)
   - Security scanning (bandit, safety)
   - Frontend build verification
   - Dependency vulnerability scanning (Dependabot, Snyk)

2. Add pre-commit hooks:
   - Code formatting
   - Secret detection (git-secrets, detect-secrets)
   - Basic linting

### 6. Incomplete Documentation

**README.md Issues:**
- ✅ Good: Quick start, structure, development setup
- ❌ Missing:
  - Project goals and vision
  - Feature list
  - API documentation
  - Environment variables documentation
  - Database setup instructions
  - Production deployment guide (references DEPLOYMENT_GUIDE.md but needs integration)
  - Troubleshooting section
  - FAQ
  - Screenshots/demos

**Recommended Actions:**
1. Expand README with:
   - Project mission statement
   - Key features list
   - Environment variables table
   - Database migration instructions
   - Link to API documentation
   - Contributing section
   - License badge

2. Consolidate documentation:
   - Move technical details from CLAUDE.md to developer docs
   - Create `/docs` structure for detailed documentation
   - Add API documentation (OpenAPI/Swagger)

---

## 📋 MEDIUM PRIORITY ISSUES

### 7. Python Package Configuration

**Issue:** No modern Python packaging configuration

**Missing:**
- `pyproject.toml` (modern Python packaging standard)
- `setup.py` (legacy packaging)
- Package metadata (author, version, description)

**Impact:**
- Cannot install as a package (`pip install -e .`)
- No declared Python version requirements
- Dependency management is manual

**Recommended Actions:**
Create `pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "fiscaliza"
version = "1.0.0"
description = "Portuguese Parliament open data analysis platform"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}  # Choose appropriate license
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
dependencies = [
    # Import from requirements.txt
]

[project.urls]
Homepage = "https://fiscaliza.pt"
Repository = "https://github.com/rfsbraz/parliament"
Documentation = "https://github.com/rfsbraz/parliament/docs"
```

### 8. Dependency Management

**Current State:**
- `requirements.txt` exists with pinned versions
- No dependency groups (dev, test, prod)
- No vulnerability scanning
- No automated updates

**Dependencies Analysis:**
```
Flask==3.0.0           ✅ Recent (Nov 2023)
SQLAlchemy==2.0.23     ✅ Recent (Nov 2023)
psycopg2-binary==2.9.9 ✅ Recent (Oct 2023)
boto3==1.34.34         ⚠️  May need update (Jan 2024)
requests==2.31.0       ✅ Secure
beautifulsoup4==4.12.2 ✅ Recent
```

**Recommended Actions:**
1. Split dependencies:
   - `requirements.txt` - production dependencies
   - `requirements-dev.txt` - development tools (pytest, black, flake8)
   - `requirements-test.txt` - testing dependencies

2. Add dependency scanning:
   - Enable Dependabot in GitHub
   - Add `safety` checks in CI
   - Run `pip-audit` for vulnerability scanning

3. Consider poetry or pipenv for better dependency management

### 9. Configuration Management

**Issues:**
- `.env.example` exists ✅
- `.env.production` is tracked ❌ (CRITICAL)
- `frontend/.env.production` is tracked (OK - only has public URLs)
- Secret key hardcoded in `config/settings.py` ❌

**Recommended Actions:**
1. Document all environment variables in README
2. Create environment-specific example files:
   - `.env.example` (development)
   - `.env.production.example` (production template, NO SECRETS)
3. Add configuration validation on startup
4. Use environment variable prefixes (e.g., `FISCALIZA_*`)

### 10. Code Quality & Standards

**Current State:**
- 159 Python files
- 40 frontend components (React/JSX)
- No copyright headers
- No consistent code style enforcement
- No linting configuration

**Recommended Actions:**
1. Add code style configuration:
   - `.flake8` or `pyproject.toml` with flake8 config
   - `.prettierrc` for frontend
   - `.editorconfig` for consistent formatting

2. Add copyright headers template:
   ```python
   # Copyright (c) 2026 [Your Name/Organization]
   # Licensed under [LICENSE] - see LICENSE file for details
   ```

3. Add linting tools:
   - Backend: `black`, `flake8`, `pylint`, `mypy` (type checking)
   - Frontend: `eslint`, `prettier`

---

## 📊 POSITIVE ASPECTS

### ✅ Strong Foundation

1. **Well-Structured Codebase:**
   - Clear separation: `app/`, `database/`, `scripts/`, `frontend/`
   - Modular architecture with blueprints
   - Database migrations with Alembic

2. **Good Security Practices in Code:**
   - AWS Secrets Manager integration (`ops/database.py`, `database/connection.py`)
   - Environment variable usage for credentials
   - Proper password URL encoding
   - PostgreSQL SSL support

3. **Comprehensive .gitignore:**
   - Python artifacts covered
   - Node modules excluded
   - Secrets patterns defined
   - Build artifacts ignored
   - **Only issue:** `.env.production` not explicitly listed

4. **Testing Infrastructure:**
   - Unit tests exist (`tests/` directory)
   - Test runner implemented
   - Tests cover critical functionality (date parsing, data validation, boolean mapping)

5. **Documentation Exists:**
   - Multiple markdown files: CLAUDE.md, DEPLOYMENT_GUIDE.md, POLITICAL_RESEARCH_GUIDE.md
   - Architecture decisions documented
   - Data import processes detailed

6. **Modern Tech Stack:**
   - Flask 3.0 with SQLAlchemy 2.0
   - React 18 with Vite
   - PostgreSQL with Aurora Serverless support
   - Terraform infrastructure as code
   - Docker containerization

7. **Production-Ready Infrastructure:**
   - AWS deployment configuration
   - Terraform modules for ECS, RDS, Lambda
   - CloudFlare integration
   - Cost-optimized architecture

---

## 📝 OSS READINESS CHECKLIST

### 🚨 Critical (Must Have)
- [ ] **Remove production credentials from repository**
- [ ] **Rotate all exposed secrets**
- [ ] **Add LICENSE file**
- [ ] **Remove hardcoded SECRET_KEY**
- [ ] **Add `.env.production` to .gitignore**

### ⚠️ High Priority (Should Have)
- [ ] Add CONTRIBUTING.md
- [ ] Add CODE_OF_CONDUCT.md
- [ ] Add SECURITY.md
- [ ] Set up CI/CD (GitHub Actions)
- [ ] Expand README documentation
- [ ] Add environment variables documentation
- [ ] Create issue/PR templates

### 📋 Medium Priority (Nice to Have)
- [ ] Add pyproject.toml
- [ ] Split requirements files (dev/test/prod)
- [ ] Add pre-commit hooks
- [ ] Set up Dependabot
- [ ] Add code style enforcement (black, flake8, prettier)
- [ ] Add copyright headers
- [ ] Create API documentation (OpenAPI/Swagger)
- [ ] Add screenshots/demo to README
- [ ] Set up security scanning (Bandit, Safety)
- [ ] Add type hints and mypy checking

### 🎯 Long Term (Future Improvements)
- [ ] Increase test coverage
- [ ] Add integration tests
- [ ] Add end-to-end tests
- [ ] Set up code coverage reporting
- [ ] Create Docker Compose for local development
- [ ] Add changelog (CHANGELOG.md)
- [ ] Version releases with semantic versioning
- [ ] Create contribution guide for data importers
- [ ] Add multilingual documentation (Portuguese/English)
- [ ] Set up project website/documentation site

---

## 🎯 RECOMMENDED ACTION PLAN

### Phase 1: Security & Legal (Week 1) - IMMEDIATE
1. **Day 1:**
   - Rotate production database password
   - Remove `.env.production` from git
   - Make repository private until credentials removed

2. **Day 2:**
   - Fix hardcoded SECRET_KEY
   - Audit entire codebase for other secrets/credentials
   - Add secret scanning to prevent future commits

3. **Day 3:**
   - Choose and add LICENSE file
   - Add copyright headers to key files
   - Update README with license badge

### Phase 2: Community Infrastructure (Week 2)
1. Create CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md
2. Set up GitHub issue/PR templates
3. Expand README with comprehensive documentation
4. Document all environment variables

### Phase 3: Automation & Quality (Week 3)
1. Set up GitHub Actions CI/CD
2. Add code linting and formatting
3. Enable Dependabot
4. Add pre-commit hooks
5. Set up automated security scanning

### Phase 4: Polish & Release (Week 4)
1. Review and update all documentation
2. Test installation from scratch
3. Create release notes
4. Announce open source release
5. Monitor issues and respond to community

---

## 📚 RESOURCES

### License Choosers
- https://choosealicense.com/
- https://opensource.org/licenses

### GitHub Templates
- https://github.com/stevemao/github-issue-templates
- https://www.contributor-covenant.org/ (Code of Conduct)

### CI/CD Examples
- https://github.com/actions/starter-workflows
- https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python

### Python Packaging
- https://packaging.python.org/en/latest/tutorials/packaging-projects/
- https://peps.python.org/pep-0621/ (pyproject.toml spec)

### Security Tools
- `detect-secrets` - Prevent secret commits
- `bandit` - Python security scanner
- `safety` - Dependency vulnerability scanner
- `git-secrets` - AWS secret detection

---

## 🎓 CONCLUSION

The Fiscaliza project has strong technical foundations and significant potential as an open source project. However, **critical security vulnerabilities must be addressed immediately** before any public release.

**Primary Concerns:**
1. Production credentials in repository (CRITICAL - fix immediately)
2. Missing license (BLOCKER - cannot legally be used as OSS)
3. Hardcoded secrets (HIGH - security vulnerability)

**Estimated Timeline to OSS Readiness:** 3-4 weeks

With focused effort on security, legal compliance, and community infrastructure, this project can become a valuable open source contribution to government transparency efforts.

**Recommendation:** Address Phase 1 (Security & Legal) immediately, then proceed with community infrastructure before public announcement.

---

**Report Generated by:** OSS Readiness Review
**Contact:** For questions about this report or implementation guidance
