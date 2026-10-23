#!/usr/bin/env python3
import os
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
BOT_ICONS_DIR = BASE_DIR / "bot" / "assets" / "icons"
STATIC_ICONS_DIR = BASE_DIR / "static" / "img" / "icons"
CHEATSHEET_PATH = BASE_DIR / "bot" / "assets" / "icons_cheatsheet.png"

# Delete and recreate folders
for folder in [BOT_ICONS_DIR, STATIC_ICONS_DIR]:
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)

# 30 real graphic icons (clean SVG vector code, NO numbers inside SVGs)
ICONS = [
    {
        "id": 1,
        "name": "Samolyotcha",
        "sub": "Tez yetkazish",
        "paths": '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
        "draw": "plane",
    },
    {
        "id": 2,
        "name": "Yulduzcha",
        "sub": "Top / Premium",
        "paths": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
        "draw": "star",
    },
    {
        "id": 3,
        "name": "Telefon",
        "sub": "Smartfon",
        "paths": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/>',
        "draw": "phone",
    },
    {
        "id": 4,
        "name": "Ekran",
        "sub": "Displey almashtirish",
        "paths": '<rect width="14" height="20" x="5" y="2" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="18" x2="16" y2="18"/><path d="M7 11l4 2-2 3 5 2"/>',
        "draw": "screen",
    },
    {
        "id": 5,
        "name": "Batareya",
        "sub": "Akkumulyator",
        "paths": '<rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><line x1="22" x2="22" y1="11" y2="13"/><path d="m11 9-2 3h4l-2 3"/>',
        "draw": "battery",
    },
    {
        "id": 6,
        "name": "Kamera",
        "sub": "Kamera / Linzalar",
        "paths": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
        "draw": "camera",
    },
    {
        "id": 7,
        "name": "Dinamik",
        "sub": "Karnay / Ovoz",
        "paths": '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>',
        "draw": "speaker",
    },
    {
        "id": 8,
        "name": "Mikrofon",
        "sub": "Ovoz yozish",
        "paths": '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>',
        "draw": "mic",
    },
    {
        "id": 9,
        "name": "Zaryad porti",
        "sub": "Type-C / Lightning",
        "paths": '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4V8Z"/>',
        "draw": "plug",
    },
    {
        "id": 10,
        "name": "Wi-Fi",
        "sub": "Simsiz tarmoq",
        "paths": '<path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" x2="12.01" y1="20" y2="20"/>',
        "draw": "wifi",
    },
    {
        "id": 11,
        "name": "Bluetooth",
        "sub": "Aloqa moduli",
        "paths": '<path d="m7 7 10 10-5 5V2l5 5L7 17"/>',
        "draw": "bluetooth",
    },
    {
        "id": 12,
        "name": "SIM karta",
        "sub": "Slot / Tray",
        "paths": '<path d="M6 2h8l6 6v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/><path d="M9 18v-4"/><path d="M12 18v-4"/><path d="M15 18v-4"/><path d="M9 10h6"/>',
        "draw": "sim",
    },
    {
        "id": 13,
        "name": "Face ID",
        "sub": "Yuz skaneri",
        "paths": '<path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/><path d="M9 9h.01"/><path d="M15 9h.01"/><path d="M10 14a2 2 0 0 0 4 0"/>',
        "draw": "faceid",
    },
    {
        "id": 14,
        "name": "Barmoq izi",
        "sub": "Touch ID",
        "paths": '<path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"/><path d="M14 13.12c0 2.38 0 6.38-1 8.88"/><path d="M2 12a10 10 0 0 1 18-6"/><path d="M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2"/><path d="M9 6.8a6 6 0 0 1 9 5.2v2"/>',
        "draw": "fingerprint",
    },
    {
        "id": 15,
        "name": "Quloqchin",
        "sub": "Audio jack / Naushnik",
        "paths": '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"/>',
        "draw": "headphones",
    },
    {
        "id": 16,
        "name": "Tugmalar",
        "sub": "Ovoz / Power",
        "paths": '<rect width="12" height="20" x="6" y="2" rx="2"/><path d="M3 7v3"/><path d="M3 12v3"/><path d="M21 9v4"/>',
        "draw": "buttons",
    },
    {
        "id": 17,
        "name": "Orqa oyna",
        "sub": "Korpus tiklash",
        "paths": '<rect width="14" height="20" x="5" y="2" rx="3"/><rect width="5" height="5" x="7" y="4" rx="1"/><path d="M12 18h.01"/><path d="m14 9-5 6"/>',
        "draw": "backglass",
    },
    {
        "id": 18,
        "name": "Lazer",
        "sub": "Lazerli ta\'mir",
        "paths": '<path d="m14 12 7-7"/><path d="M18 10h3v-3"/><path d="M10 14 3 21"/><path d="M6 14H3v3"/><circle cx="12" cy="12" r="3"/>',
        "draw": "laser",
    },
    {
        "id": 19,
        "name": "Suv tozalash",
        "sub": "Suv tushishi / Tomchi",
        "paths": '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>',
        "draw": "water",
    },
    {
        "id": 20,
        "name": "Qalqon",
        "sub": "100% Himoya / Kafolat",
        "paths": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
        "draw": "shield",
    },
    {
        "id": 21,
        "name": "Kalit / Asbob",
        "sub": "Servis usta haqqi",
        "paths": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
        "draw": "wrench",
    },
    {
        "id": 22,
        "name": "Soat",
        "sub": "Tezkor ta\'mirlash",
        "paths": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
        "draw": "clock",
    },
    {
        "id": 23,
        "name": "Olov",
        "sub": "Qizib ketish / Termo",
        "paths": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
        "draw": "flame",
    },
    {
        "id": 24,
        "name": "CPU Chip",
        "sub": "Ona plata / Protsessor",
        "paths": '<rect width="12" height="12" x="6" y="6" rx="2"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>',
        "draw": "cpu",
    },
    {
        "id": 25,
        "name": "Shleyf / Kabel",
        "sub": "USB ulagichlar",
        "paths": '<path d="M4 12v3a6 6 0 0 0 6 6h4a6 6 0 0 0 6-6v-3"/><rect width="6" height="6" x="1" y="6" rx="1"/><rect width="6" height="6" x="17" y="6" rx="1"/><path d="M4 6V3M20 6V3"/>',
        "draw": "cable",
    },
    {
        "id": 26,
        "name": "Vibratsiya",
        "sub": "Taptic Engine",
        "paths": '<rect width="8" height="14" x="8" y="5" rx="2"/><path d="M3 8a8 8 0 0 0 0 8M21 8a8 8 0 0 1 0 8M1 10a12 12 0 0 0 0 4M23 10a12 12 0 0 1 0 4"/>',
        "draw": "vibrate",
    },
    {
        "id": 27,
        "name": "Medal",
        "sub": "Original sertifikat",
        "paths": '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
        "draw": "medal",
    },
    {
        "id": 28,
        "name": "Chaqmoq",
        "sub": "Tez quvvatlash",
        "paths": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
        "draw": "lightning",
    },
    {
        "id": 29,
        "name": "Yurak",
        "sub": "Ishonchli xizmat",
        "paths": '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>',
        "draw": "heart",
    },
    {
        "id": 30,
        "name": "MagSafe",
        "sub": "Simsiz zaryadlash",
        "paths": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><line x1="12" x2="12" y1="2" y2="4"/><line x1="12" x2="12" y1="20" y2="22"/><line x1="2" x2="4" y1="12" y2="12"/><line x1="20" x2="22" y1="12" y2="12"/>',
        "draw": "magsafe",
    },
]

