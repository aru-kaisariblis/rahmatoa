import sqlite3
from datetime import datetime
from typing import List, Optional
import os

# Support environment variable for database path (for Heroku deployment)
DATABASE_PATH = os.getenv("DATABASE_PATH", "sessions/all/tasks.db")

class Database:
    """SQLite Database Manager untuk AI Agent"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._ensure_db_exists()
        self._init_tables()
    
    def _ensure_db_exists(self):
        """Pastikan folder database exists"""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
    
    def _get_connection(self):
        """Mendapatkan koneksi ke database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """Initialize database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabel untuk tasks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                subject TEXT NOT NULL,
                deadline TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                target_class TEXT DEFAULT 'ALL'
            )
        """)
        
        # Tabel untuk reminders
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                chat_id TEXT NOT NULL,
                reminder_time TIMESTAMP NOT NULL,
                message TEXT,
                is_sent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        
        # Tabel untuk user subjects (mata kuliah per user)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                chat_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, chat_id, subject)
            )
        """)
        
        # Tabel untuk pendataan mahasiswa (fitur tag-all)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                phone TEXT,
                chat_id TEXT,
                classes TEXT,
                PRIMARY KEY (phone, chat_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ===== TASK OPERATIONS =====
    def add_task(self, title: str, description: str, subject: str, deadline: datetime, 
                 chat_id: str, user_id: str, priority: str = "medium", target_class: str = "ALL") -> int:
        """Tambah task baru"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (title, description, subject, deadline, status, chat_id, user_id, priority, target_class)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)
        """, (title, description, subject, deadline, chat_id, user_id, priority, target_class))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return task_id
    
    def get_tasks_by_chat(self, chat_id: str, status: Optional[str] = None) -> List[dict]:
        """Ambil semua tasks untuk chat tertentu"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM tasks WHERE chat_id = ? AND status = ? ORDER BY deadline ASC", 
                         (chat_id, status))
        else:
            cursor.execute("SELECT * FROM tasks WHERE chat_id = ? ORDER BY deadline ASC", (chat_id,))
        
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tasks
    
    def get_tasks_by_subject(self, chat_id: str, subject: str) -> List[dict]:
        """Ambil tasks berdasarkan mata kuliah"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tasks WHERE chat_id = ? AND subject = ? ORDER BY deadline ASC", 
                      (chat_id, subject))
        
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tasks
    
    def get_task(self, task_id: int) -> Optional[dict]:
        """Ambil detail satu task berdasarkan ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
        
    def update_task(self, task_id: int, title: str = None, description: str = None, 
                    subject: str = None, deadline: datetime = None, 
                    priority: str = None, target_class: str = None) -> bool:
        """Update existing task secara dinamis"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        update_fields = []
        params = []
        
        if title is not None: update_fields.append("title = ?"); params.append(title)
        if description is not None: update_fields.append("description = ?"); params.append(description)
        if subject is not None: update_fields.append("subject = ?"); params.append(subject)
        if deadline is not None: update_fields.append("deadline = ?"); params.append(deadline)
        if priority is not None: update_fields.append("priority = ?"); params.append(priority)
        if target_class is not None: update_fields.append("target_class = ?"); params.append(target_class)
            
        if not update_fields:
            conn.close()
            return False
            
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(task_id)
        
        query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
        
        cursor.execute(query, params)
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected > 0
    
    def update_task_status(self, task_id: int, status: str):
        """Update status task"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                      (status, task_id))
        
        conn.commit()
        conn.close()
    
    def get_overdue_tasks(self, chat_id: str) -> List[dict]:
        """Ambil tasks yang sudah overdue"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM tasks 
            WHERE chat_id = ? AND status != 'completed' AND deadline < ?
            ORDER BY deadline ASC
        """, (chat_id, datetime.now()))
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tasks
    
    def delete_task(self, task_id: int):
        """Hapus task"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        
        conn.commit()
        conn.close()
    
    # ===== REMINDER OPERATIONS =====
    def add_reminder(self, task_id: int, chat_id: str, reminder_time: datetime, message: str = "") -> int:
        """Tambah reminder untuk task"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reminders (task_id, chat_id, reminder_time, message, is_sent)
            VALUES (?, ?, ?, ?, 0)
        """, (task_id, chat_id, reminder_time, message))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return reminder_id
        
    def delete_reminders_for_task(self, task_id: int):
        """Hapus semua reminder untuk suatu task sebelum diganti dengan yang baru"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
        conn.commit()
        conn.close()
    
    def get_pending_reminders(self) -> List[dict]:
        """Ambil reminders yang belum dikirim dan waktuya sudah tiba"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM reminders 
            WHERE is_sent = 0 AND reminder_time <= ?
            ORDER BY reminder_time ASC
        """, (datetime.now(),))
        
        reminders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return reminders
    
    def mark_reminder_sent(self, reminder_id: int):
        """Mark reminder as sent"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
        
        conn.commit()
        conn.close()
    
    # ===== SUBJECT OPERATIONS =====
    def add_subject(self, user_id: str, chat_id: str, subject: str):
        """Tambah mata kuliah"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO user_subjects (user_id, chat_id, subject)
                VALUES (?, ?, ?)
            """, (user_id, chat_id, subject))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Subject sudah ada
        finally:
            conn.close()
    
    def get_subjects(self, chat_id: str) -> List[str]:
        """Ambil semua mata kuliah dalam chat"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT subject FROM user_subjects WHERE chat_id = ?", (chat_id,))
        
        subjects = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return subjects

    # ===== STUDENT REGISTRATION OPERATIONS =====
    def register_student(self, phone: str, chat_id: str, classes: list):
        """Daftarkan mahasiswa ke kelas tertentu"""
        classes_str = ",".join(classes)
        conn = self._get_connection()
        conn.execute('INSERT OR REPLACE INTO students (phone, chat_id, classes) VALUES (?, ?, ?)',
                     (phone, chat_id, classes_str))
        conn.commit()
        conn.close()

    def get_mentions_for_task(self, task_id: int, chat_id: str) -> list:
        """Ambil daftar nomor HP mahasiswa untuk tag-all WAHA"""
        conn = self._get_connection()
        cursor = conn.execute('SELECT target_class FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if not row: return []
        
        target_classes = [c.strip() for c in row['target_class'].split(',')]
        mentions = []
        
        cursor = conn.execute('SELECT phone, classes FROM students WHERE chat_id = ?', (chat_id,))
        for student in cursor.fetchall():
            student_classes = [c.strip() for c in student['classes'].split(',')]
            if "ALL" in target_classes or "ALL" in student_classes or any(c in target_classes for c in student_classes):
                mentions.append(student['phone'])
                
        conn.close()
        return mentions
