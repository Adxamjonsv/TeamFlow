from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.base import AsyncSessionLocal
from database.crud import (
    get_or_create_user,
    get_all_users,
    get_user_by_id,
    create_task,
    get_all_projects,
    get_or_create_project,
    create_recurring_task
)
from database.models import UserRole, TaskPriority, RecurringFrequency
from utils.permissions import can_create_task
from utils.date_parser import parse_deadline, format_datetime_for_user
from locales import t
from keyboards.inline import (
    get_priority_choice_keyboard,
    get_skip_keyboard,
    get_cancel_keyboard,
    get_projects_choice_keyboard,
    get_recurrence_choice_keyboard
)
from services.notification import notify_assignee_new_task

router = Router()

class CreateTaskState(StatesGroup):
    title = State()
    assignee = State()
    due_date = State()
    priority = State()
    project = State()
    recurring = State()

@router.message(Command("yangi"))
async def start_create_task(message: Message, state: FSMContext):
    if message.chat.type != "private":
        await message.reply("Vazifa yaratish buyrug'i shaxsiy chatda ishlaydi: @...")
        return

    async with AsyncSessionLocal() as session:
        user, _ = await get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )
        lang = user.language or "uz"

        if not can_create_task(user, message.from_user.id):
            await message.reply(t("unauthorized", lang))
            return

        await state.set_state(CreateTaskState.title)
        await message.answer(
            t("create_step_title", lang),
            reply_markup=get_cancel_keyboard(lang)
        )

@router.callback_query(F.data == "cancel_action")
async def cancel_action_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(t("action_cancelled", "uz"))
    await callback.answer()

