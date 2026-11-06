// TELEGRAM WEB APP INIT
const tg = window.Telegram?.WebApp;
if (tg) {
    tg.ready();
    tg.expand();
}

// I18N DICTIONARY
const I18N = {
    uz: {
        new_task: "Yangi vazifa",
        tab_board: "Doska",
        tab_stats: "Statistika",
        tab_team: "Jamoa",
        tab_recurring: "Takroriy",
        tab_export: "Eksport",
        all_projects: "Barcha loyihalar",
        all_assignees: "Barcha xodimlar",
        all_priorities: "Barcha muhimlik",
        add_project: "Loyiha qo'shish",
        status_new: "Yangi",
        status_in_progress: "Jarayonda",
        status_review: "Tekshiruvda",
        status_completed: "Bajarildi",
        stats_title: "Jamoa statistikasi va KPI",
        top_performer: "Eng faol xodim",
        col_employee: "Xodim",
        col_total: "Jami",
        col_completed: "Bajarildi",
        col_on_time: "O'z vaqtida",
        col_delay: "O'rtacha kechikish",
        team_roles_title: "Jamoa a'zolari va rollar",
        export_desc: "Barcha vazifalar, ijrochilar, loyihalar va hisobotlarni Excel formatida yuklab oling.",
        btn_download_excel: "Excel faylni yuklab olish (.xlsx)",
        modal_create_title: "Yangi vazifa yaratish",
        field_title: "Vazifa nomi *",
        field_desc: "Tavsif (ixtiyoriy)",
        field_assignee: "Ijrochi",
        field_priority: "Muhimlik",
        field_project: "Loyiha",
        field_due: "Muddat",
        cancel: "Bekor qilish",
        btn_save: "Yaratish",
        comments: "Izohlar",
        btn_send: "Yuborish"
    },
    ru: {
        new_task: "Новая задача",
        tab_board: "Доска",
        tab_stats: "Статистика",
        tab_team: "Команда",
        tab_recurring: "Регулярные",
        tab_export: "Экспорт",
        all_projects: "Все проекты",
        all_assignees: "Все сотрудники",
        all_priorities: "Все приоритеты",
        add_project: "Добавить проект",
        status_new: "Новые",
        status_in_progress: "В процессе",
        status_review: "На проверке",
        status_completed: "Завершено",
        stats_title: "Статистика и KPI команды",
        top_performer: "Лучший сотрудник",
        col_employee: "Сотрудник",
        col_total: "Всего",
        col_completed: "Выполнено",
        col_on_time: "В срок",
        col_delay: "Средняя задержка",
        team_roles_title: "Члены команды и роли",
        export_desc: "Скачайте полный отчет по задачам и сотрудникам в формате Excel.",
        btn_download_excel: "Скачать Excel (.xlsx)",
        modal_create_title: "Создать новую задачу",
        field_title: "Название задачи *",
        field_desc: "Описание (необязательно)",
        field_assignee: "Исполнитель",
        field_priority: "Приоритет",
        field_project: "Проект",
        field_due: "Срок",
        cancel: "Отмена",
        btn_save: "Создать",
        comments: "Комментарии",
        btn_send: "Отправить"
    }
};

let currentLang = "uz";
let currentUser = null;
let currentTasks = [];
let usersCache = [];
let projectsCache = [];
let draggedTaskId = null;
let activeDetailTaskId = null;

// API HELPER
async function apiCall(endpoint, method = "GET", body = null) {
    const headers = {
        "Content-Type": "application/json"
    };
    if (tg?.initData) {
        headers["X-Telegram-Init-Data"] = tg.initData;
    }

    const config = { method, headers };
    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(endpoint, config);
        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: "Xatolik" }));
            throw new Error(err.detail || "Server xatosi");
        }
        return await response.json();
    } catch (e) {
        console.error("API Error:", e);
        throw e;
    }
}

