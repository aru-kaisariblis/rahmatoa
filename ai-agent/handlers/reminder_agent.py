import re
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict
from utils.database import Database
from models.task import TaskStatus

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
        }
    
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
        """Handle: /add Judul | Mata Kuliah | Deadline (DD/MM/YYYY HH:MM) | Deskripsi (optional)
        
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
        
        deadline = self.parse_datetime(deadline_str)
        if not deadline:
            return f"❌ Format tanggal tidak valid! Gunakan: DD/MM/YYYY HH:MM\n\nContoh: 25/03/2026 23:59"
        
        if deadline < datetime.now():
            return "❌ Deadline tidak boleh di masa lalu!"
        
        priority = self.extract_priority(title + " " + description)
        
        try:
            task_id = self.db.add_task(
                title=title,
                description=description,
                subject=subject,
                deadline=deadline,
                chat_id=chat_id,
                user_id=user_id,
                priority=priority
            )
            
            # Tambah subject ke database
            self.db.add_subject(user_id, chat_id, subject)
            
            # Auto-create reminders: 1 hari sebelum, 1 jam sebelum
            one_day_before = deadline - timedelta(days=1)
            one_hour_before = deadline - timedelta(hours=1)
            
            if one_day_before > datetime.now():
                self.db.add_reminder(
                    task_id=task_id,
                    chat_id=chat_id,
                    reminder_time=one_day_before,
                    message=f"⏰ Reminder: {title} ({subject}) jatuh tempo dalam 1 hari!"
                )
            
            if one_hour_before > datetime.now():
                self.db.add_reminder(
                    task_id=task_id,
                    chat_id=chat_id,
                    reminder_time=one_hour_before,
                    message=f"⚠️ Alert: {title} ({subject}) jatuh tempo dalam 1 jam!"
                )
            
            deadline_format = deadline.strftime("%d/%m/%Y %H:%M")
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "🟡")
            
            return f"""✅ Task berhasil ditambahkan!

📋 Judul: {title}
📚 Mata Kuliah: {subject}
📅 Deadline: {deadline_format}
⚡ Priority: {priority_emoji} {priority}
🔔 Reminders otomatis sudah dibuat (1 hari & 1 jam sebelum deadline)

*ID Task: #{task_id}*"""
        
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def handle_list_tasks(self, args: str, chat_id: str, user_id: str) -> str:
        """Handle: /list atau /list [subject] atau /list [status]"""
        
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

8️⃣ `/help` - Tampilkan bantuan ini

⚡ *Features:*
✨ Reminders otomatis 1 hari & 1 jam sebelum deadline
📚 Kategorisasi per mata kuliah
🔔 Notifikasi deadline yang mendekati
🎯 Priority tags (high, medium, low)"""
    
    def process_command(self, message: str, chat_id: str, user_id: str) -> str:
        """Process incoming message dan return response"""
        
        command, args = self.parse_message(message)
        
        # Remove leading slash if present
        if command.startswith("/"):
            command = command[1:]
        
        handler = self.commands.get(command)
        
        if handler:
            return handler(args, chat_id, user_id)
        else:
            return f"""❌ Perintah tidak dikenal: '{command}'

Gunakan `/help` untuk melihat daftar perintah yang tersedia."""
