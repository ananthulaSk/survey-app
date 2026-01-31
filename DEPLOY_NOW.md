# 🚀 IMMEDIATE DEPLOYMENT STEPS

## Current Issue
The code is pushed to GitHub, but **Cloud Run is still running the OLD version** without the `/surveys/assign` endpoint.

## Solution: Trigger Deployment

### Option 1: Wait for Auto-Deployment (Easiest)
If you have Cloud Build auto-deploy set up:
1. Check your Cloud Build history: https://console.cloud.google.com/cloud-build/builds
2. Wait for the build to complete (usually 3-5 minutes)
3. Check if it auto-deploys to Cloud Run

### Option 2: Manual Cloud Build Trigger
1. Go to: https://console.cloud.google.com/cloud-build/triggers
2. Find your trigger for `main` branch
3. Click "RUN" to manually trigger the build

### Option 3: Deploy from Command Line
Run this command (after enabling PowerShell scripts):

```powershell
# First, enable script execution (run PowerShell as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then deploy
gcloud run deploy survey-app `
  --image gcr.io/anvisurveyapp/survey-app:latest `
  --region asia-south1 `
  --set-env-vars BUILD_NUMBER=112 `
  --platform managed `
  --allow-unauthenticated
```

### Option 4: Deploy from Cloud Console (Simplest)
1. Go to: https://console.cloud.google.com/run
2. Click on `survey-app` service
3. Click "EDIT & DEPLOY NEW REVISION"
4. Under "Container" tab, click "SELECT" for the container image
5. Choose the most recent image (should be `survey-app:latest`)
6. Scroll to "Environment variables"
7. Add: `BUILD_NUMBER` = `112`
8. Click "DEPLOY"

## After Deployment

1. **Verify Backend Version**
   - Open: `https://survey-app-XXXXX.run.app/version`
   - Should show: `"version": "v20.112"`

2. **Test Assignment**
   - Open dashboard
   - Go to Assignments tab
   - Select survey
   - Click ➕ to assign surveyor
   - Should see: `{"status":"success","message":"Assigned successfully"}`

3. **Hard Refresh Frontend**
   - Press `Ctrl + Shift + R` to clear cache
   - Or open in Incognito mode

## What's Fixed in This Deployment

✅ `/surveys/assign` endpoint added with validation
✅ `/surveys/create` endpoint added with correct field mapping  
✅ `/surveys/active` endpoint added
✅ Legacy route aliases: `/assign`, `/unassign`, `/approvals`
✅ Auto-versioning with BUILD_NUMBER
✅ Transaction rollback protection

## If Still Not Working

Check the Cloud Run logs:
1. Go to: https://console.cloud.google.com/run
2. Click `survey-app`
3. Click "LOGS" tab
4. Look for any startup errors

Common issues:
- Database connection errors
- Missing environment variables
- Container build failures
