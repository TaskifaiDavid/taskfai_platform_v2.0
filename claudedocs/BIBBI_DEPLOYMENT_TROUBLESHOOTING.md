# BIBBI Auto-Deploy Troubleshooting

**Date**: 2025-10-29
**Issue**: BIBBI app not auto-deploying from master branch despite identical configuration to demo app

## Symptom

- **Demo app** (`taskifai-demo`): ✅ Auto-deployed commit `1b5d0c6`
- **BIBBI app** (`taskifai-bibbi`): ❌ Still on commit `17bb6de`
- **Configuration**: Both use same repo, master branch, auto-deploy enabled

## Timeline

1. **22:46** - Committed `1b5d0c6` (subdomain fix) to master branch
2. **22:46** - Pushed to GitHub origin/master
3. **Expected**: Both apps auto-deploy within 5-10 minutes
4. **Actual**: Demo deployed ✅, BIBBI did not ❌

## Possible Root Causes

### 1. GitHub Webhook Configuration

**Symptoms**:
- One app deploys, another doesn't
- Both apps configured identically

**Possible Issues**:
- BIBBI webhook disabled in GitHub repository settings
- Webhook secret mismatch between GitHub and DigitalOcean
- Webhook endpoint returning errors (check delivery logs)
- Webhook not configured to trigger on master branch

**Investigation Steps**:
```
GitHub Repo → Settings → Webhooks
→ Find DigitalOcean webhook for BIBBI
→ Check "Recent Deliveries" tab
→ Look for failed requests or error responses
```

**Expected Webhook URL**:
```
https://api.digitalocean.com/v2/apps/{BIBBI_APP_ID}/github/webhook
```

### 2. App-Specific Deployment Filters

**Symptoms**:
- App only deploys when specific files change
- Some commits trigger deploy, others don't

**Possible Configuration**:
```yaml
# In app spec or DO console
deploy_on_push:
  enabled: true
  paths:
    - backend/bibbi/**    # Only BIBBI-specific files
    - backend/app/bibbi/**
```

If configured, changes to `backend/app/api/uploads.py` wouldn't trigger BIBBI deploy.

**Investigation Steps**:
```
DigitalOcean Console
→ Apps → taskifai-bibbi
→ Settings → Source
→ Check "Deploy on Push" configuration
→ Look for path filters or ignored paths
```

### 3. Silent Build/Deployment Failure

**Symptoms**:
- Deployment started but failed
- No notification received
- App rolled back to previous version

**Possible Issues**:
- Build error specific to BIBBI configuration
- Environment variable missing or incorrect
- Health check failing after deployment
- Deployment timeout

**Investigation Steps**:
```
DigitalOcean Console
→ Apps → taskifai-bibbi
→ Activity tab
→ Check recent deployment attempts
→ Look for failed builds or cancelled deployments
```

### 4. Deployment Lock or Pause

**Symptoms**:
- Auto-deploy stops working suddenly
- Manual deployments still work

**Possible Issues**:
- Auto-deploy temporarily paused for maintenance
- Deployment schedule configured (e.g., deploy only during business hours)
- App in "paused" or "maintenance" mode

**Investigation Steps**:
```
DigitalOcean Console
→ Apps → taskifai-bibbi
→ Settings → General
→ Check if app is paused
→ Settings → Source → Check auto-deploy toggle
```

## Diagnostic Checklist

Run through this checklist to identify the issue:

- [ ] **Verify commit is on master**
  ```bash
  git log origin/master --oneline -1
  # Should show: 1b5d0c6 fix: correct BIBBI table selection...
  ```

- [ ] **Check GitHub webhook deliveries**
  - GitHub repo → Settings → Webhooks
  - Find DigitalOcean webhook URLs
  - Check "Recent Deliveries" for both demo and BIBBI
  - Compare success/failure status

- [ ] **Review DigitalOcean activity**
  - DO Console → Apps → taskifai-bibbi
  - Activity tab → Recent deployments
  - Look for attempted deployments around 22:46

- [ ] **Verify auto-deploy enabled**
  - DO Console → Apps → taskifai-bibbi
  - Settings → Source → "Deploy on Push" toggle
  - Should be ON

- [ ] **Check deployment filters**
  - DO Console → Apps → taskifai-bibbi
  - Settings → Source → Check for path filters
  - Should be empty or include `backend/app/**`

- [ ] **Compare with demo app**
  - Check demo app webhook configuration
  - Compare deployment settings
  - Identify any differences