// APP INITIALIZATION
document.addEventListener("DOMContentLoaded", async () => {
    setupEventListeners();
    await loadCurrentUser();
    await Promise.all([
        loadProjects(),
        loadUsers(),
        loadTasks()
    ]);
});

// LOAD CURRENT USER
async function loadCurrentUser() {
    try {
        currentUser = await apiCall("/api/auth/me");
        document.getElementById("user-name").textContent = currentUser.full_name;
        document.getElementById("user-role").textContent = currentUser.role;
        currentLang = currentUser.language || "uz";
        updateLanguage(currentLang);

        // Agar oddiy xodim bo'lsa, ba'zi admin tablarini yashiramiz
        if (!currentUser.is_manager) {
            document.getElementById("nav-users-tab").style.display = "none";
            document.getElementById("nav-rec-tab").style.display = "none";
            document.getElementById("btn-new-task").style.display = "none";
            document.getElementById("btn-add-project").style.display = "none";
        }
    } catch (e) {
        console.error("User load error:", e);
    }
}

// LOAD TASKS & RENDER KANBAN
async function loadTasks() {
    const project = document.getElementById("filter-project").value;
    const assignee = document.getElementById("filter-assignee").value;
    const priority = document.getElementById("filter-priority").value;

    let url = "/api/tasks?";
    if (project) url += `project=${encodeURIComponent(project)}&`;
    if (assignee) url += `assignee_id=${assignee}&`;
    if (priority) url += `priority=${priority}&`;

    try {
        currentTasks = await apiCall(url);
        renderKanban(currentTasks);
    } catch (e) {
        console.error("Tasks load error:", e);
    }
}

function renderKanban(tasks) {
    const cols = {
        new: document.getElementById("tasks-new"),
        in_progress: document.getElementById("tasks-in_progress"),
        review: document.getElementById("tasks-review"),
        completed: document.getElementById("tasks-completed")
    };

    const counts = { new: 0, in_progress: 0, review: 0, completed: 0 };
    Object.values(cols).forEach(col => col.innerHTML = "");

    tasks.forEach(t => {
        const col = cols[t.status];
        if (col) {
            counts[t.status]++;
            const card = createKanbanCard(t);
            col.appendChild(card);
        }
    });

    document.getElementById("count-new").textContent = counts.new;
    document.getElementById("count-in_progress").textContent = counts.in_progress;
    document.getElementById("count-review").textContent = counts.review;
    document.getElementById("count-completed").textContent = counts.completed;
}

function createKanbanCard(t) {
    const card = document.createElement("div");
    card.className = "task-card";
    card.draggable = true;
    card.dataset.id = t.id;

    const priorityColors = {
        urgent: "🔴",
        normal: "🟡",
        low: "🟢"
    };

    card.innerHTML = `
        <div class="card-tags">
            <span class="tag-project">${t.project || 'Umumiy'}</span>
            <span class="tag-priority">${priorityColors[t.priority] || '🟡'}</span>
        </div>
        <div class="card-title">#${t.id} ${t.title}</div>
        <div class="card-meta">
            <span class="card-assignee">👤 ${t.assignee_name || '—'}</span>
            <span>${t.due_date ? '⏰ ' + t.due_date.split(' ')[0] : ''}</span>
        </div>
    `;

    // Drag and drop events
    card.addEventListener("dragstart", (e) => {
        draggedTaskId = t.id;
        card.classList.add("dragging");
    });

    card.addEventListener("dragend", () => {
        card.classList.remove("dragging");
    });

    // Modalni ochish
    card.addEventListener("click", () => {
        openTaskDetails(t.id);
    });

    return card;
}

