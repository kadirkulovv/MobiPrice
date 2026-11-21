import logging
import os
import time
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone

from .models import AuthToken, Brand, DevicePhone, ServiceOrder, TeamMember

logger = logging.getLogger("mobiprice_maintenance")

PENDING_COURIER_TIMEOUT_MINUTES = 60
AUTO_CANCEL_TIMEOUT_NOTE = "1 soat ichida lokatsiya yuborilmagani uchun avtomatik bekor qilindi"
USER_CANCEL_BOT_NOTE = "Mijoz botda lokatsiya yuborishni bekor qildi"

MEDIA_MANAGED_SUBDIRS = ("brands", "phones", "masters")


def is_order_location_expired(order: ServiceOrder, now=None) -> bool:
    """Kuryer buyurtmasining lokatsiya yuborish muddati (1 soat) tugaganligini tekshirish."""
    if not order or order.status != "pending_location":
        return False
    ref_now = now or timezone.now()
    if order.courier_token_expires_at:
        return order.courier_token_expires_at <= ref_now
    cutoff = ref_now - timedelta(minutes=PENDING_COURIER_TIMEOUT_MINUTES)
    return order.created_at <= cutoff


def get_order_location_deadline(order: ServiceOrder):
    """Kuryer buyurtmasi lokatsiya yuborish muddati (deadline) ni qaytarish."""
    if order.courier_token_expires_at:
        return order.courier_token_expires_at
    return order.created_at + timedelta(minutes=PENDING_COURIER_TIMEOUT_MINUTES)


def expire_stale_pending_courier_orders(telegram_user=None, now=None) -> list[dict]:
    """
    1 soat ichida lokatsiya yuborilmagan barcha 'pending_location' kuryer buyurtmalarini
    avtomatik ravishda 'cancelled' holatiga o'tkazish.
    Yengil va tezkor: muddati o'tgan buyurtma bo'lmasa yozish tranzaksiyasini ochmaydi.
    """
    ref_now = now or timezone.now()
    cutoff = ref_now - timedelta(minutes=PENDING_COURIER_TIMEOUT_MINUTES)

    stale_filter = Q(status="pending_location") & (
        Q(courier_token_expires_at__lte=ref_now)
        | Q(courier_token_expires_at__isnull=True, created_at__lte=cutoff)
    )
    if telegram_user is not None:
        stale_filter &= Q(telegram_user=telegram_user)

    if not ServiceOrder.objects.filter(stale_filter).exists():
        return []

    expired_info: list[dict] = []
    with transaction.atomic():
        stale_orders = list(
            ServiceOrder.objects.select_for_update()
            .select_related("telegram_user", "phone")
            .filter(stale_filter)
        )
        if not stale_orders:
            return []

        ids_to_cancel = []
        for order in stale_orders:
            ids_to_cancel.append(order.id)
            expired_info.append(
                {
                    "order_pk": order.id,
                    "order_id": order.order_id,
                    "telegram_id": order.telegram_user.telegram_id if order.telegram_user_id and order.telegram_user else None,
                    "phone_name": order.phone.name if order.phone_id and order.phone else "Smartfon",
                }
            )

        ServiceOrder.objects.filter(id__in=ids_to_cancel, status="pending_location").update(
            status="cancelled",
            courier_token=None,
            courier_token_expires_at=None,
            admin_notes=AUTO_CANCEL_TIMEOUT_NOTE,
        )

    logger.info("1 soatlik muddat tugagani sababli %d ta kuryer buyurtmasi avtomatik bekor qilindi.", len(expired_info))
    return expired_info


def cleanup_expired_auth_tokens(grace_hours: int = 1, dry_run: bool = False) -> int:
    """Muddati o'tgan, ishlatilgan yoki rad etilgan eski AuthToken yozuvlarini bazadan tozalash."""
    cutoff = timezone.now() - timedelta(hours=max(0, grace_hours))
    qs = AuthToken.objects.filter(
        Q(expires_at__lt=cutoff)
        | Q(is_used=True, created_at__lt=cutoff)
        | (Q(created_at__lt=cutoff) & ~Q(rejected_reason=""))
    )
    if dry_run:
        return qs.count()
    deleted_count, _ = qs.delete()
    return deleted_count


