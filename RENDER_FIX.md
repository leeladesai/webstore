# Fix: Render Not Detecting Start Command

## Problem
Render is not detecting the `startCommand` from `render.yaml`.

## Root Cause
Render only reads `render.yaml` when you create services via **Blueprint** (Infrastructure as Code). If you created the service manually, `render.yaml` is ignored.

## Solutions

### Solution 1: Use Blueprint (Recommended) ✅

**Steps:**
1. **Delete existing service** (if created manually):
   - Go to Render Dashboard → Your Service
   - Settings → Delete Service

2. **Create new Blueprint:**
   - Dashboard → **Blueprints** (left sidebar)
   - Click **New Blueprint**
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Click **Apply** or **Create Web Service**

3. **Verify:**
   - Check that `startCommand` appears in service settings
   - Should show: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Solution 2: Manually Set Start Command (Quick Fix)

If you want to keep your existing service:

1. **Go to your service in Render Dashboard**
2. **Settings → Environment**
3. **Scroll to "Start Command"**
4. **Enter:**
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. **Save Changes**
6. **Redeploy** (Manual Deploy → Deploy latest commit)

### Solution 3: Update Existing Service via Render API

If you have many services, you can update via API or Render CLI.

## Verification

After applying the fix, verify:

1. **Check Service Settings:**
   - Settings → Environment
   - Start Command should be visible

2. **Check Build Logs:**
   - Go to Logs tab
   - Look for: "Starting service with command: uvicorn app.main:app..."

3. **Test Deployment:**
   ```bash
   curl https://your-app.onrender.com/health
   ```

## Common Issues

### Issue: "No open ports detected"
- **Cause**: Start command not set or incorrect
- **Fix**: Ensure `startCommand` includes `--port $PORT`

### Issue: "Service crashes on start"
- **Cause**: Missing dependencies or wrong Python path
- **Fix**: Check build logs, ensure `requirements.txt` is correct

### Issue: "Build succeeds but service won't start"
- **Cause**: Wrong start command or missing app module
- **Fix**: Verify the command works locally:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```

## Current render.yaml Configuration

Your `render.yaml` is now correctly formatted:

```yaml
services:
  - type: web
    name: fastapi-webstore
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: WEBHOOK_SECRET
        sync: false
    plan: free
```

## Next Steps

1. ✅ Fixed `render.yaml` (removed circular PORT reference)
2. 🔄 Choose Solution 1 (Blueprint) or Solution 2 (Manual)
3. 🔄 Set `WEBHOOK_SECRET` environment variable
4. 🔄 Test deployment
5. 🔄 Verify all endpoints work

## Need Help?

- **Render Docs**: https://render.com/docs/blueprint-spec
- **Render Community**: https://community.render.com
- **Troubleshooting**: https://render.com/docs/troubleshooting-deploys

