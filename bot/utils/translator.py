import asyncio
import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger("mobiprice_translator")

# Curated phone repair terms dictionary (UZ -> RU, EN)
REPAIR_GLOSSARY = {
    "ekran": ("Экран (Дисплей)", "Screen / Display"),
    "ekran almashtirish": ("Замена экрана", "Screen Replacement"),
    "displey": ("Дисплей", "Display"),
    "displey almashtirish": ("Замена дисплея", "Display Replacement"),
    "batareya": ("Аккумулятор (Батарея)", "Battery"),
    "batareya almashtirish": ("Замена аккумулятора", "Battery Replacement"),
    "akkumulyator": ("Аккумулятор", "Battery"),
    "akkumulyator almashtirish": ("Замена аккумулятора", "Battery Replacement"),
    "orqa shisha": ("Заднее стекло", "Back Glass"),
    "orqa shisha almashtirish": ("Замена заднего стекла", "Back Glass Replacement"),
    "orqa oyna": ("Заднее стекло", "Back Glass"),
    "orqa oyna almashtirish": ("Замена заднего стекла", "Back Glass Replacement"),
    "kamera": ("Камера", "Camera"),
    "kamera almashtirish": ("Замена камеры", "Camera Replacement"),
    "kamera oynasi": ("Стекло камеры", "Camera Glass"),
    "kamera shishasi": ("Стекло камеры", "Camera Glass"),
    "old kamera": ("Фронтальная камера", "Front Camera"),
    "zaryad porti": ("Разъем зарядки", "Charging Port"),
    "zaryad razyomi": ("Разъем зарядки", "Charging Port"),
    "zaryad portini almashtirish": ("Замена разъема зарядки", "Charging Port Replacement"),
    "dinamik": ("Динамик", "Speaker"),
    "dinamik almashtirish": ("Замена динамика", "Speaker Replacement"),
    "karnay": ("Динамик", "Speaker"),
    "mikrofon": ("Микрофон", "Microphone"),
    "mikrofon almashtirish": ("Замена микрофона", "Microphone Replacement"),
    "korpus": ("Корпус", "Housing / Frame"),
    "korpus almashtirish": ("Замена корпуса", "Housing Replacement"),
    "face id": ("Восстановление Face ID", "Face ID Repair"),
    "face id tiklash": ("Восстановление Face ID", "Face ID Repair"),
    "barmoq izi": ("Сканер отпечатка", "Fingerprint Sensor"),
    "touch id": ("Ремонт Touch ID", "Touch ID Repair"),
    "plata": ("Материнская плата", "Motherboard"),
    "plata ta'miri": ("Ремонт платы", "Motherboard Repair"),
    "chip": ("Микросхема / Чип", "Microchip / IC"),
    "suv tozalash": ("Чистка после воды", "Water Damage Cleaning"),
    "suv tushishi": ("Чистка от влаги", "Water Damage Cleaning"),
    "tugmalar": ("Кнопки", "Buttons"),
    "ovoz tugmasi": ("Кнопка громкости", "Volume Button"),
    "shleyf": ("Шлейф", "Flex Cable"),
    "vibratsiya": ("Вибромотор", "Vibration Motor"),
    "wi-fi": ("Ремонт Wi-Fi", "Wi-Fi Repair"),
    "bluetooth": ("Ремонт Bluetooth", "Bluetooth Repair"),
    "sim karta": ("SIM-лоток / Слот", "SIM Tray / Slot"),
    "sim slot": ("Слот SIM-карты", "SIM Card Slot"),
}


def _http_translate(text: str, target_lang: str) -> str:
    """Synchronous translate via Google Translate public API."""
    try:
        url = (
            f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=uz&tl={target_lang}&dt=t&q="
            + urllib.parse.quote(text)
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            result = "".join([part[0] for part in data[0] if part[0]])
            return result.strip() if result else text
    except Exception as e:
        logger.warning(f"Translation failed for '{text}' to '{target_lang}': {e}")
        return text


async def auto_translate_issue_title(title_uz: str) -> tuple[str, str]:
    """
    Takes an issue title in Uzbek, returns (title_ru, title_en).
    First checks curated phone repair dictionary; if not found, uses online translator.
    """
    clean_uz = title_uz.strip()
    norm = clean_uz.lower()

    # 1. Exact match in glossary
    if norm in REPAIR_GLOSSARY:
        ru, en = REPAIR_GLOSSARY[norm]
        return ru, en

    # 2. Check if any glossary key is a major substring
    for key, (ru, en) in REPAIR_GLOSSARY.items():
        if key == norm or key in norm:
            # If the user typed "iPhone 15 ekran almashtirish" -> match
            pass

    # 3. Perform online translation asynchronously
    try:
        ru_task = asyncio.to_thread(_http_translate, clean_uz, "ru")
        en_task = asyncio.to_thread(_http_translate, clean_uz, "en")
        title_ru, title_en = await asyncio.gather(ru_task, en_task)

        # Capitalize nicely
        if title_ru and len(title_ru) > 1:
            title_ru = title_ru[0].upper() + title_ru[1:]
        if title_en and len(title_en) > 1:
            title_en = title_en[0].upper() + title_en[1:]

        return title_ru or clean_uz, title_en or clean_uz
    except Exception as e:
        logger.error(f"Async translation error: {e}")
        return clean_uz, clean_uz
