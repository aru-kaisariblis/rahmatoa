# Azure App Service Deployment Guide

## Prerequisites
- Azure Account (with Student Credits)
- Git installed
- Azure CLI (optional, but helpful)

## Setup Steps

### 1. Create Resource Group & App Service (via Azure Portal)

1. Go to https://portal.azure.com
2. Click "Create a resource" → "App Service"
3. Fill in:
   - **Resource Group**: Create new `wa-bot-reminder-rg`
   - **Name**: `wa-bot-reminder-app` (must be unique)
   - **Publish**: Code
   - **Runtime stack**: Python 3.11
   - **Region**: Southeast Asia (or closest to you)
   - **App Service Plan**: Free (for testing) or B1 ($12/month)
4. Click "Create"

### 2. Setup Deployment from GitHub

1. In App Service → **Deployment Center**
2. Source: **GitHub**
3. Authorize GitHub
4. Select:
   - Organization: Your GitHub org
   - Repository: `wa-bot-reminder`
   - Branch: `main`
5. Click "Save"
6. Azure will auto-deploy on every git push!

### 3. Configure Environment Variables

In App Service → **Configuration** → **Application settings**

Add these:
```
WAHA_API_KEY = 7dde6a37742043d4b961c10ebd1d06d8
WAHA_BASE_URL = http://localhost:3000
DATABASE_PATH = /tmp/tasks.db
```

> **Tip**: Value dengan secrets sebaiknya pakai Azure Key Vault, bukan plain text!

### 4. Get Your Azure App URL

After deploy, app URL akan di: `https://wa-bot-reminder-app.azurewebsites.net/`

### 5. Update WAHA Webhook URL

Di WAHA Dashboard → **Webhooks**:
```
https://wa-bot-reminder-app.azurewebsites.net/webhook
```

## Troubleshooting

**Check deployment logs:**
- App Service → **Deployment slots** → **Logs**
- Or: `az webapp log tail --resource-group wa-bot-reminder-rg --name wa-bot-reminder-app`

**Database persistence issue:**
- App Service punya `/tmp` ephemeral storage
- Untuk production, gunakan Azure Database for PostgreSQL atau Cosmos DB
- Untuk testing, cukup `/tmp` aja

## Deploy Steps

```bash
# 1. Initialize Git (jika belum)
cd d:\Project]\wa-bot-hybrid
git init

# 2. Add all files (except .env)
git add .

# 3. Commit
git commit -m "Initial commit for Azure deployment"

# 4. Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/wa-bot-reminder.git
git branch -M main

# 5. Push (ini trigger auto-deploy ke Azure)
git push -u origin main
```

Done! ✅
