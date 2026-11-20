import hashlib
import hmac
import logging
import time
from typing import Optional, Tuple

import requests
from django.conf import settings
from django.core.cache import cache

from .models import TelegramUser

logger = logging.getLogger(__name__)

SESSION_KEY_TG_USER_ID = 'telegram_user_id'
BOT_USERNAME_CACHE_KEY = 'mobiprice_telegram_bot_username'
BOT_USERNAME_CACHE_TTL = 3600
BOT_USERNAME_ERROR_TTL = 60


def get_bot_username() -> str:
    """
    Telegram bot username ni olish:
    1) settings.TELEGRAM_BOT_USERNAME (agar .env da ko'rsatilgan bo'lsa)
    2) Aks holda TELEGRAM_BOT_TOKEN orqali Telegram API getMe ni 1 marta so'rab,
       natijani django.core.cache da 1 soat keshlab saqlash.
    """
    configured = str(getattr(settings, 'TELEGRAM_BOT_USERNAME', '') or '').lstrip('@').strip()
    if configured:
        return configured

    cached = cache.get(BOT_USERNAME_CACHE_KEY, None)
    if cached is not None:
        return str(cached)

    bot_token = str(getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or '').strip()
    if not bot_token:
        return ''

    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{bot_token}/getMe",
            timeout=3,
        )
        if resp.status_code == 200:
            payload = resp.json()
            if payload.get('ok'):
                username = str(payload.get('result', {}).get('username') or '').lstrip('@').strip()
                if username:
                    cache.set(BOT_USERNAME_CACHE_KEY, username, BOT_USERNAME_CACHE_TTL)
                    return username
    except Exception as exc:
        logger.warning("Failed to fetch Telegram bot username via getMe: %s", exc)

    cache.set(BOT_USERNAME_CACHE_KEY, '', BOT_USERNAME_ERROR_TTL)
    return ''


def sanitize_photo_url(raw_url: str) -> str:
    """
    Faqat xavfsiz ochiq profil avatar URL'ini qabul qilish.
    Hech qachon BOT_TOKEN o'z ichiga olgan Telegram file API URL'larini saqlamaydi.
    """
    url = str(raw_url or '').strip()
    if not url:
        return ''
    if not (url.startswith('https://') or url.startswith('http://')):
        return ''
    lower = url.lower()
    if '/file/bot' in lower or 'api.telegram.org' in lower:
        return ''
    bot_token = str(getattr(settings, 'TELEGRAM_BOT_TOKEN', '') or '').strip()
    if bot_token and bot_token in url:
        return ''
    return url[:500]


def verify_telegram_widget_data(
    payload: dict,
    bot_token: str,
    max_age_seconds: int = 300,
) -> Tuple[bool, str]:
    """
    Rasmiy Telegram Login Widget HMAC-SHA256 imzosi va auth_date muddatini qat'iy tekshirish.
    https://core.telegram.org/widgets/login#checking-authorization
    """
    if not isinstance(payload, dict) or not bot_token:
        return False, "Invalid auth payload or bot token"

    received_hash = str(payload.get('hash') or '').strip().lower()
    if not received_hash or len(received_hash) != 64:
        return False, "Missing or invalid hash"

    raw_id = payload.get('id')
    try:
        tg_id = int(raw_id)
        if tg_id <= 0:
            return False, "Invalid Telegram user ID"
    except (TypeError, ValueError):
        return False, "Invalid Telegram user ID"

    raw_auth_date = payload.get('auth_date')
    try:
        auth_date = int(raw_auth_date)
    except (TypeError, ValueError):
        return False, "Invalid auth_date"

    now_ts = int(time.time())
    if auth_date > now_ts + 60:
        return False, "auth_date is in the future"
    if now_ts - auth_date > max_age_seconds:
        return False, "auth_date has expired"

    check_parts = []
    for key in sorted(payload.keys()):
        if key == 'hash':
            continue
        val = payload[key]
        if val is None or val == '':
            continue
        check_parts.append(f"{key}={val}")

    if not check_parts:
        return False, "Empty auth payload"

    data_check_string = "\n".join(check_parts)
    secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
    expected_hash = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        return False, "Invalid Telegram signature"

    return True, "ok"


def normalize_phone_number(raw_phone: str) -> str:
    """
    Telegram contact orqali kelgan telefon raqamini standart +<raqamlar> formatiga keltirish.
    7 dan 15 tagacha raqam bo'lishi shart (E.164 standarti).
    """
    raw = str(raw_phone or '').strip()
    if not raw:
        return ''
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        return ''
    return f"+{digits}"


