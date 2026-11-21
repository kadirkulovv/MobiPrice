from django.core.management.base import BaseCommand

from core.maintenance import run_server_maintenance


class Command(BaseCommand):
    help = "Server diski va bazasini avtomatik tozalash (backups rotatsiya, eski tokenlar, sessiyalar, temp/orphan fayllar)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Hech narsani o'chirmasdan, nechta yozuv/fayl tozalanishini ko'rsatish",
        )
        parser.add_argument(
            "--skip-media",
            action="store_true",
            help="Bog'lanmagan (orphan) media fayllarni tekshirishni o'tkazib yuborish",
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run"))
        skip_media = bool(options.get("skip_media"))

        report = run_server_maintenance(
            include_orphan_media=not skip_media,
            include_sqlite_optimize=not dry_run,
            dry_run=dry_run,
        )

        prefix = "[DRY-RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}MobiPrice Server Cleanup yakunlandi:\n"
                f"  • Muddati o'tgan kuryer buyurtmalari (auto-cancel): {report['expired_courier_orders']}\n"
                f"  • Eski backup arxivlari o'chirildi: {report['backups_deleted_gz']} (temp: {report['backups_deleted_tmp']}, qoldi: {report['backups_kept']})\n"
                f"  • Eski AuthToken lar o'chirildi: {report['deleted_auth_tokens']}\n"
                f"  • Muddati o'tgan sessiyalar o'chirildi: {report['deleted_sessions']}\n"
                f"  • Vaqtinchalik Excel fayllari o'chirildi: {report['deleted_excel_tmp']}\n"
                f"  • Muddati o'tgan kesh fayllari o'chirildi: {report['deleted_cache_files']}\n"
                f"  • Bog'lanmagan (orphan) media fayllari o'chirildi: {report['deleted_orphan_media']}\n"
                f"  • SQLite WAL checkpoint & optimize: {'OK' if report['sqlite_optimized'] else 'skip'}"
            )
        )

