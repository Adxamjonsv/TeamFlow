MESSAGES = {
    # Til tanlash va umumiy
    "choose_language": "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
    "lang_selected": "Til muvaffaqiyatli tanlandi: 🇺🇿 O'zbekcha",
    "group_lang_updated": "Guruh tili o'zgartirildi: 🇺🇿 O'zbekcha",
    "only_admin_can_change_lang": "Kechirasiz, guruh tilini faqat guruh administratori o'zgartira oladi.",
    "welcome": (
        "Assalomu alaykum, {name}!\n\n"
        "Jamoa vazifalarini boshqarish botiga xush kelibsiz.\n"
        "Bu yerda siz o'zingizga biriktirilgan vazifalarni ko'rishingiz, "
        "bajarilishi bo'yicha hisobot berishingiz va yangi vazifalar yaratishingiz mumkin.\n\n"
        "Asosiy buyruqlar:\n"
        "📌 /mening - Mening vazifalarim\n"
        "➕ /yangi - Yangi vazifa yaratish\n"
        "🔄 /takroriy - Takroriy vazifalar\n"
        "📈 /statistika - Xodimlar statistikasi va reyting\n"
        "📥 /eksport - Excel yuklab olish\n"
        "📁 /loyihalar - Loyihalar ro'yxati\n"
        "👥 /xodimlar - Jamoa va rollar (Admin)\n"
        "🌐 /til - Tilni o'zgartirish\n"
        "📊 /panel - Vazifalar paneli"
    ),
    "unknown_user": "Foydalanuvchi",
    "unauthorized": "Kechirasiz, sizda ushbu amalni bajarish uchun yetarli ruxsat yo'q.",
    "cancel": "❌ Bekor qilish",
    "action_cancelled": "Amal bekor qilindi.",

    # Vazifa kartochkasi
    "task_card_title": "📌 <b>VAZIFA #{id}</b>",
    "task_card_project": "📁 Loyiha: <b>{project}</b>",
    "task_card_assignee": "👤 Ijrochi: {assignee}",
    "task_card_creator": "👑 Biriktiruvchi: {creator}",
    "task_card_priority": "🎯 Muhimlik: {priority}",
    "task_card_status": "📊 Holat: <b>{status}</b>",
    "task_card_due_date": "⏰ Muddat: <b>{due_date}</b>",
    "task_card_desc": "📝 Vazifa: {description}",
    "task_card_attachments": "📎 Fayllar: {count} ta",
    "task_card_comments": "💬 Izohlar: {count} ta",

    # Holatlar
    "status_new": "🆕 Yangi",
    "status_in_progress": "⚡ Jarayonda",
    "status_review": "👀 Tekshiruvda",
    "status_completed": "✅ Bajarildi",
    "status_cancelled": "❌ Bekor qilingan",

    # Muhimlik
    "priority_urgent": "🔴 Shoshilinch",
    "priority_normal": "🟡 Oddiy",
    "priority_low": "🟢 Past",

    # Tugmalar
    "btn_start_task": "🚀 Boshladim",
    "btn_submit_review": "📤 Tekshiruvga yuborish",
    "btn_comment": "💬 Izohlar",
    "btn_add_attachment": "📎 Fayl qo'shish",
    "btn_view_attachments": "📎 Fayllarni ko'rish ({count})",
    "btn_approve": "✅ Tasdiqlash",
    "btn_reject": "↩️ Izoh bilan qaytarish",
    "btn_view_in_group": "👥 Guruhda ko'rish",
    "btn_open_panel": "📱 Mini App Panel",

    # Izohlar
    "comments_title": "💬 <b>Vazifa #{id} bo'yicha izohlar:</b>\n\n",
    "no_comments": "Ushbu vazifada hali hech qanday izoh yo'q.",
    "btn_add_comment": "✍️ Izoh yozish",
    "prompt_new_comment": "Iltimos, vazifa #{id} uchun o'z izohingizni yozing:",
    "comment_added_success": "✅ Izohingiz muvaffaqiyatli saqlindi!",
    "notify_new_comment": "💬 <b>Vazifa #{id} ga yangi izoh qo'shildi!</b>\n\n👤 {author}: <i>{text}</i>",

    # Fayllar
    "prompt_send_file": "📎 Iltimos, vazifa #{id} ga biriktirmoqchi bo'lgan faylni (rasm, video, hujjat) yuboring:",
    "file_attached_success": "✅ Fayl muvaffaqiyatli biriktirildi!",
    "no_attachments": "Ushbu vazifaga biriktirilgan fayllar yo'q.",

    # Vazifa xabarlari
    "task_started_notify": "⚡ Vazifa #{id} ijrochi tomonidan boshlandi!",
    "task_not_assignee": "⚠️ Kechirasiz, siz ushbu vazifa ijrochisi emassiz!",
    "task_already_in_progress": "Bu vazifa allaqachon jarayonda.",
    "task_send_proof_prompt": (
        "📤 <b>Vazifa #{id} bo'yicha hisobot:</b>\n\n"
        "Iltimos, ishning isboti sifatida rasm, video, hujjat yoki qisqa matn yuboring.\n"
        "Agar isbot kerak bo'lmasa, 'Shunchaki yuborish' tugmasini bosing."
    ),
    "btn_just_submit": "➡️ Isbotsiz yuborish",
    "proof_received_waiting_approval": "✅ Isbot qabul qilindi va tekshirish uchun rahbarga yuborildi!",
    "proof_submitted_to_boss": (
        "👀 <b>Vazifa tekshiruvga topshirildi!</b>\n\n"
        "📌 Vazifa: #{id} - <b>{title}</b>\n"
        "👤 Ijrochi: {assignee}\n"
        "📝 Izoh: {proof_text}\n\n"
        "Iltimos, natijani tekshirib tasdiqlang yoki qaytaring:"
    ),
    "task_approved_notify_user": "🎉 Tabriklaymiz! Sizning vazifangiz (#{id} - {title}) rahbar tomonidan tasdiqlandi va bajarildi deb belgilandi!",
    "task_approved_group_notify": "✅ Vazifa #{id} muvaffaqiyatli bajarildi va tasdiqlandi!",
    "reject_prompt_reason": "Iltimos, vazifani nima sababdan qaytarayotganingizni yozing (xodimga ko'rsatiladi):",
    "task_rejected_notify_user": (
        "⚠️ <b>Vazifangiz qaytarildi!</b>\n\n"
        "📌 Vazifa: #{id} - <b>{title}</b>\n"
        "↩️ Sabab / Izoh: <i>{reason}</i>\n\n"
        "Vazifa qaytadan 'Jarayonda' holatiga o'tkazildi. Kamchiliklarni bartaraf etib qayta topshiring."
    ),
    "task_rejected_group_notify": "↩️ Vazifa #{id} kamchiliklar sababli yana 'Jarayonda' holatiga qaytarildi.",

    # Vazifa yaratish (FSM /yangi)
    "create_step_title": "📝 Yangi vazifa nomini / matnini kiriting:",
    "create_step_assignee": "👤 Vazifani kimga biriktirmoqchisiz? Quyidagi xodimlardan birini tanlang:",
    "create_step_due_date": (
        "⏰ Vazifa muddatini kiriting:\n"
        "Misol: <i>bugun 18:00</i>, <i>ertaga</i>, <i>juma 16:00</i>, <i>15.11 20:00</i>"
    ),
    "create_step_priority": "🎯 Muhimlik darajasini tanlang:",
    "create_step_project": "📁 Loyiha nomini tanlang yoki yangisini yozing:",
    "create_step_recurring": "🔄 Ushbu vazifa takrorlansinmi?",
    "recurrence_none": "❌ Bir martalik (Takrorlanmaydi)",
    "recurrence_daily": "🔄 Har kuni",
    "recurrence_weekly": "📅 Har hafta (Dushanba)",
    "recurrence_monthly": "🗓 Har oy (1-sana)",
    "btn_skip": "⏭ O'tkazish",
    "task_created_success": "✅ Vazifa muvaffaqiyatli yaratildi!",
    "recurring_created_success": "✅ Takrorlanuvchi vazifa jadvalga kiritildi!",
    "task_assigned_private_notify": (
        "📬 <b>Sizga yangi vazifa biriktirildi!</b>\n\n"
        "📌 <b>{title}</b>\n"
        "📁 Loyiha: {project}\n"
        "🎯 Muhimlik: {priority}\n"
        "⏰ Muddat: <b>{due_date}</b>\n"
        "👑 Biriktiruvchi: {creator}"
    ),
    "user_not_found_group": "⚠️ Xodim topilmadi. U botdan kamida bir marta /start o'tgan bo'lishi kerak.",
    "unlinked_task_assigned": "📌 Siz botga qo'shildingiz! Sizning nomingizga biriktirilgan {count} ta vazifa profilingizga bog'landi.",

    # Takroriy vazifalar boshqaruvi (/takroriy)
    "recurring_list_title": "🔄 <b>TAKRORLANUVCHI VAZIFALAR:</b>\n\n",
    "recurring_empty": "Hozircha faol takroriy vazifalar mavjud emas.",

    # Rollar
    "roles_management_title": "👥 <b>JAMOA VA ROLLAR BOSHQARUVI:</b>\n\nQuyidagi xodim ustiga bosib uning rolini o'zgartirishingiz mumkin:",
    "role_admin": "👑 Administrator",
    "role_manager": "👔 Menejer",
    "role_employee": "👤 Xodim",
    "role_change_prompt": "Foydalanuvchi: <b>{name}</b>\nHozirgi roli: {role}\n\nYangi rolni tanlang:",
    "role_updated_success": "✅ {name} ning roli {role} ga o'zgartirildi!",

    # Loyihalar
    "projects_title": "📁 <b>LOYIHALAR RO'YXATI:</b>\n\n",
    "projects_empty": "Hozircha hech qanday loyiha qo'shilmagan.",
    "btn_create_project": "➕ Yangi loyiha qo'shish",
    "prompt_project_name": "📁 Yangi loyiha nomini kiriting (masalan: <i>Xon Saroy</i> yoki <i>Damoling</i>):",
    "project_created_success": "✅ '{name}' loyihasi muvaffaqiyatli yaratildi!",

    # Eslatmalar
    "reminder_24h": (
        "⏳ <b>ESLATMA: 1 KUN QOLDI!</b>\n\n"
        "👤 Ijrochi: {assignee}\n"
        "📌 Vazifa #{id}: <b>{title}</b>\n"
        "⏰ Muddat: <b>{due_date}</b>"
    ),
    "reminder_2h": (
        "⚡ <b>SHOSHILING: 2 SOAT QOLDI!</b>\n\n"
        "👤 Ijrochi: {assignee}\n"
        "📌 Vazifa #{id}: <b>{title}</b>\n"
        "⏰ Muddat: <b>{due_date}</b>"
    ),
    "reminder_overdue": (
        "🚨 <b>MUDDATI O'TDI!</b>\n\n"
        "👤 Ijrochi: {assignee}\n"
        "📌 Vazifa #{id}: <b>{title}</b>\n"
        "⏰ Muddat edi: <b>{due_date}</b> ({overdue_str} kechikmoqda)\n"
        "Iltimos, tezroq topshiring yoki muddatni uzaytiring!"
    ),

    # Statistika va Reyting (/statistika)
    "stats_title": "📊 <b>XODIMLAR STATISTIKASI VA KPI ({days} KUNLIK)</b>\n\n",
    "stats_empty": "Hozircha statistika uchun ma'lumotlar mavjud emas.",
    "stats_user_line": (
        "👤 <b>{name}</b>:\n"
        "  • Jami vazifalar: <b>{total} ta</b>\n"
        "  • Bajarilgan: <b>{completed} ta</b>\n"
        "  • O'z vaqtida bajarish: <b>{on_time_rate}%</b>\n"
        "  • O'rtacha kechikish: <b>{avg_delay} soat</b>\n\n"
    ),
    "stats_top_performer": "🏆 <b>ENG FAOL XODIM:</b> {name} (Bajarildi: {count} ta, {pct}%)\n\n",

    # Eksport (/eksport)
    "export_caption": "📊 <b>Barcha vazifalar bo'yicha to'liq Excel hisoboti</b>\nSana: {date}",
    "export_btn_excel": "📥 Excel faylni yuklab olish",

    # Hisobotlar
    "morning_report_title": "📊 <b>KUNLIK ERTALABKI HISOBOT ({date})</b>\n",
    "report_section_completed": "✅ <b>Oxirgi 24 soatda bajarildi:</b>\n{items}\n",
    "report_section_review": "👀 <b>Tekshiruvda turganlar:</b>\n{items}\n",
    "report_section_in_progress": "⚡ <b>Jarayonda:</b>\n{items}\n",
    "report_section_new": "🆕 <b>Boshlanmagan (Yangi):</b>\n{items}\n",
    "report_section_due_today": "⏰ <b>Bugun muddati tugaydiganlar:</b>\n{items}\n",
    "report_section_overdue": "🚨 <b>Muddati o'tganlar:</b>\n{items}\n",
    "report_no_tasks": "Hozircha vazifalar mavjud emas.",
    "report_none": "— Yo'q",

    # Kechki hisobot
    "evening_report_title": "🌙 <b>KUN YAKUNI HISOBOTI ({date})</b>\n\n",
    "evening_section_completed": "✅ <b>Bugun muvaffaqiyatli bajarilganlar:</b>\n{items}\n\n",
    "evening_section_overdue": "🚨 <b>Kechikkan / Muddati o'tgan vazifalar:</b>\n{items}\n\n",
    "evening_section_active": "⚡ <b>Ertangi kunga qolgan faol vazifalar:</b>\n{items}",

    # Shaxsiy kunlik ro'yxat
    "daily_personal_title": "☀️ <b>Xayrli tong, {name}!</b>\n📅 Bugungi vazifalaringiz ro'yxati ({date}):\n\n",
    "daily_personal_due_today": "⏰ <b>Bugun topshirilishi kerak:</b>\n{items}\n\n",
    "daily_personal_overdue": "🚨 <b>Kechikkan vazifalar:</b>\n{items}\n\n",
    "daily_personal_other": "📌 <b>Boshqa faol vazifalar:</b>\n{items}",
    "daily_personal_empty": "Bugun sizda hech qanday kechiktirilgan yoki shoshilinch vazifa yo'q. Kuningiz unumli o'tsin! 🚀",

    # Mening vazifalarim
    "my_tasks_title": "📋 <b>Sizning ochiq vazifalaringiz ({count} ta):</b>\n\n",
    "my_tasks_empty": "Sizda hozircha ochiq vazifalar yo'q. Yashang! 👍",
    "group_tasks_title": "📋 <b>Guruhdagi ochiq vazifalar ({count} ta):</b>\n\n",
    "group_tasks_empty": "Guruhda hozircha ochiq vazifalar yo'q.",
}

