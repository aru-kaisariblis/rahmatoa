import re
import os
import json
from datetime import datetime, timedelta
from typing import Tuple, Optional
from groq import Groq
from utils.database import Database

class ReminderAgent:
    """AI Agent untuk mengolah perintah reminder tugas kuliah"""
    
    def __init__(self, db: Database):
        self.db = db
        self.commands = {
            "add": self.handle_add_task,
            "list": self.handle_list_tasks,
            "done": self.handle_complete_task,
            "delete": self.handle_delete_task,
            "subject": self.handle_subject,
            "help": self.handle_help,
            "overdue": self.handle_overdue,
            "status": self.handle_task_status,
            "daftar": self.handle_daftar,
        }
        
        # Setup Groq Client
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        
        self.chat_history = {} # Untuk menyimpan memori percakapan
    
    def parse_message(self, message: str) -> Tuple[str, str]:
        """Parse perintah dari message"""
        parts = message.strip().split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        return command, args
    
    def parse_datetime(self, date_str: str) -> Optional[datetime]:
        """Parse string tanggal ke datetime
        Format: DD/MM/YYYY HH:MM atau DD/MM/YYYY
        """
        formats = [
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt
            except ValueError:
                continue
        
        return None
    
    def extract_priority(self, text: str) -> str:
        """Extract priority dari text (high, medium, low)"""
        text_lower = text.lower()
        if any(word in text_lower for word in ["urgent", "high", "penting"]):
            return "high"
        elif any(word in text_lower for word in ["low", "santai"]):
            return "low"
        return "medium"
    
    def handle_add_task(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /add Judul | Mata Kuliah | Deadline | Deskripsi | Target Class | Reminders
        
        Contoh: /add Buat Laporan | Algoritma | 25/03/2026 23:59 | Laporan praktikum minggu ke-7
        """
        if not args.strip():
            return "❌ Format tidak valid!\n\nPenggunaan: `/add Judul | Mata Kuliah | Deadline (DD/MM/YYYY HH:MM) | Deskripsi`\n\nContoh:\n`/add Buat Laporan | Algoritma | 25/03/2026 23:59 | Laporan praktikum`"
        
        parts = [p.strip() for p in args.split("|")]
        
        if len(parts) < 3:
            return "❌ Format tidak valid! Minimal butuh: Judul | Mata Kuliah | Deadline"
        
        title = parts[0]
        subject = parts[1]
        deadline_str = parts[2]
        description = parts[3] if len(parts) > 3 else ""
        target_class = parts[4] if len(parts) > 4 else "ALL"
        reminders_str = parts[5] if len(parts) > 5 else "1 day, 1 hour"
        
        deadline = self.parse_datetime(deadline_str)
        if not deadline:
            return f"❌ Format tanggal tidak valid! Gunakan: DD/MM/YYYY HH:MM\n\nContoh: 25/03/2026 23:59"
        
        if deadline < datetime.now():
            return "❌ Deadline tidak boleh di masa lalu!"
        
        priority = self.extract_priority(title + " " + description)
        
        try:
            # Pass target_class if add_task supports it
            try:
                task_id = self.db.add_task(title, description, subject, deadline, chat_id, user_id, priority, target_class)
            except TypeError:
                # Fallback if database.py is not updated yet
                task_id = self.db.add_task(title, description, subject, deadline, chat_id, user_id, priority)
            
            # Tambah subject ke database
            self.db.add_subject(user_id, chat_id, subject)
            
            # Parse custom reminders
            reminder_times = []
            if reminders_str:
                for rem in reminders_str.split(","):
                    rem = rem.strip().lower()
                    try:
                        num = int(re.search(r'\d+', rem).group())
                        if "day" in rem or "hari" in rem:
                            reminder_times.append((timedelta(days=num), f"{num} hari"))
                        elif "hour" in rem or "jam" in rem:
                            reminder_times.append((timedelta(hours=num), f"{num} jam"))
                        elif "minute" in rem or "menit" in rem:
                            reminder_times.append((timedelta(minutes=num), f"{num} menit"))
                    except:
                        pass
            
            # Fallback jika parsing LLM gagal
            if not reminder_times:
                reminder_times = [(timedelta(days=1), "1 hari"), (timedelta(hours=1), "1 jam")]
            
            created_reminders = []
            for td, label in reminder_times:
                rem_time = deadline - td
                if rem_time > datetime.now():
                    self.db.add_reminder(
                        task_id=task_id,
                        chat_id=chat_id,
                        reminder_time=rem_time,
                        message=f"⏰ Reminder: *{title}* ({subject}) untuk kelas *{target_class}* jatuh tempo dalam {label}!"
                    )
                    created_reminders.append(label)
                    
            # Tambahkan pengingat TEPAT saat deadline (Tenggat Waktu)
            if deadline > datetime.now():
                self.db.add_reminder(
                    task_id=task_id,
                    chat_id=chat_id,
                    reminder_time=deadline,
                    message=f"🚨 TENGGAT WAKTU TIBA! Tugas *{title}* ({subject}) untuk kelas *{target_class}* harus dikumpulkan SEKARANG!"
                )
                created_reminders.append("Saat deadline")
            
            deadline_format = deadline.strftime("%d/%m/%Y %H:%M")
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "🟡")
            
            # Ambil nomor mahasiswa yang terdaftar di kelas ini untuk di-tag
            mention_tags = ""
            if hasattr(self.db, 'get_mentions_for_task'):
                mentions_list = self.db.get_mentions_for_task(task_id, chat_id)
                if mentions_list:
                    mention_tags = " ".join([f"@{m.split('@')[0]}" for m in mentions_list if m])
            
            rems_text = ", ".join(created_reminders) if created_reminders else "Tidak ada"
            tag_info = f"🎯 Target Kelas: {target_class}"
            if mention_tags:
                tag_info += f"\n📢 Panggilan: {mention_tags}"
            
            return f"""✅ Task berhasil ditambahkan!

📋 Judul: {title}
📚 Mata Kuliah: {subject}
{tag_info}
📅 Deadline: {deadline_format}
⚡ Priority: {priority_emoji} {priority}
🔔 Jadwal Pengingat: {rems_text}

*ID Task: #{task_id}*"""
        
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def handle_list_tasks(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /list atau /list [subject] atau /list [status]"""

    def handle_daftar(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /daftar [Kelas MKW] [Kelas MKU]"""
        if not args.strip():
            return "❌ Format tidak valid!\n\nPenggunaan: `/daftar Kelas1, Kelas2`\nContoh: `/daftar MKW B, MKU A`"
            
        if ',' in args:
            classes = [c.strip().upper() for c in args.split(',')]
        else:
            classes = [c.strip().upper() for c in args.split()]
            
        try:
            if hasattr(self.db, 'register_student'):
                self.db.register_student(user_id, chat_id, classes)
                return f"✅ Berhasil mendaftar ke kelas: *{', '.join(classes)}*!\nKamu akan otomatis di-tag saat ada tugas untuk kelas tersebut."
            else:
                return "❌ Fitur pendataan kelas belum diaktifkan di database."
        except Exception as e:
            return f"❌ Error saat mendaftar: {str(e)}"
        
        filter_type = args.strip().lower() if args.strip() else None
        tasks = []
        
        if filter_type in ["pending", "in_progress", "done", "completed", "overdue"]:
            status_map = {
                "pending": "pending",
                "in_progress": "in_progress", 
                "done": "completed",
                "completed": "completed",
                "overdue": "overdue"
            }
            tasks = self.db.get_tasks_by_chat(chat_id, status_map.get(filter_type))
        elif filter_type:
            tasks = self.db.get_tasks_by_subject(chat_id, filter_type)
        else:
            tasks = self.db.get_tasks_by_chat(chat_id)
        
        if not tasks:
            return "📭 Tidak ada tasks"
        
        response = "📋 *Daftar Tasks:*\n\n"
        
        for task in tasks:
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "overdue": "🔴"
            }.get(task['status'], "❓")
            
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task['priority'], "🟡")
            
            deadline = datetime.fromisoformat(task['deadline'])
            deadline_str = deadline.strftime("%d/%m %H:%M")
            
            response += f"{status_emoji} *{task['title']}*\n"
            response += f"   📚 {task['subject']} | {priority_emoji} {task['priority']}\n"
            response += f"   📅 {deadline_str}\n"
            if task['description']:
                response += f"   📝 {task['description']}\n"
            response += f"   ID: #{task['id']}\n\n"
        
        return response
    
    def handle_complete_task(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /done [task_id]"""
        
        if not args.strip():
            return "❌ Gunakan: `/done [task_id]`\n\nContoh: `/done 1`"
        
        try:
            task_id = int(args.strip())
            self.db.update_task_status(task_id, "completed")
            return f"✅ Task #{task_id} ditandai selesai!"
        except ValueError:
            return "❌ Task ID harus berupa angka!"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def handle_delete_task(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /delete [task_id]"""
        
        if not args.strip():
            return "❌ Gunakan: `/delete [task_id]`"
        
        try:
            task_id = int(args.strip())
            self.db.delete_task(task_id)
            return f"🗑️ Task #{task_id} berhasil dihapus!"
        except ValueError:
            return "❌ Task ID harus berupa angka!"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def handle_subject(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /subject - tampilkan mata kuliah"""
        
        subjects = self.db.get_subjects(chat_id)
        
        if not subjects:
            return "📭 Tidak ada mata kuliah terdaftar"
        
        response = "📚 *Mata Kuliah:*\n\n"
        for i, subject in enumerate(subjects, 1):
            task_count = len(self.db.get_tasks_by_subject(chat_id, subject))
            response += f"{i}. {subject} ({task_count} tasks)\n"
        
        response += "\nGunakan `/list [subject]` untuk melihat tasks per mata kuliah"
        
        return response
    
    def handle_overdue(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /overdue - tampilkan tasks yang overdue"""
        
        tasks = self.db.get_overdue_tasks(chat_id)
        
        if not tasks:
            return "✅ Tidak ada tasks yang overdue"
        
        response = "🔴 *Tasks Overdue:*\n\n"
        
        for task in tasks:
            deadline = datetime.fromisoformat(task['deadline'])
            days_overdue = (datetime.now() - deadline).days
            
            response += f"⚠️ *{task['title']}*\n"
            response += f"   📚 {task['subject']}\n"
            response += f"   📅 Overdue {days_overdue} hari\n"
            response += f"   ID: #{task['id']}\n\n"
        
        return response
    
    def handle_task_status(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /status - tampilkan statistik tasks"""
        
        all_tasks = self.db.get_tasks_by_chat(chat_id)
        
        if not all_tasks:
            return "📭 Tidak ada tasks"
        
        pending = len([t for t in all_tasks if t['status'] == 'pending'])
        in_progress = len([t for t in all_tasks if t['status'] == 'in_progress'])
        completed = len([t for t in all_tasks if t['status'] == 'completed'])
        overdue = len([t for t in all_tasks if t['status'] == 'overdue'])
        
        total = len(all_tasks)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        return f"""📊 *Statistik Tasks:*

⏳ Pending: {pending}
🔄 In Progress: {in_progress}
✅ Completed: {completed}
🔴 Overdue: {overdue}

📈 Total: {total}
✨ Completion Rate: {completion_rate:.1f}%"""
    
    def handle_help(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /help - tampilkan bantuan"""
        
        return """🤖 *AI Reminder Agent - Bantuan*

📌 *Perintah Tersedia:*

1️⃣ `/add` - Tambah task baru
   Format: `/add Judul | Mata Kuliah | Deadline (DD/MM/YYYY HH:MM) | Deskripsi`
   Contoh: `/add Buat Laporan | Algoritma | 25/03/2026 23:59 | Laporan praktikum`

2️⃣ `/list` - Tampilkan semua tasks
   Opsi: `/list [subject]` atau `/list [status]`
   Status: pending, in_progress, done, overdue

3️⃣ `/done` - Tandai task selesai
   Format: `/done [task_id]`
   Contoh: `/done 1`

4️⃣ `/delete` - Hapus task
   Format: `/delete [task_id]`

5️⃣ `/subject` - Lihat mata kuliah terdaftar

6️⃣ `/overdue` - Lihat tasks yang overdue

7️⃣ `/status` - Lihat statistik tasks

8️⃣ `/daftar` - Daftar notifikasi kelas
   Contoh: `/daftar MKW1 MKU2`

9️⃣ `/help` - Tampilkan bantuan ini

⚡ *Features:*
✨ Reminders kustom & Tag-all mahasiswa per kelas
📚 Kategorisasi per mata kuliah
🔔 Notifikasi deadline yang mendekati
🎯 Priority tags (high, medium, low)"""

    def handle_llm_chat(self, user_text: str, chat_id: str, user_id: str) -> str:
        """Handle natural language menggunakan Groq API"""
        if not self.groq_client:
            return "❌ GROQ API Key belum di-setup di environment. Minta admin untuk menambahkan GROQ_API_KEY."
            
        chat_key = f"{chat_id}_{user_id}"
        if chat_key not in self.chat_history:
            self.chat_history[chat_key] = []
            
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        system_prompt = f"""Kamu adalah "Bot Akademik", asisten AI super asik, gaul, tapi cerdas ala mahasiswa Indonesia.
Waktu saat ini adalah: {current_time}

KONTEKS KELAS:
Terdapat berbagai macam kelas Mata Kuliah Wajib (MKW 1, MKW 2, MKW 3) dan berbagai macam kelas Mata Kuliah Umum (MKU 1, MKU 2).
Satu matkul bisa ditujukan untuk 1 kelas saja, atau digabung (misal: MKW 1 & MKW 2).

TUGAS KAMU:
1. Ngobrol layaknya teman seangkatan (pakai kata santai seperti bro, cuy, oke siap, dkk tapi tetap sopan). Jangan kaku kayak robot resmi. Gunakan emoji yang pas!
2. Jika user memberikan tugas, ekstrak 6 hal ini:
1. title (Judul/Nama Tugas)
2. subject (Nama Matkul)
3. deadline (Waktu pengumpulan, format WAJIB: DD/MM/YYYY HH:MM)
4. description (Detail tugas)
5. target_class (Tugas ini untuk anak kelas mana? Misal: ["MKW 1"], ["MKW 1", "MKW 2"], atau ["ALL"])
6. reminder_schedule (Kapan saja bot harus mengingatkan? Misal: ["1 hari sebelum", "2 jam sebelum"])

3. WAJIB tanyakan balik dengan santai jika info belum lengkap (misal: "Deadlinenya kapan nih bro biar bisa dicatet?").
4. Jika info sudah LENGKAP, set action menjadi "add_task". Jika masih kurang/hanya ngobrol, set "chat".

OUTPUT WAJIB DALAM FORMAT JSON SEPERTI INI SAJA (TANPA MARKDOWN):
{{
    "action": "chat" | "add_task",
    "response": "Balasan gaulmu untuk user",
    "title": "Judul tugas (jika add_task)",
    "subject": "Nama matkul (jika add_task)",
    "deadline": "DD/MM/YYYY HH:MM (jika add_task)",
    "description": "Deskripsi (jika add_task)",
    "target_class": ["MKW 1"],
    "reminder_schedule": ["1 day", "2 hours"]
}}"""

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.chat_history[chat_key])
        messages.append({"role": "user", "content": user_text})

        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
                temperature=0.65, # Sedikit dinaikkan agar bahasanya lebih bervariasi dan luwes
            )
            
            response_content = chat_completion.choices[0].message.content
            response_json = json.loads(response_content)
            
            # Simpan percakapan ke memori
            self.chat_history[chat_key].append({"role": "user", "content": user_text})
            self.chat_history[chat_key].append({"role": "assistant", "content": response_content})
            
            # Batasi memori maksimal 6 pesan terakhir agar hemat token API
            if len(self.chat_history[chat_key]) > 6:
                self.chat_history[chat_key] = self.chat_history[chat_key][-6:]
                
            action = response_json.get("action", "chat")
            reply_msg = response_json.get("response", "Oke!")
            
            if action == "add_task":
                # Jika Groq memutuskan data sudah lengkap, masukkan ke sistem /add existing
                title = response_json.get("title", "Tugas")
                subject = response_json.get("subject", "General")
                deadline_str = response_json.get("deadline", "")
                desc = response_json.get("description", "")
                
                tc_raw = response_json.get("target_class", ["ALL"])
                if isinstance(tc_raw, list):
                    target_class = ",".join([str(x) for x in tc_raw])
                else:
                    target_class = str(tc_raw)
                    
                rem_raw = response_json.get("reminder_schedule", ["1 day", "1 hour"])
                if isinstance(rem_raw, list):
                    reminders = ",".join([str(x) for x in rem_raw])
                else:
                    reminders = str(rem_raw)
                
                # Buat format command seperti yang diharapkan oleh handle_add_task
                fake_args = f"{title} | {subject} | {deadline_str} | {desc} | {target_class} | {reminders}"
                add_result = self.handle_add_task(fake_args, chat_id, user_id)
                
                return f"🤖 *Asisten AI:*\n{reply_msg}\n\n{add_result}"
            else:
                # Jika hanya ngobrol atau menanyakan detail yang kurang
                return f"🤖 *Asisten AI:*\n{reply_msg}"
                
        except Exception as e:
            return f"❌ Error saat memproses dengan LLM: {str(e)}"
    
    def process_command(self, message: str, chat_id: str, user_id: str) -> str:
        """Process incoming message dan return response"""
        
        # Cek apakah pesan diawali dengan "!" untuk masuk ke mode LLM
        if message.startswith("!"):
            user_text = message[1:].strip()
            if not user_text:
                return "Ya? Ada yang bisa dibantu? Ketik `!tugas matkul X besok` untuk mencatat tugas."
            return self.handle_llm_chat(user_text, chat_id, user_id)
            
        # Cek apakah pesan diawali command garis miring (/)
        if message.startswith("/"):
            command, args = self.parse_message(message)
            command = command[1:].lower() # Hapus slash
            
            handler = self.commands.get(command)
            if handler:
                return handler(args, chat_id, user_id)
            else:
                return f"❌ Perintah tidak dikenal: '/{command}'\n\nGunakan `/help` untuk daftar perintah."
                
        # Abaikan pesan biasa yang tidak diawali . atau / (Agar tidak spam di Grup)
        return ""
