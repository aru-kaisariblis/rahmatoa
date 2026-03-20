# 🔗 WAHA Integration Guide

## 📌 Pendahuluan

Dokumen ini menjelaskan cara mengintegrasikan AI Reminder Agent dengan WAHA (WhatsApp HTTP API) sehingga bot dapat menerima pesan dari WhatsApp dan merespons dengan bantuan reminders.

## 🎯 Tujuan Integrasi

Setelah integrasi selesai:
- ✅ Bot akan menerima pesan dari WhatsApp group
- ✅ Bot akan memproses perintah reminders
- ✅ Bot akan mengirim reminder otomatis
- ✅ Bot akan memberikan status updates

## 📋 Prerequisites

1. ✅ WAHA bot sudah running di `http://localhost:3000`
2. ✅ AI Agent sudah running di `http://localhost:8001`
3. ✅ Bot sudah ditambahkan ke WhatsApp group
4. ✅ Environment variables sudah dikonfigurasi

## 🔧 Step-by-Step Integration

### Step 1: Verify WAHA is Running

Check apakah WAHA API accessible (dengan API Key):

```bash
curl http://localhost:3000/health \
  -H "X-API-Key: 7dde6a37742043d4b961c10ebd1d06d8"
```

Expected response:
```json
{"status":"running"}
```

**Atau di PowerShell:**
```powershell
curl http://localhost:3000/health `
  -H "X-API-Key: 7dde6a37742043d4b961c10ebd1d06d8"
```

### Step 2: Get Your Chat ID

Untuk setup webhook yang correct, kita perlu chat ID. Ada beberapa cara:

**Cara 1: Via WAHA Dashboard**
1. Buka http://localhost:3000 di browser
2. Login dengan credentials dari `.env`
3. Cari chat ID di session info

**Cara 2: Via API**
```bash
curl -X GET http://localhost:3000/api/sessions \
  -H "X-API-Key: 7dde6a37742043d4b961c10ebd1d06d8"
```

**Cara 3: Kirim test message ke group**
- Buka WhatsApp group yang ada bot-nya
- Kirim test message
- Check logs WAHA untuk melihat chat ID yang masuk

### Step 3: Configure Webhook URL

Edit `.env` di root project:

```env
# Add atau update ini:
WHATSAPP_HOOK_URL=http://localhost:8001/webhook
WHATSAPP_HOOK_EVENTS=message
```

Atau setup via WAHA API:

```bash
curl -X POST http://localhost:3000/api/webhooks \
  -H "X-API-Key: 7dde6a37742043d4b961c10ebd1d06d8" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "http://localhost:8001/webhook",
    "events": ["message"]
  }'
```

### Step 4: Restart WAHA

Restart WAHA bot untuk apply webhook configuration:

```bash
# Jika running di Docker
docker restart waha

# Atau matikan dan jalankan ulang
```

### Step 5: Test Integration

#### Manual Test via curl

```bash
# Simulate incoming message dari WAHA
curl -X POST http://localhost:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "session-default",
    "chatId": "120363215xxx@g.us",
    "fromId": "120363215xxx@c.us",
    "text": "/help",
    "senderName": "Test User"
  }'
```

#### Test melalui WhatsApp

1. Buka WhatsApp group yang ada bot-nya
2. Kirim pesan: `/help`
3. Bot seharusnya merespon dengan daftar commands

## 📱 Penggunaan dalam WhatsApp

Setelah integrasi berhasil, Anda bisa menggunakan AI Agent langsung di WhatsApp:

### Commands

```
/add Judul | Mata Kuliah | DD/MM/YYYY HH:MM | Deskripsi
/list [subject|status]
/done [task_id]
/delete [task_id]
/subject
/status
/overdue
/daftar [Nomor_HP] [Kelas]
/help
```

### Contoh Real Usage

```
User: /add Buat Laporan | Algoritma | 25/03/2026 23:59 | Laporan praktikum minggu ke-7
Bot:  ✅ Task berhasil ditambahkan!
      📋 Judul: Buat Laporan
      📚 Mata Kuliah: Algoritma
      📅 Deadline: 25/03/2026 23:59
      ⚡ Priority: 🔴 high
      🔔 Reminders otomatis sudah dibuat (1 hari & 1 jam sebelum deadline)
      ID Task: #1

User: /list
Bot:  📋 Daftar Tasks:
      
      ⏳ Buat Laporan
         📚 Algoritma | 🔴 high
         📅 25/03 23:59
         📝 Laporan praktikum minggu ke-7
         ID: #1