# 1. Write the clean SVG files (without any numbers in the artwork)
for item in ICONS:
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  {item["paths"]}
</svg>
'''
    bot_path = BOT_ICONS_DIR / f"{item['id']}.svg"
    static_path = STATIC_ICONS_DIR / f"{item['id']}.svg"
    with open(bot_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    with open(static_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

print(f"Generated {len(ICONS)} SVG icons into bot/assets/icons and static/img/icons.")


# 2. Draw high quality Cheatsheet image for Telegram Bot Admin
# 6 columns x 5 rows = 30 cells
IMG_WIDTH = 1200
IMG_HEIGHT = 1100
CARD_W = 180
CARD_H = 170
PAD_X = 16
PAD_Y = 16
HEADER_H = 110

img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), color=(11, 15, 23))
draw = ImageDraw.Draw(img)

# Try loading fonts, fallback to default
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    font_badge = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    font_card_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
    font_card_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
except Exception:
    font_title = font_sub = font_badge = font_card_title = font_card_sub = ImageFont.load_default()

# Header banner
draw.rectangle([(0, 0), (IMG_WIDTH, HEADER_H)], fill=(16, 23, 38))
draw.line([(0, HEADER_H), (IMG_WIDTH, HEADER_H)], fill=(0, 242, 254), width=2)

draw.text((30, 20), "MobiPrice — 30 ta Tayyor Ikonkalar Katalogi", fill=(255, 255, 255), font=font_title)
draw.text(
    (30, 60),
    "Botga kerakli ikonka raqamini yuboring (1 dan 30 gacha). Saytda aynan shu ikonka paydo bo‘ladi!",
    fill=(0, 242, 254),
    font=font_sub
)


def draw_icon_symbol(d, kind, cx, cy):
    c_color = (0, 242, 254)  # Cyan
    w = 2

    if kind == "plane":
        # Airplane shape
        d.polygon([(cx, cy - 20), (cx + 18, cy + 14), (cx, cy + 8), (cx - 18, cy + 14)], outline=c_color, width=w)
        d.line([(cx, cy - 20), (cx, cy + 8)], fill=c_color, width=w)
    elif kind == "star":
        # Star shape
        pts = [
            (cx, cy - 20), (cx + 6, cy - 6), (cx + 20, cy - 5), (cx + 9, cy + 5),
            (cx + 13, cy + 19), (cx, cy + 10), (cx - 13, cy + 19), (cx - 9, cy + 5),
            (cx - 20, cy - 5), (cx - 6, cy - 6)
        ]
        d.polygon(pts, outline=c_color, width=w)
    elif kind == "phone":
        d.rounded_rectangle([(cx - 12, cy - 18), (cx + 12, cy + 18)], radius=4, outline=c_color, width=w)
        d.ellipse([(cx - 2, cy + 12), (cx + 2, cy + 16)], fill=c_color)
    elif kind == "screen":
        d.rounded_rectangle([(cx - 15, cy - 18), (cx + 15, cy + 18)], radius=3, outline=c_color, width=w)
        d.line([(cx - 10, cy - 5), (cx + 2, cy + 1), (cx - 2, cy + 8), (cx + 10, cy + 11)], fill=c_color, width=w)
    elif kind == "battery":
        d.rounded_rectangle([(cx - 16, cy - 10), (cx + 12, cy + 10)], radius=3, outline=c_color, width=w)
        d.line([(cx + 14, cy - 4), (cx + 14, cy + 4)], fill=c_color, width=w + 1)
        # bolt
        d.line([(cx - 4, cy - 6), (cx - 6, cy + 1), (cx + 2, cy + 1), (cx, cy + 7)], fill=(255, 230, 0), width=w)
    elif kind == "camera":
        d.rounded_rectangle([(cx - 18, cy - 11), (cx + 18, cy + 14)], radius=4, outline=c_color, width=w)
        d.polygon([(cx - 7, cy - 11), (cx - 4, cy - 16), (cx + 4, cy - 16), (cx + 7, cy - 11)], outline=c_color, width=w)
        d.ellipse([(cx - 7, cy - 4), (cx + 7, cy + 9)], outline=c_color, width=w)
    elif kind == "speaker":
        d.polygon([(cx - 12, cy - 6), (cx - 6, cy - 6), (cx + 4, cy - 16), (cx + 4, cy + 16), (cx - 6, cy + 6), (cx - 12, cy + 6)], outline=c_color, width=w)
        d.arc([(cx + 5, cy - 9), (cx + 13, cy + 9)], -60, 60, fill=c_color, width=w)
        d.arc([(cx + 8, cy - 15), (cx + 19, cy + 15)], -60, 60, fill=c_color, width=w)
    elif kind == "mic":
        d.rounded_rectangle([(cx - 5, cy - 16), (cx + 5, cy + 4)], radius=4, outline=c_color, width=w)
        d.arc([(cx - 11, cy - 6), (cx + 11, cy + 8)], 0, 180, fill=c_color, width=w)
        d.line([(cx, cy + 8), (cx, cy + 16)], fill=c_color, width=w)
        d.line([(cx - 6, cy + 16), (cx + 6, cy + 16)], fill=c_color, width=w)
    elif kind == "plug":
        d.line([(cx, cy + 6), (cx, cy + 17)], fill=c_color, width=w)
        d.line([(cx - 5, cy - 14), (cx - 5, cy - 6)], fill=c_color, width=w)
        d.line([(cx + 5, cy - 14), (cx + 5, cy - 6)], fill=c_color, width=w)
        d.rounded_rectangle([(cx - 10, cy - 6), (cx + 10, cy + 6)], radius=3, outline=c_color, width=w)
    elif kind == "wifi":
        d.arc([(cx - 18, cy - 14), (cx + 18, cy + 18)], 200, 340, fill=c_color, width=w)
        d.arc([(cx - 12, cy - 8), (cx + 12, cy + 14)], 200, 340, fill=c_color, width=w)
        d.arc([(cx - 6, cy - 2), (cx + 6, cy + 10)], 200, 340, fill=c_color, width=w)
        d.ellipse([(cx - 2, cy + 12), (cx + 2, cy + 16)], fill=c_color)
    elif kind == "bluetooth":
        d.line([(cx - 8, cy - 10), (cx + 8, cy + 6)], fill=c_color, width=w)
        d.line([(cx + 8, cy + 6), (cx, cy + 16)], fill=c_color, width=w)
        d.line([(cx, cy + 16), (cx, cy - 16)], fill=c_color, width=w)
        d.line([(cx, cy - 16), (cx + 8, cy - 6)], fill=c_color, width=w)
        d.line([(cx + 8, cy - 6), (cx - 8, cy + 10)], fill=c_color, width=w)
    elif kind == "sim":
        d.polygon([(cx - 12, cy - 16), (cx + 4, cy - 16), (cx + 12, cy - 8), (cx + 12, cy + 16), (cx - 12, cy + 16)], outline=c_color, width=w)
        d.line([(cx - 6, cy + 4), (cx - 6, cy + 11)], fill=c_color, width=w)
        d.line([(cx, cy + 4), (cx, cy + 11)], fill=c_color, width=w)
        d.line([(cx + 6, cy + 4), (cx + 6, cy + 11)], fill=c_color, width=w)
    elif kind == "faceid":
        d.arc([(cx - 16, cy - 16), (cx - 4, cy - 4)], 180, 270, fill=c_color, width=w)
        d.arc([(cx + 4, cy - 16), (cx + 16, cy - 4)], 270, 360, fill=c_color, width=w)
        d.arc([(cx - 16, cy + 4), (cx - 4, cy + 16)], 90, 180, fill=c_color, width=w)
        d.arc([(cx + 4, cy + 4), (cx + 16, cy + 16)], 0, 90, fill=c_color, width=w)
        d.ellipse([(cx - 6, cy - 4), (cx - 4, cy - 2)], fill=c_color)
        d.ellipse([(cx + 4, cy - 4), (cx + 6, cy - 2)], fill=c_color)
        d.arc([(cx - 5, cy + 2), (cx + 5, cy + 8)], 0, 180, fill=c_color, width=w)
    elif kind == "fingerprint":
        d.arc([(cx - 14, cy - 14), (cx + 14, cy + 14)], 140, 40, fill=c_color, width=w)
        d.arc([(cx - 9, cy - 9), (cx + 9, cy + 9)], 130, 50, fill=c_color, width=w)
        d.arc([(cx - 5, cy - 5), (cx + 5, cy + 5)], 120, 60, fill=c_color, width=w)
    elif kind == "headphones":
        d.arc([(cx - 16, cy - 16), (cx + 16, cy + 16)], 180, 360, fill=c_color, width=w)
        d.rounded_rectangle([(cx - 16, cy), (cx - 10, cy + 14)], radius=3, outline=c_color, width=w)
        d.rounded_rectangle([(cx + 10, cy), (cx + 16, cy + 14)], radius=3, outline=c_color, width=w)
    elif kind == "buttons":
        d.rounded_rectangle([(cx - 10, cy - 16), (cx + 10, cy + 16)], radius=3, outline=c_color, width=w)
        d.line([(cx - 13, cy - 8), (cx - 13, cy - 3)], fill=c_color, width=w + 1)
        d.line([(cx - 13, cy + 2), (cx - 13, cy + 7)], fill=c_color, width=w + 1)
        d.line([(cx + 13, cy - 4), (cx + 13, cy + 4)], fill=c_color, width=w + 1)
    elif kind == "backglass":
        d.rounded_rectangle([(cx - 12, cy - 16), (cx + 12, cy + 16)], radius=4, outline=c_color, width=w)
        d.rounded_rectangle([(cx - 9, cy - 13), (cx - 3, cy - 7)], radius=2, outline=c_color, width=1)
        d.line([(cx + 5, cy - 2), (cx - 5, cy + 8)], fill=c_color, width=w)
    elif kind == "laser":
        d.line([(cx - 15, cy + 15), (cx + 15, cy - 15)], fill=(239, 68, 68), width=w + 1)
        d.ellipse([(cx - 6, cy - 6), (cx + 6, cy + 6)], outline=c_color, width=w)
        d.line([(cx - 10, cy), (cx + 10, cy)], fill=c_color, width=1)
        d.line([(cx, cy - 10), (cx, cy + 10)], fill=c_color, width=1)
    elif kind == "water":
        d.polygon([(cx, cy - 17), (cx + 12, cy + 6), (cx + 6, cy + 14), (cx - 6, cy + 14), (cx - 12, cy + 6)], outline=c_color, width=w)
    elif kind == "shield":
        d.polygon([(cx - 14, cy - 14), (cx + 14, cy - 14), (cx + 14, cy - 2), (cx, cy + 16), (cx - 14, cy - 2)], outline=c_color, width=w)
        d.line([(cx - 6, cy), (cx - 2, cy + 5), (cx + 7, cy - 5)], fill=(16, 185, 129), width=w)
    elif kind == "wrench":
        d.line([(cx - 11, cy + 11), (cx + 6, cy - 6)], fill=c_color, width=w + 2)
        d.arc([(cx + 2, cy - 15), (cx + 16, cy - 1)], 60, 300, fill=c_color, width=w)
    elif kind == "clock":
        d.ellipse([(cx - 15, cy - 15), (cx + 15, cy + 15)], outline=c_color, width=w)
        d.line([(cx, cy), (cx, cy - 8)], fill=c_color, width=w)
        d.line([(cx, cy), (cx + 6, cy + 3)], fill=c_color, width=w)
    elif kind == "flame":
        d.arc([(cx - 12, cy - 8), (cx + 12, cy + 16)], 0, 180, fill=(245, 158, 11), width=w)
        d.polygon([(cx, cy - 16), (cx + 11, cy + 2), (cx, cy + 8), (cx - 11, cy + 2)], outline=(239, 68, 68), width=w)
    elif kind == "cpu":
        d.rounded_rectangle([(cx - 12, cy - 12), (cx + 12, cy + 12)], radius=3, outline=c_color, width=w)
        for offset in [-6, 0, 6]:
            d.line([(cx + offset, cy - 16), (cx + offset, cy - 12)], fill=c_color, width=w)
            d.line([(cx + offset, cy + 12), (cx + offset, cy + 16)], fill=c_color, width=w)
            d.line([(cx - 16, cy + offset), (cx - 12, cy + offset)], fill=c_color, width=w)
            d.line([(cx + 12, cy + offset), (cx + 16, cy + offset)], fill=c_color, width=w)
    elif kind == "cable":
        d.rounded_rectangle([(cx - 15, cy - 7), (cx - 5, cy + 7)], radius=2, outline=c_color, width=w)
        d.rounded_rectangle([(cx + 5, cy - 7), (cx + 15, cy + 7)], radius=2, outline=c_color, width=w)
        d.arc([(cx - 8, cy - 12), (cx + 8, cy + 15)], 0, 180, fill=c_color, width=w)
    elif kind == "vibrate":
        d.rounded_rectangle([(cx - 8, cy - 12), (cx + 8, cy + 12)], radius=3, outline=c_color, width=w)
        d.arc([(cx - 16, cy - 8), (cx - 10, cy + 8)], 90, 270, fill=c_color, width=w)
        d.arc([(cx + 10, cy - 8), (cx + 16, cy + 8)], 270, 90, fill=c_color, width=w)
    elif kind == "medal":
        d.ellipse([(cx - 10, cy - 14), (cx + 10, cy + 6)], outline=c_color, width=w)
        d.polygon([(cx - 5, cy + 4), (cx - 9, cy + 16), (cx, cy + 12), (cx + 9, cy + 16), (cx + 5, cy + 4)], outline=c_color, width=w)
    elif kind == "lightning":
        d.polygon([(cx + 2, cy - 17), (cx - 11, cy + 1), (cx, cy + 1), (cx - 2, cy + 17), (cx + 11, cy - 1), (cx, cy - 1)], outline=(255, 230, 0), width=w)
    elif kind == "heart":
        d.polygon([(cx, cy + 14), (cx - 14, cy), (cx - 14, cy - 8), (cx - 6, cy - 14), (cx, cy - 6), (cx + 6, cy - 14), (cx + 14, cy - 8), (cx + 14, cy)], outline=(236, 72, 153), width=w)
    elif kind == "magsafe":
        d.ellipse([(cx - 15, cy - 15), (cx + 15, cy + 15)], outline=c_color, width=w)
        d.ellipse([(cx - 7, cy - 7), (cx + 7, cy + 7)], outline=c_color, width=1)
        d.line([(cx, cy - 18), (cx, cy - 15)], fill=c_color, width=w)
        d.line([(cx, cy + 15), (cx, cy + 18)], fill=c_color, width=w)


# Render 6 columns x 5 rows
COLS = 6
ROWS = 5
start_x = (IMG_WIDTH - (COLS * CARD_W + (COLS - 1) * PAD_X)) // 2
start_y = HEADER_H + 20

for idx, item in enumerate(ICONS):
    col = idx % COLS
    row = idx // COLS
    x1 = start_x + col * (CARD_W + PAD_X)
    y1 = start_y + row * (CARD_H + PAD_Y)
    x2 = x1 + CARD_W
    y2 = y1 + CARD_H

    # Card background & border
    draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=12, fill=(18, 24, 38), outline=(32, 44, 68), width=1)

    # Number badge at top left (Prominent!)
    badge_w = 46
    badge_h = 24
    draw.rounded_rectangle([(x1 + 8, y1 + 8), (x1 + 8 + badge_w, y1 + 8 + badge_h)], radius=6, fill=(0, 242, 254))
    badge_text = f"#{item['id']}"
    draw.text((x1 + 14, y1 + 11), badge_text, fill=(8, 11, 17), font=font_badge)

    # Icon symbol in center
    icon_cx = (x1 + x2) // 2
    icon_cy = y1 + 75
    draw_icon_symbol(draw, item["draw"], icon_cx, icon_cy)

    # Title & Subtitle at bottom
    title_text = item["name"]
    sub_text = item["sub"]
    draw.text((x1 + 10, y2 - 42), title_text, fill=(255, 255, 255), font=font_card_title)
    draw.text((x1 + 10, y2 - 24), sub_text, fill=(148, 163, 184), font=font_card_sub)

# Save image
img.save(CHEATSHEET_PATH, format="PNG", optimize=True)
print(f"Icons cheatsheet saved to: {CHEATSHEET_PATH}")
