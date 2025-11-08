# Render.com Deployment Guide

This guide will walk you through deploying the FastAPI Webstore application to Render.com using the `render.yaml` configuration file.

## Prerequisites

1. **GitHub Account**: Your code needs to be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com) (free tier available)
3. **Git Repository**: Ensure your code is pushed to GitHub

## Step-by-Step Deployment

### Step 1: Prepare Your Code

1. **Ensure your code is committed and pushed to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Verify `render.yaml` is in the root directory:**
   - The file should be at the root of your repository
   - Check that it's committed to git

### Step 2: Create a Render Account

1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account (recommended for easy repository access)
3. Verify your email address

### Step 3: Connect Your Repository

1. **In Render Dashboard:**
   - Click "New +" button
   - Select "Blueprint" (Infrastructure as Code)
   - Connect your GitHub account if not already connected
   - Select your repository: `fastapi_webstore`
   - Render will detect the `render.yaml` file automatically

2. **Alternative: Manual Setup**
   - If you prefer manual setup, select "Web Service" instead
   - Connect your repository
   - Render will still detect `render.yaml` if present

### Step 4: Review Configuration

Render will automatically read your `render.yaml` file. You should see:
- **Service Name**: `fastapi-webstore`
- **Environment**: `python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Plan**: `free`

### Step 5: Set Environment Variables

**IMPORTANT**: Before deploying, set the `WEBHOOK_SECRET` environment variable:

1. **Generate a secure secret:**
   ```bash
   openssl rand -hex 32
   ```
   Or use Python:
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

2. **In Render Dashboard:**
   - Go to your service settings
   - Navigate to "Environment" section
   - Click "Add Environment Variable"
   - Key: `WEBHOOK_SECRET`
   - Value: (paste your generated secret)
   - Click "Save Changes"

### Step 6: Deploy

1. **Click "Apply" or "Create Web Service"**
2. Render will:
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Build your application
   - Start the service
3. **Monitor the deployment logs:**
   - Watch for any build errors
   - Ensure the service starts successfully

### Step 7: Verify Deployment

1. **Get your service URL:**
   - Render provides a URL like: `https://fastapi-webstore.onrender.com`
   - Note: Free tier services spin down after 15 minutes of inactivity
   - First request after spin-down may take 30-60 seconds

2. **Test the deployment:**
   ```bash
   # Health check
   curl https://your-app.onrender.com/health
   
   # Root endpoint
   curl https://your-app.onrender.com/
   
   # API docs
   open https://your-app.onrender.com/docs
   ```

3. **Test API endpoints:**
   ```bash
   # Create a product
   curl -X POST https://your-app.onrender.com/products \
     -H "Content-Type: application/json" \
     -d '{"sku": "PROD-001", "name": "Test Product", "price": 99.99, "stock": 10}'
   
   # List products
   curl https://your-app.onrender.com/products
   ```

## Important Notes

### SQLite Limitations on Render

⚠️ **CRITICAL**: Your application uses SQLite, which has limitations on Render:

1. **Ephemeral Storage**: 
   - SQLite files are stored on the filesystem
   - Render's free tier uses ephemeral filesystems
   - Data will be **lost** when the service restarts or redeploys

2. **Concurrency**:
   - SQLite doesn't handle high concurrency well
   - Multiple simultaneous writes can cause errors

3. **Solutions**:
   - **For Development/Testing**: Current setup is fine
   - **For Production**: Migrate to PostgreSQL (see below)

### Free Tier Limitations

- **Spinning Down**: Services spin down after 15 minutes of inactivity
- **Cold Starts**: First request after spin-down takes 30-60 seconds
- **Build Time**: Limited build time (may need to upgrade for large apps)
- **Memory**: Limited RAM (512 MB)

### Upgrading to Production Plan

For production use:
1. Change `plan: free` to `plan: starter` in `render.yaml`
2. Add PostgreSQL database (see below)
3. Update `DATABASE_URL` environment variable

## Migrating to PostgreSQL (Production)

### Step 1: Add PostgreSQL Database

