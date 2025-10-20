# Branch Protection Setup Guide

**Repository**: TaskifaiDavid/taskfai_platform_v2.0
**Branch**: master
**Time Required**: 5 minutes

---

## Why Branch Protection?

Branch protection prevents:
- Direct pushes to master (all changes go through PR)
- Merging untested code
- Accidental force pushes or deletions
- Deploying broken code to production

---

## Step-by-Step Configuration

### Step 1: Navigate to Branch Protection Settings

1. Go to: https://github.com/TaskifaiDavid/taskfai_platform_v2.0/settings/branches
2. Click **"Add branch protection rule"** button

### Step 2: Branch Name Pattern

```
Branch name pattern: master
```

### Step 3: Configure Protection Rules

#### ✅ Protect matching branches
- Check: **"Require a pull request before merging"**
  - Number of approvals required: **1**
  - Check: **"Dismiss stale pull request approvals when new commits are pushed"**
  - Uncheck: "Require review from Code Owners" (unless you have CODEOWNERS file)

#### ✅ Status Checks
- Check: **"Require status checks to pass before merging"**
- Check: **"Require branches to be up to date before merging"**
- In the search box, type and select:
  - `backend-tests`
  - `frontend-tests`
  - `security-scan`

#### ✅ Additional Settings
- Check: **"Do not allow bypassing the above settings"**
  - This applies rules to administrators too
- Uncheck: "Restrict who can push to matching branches" (leave empty)
- Uncheck: "Allow force pushes"
- Uncheck: "Allow deletions"

### Step 4: Save Changes

Click **"Create"** or **"Save changes"** button at the bottom.

---

## Verification

### Test 1: Direct Push Blocked
```bash
# This should now be BLOCKED
git checkout master
echo "test" >> test.txt
git add test.txt
git commit -m "test"
git push origin master

# Expected: ERROR - protected branch hook declined
```

### Test 2: PR Required
```bash
# This is the correct workflow now
git checkout -b feature/test
echo "test" >> test.txt
git add test.txt
git commit -m "test"
git push origin feature/test

# Then create PR via GitHub UI
# PR will require 1 approval + passing tests before merge
```

---

## New Workflow After Protection

```
1. Create feature branch
   git checkout -b feature/my-feature

2. Make changes and commit
   git add .
   git commit -m "feat: description"

3. Push branch
   git push origin feature/my-feature

4. Create PR on GitHub
   Go to: https://github.com/TaskifaiDavid/taskfai_platform_v2.0/pulls
   Click "New pull request"
   Select: base: master ← compare: feature/my-feature

5. Wait for CI/CD checks
   backend-tests ✅
   frontend-tests ✅
   security-scan ✅

6. Request review or approve (if you have write access)

7. Merge PR
   Only possible after:
   - 1 approval ✅
   - All status checks pass ✅
   - Branch is up-to-date ✅

8. Deploy manually via DigitalOcean
   (See DEPLOYMENT_WORKFLOW.md)
```

---

## Troubleshooting

### "Status check not found"
If you can't find `backend-tests`, `frontend-tests`, or `security-scan` in the status check search:
- The checks must run at least once on master branch first
- Push any commit to master (before protection is active)
- GitHub will then recognize the check names
- Return to branch protection settings and add them

### "I can't merge my own PR"
This is correct! With branch protection:
- You need another person to approve (if team size > 1)
- Or you can approve your own PR if you're solo (GitHub allows this)
- Main protection is: tests must pass before merge

### "I need to push directly to master for emergency"
1. Go to: https://github.com/TaskifaiDavid/taskfai_platform_v2.0/settings/branches
2. Click "Edit" on master protection rule
3. Temporarily uncheck protection (not recommended)
4. Push your emergency fix
5. Re-enable protection immediately after

**Better approach**: Use hotfix branch → emergency PR → fast approval

---

## What's Protected Now?

✅ **Can't push directly to master**
✅ **Can't force push to master**
✅ **Can't delete master branch**
✅ **PRs require 1 approval**
✅ **PRs require passing tests (backend-tests, frontend-tests, security-scan)**
✅ **PRs must be up-to-date with master**
✅ **Rules apply to everyone (including admins)**

---

## Next Steps

After setting up branch protection:
1. ✅ Complete DigitalOcean auto-deploy disable (see Task 2)
2. ✅ Review DEPLOYMENT_WORKFLOW.md
3. ✅ Test the new PR workflow with a small change
4. ✅ Train team members on new workflow

---

**Questions?** See [DEPLOYMENT_WORKFLOW.md](./DEPLOYMENT_WORKFLOW.md) for complete deployment procedures.
