from datetime import datetime
import pytz
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from config import settings
from database.base import AsyncSessionLocal
from database.crud import (
    get_user_by_id,
    get_or_create_group,
    get_morning_report_data,
    get_all_groups
)
from utils.permissions import is_admin
from locales import t

router = Router()

@router.message(Command("hisobot"))
async def handle_manual_report(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        if not is_admin(user, message.from_user.id):
            # Guruhda adminmi tekshiramiz
            is_group_admin = False
            if message.chat.type in ("group", "supergroup"):
                try:
                    chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
                    if chat_member.status in ("creator", "administrator"):
                        is_group_admin = True
                except Exception:
                    pass
            if not is_group_admin:
                await message.reply(t("unauthorized", "uz"))
                return

        chat_id = message.chat.id
        if message.chat.type == "private":
            # Agar shaxsiy chatda bo'lsa, birinchi guruhni olamiz yoki xabar beramiz
            groups = await get_all_groups(session)
            if not groups:
                await message.reply("Hozircha faol guruhlar topilmadi.")
                return
            chat_id = groups[0].chat_id

        group = await get_or_create_group(session, chat_id)
        lang = group.language or "uz"

        now_utc = datetime.utcnow()
        tz = pytz.timezone(settings.TIMEZONE)
        now_local = datetime.now(tz)
        date_str = now_local.strftime("%d.%m.%Y")

        data = await get_morning_report_data(session, chat_id, now_utc)

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

        await message.reply(full_report, parse_mode="HTML")

