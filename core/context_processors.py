from .telegram_auth import get_bot_username, get_current_telegram_user, get_shop_info


def telegram_auth_context(request):
    """Har bir Django shabloniga aktiv Telegram foydalanuvchi, bot username va do'kon ma'lumotlarini uzatish"""
    return {
        'tg_user': get_current_telegram_user(request),
        'telegram_bot_username': get_bot_username(),
        'shop_info': get_shop_info(),
    }

