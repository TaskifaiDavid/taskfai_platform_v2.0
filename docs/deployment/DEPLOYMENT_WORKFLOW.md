# Deployment Workflow Guide

**Last Updated**: October 20, 2025
**Status**: Manual approval workflow with branch protection

---

## 🏗️ Current Architecture

```
Developer → Feature Branch → Pull Request → Code Review → Merge to Master
                                               ↓
                                          Tests Pass ✅
                                               ↓
                                      ⏸️  DEPLOYMENT PAUSED
                                               ↓
                                   You manually click "Deploy"
                                               ↓
                            DigitalOcean builds and deploys
                                               ↓
                                    Live in Production ✅
```

### Deployment Configuration

| Component | Branch | Auto-Deploy | Manual Approval |
|-----------|--------|-------------|-----------------|
| Frontend (demo.taskifai.com) | master | ❌ Disabled | ✅ Required |
| Backend API + Worker | master | ❌ Disabled | ✅ Required |

**Key Points**:
- ✅ All code goes through PR review
- ✅ All tests must pass before merge
- ✅ Deployment happens only when you approve
- ✅ No automatic deployments to production

---

## 📋 Daily Development Workflow

### Step 1: Create Feature Branch

```bash
# Always start from up-to-date master
git checkout master
git pull origin master

# Create feature branch
git checkout -b feature/descriptive-name

# Examples:
# feature/add-liberty-processor
# feature/fix-date-filter
# feature/improve-dashboard-performance
```

### Step 2: Develop and Commit

```bash
# Make your changes
# ...

# Commit with conventional commits format
git add .
git commit -m "feat: add Liberty processor for BIBBI uploads"

# Commit message prefixes:
# feat: new feature
# fix: bug fix
# docs: documentation
# refactor: code refactoring
# test: test updates
# chore: maintenance tasks
```

### Step 3: Push Branch

```bash
git push origin feature/descriptive-name
```

### Step 4: Create Pull Request

1. Go to: https://github.com/TaskifaiDavid/taskfai_platform_v2.0/pulls
2. Click **"New pull request"**
3. Select:
   - Base: `master`
   - Compare: `feature/descriptive-name`
4. Fill in PR template:
   - **Title**: Clear description
   - **Description**: What changed and why
   - **Testing**: How you tested it
5. Click **"Create pull request"**

### Step 5: Wait for CI/CD Checks

GitHub Actions will automatically run:

```
✅ backend-tests (pytest)
✅ frontend-tests (npm test)
✅ security-scan (SAST)
⏳ docker-build (image creation)
```

**All must pass before merge is allowed.**

### Step 6: Code Review & Approval

- If solo developer: Review your own changes, then approve
- If team: Request review from teammate
- Address any feedback with new commits

**Required**: 1 approving review

### Step 7: Merge PR

Once approved and tests pass:

1. Click **"Merge pull request"**
2. Choose merge strategy:
   - **Merge commit** (default, recommended)
   - Squash and merge (cleaner history)
3. Click **"Confirm merge"**
4. Optionally delete the feature branch

**✅ Code is now in master, but NOT deployed yet**

### Step 8: Deploy to Production (Manual)

#### Option A: DigitalOcean Dashboard (Recommended)

**Backend + Worker Deployment**:
1. Login to DigitalOcean: https://cloud.digitalocean.com/apps
2. Select app: **taskifai-demo**
3. Click **"Deploy"** button (top right)
4. Confirm deployment
5. Wait 2-3 minutes for build + deploy
6. Verify: https://taskifai-demo-ak4kq.ondigitalocean.app/health

**Frontend Deployment**:
1. Select app: **taskifai-demo-frontend**
2. Click **"Deploy"** button
3. Confirm deployment
4. Wait 2-3 minutes for build + deploy
5. Verify: https://demo.taskifai.com

#### Option B: DigitalOcean CLI (Advanced)

```bash
# Install doctl if not already installed
# snap install doctl
# doctl auth init

# Deploy backend
doctl apps create-deployment ef090864-9e06-4a9a-96fb-276a047cf479

# Deploy frontend
doctl apps create-deployment 965ce42d-7cee-452e-9147-0b641b558449
```

---

## 🚨 Emergency Hotfix Procedure

For critical production bugs that need immediate fixes:

### Step 1: Create Hotfix Branch from Master

```bash
git checkout master
git pull origin master
git checkout -b hotfix/critical-bug-description
```

### Step 2: Fix the Issue

```bash
# Make minimal changes to fix the critical issue
git add .
git commit -m "fix: critical bug in authentication flow"
git push origin hotfix/critical-bug-description
```

### Step 3: Create Emergency PR

1. Create PR to master
2. Add label: **"🚨 HOTFIX"**
3. Request immediate review (or self-approve if solo)
4. Wait for tests (should be < 3 minutes)

### Step 4: Fast-Track Deployment

