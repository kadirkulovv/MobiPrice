from django.apps import AppConfig
from django.db.backends.signals import connection_created


def activate_sqlite_wal(sender, connection, **kwargs):
    """Enable WAL mode, 30s busy timeout, 64MB cache and MMAP for high-concurrency SQLite operations"""
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode = WAL;')
            cursor.execute('PRAGMA synchronous = NORMAL;')
            cursor.execute('PRAGMA busy_timeout = 30000;')
            cursor.execute('PRAGMA cache_size = -64000;')
            cursor.execute('PRAGMA mmap_size = 268435456;')
            cursor.execute('PRAGMA temp_store = MEMORY;')


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        connection_created.connect(activate_sqlite_wal)

        # Invalidate API memory cache when catalog data changes
        from django.db.models.signals import post_save, post_delete
        from django.core.cache import cache
        from .models import Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison

        def clear_catalog_cache(sender, **kwargs):
            try:
                cache.clear()
            except Exception:
                pass

        for model in (Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison):
            post_save.connect(clear_catalog_cache, sender=model)
            post_delete.connect(clear_catalog_cache, sender=model)

