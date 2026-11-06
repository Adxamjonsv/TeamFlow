import io
from datetime import datetime
import pytz
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from config import settings
from database.models import Task, TaskStatus, TaskPriority
from database.base import AsyncSessionLocal
from database.crud import get_all_tasks_for_export, get_user_by_id

async def generate_tasks_excel(session) -> io.BytesIO:
    tasks = await get_all_tasks_for_export(session)
    tz = pytz.timezone(settings.TIMEZONE)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Vazifalar"

    # Sarlavhalar
    headers = [
        "ID", "Loyiha", "Vazifa nomi", "Ijrochi", "Biriktiruvchi",
        "Muhimlik", "Holat", "Muddat", "Yaratildi", "Boshlandi", "Bajarildi", "Kechikish (soat)"
    ]
    ws.append(headers)

    # Dizayn: Sarlavha
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    # Ma'lumotlarni to'ldirish
    status_map = {
        TaskStatus.NEW: "Yangi",
        TaskStatus.IN_PROGRESS: "Jarayonda",
        TaskStatus.REVIEW: "Tekshiruvda",
        TaskStatus.COMPLETED: "Bajarildi",
        TaskStatus.CANCELLED: "Bekor qilingan"
    }
    priority_map = {
        TaskPriority.URGENT: "Shoshilinch 🔴",
        TaskPriority.NORMAL: "Oddiy 🟡",
        TaskPriority.LOW: "Past 🟢"
    }

    def fmt_dt(dt: datetime) -> str:
        if not dt:
            return ""
        local_dt = pytz.utc.localize(dt).astimezone(tz)
        return local_dt.strftime("%d.%m.%Y %H:%M")

    for t in tasks:
        assignee_user = await get_user_by_id(session, t.assignee_id) if t.assignee_id else None
        creator_user = await get_user_by_id(session, t.creator_id) if t.creator_id else None

        assignee_str = assignee_user.full_name if assignee_user else (f"@{t.assignee_username}" if t.assignee_username else "—")
        creator_str = creator_user.full_name if creator_user else "Admin"

        # Kechikish hisoblash
        delay_hours = 0.0
        if t.due_date:
            end_t = t.completed_at if t.status == TaskStatus.COMPLETED and t.completed_at else datetime.utcnow()
            if end_t > t.due_date:
                delay_hours = round((end_t - t.due_date).total_seconds() / 3600.0, 1)

        row = [
            t.id,
            t.project or "Umumiy",
            t.title,
            assignee_str,
            creator_str,
            priority_map.get(t.priority, "Oddiy"),
            status_map.get(t.status, "Yangi"),
            fmt_dt(t.due_date),
            fmt_dt(t.created_at),
            fmt_dt(t.started_at),
            fmt_dt(t.completed_at),
            delay_hours if delay_hours > 0 else ""
        ]
        ws.append(row)

    # Ustun kengliklarini avtomatik to'g'rilash
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
            if cell.row > 1:
                cell.border = thin_border
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output

