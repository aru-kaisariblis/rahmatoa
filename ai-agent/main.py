"""
AI Reminder Agent - Main FastAPI Application
Integrasi dengan WAHA (WhatsApp HTTP API)
"""

import re
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from datetime import datetime
import os
import sys
import asyncio
import aiohttp
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.database import Database
from handlers.reminder_agent import ReminderAgent

# ===== CONFIG =====
WAHA_API_URL = os.getenv("WAHA_BASE_URL", "http://localhost:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "7dde6a37742043d4b961c10ebd1d06d8")
REMINDER_CHECK_INTERVAL = 60  # Check untuk pending reminders setiap 60 detik

# ===== FASTAPI APP =====
app = FastAPI(
    title="AI Reminder Agent",
    description="AI Agent untuk reminder tugas kuliah yang terintegrasi dengan WhatsApp",
    version="1.0.0"
)

# ===== DATABASE =====
db = Database()
agent = ReminderAgent(db)

# ===== BACKGROUND TASKS =====
async def mark_chat_as_seen(chat_id: str):
    """Mark chat as seen di WhatsApp"""
    url = f"{WAHA_API_URL}/api/sendSeen"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": WAHA_API_KEY
    }
    
    payload = {
        "session": "default",
        "chatId": chat_id
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status in [200, 201]:
                    print(f"✅ Chat marked as seen: {chat_id}")
                else:
                    print(f"⚠️ Warning mark as seen: {response.status}")
    except Exception as e:
        print(f"⚠️ Warning: {str(e)}")

async def send_message_to_waha(chat_id: str, text: str, mentions: Optional[list] = None):
    """Kirim pesan ke WhatsApp melalui WAHA API"""
    # Mark as seen dulu
    await mark_chat_as_seen(chat_id)
    
    if mentions is None:
        mentions = []
        
    # Auto-extract nomor HP dari teks (misal: @628123456)
    extracted_numbers = re.findall(r'@(\d+)', text)
    for num in extracted_numbers:
        mentions.append(f"{num}@c.us")
        
    mentions = list(set(mentions)) # Hapus duplikat
    
    url = f"{WAHA_API_URL}/api/sendText"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": WAHA_API_KEY
    }
    
    payload = {
        "session": "default",
        "chatId": chat_id,
        "text": text
    }
    if mentions:
        payload["mentions"] = mentions
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status in [200, 201]:
                    print(f"✅ Pesan terkirim ke {chat_id}")
                else:
                    print(f"❌ Error mengirim pesan: {response.status}")
                    print(f"Response: {await response.text()}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

async def check_and_send_reminders():
    """Background task: Check pending reminders dan kirim"""
    while True:
        try:
            reminders = db.get_pending_reminders()
            
            for reminder in reminders:
                # Ambil mentions mahasiswa sesuai kelas tugas (jika ada fungsi get_mentions_for_task)
                mentions = getattr(db, 'get_mentions_for_task', lambda t, c: [])(reminder['task_id'], reminder['chat_id'])
                
                message_text = reminder['message']
                if mentions:
                    mention_tags = " ".join([f"@{m.split('@')[0]}" for m in mentions])
                    message_text += f"\n\n📢 Panggilan: {mention_tags}"
                
                await send_message_to_waha(
                    chat_id=reminder['chat_id'],
                    text=message_text,
                    mentions=mentions
                )
                db.mark_reminder_sent(reminder['id'])
                print(f"📤 Reminder #{reminder['id']} sent to {reminder['chat_id']}")
        
        except Exception as e:
            print(f"❌ Error in reminder check: {str(e)}")
        
        await asyncio.sleep(REMINDER_CHECK_INTERVAL)

# ===== ROUTES =====

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    asyncio.create_task(check_and_send_reminders())
    print("🚀 AI Reminder Agent started!")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "AI Reminder Agent",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "OK"}

