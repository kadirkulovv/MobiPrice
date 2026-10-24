import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

# Bootstrap Django ORM before importing any handlers
import bot.database  # noqa: F401

from bot.config import BOT_TOKEN, ADMIN_IDS
from bot.handlers import start, brands, series, phones, issues, comparisons, masters, admins, crm



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("mobiprice_bot")


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Botni ishga tushirish / Bosh menyu"),
        BotCommand(command="menu", description="📱 Asosiy Admin menyusi"),
        BotCommand(command="cancel", description="❌ Jarayonni bekor qilish"),
    ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot):
    logger.info("MobiPrice Admin Bot ishga tushdi!")
    logger.info(f"Ruxsat berilgan Admin IDlar: {ADMIN_IDS}")
    await set_bot_commands(bot)
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text="🤖 <b>MobiPrice Admin Bot ishga tushdi!</b>\n\nBoshqaruv uchun /start yoki /menu buyrug'ini yuboring.",
            )
        except Exception as e:
            logger.warning(f"Admin {admin_id} ga xabar yuborilmadi: {e}")


async def on_shutdown(bot: Bot):
    logger.info("MobiPrice Admin Bot to'xtatilmoqda...")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text="⚠️ <b>MobiPrice Admin Bot to'xtatildi.</b>",
            )
        except Exception:
            pass


async def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN topilmadi! .env faylni tekshiring.")
        sys.exit(1)

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers in logical sequence
    dp.include_router(start.router)
    dp.include_router(brands.router)
    dp.include_router(series.router)
    dp.include_router(phones.router)
    dp.include_router(issues.router)
    dp.include_router(comparisons.router)
    dp.include_router(masters.router)
    dp.include_router(admins.router)
    dp.include_router(crm.router)



    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Delete webhook if previously set to ensure polling works
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
