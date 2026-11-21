import asyncio
import html
import logging
import sys

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, ReplyKeyboardRemove, TelegramObject

# Bootstrap Django ORM before importing any handlers
import bot.database
from bot.database import close_old_connections, sync_to_async

from bot.config import ADMIN_IDS, BOT_TOKEN
from bot.handlers import admins, brands, client, comparisons, crm, excel, issues, masters, phones, series, start
from bot.keyboards.main_menu import get_main_menu
from bot.permissions import get_user_permissions
from bot.states.client_states import CourierLocationStates
from core.maintenance import expire_stale_pending_courier_orders, run_server_maintenance
from core.telegram_auth import cache_bot_username


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("mobiprice_bot")
_background_tasks: list[asyncio.Task] = []


class DjangoDBCleanupMiddleware(BaseMiddleware):
    """Uzoq ishlovchi bot protsessida SQLite WAL ulanishlarini yangilab turish"""
    async def __call__(self, handler, event: TelegramObject, data: dict):
        await sync_to_async(close_old_connections)()
        try:
            return await handler(event, data)
        finally:
            await sync_to_async(close_old_connections)()


def prune_empty_fsm_memory(storage) -> int:
    """MemoryStorage ichida bo'sh qolib ketgan FSM yozuvlarini RAM dan tozalash."""
    store = getattr(storage, "storage", None)
    if not isinstance(store, dict):
        return 0
    empty_keys = [
        k for k, rec in list(store.items())
        if getattr(rec, "state", None) is None and not getattr(rec, "data", None)
    ]
    for k in empty_keys:
        store.pop(k, None)
    return len(empty_keys)


async def courier_expiry_watcher_task(bot: Bot, dp: Dispatcher):
    """
    Har 60 soniyada 1 soat ichida lokatsiya yuborilmagan 'pending_location' buyurtmalarni
    avtomatik bekor qilish, mos FSM holatini tozalash va mijozni xabardor qilish.
    """
    logger.info("Kuryer lokatsiya 1-soatlik auto-cancel kuzatuvchisi ishga tushdi.")
    while True:
        try:
            await sync_to_async(close_old_connections)()
            expired_orders = await sync_to_async(expire_stale_pending_courier_orders)()

            for item in expired_orders:
                tg_id = item.get("telegram_id")
                order_code = item.get("order_id") or ""
                order_pk = item.get("order_pk")
                if not tg_id:
                    continue

                # Agar mijoz aynan shu muddati o'tgan buyurtmaning lokatsiya holatida turgan bo'lsa, state ni tozalaymiz
                try:
                    storage_key = StorageKey(bot_id=bot.id, chat_id=int(tg_id), user_id=int(tg_id))
                    cur_state = await dp.storage.get_state(storage_key)
                    if cur_state == CourierLocationStates.waiting_for_location.state:
                        cur_data = await dp.storage.get_data(storage_key)
                        if not cur_data.get("courier_order_pk") or int(cur_data.get("courier_order_pk")) == int(order_pk):
                            await dp.storage.set_state(storage_key, None)
                            await dp.storage.set_data(storage_key, {})
                except Exception as exc:
                    logger.warning("FSM state tozalashda xatolik (user %s): %s", tg_id, exc)

                try:
                    perms = await get_user_permissions(int(tg_id), None)
                    markup = get_main_menu(perms) if perms.has_any_access else ReplyKeyboardRemove()
                except Exception:
                    markup = ReplyKeyboardRemove()

                try:
                    await bot.send_message(
                        chat_id=int(tg_id),
                        text=(
                            f"⏰ <b>Buyurtma #{html.escape(order_code)} avtomatik bekor qilindi.</b>\n\n"
                            f"1 soat ichida lokatsiya yuborilmagani sababli kuryer buyurtmangiz bekor qilindi. "
                            f"Agar kerak bo'lsa, saytdan yangi buyurtma rasmiylashtirishingiz mumkin."
                        ),
                        parse_mode="HTML",
                        reply_markup=markup,
                    )
                except Exception as exc:
                    logger.warning("Auto-cancel xabari yuborilmadi (user %s, order #%s): %s", tg_id, order_code, exc)

            await sync_to_async(close_old_connections)()
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            logger.info("Kuryer auto-cancel kuzatuvchisi to'xtatildi.")
            break
        except Exception as exc:
            logger.error("Kuryer auto-cancel siklida xatolik: %s", exc)
            await asyncio.sleep(60)


