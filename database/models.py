from datetime import datetime
import enum
from sqlalchemy import BigInteger, Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database.base import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

class TaskStatus(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, enum.Enum):
    URGENT = "urgent"    # 🔴
    NORMAL = "normal"    # 🟡
    LOW = "low"          # 🟢

class RecurringFrequency(str, enum.Enum):
    DAILY = "daily"      # Har kuni
    WEEKLY = "weekly"    # Har hafta
    MONTHLY = "monthly"  # Har oy

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), index=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    language = Column(String(10), default="uz", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GroupSettings(Base):
    __tablename__ = "group_settings"

    chat_id = Column(BigInteger, primary_key=True)
    title = Column(String(255), nullable=True)
    language = Column(String(10), default="uz", nullable=False)
    morning_report = Column(Boolean, default=True)
    evening_report = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    creator_id = Column(BigInteger, nullable=False)
    assignee_id = Column(BigInteger, nullable=True, index=True)
    assignee_username = Column(String(255), nullable=True, index=True)

    chat_id = Column(BigInteger, nullable=True, index=True)
    group_message_id = Column(BigInteger, nullable=True)

    status = Column(Enum(TaskStatus), default=TaskStatus.NEW, nullable=False, index=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.NORMAL, nullable=False)
    project = Column(String(255), nullable=True, index=True)

    due_date = Column(DateTime, nullable=True)

    # Hisobot va tekshiruv (Proof)
    proof_file_id = Column(String(255), nullable=True)
    proof_type = Column(String(50), nullable=True) # photo, video, document, text
    proof_text = Column(Text, nullable=True)
    reject_reason = Column(Text, nullable=True)

    # Eslatmalar yuborilganligi bayroqlari
    reminded_24h = Column(Boolean, default=False)
    reminded_2h = Column(Boolean, default=False)
    reminded_overdue = Column(Boolean, default=False)

    # Vaqtlar
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Aloqalar
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")

class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    user_name = Column(String(255), nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")

class TaskAttachment(Base):
    __tablename__ = "task_attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(String(255), nullable=False)
    file_unique_id = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="attachments")

class RecurringTask(Base):
    __tablename__ = "recurring_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    creator_id = Column(BigInteger, nullable=False)
    assignee_id = Column(BigInteger, nullable=True, index=True)
    assignee_username = Column(String(255), nullable=True)
    chat_id = Column(BigInteger, nullable=True)

    priority = Column(Enum(TaskPriority), default=TaskPriority.NORMAL, nullable=False)
    project = Column(String(255), nullable=True)

    frequency = Column(Enum(RecurringFrequency), default=RecurringFrequency.WEEKLY, nullable=False)
    day_of_week = Column(Integer, nullable=True) # 0=Dushanba, 6=Yakshanba
    day_of_month = Column(Integer, nullable=True) # 1..31
    time_str = Column(String(10), default="09:00", nullable=False) # HH:MM

    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

