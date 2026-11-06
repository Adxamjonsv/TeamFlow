import asyncio
import logging
import sys
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import settings
from database.base import init_db
from handlers import main_router
from services.scheduler import setup_scheduler
from api.app import app as fastapi_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish / Запустить"),
        BotCommand(command="panel", description="Mini App Panel / Панель"),
        BotCommand(command="mening", description="Mening vazifalarim / Мои задачи"),
        BotCommand(command="vazifalar", description="Guruh vazifalari / Задачи группы"),
        BotCommand(command="yangi", description="Yangi vazifa berish / Создать задачу"),
        BotCommand(command="takroriy", description="Takroriy vazifalar / Регулярные"),
        BotCommand(command="statistika", description="KPI va Statistika / Статистика"),
        BotCommand(command="eksport", description="Excel yuklab olish / Экспорт"),
        BotCommand(command="loyihalar", description="Loyihalar / Проекты"),
        BotCommand(command="xodimlar", description="Jamoa va rollar / Команда и роли"),
        BotCommand(command="til", description="Tilni o'zgartirish / Сменить язык"),
        BotCommand(command="hisobot", description="Hisobot olish / Получить отчет"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

async def run_fastapi_server():
    port = settings.server_port
    config = uvicorn.Config(
        app=fastapi_app,
        host=settings.WEBAPP_HOST,
        port=port,
        log_level="warning"
    )
    server = uvicorn.Server(config)
    logger.info(f"FastAPI Mini App serveri http://{settings.WEBAPP_HOST}:{port} da ishga tushdi.")
    await server.serve()

async def main():
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN ko'rsatilmagan! Iltimos, .env fayliga haqiqiy bot tokenini kiriting.")
        raise RuntimeError("BOT_TOKEN environment variable is required")

    logger.info("Ma'lumotlar bazasini initsializatsiya qilish...")
    await init_db()

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ulash
    dp.include_router(main_router)

    # Rejalashtiruvchi (Scheduler) ni ishga tushirish
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("APScheduler eslatmalar, hisobotlar va takroriy vazifalar xizmati ishga tushdi.")

    # Buyruqlar menyusini o'rnatish
    try:
        await set_bot_commands(bot)
    except Exception as e:
        logger.warning(f"Bot buyruqlarini o'rnatishda xatolik: {e}")

    logger.info("Bot va Mini App muvaffaqiyatli ishga tushdi...")
    try:
        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            run_fastapi_server()
        )
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot va server to'xtatildi.")

