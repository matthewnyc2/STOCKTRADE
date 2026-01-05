# Architect 6 Context: Security & CI/CD

**Generated**: 2026-01-03
**Architect ID**: 6
**Feature**: Fix security vulnerabilities, clean up CI/CD configuration, remove artifacts
**Priority**: HIGH
**Complexity**: LOW

---

## Current State

### Backend Admin Security

**Issue**: Default SECRET_KEY in production code

**Location**: `api/auth.py`

**Current Code**:
```python
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
```

**Problem**:
- Default value allows application to start without SECRET_KEY
- Production deployments may use default (weak) key
- Security vulnerability: JWT tokens can be forged

### Frontend Admin Guards

**Issue**: ProtectedRoute exists but not used

**Location**: `frontend/src/components/ui/ProtectedRoute.tsx`

**Current State**:
- `ProtectedRoute` component exists
- Admin pages (`/admin/*`) NOT wrapped in ProtectedRoute
- Any user can navigate to admin pages (UI renders, API blocks data)

**Problem**:
- Confusing user experience (UI shows admin features, API returns 403)
- Security information disclosure (non-admins see admin UI)
- Poor UX

### CI/CD Configuration

**Issue 1**: Python 3.14 doesn't exist

**Location**: `.github/workflows/ci.yml`, `.github/workflows/contract-test.yml`

**Current Code**:
```yaml
python-version: '3.14'
```

**Problem**:
- Python 3.14 doesn't exist (3.13 is latest, 3.12 is stable LTS)
- CI pipeline fails immediately
- No automated testing

**Issue 2**: `continue-on-error: true` on critical steps

**Location**: `.github/workflows/ci.yml`

**Current Code**:
```yaml
- name: Run tests
  run: pytest tests/
  continue-on-error: true  # PROBLEM: Tests can fail but pipeline passes
```

**Problem**:
- Critical steps (tests, linting, security) can fail but pipeline passes
- No enforcement of code quality
- Tests can be broken undetected

### Tracked Artifacts

**Issue**: Tracked files that should be gitignored

**Files**:
- `nul` (Windows null device?)
- `=1.24.0` (package name fragment?)
- `C:Users/matt/AppData/Local/` (absolute path in Git?)

**Problem**:
- These files should not be tracked
- Clutter repository
- May contain sensitive data

### Tracked __pycache__

**Issue**: Python cache files tracked in Git

**Files**: `**/__pycache__/` directories tracked

**Problem**:
- `__pycache__` should be in .gitignore
- Unnecessary files in repository
- Conflicts across different Python versions

---

## Desired State

### Backend Admin Security

**Configuration**: SECRET_KEY must be provided via environment variable

**Code**:
```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        raise ValueError("SECRET_KEY must be set in production")
    else:
        SECRET_KEY = "dev-secret-key-change-in-production"  # Fallback for dev
```

**Behavior**:
- Production: SECRET_KEY required, raises ValueError if missing
- Development: Uses default only if ENVIRONMENT != production

### Frontend Admin Guards

**Configuration**: All admin pages wrapped in ProtectedRoute

**Code**:
```typescript
// frontend/src/app/admin/layout.tsx
import { ProtectedRoute } from '@/components/ui/ProtectedRoute'

export default function AdminLayout({ children }) {
  return (
    <ProtectedRoute>
      {children}
    </ProtectedRoute>
  )
}
```

**Behavior**:
- Non-admin users redirected to dashboard
- Admin pages inaccessible to unauthorized users
- Clear security boundary

### CI/CD Configuration

**Python Version**: Fixed to 3.12 (stable LTS)

**Code**:
```yaml
python-version: '3.12'
```

**continue-on-error**: Removed from critical steps

**Code**:
```yaml
- name: Run tests
  run: pytest tests/
  # continue-on-error: true  # REMOVED
```

**Behavior**:
- Tests, linting, security steps fail pipeline if they fail
- Enforced code quality
- Immediate feedback on broken code

### Clean Repository

**Artifacts Removed**:
- `nul` deleted
- `=1.24.0` deleted
- `C:Users/matt/AppData/Local/` deleted

**__pycache__ Untracked**:
- `__pycache__/` in .gitignore
- All `__pycache__` directories removed from Git tracking
- Clean repository

---

## Specific Tasks

### Task 1: Fix SECRET_KEY Validation
- Update `api/auth.py` to validate SECRET_KEY
- Add check for ENVIRONMENT == production
- Raise ValueError if SECRET_KEY missing in production
- Keep default for development only

### Task 2: Add ProtectedRoute to Admin Layout
- Import ProtectedRoute in `frontend/src/app/admin/layout.tsx`
- Wrap children in ProtectedRoute
- Test with non-admin user (should redirect)
- Test with admin user (should access)

### Task 3: Fix Python Version in CI/CD
- Update `.github/workflows/ci.yml`: Change `python-version: '3.14'` to `'3.12'`
- Update `.github/workflows/contract-test.yml`: Change `python-version: '3.14'` to `'3.12'`
- Verify Python 3.12 is available in GitHub Actions

### Task 4: Remove continue-on-error from Critical Steps
- Update `.github/workflows/ci.yml`: Remove `continue-on-error: true` from test steps
- Remove from lint steps
- Remove from security steps
- Keep for non-critical steps (optional: deploy notifications)

