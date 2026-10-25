from dataclasses import dataclass
from typing import Optional
from bot.config import ADMIN_IDS
from bot.database import BotAdmin, sync_to_async


@dataclass
class UserPermissions:
    """Foydalanuvchi huquqlari va rollari"""
    is_superadmin: bool = False
    can_manage_site: bool = False
    can_handle_leads: bool = False
    can_manage_admins: bool = False
    role: Optional[str] = None  # 'superadmin', 'admin', 'manager', 'both'
    role_badge: str = ""
    display_name: str = ""
    db_obj: Optional[object] = None

    @property
    def has_any_access(self) -> bool:
        return self.is_superadmin or self.can_manage_site or self.can_handle_leads


def check_permissions_sync(user_id: int, username: str = None) -> UserPermissions:
    """Foydalanuvchi huquqlarini sinxron tekshirish"""
    # 1. Glavniy Admin (Superadmin) .env dagi ID bo'yicha
    if ADMIN_IDS and user_id in ADMIN_IDS:
        return UserPermissions(
            is_superadmin=True,
            can_manage_site=True,
            can_handle_leads=True,
            can_manage_admins=True,  # Faqat Glavniy admin boshqa adminlarni qo'sha/o'chira oladi
            role='superadmin',
            role_badge="👑 Bosh Admin (Superadmin)",
            display_name="Bosh Admin"
        )

    # 2. Bazadagi BotAdmin jadvalidan tekshirish
    obj = None
    if user_id:
        obj = BotAdmin.objects.filter(telegram_id=user_id, is_active=True).first()

    if not obj and username:
        clean_user = username.replace('@', '').strip().lower()
        obj = BotAdmin.objects.filter(username__iexact=clean_user, is_active=True).first()
        if obj and user_id and not obj.telegram_id:
            obj.telegram_id = user_id
            obj.save(update_fields=['telegram_id'])

    if obj:
        role = obj.role
        can_site = role in ('admin', 'both')
        can_leads = role in ('manager', 'both')
        return UserPermissions(
            is_superadmin=False,
            can_manage_site=can_site,
            can_handle_leads=can_leads,
            can_manage_admins=False,  # Oddiy admin yoki menejer boshqa admin qo'sha olmaydi!
            role=role,
            role_badge=obj.role_badge,
            display_name=obj.full_name or (f"@{obj.username}" if obj.username else str(obj.telegram_id)),
            db_obj=obj
        )

    return UserPermissions()


@sync_to_async
def get_user_permissions(user_id: int, username: str = None) -> UserPermissions:
    """Foydalanuvchi huquqlarini asinxron olish"""
    return check_permissions_sync(user_id, username)


@sync_to_async
def can_manage_site_user(user_id: int, username: str = None) -> bool:
    perms = check_permissions_sync(user_id, username)
    return perms.can_manage_site


@sync_to_async
def can_handle_leads_user(user_id: int, username: str = None) -> bool:
    perms = check_permissions_sync(user_id, username)
    return perms.can_handle_leads


@sync_to_async
def is_superadmin_user(user_id: int, username: str = None) -> bool:
    perms = check_permissions_sync(user_id, username)
    return perms.is_superadmin