def cleanup_expired_sessions(dry_run: bool = False) -> int:
    """Muddati tugagan Django sessiya yozuvlarini tozalash (clearsessions ekvivalenti)."""
    qs = Session.objects.filter(expire_date__lt=timezone.now())
    if dry_run:
        return qs.count()
    deleted_count, _ = qs.delete()
    return deleted_count


def cleanup_excel_tmp(max_age_minutes: int = 60, dry_run: bool = False) -> int:
    """media/excel_tmp ichida qolib ketgan vaqtinchalik Excel fayllarini o'chirish."""
    tmp_dir = Path(settings.MEDIA_ROOT) / "excel_tmp"
    if not tmp_dir.exists():
        return 0

    cutoff_ts = time.time() - max(0, max_age_minutes) * 60
    removed = 0
    for item in tmp_dir.iterdir():
        try:
            if not item.is_file():
                continue
            if item.stat().st_mtime <= cutoff_ts:
                if not dry_run:
                    item.unlink()
                removed += 1
        except OSError as exc:
            logger.warning("Excel tmp faylini o'chirishda xatolik (%s): %s", item.name, exc)
    return removed


def cleanup_expired_cache_files(dry_run: bool = False) -> int:
    """FileBasedCache papkasidagi muddati o'tgan .djcache fayllarini tozalash."""
    cache_dir_raw = getattr(cache, "_dir", None)
    if not cache_dir_raw:
        return 0
    cache_dir = Path(cache_dir_raw)
    if not cache_dir.exists() or not cache_dir.is_dir():
        return 0

    is_expired_fn = getattr(cache, "_is_expired", None)
    fallback_cutoff = time.time() - 3600
    removed = 0

    for item in cache_dir.glob("*.djcache"):
        try:
            if not item.is_file():
                continue
            expired = False
            if callable(is_expired_fn):
                with open(item, "rb") as fh:
                    expired = bool(is_expired_fn(fh))
            else:
                expired = item.stat().st_mtime <= fallback_cutoff

            if expired:
                if not dry_run:
                    item.unlink(missing_ok=True)
                removed += 1
        except OSError:
            continue
        except Exception:
            # Buzilgan kesh faylini tozalash
            try:
                if not dry_run:
                    item.unlink(missing_ok=True)
                removed += 1
            except OSError:
                continue
    return removed


def _collect_referenced_media_paths() -> set[str]:
    """Bazadagi barcha faol Brand, DevicePhone va TeamMember media fayl yo'llarini yig'ish."""
    refs: set[str] = set()
    for qs in (
        Brand.objects.exclude(logo="").exclude(logo__isnull=True).values_list("logo", flat=True),
        DevicePhone.objects.exclude(image="").exclude(image__isnull=True).values_list("image", flat=True),
        TeamMember.objects.exclude(photo="").exclude(photo__isnull=True).values_list("photo", flat=True),
    ):
        for rel in qs:
            clean = str(rel or "").strip().lstrip("/")
            if clean:
                refs.add(clean)
    return refs


def safe_delete_media_file(rel_path: str, exclude_model=None, exclude_pk=None) -> bool:
    """
    O'zgartirilgan yoki o'chirilgan modelning eski media faylini diskdan xavfsiz o'chirish.
    Agar boshqa DB yozuvi shu faylga bog'langan bo'lsa, o'chirmaydi.
    """
    clean_rel = str(rel_path or "").strip().lstrip("/")
    if not clean_rel:
        return False

    media_root = Path(settings.MEDIA_ROOT).resolve()
    target = (media_root / clean_rel).resolve()
    try:
        target.relative_to(media_root)
    except ValueError:
        return False

    if not target.exists() or not target.is_file():
        return False

    # Boshqa yozuvlar bu fayldan foydalanayotgan bo'lsa o'chirmaymiz
    checks = (
        (Brand, "logo"),
        (DevicePhone, "image"),
        (TeamMember, "photo"),
    )
    for model_cls, field_name in checks:
        qs = model_cls.objects.filter(**{field_name: clean_rel})
        if exclude_model is model_cls and exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        if qs.exists():
            return False

    try:
        target.unlink()
        return True
    except OSError as exc:
        logger.warning("Eski media faylni o'chirishda xatolik (%s): %s", clean_rel, exc)
        return False


