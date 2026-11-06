from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from database.models import Task, TaskStatus, TaskPriority, User, UserRole, Project, RecurringTask, RecurringFrequency
from locales import t
from config import settings

def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru"),
            ]
        ]
    )

def get_group_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_group_lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_group_lang:ru"),
            ]
        ]
    )

def get_task_card_keyboard(task: Task, lang: str = "uz", attachment_count: int = 0) -> InlineKeyboardMarkup:
    buttons = []

    # 1. Asosiy holat tugmasi
    if task.status == TaskStatus.NEW:
        buttons.append([
            InlineKeyboardButton(text=t("btn_start_task", lang), callback_data=f"task_start:{task.id}")
        ])
    elif task.status == TaskStatus.IN_PROGRESS:
        buttons.append([
            InlineKeyboardButton(text=t("btn_submit_review", lang), callback_data=f"task_review:{task.id}")
        ])
    elif task.status == TaskStatus.REVIEW:
        buttons.append([
            InlineKeyboardButton(text="👀 Tekshiruvda...", callback_data=f"task_info:{task.id}")
        ])

    # 2. Izohlar va Fayllar tugmalari
    att_text = f"📎 Fayllar ({attachment_count})" if lang == "uz" else f"📎 Файлы ({attachment_count})"
    buttons.append([
        InlineKeyboardButton(text=t("btn_comment", lang), callback_data=f"task_comments:{task.id}"),
        InlineKeyboardButton(text=att_text, callback_data=f"task_files:{task.id}")
    ])

    # 3. Mini App yoki panel tugmasi
    if settings.WEBAPP_URL:
        if settings.WEBAPP_URL.startswith("https://"):
            buttons.append([
                InlineKeyboardButton(text=t("btn_open_panel", lang), web_app=WebAppInfo(url=settings.WEBAPP_URL))
            ])
        else:
            buttons.append([
                InlineKeyboardButton(text=t("btn_open_panel", lang), url=settings.WEBAPP_URL)
            ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_panel_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    url = settings.WEBAPP_URL or "http://localhost:8000"
    if url.startswith("https://"):
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📱 Mini App Panelni ochish" if lang == "uz" else "📱 Открыть Mini App Панель", web_app=WebAppInfo(url=url))]
            ]
        )
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📱 Panelni ochish (Brauzer)" if lang == "uz" else "📱 Открыть Панель", url=url)]
            ]
        )

def get_comments_menu_keyboard(task_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_add_comment", lang), callback_data=f"add_comment:{task_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga" if lang == "uz" else "🔙 Назад", callback_data=f"back_to_task:{task_id}")
            ]
        ]
    )

def get_files_menu_keyboard(task_id: int, count: int, lang: str = "uz") -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("btn_add_attachment", lang), callback_data=f"add_file:{task_id}")]
    ]
    if count > 0:
        rows.append([
            InlineKeyboardButton(text=t("btn_view_attachments", lang, count=count), callback_data=f"view_files:{task_id}")
        ])
    rows.append([
        InlineKeyboardButton(text="🔙 Orqaga" if lang == "uz" else "🔙 Назад", callback_data=f"back_to_task:{task_id}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_boss_approval_keyboard(task_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_approve", lang), callback_data=f"boss_approve:{task_id}"),
                InlineKeyboardButton(text=t("btn_reject", lang), callback_data=f"boss_reject:{task_id}")
            ]
        ]
    )

def get_just_submit_keyboard(task_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("btn_just_submit", lang), callback_data=f"submit_no_proof:{task_id}")
            ],
            [
                InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_action")
            ]
        ]
    )

def get_priority_choice_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔴 Shoshilinch" if lang == "uz" else "🔴 Срочно", callback_data="priority:urgent"),
                InlineKeyboardButton(text="🟡 Oddiy" if lang == "uz" else "🟡 Обычный", callback_data="priority:normal"),
                InlineKeyboardButton(text="🟢 Past" if lang == "uz" else "🟢 Низкий", callback_data="priority:low"),
            ]
        ]
    )

def get_recurrence_choice_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("recurrence_none", lang), callback_data="rec:none")],
            [InlineKeyboardButton(text=t("recurrence_daily", lang), callback_data="rec:daily")],
            [InlineKeyboardButton(text=t("recurrence_weekly", lang), callback_data="rec:weekly")],
            [InlineKeyboardButton(text=t("recurrence_monthly", lang), callback_data="rec:monthly")],
        ]
    )

def get_recurring_list_keyboard(recurring_tasks: list[RecurringTask], lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = []
    freq_map = {
        RecurringFrequency.DAILY: "Har kuni" if lang == "uz" else "Ежедневно",
        RecurringFrequency.WEEKLY: "Har hafta" if lang == "uz" else "Еженедельно",
        RecurringFrequency.MONTHLY: "Har oy" if lang == "uz" else "Ежемесячно",
    }
    for r in recurring_tasks:
        status_icon = "🟢" if r.is_active else "🔴"
        freq_str = freq_map.get(r.frequency, "")
        text = f"{status_icon} #{r.id} {r.title} ({freq_str})"
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f"rec_info:{r.id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_recurring_item_keyboard(rec: RecurringTask, lang: str = "uz") -> InlineKeyboardMarkup:
    toggle_text = "⏸ To'xtatish" if rec.is_active else "▶️ Yoqish"
    if lang == "ru":
        toggle_text = "⏸ Приостановить" if rec.is_active else "▶️ Активировать"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=toggle_text, callback_data=f"rec_toggle:{rec.id}"),
                InlineKeyboardButton(text="🗑 O'chirish" if lang == "uz" else "🗑 Удалить", callback_data=f"rec_delete:{rec.id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Orqaga" if lang == "uz" else "🔙 Назад", callback_data="rec_back")
            ]
        ]
    )

def get_stats_period_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="7 kunlik" if lang == "uz" else "7 дней", callback_data="stats_days:7"),
                InlineKeyboardButton(text="30 kunlik" if lang == "uz" else "30 дней", callback_data="stats_days:30"),
                InlineKeyboardButton(text="90 kunlik" if lang == "uz" else "90 дней", callback_data="stats_days:90"),
            ]
        ]
    )

def get_projects_choice_keyboard(projects: list[Project], lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = []
    for p in projects:
        buttons.append([InlineKeyboardButton(text=f"📁 {p.name}", callback_data=f"project_select:{p.name}")])
    buttons.append([InlineKeyboardButton(text=t("btn_skip", lang), callback_data="skip_step")])
    buttons.append([InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_users_roles_keyboard(users: list[User], lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = []
    role_icons = {
        UserRole.ADMIN: "👑",
        UserRole.MANAGER: "👔",
        UserRole.EMPLOYEE: "👤"
    }
    for u in users:
        icon = role_icons.get(u.role, "👤")
        name = u.full_name
        if u.username:
            name += f" (@{u.username})"
        buttons.append([
            InlineKeyboardButton(text=f"{icon} {name}", callback_data=f"user_role_edit:{u.telegram_id}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_role_select_keyboard(telegram_id: int, lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("role_admin", lang), callback_data=f"set_role:{telegram_id}:admin")],
            [InlineKeyboardButton(text=t("role_manager", lang), callback_data=f"set_role:{telegram_id}:manager")],
            [InlineKeyboardButton(text=t("role_employee", lang), callback_data=f"set_role:{telegram_id}:employee")],
            [InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_action")]
        ]
    )

def get_skip_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_skip", lang), callback_data="skip_step")],
            [InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_action")]
        ]
    )

def get_cancel_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("cancel", lang), callback_data="cancel_action")]
        ]
    )

