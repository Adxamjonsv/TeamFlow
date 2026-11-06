import logging
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot

from config import settings
from database.base import AsyncSessionLocal
from database.models import Task, TaskStatus, TaskPriority, UserRole, RecurringFrequency, RecurringTask
from database.crud import (
    get_tasks_due_in_range,
    get_overdue_tasks,
    get_all_groups,
    get_all_users,
    get_morning_report_data,
    get_evening_report_data,
    get_user_daily_tasks,
    get_user_by_id,
    get_all_recurring_tasks,
    create_task,
    update_task_group_message,
    get_or_create_group
)
from locales import t
from utils.date_parser import format_datetime_for_user
from services.notification import build_task_card_text, notify_assignee_new_task
from keyboards.inline import get_task_card_keyboard

logger = logging.getLogger(__name__)

async def check_deadline_reminders(bot: Bot):
    now_utc = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        # 1. 24 soat qolgan vazifalar
        start_24h = now_utc + timedelta(hours=23, minutes=30)
        end_24h = now_utc + timedelta(hours=24, minutes=30)
        tasks_24h = await get_tasks_due_in_range(session, start_24h, end_24h, "reminded_24h")

        for task in tasks_24h:
            task.reminded_24h = True
            await session.commit()
            await send_reminder(bot, task, reminder_type="24h")

        # 2. 2 soat qolgan vazifalar
        start_2h = now_utc + timedelta(hours=1, minutes=30)
        end_2h = now_utc + timedelta(hours=2, minutes=30)
        tasks_2h = await get_tasks_due_in_range(session, start_2h, end_2h, "reminded_2h")

        for task in tasks_2h:
            task.reminded_2h = True
            await session.commit()
            await send_reminder(bot, task, reminder_type="2h")

        # 3. Muddati o'tgan vazifalar
        overdue_tasks = await get_overdue_tasks(session, now_utc)
        for task in overdue_tasks:
            task.reminded_overdue = True
            await session.commit()
            await send_reminder(bot, task, reminder_type="overdue")