User: /status
Bot:  📊 Statistik Tasks:
      ⏳ Pending: 1
      🔄 In Progress: 0
      ✅ Completed: 0
      🔴 Overdue: 0
      📈 Total: 1
      ✨ Completion Rate: 0.0%
```

## 🔔 Automatic Reminders

Sistem reminders bekerja otomatis:

1. **Saat task dibuat**, 2 reminders otomatis dibuat:
   - ⏰ Reminder 1 hari sebelum deadline
   - ⚠️ Alert 1 jam sebelum deadline

2. **Setiap 60 detik**, AI Agent:
   - Check pending reminders di database
   - Kirim reminder jika sudah waktunya
   - Mark reminder as sent

3. **Reminders dikirim ke chat** dengan format:
   ```
   ⏰ Reminder: Buat Laporan (Algoritma) jatuh tempo dalam 1 hari!
   ⚠️ Alert: Buat Laporan (Algoritma) jatuh tempo dalam 1 jam!
   ```

## 🌐 Public Deployment (Optional)

Jika ingin bot accessible dari internet:

### Option 1: Ngrok (Development)

```bash
# Install ngrok
# Download dari https://ngrok.com

# Run ngrok
ngrok http 8001

# Copy public URL, contoh: https://xxxx-xxx-xxx-xxx.ngrok.io
```

Update webhook URL di WAHA:
```env
WHATSAPP_HOOK_URL=https://xxxx-xxx-xxx-xxx.ngrok.io/webhook
```

### Option 2: Production Server

1. Deploy AI Agent ke server (Heroku, AWS, Digital Ocean, etc)
2. Update webhook URL ke public URL
3. Setup SSL/TLS untuk HTTPS

Contoh Heroku:
```bash
# Deploy
git push heroku main

# WAHA webhook URL
WHATSAPP_HOOK_URL=https://your-app.herokuapp.com/webhook
```

## 🔍 Monitoring & Debugging

### Check WAHA Webhook Logs

```bash
# If running in Docker
docker logs waha | grep webhook

# Or check WAHA dashboard
curl http://localhost:3000/api/webhooks \
  -H "X-API-Key: 7dde6a37742043d4b961c10ebd1d06d8"
```

### Check AI Agent Logs

```bash
# Get output logs
python main.py 2>&1 | tee agent.log

# Or check specific log file
tail -f agent.log
```

### Test Webhook Endpoint

```bash
# Health check
curl http://localhost:8001/health

# Get stats
curl http://localhost:8001/stats/120363215xxx@g.us

# Get tasks
curl http://localhost:8001/tasks/120363215xxx@g.us

# Get pending reminders
curl http://localhost:8001/reminders/120363215xxx@g.us
```

## ⚠️ Troubleshooting

### Problem: Webhook URL tidak diterima

**Solution:**
- Pastikan AI Agent running
- Pastikan port 8001 accessible
- Check firewall rules
- Verify webhook URL format

### Problem: Pesan tidak diproses

**Solution:**
- Check WAHA logs untuk incoming messages
- Check AI Agent logs untuk errors
- Verify chat ID format (harus `xxx@g.us` untuk group)
- Test dengan script `test.py`

### Problem: Reminders tidak terkirim

**Solution:**
- Check database untuk reminders yang pending
- Verify WAHA API connection
- Check WAHA send message endpoint
- Look at AI Agent logs untuk errors

### Problem: Port 8001 already in use

**Solution:**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID [number] /F

# Linux/macOS
lsof -ti :8001 | xargs kill -9
```

## 📝 Quick Reference

| Component | Status | URL | Check |
|-----------|--------|-----|-------|
| WAHA API | ✅ | http://localhost:3000/health | `curl http://localhost:3000/health` |
| AI Agent | ✅ | http://localhost:8001/health | `curl http://localhost:8001/health` |
| Webhook | ✅ | http://localhost:8001/webhook | Send test message |

## 🎓 Learning Resources

- WAHA Documentation: https://waha.devlike.pro
- FastAPI Documentation: https://fastapi.tiangolo.com
- WhatsApp API Integration Patterns: https://developers.facebook.com/docs/whatsapp/cloud-api

## 📞 Support

Butuh bantuan?

1. Check logs di AI Agent dan WAHA
2. Baca dokumentasi README.md
3. Run test script: `python test.py`
4. Verify environment variables

---

**Last Updated:** March 20, 2026  
**Version:** 1.0.0
