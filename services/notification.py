import logging
from typing import Optional
from aiogram import Bot
from database.models import Task, TaskStatus, TaskPriority, User, GroupSettings
from database.crud import get_user_by_id, get_or_create_group, get_task_attachment_count
from database.base import AsyncSessionLocal
from locales import t
from utils.date_parser import format_datetime_for_user
from keyboards.inline import get_task_card_keyboard, get_boss_approval_keyboard

logger = logging.getLogger(__name__)

def build_task_card_text(
    task: Task,
    lang: str = "uz",
    assignee_name: Optional[str] = None,
    creator_name: Optional[str] = None,
    attachment_count: int = 0
) -> str:
    status_keys = {
        TaskStatus.NEW: "status_new",
        TaskStatus.IN_PROGRESS: "status_in_progress",
        TaskStatus.REVIEW: "status_review",
        TaskStatus.COMPLETED: "status_completed",
        TaskStatus.CANCELLED: "status_cancelled"
    }
    status_str = t(status_keys.get(task.status, "status_new"), lang)

    priority_keys = {
        TaskPriority.URGENT: "priority_urgent",
        TaskPriority.NORMAL: "priority_normal",
        TaskPriority.LOW: "priority_low"
    }
    priority_str = t(priority_keys.get(task.priority, "priority_normal"), lang)

    if assignee_name:
        assignee_str = assignee_name
    elif task.assignee_username:
        assignee_str = f"@{task.assignee_username}"
    else:
        assignee_str = t("unknown_user", lang)

    creator_str = creator_name or "Admin"
    due_str = format_datetime_for_user(task.due_date, lang)

    lines = [
        t("task_card_title", lang, id=task.id),
    ]
    if task.project:
        lines.append(t("task_card_project", lang, project=task.project))
    
    lines.extend([
        t("task_card_desc", lang, description=task.title),
        t("task_card_assignee", lang, assignee=assignee_str),
        t("task_card_creator", lang, creator=creator_str),
        t("task_card_priority", lang, priority=priority_str),
        t("task_card_status", lang, status=status_str),
        t("task_card_due_date", lang, due_date=due_str),
    ])

    if attachment_count > 0:
        lines.append(t("task_card_attachments", lang, count=attachment_count))

    if task.reject_reason and task.status == TaskStatus.IN_PROGRESS:
        lines.append(f"\n⚠️ <i>Izoh: {task.reject_reason}</i>" if lang == "uz" else f"\n⚠️ <i>Замечание: {task.reject_reason}</i>")

    return "\n".join(lines)

async def update_group_task_card(bot: Bot, task: Task):
    if not task.chat_id or not task.group_message_id:
        return

    try:
        async with AsyncSessionLocal() as session:
            group = await get_or_create_group(session, task.chat_id)
            group_lang = group.language or "uz"

            assignee_user = await get_user_by_id(session, task.assignee_id) if task.assignee_id else None
            creator_user = await get_user_by_id(session, task.creator_id) if task.creator_id else None

            assignee_name = None
            if assignee_user:
                assignee_name = f"{assignee_user.full_name} (@{assignee_user.username})" if assignee_user.username else assignee_user.full_name
            elif task.assignee_username:
                assignee_name = f"@{task.assignee_username}"

            creator_name = creator_user.full_name if creator_user else "Admin"
            att_count = await get_task_attachment_count(session, task.id)

            card_text = build_task_card_text(
                task=task,
                lang=group_lang,
                assignee_name=assignee_name,
                creator_name=creator_name,
                attachment_count=att_count
            )
            keyboard = get_task_card_keyboard(task, lang=group_lang, attachment_count=att_count)

            await bot.edit_message_text(
                chat_id=task.chat_id,
                message_id=task.group_message_id,
                text=card_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.warning(f"Failed to update task #{task.id} card in group: {e}")

async def notify_assignee_new_task(bot: Bot, task: Task, creator_name: str):
    if not task.assignee_id:
        return

    try:
        async with AsyncSessionLocal() as session:
            user = await get_user_by_id(session, task.assignee_id)
            lang = user.language if user else "uz"
            att_count = await get_task_attachment_count(session, task.id)

            priority_keys = {
                TaskPriority.URGENT: "priority_urgent",
                TaskPriority.NORMAL: "priority_normal",
                TaskPriority.LOW: "priority_low"
            }
            priority_str = t(priority_keys.get(task.priority, "priority_normal"), lang)
            due_str = format_datetime_for_user(task.due_date, lang)

            text = t(
                "task_assigned_private_notify",
                lang,
                title=task.title,
                project=task.project or ("Umumiy" if lang == "uz" else "Общий"),
                priority=priority_str,
                due_date=due_str,
                creator=creator_name
            )
            keyboard = get_task_card_keyboard(task, lang=lang, attachment_count=att_count)
            await bot.send_message(
                chat_id=task.assignee_id,
                text=text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.info(f"Could not send private notification to user {task.assignee_id}: {e}")

