# 🚀 Quick Start Guide - AI Reminder Agent

## ⚡ Setup (5 menit)

### 1. Install Dependencies
```bash
cd ai-agent
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python setup.py
```

Atau manual:
```bash
python -c "from utils.database import Database; Database()"
```

### 3. Start AI Agent
```bash
# Windows
python run.py
# atau
run.bat

# Linux/macOS
python main.py
# atau
bash run.sh
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
🚀 AI Reminder Agent started!
```

---

## 📱 Test dalam WhatsApp

Kirim ke group chat tempat bot diadd:

```
/help
```

Jika setup benar, bot akan merespon dengan bantuan lengkap.

---

## 📝 Contoh Penggunaan

### Tambah Task
```
/add Buat Laporan | Algoritma | 25/03/2026 23:59 | Laporan praktikum
```

### Lihat Semua Tasks
```
/list
```

### Lihat Tasks Pending
```
/list pending
```

### Tandai Task Selesai
```
/done 1
```

### Lihat Statistik
```
/status
```

---

## 🔧 Troubleshooting

### Error: Connection refused (WAHA)
Pastikan WAHA bot sudah running:
```bash
curl http://localhost:3000/health
```

### Error: Port 8001 already in use
Matikan process yang pakai port 8001:
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID [PID] /F

# Linux/macOS
lsof -ti :8001 | xargs kill -9
```

### Database error
Cek file database ada di:
```
sessions/all/tasks.db
```

---

## 📚 Dokumentasi Lengkap

Baca [README.md](README.md) untuk:
- Daftar lengkap perintah
- Contoh penggunaan detail
- API Reference
- Troubleshooting advanced

---

## 🎯 Apa Selanjutnya?

1. ✅ Baca dokumentasi lengkap di README.md
2. ✅ Tambahkan tasks dan test semua features
3. ✅ Setup webhooks di WAHA dashboard jika diperlukan
4. ✅ Deploy ke server production (optional)

---

**Butuh bantuan?** Cek README.md atau logs dengan:
```bash
python main.py 2>&1 | tee agent.log
```

**Version:** 1.0.0  
**Last Updated:** March 20, 2026