1. Merge PR immediately after tests pass
2. Deploy to production immediately via DigitalOcean
3. Monitor production logs for 10-15 minutes
4. **Document the incident** in GitHub Issues

---

## 🔄 Rollback Procedure

If a deployment causes issues in production:

### Method 1: DigitalOcean UI Rollback (Fastest)

1. Go to DigitalOcean app (taskifai-demo or taskifai-demo-frontend)
2. Click **"Deployments"** tab
3. Find the last working deployment
4. Click **"⋯"** (three dots) → **"Redeploy"**
5. Confirm rollback

**Deployment restores to previous version in 2-3 minutes**

### Method 2: Git Revert (Recommended for permanent fix)

```bash
# Find the problematic commit
git log --oneline

# Revert the commit
git revert <commit-hash>

# Push revert commit
git push origin master

# Deploy the revert
# (Follow normal deployment process)
```

### Method 3: Emergency Branch Protection Bypass

**⚠️ Use only in extreme emergencies**

1. Go to: https://github.com/TaskifaiDavid/taskfai_platform_v2.0/settings/branches
2. Click "Edit" on master protection rule
3. Uncheck **"Do not allow bypassing"**
4. Save changes
5. Push your emergency fix directly to master
6. **Re-enable protection immediately after**

---

## 📊 Monitoring After Deployment

### Check Application Health

```bash
# Backend health check
curl -sS https://taskifai-demo-ak4kq.ondigitalocean.app/health

# Should return: {"status": "healthy"}

# Frontend check
curl -sS https://demo.taskifai.com

# Should return HTML
```

### Check Logs in DigitalOcean

1. Go to app in DigitalOcean dashboard
2. Click **"Runtime Logs"** tab
3. Select component (demo-api or demo-worker)
4. Watch for errors in first 5 minutes after deployment

### Test Critical Paths

After deployment, manually test:
- ✅ Login flow
- ✅ File upload
- ✅ Dashboard load
- ✅ AI chat functionality

---

## 🎯 Deployment Checklist

Before deploying to production:

```markdown
- [ ] All tests pass in CI/CD
- [ ] Code review completed and approved
- [ ] No obvious console errors in local testing
- [ ] Database migrations tested (if any)
- [ ] Environment variables verified
- [ ] Deployment scheduled (avoid Friday evening!)
- [ ] Monitoring ready (have logs dashboard open)
- [ ] Rollback plan documented
```

---

## ⚙️ Configuration: Disable Auto-Deploy

**Important**: Auto-deploy should be disabled for production apps to require manual approval.

### Disable for Backend App

1. Go to: https://cloud.digitalocean.com/apps/ef090864-9e06-4a9a-96fb-276a047cf479/settings
2. Scroll to **"Source"** section
3. Click **"Edit"** (pencil icon)
4. **Uncheck**: "Autodeploy code changes"
5. Click **"Save"**

### Disable for Frontend App

1. Go to: https://cloud.digitalocean.com/apps/965ce42d-7cee-452e-9147-0b641b558449/settings
2. Scroll to **"Source"** section
3. Click **"Edit"**
4. **Uncheck**: "Autodeploy code changes"
5. Click **"Save"**

**Verification**: After disabling, push a commit to master. It should NOT trigger a deployment automatically.

---

## 📚 Related Documentation

- [Branch Protection Setup](./BRANCH_PROTECTION_SETUP_GUIDE.md) - GitHub protection rules
- [Contributing Guide](../../CONTRIBUTING.md) - Git workflow and standards
- [Infrastructure Setup](./01_Infrastructure_Setup.md) - DigitalOcean configuration
- [Deployment Checklist](./04_Deployment_Checklist_And_Troubleshooting.md) - Pre-deployment validation

---

## 🆘 Troubleshooting

### "I can't push to master"
**This is correct!** Branch protection is working. Create a feature branch and PR instead.

### "My PR can't be merged"
Check:
- ✅ Do you have 1 approval?
- ✅ Are all status checks passing?
- ✅ Is the branch up-to-date with master?

### "Tests are failing but I need to merge urgently"
Don't bypass tests! Fix the tests first. If it's truly an emergency:
1. Fix the failing tests
2. Use hotfix procedure with fast-track approval

### "Deployment failed in DigitalOcean"
1. Check build logs in DigitalOcean dashboard
2. Common issues:
   - Docker build errors (check Dockerfile)
   - Missing environment variables
   - Port conflicts
3. Rollback to previous version
4. Fix issue in a new PR

### "Production is down after deployment"
1. **Immediate**: Rollback via DigitalOcean UI
2. Check runtime logs for error messages
3. Create hotfix PR for the issue
4. Re-deploy after fix

---

## 📞 Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check [docs/](../README.md) directory
- **Deployment Issues**: Check DigitalOcean status page first

---

**Questions?** Open an issue or check the [Contributing Guide](../../CONTRIBUTING.md).
