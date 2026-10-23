from django.apps import AppConfig
from django.db.backends.signals import connection_created


def activate_sqlite_wal(sender, connection, **kwargs):
    """Enable WAL mode and busy timeout for high-concurrency SQLite operations"""
    if connection.vendor == 'sqlite':
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA journal_mode = WAL;')
            cursor.execute('PRAGMA synchronous = NORMAL;')
            cursor.execute('PRAGMA busy_timeout = 5000;')


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        connection_created.connect(activate_sqlite_wal)