### Task 5: Delete Artifact Files
- Delete `nul` file from root directory
- Delete `=1.24.0` file from root directory
- Delete `C:Users/matt/AppData/Local/` directory from Git
- Verify files are deleted

### Task 6: Untrack __pycache__ Directories
- Verify `.gitignore` includes `**/__pycache__/`
- Run `git rm -r --cached .` to remove all cached files
- Run `git add .` to re-add with gitignore rules
- Verify no __pycache__ files in `git status`

### Task 7: Update Documentation
- Update `.env.example`: Mark SECRET_KEY as required
- Add comment: "REQUIRED for production"
- Update `README.md`: Document SECRET_KEY requirement
- Update `DEPLOYMENT.md`: Document SECRET_KEY configuration

### Task 8: Run CI/CD Pipeline
- Trigger GitHub Actions workflow manually
- Verify Python 3.12 installation succeeds
- Verify tests run and fail pipeline if broken
- Verify linting enforces code quality
- Verify security checks run

### Task 9: Test Admin Access Control
- Start development server
- Log in as non-admin user
- Navigate to `/admin/dashboard`
- Verify redirect to dashboard
- Log in as admin user
- Navigate to `/admin/dashboard`
- Verify access granted

### Task 10: Test SECRET_KEY Validation
- Test development mode: Start server without SECRET_KEY (should work with default)
- Test production mode: Set ENVIRONMENT=production, start without SECRET_KEY (should fail)
- Verify ValueError raised
- Verify error message is clear

---

## Critical Considerations

### SECRET_KEY Validation
- **CRITICAL**: Production must have SECRET_KEY set
- Development can use default (convenience)
- Error message must be clear
- Test both production and development modes

### Admin Route Protection
- **CRITICAL**: All admin pages must be protected
- Verify redirect works correctly
- Test with both admin and non-admin users
- Ensure API still blocks data requests (defense in depth)

### CI/CD Python Version
- Python 3.12 is stable LTS (long-term support)
- Verify all dependencies work with 3.12
- Check `requirements.txt` for version constraints
- No breaking changes expected

### continue-on-error Removal
- **CRITICAL**: Tests must fail pipeline if broken
- Linting must fail pipeline if errors
- Security checks must fail pipeline if vulnerabilities
- Enforces code quality

### Artifact Cleanup
- Verify no sensitive data in artifact files before deletion
- Backup important data if needed
- Confirm files are safe to delete
- Clean repository for future development

---

## Risk Areas

| Risk | Severity | Mitigation |
|------|-----------|------------|
| Production deployment without SECRET_KEY | HIGH | Validate SECRET_KEY, fail fast with clear error |
| Admin pages accessible to non-admins | MEDIUM | Test with both user roles, verify redirect |
| CI/CD pipeline always passes with broken tests | HIGH | Remove continue-on-error, test broken test scenario |
| Python 3.14 causes CI to fail | LOW | Change to 3.12, verify dependencies work |
| Deleting artifact files removes important data | LOW | Verify files are safe to delete, backup if needed |

---

## Success Criteria

### Backend Security
- [ ] SECRET_KEY validation implemented
- [ ] Production fails without SECRET_KEY
- [ ] Development uses default fallback
- [ ] Error messages are clear
- [ ] Documentation updated

### Frontend Security
- [ ] ProtectedRoute added to admin layout
- [ ] Non-admin users redirected to dashboard
- [ ] Admin users can access admin pages
- [ ] UI protection works correctly

### CI/CD Configuration
- [ ] Python version fixed to 3.12
- [ ] continue-on-error removed from critical steps
- [ ] Tests fail pipeline if broken
- [ ] Linting enforces code quality
- [ ] Security checks run correctly

### Repository Cleanup
- [ ] Artifact files deleted (nul, =1.24.0, C:Users/matt/AppData/Local/)
- [ ] __pycache__ untracked
- [ ] .gitignore includes __pycache__
- [ ] Repository is clean

### Tests
- [ ] CI/CD pipeline runs successfully
- [ ] Admin access control tested
- [ ] SECRET_KEY validation tested
- [ ] All tests pass

---

## Notes

- **DO NOT** deploy to production without SECRET_KEY
- **DO NOT** skip admin route protection testing
- **DO NOT** keep continue-on-error on critical steps
- **DO** verify Python 3.12 compatibility
- **DO** backup important data before deleting artifacts
- **DO NOT** delete __pycache__ from file system (only from Git)

---

## References

- Original analysis: `.phoenix/delta_breakdown.md` (Section 4)
- Risk assessment: `.phoenix/risk_assessment.md` (Sections 7, 8)
- Codebase knowledge: `AGENTS.md` (Security & CI/CD section)

---

## Handoff to Conductors

Each Task should spawn a Conductor with:
1. TEST_WRITER: Create test for the security fix
2. CODE_WRITER: Implement the fix (SECRET_KEY validation, ProtectedRoute, CI/CD config)
3. Regression Check: Run tests after each fix

**Order of Execution**: Tasks 1-2 (security) sequential, Tasks 3-4 (CI/CD) sequential, Tasks 5-6 (cleanup) sequential, Tasks 7-10 (verification) sequential