// TASK DETAILS MODAL
async function openTaskDetails(taskId) {
    activeDetailTaskId = taskId;
    try {
        const t = await apiCall(`/api/tasks/${taskId}`);
        document.getElementById("detail-task-title").textContent = `#${t.id} - ${t.title}`;
        document.getElementById("detail-task-desc").textContent = t.description || "Tavsif ko'rsatilmagan.";
        document.getElementById("detail-task-priority").textContent = t.priority === "urgent" ? "🔴 Shoshilinch" : (t.priority === "low" ? "🟢 Past" : "🟡 Oddiy");
        document.getElementById("detail-task-status").textContent = t.status;
        document.getElementById("detail-task-project").textContent = t.project || "Umumiy";
        document.getElementById("detail-task-assignee").textContent = t.assignee || "—";
        document.getElementById("detail-task-due").textContent = t.due_date || "—";

        // Izohlarni chiqarish
        const commentsList = document.getElementById("detail-comments-list");
        commentsList.innerHTML = "";
        if (t.comments && t.comments.length > 0) {
            t.comments.forEach(c => {
                const item = document.createElement("div");
                item.className = "comment-item";
                item.innerHTML = `
                    <div class="comment-header">
                        <span>${c.author}</span>
                        <span class="comment-time">${c.time}</span>
                    </div>
                    <div>${c.text}</div>
                `;
                commentsList.appendChild(item);
            });
        } else {
            commentsList.innerHTML = "<p style='color:var(--text-muted); font-size:12px;'>Hozircha izohlar yo'q.</p>";
        }

        document.getElementById("modal-task-details").classList.add("active");
    } catch (e) {
        alert("Vazifa tafsilotlarini yuklashda xatolik yuz berdi.");
    }
}

// LOAD PROJECTS & USERS FOR FILTERS & FORMS
async function loadProjects() {
    try {
        projectsCache = await apiCall("/api/projects");
        const filterSelect = document.getElementById("filter-project");
        const formSelect = document.getElementById("task-project-select");

        projectsCache.forEach(p => {
            const opt1 = new Option(p.name, p.name);
            const opt2 = new Option(p.name, p.name);
            filterSelect.appendChild(opt1);
            formSelect.appendChild(opt2);
        });
    } catch (e) {}
}

async function loadUsers() {
    try {
        usersCache = await apiCall("/api/users");
        const filterSelect = document.getElementById("filter-assignee");
        const formSelect = document.getElementById("task-assignee-select");

        usersCache.forEach(u => {
            const label = u.full_name + (u.username ? ` (@${u.username})` : '');
            const opt1 = new Option(label, u.telegram_id);
            const opt2 = new Option(label, u.telegram_id);
            filterSelect.appendChild(opt1);
            formSelect.appendChild(opt2);
        });
    } catch (e) {}
}

