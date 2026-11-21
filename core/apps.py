import os

from django.apps import AppConfig
from django.db.backends.signals import connection_created


def activate_sqlite_wal(sender, connection, **kwargs):
    """
    Production VPS uchun xavfsiz va tezkor SQLite WAL sozlamalari:
    - 16MB cache per connection (kichik VPS da OOM oldini oladi)
    - 64MB mmap & 16MB WAL journal hajmi chegarasi
    """
    if connection.vendor == 'sqlite':
        cache_kb = int(os.getenv('SQLITE_CACHE_KB', '16000'))
        mmap_bytes = int(os.getenv('SQLITE_MMAP_BYTES', str(64 * 1024 * 1024)))
        wal_limit_bytes = int(os.getenv('SQLITE_JOURNAL_LIMIT_BYTES', str(16 * 1024 * 1024)))
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode = WAL;')
            cursor.execute('PRAGMA synchronous = NORMAL;')
            cursor.execute('PRAGMA busy_timeout = 30000;')
            cursor.execute(f'PRAGMA cache_size = -{max(2000, cache_kb)};')
            cursor.execute(f'PRAGMA mmap_size = {max(0, mmap_bytes)};')
            cursor.execute(f'PRAGMA journal_size_limit = {max(1024 * 1024, wal_limit_bytes)};')
            cursor.execute('PRAGMA temp_store = MEMORY;')


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        connection_created.connect(activate_sqlite_wal)

        # Invalidate API cache when catalog data changes (NOT on Review to keep rate limits & cache warm)
        from django.core.cache import cache
        from django.db.models.signals import post_delete, post_save, pre_save
        from .maintenance import safe_delete_media_file
        from .models import (
            Brand,
            DeviceIssue,
            DevicePhone,
            DeviceSeries,
            IssueComparison,
            RepairFAQ,
            TeamMember,
        )

        def clear_catalog_cache(sender, **kwargs):
            try:
                cache.clear()
            except Exception:
                pass

        for model in (Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison, RepairFAQ, TeamMember):
            post_save.connect(clear_catalog_cache, sender=model, dispatch_uid=f"clear_cache_save_{model.__name__}")
            post_delete.connect(clear_catalog_cache, sender=model, dispatch_uid=f"clear_cache_del_{model.__name__}")

        # Auto-cleanup replaced or deleted media files to prevent disk bloat
        media_models = (
            (Brand, 'logo'),
            (DevicePhone, 'image'),
            (TeamMember, 'photo'),
        )

        def _make_cleanup_handlers(model_cls, field_name):
            def _on_pre_save(sender, instance, **kwargs):
                if not instance.pk:
                    return
                try:
                    old_rel = (
                        model_cls.objects.filter(pk=instance.pk)
                        .values_list(field_name, flat=True)
                        .first()
                    )
                except Exception:
                    return
                new_file = getattr(instance, field_name, None)
                new_rel = getattr(new_file, 'name', '') or ''
                if old_rel and old_rel != new_rel:
                    safe_delete_media_file(old_rel, exclude_model=model_cls, exclude_pk=instance.pk)

            def _on_post_delete(sender, instance, **kwargs):
                old_file = getattr(instance, field_name, None)
                old_rel = getattr(old_file, 'name', '') or ''
                if old_rel:
                    safe_delete_media_file(old_rel, exclude_model=model_cls, exclude_pk=instance.pk)

            return _on_pre_save, _on_post_delete

        for model_cls, field_name in media_models:
            pre_h, del_h = _make_cleanup_handlers(model_cls, field_name)
            pre_save.connect(pre_h, sender=model_cls, dispatch_uid=f"media_replace_{model_cls.__name__}_{field_name}")
            post_delete.connect(del_h, sender=model_cls, dispatch_uid=f"media_delete_{model_cls.__name__}_{field_name}")
