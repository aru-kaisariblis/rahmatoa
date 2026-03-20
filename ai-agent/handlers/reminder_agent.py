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
        """Handle: /daftar [Nomor] [Kelas]"""
        if not args.strip():
            return "❌ Format tidak valid!\n\nPenggunaan Wajib: `/daftar [Nomor_HP] Kelas1, Kelas2`\nContoh: `/daftar 628123456789 MKW B, MKU A`"
            
        # Cari nomor HP yang di-mention (@628...) atau diketik manual (628... / 08...)
        mentioned_numbers = re.findall(r'@(\d+)', args)
        manual_numbers = re.findall(r'\b(628\d{8,13}|08\d{8,13})\b', args)
        
        all_numbers = list(set(mentioned_numbers + manual_numbers))
        
        # Normalisasi format 08 menjadi 628
        normalized_numbers = []
        for num in all_numbers:
            if num.startswith('08'):
                normalized_numbers.append('62' + num[1:])
            else:
                normalized_numbers.append(num)
                
        if normalized_numbers:
            targets = [f"{num}@c.us" for num in normalized_numbers]
        else:
            return "❌ Nomor HP wajib disertakan!\n\nKarena aturan privasi WhatsApp, kamu *WAJIB* mengetik nomor HP aslimu saat mendaftar.\n\nContoh: `/daftar 628123456789 MKU B, MKW A`"
            
        # Gunakan regex untuk mencari pola kelas (case insensitive & kebal spasi/koma)
        matches = re.findall(r'(MKW|MKU)\s*([A-C])', args.upper())
        
        if not matches:
            return "❌ Format kelas tidak dikenali!\n\n*Pilihan kelas yang tersedia:*\n📚 MKW: A, B, atau C\n📚 MKU: A atau B\n\nContoh penggunaan: `/daftar mkw b, mku a`"
            
        classes = []
        for prefix, suffix in matches:
            if prefix == "MKU" and suffix not in ["A", "B"]:
                return f"❌ Pendaftaran gagal! Kelas *MKU {suffix}* tidak ada. MKU hanya sampai B."
            if prefix == "MKW" and suffix not in ["A", "B", "C"]:
                return f"❌ Pendaftaran gagal! Kelas *MKW {suffix}* tidak ada. MKW hanya sampai C."
            classes.append(f"{prefix} {suffix}")
            
        classes = list(set(classes)) # Hapus duplikat
            
        try:
            if hasattr(self.db, 'register_student'):
                registered_tags = []
                for target in targets:
                    self.db.register_student(target, chat_id, classes)
                    # Tampilkan nomor yang didaftarkan untuk konfirmasi
                    num_only = target.split('@')[0]
                    registered_tags.append(f"@{num_only}")
                
                tags_str = " ".join(registered_tags)
                return f"✅ Berhasil mendaftarkan nomor {tags_str} ke kelas: *{', '.join(classes)}*!\n\nNomor ini akan otomatis dipanggil saat ada tugas."
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