1. **In Render Dashboard:**
   - Click "New +" → "PostgreSQL"
   - Choose a name: `fastapi-webstore-db`
   - Select plan: `free` (or `starter` for production)
   - Create database

2. **Update `render.yaml`:**
   ```yaml
   services:
     - type: web
       name: fastapi-webstore
       # ... existing config ...
       envVars:
         - key: DATABASE_URL
           fromDatabase:
             name: fastapi-webstore-db
             property: connectionString
         # ... other env vars ...
     
     - type: pspg
       name: fastapi-webstore-db
       plan: free
       # For production: plan: starter
   ```

### Step 2: Update Database Configuration

Update `app/database.py`:
```python
import os
from sqlmodel import SQLModel, create_engine, Session

# Use DATABASE_URL from environment, fallback to SQLite for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./store.db")

# Handle PostgreSQL connection strings (Render provides postgres://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10)
```

### Step 3: Update Requirements

Add PostgreSQL driver to `requirements.txt`:
```
psycopg2-binary==2.9.9
```

### Step 4: Redeploy

1. Commit changes
2. Push to GitHub
3. Render will automatically redeploy

## Troubleshooting

### Build Failures

1. **Check build logs** in Render dashboard
2. **Common issues:**
   - Missing dependencies in `requirements.txt`
   - Python version incompatibility
   - Memory issues during build

### Runtime Errors

1. **Check service logs** in Render dashboard
2. **Common issues:**
   - Missing environment variables
   - Database connection errors
   - Port binding issues

### Service Not Starting

1. **Verify start command:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

2. **Check logs for:**
   - Import errors
   - Database initialization errors
   - Port conflicts

### Environment Variables Not Working

1. **Verify variable names** match exactly (case-sensitive)
2. **Restart service** after adding environment variables
3. **Check** that variables are marked as "Secret" if needed

## Testing After Deployment

### Using curl

```bash
# Set your Render URL
export RENDER_URL="https://your-app.onrender.com"

# Health check
curl $RENDER_URL/health

# Create product
curl -X POST $RENDER_URL/products \
  -H "Content-Type: application/json" \
  -d '{"sku": "PROD-001", "name": "Laptop", "price": 999.99, "stock": 50}'

# List products
curl $RENDER_URL/products

# Create order
curl -X POST $RENDER_URL/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'
```

### Using the Test Scripts

Update `BASE_URL` in your test scripts:
```bash
BASE_URL=https://your-app.onrender.com python tests/test_smoke.py
BASE_URL=https://your-app.onrender.com python tests/test_webhook.py
```

### Using Postman

1. Import `postman_collection.json`
2. Set `base_url` variable to your Render URL
3. Set `webhook_secret` variable
4. Run collection

## Continuous Deployment

Render automatically deploys when you push to your connected branch:
- **Default branch**: `main` or `master`
- **Auto-deploy**: Enabled by default
- **Manual deploy**: Available in dashboard

## Monitoring

1. **Logs**: View real-time logs in Render dashboard
2. **Metrics**: Monitor CPU, memory, and request metrics
3. **Alerts**: Set up email alerts for service failures

## Cost Estimation

- **Free Tier**: $0/month (with limitations)
- **Starter Plan**: $7/month per service
- **PostgreSQL Free**: $0/month (with limitations)
- **PostgreSQL Starter**: $7/month

## Next Steps

1. ✅ Deploy to Render
2. ✅ Test all endpoints
3. ✅ Set up monitoring
4. 🔄 Migrate to PostgreSQL (for production)
5. 🔄 Add custom domain (optional)
6. 🔄 Set up CI/CD (optional)
7. 🔄 Configure backups (for production)

## Support

- **Render Documentation**: [render.com/docs](https://render.com/docs)
- **Render Support**: [community.render.com](https://community.render.com)
- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

## Summary

Your `render.yaml` file is already configured for deployment. Simply:

1. Push code to GitHub
2. Connect repository to Render
3. Set `WEBHOOK_SECRET` environment variable
4. Deploy!

The service will be available at `https://fastapi-webstore.onrender.com` (or your custom URL).

⚠️ **Remember**: SQLite data will be lost on restarts. For production, migrate to PostgreSQL.