async def server_maintenance_scheduler_task(dp: Dispatcher):
    """
    Har 6 soatda server diski va bazasini avtomatik tozalash:
    - Faqat oxirgi 2 ta backup qoldirish
    - Eski AuthToken va Django sessiyalarni o'chirish
    - media/excel_tmp va kesh fayllarini tozalash
    - Bog'lanmagan (orphan) eski media fayllarni tozalash
    - SQLite WAL checkpoint & optimize + MemoryStorage RAM tozalash
    """
    logger.info("Server avtomatik tozalash (maintenance) rejalashtiruvchisi ishga tushdi.")
    try:
        await asyncio.sleep(15)
    except asyncio.CancelledError:
        return

    while True:
        try:
            await sync_to_async(close_old_connections)()
            await asyncio.to_thread(run_server_maintenance)
            pruned_fsm = prune_empty_fsm_memory(dp.storage)
            if pruned_fsm:
                logger.info("MemoryStorage dan %d ta bo'sh yozuv tozalandi.", pruned_fsm)
            await sync_to_async(close_old_connections)()
            await asyncio.sleep(6 * 3600)
        except asyncio.CancelledError:
            logger.info("Server maintenance rejalashtiruvchisi to'xtatildi.")
            break
        except Exception as exc:
            logger.error("Server maintenance siklida xatolik: %s", exc)
            await asyncio.sleep(1800)


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Botni ishga tushirish / Bosh menyu"),
        BotCommand(command="menu", description="📱 Asosiy Admin menyusi"),
        BotCommand(command="backup", description="💾 Zaxira nusxasini olish (DB Backup)"),
        BotCommand(command="cancel", description="❌ Jarayonni bekor qilish"),
    ]
    await bot.set_my_commands(commands)


async def on_startup(bot: Bot, dispatcher: Dispatcher):
    logger.info("MobiPrice Admin Bot ishga tushdi!")
    logger.info(f"Ruxsat berilgan Admin IDlar: {ADMIN_IDS}")
    await set_bot_commands(bot)

    # Bot username ni umumiy keshga saqlash (saytdagi havolalar har doim ishlashi uchun)
    try:
        me = await bot.get_me()
        if me and me.username:
            await sync_to_async(cache_bot_username)(me.username)
    except Exception as exc:
        logger.warning("Bot username ni keshlashda xatolik: %s", exc)

    # Background vazifalarni ishga tushirish: kunlik backup + 1 soatlik kuryer auto-cancel + server tozalash
    from core.backup_service import daily_backup_scheduler_task

    _background_tasks.clear()
    _background_tasks.append(asyncio.create_task(daily_backup_scheduler_task(bot)))
    _background_tasks.append(asyncio.create_task(courier_expiry_watcher_task(bot, dispatcher)))
    _background_tasks.append(asyncio.create_task(server_maintenance_scheduler_task(dispatcher)))

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
    for task in list(_background_tasks):
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    _background_tasks.clear()

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
    dp.update.outer_middleware(DjangoDBCleanupMiddleware())

    # Register routers in logical sequence (client deep-link router MUST come before start.router)
    dp.include_router(client.router)
    dp.include_router(start.router)
    dp.include_router(brands.router)
    dp.include_router(series.router)
    dp.include_router(phones.router)
    dp.include_router(issues.router)
    dp.include_router(comparisons.router)
    dp.include_router(masters.router)
    dp.include_router(admins.router)
    dp.include_router(crm.router)
    dp.include_router(excel.router)

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