@app.post("/webhook")
async def webhook_handler(payload: dict, background_tasks: BackgroundTasks):
    """
    Webhook endpoint untuk menerima pesan dari WAHA
    
    Endpoint ini dipanggil setiap kali ada pesan masuk di WhatsApp
    """
    try:
        # Deteksi format payload (WAHA Asli vs test.py)
        if "payload" in payload:
            # Payload asli dari WAHA
            if payload.get("event") != "message":
                return JSONResponse({"status": "ignored", "message": "Bukan event message"})
                
            waha_payload = payload.get("payload", {})
            
            # Abaikan pesan dari bot itu sendiri agar tidak lo
            if waha_payload.get("fromMe", False):
                print(f"⚠️ Pesan diabaikan karena dikirim oleh nomor bot itu sendiri.")
                return JSONResponse({"status": "ignored"})
                
            message = waha_payload.get("body", "")
            message = message.strip() if message else ""
            chat_id = waha_payload.get("from", "")
            
            # 1. Ambil dari field author atau participant
            user_id = waha_payload.get("author") or waha_payload.get("participant")
            # 2. Coba gali dari dalam field _data (Khas engine WebJS)
            if not user_id and isinstance(waha_payload.get("_data"), dict):
                user_id = waha_payload["_data"].get("author")
            # 3. Coba ekstrak dari string ID pesan (Kadang WAHA menyelipkan nomor di sini)
            if not user_id and isinstance(waha_payload.get("id"), str) and "@c.us" in waha_payload.get("id"):
                user_id = next((part for part in waha_payload["id"].split("_") if "@c.us" in part), None)
            # 4. Fallback terakhir ke chat_id (hanya cocok untuk private chat)
            if not user_id:
                user_id = chat_id
        else:
            # Payload custom dari test.py lokal
            message = payload.get("text", "").strip()
            chat_id = payload.get("chatId", "")
            user_id = payload.get("fromId", "")
            
        print(f"👀 Teks yang dibaca bot: '{message}'")

        if not message:
            return JSONResponse({"status": "ignored", "message": "Pesan kosong / bukan teks"})
        
        print(f"📨 Pesan diterima: {message} dari {user_id} di {chat_id}")
        
        # Proses perintah menggunakan AI Agent
        response = agent.process_command(message, chat_id, user_id)
        
        # Kirim response ke WhatsApp via WAHA
        if response: # Hanya kirim pesan jika bot memang ingin membalas
            background_tasks.add_task(send_message_to_waha, chat_id, response)
        
        return JSONResponse({
            "status": "success",
            "message": "Pesan diproses"
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        background_tasks.add_task(send_message_to_waha, chat_id, f"❌ Error: {str(e)}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

@app.get("/tasks/{chat_id}")
async def get_tasks(chat_id: str):
    """API untuk mendapatkan semua tasks dalam chat"""
    tasks = db.get_tasks_by_chat(chat_id)
    return {
        "chat_id": chat_id,
        "tasks": tasks,
        "count": len(tasks)
    }

@app.get("/reminders/{chat_id}")
async def get_reminders(chat_id: str):
    """API untuk mendapatkan semua reminders dalam chat"""
    all_reminders = db.get_pending_reminders()
    reminders = [r for r in all_reminders if r['chat_id'] == chat_id]
    return {
        "chat_id": chat_id,
        "reminders": reminders,
        "count": len(reminders)
    }

@app.get("/stats/{chat_id}")
async def get_stats(chat_id: str):
    """API untuk mendapatkan statistik tasks"""
    all_tasks = db.get_tasks_by_chat(chat_id)
    
    if not all_tasks:
        return {
            "chat_id": chat_id,
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "overdue": 0,
            "completion_rate": 0
        }
    
    pending = len([t for t in all_tasks if t['status'] == 'pending'])
    in_progress = len([t for t in all_tasks if t['status'] == 'in_progress'])
    completed = len([t for t in all_tasks if t['status'] == 'completed'])
    overdue = len([t for t in all_tasks if t['status'] == 'overdue'])
    
    total = len(all_tasks)
    completion_rate = (completed / total * 100) if total > 0 else 0
    
    return {
        "chat_id": chat_id,
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "completed": completed,
        "overdue": overdue,
        "completion_rate": round(completion_rate, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
