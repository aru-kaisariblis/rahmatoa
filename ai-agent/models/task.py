from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class TaskStatus(str, Enum):
    """Status tugas"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"

@dataclass
class Task:
    """Model untuk tugas kuliah"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    subject: str = ""  # Mata kuliah
    deadline: datetime = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    updated_at: datetime = None
    chat_id: str = ""  # ID grup/chat WhatsApp
    user_id: str = ""  # ID user yang membuat task
    priority: str = "medium"  # low, medium, high
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "priority": self.priority,
        }

@dataclass
class Reminder:
    """Model untuk reminder"""
    id: Optional[int] = None
    task_id: int = None
    chat_id: str = ""
    reminder_time: datetime = None  # Kapan reminder dikirim
    message: str = ""
    is_sent: bool = False
    created_at: datetime = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "chat_id": self.chat_id,
            "reminder_time": self.reminder_time.isoformat() if self.reminder_time else None,
            "message": self.message,
            "is_sent": self.is_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
