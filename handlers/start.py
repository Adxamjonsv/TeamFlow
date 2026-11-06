from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from database.base import AsyncSessionLocal
from database.crud import (
    get_or_create_user,
    update_user_language,
    update_group_language,
    get_or_create_group,
    link_tasks_by_username,
    get_user_by_id
)
from locales import t
from keyboards.inline import get_language_keyboard, get_group_language_keyboard, get_panel_keyboard
from utils.permissions import is_admin

router = Router()

@router.message(CommandStart())
async def handle_start(message: Message):
    if message.chat.type != "private":
        return

    async with AsyncSessionLocal() as session:
        user, created = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

        linked_count = 0
        if message.from_user.username:
            linked_count = await link_tasks_by_username(
                session,
                message.from_user.username,
                message.from_user.id
            )

        if created:
            await message.answer(
                t("choose_language", "uz"),
                reply_markup=get_language_keyboard()
            )
        else:
            lang = user.language or "uz"
            welcome_text = t("welcome", lang, name=message.from_user.first_name)
            if linked_count > 0:
                welcome_text += "\n\n" + t("unlinked_task_assigned", lang, count=linked_count)
            await message.answer(welcome_text, reply_markup=get_panel_keyboard(lang))

@router.callback_query(F.data.startswith("set_lang:"))
async def handle_set_language(callback: CallbackQuery):
    lang = callback.data.split(":")[1]
    async with AsyncSessionLocal() as session:
        user = await update_user_language(session, callback.from_user.id, lang)
        
        linked_count = 0
        if callback.from_user.username:
            linked_count = await link_tasks_by_username(
                session,
                callback.from_user.username,
                callback.from_user.id
            )

        await callback.answer(t("lang_selected", lang))
        welcome_text = t("welcome", lang, name=callback.from_user.first_name)
        if linked_count > 0:
            welcome_text += "\n\n" + t("unlinked_task_assigned", lang, count=linked_count)

        await callback.message.edit_text(welcome_text, reply_markup=get_panel_keyboard(lang))

@router.message(Command("til"))
async def handle_change_language(message: Message):
    if message.chat.type == "private":
        await message.answer(
            t("choose_language", "uz"),
            reply_markup=get_language_keyboard()
        )
    else:
        chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in ("creator", "administrator"):
            async with AsyncSessionLocal() as session:
                group = await get_or_create_group(session, message.chat.id, message.chat.title)
                lang = group.language or "uz"
                await message.reply(t("only_admin_can_change_lang", lang))
                return

        await message.reply(
            "Guruh tili / Язык группы:",
            reply_markup=get_group_language_keyboard()
        )

@router.callback_query(F.data.startswith("set_group_lang:"))
async def handle_set_group_language(callback: CallbackQuery):
    chat_member = await callback.bot.get_chat_member(callback.message.chat.id, callback.from_user.id)
    if chat_member.status not in ("creator", "administrator"):
        await callback.answer(t("only_admin_can_change_lang", "uz"), show_alert=True)
        return

    lang = callback.data.split(":")[1]
    async with AsyncSessionLocal() as session:
        await update_group_language(session, callback.message.chat.id, lang)
        await callback.answer(t("group_lang_updated", lang))
        await callback.message.edit_text(t("group_lang_updated", lang))

@router.message(Command("panel"))
async def handle_open_panel(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"
        await message.reply(
            "📱 Mini App Admin Panel:\nQuyidagi tugma orqali boshqaruv panelini ochishingiz mumkin:"
            if lang == "uz" else
            "📱 Mini App Панель управления:\nВы можете открыть панель управления с помощью кнопки ниже:",
            reply_markup=get_panel_keyboard(lang)
        )

