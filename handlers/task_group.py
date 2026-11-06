import logging
from aiogram import Router, F
from aiogram.types import Message
from database.base import AsyncSessionLocal
from database.crud import (
    get_or_create_user,
    get_or_create_group,
    get_user_by_id,
    get_user_by_username,
    create_task,
    update_task_group_message
)
from database.models import UserRole
from utils.task_parser import parse_group_task_message
from utils.permissions import can_create_task, is_admin
from locales import t
from services.notification import build_task_card_text, notify_assignee_new_task
from keyboards.inline import get_task_card_keyboard

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.chat.type.in_({"group", "supergroup"}), F.text.func(lambda text: bool(text and "#vazifa" in text.lower())))
async def handle_group_task_creation(message: Message):
    async with AsyncSessionLocal() as session:
        # 1. Guruh va muallif ma'lumotlarini olish
        group = await get_or_create_group(session, message.chat.id, message.chat.title)
        group_lang = group.language or "uz"

        creator_user, _ = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

        # Ruxsatni tekshirish: Guruh adminimi yoki botdagi admin/menejermi?
        has_permission = can_create_task(creator_user, message.from_user.id)
        if not has_permission:
            # Guruhdagi administratorligini ham tekshirib ko'ramiz
            try:
                chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
                if chat_member.status in ("creator", "administrator"):
                    has_permission = True
            except Exception:
                pass

        if not has_permission:
            await message.reply(t("unauthorized", group_lang))
            return

        # 2. Xabarni tahlil qilish (parser)
        parsed = parse_group_task_message(message.text)
        usernames = parsed["usernames"]
        priority = parsed["priority"]
        project = parsed["project"]
        due_date = parsed["due_date"]
        task_title = parsed["title"]

        targets = []

        # Agar kimningdir xabariga reply qilib yozilgan bo'lsa
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
            if not target_user.is_bot:
                # Reply qilingan foydalanuvchini bazaga qo'shamiz/olamiz
                u, _ = await get_or_create_user(
                    session=session,
                    telegram_id=target_user.id,
                    full_name=target_user.full_name,
                    username=target_user.username
                )
                targets.append({
                    "telegram_id": target_user.id,
                    "username": target_user.username,
                    "full_name": target_user.full_name
                })

        # Agar xabarda @nik lar yozilgan bo'lsa
        for un in usernames:
            clean_un = un.lstrip("@").lower()
            # Agar reply qilingan odam bilan bir xil bo'lsa, qayta qo'shmaymiz
            if any(t.get("username") and t["username"].lower() == clean_un for t in targets):
                continue

            existing_user = await get_user_by_username(session, clean_un)
            if existing_user:
                targets.append({
                    "telegram_id": existing_user.telegram_id,
                    "username": clean_un,
                    "full_name": existing_user.full_name
                })
            else:
                # Foydalanuvchi hali botga kirmagan bo'lsa ham username saqlanadi!
                targets.append({
                    "telegram_id": None,
                    "username": clean_un,
                    "full_name": f"@{clean_un}"
                })

        # Agar hech qanday ijrochi belgilanmagan bo'lsa
        if not targets:
            await message.reply(
                "⚠️ Iltimos, vazifani kimga biriktirishni @nik orqali yozing yoki xodimning xabariga reply qiling.\n"
                "Misol: <code>#vazifa @ali Sayt dizayni, ertaga 18:00</code>"
                if group_lang == "uz" else
                "⚠️ Пожалуйста, укажите исполнителя через @ник или ответьте на его сообщение.\n"
                "Пример: <code>#vazifa @ivan Дизайн сайта, завтра 18:00</code>",
                parse_mode="HTML"
            )
            return

        # 3. Har bir ijrochi uchun alohida vazifa yaratish
        for target in targets:
            task = await create_task(
                session=session,
                title=task_title,
                creator_id=message.from_user.id,
                assignee_id=target["telegram_id"],
                assignee_username=target["username"],
                chat_id=message.chat.id,
                priority=priority,
                project=project,
                due_date=due_date
            )

            # Guruhga vazifa kartochkasini yuborish
            assignee_display = target["full_name"]
            if target["username"] and not assignee_display.startswith("@"):
                assignee_display += f" (@{target['username']})"

            card_text = build_task_card_text(
                task=task,
                lang=group_lang,
                assignee_name=assignee_display,
                creator_name=message.from_user.full_name
            )
            keyboard = get_task_card_keyboard(task, lang=group_lang)

            card_msg = await message.reply(
                text=card_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )

            # Kartochka xabar ID sini saqlaymiz
            await update_task_group_message(session, task.id, card_msg.message_id)
            task.group_message_id = card_msg.message_id

            # Ijrochiga shaxsiy xabarda bildirishnoma yuborish
            await notify_assignee_new_task(
                bot=message.bot,
                task=task,
                creator_name=message.from_user.full_name
            )

