from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.base import AsyncSessionLocal
from database.crud import (
    get_task_by_id,
    get_user_by_id,
    get_or_create_user,
    get_or_create_group,
    get_user_open_tasks,
    get_group_open_tasks
)
from database.models import TaskStatus, TaskPriority
from utils.permissions import can_manage_task, can_approve_task
from locales import t
from utils.date_parser import format_datetime_for_user
from services.notification import update_group_task_card, build_task_card_text
from keyboards.inline import (
    get_task_card_keyboard,
    get_boss_approval_keyboard,
    get_just_submit_keyboard,
    get_cancel_keyboard
)

router = Router()

class TaskProofState(StatesGroup):
    task_id = State()
    waiting_proof = State()

class TaskRejectState(StatesGroup):
    task_id = State()
    waiting_reason = State()

# --- 1. BOSHLADIM (IN_PROGRESS) ---
@router.callback_query(F.data.startswith("task_start:"))
async def handle_task_start(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await callback.answer("Vazifa topilmadi!", show_alert=True)
            return

        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

        if not can_manage_task(user, callback.from_user.id, task):
            await callback.answer(t("task_not_assignee", lang), show_alert=True)
            return

        if task.status != TaskStatus.NEW:
            await callback.answer(t("task_already_in_progress", lang), show_alert=True)
            return

        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        await session.commit()
        await session.refresh(task)

        await callback.answer(t("task_started_notify", lang, id=task.id))

        # Guruhdagi va chatdagi kartochkani yangilash
        if callback.message.chat.type in ("group", "supergroup"):
            await update_group_task_card(callback.bot, task)
        else:
            creator_user = await get_user_by_id(session, task.creator_id) if task.creator_id else None
            card_text = build_task_card_text(
                task=task,
                lang=lang,
                assignee_name=callback.from_user.full_name,
                creator_name=creator_user.full_name if creator_user else "Admin"
            )
            await callback.message.edit_text(
                text=card_text,
                reply_markup=get_task_card_keyboard(task, lang),
                parse_mode="HTML"
            )
            if task.chat_id and task.group_message_id:
                await update_group_task_card(callback.bot, task)

# --- 2. TEKSHIRUVGA TOPSHIRISH (REVIEW) ---
@router.callback_query(F.data.startswith("task_review:"))
async def handle_task_review_request(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await callback.answer("Vazifa topilmadi!", show_alert=True)
            return

        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

        if not can_manage_task(user, callback.from_user.id, task):
            await callback.answer(t("task_not_assignee", lang), show_alert=True)
            return

        # Isbot so'rash holatiga o'tish
        await state.set_state(TaskProofState.waiting_proof)
        await state.update_data(task_id=task_id)

        # Agar guruhda bo'lsa, xodimga shaxsiyga o'tishni aytamiz yoki shu yerda javob berishini so'raymiz
        prompt_text = t("task_send_proof_prompt", lang, id=task.id)
        keyboard = get_just_submit_keyboard(task.id, lang)

        if callback.message.chat.type in ("group", "supergroup"):
            # Shaxsiyga xabar yuborish
            try:
                await callback.bot.send_message(
                    chat_id=callback.from_user.id,
                    text=prompt_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                await callback.answer("Hisobot yuborish uchun bot sizga shaxsiy xabar yubordi!", show_alert=True)
            except Exception:
                await callback.message.reply(
                    f"@{callback.from_user.username or callback.from_user.first_name}\n{prompt_text}",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        else:
            await callback.message.answer(prompt_text, reply_markup=keyboard, parse_mode="HTML")

# Isbotsiz shunchaki yuborish
@router.callback_query(F.data.startswith("submit_no_proof:"))
async def handle_submit_no_proof(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])
    await state.clear()
    await submit_task_to_review(
        bot=callback.bot,
        task_id=task_id,
        user_id=callback.from_user.id,
        user_name=callback.from_user.full_name,
        proof_text=None,
        proof_file_id=None,
        proof_type="none",
        origin_message=callback.message
    )
    await callback.answer()

# Isbot fayli yoki matni kelganda
@router.message(TaskProofState.waiting_proof)
async def handle_proof_message(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    await state.clear()

    proof_file_id = None
    proof_type = "text"
    proof_text = message.caption or message.text or ""

    if message.photo:
        proof_file_id = message.photo[-1].file_id
        proof_type = "photo"
    elif message.video:
        proof_file_id = message.video.file_id
        proof_type = "video"
    elif message.document:
        proof_file_id = message.document.file_id
        proof_type = "document"

    await submit_task_to_review(
        bot=message.bot,
        task_id=task_id,
        user_id=message.from_user.id,
        user_name=message.from_user.full_name,
        proof_text=proof_text,
        proof_file_id=proof_file_id,
        proof_type=proof_type,
        origin_message=message
    )

async def submit_task_to_review(bot, task_id: int, user_id: int, user_name: str, proof_text: str, proof_file_id: str, proof_type: str, origin_message: Message):
    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            return

        task.status = TaskStatus.REVIEW
        task.proof_text = proof_text
        task.proof_file_id = proof_file_id
        task.proof_type = proof_type
        task.submitted_at = datetime.utcnow()
        await session.commit()
        await session.refresh(task)

        user = await get_user_by_id(session, user_id)
        lang = user.language if user else "uz"

        await origin_message.answer(t("proof_received_waiting_approval", lang))

        # Guruhdagi kartochkani yangilash
        if task.chat_id and task.group_message_id:
            await update_group_task_card(bot, task)

        # Rahbarga tekshirish uchun yuborish
        recipient_id = task.creator_id
        boss = await get_user_by_id(session, recipient_id)
        boss_lang = boss.language if boss else "uz"

        boss_text = t(
            "proof_submitted_to_boss",
            boss_lang,
            id=task.id,
            title=task.title,
            assignee=user_name,
            proof_text=proof_text or ("—" if boss_lang == "uz" else "—")
        )
        approval_kb = get_boss_approval_keyboard(task.id, boss_lang)

        try:
            if proof_type == "photo" and proof_file_id:
                await bot.send_photo(
                    chat_id=recipient_id,
                    photo=proof_file_id,
                    caption=boss_text,
                    reply_markup=approval_kb,
                    parse_mode="HTML"
                )
            elif proof_type == "video" and proof_file_id:
                await bot.send_video(
                    chat_id=recipient_id,
                    video=proof_file_id,
                    caption=boss_text,
                    reply_markup=approval_kb,
                    parse_mode="HTML"
                )
            elif proof_type == "document" and proof_file_id:
                await bot.send_document(
                    chat_id=recipient_id,
                    document=proof_file_id,
                    caption=boss_text,
                    reply_markup=approval_kb,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=recipient_id,
                    text=boss_text,
                    reply_markup=approval_kb,
                    parse_mode="HTML"
                )
        except Exception:
            pass

# --- 3. RAHBAR TASDIQLASHI (APPROVE) ---
@router.callback_query(F.data.startswith("boss_approve:"))
async def handle_boss_approve(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await callback.answer("Vazifa topilmadi!", show_alert=True)
            return

        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

        if not can_approve_task(user, callback.from_user.id, task):
            await callback.answer(t("unauthorized", lang), show_alert=True)
            return

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        await session.commit()
        await session.refresh(task)

        await callback.answer("Vazifa tasdiqlandi!")
        if callback.message.caption:
            await callback.message.edit_caption(
                caption=callback.message.caption + f"\n\n✅ <b>Tasdiqlandi!</b>",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                text=callback.message.text + f"\n\n✅ <b>Tasdiqlandi!</b>",
                parse_mode="HTML"
            )

        # Guruhdagi kartochkani yangilash
        if task.chat_id and task.group_message_id:
            await update_group_task_card(callback.bot, task)

        # Guruhga xabar yuborish
        if task.chat_id:
            try:
                group = await get_or_create_group(session, task.chat_id)
                g_lang = group.language or "uz"
                await callback.bot.send_message(
                    chat_id=task.chat_id,
                    text=t("task_approved_group_notify", g_lang, id=task.id),
                    reply_to_message_id=task.group_message_id
                )
            except Exception:
                pass

        # Ijrochiga quvonchli xabar
        if task.assignee_id:
            try:
                assignee = await get_user_by_id(session, task.assignee_id)
                a_lang = assignee.language if assignee else "uz"
                await callback.bot.send_message(
                    chat_id=task.assignee_id,
                    text=t("task_approved_notify_user", a_lang, id=task.id, title=task.title)
                )
            except Exception:
                pass

# --- 4. RAHBAR QAYTARISHI (REJECT) ---
@router.callback_query(F.data.startswith("boss_reject:"))
async def handle_boss_reject_prompt(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await callback.answer("Vazifa topilmadi!", show_alert=True)
            return

        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

        if not can_approve_task(user, callback.from_user.id, task):
            await callback.answer(t("unauthorized", lang), show_alert=True)
            return

        await state.set_state(TaskRejectState.waiting_reason)
        await state.update_data(task_id=task_id)

        await callback.message.answer(
            t("reject_prompt_reason", lang),
            reply_markup=get_cancel_keyboard(lang)
        )
        await callback.answer()

@router.message(TaskRejectState.waiting_reason)
async def handle_reject_reason(message: Message, state: FSMContext):
    reason = message.text.strip()
    data = await state.get_data()
    task_id = data.get("task_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            return

        task.status = TaskStatus.IN_PROGRESS
        task.reject_reason = reason
        await session.commit()
        await session.refresh(task)

        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        await message.answer("Vazifa qaytarildi va xodimga xabar berildi.")

        # Guruhdagi kartochkani yangilash
        if task.chat_id and task.group_message_id:
            await update_group_task_card(message.bot, task)

        # Xodimga izoh bilan xabar yuborish
        if task.assignee_id:
            try:
                assignee = await get_user_by_id(session, task.assignee_id)
                a_lang = assignee.language if assignee else "uz"
                await message.bot.send_message(
                    chat_id=task.assignee_id,
                    text=t("task_rejected_notify_user", a_lang, id=task.id, title=task.title, reason=reason),
                    parse_mode="HTML"
                )
            except Exception:
                pass

# --- 5. /mening VA /vazifalar BUYRUQLARI ---
@router.message(Command("mening"))
async def handle_my_tasks(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        tasks = await get_user_open_tasks(session, message.from_user.id)
        if not tasks:
            await message.reply(t("my_tasks_empty", lang))
            return

        lines = [t("my_tasks_title", lang, count=len(tasks))]
        status_emojis = {
            TaskStatus.NEW: "🆕",
            TaskStatus.IN_PROGRESS: "⚡",
            TaskStatus.REVIEW: "👀"
        }
        for task in tasks:
            emoji = status_emojis.get(task.status, "📌")
            due = format_datetime_for_user(task.due_date, lang)
            lines.append(f"{emoji} <b>#{task.id} {task.title}</b> (Muddat: {due})")

        await message.reply("\n".join(lines), parse_mode="HTML")

@router.message(Command("vazifalar"))
async def handle_group_tasks(message: Message):
    if message.chat.type == "private":
        await message.reply("Bu buyruq guruhda ishlaydi. Shaxsiy vazifalar uchun /mening")
        return

    async with AsyncSessionLocal() as session:
        group = await get_or_create_group(session, message.chat.id, message.chat.title)
        lang = group.language or "uz"

        tasks = await get_group_open_tasks(session, message.chat.id)
        if not tasks:
            await message.reply(t("group_tasks_empty", lang))
            return

        lines = [t("group_tasks_title", lang, count=len(tasks))]
        status_emojis = {
            TaskStatus.NEW: "🆕",
            TaskStatus.IN_PROGRESS: "⚡",
            TaskStatus.REVIEW: "👀"
        }
        for task in tasks:
            emoji = status_emojis.get(task.status, "📌")
            due = format_datetime_for_user(task.due_date, lang)
            tag = f"@{task.assignee_username}" if task.assignee_username else "Xodim"
            lines.append(f"{emoji} <b>#{task.id} {task.title}</b> ({tag}, {due})")

        await message.reply("\n".join(lines), parse_mode="HTML")

