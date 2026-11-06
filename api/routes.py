from datetime import datetime
from typing import Optional, List
import pytz
from fastapi import APIRouter, Header, HTTPException, Query, Response
from pydantic import BaseModel

from config import settings
from database.base import AsyncSessionLocal
from database.models import TaskStatus, TaskPriority, UserRole, RecurringFrequency, Task
from database.crud import (
    get_or_create_user,
    get_user_by_id,
    get_all_users,
    update_user_role,
    create_task,
    get_task_by_id,
    get_all_projects,
    get_or_create_project,
    get_all_recurring_tasks,
    toggle_recurring_task,
    delete_recurring_task,
    get_team_statistics,
    get_task_comments,
    add_task_comment,
    get_task_attachments,
    get_task_attachment_count,
    get_all_tasks_for_export
)
from api.auth import verify_telegram_init_data
from utils.permissions import is_admin, can_create_task, can_manage_task
from services.exporter import generate_tasks_excel

router = APIRouter(prefix="/api")

# --- AUTH HELPER ---
async def get_current_user_from_header(init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")):
    # 1. Telegram WebApp orqali kelgan bo'lsa
    if init_data:
        data = verify_telegram_init_data(init_data)
        if data and "id" in data:
            async with AsyncSessionLocal() as session:
                user, _ = await get_or_create_user(
                    session=session,
                    telegram_id=data["id"],
                    full_name=f"{data.get('first_name', '')} {data.get('last_name', '')}".strip() or "Foydalanuvchi",
                    username=data.get("username")
                )
                return user

    # 2. Dev mode / Brauzerda test qilish uchun (fallback)
    async with AsyncSessionLocal() as session:
        users = await get_all_users(session)
        if users:
            # Birinchi admin yoki birinchi foydalanuvchini qaytaramiz
            admin_user = next((u for u in users if u.role == UserRole.ADMIN or u.telegram_id in settings.ADMIN_IDS), users[0])
            return admin_user

        # Agar bazada hech kim bo'lmasa, vaqtinchalik admin yaratamiz
        test_id = settings.ADMIN_IDS[0] if settings.ADMIN_IDS else 1001
        u, _ = await get_or_create_user(session, telegram_id=test_id, full_name="Bosh Admin", role=UserRole.ADMIN)
        return u

# --- SCHEMAS ---
class TaskCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: str = "normal"
    project: Optional[str] = None
    due_date: Optional[str] = None # ISO format

class StatusUpdateSchema(BaseModel):
    status: str

class CommentCreateSchema(BaseModel):
    comment: str

class RoleUpdateSchema(BaseModel):
    role: str

class ProjectCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None

# --- ENDPOINTS ---

@router.get("/auth/me")
async def get_me(init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")):
    user = await get_current_user_from_header(init_data)
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "username": user.username,
        "role": user.role.value,
        "language": user.language,
        "is_admin": user.role == UserRole.ADMIN or user.telegram_id in settings.ADMIN_IDS,
        "is_manager": user.role in (UserRole.ADMIN, UserRole.MANAGER) or user.telegram_id in settings.ADMIN_IDS,
    }

@router.get("/tasks")
async def get_tasks(
    project: Optional[str] = None,
    assignee_id: Optional[int] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
):
    current_user = await get_current_user_from_header(init_data)
    is_staff = current_user.role in (UserRole.ADMIN, UserRole.MANAGER) or current_user.telegram_id in settings.ADMIN_IDS

    async with AsyncSessionLocal() as session:
        all_tasks = await get_all_tasks_for_export(session)
        result = []
        tz = pytz.timezone(settings.TIMEZONE)

        for t in all_tasks:
            # Agar oddiy xodim bo'lsa — faqat o'ziga biriktirilgan vazifalarni ko'radi!
            if not is_staff and t.assignee_id != current_user.telegram_id:
                continue

            # Filtrlar
            if project and t.project != project:
                continue
            if assignee_id and t.assignee_id != assignee_id:
                continue
            if priority and t.priority.value != priority:
                continue
            if status and t.status.value != status:
                continue

            # Ijrochi nomi
            assignee_user = await get_user_by_id(session, t.assignee_id) if t.assignee_id else None
            assignee_name = assignee_user.full_name if assignee_user else (f"@{t.assignee_username}" if t.assignee_username else "Biriktirilmagan")

            # Fayllar soni
            att_count = await get_task_attachment_count(session, t.id)

            due_str = None
            if t.due_date:
                local_dt = pytz.utc.localize(t.due_date).astimezone(tz)
                due_str = local_dt.strftime("%d.%m.%Y %H:%M")

            result.append({
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "project": t.project,
                "priority": t.priority.value,
                "status": t.status.value,
                "assignee_id": t.assignee_id,
                "assignee_name": assignee_name,
                "due_date": due_str,
                "attachments_count": att_count,
                "reject_reason": t.reject_reason,
                "created_at": t.created_at.strftime("%d.%m %H:%M") if t.created_at else None
            })

        return result

@router.post("/tasks")
async def create_new_task(
    payload: TaskCreateSchema,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
):
    current_user = await get_current_user_from_header(init_data)
    is_staff = current_user.role in (UserRole.ADMIN, UserRole.MANAGER) or current_user.telegram_id in settings.ADMIN_IDS
    if not is_staff:
        raise HTTPException(status_code=403, detail="Vazifa yaratish uchun yetarli ruxsat yo'q.")

    async with AsyncSessionLocal() as session:
        # Muddatni o'qish
        due_dt = None
        if payload.due_date:
            try:
                clean_due = payload.due_date.replace("Z", "")
                naive_dt = datetime.fromisoformat(clean_due)
                tz = pytz.timezone(settings.TIMEZONE)
                local_dt = tz.localize(naive_dt)
                due_dt = local_dt.astimezone(pytz.utc).replace(tzinfo=None)
            except Exception:
                pass

        p_map = {
            "urgent": TaskPriority.URGENT,
            "normal": TaskPriority.NORMAL,
            "low": TaskPriority.LOW
        }
        priority = p_map.get(payload.priority.lower(), TaskPriority.NORMAL)

        assignee_user = await get_user_by_id(session, payload.assignee_id) if payload.assignee_id else None

        task = await create_task(
            session=session,
            title=payload.title,
            description=payload.description,
            creator_id=current_user.telegram_id,
            assignee_id=payload.assignee_id,
            assignee_username=assignee_user.username if assignee_user else None,
            priority=priority,
            project=payload.project,
            due_date=due_dt
        )
        return {"success": True, "task_id": task.id}

@router.put("/tasks/{task_id}/status")
async def update_task_status(
    task_id: int,
    payload: StatusUpdateSchema,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
):
    current_user = await get_current_user_from_header(init_data)

    status_map = {
        "new": TaskStatus.NEW,
        "in_progress": TaskStatus.IN_PROGRESS,
        "review": TaskStatus.REVIEW,
        "completed": TaskStatus.COMPLETED,
        "cancelled": TaskStatus.CANCELLED
    }
    new_status = status_map.get(payload.status.lower())
    if not new_status:
        raise HTTPException(status_code=400, detail="Noto'g'ri holat!")

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Vazifa topilmadi!")

        # Ruxsat tekshirish
        is_staff = current_user.role in (UserRole.ADMIN, UserRole.MANAGER) or current_user.telegram_id in settings.ADMIN_IDS
        is_assignee = task.assignee_id == current_user.telegram_id

        if not (is_staff or is_assignee):
            raise HTTPException(status_code=403, detail="Ruxsat berilmagan!")

        task.status = new_status
        if new_status == TaskStatus.IN_PROGRESS and not task.started_at:
            task.started_at = datetime.utcnow()
        elif new_status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.utcnow()

        await session.commit()
        return {"success": True, "status": new_status.value}

@router.get("/tasks/{task_id}")
async def get_task_details(
    task_id: int,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
):
    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Vazifa topilmadi!")

        tz = pytz.timezone(settings.TIMEZONE)
        due_str = None
        if task.due_date:
            local_dt = pytz.utc.localize(task.due_date).astimezone(tz)
            due_str = local_dt.strftime("%d.%m.%Y %H:%M")

        assignee = await get_user_by_id(session, task.assignee_id) if task.assignee_id else None
        creator = await get_user_by_id(session, task.creator_id) if task.creator_id else None

        comments = await get_task_comments(session, task_id)
        attachments = await get_task_attachments(session, task_id)

        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "project": task.project,
            "priority": task.priority.value,
            "status": task.status.value,
            "due_date": due_str,
            "assignee": assignee.full_name if assignee else (f"@{task.assignee_username}" if task.assignee_username else "—"),
            "creator": creator.full_name if creator else "Admin",
            "proof_text": task.proof_text,
            "reject_reason": task.reject_reason,
            "comments": [
                {
                    "id": c.id,
                    "author": c.user_name,
                    "text": c.comment,
                    "time": c.created_at.strftime("%d.%m %H:%M")
                }
                for c in comments
            ],
            "attachments": [
                {
                    "id": a.id,
                    "name": a.file_name or "Fayl",
                    "type": a.file_type,
                    "file_id": a.file_id
                }
                for a in attachments
            ]
        }

