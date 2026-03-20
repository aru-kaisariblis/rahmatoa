# Azure Deployment Checklist

## Pre-Deployment (Do These Now)

- [ ] `.gitignore` created (secrets tidak ter-commit)
- [ ] `requirements.txt` updated
- [ ] `Procfile` created (web command)
- [ ] `runtime.txt` created (Python 3.11.8)
- [ ] `utils/database.py` use `DATABASE_PATH` env var
- [ ] All code tested locally

## Deployment Steps

### Phase 1: GitHub Setup
- [ ] Create GitHub repo `wa-bot-reminder`
- [ ] `git init` di folder ini
- [ ] `git add .`
- [ ] `git commit -m "Initial commit"`
- [ ] Push ke GitHub

### Phase 2: Azure Portal Setup
- [ ] Login ke https://portal.azure.com
- [ ] Create Resource Group: `wa-bot-reminder-rg`
- [ ] Create App Service:
  - [ ] Name: `wa-bot-reminder-app`
  - [ ] Runtime: Python 3.11
  - [ ] Region: Southeast Asia
- [ ] Link GitHub repo via Deployment Center
- [ ] Wait for first deployment (5-10 min)

### Phase 3: Configuration
- [ ] Go to App Service → Configuration
- [ ] Add Application Settings:
  - [ ] `WAHA_API_KEY`
  - [ ] `WAHA_BASE_URL`
  - [ ] `DATABASE_PATH = /tmp/tasks.db`
- [ ] Save + Restart app service

### Phase 4: WAHA Integration
- [ ] Get Azure app URL: `https://wa-bot-reminder-app.azurewebsites.net`
- [ ] Update WAHA webhook URL di dashboard
- [ ] Test webhook di WAHA
- [ ] Send test message dari WhatsApp

## Post-Deployment

- [ ] Check logs: App Service → Logs
- [ ] Verify webhook working
- [ ] Test all bot commands
- [ ] Monitor app performance

## Rollback
```bash
git revert HEAD~1
git push origin main
# Azure auto-redeploy ke previous version (~2 min)
```

---

**Status Check Command:**
```bash
az webapp show --resource-group wa-bot-reminder-rg --name wa-bot-reminder-app
```