## Solution: Merge PR to Trigger Fresh Deployment

**Current Status**: PR #41 created with the fix
**URL**: https://github.com/TaskifaiDavid/taskfai_platform_v2.0/pull/41

### Why This Should Work

1. **Different webhook event**: PR merge creates `push` + `pull_request` events
2. **Fresh deployment trigger**: New merge event may bypass whatever blocked the direct push
3. **Proven pattern**: Demo app deployed from direct push, merge is more reliable
4. **Metadata rich**: Merge events include PR context that might satisfy filters

### Steps to Resolve

1. **Merge PR #41** via GitHub UI
   - Go to: https://github.com/TaskifaiDavid/taskfai_platform_v2.0/pull/41
   - Review changes (should match commit `1b5d0c6`)
   - Click "Merge pull request"
   - Confirm merge

2. **Monitor deployment notifications**
   - Watch for DO deployment notification (email, Slack, or DO console)
   - Expected within 2-5 minutes of merge

3. **Check both apps**
   ```bash
   # Demo app (should stay on 1b5d0c6)
   curl -sS https://taskifai-demo.ondigitalocean.app/health | jq .version

   # BIBBI app (should deploy to new commit)
   curl -sS https://taskifai-bibbi-3lmi3.ondigitalocean.app/health | jq .version
   ```

4. **Test fixed endpoint**
   ```bash
   bash /tmp/test_uploads_endpoint.sh
   ```
   - Expected: `200 OK` with empty batches array

## If PR Merge Also Fails to Deploy BIBBI

Then we know it's a configuration issue specific to the BIBBI app:

### Manual Deployment Fallback

**Option 1: DigitalOcean Console**
```
1. Log in to DigitalOcean dashboard
2. Apps → taskifai-bibbi
3. Actions → "Create Deployment"
4. Confirm branch: master
5. Click "Deploy"
6. Wait 5-10 minutes
7. Test endpoint
```

**Option 2: DigitalOcean API** (requires token)
```bash
# Get BIBBI app ID
curl -H "Authorization: Bearer $DO_TOKEN" \
  'https://api.digitalocean.com/v2/apps' | \
  jq '.apps[] | select(.spec.name | contains("bibbi")) | .id'

# Trigger deployment
curl -X POST \
  -H "Authorization: Bearer $DO_TOKEN" \
  -H "Content-Type: application/json" \
  'https://api.digitalocean.com/v2/apps/{BIBBI_APP_ID}/deployments'
```

**Option 3: GitHub Actions Workflow Dispatch**
```bash
# If workflow configured for manual trigger
gh workflow run deploy-bibbi.yml
```

### Deep Investigation Required

If manual deployment also fails or succeeds but auto-deploy still broken:

1. **Contact DigitalOcean Support**
   - Provide app ID and webhook delivery logs
   - Request webhook configuration review
   - Ask about path-based deployment filters

2. **Review App Spec**
   ```bash
   # Export current app spec
   doctl apps spec get {BIBBI_APP_ID} > bibbi-app-spec.yaml

   # Look for:
   # - github.deploy_on_push configuration
   # - path filters or ignored_paths
   # - any conditional deployment rules
   ```

3. **Compare Working vs Broken**
   - Export demo app spec: `doctl apps spec get {DEMO_APP_ID}`
   - Diff against BIBBI spec
   - Identify configuration differences

4. **Webhook Re-registration**
   - Delete BIBBI webhook in GitHub
   - Re-add via DigitalOcean console
   - Test with dummy commit

## Prevention

Once resolved, document the root cause and add monitoring:

1. **Webhook Health Check**
   - Set up alerts for webhook delivery failures
   - Monitor GitHub webhook delivery success rate

2. **Deployment Notifications**
   - Configure Slack/email notifications for all deployments
   - Alert on failed or cancelled deployments

3. **Auto-Deploy Verification**
   - After any configuration change, test with dummy commit
   - Verify both demo and BIBBI deploy

4. **Documentation**
   - Document exact webhook configuration
   - Note any path filters or special rules
   - Keep app spec in version control

## Summary

**Most Likely Cause**: GitHub webhook misconfiguration or path-based filter
**Immediate Action**: Merge PR #41 to trigger fresh deployment
**Fallback**: Manual deployment via DigitalOcean console
**Long-term Fix**: Investigate and fix webhook/filter configuration

---

**Created**: 2025-10-29
**Status**: TROUBLESHOOTING IN PROGRESS
**Related**: BIBBI_UPLOADS_FIX_STATUS.md, PR #41
