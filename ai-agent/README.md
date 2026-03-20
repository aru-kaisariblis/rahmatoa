# 🤖 AI Reminder Agent - Dokumentasi

## 📋 Daftar Isi
1. [Pengenalan](#pengenalan)
2. [Instalasi](#instalasi)
3. [Konfigurasi](#konfigurasi)
4. [Menjalankan](#menjalankan)
5. [Perintah](#perintah)
6. [Contoh Penggunaan](#contoh-penggunaan)
7. [API Reference](#api-reference)

## 🎯 Pengenalan

AI Reminder Agent adalah sistem otomatis yang membantu Anda mengelola tugas-tugas kuliah melalui WhatsApp. Agent ini terintegrasi dengan WAHA (WhatsApp HTTP API) dan menyediakan features seperti:

✨ **Features:**
- ✅ Membuat, mengedit, dan menghapus tasks
- 🔔 Reminders otomatis (1 hari & 1 jam sebelum deadline)
- 📚 Kategorisasi per mata kuliah  
- 📊 Statistik dan tracking progress
- 🎯 Priority marking (high, medium, low)
- 📱 Akses melalui WhatsApp group chat

## 🚀 Instalasi

### Prerequisite
- Python 3.8+
- WhatsApp Hybrid Bot (wa-bot-hybrid) sudah berjalan
- WAHA API running di `http://localhost:3000`

### Setup

1. **Navigasi ke folder ai-agent:**
```bash
cd ai-agent
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Database akan otomatis dibuat di:**
```
sessions/all/tasks.db
```

## ⚙️ Konfigurasi

### Environment Variables

Tambahkan ke file `.env` di root project (atau di folder ai-agent):

```env
# WAHA Configuration
WAHA_BASE_URL=http://localhost:3000
WAHA_API_KEY=7dde6a37742043d4b961c10ebd1d06d8

# AI Agent Configuration
REMINDER_CHECK_INTERVAL=60  # Detik
AI_AGENT_PORT=8001          # Port untuk FastAPI
```

## 🏃 Menjalankan

### Start AI Agent

```bash
cd ai-agent
python main.py
```

atau dengan uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Output yang diharapkan:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete
🚀 AI Reminder Agent started!
```

## 📝 Perintah

### 1. `/add` - Tambah Task Baru

**Format:**
```
/add Judul | Mata Kuliah | Deadline (DD/MM/YYYY HH:MM) | Deskripsi (optional)
```

**Contoh:**
```
/add Buat Laporan | Algoritma | 25/03/2026 23:59 | Laporan praktikum minggu ke-7
```

**Features:**
- Format deadline fleksibel: `DD/MM/YYYY HH:MM` atau `DD/MM/YYYY`
- Priority otomatis terdeteksi dari kata kunci (urgent, penting, high = high priority)
- Reminders otomatis dibuat (1 hari & 1 jam sebelum deadline)

---

### 2. `/list` - Tampilkan Tasks

**Varian:**
```
/list                    # Tampilkan semua tasks
/list pending           # Tampilkan tasks yang pending
/list in_progress       # Tampilkan tasks yang sedang dikerjakan
/list done              # Tampilkan tasks yang selesai
/list overdue           # Tampilkan tasks yang overdue
/list [Nama Mata Kuliah] # Tampilkan tasks dari mata kuliah tertentu
```

**Contoh:**
```
/list Algoritma
/list pending
```

**Output:**
```
📋 *Daftar Tasks:*

⏳ *Buat Laporan*
   📚 Algoritma | 🔴 high
   📅 25/03 23:59
   📝 Laporan praktikum minggu ke-7
   ID: #1

✅ *Presentasi Project*
   📚 Database | 🟡 medium
   📅 20/04 10:00
   ID: #2
```

---

### 3. `/done` - Tandai Task Selesai

**Format:**
```
/done [task_id]
```

**Contoh:**
```
/done 1
```

---

### 4. `/delete` - Hapus Task

**Format:**
```
/delete [task_id]
```

**Contoh:**
```
/delete 5
```

---

### 5. `/subject` - Daftar Mata Kuliah

**Format:**
```
/subject
```

**Output:**
```
📚 *Mata Kuliah:*

1. Algoritma (5 tasks)
2. Database (3 tasks)
3. Web Development (7 tasks)
```

---

### 6. `/overdue` - Lihat Tasks yang Overdue

**Format:**
```
/overdue
```

**Output:**
```
🔴 *Tasks Overdue:*

⚠️ *Buat Laporan*
   📚 Algoritma
   📅 Overdue 3 hari
   ID: #1
```

---

### 7. `/status` - Lihat Statistik

**Format:**
```
/status
```

**Output:**
```
📊 *Statistik Tasks:*

⏳ Pending: 5
🔄 In Progress: 2
✅ Completed: 8
🔴 Overdue: 1

📈 Total: 16
✨ Completion Rate: 50.0%
```

---

### 8. `/help` - Bantuan

**Format:**
```
/help
```

Menampilkan daftar lengkap semua perintah.

## 📚 Contoh Penggunaan

### Skenario 1: Tambah beberapa tasks

```
User: /add Buat Laporan | Algoritma | 25/03/2026 23:59 | Laporan praktikum
Agent: ✅ Task berhasil ditambahkan!
       ID Task: #1

User: /add Study Chapter 5-8 | Database | 28/03/2026 14:00
Agent: ✅ Task berhasil ditambahkan!
       ID Task: #2

User: /list
Agent: 📋 *Daftar Tasks:*
       
       ⏳ *Buat Laporan*
          📚 Algoritma | 🔴 high
          📅 25/03 23:59
          ID: #1
       
       ⏳ *Study Chapter 5-8*
          📚 Database | 🟡 medium
          📅 28/03 14:00
          ID: #2
```

### Skenario 2: Track progress

```
User: /status
Agent: 📊 *Statistik Tasks:*
       
       ⏳ Pending: 8
       🔄 In Progress: 2
       ✅ Completed: 5
       🔴 Overdue: 1
       
       📈 Total: 16
       ✨ Completion Rate: 31.3%

User: /done 1
Agent: ✅ Task #1 ditandai selesai!

User: /status
Agent: 📊 *Statistik Tasks:*
       
       ⏳ Pending: 7
       🔄 In Progress: 2
       ✅ Completed: 6
       🔴 Overdue: 1
       
       📈 Total: 16
       ✨ Completion Rate: 37.5%
```

### Skenario 3: Filter by mata kuliah

```
User: /subject
Agent: 📚 *Mata Kuliah:*
       
       1. Algoritma (4 tasks)
       2. Database (3 tasks)
       3. Web (5 tasks)

User: /list Algoritma
Agent: 📋 *Daftar Tasks:*
       
       ⏳ *Buat Laporan* (#1)
       ⏳ *Study Chapter 5-8* (#2)
       ✅ *Present Project* (#3)
       🔴 *Final Exam Prep* (#4)
```

## 🔌 API Reference

### REST API Endpoints

#### 1. Health Check
```
GET /
GET /health
```

**Response:**
```json
{
  "status": "running",
  "service": "AI Reminder Agent",
  "version": "1.0.0"
}
```

---

#### 2. Get All Tasks
```
GET /tasks/{chat_id}
```

**Response:**
```json
{
  "chat_id": "120363xxx@g.us",
  "tasks": [
    {
      "id": 1,
      "title": "Buat Laporan",
      "subject": "Algoritma",
      "deadline": "2026-03-25T23:59:00",
      "status": "pending",
      "priority": "high"
    }
  ],
  "count": 1
}
```

---

#### 3. Get Reminders
```
GET /reminders/{chat_id}
```

**Response:**
```json
{
  "chat_id": "120363xxx@g.us",
  "reminders": [
    {
      "id": 1,
      "task_id": 1,
      "reminder_time": "2026-03-24T23:59:00",
      "message": "⏰ Reminder: Buat Laporan (Algoritma) jatuh tempo dalam 1 hari!",
      "is_sent": false
    }
  ],
  "count": 1
}
```

---

#### 4. Get Statistics
```
GET /stats/{chat_id}
```

**Response:**
```json
{
  "chat_id": "120363xxx@g.us",
  "total": 16,
  "pending": 7,
  "in_progress": 2,
  "completed": 6,
  "overdue": 1,
  "completion_rate": 37.5
}
```

---

#### 5. Webhook (Incoming Message)
```
POST /webhook

Content-Type: application/json

{
  "sessionId": "session-id",
  "chatId": "120363xxx@g.us",
  "fromId": "120363xxx@c.us",
  "text": "/add Buat Laporan | Algoritma | 25/03/2026 23:59",
  "senderName": "User Name"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Pesan diproses"
}
```

## 🔗 Integrasi dengan WAHA Bot

### 1. Configure WAHA Webhook

Di folder root, edit file konfigurasi atau environment:

```env
# .env
WHATSAPP_HOOK_URL=http://localhost:8001/webhook
WHATSAPP_HOOK_EVENTS=message
```

Restart WAHA service untuk mengupdate webhook configuration.

### 2. Test Webhook

Kirim pesan test dari WhatsApp:
```
/help
```

Jika setup benar, agent akan merespon dengan bantuan.

## 📁 Struktur File

```
ai-agent/
├── main.py                 # FastAPI Application
├── requirements.txt        # Dependencies
├── README.md              # Dokumentasi (file ini)
├── models/
│   ├── __init__.py
│   └── task.py            # Task dan Reminder models
├── handlers/
│   ├── __init__.py
│   └── reminder_agent.py   # AI Agent logic
└── utils/
    ├── __init__.py
    ├── database.py        # SQLite database manager
    └── __init__.py

sessions/all/
└── tasks.db              # SQLite database (auto-generated)
```

## 🔧 Troubleshooting

### Error: "Connection refused" ke WAHA API

**Solution:** Pastikan WAHA bot sudah berjalan di localhost:3000
```bash
# Check WAHA status
curl http://localhost:3000/health
```

### Database error: "database is locked"

**Solution:** Hanya satu instance FastAPI yang bisa berjalan. Stop instance lain:
```bash
# Kill process di port 8001
lsof -ti :8001 | xargs kill -9
```

### Reminders tidak terkirim

**Solution:** Check reminder check interval dan pastikan AI Agent berjalan
```bash
# Check logs
tail -f /tmp/ai-agent.log
```

## 📞 Support

Untuk questions atau issues, bisa hubungi atau cek logs di:
```
python main.py 2>&1 | tee ai-agent.log
```

---

**Last Updated:** March 20, 2026
**Version:** 1.0.0