def is_uzbek_phone_number(raw_phone: str) -> bool:
    """Faqat O'zbekiston telefon raqami (+998 + 9 ta raqam, jami 12 ta raqam) ekanligini tekshirish."""
    normalized = normalize_phone_number(raw_phone)
    if not normalized:
        return False
    digits = normalized[1:]
    return len(digits) == 12 and digits.startswith('998')


def normalize_uzbek_phone_number(raw_phone: str) -> str:
    """Faqat O'zbekiston (+998XXXXXXXXX) raqamini qaytarish; aks holda bo'sh satr."""
    normalized = normalize_phone_number(raw_phone)
    if normalized and is_uzbek_phone_number(normalized):
        return normalized
    return ''


def upsert_telegram_user(data: dict) -> TelegramUser:
    """
    Telegram foydalanuvchi profilini yaratish yoki yangilash.
    Faqat ochiq profil maydonlari (id, first_name, last_name, username, ochiq photo_url)
    hamda bot tugmasi orqali tasdiqlangan O'zbekiston (+998) telefon raqami (agar berilgan bo'lsa) saqlanadi.
    """
    tg_id = int(data['id'])
    first_name = str(data.get('first_name') or '').strip()[:150]
    last_name = str(data.get('last_name') or '').strip()[:150]
    username = str(data.get('username') or '').lstrip('@').strip()[:150]
    has_photo_key = 'photo_url' in data and data.get('photo_url') is not None
    clean_photo_url = sanitize_photo_url(data.get('photo_url') or '') if has_photo_key else ''
    clean_phone = normalize_uzbek_phone_number(data.get('phone_number') or '')

    defaults = {
        'first_name': first_name,
        'last_name': last_name,
        'username': username,
    }
    if has_photo_key:
        defaults['photo_url'] = clean_photo_url
    if clean_phone:
        defaults['phone_number'] = clean_phone

    tg_user, created = TelegramUser.objects.get_or_create(
        telegram_id=tg_id,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'phone_number': clean_phone,
            'photo_url': clean_photo_url,
        },
    )

    if not created:
        update_fields = []
        for field_name, new_val in defaults.items():
            if getattr(tg_user, field_name) != new_val:
                setattr(tg_user, field_name, new_val)
                update_fields.append(field_name)
        if update_fields:
            update_fields.append('updated_at')
            tg_user.save(update_fields=update_fields)

    return tg_user


def serialize_telegram_user(tg_user: Optional[TelegramUser]) -> Optional[dict]:
    """Frontend va API javoblari uchun xavfsiz foydalanuvchi obyekti"""
    if not tg_user:
        return None
    return {
        'id': tg_user.id,
        'telegram_id': tg_user.telegram_id,
        'first_name': tg_user.first_name,
        'last_name': tg_user.last_name,
        'full_name': tg_user.full_name,
        'username': tg_user.username,
        'phone_number': tg_user.phone_number,
        'display_handle': tg_user.display_handle,
        'photo_url': tg_user.photo_url,
        'initials': tg_user.initials,
        'tg_profile_url': tg_user.tg_profile_url,
    }


def get_current_telegram_user(request) -> Optional[TelegramUser]:
    """Aktiv Django sessiyasiga bog'langan TelegramUser ni olish"""
    if hasattr(request, '_cached_tg_user'):
        return request._cached_tg_user

    tg_user_id = request.session.get(SESSION_KEY_TG_USER_ID)
    if not tg_user_id:
        request._cached_tg_user = None
        return None

    tg_user = TelegramUser.objects.filter(id=tg_user_id).first()
    if not tg_user or not is_uzbek_phone_number(tg_user.phone_number):
        request.session.pop(SESSION_KEY_TG_USER_ID, None)
        request._cached_tg_user = None
        return None

    request._cached_tg_user = tg_user
    return tg_user


def login_telegram_session(request, tg_user: TelegramUser) -> None:
    """Telegram foydalanuvchini Django sessiyasiga biriktirish (session fixation himoyasi bilan)"""
    if not request.session.session_key:
        request.session.create()
    request.session[SESSION_KEY_TG_USER_ID] = tg_user.id
    request.session.cycle_key()
    request._cached_tg_user = tg_user


def logout_telegram_session(request) -> None:
    """Telegram sessiyasidan xavfsiz chiqish"""
    request.session.pop(SESSION_KEY_TG_USER_ID, None)
    request.session.cycle_key()
    request._cached_tg_user = None


def get_shop_info() -> dict:
    """Do'kon / servis markazi lokatsiya ma'lumotlari"""
    return {
        'lat': settings.SHOP_LAT,
        'lon': settings.SHOP_LON,
        'address': settings.SHOP_ADDRESS,
        'google_maps_url': settings.SHOP_GOOGLE_MAPS_URL,
        'yandex_maps_url': settings.SHOP_YANDEX_MAPS_URL,
    }

