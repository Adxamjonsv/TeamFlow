from datetime import datetime
import pytz
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from config import settings
from database.base import AsyncSessionLocal
from database.crud import (
    get_user_by_id,
    get_team_statistics,
    get_all_recurring_tasks,
    toggle_recurring_task,
    delete_recurring_task
)
from database.models import UserRole, RecurringFrequency
from utils.permissions import can_create_task, is_admin
from locales import t
from services.exporter import generate_tasks_excel
from keyboards.inline import (
    get_stats_period_keyboard,
    get_recurring_list_keyboard,
    get_recurring_item_keyboard
)

router = Router()

# --- 1. STATISTIKA VA REYTING (/statistika) ---

@router.message(Command("statistika"))
async def handle_statistics_command(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        if not can_create_task(user, message.from_user.id):
            await message.reply(t("unauthorized", lang))
            return

        text = await build_statistics_text(session, days=30, lang=lang)
        keyboard = get_stats_period_keyboard(lang)
        await message.reply(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("stats_days:"))
async def handle_change_stats_period(callback: CallbackQuery):
    days = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

        if not can_create_task(user, callback.from_user.id):
            await callback.answer(t("unauthorized", lang), show_alert=True)
            return

        text = await build_statistics_text(session, days=days, lang=lang)
        keyboard = get_stats_period_keyboard(lang)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

async def build_statistics_text(session, days: int, lang: str) -> str:
    data = await get_team_statistics(session, days=days)
    users_stats = data["users"]
    top = data["top_performer"]

    if not users_stats:
        return t("stats_title", lang, days=days) + t("stats_empty", lang)

    lines = [t("stats_title", lang, days=days)]

    if top and top["completed"] > 0:
        top_name = top["user"].full_name
        lines.append(t("stats_top_performer", lang, name=top_name, count=top["completed"], pct=top["on_time_rate"]))

    for s in users_stats:
        u_name = s["user"].full_name
        lines.append(t(
            "stats_user_line",
            lang,
            name=u_name,
            total=s["total"],
            completed=s["completed"],
            on_time_rate=s["on_time_rate"],
            avg_delay=s["avg_delay_hours"]
        ))

    return "".join(lines)

# --- 2. EXCEL EKSPORT (/eksport) ---

@router.message(Command("eksport"))
async def handle_export_excel(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        if not can_create_task(user, message.from_user.id):
            await message.reply(t("unauthorized", lang))
            return

        wait_msg = await message.reply("⏳ Excel fayl tayyorlanmoqda...")

        excel_io = await generate_tasks_excel(session)
        tz = pytz.timezone(settings.TIMEZONE)
        now_str = datetime.now(tz).strftime("%d.%m.%Y_%H%M")
        filename = f"vazifalar_hisoboti_{now_str}.xlsx"

        input_file = BufferedInputFile(excel_io.getvalue(), filename=filename)

        caption = t("export_caption", lang, date=datetime.now(tz).strftime("%d.%m.%Y %H:%M"))
        await message.answer_document(document=input_file, caption=caption, parse_mode="HTML")
        await wait_msg.delete()

# --- 3. TAKRORLANUVCHI VAZIFALAR (/takroriy) ---

@router.message(Command("takroriy"))
async def handle_recurring_tasks_list(message: Message):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, message.from_user.id)
        lang = user.language if user else "uz"

        if not can_create_task(user, message.from_user.id):
            await message.reply(t("unauthorized", lang))
            return

        recs = await get_all_recurring_tasks(session)
        if not recs:
            await message.reply(t("recurring_list_title", lang) + t("recurring_empty", lang), parse_mode="HTML")
            return

        keyboard = get_recurring_list_keyboard(recs, lang)
        await message.reply(t("recurring_list_title", lang) + "Quyidagi takroriy vazifalardan birini tanlang:", reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("rec_info:"))
async def handle_rec_item_info(callback: CallbackQuery):
    rec_id = int(callback.data.split(":")[1])

    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"

        recs = await get_all_recurring_tasks(session)
        rec = next((r for r in recs if r.id == rec_id), None)
        if not rec:
            await callback.answer("Takroriy vazifa topilmadi!", show_alert=True)
            return

        status_str = "Faol 🟢" if rec.is_active else "To'xtatilgan 🔴"
        freq_map = {
            RecurringFrequency.DAILY: "Har kuni",
            RecurringFrequency.WEEKLY: "Har hafta",
            RecurringFrequency.MONTHLY: "Har oy"
        }
        text = (
            f"🔄 <b>Takroriy vazifa #{rec.id}</b>\n\n"
            f"📌 Nomi: <b>{rec.title}</b>\n"
            f"📁 Loyiha: {rec.project or '—'}\n"
            f"⏰ Takrorlanish: {freq_map.get(rec.frequency, '')} (Soat {rec.time_str})\n"
            f"📊 Holati: <b>{status_str}</b>\n"
        )
        keyboard = get_recurring_item_keyboard(rec, lang)
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("rec_toggle:"))
async def handle_rec_toggle(callback: CallbackQuery):
    rec_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        await toggle_recurring_task(session, rec_id)
        await callback.answer("Holati o'zgartirildi!")
        # Ro'yxatga qaytish
        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"
        recs = await get_all_recurring_tasks(session)
        keyboard = get_recurring_list_keyboard(recs, lang)
        await callback.message.edit_text(t("recurring_list_title", lang), reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data.startswith("rec_delete:"))
async def handle_rec_delete(callback: CallbackQuery):
    rec_id = int(callback.data.split(":")[1])
    async with AsyncSessionLocal() as session:
        await delete_recurring_task(session, rec_id)
        await callback.answer("O'chirildi!")
        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"
        recs = await get_all_recurring_tasks(session)
        if not recs:
            await callback.message.edit_text(t("recurring_list_title", lang) + t("recurring_empty", lang), parse_mode="HTML")
            return
        keyboard = get_recurring_list_keyboard(recs, lang)
        await callback.message.edit_text(t("recurring_list_title", lang), reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "rec_back")
async def handle_rec_back(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await get_user_by_id(session, callback.from_user.id)
        lang = user.language if user else "uz"
        recs = await get_all_recurring_tasks(session)
        keyboard = get_recurring_list_keyboard(recs, lang)
        await callback.message.edit_text(t("recurring_list_title", lang), reply_markup=keyboard, parse_mode="HTML")

