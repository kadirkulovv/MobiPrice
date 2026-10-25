import os
import gzip
import sqlite3
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot
from aiogram.types import FSInputFile
from django.conf import settings
from bot.database import BotAdmin, sync_to_async

logger = logging.getLogger("mobiprice_backup")
TZ_TASHKENT = ZoneInfo("Asia/Tashkent")


def create_db_backup() -> tuple[Path, float]:
    """
    SQLite ma'lumotlar bazasini xavfsiz (hot backup) usulida zaxiralash
    va gzip bilan siqish (sayt to'xtamaydi, jadvallar bloklanmaydi).
    """
    base_dir = settings.BASE_DIR
    backup_dir = base_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(TZ_TASHKENT).strftime("%Y%m%d_%H%M%S")
    db_file = base_dir / "db.sqlite3"
    raw_backup_path = backup_dir / f"mobiprice_db_{timestamp}.sqlite3"
    gz_backup_path = backup_dir / f"mobiprice_db_{timestamp}.sqlite3.gz"

    # 1. Native SQLite hot backup (WAL-safe)
    src_conn = sqlite3.connect(str(db_file))
    dst_conn = sqlite3.connect(str(raw_backup_path))
    src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()

    # 2. Gzip compression
    with open(raw_backup_path, "rb") as f_in, gzip.open(gz_backup_path, "wb", compresslevel=9) as f_out:
        while chunk := f_in.read(64 * 1024):
            f_out.write(chunk)

    # Xom faylni o'chiramiz, faqat siqilgan .gz qoladi
    if raw_backup_path.exists():
        raw_backup_path.unlink()

    # 3. 14 kundan eski arxivlarni avtomatik tozalash
    retention_cutoff = datetime.now() - timedelta(days=14)
    for old_file in backup_dir.glob("*.gz"):
        try:
            mtime = datetime.fromtimestamp(old_file.stat().st_mtime)
            if mtime < retention_cutoff:
                old_file.unlink()
        except Exception:
            pass

    size_kb = gz_backup_path.stat().st_size / 1024
    return gz_backup_path, size_kb


async def get_all_admin_ids() -> list[int]:
    """Konfiguratsiyadagi va ma'lumotlar bazasidagi barcha faol adminlar IDlari"""
    admin_ids: list[int] = []

    # Config / settings dan
    raw_env_ids = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '') or os.getenv('TELEGRAM_ADMIN_CHAT_ID', '') or os.getenv('TELEGRAM_ADMIN_IDS', '')
    for item in str(raw_env_ids).split(','):
        item = item.strip()
        if item.isdigit():
            admin_ids.append(int(item))

    # BotAdmin modelidan faqat sayt adminlari (menejerlar bazani olmasligi kerak)
    try:
        db_admins = await sync_to_async(list)(
            BotAdmin.objects.filter(
                is_active=True,
                role__in=['admin', 'both']
            ).exclude(telegram_id__isnull=True).values_list('telegram_id', flat=True)
        )
        for tid in db_admins:
            if tid and tid not in admin_ids:
                admin_ids.append(int(tid))
    except Exception as e:
        logger.warning(f"BotAdmin bazadan olinmadi: {e}")

    return admin_ids


async def send_backup_to_admins(bot: Bot, trigger: str = "Avtomatik kunlik zaxira (00:00)") -> dict:
    """Zaxira nusxasini tayyorlab, barcha adminlarga Telegram orqali yuborish"""
    try:
        gz_path, size_kb = await asyncio.to_thread(create_db_backup)
    except Exception as e:
        logger.error(f"Zaxira faylini yaratishda xatolik: {e}")
        return {'success': False, 'error': str(e)}

    admin_ids = await get_all_admin_ids()
    if not admin_ids:
        logger.warning("Zaxirani yuborish uchun birorta ham admin ID topilmadi.")
        return {'success': False, 'error': "Admin IDlar topilmadi"}

    now_tashkent = datetime.now(TZ_TASHKENT).strftime("%d.%m.%Y %H:%M:%S")
    caption = (
        f"💾 <b>MobiPrice Ma'lumotlar Bazasi Zaxirasi</b>\n\n"
        f"⏰ <b>Vaqt:</b> {now_tashkent} (Asia/Tashkent)\n"
        f"📦 <b>Turi:</b> SQLite3 (Gzip siqilgan .gz)\n"
        f"📁 <b>Hajmi:</b> {size_kb:.1f} KB\n"
        f"🚀 <b>Sabab:</b> {trigger}\n"
        f"🛡 <b>Xavfsizlik:</b> WAL-safe snapshot (to‘liq ma'lumot saqlangan)"
    )

    doc_file = FSInputFile(path=str(gz_path), filename=gz_path.name)
    sent_count = 0

    for aid in admin_ids:
        try:
            await bot.send_document(
                chat_id=aid,
                document=doc_file,
                caption=caption,
                parse_mode="HTML"
            )
            sent_count += 1
            logger.info(f"Zaxira fayli admin {aid} ga yuborildi.")
        except Exception as e:
            logger.error(f"Admin {aid} ga zaxira yuborilmadi: {e}")

    return {'success': True, 'sent_count': sent_count, 'file': str(gz_path), 'size_kb': size_kb}


async def daily_backup_scheduler_task(bot: Bot):
    """
    Har kuni 00:00 (Asia/Tashkent) vaqtida avtomatik ravishda
    adminlarga bazaning zaxira nusxasini yuboruvchi asinxron scheduler.
    """
    logger.info("MobiPrice kunlik avtomatik zaxira (00:00 Asia/Tashkent) rejalashtiruvchisi ishga tushdi.")
    while True:
        try:
            now = datetime.now(TZ_TASHKENT)
            # Ertangi kun 00:00:00 vaqti
            tomorrow = now.date() + timedelta(days=1)
            target = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0, tzinfo=TZ_TASHKENT)
            sleep_seconds = (target - now).total_seconds()

            logger.info(
                f"Keyingi avtomatik zaxira nusxasi {target.strftime('%d.%m.%Y %H:%M:%S')} da "
                f"({int(sleep_seconds // 3600)} soat {int((sleep_seconds % 3600) // 60)} daqiqadan so‘ng) yuboriladi."
            )

            await asyncio.sleep(sleep_seconds)

            # 00:00 da zaxirani barcha adminlarga yuboramiz
            await send_backup_to_admins(bot, trigger="Kunlik avtomatik reja (00:00 Asia/Tashkent)")

            # Bir soniya kutamiz (qayta-qayta chaqirilmasligi uchun)
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            logger.info("Zaxira rejalashtiruvchisi bekor qilindi.")
            break
        except Exception as e:
            logger.error(f"Scheduler siklida xatolik: {e}")
            await asyncio.sleep(60)