def cleanup_orphan_media(min_age_hours: int = 24, dry_run: bool = False) -> int:
    """
    Bazaga bog'lanmagan (orphan) eski rasm/logotip fayllarini diskdan tozalash.
    24 soatlik xavfsizlik oynasi aktiv yuklanayotgan fayllarga tegmaslikni kafolatlaydi.
    """
    media_root = Path(settings.MEDIA_ROOT).resolve()
    if not media_root.exists():
        return 0

    referenced = _collect_referenced_media_paths()
    cutoff_ts = time.time() - max(0, min_age_hours) * 3600
    removed = 0

    for subdir in MEDIA_MANAGED_SUBDIRS:
        folder = (media_root / subdir).resolve()
        if not folder.exists() or not folder.is_dir():
            continue
        for item in folder.iterdir():
            try:
                if not item.is_file():
                    continue
                rel_posix = item.resolve().relative_to(media_root).as_posix()
                if rel_posix in referenced:
                    continue
                if item.stat().st_mtime > cutoff_ts:
                    continue
                if not dry_run:
                    item.unlink()
                removed += 1
            except (OSError, ValueError) as exc:
                logger.warning("Orphan media faylini tekshirishda xatolik (%s): %s", item.name, exc)
    return removed


def optimize_sqlite_database() -> bool:
    """SQLite WAL faylini qisqartirish va query planner statistikasini yangilash."""
    if connection.vendor != "sqlite":
        return False
    try:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            cursor.execute("PRAGMA optimize;")
        return True
    except Exception as exc:
        logger.warning("SQLite optimallashtirishda xatolik: %s", exc)
        return False


def run_server_maintenance(
    *,
    include_orphan_media: bool = True,
    include_sqlite_optimize: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Server diski, operativ xotira va ma'lumotlar bazasi sog'lomligini saqlash uchun
    barcha avtomatik tozalash vazifalarini bitta joyda xavfsiz bajarish.
    """
    from .backup_service import prune_old_backups

    report: dict = {
        "expired_courier_orders": 0,
        "backups_deleted_gz": 0,
        "backups_deleted_tmp": 0,
        "backups_kept": 0,
        "deleted_auth_tokens": 0,
        "deleted_sessions": 0,
        "deleted_excel_tmp": 0,
        "deleted_cache_files": 0,
        "deleted_orphan_media": 0,
        "sqlite_optimized": False,
    }

    if not dry_run:
        try:
            report["expired_courier_orders"] = len(expire_stale_pending_courier_orders())
        except Exception as exc:
            logger.error("Maintenance expire_stale_pending_courier_orders failed: %s", exc)

        try:
            b_res = prune_old_backups()
            report["backups_deleted_gz"] = b_res["deleted_gz"]
            report["backups_deleted_tmp"] = b_res["deleted_tmp"]
            report["backups_kept"] = b_res["kept"]
        except Exception as exc:
            logger.error("Maintenance prune_old_backups failed: %s", exc)

    try:
        report["deleted_auth_tokens"] = cleanup_expired_auth_tokens(dry_run=dry_run)
    except Exception as exc:
        logger.error("Maintenance cleanup_expired_auth_tokens failed: %s", exc)

    try:
        report["deleted_sessions"] = cleanup_expired_sessions(dry_run=dry_run)
    except Exception as exc:
        logger.error("Maintenance cleanup_expired_sessions failed: %s", exc)

    try:
        report["deleted_excel_tmp"] = cleanup_excel_tmp(dry_run=dry_run)
    except Exception as exc:
        logger.error("Maintenance cleanup_excel_tmp failed: %s", exc)

    try:
        report["deleted_cache_files"] = cleanup_expired_cache_files(dry_run=dry_run)
    except Exception as exc:
        logger.error("Maintenance cleanup_expired_cache_files failed: %s", exc)

    if include_orphan_media:
        try:
            report["deleted_orphan_media"] = cleanup_orphan_media(dry_run=dry_run)
        except Exception as exc:
            logger.error("Maintenance cleanup_orphan_media failed: %s", exc)

    if include_sqlite_optimize and not dry_run:
        report["sqlite_optimized"] = optimize_sqlite_database()

    cleaned_total = (
        report["expired_courier_orders"]
        + report["backups_deleted_gz"]
        + report["backups_deleted_tmp"]
        + report["deleted_auth_tokens"]
        + report["deleted_sessions"]
        + report["deleted_excel_tmp"]
        + report["deleted_cache_files"]
        + report["deleted_orphan_media"]
    )
    if cleaned_total > 0:
        logger.info("Server maintenance yakunlandi: %s", report)
    return report

