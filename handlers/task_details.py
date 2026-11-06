from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.base import AsyncSessionLocal
from database.crud import (
    get_task_by_id,
    get_user_by_id,
    add_task_comment,
    get_task_comments,
    add_task_attachment,
    get_task_attachments,
    get_task_attachment_count
)
from database.models import TaskStatus
from locales import t
from keyboards.inline import (
    get_comments_menu_keyboard,
    get_files_menu_keyboard,
    get_task_card_keyboard,
    get_cancel_keyboard
)
from services.notification import update_group_task_card, build_task_card_text

router = Router()

class TaskCommentState(StatesGroup):
    task_id = State()
    waiting_text = State()

class TaskAttachmentState(StatesGroup):
    task_id = State()
    waiting_file = State()

# --- IZOHLAR (COMMENTS) ---

@router.callback_query(F.data.startswith("task_comments:"))
async def handle_view_comments(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await callback.answer("Vazifa topilmadi!", show_alert=True)
            return

        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

        comments = await get_task_comments(session, task_id)
        header = t("comments_title", lang, id=task.id)

        if not comments:
            body = t("no_comments", lang)
        else:
            lines = []
            for c in comments:
                time_str = c.created_at.strftime("%d.%m %H:%M")
                lines.append(f"👤 <b>{c.user_name}</b> ({time_str}):\n{c.comment}\n")
            body = "\n".join(lines)

        text = f"{header}{body}"
        keyboard = get_comments_menu_keyboard(task_id, lang)

        if callback.message.chat.type in ("group", "supergroup"):
            # Guruhda bo'lsa, yangi xabar qilib yoki shaxsiyga
            await callback.message.reply(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
        else:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("add_comment:"))
async def handle_start_add_comment(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

    await state.set_state(TaskCommentState.waiting_text)
    await state.update_data(task_id=task_id)

    prompt = t("prompt_new_comment", lang, id=task_id)
    cancel_kb = get_cancel_keyboard(lang)

    if callback.message.chat.type in ("group", "supergroup"):
        try:
            await callback.bot.send_message(chat_id=callback.from_user.id, text=prompt, reply_markup=cancel_kb)
            await callback.answer("Izoh yozish uchun bot sizga shaxsiy xabar yubordi!", show_alert=True)
        except Exception:
            await callback.message.reply(prompt, reply_markup=cancel_kb)
    else:
        await callback.message.answer(prompt, reply_markup=cancel_kb)
        await callback.answer()

@router.message(TaskCommentState.waiting_text)
async def handle_save_comment(message: Message, state: FSMContext):
    comment_text = message.text.strip()
    data = await state.get_data()
    task_id = data.get("task_id")
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        task = await get_task_by_id(session, task_id)
        if not task:
            await message.answer("Vazifa topilmadi.")
            return

        user_name = user.full_name if user else message.from_user.full_name
        await add_task_comment(
            session=session,
            task_id=task_id,
            user_id=message.from_user.id,
            user_name=user_name,
            comment=comment_text
        )

        await message.answer(t("comment_added_success", lang))

        # Bildirishnoma yuborish: agar xodim yozgan bo'lsa rahbarga, rahbar yozgan bo'lsa xodimga
        notify_user_id = task.creator_id if message.from_user.id != task.creator_id else task.assignee_id
        if notify_user_id and notify_user_id != message.from_user.id:
            try:
                dest_user = await get_user_by_id(session, notify_user_id)
                d_lang = dest_user.language if dest_user else "uz"
                notify_text = t("notify_new_comment", d_lang, id=task.id, author=user_name, text=comment_text)
                await message.bot.send_message(chat_id=notify_user_id, text=notify_text, parse_mode="HTML")
            except Exception:
                pass

        # Guruhdagi kartochkani yangilash
        if task.chat_id and task.group_message_id:
            await update_group_task_card(message.bot, task)

# --- FAYLLAR (ATTACHMENTS) ---

@router.callback_query(F.data.startswith("task_files:"))
async def handle_view_files_menu(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await callback.answer("Vazifa topilmadi!", show_alert=True)
            return

        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"
        count = await get_task_attachment_count(session, task_id)

        keyboard = get_files_menu_keyboard(task_id, count, lang)
        text = f"📎 <b>Vazifa #{task.id} fayllari ({count} ta):</b>" if lang == "uz" else f"📎 <b>Файлы задачи #{task.id} ({count} шт.):</b>"

        if callback.message.chat.type in ("group", "supergroup"):
            await callback.message.reply(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
        else:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("add_file:"))
async def handle_start_add_file(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

    await state.set_state(TaskAttachmentState.waiting_file)
    await state.update_data(task_id=task_id)

    prompt = t("prompt_send_file", lang, id=task_id)
    cancel_kb = get_cancel_keyboard(lang)

    if callback.message.chat.type in ("group", "supergroup"):
        try:
            await callback.bot.send_message(chat_id=callback.from_user.id, text=prompt, reply_markup=cancel_kb)
            await callback.answer("Fayl yuborish uchun bot sizga shaxsiy xabar yubordi!", show_alert=True)
        except Exception:
            await callback.message.reply(prompt, reply_markup=cancel_kb)
    else:
        await callback.message.answer(prompt, reply_markup=cancel_kb)
        await callback.answer()

@router.message(TaskAttachmentState.waiting_file)
async def handle_save_file(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("task_id")
    await state.clear()

    file_id = None
    file_unique_id = None
    file_type = "document"
    file_name = None

    if message.photo:
        file_id = message.photo[-1].file_id
        file_unique_id = message.photo[-1].file_unique_id
        file_type = "photo"
        file_name = "photo.jpg"
    elif message.video:
        file_id = message.video.file_id
        file_unique_id = message.video.file_unique_id
        file_type = "video"
        file_name = message.video.file_name or "video.mp4"
    elif message.document:
        file_id = message.document.file_id
        file_unique_id = message.document.file_unique_id
        file_type = "document"
        file_name = message.document.file_name
    elif message.audio:
        file_id = message.audio.file_id
        file_unique_id = message.audio.file_unique_id
        file_type = "audio"
        file_name = message.audio.file_name or "audio.mp3"
    else:
        await message.answer("Iltimos, rasm, video yoki hujjat yuboring.")
        return

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await message.answer("Vazifa topilmadi.")
            return

        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        await add_task_attachment(
            session=session,
            task_id=task_id,
            file_id=file_id,
            file_type=file_type,
            file_unique_id=file_unique_id,
            file_name=file_name
        )

        await message.answer(t("file_attached_success", lang))

        # Guruhdagi kartochkani yangilash
        if task.chat_id and task.group_message_id:
            await update_group_task_card(message.bot, task)

@router.callback_query(F.data.startswith("view_files:"))
async def handle_view_files(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await callback.answer("Vazifa topilmadi!", show_alert=True)
            return

        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

        attachments = await get_task_attachments(session, task_id)
        if not attachments:
            await callback.answer(t("no_attachments", lang), show_alert=True)
            return

        await callback.answer("Fayllar yuborilmoqda...")
        for att in attachments:
            caption = f"📌 #{task.id} - {att.file_name or 'Fayl'}"
            try:
                if att.file_type == "photo":
                    await callback.bot.send_photo(chat_id=callback.from_user.id, photo=att.file_id, caption=caption)
                elif att.file_type == "video":
                    await callback.bot.send_video(chat_id=callback.from_user.id, video=att.file_id, caption=caption)
                elif att.file_type == "document":
                    await callback.bot.send_document(chat_id=callback.from_user.id, document=att.file_id, caption=caption)
                elif att.file_type == "audio":
                    await callback.bot.send_audio(chat_id=callback.from_user.id, audio=att.file_id, caption=caption)
            except Exception:
                pass

@router.callback_query(F.data.startswith("back_to_task:"))
async def handle_back_to_task(callback: CallbackQuery):
    task_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        task = await get_task_by_id(session, task_id)
        if not task:
            await callback.answer("Vazifa topilmadi!", show_alert=True)
            return

        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

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
            lang=lang,
            assignee_name=assignee_name,
            creator_name=creator_name,
            attachment_count=att_count
        )
        keyboard = get_task_card_keyboard(task, lang=lang, attachment_count=att_count)

        await callback.message.edit_text(text=card_text, reply_markup=keyboard, parse_mode="HTML")