// STATS
async function loadStats(days = 30) {
    try {
        const data = await apiCall(`/api/stats?days=${days}`);
        const tbody = document.getElementById("stats-tbody");
        tbody.innerHTML = "";

        if (data.top_performer) {
            document.getElementById("top-performer-card").style.display = "block";
            document.getElementById("top-name").textContent = data.top_performer.name;
            document.getElementById("top-details").textContent = `Bajarilgan: ${data.top_performer.completed} ta (${data.top_performer.on_time_rate}% o'z vaqtida)`;
        } else {
            document.getElementById("top-performer-card").style.display = "none";
        }

        if (data.users && data.users.length > 0) {
            data.users.forEach(u => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td><b>${u.name}</b></td>
                    <td>${u.total}</td>
                    <td><span style="color:var(--success); font-weight:600;">${u.completed}</span></td>
                    <td>${u.on_time_rate}%</td>
                    <td>${u.avg_delay_hours} soat</td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = "<tr><td colspan='5' class='text-center'>Statistika ma'lumotlari mavjud emas.</td></tr>";
        }
    } catch (e) {
        console.error("Stats load error:", e);
    }
}

// USERS & ROLES TAB
async function loadUsersRoles() {
    try {
        const users = await apiCall("/api/users");
        const list = document.getElementById("users-list");
        list.innerHTML = "";

        users.forEach(u => {
            const item = document.createElement("div");
            item.className = "user-item";
            item.innerHTML = `
                <div>
                    <div style="font-weight:600;">${u.full_name}</div>
                    <div style="font-size:12px; color:var(--text-muted);">${u.username ? '@' + u.username : 'ID: ' + u.telegram_id}</div>
                </div>
                <select class="form-control" style="width:130px;" onchange="changeUserRole(${u.telegram_id}, this.value)" ${!currentUser.is_admin ? 'disabled' : ''}>
                    <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>👑 Admin</option>
                    <option value="manager" ${u.role === 'manager' ? 'selected' : ''}>👔 Menejer</option>
                    <option value="employee" ${u.role === 'employee' ? 'selected' : ''}>👤 Xodim</option>
                </select>
            `;
            list.appendChild(item);
        });
    } catch (e) {}
}

window.changeUserRole = async function(telegramId, newRole) {
    try {
        await apiCall(`/api/users/${telegramId}/role`, "PUT", { role: newRole });
        alert("Rol muvaffaqiyatli o'zgartirildi!");
    } catch (e) {
        alert("Rolni o'zgartirishda xatolik yuz berdi.");
    }
};

// RECURRING TASKS TAB
async function loadRecurring() {
    try {
        const recs = await apiCall("/api/recurring");
        const list = document.getElementById("recurring-list");
        list.innerHTML = "";

        if (recs.length === 0) {
            list.innerHTML = "<p style='color:var(--text-muted);'>Hozircha takroriy vazifalar mavjud emas.</p>";
            return;
        }

        recs.forEach(r => {
            const item = document.createElement("div");
            item.className = "rec-item";
            const statusBadge = r.is_active ? "<span style='color:var(--success);'>🟢 Faol</span>" : "<span style='color:var(--danger);'>🔴 To'xtatilgan</span>";
            item.innerHTML = `
                <div>
                    <div style="font-weight:600;">${r.title}</div>
                    <div style="font-size:12px; color:var(--text-muted);">${r.frequency} | Soat ${r.time_str} | ${statusBadge}</div>
                </div>
                <div style="display:flex; gap:6px;">
                    <button class="btn btn-sm btn-secondary" onclick="toggleRec(${r.id})">${r.is_active ? '⏸' : '▶️'}</button>
                    <button class="btn btn-sm btn-secondary" onclick="deleteRec(${r.id})">🗑</button>
                </div>
            `;
            list.appendChild(item);
        });
    } catch (e) {}
}

window.toggleRec = async function(id) {
    await apiCall(`/api/recurring/${id}/toggle`, "POST");
    loadRecurring();
};

window.deleteRec = async function(id) {
    if (confirm("Ushbu takroriy vazifani o'chirmoqchimisiz?")) {
        await apiCall(`/api/recurring/${id}`, "DELETE");
        loadRecurring();
    }
};

// EVENT LISTENERS SETUP
function setupEventListeners() {
    // Navigation Tabs
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const target = btn.dataset.tab;
            document.getElementById(target).classList.add("active");

            // Filtr bar faqat doska tabida ko'rinadi
            document.getElementById("filters-bar").style.display = target === "tab-kanban" ? "flex" : "none";

            if (target === "tab-stats") loadStats(30);
            if (target === "tab-users") loadUsersRoles();
            if (target === "tab-recurring") loadRecurring();
        });
    });

    // Filters change
    ["filter-project", "filter-assignee", "filter-priority"].forEach(id => {
        document.getElementById(id).addEventListener("change", loadTasks);
    });

    // Stats period buttons
    document.querySelectorAll(".period-selector .btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".period-selector .btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            loadStats(btn.dataset.days);
        });
    });

    // Drag and Drop for Kanban Columns
    document.querySelectorAll(".kanban-col").forEach(col => {
        const tasksContainer = col.querySelector(".col-tasks");

        col.addEventListener("dragover", (e) => {
            e.preventDefault();
            tasksContainer.classList.add("drag-over");
        });

        col.addEventListener("dragleave", () => {
            tasksContainer.classList.remove("drag-over");
        });

        col.addEventListener("drop", async (e) => {
            e.preventDefault();
            tasksContainer.classList.remove("drag-over");
            const newStatus = col.dataset.status;

            if (draggedTaskId && newStatus) {
                try {
                    await apiCall(`/api/tasks/${draggedTaskId}/status`, "PUT", { status: newStatus });
                    await loadTasks();
                } catch (err) {
                    alert("Holatni o'zgartirishga ruxsat yo'q yoki xatolik yuz berdi.");
                }
            }
        });
    });

    // Modals open/close
    document.getElementById("btn-new-task").addEventListener("click", () => {
        document.getElementById("modal-task-create").classList.add("active");
    });
    document.getElementById("close-modal-task").addEventListener("click", () => {
        document.getElementById("modal-task-create").classList.remove("active");
    });
    document.getElementById("btn-cancel-create").addEventListener("click", () => {
        document.getElementById("modal-task-create").classList.remove("active");
    });

    document.getElementById("close-modal-detail").addEventListener("click", () => {
        document.getElementById("modal-task-details").classList.remove("active");
    });

    document.getElementById("btn-add-project").addEventListener("click", () => {
        document.getElementById("modal-project-create").classList.add("active");
    });
    document.getElementById("close-modal-project").addEventListener("click", () => {
        document.getElementById("modal-project-create").classList.remove("active");
    });
    document.getElementById("btn-cancel-project").addEventListener("click", () => {
        document.getElementById("modal-project-create").classList.remove("active");
    });

    // Form Task Create Submit
    document.getElementById("form-task-create").addEventListener("submit", async (e) => {
        e.preventDefault();
        const title = document.getElementById("task-title-input").value;
        const description = document.getElementById("task-desc-input").value;
        const assignee_id = document.getElementById("task-assignee-select").value || null;
        const priority = document.getElementById("task-priority-select").value;
        const project = document.getElementById("task-project-select").value || null;
        const due_date = document.getElementById("task-due-input").value || null;

        try {
            await apiCall("/api/tasks", "POST", {
                title,
                description,
                assignee_id: assignee_id ? parseInt(assignee_id) : null,
                priority,
                project,
                due_date
            });
            document.getElementById("modal-task-create").classList.remove("active");
            document.getElementById("form-task-create").reset();
            await loadTasks();
        } catch (err) {
            alert("Vazifa yaratishda xatolik: " + err.message);
        }
    });

    // Form Comment Submit
    document.getElementById("form-add-comment").addEventListener("submit", async (e) => {
        e.preventDefault();
        const input = document.getElementById("comment-input");
        const comment = input.value.trim();
        if (!comment || !activeDetailTaskId) return;

        try {
            await apiCall(`/api/tasks/${activeDetailTaskId}/comments`, "POST", { comment });
            input.value = "";
            openTaskDetails(activeDetailTaskId); // Izohlarni qayta yangilash
        } catch (err) {
            alert("Izoh qo'shishda xatolik yuz berdi.");
        }
    });

    // Form Project Create Submit
    document.getElementById("form-project-create").addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("project-name-input").value.trim();
        if (!name) return;

        try {
            await apiCall("/api/projects", "POST", { name });
            document.getElementById("modal-project-create").classList.remove("active");
            document.getElementById("form-project-create").reset();
            await loadProjects();
        } catch (err) {
            alert("Loyiha qo'shishda xatolik yuz berdi.");
        }
    });

    // Language Toggle
    document.getElementById("btn-lang-toggle").addEventListener("click", () => {
        currentLang = currentLang === "uz" ? "ru" : "uz";
        updateLanguage(currentLang);
    });
}

// UPDATE LANGUAGE STRINGS
function updateLanguage(lang) {
    const dict = I18N[lang] || I18N.uz;
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.dataset.i18n;
        if (dict[key]) {
            el.textContent = dict[key];
        }
    });
    document.getElementById("btn-lang-toggle").textContent = lang === "uz" ? "🇺🇿" : "🇷🇺";
}

