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
                priority TEXT DEFAULT 'medium'
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
        
        conn.commit()
        conn.close()
    
    # ===== TASK OPERATIONS =====
    def add_task(self, title: str, description: str, subject: str, deadline: datetime, 
                 chat_id: str, user_id: str, priority: str = "medium") -> int:
        """Tambah task baru"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (title, description, subject, deadline, status, chat_id, user_id, priority)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
        """, (title, description, subject, deadline, chat_id, user_id, priority))
        
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
            WHERE chat_id = ? AND status != 'completed' AND deadline < CURRENT_TIMESTAMP
            ORDER BY deadline ASC
        """, (chat_id,))
        
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
    
    def get_pending_reminders(self) -> List[dict]:
        """Ambil reminders yang belum dikirim dan waktuya sudah tiba"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM reminders 
            WHERE is_sent = 0 AND reminder_time <= CURRENT_TIMESTAMP
            ORDER BY reminder_time ASC
        """)
        
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