@router.post("/tasks/{task_id}/comments")
async def add_comment_api(
    task_id: int,
    payload: CommentCreateSchema,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
):
    current_user = await get_current_user_from_header(init_data)
    comment_text = payload.comment.strip()
    if not comment_text:
        raise HTTPException(status_code=400, detail="Izoh bo'sh bo'lishi mumkin emas.")

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Vazifa topilmadi!")

        c = await add_task_comment(
            session=session,
            task_id=task_id,
            user_id=current_user.telegram_id,
            user_name=current_user.full_name,
            comment=comment_text
        )
        return {"success": True, "comment_id": c.id}

@router.get("/users")
async def get_users_list(init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")):
    async with AsyncSessionLocal() as session:
        users = await get_all_users(session)
        return [
            {
                "id": u.id,
                "telegram_id": u.telegram_id,
                "full_name": u.full_name,
                "username": u.username,
                "role": u.role.value
            }
            for u in users
        ]

@router.put("/users/{telegram_id}/role")
async def change_user_role_api(
    telegram_id: int,
    payload: RoleUpdateSchema,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
):
    current_user = await get_current_user_from_header(init_data)
    if not (current_user.role == UserRole.ADMIN or current_user.telegram_id in settings.ADMIN_IDS):
        raise HTTPException(status_code=403, detail="Faqat Administrator rol bera oladi.")

    role_map = {
        "admin": UserRole.ADMIN,
        "manager": UserRole.MANAGER,
        "employee": UserRole.EMPLOYEE
    }
    new_role = role_map.get(payload.role.lower())
    if not new_role:
        raise HTTPException(status_code=400, detail="Noto'g'ri rol!")

    async with AsyncSessionLocal() as session:
        u = await update_user_role(session, telegram_id, new_role)
        return {"success": True, "role": u.role.value}

@router.get("/projects")
async def get_projects_api():
    async with AsyncSessionLocal() as session:
        projects = await get_all_projects(session)
        return [{"id": p.id, "name": p.name, "description": p.description} for p in projects]

@router.post("/projects")
async def add_project_api(
    payload: ProjectCreateSchema,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data")
):
    async with AsyncSessionLocal() as session:
        p = await get_or_create_project(session, payload.name, payload.description)
        return {"success": True, "project": {"id": p.id, "name": p.name}}

@router.get("/recurring")
async def get_recurring_api():
    async with AsyncSessionLocal() as session:
        recs = await get_all_recurring_tasks(session)
        return [
            {
                "id": r.id,
                "title": r.title,
                "project": r.project,
                "frequency": r.frequency.value,
                "time_str": r.time_str,
                "is_active": r.is_active
            }
            for r in recs
        ]

@router.post("/recurring/{rec_id}/toggle")
async def toggle_recurring_api(rec_id: int):
    async with AsyncSessionLocal() as session:
        r = await toggle_recurring_task(session, rec_id)
        return {"success": True, "is_active": r.is_active if r else False}

@router.delete("/recurring/{rec_id}")
async def delete_recurring_api(rec_id: int):
    async with AsyncSessionLocal() as session:
        ok = await delete_recurring_task(session, rec_id)
        return {"success": ok}

@router.get("/stats")
async def get_stats_api(days: int = 30):
    async with AsyncSessionLocal() as session:
        stats = await get_team_statistics(session, days=days)
        formatted_users = []
        for item in stats["users"]:
            formatted_users.append({
                "name": item["user"].full_name,
                "total": item["total"],
                "completed": item["completed"],
                "on_time_rate": item["on_time_rate"],
                "avg_delay_hours": item["avg_delay_hours"]
            })

        top = None
        if stats["top_performer"]:
            top = {
                "name": stats["top_performer"]["user"].full_name,
                "completed": stats["top_performer"]["completed"],
                "on_time_rate": stats["top_performer"]["on_time_rate"]
            }

        return {
            "days": days,
            "top_performer": top,
            "users": formatted_users
        }

@router.get("/export/excel")
async def export_excel_api():
    async with AsyncSessionLocal() as session:
        excel_io = await generate_tasks_excel(session)
        tz = pytz.timezone(settings.TIMEZONE)
        now_str = datetime.now(tz).strftime("%d.%m.%Y_%H%M")
        filename = f"vazifalar_hisoboti_{now_str}.xlsx"

        return Response(
            content=excel_io.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