@router.message(CreateTaskState.title)
async def process_task_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("Iltimos, vazifa nomini yozing:")
        return

    await state.update_data(title=title)

    async with AsyncSessionLocal() as session:
        users = await get_all_users(session)
        user_db = await get_user_by_id(session, message.from_user.id)
        lang = user_db.language if user_db else "uz"

        if not users:
            await message.answer(
                "Hozircha botda xodimlar ro'yxatdan o'tmagan. Xodimlar botga /start bosishlari kerak."
            )
            await state.clear()
            return

        keyboard_buttons = []
        for u in users:
            name = u.full_name
            if u.username:
                name += f" (@{u.username})"
            keyboard_buttons.append([
                InlineKeyboardButton(text=name, callback_data=f"assignee_select:{u.telegram_id}")
            ])
        keyboard_buttons.append([
            InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_action")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        await state.set_state(CreateTaskState.assignee)
        await message.answer(t("create_step_assignee", lang), reply_markup=keyboard)

@router.callback_query(CreateTaskState.assignee, F.data.startswith("assignee_select:"))
async def process_assignee_choice(callback: CallbackQuery, state: FSMContext):
    assignee_id = int(callback.data.split(":")[1])
    await state.update_data(assignee_id=assignee_id)

    async with AsyncSessionLocal() as session:
        user_db = await get_user_by_id(session, callback.from_user.id)
        lang = user_db.language if user_db else "uz"

    await state.set_state(CreateTaskState.due_date)
    await callback.message.edit_text(
        t("create_step_due_date", lang),
        reply_markup=get_skip_keyboard(lang),
        parse_mode="HTML"
    )

@router.message(CreateTaskState.due_date)
async def process_due_date_text(message: Message, state: FSMContext):
    parsed_date, _ = parse_deadline(message.text)
    await state.update_data(due_date=parsed_date)

    async with AsyncSessionLocal() as session:
        user_db = await get_user_by_id(session, message.from_user.id)
        lang = user_db.language if user_db else "uz"

    await state.set_state(CreateTaskState.priority)
    await message.answer(
        t("create_step_priority", lang),
        reply_markup=get_priority_choice_keyboard(lang)
    )

@router.callback_query(CreateTaskState.due_date, F.data == "skip_step")
async def skip_due_date(callback: CallbackQuery, state: FSMContext):
    await state.update_data(due_date=None)

    async with AsyncSessionLocal() as session:
        user_db = await get_user_by_id(session, callback.from_user.id)
        lang = user_db.language if user_db else "uz"

    await state.set_state(CreateTaskState.priority)
    await callback.message.edit_text(
        t("create_step_priority", lang),
        reply_markup=get_priority_choice_keyboard(lang)
    )

@router.callback_query(CreateTaskState.priority, F.data.startswith("priority:"))
async def process_priority_choice(callback: CallbackQuery, state: FSMContext):
    p_map = {
        "priority:urgent": TaskPriority.URGENT,
        "priority:normal": TaskPriority.NORMAL,
        "priority:low": TaskPriority.LOW
    }
    priority = p_map.get(callback.data, TaskPriority.NORMAL)
    await state.update_data(priority=priority)

    async with AsyncSessionLocal() as session:
        user_db = await get_user_by_id(session, callback.from_user.id)
        lang = user_db.language if user_db else "uz"
        projects = await get_all_projects(session)

    await state.set_state(CreateTaskState.project)
    keyboard = get_projects_choice_keyboard(projects, lang)
    await callback.message.edit_text(
        t("create_step_project", lang),
        reply_markup=keyboard
    )

@router.callback_query(CreateTaskState.project, F.data.startswith("project_select:"))
async def process_project_choice(callback: CallbackQuery, state: FSMContext):
    project_name = callback.data.split(":")[1]
    await state.update_data(project=project_name)
    await prompt_recurrence(callback.message, state, is_callback=True)

@router.message(CreateTaskState.project)
async def process_project_text(message: Message, state: FSMContext):
    project = message.text.strip()
    await state.update_data(project=project)
    await prompt_recurrence(message, state, is_callback=False)

@router.callback_query(CreateTaskState.project, F.data == "skip_step")
async def skip_project(callback: CallbackQuery, state: FSMContext):
    await state.update_data(project=None)
    await prompt_recurrence(callback.message, state, is_callback=True)

async def prompt_recurrence(message: Message, state: FSMContext, is_callback: bool = False):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.chat.id)
        lang = user.language if user else "uz"

    await state.set_state(CreateTaskState.recurring)
    keyboard = get_recurrence_choice_keyboard(lang)
    text = t("create_step_recurring", lang)

    if is_callback:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(CreateTaskState.recurring, F.data.startswith("rec:"))
async def process_recurrence_choice(callback: CallbackQuery, state: FSMContext):
    rec_type = callback.data.split(":")[1]
    data = await state.get_data()
    await state.clear()

    title = data.get("title")
    assignee_id = data.get("assignee_id")
    due_date = data.get("due_date")
    priority = data.get("priority", TaskPriority.NORMAL)
    project = data.get("project")

    async with AsyncSessionLocal() as session:
        creator_id = callback.message.chat.id
        creator_user = await get_user_by_id(session, creator_id)
        lang = creator_user.language if creator_user else "uz"

        assignee_user = await get_user_by_id(session, assignee_id)
        assignee_username = assignee_user.username if assignee_user else None

        # 1. Hozirgi vazifani yaratish
        task = await create_task(
            session=session,
            title=title,
            creator_id=creator_id,
            assignee_id=assignee_id,
            assignee_username=assignee_username,
            priority=priority,
            project=project,
            due_date=due_date
        )

        # 2. Agar takrorlanuvchi bo'lsa, jadvalga kiritish
        rec_msg = ""
        if rec_type != "none":
            freq_map = {
                "daily": RecurringFrequency.DAILY,
                "weekly": RecurringFrequency.WEEKLY,
                "monthly": RecurringFrequency.MONTHLY
            }
            freq = freq_map.get(rec_type, RecurringFrequency.WEEKLY)
            await create_recurring_task(
                session=session,
                title=title,
                creator_id=creator_id,
                frequency=freq,
                assignee_id=assignee_id,
                assignee_username=assignee_username,
                priority=priority,
                project=project,
                day_of_week=0, # Dushanba
                day_of_month=1
            )
            rec_msg = f"\n🔄 {t('recurring_created_success', lang)}"

        # Ijrochiga bildirishnoma
        await notify_assignee_new_task(
            bot=callback.bot,
            task=task,
            creator_name=creator_user.full_name if creator_user else "Admin"
        )

    success_text = t("task_created_success", lang) + f"\n\n📌 #{task.id} - <b>{task.title}</b>{rec_msg}"
    await callback.message.edit_text(success_text, parse_mode="HTML")
    await callback.answer()