8️⃣ `/daftar` - Daftar notifikasi kelas (Wajib dengan nomor)
   Contoh: `/daftar 628123456789 MKW A, MKU B`

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
        
        system_prompt = f"""Kamu adalah "Bot Akademik", asisten AI super asik, gaul, tapi cerdas ala Gen-Z mahasiswa Indonesia.
Waktu saat ini adalah: {current_time}

KONTEKS KELAS:
Terdapat 3 kelas Mata Kuliah Wajib (MKW A, MKW B, MKW C) dan 2 kelas Mata Kuliah Umum (MKU A, MKU B).
Satu matkul bisa ditujukan untuk 1 kelas saja, atau digabung (misal: MKW A & MKW B).

TUGAS KAMU:
1. Ngobrol layaknya teman seangkatan (pakai kata santai bro, cuy, oke siap). Jangan kaku!
2. Pahami KEMAMPUAN-mu (ACTION) dan set pada JSON:
   - "add_task": Jika user minta buat tugas. Ekstrak: title, subject, deadline (DD/MM/YYYY HH:MM), description, target_class (misal ["MKW A"]), reminder_schedule (misal ["1 day"]). Tanyakan balik jika data penting belum lengkap!
   - "update_task": Jika user minta mengubah tugas yang sudah ada (tambah/ganti reminder, ganti deadline, judul, dll). Ekstrak: task_id, dan field yang diubah saja ke dalam object "updates" (opsi: title, subject, deadline, description, target_class, reminder_schedule).
   - "delete_task": Jika user minta hapus/batalkan tugas (ekstrak task_id).
   - "done_task": Jika user minta tandai tugas sudah dikerjakan/selesai (ekstrak task_id).
   - "list_tasks": Jika user minta lihat daftar tugas. Ekstrak filter (misal: "pending", "overdue", atau nama matkul).
   - "chat": Ngobrol biasa, atau beri tahu cara pakai command.
3. ATURAN COMMAND DAFTAR: Jika user nanya cara mendaftar ke bot, pastikan kamu memberi tahu mereka WAJIB menggunakan nomor HP. Contoh yang harus kamu sebutkan: "Ketik gini ya bro: /daftar 628123456789 MKU B"

OUTPUT WAJIB DALAM FORMAT JSON SEPERTI INI SAJA (TANPA MARKDOWN):
{{
    "action": "chat" | "add_task" | "update_task" | "delete_task" | "done_task" | "list_tasks",
    "response": "Balasan gaulmu untuk user",
    "title": "Judul tugas (jika add_task)",
    "subject": "Nama matkul (jika add_task)",
    "deadline": "DD/MM/YYYY HH:MM (jika add_task)",
    "description": "Deskripsi (jika add_task)",
    "target_class": ["MKW A"],
    "reminder_schedule": ["1 day", "2 hours"],
    "task_id": 1,
    "filter": "pending",
    "updates": {{
        "deadline": "25/03/2026 15:00",
        "reminder_schedule": ["30 minutes"]
    }}
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
            elif action == "update_task":
                task_id = response_json.get("task_id")
                updates = response_json.get("updates", {})
                if not task_id:
                    return f"🤖 *Asisten AI:*\n{reply_msg}\n\n❌ Error: Tolong sebutkan ID tugas yang mau diupdate ya bro."
                res = self.handle_update_from_llm(task_id, updates, chat_id, user_id)
                return f"🤖 *Asisten AI:*\n{reply_msg}\n\n{res}"
            elif action == "delete_task":
                task_id = response_json.get("task_id", "")
                res = self.handle_delete_task(str(task_id), chat_id, user_id)
                return f"🤖 *Asisten AI:*\n{reply_msg}\n\n{res}"
            elif action == "done_task":
                task_id = response_json.get("task_id", "")
                res = self.handle_complete_task(str(task_id), chat_id, user_id)
                return f"🤖 *Asisten AI:*\n{reply_msg}\n\n{res}"
            elif action == "list_tasks":
                filter_val = response_json.get("filter", "")
                res = self.handle_list_tasks(str(filter_val), chat_id, user_id)
                return f"🤖 *Asisten AI:*\n{reply_msg}\n\n{res}"
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

    def handle_update_from_llm(self, task_id, updates: dict, chat_id: str, user_id: str) -> str:
        """Handle update task dinamis dari LLM"""
        try:
            task_id = int(task_id)
        except (ValueError, TypeError):
            return "❌ Task ID tidak valid!"
            
        if not hasattr(self.db, 'get_task') or not hasattr(self.db, 'update_task'):
            return "❌ Fitur update belum diaktifkan di database."
            
        task = self.db.get_task(task_id)
        if not task:
            return f"❌ Tugas #{task_id} tidak ditemukan!"
            
        if str(task['chat_id']) != str(chat_id):
            return f"❌ Tugas #{task_id} tidak ada di dalam chat ini."
            
        new_title = updates.get("title", task['title'])
        new_desc = updates.get("description", task['description'])
        new_subj = updates.get("subject", task['subject'])
        new_target = updates.get("target_class", task['target_class'])
        
        if isinstance(new_target, list):
            new_target = ",".join([str(x) for x in new_target])
            
        new_deadline = task['deadline']
        deadline_updated = False
        if "deadline" in updates and updates["deadline"]:
            dl = self.parse_datetime(updates["deadline"])
            if dl:
                new_deadline = dl
                deadline_updated = True
        else:
            try:
                new_deadline = datetime.fromisoformat(new_deadline)
            except Exception:
                pass
                
        new_priority = self.extract_priority(f"{new_title} {new_desc}")
        
        self.db.update_task(task_id, title=new_title, description=new_desc,
                           subject=new_subj, deadline=new_deadline,
                           priority=new_priority, target_class=new_target)
                           
        rems_text = "Tetap seperti sebelumnya"
        if "reminder_schedule" in updates or deadline_updated:
            if hasattr(self.db, 'delete_reminders_for_task'):
                self.db.delete_reminders_for_task(task_id)
                
            rem_raw = updates.get("reminder_schedule", [])
            if not rem_raw and deadline_updated:
                rem_raw = ["1 day", "1 hour"]  # Fallback kalau ganti jam tapi gk minta reminder custom
                
            if rem_raw:
                reminders_str = ",".join([str(x) for x in rem_raw]) if isinstance(rem_raw, list) else str(rem_raw)
                
                reminder_times = []
                for rem in reminders_str.split(","):
                    rem = rem.strip().lower()
                    try:
                        num = int(re.search(r'\d+', rem).group())
                        if "day" in rem or "hari" in rem: reminder_times.append((timedelta(days=num), f"{num} hari"))
                        elif "hour" in rem or "jam" in rem: reminder_times.append((timedelta(hours=num), f"{num} jam"))
                        elif "minute" in rem or "menit" in rem: reminder_times.append((timedelta(minutes=num), f"{num} menit"))
                    except Exception:
                        pass
                        
                created_reminders = []
                if isinstance(new_deadline, datetime):
                    for td, label in reminder_times:
                        rem_time = new_deadline - td
                        if rem_time > datetime.now():
                            self.db.add_reminder(task_id, chat_id, rem_time, f"⏰ Reminder: *{new_title}* ({new_subj}) untuk kelas *{new_target}* jatuh tempo dalam {label}!")
                            created_reminders.append(label)
                            
                    if new_deadline > datetime.now():
                        self.db.add_reminder(task_id, chat_id, new_deadline, f"🚨 TENGGAT WAKTU TIBA! Tugas *{new_title}* ({new_subj}) untuk kelas *{new_target}* harus dikumpulkan SEKARANG!")
                        created_reminders.append("Saat deadline")
                        
                rems_text = ", ".join(created_reminders) if created_reminders else "Tidak ada"
            else:
                rems_text = "Tidak ada"
            
        deadline_format = new_deadline.strftime("%d/%m/%Y %H:%M") if isinstance(new_deadline, datetime) else new_deadline
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(new_priority, "🟡")
        
        return f"""🔄 Task berhasil diperbarui!

📋 Judul: {new_title}
📚 Mata Kuliah: {new_subj}
🎯 Target Kelas: {new_target}
📅 Deadline: {deadline_format}
⚡ Priority: {priority_emoji} {new_priority}
🔔 Jadwal Pengingat: {rems_text}

*ID Task: #{task_id}*"""
