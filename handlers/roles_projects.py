from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.base import AsyncSessionLocal
from database.crud import (
    get_user_by_id,
    get_all_users,
    update_user_role,
    get_all_projects,
    get_or_create_project
)
from database.models import UserRole
from utils.permissions import is_admin
from locales import t
from keyboards.inline import (
    get_users_roles_keyboard,
    get_role_select_keyboard,
    get_cancel_keyboard
)

router = Router()

class ProjectCreateState(StatesGroup):
    waiting_name = State()

# --- 1. ROLLAR BOSHQARUVI (/xodimlar yoki /rollar) ---

@router.message(Command("xodimlar"))
@router.message(Command("rollar"))
async def handle_roles_management(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        if not is_admin(user, message.from_user.id):
            await message.reply(t("unauthorized", lang))
            return

        users = await get_all_users(session)
        if not users:
            await message.reply("Hozircha xodimlar ro'yxati bo'sh.")
            return

        keyboard = get_users_roles_keyboard(users, lang)
        await message.reply(t("roles_management_title", lang), reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("user_role_edit:"))
async def handle_select_user_for_role(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        admin_user = await get_user_by_id(session, callback.from_user.id)
        lang = admin_user.language if admin_user else "uz"

        if not is_admin(admin_user, callback.from_user.id):
            await callback.answer(t("unauthorized", lang), show_alert=True)
            return

        target_user = await get_user_by_id(session, target_id)
        if not target_user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return

        role_str = t(f"role_{target_user.role.value}", lang)
        text = t("role_change_prompt", lang, name=target_user.full_name, role=role_str)
        keyboard = get_role_select_keyboard(target_id, lang)

        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("set_role:"))
async def handle_save_user_role(callback: CallbackQuery):
    parts = callback.data.split(":")
    target_id = int(parts[1])
    role_name = parts[2]

    role_map = {
        "admin": UserRole.ADMIN,
        "manager": UserRole.MANAGER,
        "employee": UserRole.EMPLOYEE
    }
    new_role = role_map.get(role_name, UserRole.EMPLOYEE)

    async with AsyncSessionLocal() as session:
        admin_user = await get_user_by_id(session, callback.from_user.id)
        lang = admin_user.language if admin_user else "uz"

        if not is_admin(admin_user, callback.from_user.id):
            await callback.answer(t("unauthorized", lang), show_alert=True)
            return

        updated_user = await update_user_role(session, target_id, new_role)
        role_display = t(f"role_{new_role.value}", lang)

        await callback.answer(t("role_updated_success", lang, name=updated_user.full_name, role=role_display), show_alert=True)

        # Xodimlar ro'yxatiga qaytish
        users = await get_all_users(session)
        keyboard = get_users_roles_keyboard(users, lang)
        await callback.message.edit_text(t("roles_management_title", lang), reply_markup=keyboard, parse_mode="HTML")

# --- 2. LOYIHALAR BOSHQARUVI (/loyihalar) ---

@router.message(Command("loyihalar"))
async def handle_projects_list(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        projects = await get_all_projects(session)
        lines = [t("projects_title", lang)]

        if not projects:
            lines.append(t("projects_empty", lang))
        else:
            for p in projects:
                lines.append(f"📁 <b>{p.name}</b>" + (f" — <i>{p.description}</i>" if p.description else ""))

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=t("btn_create_project", lang), callback_data="add_project")]
            ]
        )

        await message.reply("\n".join(lines), reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "add_project")
async def handle_add_project_prompt(callback: CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

    await state.set_state(ProjectCreateState.waiting_name)
    await callback.message.answer(
        t("prompt_project_name", lang),
        reply_markup=get_cancel_keyboard(lang),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(ProjectCreateState.waiting_name)
async def handle_save_project(message: Message, state: FSMContext):
    proj_name = message.text.strip()
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        project = await get_or_create_project(session, proj_name)
        await message.answer(t("project_created_success", lang, name=project.name))

