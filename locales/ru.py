MESSAGES = {
    # Til tanlash va umumiy
    "choose_language": "Пожалуйста, выберите язык / Iltimos, tilni tanlang:",
    "lang_selected": "Язык успешно выбран: 🇷🇺 Русский",
    "group_lang_updated": "Язык группы изменен: 🇷🇺 Русский",
    "only_admin_can_change_lang": "Извините, только администратор группы может изменять язык группы.",
    "welcome": (
        "Здравствуйте, {name}!\n\n"
        "Добро пожаловать в бот управления командными задачами.\n"
        "Здесь вы можете просматривать назначенные вам задачи, "
        "отправлять отчеты о выполнении и создавать новые задачи.\n\n"
        "Основные команды:\n"
        "📌 /mening - Мои задачи\n"
        "➕ /yangi - Создать новую задачу\n"
        "🔄 /takroriy - Регулярные задачи\n"
        "📈 /statistika - Статистика и рейтинг команды\n"
        "📥 /eksport - Скачать Excel\n"
        "📁 /loyihalar - Список проектов\n"
        "👥 /xodimlar - Команда и роли (Админ)\n"
        "🌐 /til - Сменить язык\n"
        "📊 /panel - Панель задач"
    ),
    "unknown_user": "Пользователь",
    "unauthorized": "Извините, у вас недостаточно прав для выполнения этого действия.",
    "cancel": "❌ Отмена",
    "action_cancelled": "Действие отменено.",

    # Vazifa kartochkasi
    "task_card_title": "📌 <b>ЗАДАЧА #{id}</b>",
    "task_card_project": "📁 Проект: <b>{project}</b>",
    "task_card_assignee": "👤 Исполнитель: {assignee}",
    "task_card_creator": "👑 Поручил: {creator}",
    "task_card_priority": "🎯 Приоритет: {priority}",
    "task_card_status": "📊 Статус: <b>{status}</b>",
    "task_card_due_date": "⏰ Срок: <b>{due_date}</b>",
    "task_card_desc": "📝 Задача: {description}",
    "task_card_attachments": "📎 Файлы: {count} шт.",
    "task_card_comments": "💬 Комментарии: {count} шт.",

    # Holatlar
    "status_new": "🆕 Новая",
    "status_in_progress": "⚡ В процессе",
    "status_review": "👀 На проверке",
    "status_completed": "✅ Завершена",
    "status_cancelled": "❌ Отменена",

    # Muhimlik
    "priority_urgent": "🔴 Срочно",
    "priority_normal": "🟡 Обычный",
    "priority_low": "🟢 Низкий",

    # Tugmalar
    "btn_start_task": "🚀 Приступил",
    "btn_submit_review": "📤 На проверку",
    "btn_comment": "💬 Комментарии",
    "btn_add_attachment": "📎 Добавить файл",
    "btn_view_attachments": "📎 Просмотр файлов ({count})",
    "btn_approve": "✅ Утвердить",
    "btn_reject": "↩️ Вернуть с замечанием",
    "btn_view_in_group": "👥 Смотреть в группе",
    "btn_open_panel": "📱 Mini App Панель",

    # Izohlar
    "comments_title": "💬 <b>Комментарии по задаче #{id}:</b>\n\n",
    "no_comments": "К этой задаче пока нет комментариев.",
    "btn_add_comment": "✍️ Написать комментарий",
    "prompt_new_comment": "Пожалуйста, напишите ваш комментарий к задаче #{id}:",
    "comment_added_success": "✅ Комментарий успешно сохранен!",
    "notify_new_comment": "💬 <b>Новый комментарий к задаче #{id}!</b>\n\n👤 {author}: <i>{text}</i>",

    # Fayllar
    "prompt_send_file": "📎 Пожалуйста, отправьте файл (фото, видео, документ) для задачи #{id}:",
    "file_attached_success": "✅ Файл успешно прикреплен!",
    "no_attachments": "К этой задаче нет прикрепленных файлов.",

    # Vazifa xabarlari
    "task_started_notify": "⚡ Задача #{id} взята в работу исполнителем!",
    "task_not_assignee": "⚠️ Вы не являетесь исполнителем этой задачи!",
    "task_already_in_progress": "Эта задача уже в процессе выполнения.",
    "task_send_proof_prompt": (
        "📤 <b>Отчет по задаче #{id}:</b>\n\n"
        "Пожалуйста, отправьте подтверждение работы (фото, видео, документ или краткий текст).\n"
        "Если доказательство не требуется, нажмите 'Отправить без файлов'."
    ),
    "btn_just_submit": "➡️ Отправить без файлов",
    "proof_received_waiting_approval": "✅ Отчет принят и отправлен руководителю на проверку!",
    "proof_submitted_to_boss": (
        "👀 <b>Задача сдана на проверку!</b>\n\n"
        "📌 Задача: #{id} - <b>{title}</b>\n"
        "👤 Исполнитель: {assignee}\n"
        "📝 Описание: {proof_text}\n\n"
        "Пожалуйста, проверьте результат и утвердите или верните:"
    ),
    "task_approved_notify_user": "🎉 Поздравляем! Ваша задача (#{id} - {title}) утверждена руководителем и отмечена как выполненная!",
    "task_approved_group_notify": "✅ Задача #{id} успешно выполнена и утверждена!",
    "reject_prompt_reason": "Пожалуйста, напишите причину возврата задачи (будет показана сотруднику):",
    "task_rejected_notify_user": (
        "⚠️ <b>Ваша задача возвращена на доработку!</b>\n\n"
        "📌 Задача: #{id} - <b>{title}</b>\n"
        "↩️ Причина / Замечание: <i>{reason}</i>\n\n"
        "Задача возвращена в статус 'В процессе'. Исправьте замечания и отправьте повторно."
    ),
    "task_rejected_group_notify": "↩️ Задача #{id} возвращена в статус 'В процессе' из-за замечаний.",

    # Vazifa yaratish (FSM /yangi)
    "create_step_title": "📝 Введите название / описание новой задачи:",
    "create_step_assignee": "👤 Кому поручить задачу? Выберите сотрудника из списка:",
    "create_step_due_date": (
        "⏰ Укажите срок выполнения:\n"
        "Например: <i>сегодня 18:00</i>, <i>завтра</i>, <i>пятница 16:00</i>, <i>15.11 20:00</i>"
    ),
    "create_step_priority": "🎯 Выберите приоритет задачи:",
    "create_step_project": "📁 Выберите проект из списка или введите новый:",
    "create_step_recurring": "🔄 Будет ли задача повторяться?",
    "recurrence_none": "❌ Разовая (Не повторять)",
    "recurrence_daily": "🔄 Каждый день",
    "recurrence_weekly": "📅 Каждую неделю (Понедельник)",
    "recurrence_monthly": "🗓 Каждый месяц (1-е число)",
    "btn_skip": "⏭ Пропустить",
    "task_created_success": "✅ Задача успешно создана!",
    "recurring_created_success": "✅ Регулярная задача добавлена в расписание!",
    "task_assigned_private_notify": (
        "📬 <b>Вам назначена новая задача!</b>\n\n"
        "📌 <b>{title}</b>\n"
        "📁 Проект: {project}\n"
        "🎯 Приоритет: {priority}\n"
        "⏰ Срок: <b>{due_date}</b>\n"
        "👑 Поручил: {creator}"
    ),
    "user_not_found_group": "⚠️ Сотрудник не найден. Он должен хотя бы один раз запустить бота через /start.",
    "unlinked_task_assigned": "📌 Вы присоединились к боту! {count} задач(и), назначенных на вас, привязаны к вашему аккаунту.",

    # Takroriy vazifalar boshqaruvi (/takroriy)
    "recurring_list_title": "🔄 <b>РЕГУЛЯРНЫЕ ЗАДАЧИ:</b>\n\n",
    "recurring_empty": "На данный момент нет активных регулярных задач.",

    # Rollar
    "roles_management_title": "👥 <b>УПРАВЛЕНИЕ КОМАНДОЙ И РОЛЯМИ:</b>\n\nНажмите на сотрудника, чтобы изменить его роль:",
    "role_admin": "👑 Администратор",
    "role_manager": "👔 Менеджер",
    "role_employee": "👤 Сотрудник",
    "role_change_prompt": "Пользователь: <b>{name}</b>\nТекущая роль: {role}\n\nВыберите новую роль:",
    "role_updated_success": "✅ Роль сотрудника {name} изменена на {role}!",

    # Loyihalar
    "projects_title": "📁 <b>СПИСОК ПРОЕКТОВ:</b>\n\n",
    "projects_empty": "Пока нет добавленных проектов.",
    "btn_create_project": "➕ Добавить проект",
    "prompt_project_name": "📁 Введите название нового проекта (например: <i>Xon Saroy</i> или <i>Damoling</i>):",
    "project_created_success": "✅ Проект '{name}' успешно создан!",

    # Eslatmalar
    "reminder_24h": (
        "⏳ <b>НАПОМИНАНИЕ: ОСТАЛСЯ 1 ДЕНЬ!</b>\n\n"
        "👤 Исполнитель: {assignee}\n"
        "📌 Задача #{id}: <b>{title}</b>\n"
        "⏰ Срок: <b>{due_date}</b>"
    ),
    "reminder_2h": (
        "⚡ <b>ВНИМАНИЕ: ОСТАЛОСЬ 2 ЧАСА!</b>\n\n"
        "👤 Исполнитель: {assignee}\n"
        "📌 Задача #{id}: <b>{title}</b>\n"
        "⏰ Срок: <b>{due_date}</b>"
    ),
    "reminder_overdue": (
        "🚨 <b>СРОК ИСТЕК! ПРОСРОЧКА!</b>\n\n"
        "👤 Исполнитель: {assignee}\n"
        "📌 Задача #{id}: <b>{title}</b>\n"
        "⏰ Срок был: <b>{due_date}</b> (просрочено на {overdue_str})\n"
        "Пожалуйста, завершите задачу или продлите срок!"
    ),

    # Statistika va Reyting (/statistika)
    "stats_title": "📊 <b>СТАТИСТИКА И KPI СОТРУДНИКОВ (ЗА {days} ДНЕЙ)</b>\n\n",
    "stats_empty": "На данный момент нет данных для статистики.",
    "stats_user_line": (
        "👤 <b>{name}</b>:\n"
        "  • Всего задач: <b>{total} шт.</b>\n"
        "  • Выполнено: <b>{completed} шт.</b>\n"
        "  • В срок: <b>{on_time_rate}%</b>\n"
        "  • Средняя задержка: <b>{avg_delay} ч.</b>\n\n"
    ),
    "stats_top_performer": "🏆 <b>ЛУЧШИЙ СОТРУДНИК:</b> {name} (Выполнено: {count} шт., {pct}%)\n\n",

    # Eksport (/eksport)
    "export_caption": "📊 <b>Полный отчет по всем задачам в формате Excel</b>\nДата: {date}",
    "export_btn_excel": "📥 Скачать Excel файл",

    # Hisobotlar
    "morning_report_title": "📊 <b>ЕЖЕДНЕВНЫЙ УТРЕННИЙ ОТЧЕТ ({date})</b>\n",
    "report_section_completed": "✅ <b>Выполнено за последние 24 часа:</b>\n{items}\n",
    "report_section_review": "👀 <b>На проверке:</b>\n{items}\n",
    "report_section_in_progress": "⚡ <b>В процессе:</b>\n{items}\n",
    "report_section_new": "🆕 <b>Не начато (Новые):</b>\n{items}\n",
    "report_section_due_today": "⏰ <b>Срок сегодня:</b>\n{items}\n",
    "report_section_overdue": "🚨 <b>Просроченные задачи:</b>\n{items}\n",
    "report_no_tasks": "На данный момент задач нет.",
    "report_none": "— Нет",

    # Kechki hisobot
    "evening_report_title": "🌙 <b>ВЕЧЕРНИЙ ОТЧЕТ — ИТОГИ ДНЯ ({date})</b>\n\n",
    "evening_section_completed": "✅ <b>Успешно выполнено сегодня:</b>\n{items}\n\n",
    "evening_section_overdue": "🚨 <b>Просроченные / Отстающие задачи:</b>\n{items}\n\n",
    "evening_section_active": "⚡ <b>Активные задачи, перешедшие на завтра:</b>\n{items}",

    # Shaxsiy kunlik ro'yxat
    "daily_personal_title": "☀️ <b>Доброе утро, {name}!</b>\n📅 Список ваших задач на сегодня ({date}):\n\n",
    "daily_personal_due_today": "⏰ <b>Нужно сдать сегодня:</b>\n{items}\n\n",
    "daily_personal_overdue": "🚨 <b>Просроченные задачи:</b>\n{items}\n\n",
    "daily_personal_other": "📌 <b>Другие активные задачи:</b>\n{items}",
    "daily_personal_empty": "Сегодня у вас нет срочных или просроченных задач. Продуктивного дня! 🚀",

    # Mening vazifalarim
    "my_tasks_title": "📋 <b>Ваши активные задачи ({count}):</b>\n\n",
    "my_tasks_empty": "У вас пока нет активных задач. Отличная работа! 👍",
    "group_tasks_title": "📋 <b>Активные задачи группы ({count}):</b>\n\n",
    "group_tasks_empty": "В группе пока нет активных задач.",
}

