from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, update, delete, or_, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import (
    User, GroupSettings, Task, TaskComment, TaskAttachment, Project, RecurringTask,
    TaskStatus, TaskPriority, UserRole, RecurringFrequency
)
from config import settings

# --- USER CRUD ---

async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    username: Optional[str] = None,
    role: Optional[UserRole] = None,
    language: Optional[str] = None
) -> Tuple[User, bool]:
    clean_username = username.lstrip("@").lower() if username else None
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    created = False
    if not user:
        if not role:
            role = UserRole.ADMIN if telegram_id in settings.ADMIN_IDS else UserRole.EMPLOYEE
        user = User(
            telegram_id=telegram_id,
            username=clean_username,
            full_name=full_name,
            role=role,
            language=language or "uz"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        created = True
    else:
        changed = False
        if clean_username and user.username != clean_username:
            user.username = clean_username
            changed = True
        if full_name and user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if telegram_id in settings.ADMIN_IDS and user.role != UserRole.ADMIN:
            user.role = UserRole.ADMIN
            changed = True
        if language and user.language != language:
            user.language = language
            changed = True
        if changed:
            await session.commit()
            await session.refresh(user)

    return user, created

async def update_user_language(session: AsyncSession, telegram_id: int, language: str) -> Optional[User]:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.language = language
        await session.commit()
        await session.refresh(user)
    return user

async def update_user_role(session: AsyncSession, telegram_id: int, role: UserRole) -> Optional[User]:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.role = role
        await session.commit()
        await session.refresh(user)
    return user

async def get_user_by_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    clean_username = username.lstrip("@").lower()
    stmt = select(User).where(User.username == clean_username)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def get_all_users(session: AsyncSession) -> List[User]:
    stmt = select(User).order_by(User.full_name)
    result = await session.execute(stmt)
    return list(result.scalars().all())

# --- GROUP CRUD ---

async def get_or_create_group(session: AsyncSession, chat_id: int, title: Optional[str] = None) -> GroupSettings:
    stmt = select(GroupSettings).where(GroupSettings.chat_id == chat_id)
    result = await session.execute(stmt)
    group = result.scalar_one_or_none()
    if not group:
        group = GroupSettings(
            chat_id=chat_id,
            title=title or f"Group {chat_id}",
            language="uz"
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)
    elif title and group.title != title:
        group.title = title
        await session.commit()
        await session.refresh(group)
    return group

async def update_group_language(session: AsyncSession, chat_id: int, language: str) -> Optional[GroupSettings]:
    group = await get_or_create_group(session, chat_id)
    group.language = language
    await session.commit()
    await session.refresh(group)
    return group

async def get_all_groups(session: AsyncSession) -> List[GroupSettings]:
    stmt = select(GroupSettings)
    result = await session.execute(stmt)
    return list(result.scalars().all())

# --- PROJECT CRUD ---

async def get_or_create_project(session: AsyncSession, name: str, description: Optional[str] = None) -> Project:
    clean_name = name.strip()
    stmt = select(Project).where(func.lower(Project.name) == clean_name.lower())
    result = await session.execute(stmt)
    proj = result.scalar_one_or_none()
    if not proj:
        proj = Project(
            name=clean_name,
            description=description,
            is_active=True
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
    return proj

async def get_all_projects(session: AsyncSession, only_active: bool = True) -> List[Project]:
    stmt = select(Project)
    if only_active:
        stmt = stmt.where(Project.is_active == True)
    stmt = stmt.order_by(Project.name)
    result = await session.execute(stmt)
    return list(result.scalars().all())

# --- TASK CRUD ---

async def create_task(
    session: AsyncSession,
    title: str,
    creator_id: int,
    assignee_id: Optional[int] = None,
    assignee_username: Optional[str] = None,
    chat_id: Optional[int] = None,
    group_message_id: Optional[int] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    project: Optional[str] = None,
    due_date: Optional[datetime] = None,
    description: Optional[str] = None
) -> Task:
    clean_username = assignee_username.lstrip("@").lower() if assignee_username else None
    
    if project:
        await get_or_create_project(session, project)

    task = Task(
        title=title,
        description=description,
        creator_id=creator_id,
        assignee_id=assignee_id,
        assignee_username=clean_username,
        chat_id=chat_id,
        group_message_id=group_message_id,
        status=TaskStatus.NEW,
        priority=priority,
        project=project,
        due_date=due_date,
        created_at=datetime.utcnow()
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task

async def get_task_by_id(session: AsyncSession, task_id: int) -> Optional[Task]:
    stmt = select(Task).where(Task.id == task_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_task_group_message(session: AsyncSession, task_id: int, message_id: int):
    stmt = update(Task).where(Task.id == task_id).values(group_message_id=message_id)
    await session.execute(stmt)
    await session.commit()

async def link_tasks_by_username(session: AsyncSession, username: str, telegram_id: int) -> int:
    clean_username = username.lstrip("@").lower()
    stmt = (
        update(Task)
        .where(
            and_(
                Task.assignee_username == clean_username,
                Task.assignee_id.is_(None)
            )
        )
        .values(assignee_id=telegram_id)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount

async def get_user_open_tasks(session: AsyncSession, telegram_id: int) -> List[Task]:
    stmt = (
        select(Task)
        .where(
            and_(
                Task.assignee_id == telegram_id,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW])
            )
        )
        .order_by(Task.due_date.asc().nulls_last())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_group_open_tasks(session: AsyncSession, chat_id: int) -> List[Task]:
    stmt = (
        select(Task)
        .where(
            and_(
                Task.chat_id == chat_id,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW])
            )
        )
        .order_by(Task.due_date.asc().nulls_last())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

# --- COMMENTS & ATTACHMENTS ---

async def add_task_comment(session: AsyncSession, task_id: int, user_id: int, user_name: str, comment: str) -> TaskComment:
    tc = TaskComment(
        task_id=task_id,
        user_id=user_id,
        user_name=user_name,
        comment=comment,
        created_at=datetime.utcnow()
    )
    session.add(tc)
    await session.commit()
    await session.refresh(tc)
    return tc

async def get_task_comments(session: AsyncSession, task_id: int, limit: int = 10) -> List[TaskComment]:
    stmt = select(TaskComment).where(TaskComment.task_id == task_id).order_by(TaskComment.created_at.asc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def add_task_attachment(
    session: AsyncSession,
    task_id: int,
    file_id: str,
    file_type: str,
    file_unique_id: Optional[str] = None,
    file_name: Optional[str] = None
) -> TaskAttachment:
    att = TaskAttachment(
        task_id=task_id,
        file_id=file_id,
        file_unique_id=file_unique_id,
        file_type=file_type,
        file_name=file_name,
        created_at=datetime.utcnow()
    )
    session.add(att)
    await session.commit()
    await session.refresh(att)
    return att

async def get_task_attachments(session: AsyncSession, task_id: int) -> List[TaskAttachment]:
    stmt = select(TaskAttachment).where(TaskAttachment.task_id == task_id).order_by(TaskAttachment.created_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_task_attachment_count(session: AsyncSession, task_id: int) -> int:
    stmt = select(func.count(TaskAttachment.id)).where(TaskAttachment.task_id == task_id)
    result = await session.execute(stmt)
    return result.scalar() or 0

# --- RECURRING TASKS CRUD ---

async def create_recurring_task(
    session: AsyncSession,
    title: str,
    creator_id: int,
    frequency: RecurringFrequency,
    assignee_id: Optional[int] = None,
    assignee_username: Optional[str] = None,
    chat_id: Optional[int] = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    project: Optional[str] = None,
    day_of_week: Optional[int] = None,
    day_of_month: Optional[int] = None,
    time_str: str = "09:00",
    description: Optional[str] = None
) -> RecurringTask:
    clean_un = assignee_username.lstrip("@").lower() if assignee_username else None
    rec = RecurringTask(
        title=title,
        description=description,
        creator_id=creator_id,
        assignee_id=assignee_id,
        assignee_username=clean_un,
        chat_id=chat_id,
        priority=priority,
        project=project,
        frequency=frequency,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        time_str=time_str,
        is_active=True,
        created_at=datetime.utcnow()
    )
    session.add(rec)
    await session.commit()
    await session.refresh(rec)
    return rec

async def get_all_recurring_tasks(session: AsyncSession, only_active: bool = False) -> List[RecurringTask]:
    stmt = select(RecurringTask)
    if only_active:
        stmt = stmt.where(RecurringTask.is_active == True)
    stmt = stmt.order_by(RecurringTask.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def toggle_recurring_task(session: AsyncSession, rec_id: int) -> Optional[RecurringTask]:
    stmt = select(RecurringTask).where(RecurringTask.id == rec_id)
    result = await session.execute(stmt)
    rec = result.scalar_one_or_none()
    if rec:
        rec.is_active = not rec.is_active
        await session.commit()
        await session.refresh(rec)
    return rec

async def delete_recurring_task(session: AsyncSession, rec_id: int) -> bool:
    stmt = delete(RecurringTask).where(RecurringTask.id == rec_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0

# --- STATISTIKA VA REYTINQ (KPI) ---

async def get_team_statistics(session: AsyncSession, days: int = 30) -> dict:
    since_date = datetime.utcnow() - timedelta(days=days)

    users = await get_all_users(session)
    stats_by_user = []

    for u in users:
        # 1. Jami biriktirilgan
        res_total = await session.execute(
            select(func.count(Task.id)).where(
                and_(Task.assignee_id == u.telegram_id, Task.created_at >= since_date)
            )
        )
        total_tasks = res_total.scalar() or 0

        # 2. Bajarilganlar
        res_comp = await session.execute(
            select(Task).where(
                and_(
                    Task.assignee_id == u.telegram_id,
                    Task.status == TaskStatus.COMPLETED,
                    Task.completed_at >= since_date
                )
            )
        )
        comp_tasks = list(res_comp.scalars().all())
        completed_count = len(comp_tasks)

        # 3. O'z vaqtida bajarilganlar va kechikish
        on_time_count = 0
        total_delay_hours = 0
        overdue_completed_count = 0

        for t in comp_tasks:
            if t.due_date and t.completed_at:
                if t.completed_at <= t.due_date:
                    on_time_count += 1
                else:
                    overdue_completed_count += 1
                    diff = (t.completed_at - t.due_date).total_seconds() / 3600.0
                    total_delay_hours += max(0, diff)
            else:
                on_time_count += 1

        on_time_rate = (on_time_count / completed_count * 100.0) if completed_count > 0 else 0.0
        avg_delay = (total_delay_hours / overdue_completed_count) if overdue_completed_count > 0 else 0.0

        if total_tasks > 0 or completed_count > 0:
            stats_by_user.append({
                "user": u,
                "total": total_tasks,
                "completed": completed_count,
                "on_time_count": on_time_count,
                "on_time_rate": round(on_time_rate, 1),
                "avg_delay_hours": round(avg_delay, 1)
            })

    # Eng faol xodimlarni saralash (bajarilgan soni va o'z vaqtidalik foizi bo'yicha)
    stats_by_user.sort(key=lambda x: (x["completed"], x["on_time_rate"]), reverse=True)

    return {
        "days": days,
        "users": stats_by_user,
        "top_performer": stats_by_user[0] if stats_by_user else None
    }

# --- EKSPORT SO'ROVLARI ---

async def get_all_tasks_for_export(session: AsyncSession) -> List[Task]:
    stmt = select(Task).order_by(Task.id.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())

# --- REMINDERS & REPORTS QUERIES ---

async def get_tasks_due_in_range(
    session: AsyncSession,
    start_time: datetime,
    end_time: datetime,
    flag_attr: str
) -> List[Task]:
    attr = getattr(Task, flag_attr)
    stmt = (
        select(Task)
        .where(
            and_(
                Task.due_date >= start_time,
                Task.due_date <= end_time,
                attr == False,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS])
            )
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_overdue_tasks(session: AsyncSession, now: datetime) -> List[Task]:
    stmt = (
        select(Task)
        .where(
            and_(
                Task.due_date < now,
                Task.reminded_overdue == False,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS])
            )
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_morning_report_data(session: AsyncSession, chat_id: int, now: datetime) -> dict:
    one_day_ago = now - timedelta(hours=24)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    res_completed = await session.execute(
        select(Task).where(
            and_(
                Task.chat_id == chat_id,
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= one_day_ago
            )
        )
    )
    completed_tasks = list(res_completed.scalars().all())

    res_review = await session.execute(
        select(Task).where(
            and_(Task.chat_id == chat_id, Task.status == TaskStatus.REVIEW)
        )
    )
    review_tasks = list(res_review.scalars().all())

    res_in_prog = await session.execute(
        select(Task).where(
            and_(Task.chat_id == chat_id, Task.status == TaskStatus.IN_PROGRESS)
        )
    )
    in_progress_tasks = list(res_in_prog.scalars().all())

    res_new = await session.execute(
        select(Task).where(
            and_(Task.chat_id == chat_id, Task.status == TaskStatus.NEW)
        )
    )
    new_tasks = list(res_new.scalars().all())

    res_due_today = await session.execute(
        select(Task).where(
            and_(
                Task.chat_id == chat_id,
                Task.due_date >= start_of_day,
                Task.due_date < end_of_day,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS])
            )
        )
    )
    due_today_tasks = list(res_due_today.scalars().all())

    res_overdue = await session.execute(
        select(Task).where(
            and_(
                Task.chat_id == chat_id,
                Task.due_date < now,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS])
            )
        )
    )
    overdue_tasks = list(res_overdue.scalars().all())

    return {
        "completed": completed_tasks,
        "review": review_tasks,
        "in_progress": in_progress_tasks,
        "new": new_tasks,
        "due_today": due_today_tasks,
        "overdue": overdue_tasks
    }

async def get_evening_report_data(session: AsyncSession, now: datetime) -> dict:
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    res_completed = await session.execute(
        select(Task).where(
            and_(
                Task.status == TaskStatus.COMPLETED,
                Task.completed_at >= start_of_day,
                Task.completed_at < end_of_day
            )
        )
    )
    completed_today = list(res_completed.scalars().all())

    res_overdue = await session.execute(
        select(Task).where(
            and_(
                Task.due_date < now,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW])
            )
        )
    )
    overdue_tasks = list(res_overdue.scalars().all())

    res_active = await session.execute(
        select(Task).where(
            Task.status.in_([TaskStatus.IN_PROGRESS, TaskStatus.REVIEW])
        )
    )
    active_tasks = list(res_active.scalars().all())

    return {
        "completed_today": completed_today,
        "overdue": overdue_tasks,
        "active": active_tasks
    }

async def get_user_daily_tasks(session: AsyncSession, telegram_id: int, now: datetime) -> dict:
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    res_today = await session.execute(
        select(Task).where(
            and_(
                Task.assignee_id == telegram_id,
                Task.due_date >= start_of_day,
                Task.due_date < end_of_day,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS])
            )
        ).order_by(Task.due_date.asc())
    )
    due_today = list(res_today.scalars().all())

    res_overdue = await session.execute(
        select(Task).where(
            and_(
                Task.assignee_id == telegram_id,
                Task.due_date < now,
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS])
            )
        ).order_by(Task.due_date.asc())
    )
    overdue = list(res_overdue.scalars().all())

    res_other = await session.execute(
        select(Task).where(
            and_(
                Task.assignee_id == telegram_id,
                or_(Task.due_date.is_(None), Task.due_date >= end_of_day),
                Task.status.in_([TaskStatus.NEW, TaskStatus.IN_PROGRESS])
            )
        ).order_by(Task.due_date.asc().nulls_last())
    )
    other_active = list(res_other.scalars().all())

    return {
        "due_today": due_today,
        "overdue": overdue,
        "other_active": other_active
    }