async def send_reminder(bot: Bot, task: Task, reminder_type: str):
    async with AsyncSessionLocal() as session:
        assignee = await get_user_by_id(session, task.assignee_id) if task.assignee_id else None
        user_lang = assignee.language if assignee else "uz"

        assignee_tag = f"@{task.assignee_username}" if task.assignee_username else (
            f"@{assignee.username}" if (assignee and assignee.username) else (assignee.full_name if assignee else "Xodim")
        )

        due_str = format_datetime_for_user(task.due_date, user_lang)

        overdue_str = ""
        if reminder_type == "overdue" and task.due_date:
            now_utc = datetime.utcnow()
            diff = now_utc - task.due_date
            hours = int(diff.total_seconds() // 3600)
            overdue_str = f"{hours} soat" if user_lang == "uz" else f"{hours} ч."

        template_key = f"reminder_{reminder_type}"
        msg_text = t(
            template_key,
            user_lang,
            id=task.id,
            title=task.title,
            assignee=assignee_tag,
            due_date=due_str,
            overdue_str=overdue_str
        )

        if task.assignee_id:
            try:
                await bot.send_message(chat_id=task.assignee_id, text=msg_text, parse_mode="HTML")
            except Exception as e:
                logger.info(f"Could not send reminder to assignee {task.assignee_id}: {e}")

        if task.chat_id:
            try:
                await bot.send_message(
                    chat_id=task.chat_id,
                    text=f"{assignee_tag}\n\n{msg_text}",
                    reply_to_message_id=task.group_message_id,
                    parse_mode="HTML"
                )
            except Exception:
                try:
                    await bot.send_message(chat_id=task.chat_id, text=f"{assignee_tag}\n\n{msg_text}", parse_mode="HTML")
                except Exception as e:
                    logger.warning(f"Failed to send reminder to group {task.chat_id}: {e}")

        if reminder_type == "overdue" and task.creator_id and task.creator_id != task.assignee_id:
            try:
                boss = await get_user_by_id(session, task.creator_id)
                boss_lang = boss.language if boss else "uz"
                boss_msg = t(
                    "reminder_overdue",
                    boss_lang,
                    id=task.id,
                    title=task.title,
                    assignee=assignee_tag,
                    due_date=format_datetime_for_user(task.due_date, boss_lang),
                    overdue_str=overdue_str
                )
                await bot.send_message(chat_id=task.creator_id, text=boss_msg, parse_mode="HTML")
            except Exception as e:
                logger.info(f"Could not notify creator of overdue task: {e}")

async def process_recurring_tasks(bot: Bot):
    tz = pytz.timezone(settings.TIMEZONE)
    now_local = datetime.now(tz)
    now_utc = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        active_recs = await get_all_recurring_tasks(session, only_active=True)

        for rec in active_recs:
            should_run = False

            # Vaqtni tekshirish
            try:
                r_h, r_m = [int(p) for p in rec.time_str.split(":")]
            except Exception:
                r_h, r_m = 9, 0

            # Agar belgilangan soat kelgan bo'lsa
            if now_local.hour == r_h:
                if rec.frequency == RecurringFrequency.DAILY:
                    # Bugun ishga tushmagan bo'lsa
                    if not rec.last_run_at or rec.last_run_at.date() < now_utc.date():
                        should_run = True

                elif rec.frequency == RecurringFrequency.WEEKLY:
                    # Belgilangan hafta kuni bo'lsa va bu hafta ishga tushmagan bo'lsa
                    target_day = rec.day_of_week if rec.day_of_week is not None else 0
                    if now_local.weekday() == target_day:
                        if not rec.last_run_at or (now_utc - rec.last_run_at).days >= 6:
                            should_run = True

                elif rec.frequency == RecurringFrequency.MONTHLY:
                    # Belgilangan oy kuni bo'lsa va bu oy ishga tushmagan bo'lsa
                    target_month_day = rec.day_of_month if rec.day_of_month else 1
                    if now_local.day == target_month_day:
                        if not rec.last_run_at or (now_utc - rec.last_run_at).days >= 25:
                            should_run = True

            if should_run:
                rec.last_run_at = now_utc
                await session.commit()

                # Yangi vazifa yaratamiz (muddati bugun kun oxirigacha yoki ertagacha)
                due_dt = now_local.replace(hour=18, minute=0, second=0, microsecond=0)
                due_utc = due_dt.astimezone(pytz.utc).replace(tzinfo=None)

                new_task = await create_task(
                    session=session,
                    title=rec.title,
                    description=rec.description,
                    creator_id=rec.creator_id,
                    assignee_id=rec.assignee_id,
                    assignee_username=rec.assignee_username,
                    chat_id=rec.chat_id,
                    priority=rec.priority,
                    project=rec.project,
                    due_date=due_utc
                )

                creator_user = await get_user_by_id(session, rec.creator_id)
                creator_name = creator_user.full_name if creator_user else "Admin"

                # Guruhga yuborish
                if rec.chat_id:
                    try:
                        group = await get_or_create_group(session, rec.chat_id)
                        g_lang = group.language or "uz"
                        card_text = build_task_card_text(
                            task=new_task,
                            lang=g_lang,
                            creator_name=creator_name
                        )
                        kb = get_task_card_keyboard(new_task, lang=g_lang)
                        c_msg = await bot.send_message(chat_id=rec.chat_id, text=card_text, reply_markup=kb, parse_mode="HTML")
                        await update_task_group_message(session, new_task.id, c_msg.message_id)
                    except Exception as e:
                        logger.warning(f"Could not send recurring task to group: {e}")

                # Ijrochiga bildirishnoma
                await notify_assignee_new_task(bot, new_task, creator_name)

async def send_morning_reports(bot: Bot):
    now_utc = datetime.utcnow()
    tz = pytz.timezone(settings.TIMEZONE)
    now_local = datetime.now(tz)
    date_str = now_local.strftime("%d.%m.%Y")

    async with AsyncSessionLocal() as session:
        # 1. Guruhlarga umumiy hisobot
        groups = await get_all_groups(session)
        for group in groups:
            if not group.morning_report:
                continue

            lang = group.language or "uz"
            data = await get_morning_report_data(session, group.chat_id, now_utc)

            has_tasks = any(len(lst) > 0 for lst in data.values())
            if not has_tasks:
                continue

            def format_list(tasks):
                if not tasks:
                    return t("report_none", lang)
                lines = []
                for item in tasks:
                    tag = f"@{item.assignee_username}" if item.assignee_username else "Xodim"
                    lines.append(f"• #{item.id} {item.title} ({tag})")
                return "\n".join(lines)

            def format_overdue_list(tasks):
                if not tasks:
                    return t("report_none", lang)
                lines = []
                for item in tasks:
                    tag = f"@{item.assignee_username}" if item.assignee_username else "Xodim"
                    kechikish = ""
                    if item.due_date:
                        diff = now_utc - item.due_date
                        days = diff.days
                        kechikish = f" [{days} kun kechikdi]" if lang == "uz" else f" [просрочено на {days} дн.]"
                    lines.append(f"• #{item.id} {item.title} ({tag}){kechikish}")
                return "\n".join(lines)

            report_parts = [
                t("morning_report_title", lang, date=date_str),
                t("report_section_completed", lang, items=format_list(data["completed"])),
                t("report_section_review", lang, items=format_list(data["review"])),
                t("report_section_in_progress", lang, items=format_list(data["in_progress"])),
                t("report_section_new", lang, items=format_list(data["new"])),
                t("report_section_due_today", lang, items=format_list(data["due_today"])),
                t("report_section_overdue", lang, items=format_overdue_list(data["overdue"])),
            ]
            full_report = "\n".join(report_parts)

            try:
                await bot.send_message(chat_id=group.chat_id, text=full_report, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Could not send morning report to group {group.chat_id}: {e}")

        # 2. Xodimlarga shaxsiy kunlik ro'yxat (09:00 da)
        users = await get_all_users(session)
        for u in users:
            p_data = await get_user_daily_tasks(session, u.telegram_id, now_utc)
            has_p_tasks = p_data["due_today"] or p_data["overdue"] or p_data["other_active"]
            u_lang = u.language or "uz"

            if not has_p_tasks:
                continue

            def format_p_list(tasks):
                if not tasks:
                    return "—"
                return "\n".join([f"• #{t_item.id} {t_item.title} (Muddat: {format_datetime_for_user(t_item.due_date, u_lang)})" for t_item in tasks])

            p_report = t("daily_personal_title", u_lang, name=u.full_name, date=date_str)
            if p_data["due_today"]:
                p_report += t("daily_personal_due_today", u_lang, items=format_p_list(p_data["due_today"]))
            if p_data["overdue"]:
                p_report += t("daily_personal_overdue", u_lang, items=format_p_list(p_data["overdue"]))
            if p_data["other_active"]:
                p_report += t("daily_personal_other", u_lang, items=format_p_list(p_data["other_active"]))

            try:
                await bot.send_message(chat_id=u.telegram_id, text=p_report, parse_mode="HTML")
            except Exception:
                pass

async def send_evening_reports(bot: Bot):
    now_utc = datetime.utcnow()
    tz = pytz.timezone(settings.TIMEZONE)
    now_local = datetime.now(tz)
    date_str = now_local.strftime("%d.%m.%Y")

    async with AsyncSessionLocal() as session:
        data = await get_evening_report_data(session, now_utc)
        users = await get_all_users(session)
        bosses = [u for u in users if u.role in (UserRole.ADMIN, UserRole.MANAGER) or u.telegram_id in settings.ADMIN_IDS]

        for boss in bosses:
            lang = boss.language or "uz"

            def fmt_comp(tasks):
                if not tasks:
                    return "—"
                lines = []
                for item in tasks:
                    tag = f"@{item.assignee_username}" if item.assignee_username else "Xodim"
                    lines.append(f"• #{item.id} {item.title} ({tag})")
                return "\n".join(lines)

            def fmt_overdue(tasks):
                if not tasks:
                    return "—"
                lines = []
                for item in tasks:
                    tag = f"@{item.assignee_username}" if item.assignee_username else "Xodim"
                    kechikish = ""
                    if item.due_date:
                        diff = now_utc - item.due_date
                        days = diff.days
                        kechikish = f" [{days} kun kechikdi]" if lang == "uz" else f" [просрочено на {days} дн.]"
                    lines.append(f"• #{item.id} {item.title} ({tag}){kechikish}")
                return "\n".join(lines)

            def fmt_active(tasks):
                if not tasks:
                    return "—"
                lines = []
                for item in tasks:
                    tag = f"@{item.assignee_username}" if item.assignee_username else "Xodim"
                    lines.append(f"• #{item.id} {item.title} ({tag})")
                return "\n".join(lines)

            report_text = (
                t("evening_report_title", lang, date=date_str) +
                t("evening_section_completed", lang, items=fmt_comp(data["completed_today"])) +
                t("evening_section_overdue", lang, items=fmt_overdue(data["overdue"])) +
                t("evening_section_active", lang, items=fmt_active(data["active"]))
            )

            try:
                await bot.send_message(chat_id=boss.telegram_id, text=report_text, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Could not send evening report to boss {boss.telegram_id}: {e}")

def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    tz = pytz.timezone(settings.TIMEZONE)
    scheduler = AsyncIOScheduler(timezone=tz)

    # 1. Eslatmalar har 5 daqiqada tekshiriladi
    scheduler.add_job(
        check_deadline_reminders,
        "interval",
        minutes=5,
        args=[bot],
        id="check_deadline_reminders"
    )

    # 2. Takrorlanuvchi vazifalar har 15 daqiqada tekshiriladi
    scheduler.add_job(
        process_recurring_tasks,
        "interval",
        minutes=15,
        args=[bot],
        id="process_recurring_tasks"
    )

    # 3. Ertalabki hisobot va Shaxsiy kunlik ro'yxat (09:00)
    m_hour, m_minute = 9, 0
    if settings.MORNING_REPORT_TIME and ":" in settings.MORNING_REPORT_TIME:
        try:
            parts = settings.MORNING_REPORT_TIME.split(":")
            m_hour, m_minute = int(parts[0]), int(parts[1])
        except Exception:
            pass

    scheduler.add_job(
        send_morning_reports,
        "cron",
        hour=m_hour,
        minute=m_minute,
        args=[bot],
        id="morning_report"
    )

    # 4. Kechki hisobot — Kun yakuni (19:00)
    e_hour, e_minute = 19, 0
    if settings.EVENING_REPORT_TIME and ":" in settings.EVENING_REPORT_TIME:
        try:
            parts = settings.EVENING_REPORT_TIME.split(":")
            e_hour, e_minute = int(parts[0]), int(parts[1])
        except Exception:
            pass

    scheduler.add_job(
        send_evening_reports,
        "cron",
        hour=e_hour,
        minute=e_minute,
        args=[bot],
        id="evening_report"
    )

    return scheduler

