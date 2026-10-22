from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Brand, DeviceModel, PartCategory, PartOption, RepairFAQ, Review


class Command(BaseCommand):
    help = "Populate initial seed data for demo"

    def handle(self, *args, **options):
        self.stdout.write("Seeding data for MobiPrice...")

        # 1. Superuser
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@mobiprice.uz", "admin123")
            self.stdout.write(self.style.SUCCESS("Superuser created: admin / admin123"))

        # 2. Brands
        apple, _ = Brand.objects.get_or_create(name="Apple", defaults={"slug": "apple", "order": 1})
        samsung, _ = Brand.objects.get_or_create(name="Samsung", defaults={"slug": "samsung", "order": 2})
        xiaomi, _ = Brand.objects.get_or_create(name="Xiaomi (Redmi)", defaults={"slug": "xiaomi", "order": 3})
        honor, _ = Brand.objects.get_or_create(name="Honor", defaults={"slug": "honor", "order": 4})

        # 3. Models
        ip16pm, _ = DeviceModel.objects.get_or_create(
            brand=apple,
            name="iPhone 16 Pro Max",
            defaults={"slug": "iphone-16-pro-max", "release_year": 2024, "is_popular": True, "order": 1}
        )
        ip15p, _ = DeviceModel.objects.get_or_create(
            brand=apple,
            name="iPhone 15 Pro",
            defaults={"slug": "iphone-15-pro", "release_year": 2023, "is_popular": True, "order": 2}
        )
        s24u, _ = DeviceModel.objects.get_or_create(
            brand=samsung,
            name="Galaxy S24 Ultra",
            defaults={"slug": "galaxy-s24-ultra", "release_year": 2024, "is_popular": True, "order": 3}
        )
        redmi13, _ = DeviceModel.objects.get_or_create(
            brand=xiaomi,
            name="Redmi Note 13 Pro",
            defaults={"slug": "redmi-note-13-pro", "release_year": 2024, "is_popular": True, "order": 4}
        )

        # 4. Categories
        cat_screen, _ = PartCategory.objects.get_or_create(
            code="screen",
            defaults={
                "name": "Ekran (Displey)",
                "name_ru": "Экран (Дисплей)",
                "name_en": "Screen (Display)",
                "order": 1
            }
        )
        cat_back, _ = PartCategory.objects.get_or_create(
            code="back_glass",
            defaults={
                "name": "Orqa shisha (Krishka)",
                "name_ru": "Заднее стекло (Крышка)",
                "name_en": "Back Glass (Cover)",
                "order": 2
            }
        )
        cat_battery, _ = PartCategory.objects.get_or_create(
            code="battery",
            defaults={
                "name": "Batareya (Akkumulyator)",
                "name_ru": "Аккумулятор (Батарея)",
                "name_en": "Battery Replacement",
                "order": 3
            }
        )
        cat_camera, _ = PartCategory.objects.get_or_create(
            code="camera_glass",
            defaults={
                "name": "Kamera oynasi",
                "name_ru": "Стекло камеры",
                "name_en": "Camera Glass",
                "order": 4
            }
        )

        # 5. Part Options for iPhone 16 Pro Max
        # Screen options
        PartOption.objects.get_or_create(
            device_model=ip16pm,
            category=cat_screen,
            quality_type="original_service_pack",
            defaults={
                "title": "Original Zavod Service Pack (100% Original)",
                "title_ru": "Оригинальный заводской Service Pack (100% Original)",
                "title_en": "Original Factory Service Pack (100% Genuine)",
                "part_price_uzs": 2900000,
                "service_fee_uzs": 150000,
                "price_usd": 240,
                "warranty": "6 oy to‘liq kafolat",
                "warranty_ru": "6 месяцев полной гарантии",
                "warranty_en": "6 months full warranty",
                "repair_time": "40 daqiqa",
                "badge": "Tavsiya etiladi",
                "description": "100% Zavodskoy yangi original modul. TrueTone datchigi to‘liq o‘tadi, 120Hz ProMotion ravonligi, quyoshda yorug‘ligi va ranglar tabiiyligi zavod holatidek saqlanadi.",
                "description_ru": "100% новый заводской оригинальный модуль. Полная поддержка TrueTone, 120Hz ProMotion, максимальная яркость и цветопередача как с завода.",
                "features": ["100% Zavodskoy Original", "TrueTone o‘tadi", "120Hz ProMotion qo‘llab-quvvatlaydi", "Suvdan himoya germetikasi tiklanadi", "6 oy kafolat"]
            }
        )
        PartOption.objects.get_or_create(
            device_model=ip16pm,
            category=cat_screen,
            quality_type="oled_gx",
            defaults={
                "title": "OLED GX Premium Kopiya (Originalga eng yaqin)",
                "title_ru": "OLED GX Премиум копия (Максимально к оригиналу)",
                "title_en": "OLED GX Premium Copy (Closest to Original)",
                "part_price_uzs": 1500000,
                "service_fee_uzs": 100000,
                "price_usd": 125,
                "warranty": "3 oy kafolat",
                "warranty_ru": "3 месяца гарантии",
                "warranty_en": "3 months warranty",
                "repair_time": "35 daqiqa",
                "badge": "Optimal narx",
                "description": "Sifatli Hard/Soft OLED matritsa. Ranglar to‘yingan, sensor sezgirligi juda yuqori. Byudjetni tejamoqchi bo‘lganlar uchun eng zo‘r muqobil.",
                "description_ru": "Качественная OLED матрица. Насыщенные цвета, высокая чувствительность сенсора. Лучший выбор в соотношении цена/качество.",
                "features": ["Haqiqiy OLED matritsa", "Sensor sezgirligi a'lo darajada", "TrueTone o‘tkaziladi", "3 oy kafolat"]
            }
        )
        PartOption.objects.get_or_create(
            device_model=ip16pm,
            category=cat_screen,
            quality_type="tft_incell",
            defaults={
                "title": "Incell / TFT Byudjet Kopiya",
                "title_ru": "Incell / TFT Бюджетная копия",
                "title_en": "Incell / TFT Budget Copy",
                "part_price_uzs": 850000,
                "service_fee_uzs": 100000,
                "price_usd": 75,
                "warranty": "1 oy kafolat",
                "warranty_ru": "1 месяц гарантии",
                "warranty_en": "1 month warranty",
                "repair_time": "30 daqiqa",
                "badge": "Eng arzoni",
                "description": "Hamyonbop TFT/Incell texnologiyasi. Ekran romi originaldan biroz qalinroq bo‘lishi mumkin, lekin to‘liq ishlaydi.",
                "description_ru": "Доступный вариант на технологии Incell. Рамки могут быть чуть шире оригинала, работает стабильно.",
                "features": ["Eng hamyonbop narx", "Tezkor ta'mirlash", "1 oy kafolat"]
            }
        )

        # Back glass options
        PartOption.objects.get_or_create(
            device_model=ip16pm,
            category=cat_back,
            quality_type="original_service_pack",
            defaults={
                "title": "Original Zavod Orqa Shisha (Titanium ramka bilan)",
                "title_ru": "Оригинальное заводское заднее стекло",
                "title_en": "Original Factory Back Glass",
                "part_price_uzs": 950000,
                "service_fee_uzs": 150000,
                "price_usd": 85,
                "warranty": "6 oy kafolat",
                "repair_time": "1 soat (Lazer usuli)",
                "badge": "Tavsiya etiladi",
                "description": "Maxsus lazer dastgohi yordamida telefonni ochmasdan orqa shishani almashtirish. Zavod ranglari va magniy-titanium jilosi bilan 100% bir xil.",
                "features": ["Lazer yordamida xavfsiz tozalash", "MagSafe simsiz zaryadka buzilmaydi", "Zavodskoy germetika"]
            }
        )
        PartOption.objects.get_or_create(
            device_model=ip16pm,
            category=cat_back,
            quality_type="oled_gx",
            defaults={
                "title": "Sifatli Dublikat Orqa Oyna (Katta teshikli)",
                "title_ru": "Качественное дубликат стекло",
                "title_en": "High Quality Duplicate Back Glass",
                "part_price_uzs": 450000,
                "service_fee_uzs": 100000,
                "price_usd": 45,
                "warranty": "1 oy kafolat",
                "repair_time": "45 daqiqa",
                "badge": "Hamyonbop",
                "description": "Zarbalarga chidamli sifatli dublikat shisha. Tashqi ko‘rinishi originaldan deyarli farq qilmaydi.",
                "features": ["Arzon va sifatli", "MagSafe ishlaydi", "1 oy kafolat"]
            }
        )

        # Battery options
        PartOption.objects.get_or_create(
            device_model=ip16pm,
            category=cat_battery,
            quality_type="original_service_pack",
            defaults={
                "title": "Original Zavod Batareya (BMS chip ko'chirish bilan)",
                "title_ru": "Оригинальный заводской аккумулятор с переносом BMS",
                "title_en": "Original Factory Battery with BMS Transfer",
                "part_price_uzs": 800000,
                "service_fee_uzs": 120000,
                "price_usd": 70,
                "warranty": "6 oy kafolat",
                "repair_time": "45 daqiqa",
                "badge": "100% Holat",
                "description": "Zavod batareyasi. Eski batareyangizning mikrosxemasi (BMS) yangisiga lehimlanadi, natijada sozlamalarda 'Noma'lum qism' degan xatolik chiqmaydi va Batareya sog'lig'i 100% ko'rinadi.",
                "features": ["Xatolik xabari chiqmaydi", "100% Battery Health ko'rsatadi", "Zavod quvvati", "6 oy kafolat"]
            }
        )

        # 6. Part Options for Galaxy S24 Ultra
        PartOption.objects.get_or_create(
            device_model=s24u,
            category=cat_screen,
            quality_type="original_service_pack",
            defaults={
                "title": "Samsung Original Service Pack (Ramkasi bilan)",
                "title_ru": "Samsung Оригинальный Service Pack (в сборе с рамкой)",
                "title_en": "Samsung Genuine Service Pack Display with Frame",
                "part_price_uzs": 2800000,
                "service_fee_uzs": 150000,
                "price_usd": 230,
                "warranty": "6 oy kafolat",
                "repair_time": "30 daqiqa",
                "badge": "Zavodskoy",
                "description": "Samsung rasmiy servis moduli. Dynamic AMOLED 2X, 2600 nit yorug'lik, Gorilla Armor yaltiramaydigan qoplama.",
                "features": ["100% Original Samsung", "Titanium ramka bilan yig'ilgan", "Barmoq izi ultratovush sensori ishlaydi"]
            }
        )

        # 7. FAQs
        RepairFAQ.objects.get_or_create(
            question="Nega batareya shishib ketadi va bu xavflimi?",
            defaults={
                "question_ru": "Почему вздувается аккумулятор и опасно ли это?",
                "question_en": "Why does the battery swell and is it dangerous?",
                "category": cat_battery,
                "answer": "Batareya asosan arzon va nooriginal zaryadlash moslamalari, mashina zaryadkasi (kuchsiz tok tebranishi) yoki telefonni zaryadda qoldirib og'ir o'yinlar o'ynash oqibatida qizib, gaz to'planishi tufayli shishadi. Bu juda xavfli, chunki shishgan batareya ekranni ichkaridan itarib sindirishi yoki yonib ketish xavfini tug'dirishi mumkin. Zudlik bilan almashtirish tavsiya etiladi.",
                "answer_ru": "Аккумулятор вздувается из-за некачественных зарядок, перепадов напряжения в авто или перегрева при зарядке во время игр. Это опасно: вздутая батарея может выдавить экран или воспламениться.",
                "order": 1
            }
        )
        RepairFAQ.objects.get_or_create(
            question="Nega original ekran qimmat, kopiyasi esa 2-3 barobar arzon?",
            defaults={
                "question_ru": "Почему оригинальный экран дорогой, а копия дешевле в 2-3 раза?",
                "question_en": "Why is an original screen expensive while copies are cheaper?",
                "category": cat_screen,
                "answer": "Original ekranda millionlab piksellardan iborat Super Retina XDR yoki Dynamic AMOLED matritsa, 120Hz chastota, quyoshda ko'rinish va TrueTone datchigi bo'ladi. Arzon kopiyalar esa oddiyroq texnologiyada tayyorlanadi, ularda qora rang chuqur qora emas, sensor javob berish tezligi biroz sekinroq bo'ladi. Bizning servisimizda siz har ikkala variantni solishtirib ko'rishingiz mumkin.",
                "answer_ru": "Оригинал имеет фирменную AMOLED/Retina матрицу, 120Hz, поддержку TrueTone и максимальную яркость. В копиях используются более простые материалы.",
                "order": 2
            }
        )
        RepairFAQ.objects.get_or_create(
            question="Ta'mirlash qancha vaqt oladi? Telefonimni qoldirib ketishim shartmi?",
            defaults={
                "question_ru": "Сколько длится ремонт? Обязательно ли оставлять телефон?",
                "question_en": "How long does repair take? Do I have to leave my phone?",
                "answer": "Telefonni qoldirib ketish shart emas! Ekranni yoki orqa oynani almashtirish 30 daqiqadan 1 soatgacha vaqt oladi. Siz qulay kutish zalimizda kofe ichib, ustaning ish jarayonini kuzatib turishingiz mumkin.",
                "answer_ru": "Ремонт занимает от 30 минут до 1 часа. Вы можете подождать в зоне ожидания и наблюдать за процессом.",
                "order": 3
            }
        )

        # 8. Reviews
        Review.objects.get_or_create(
            client_name="Shoxrux Bekmurodov",
            device_model="iPhone 16 Pro Max",
            service_type="Orqa oyna almashtirish",
            defaults={
                "rating": 5,
                "comment": "Orqa oynasini singdirib qo'yib rosa siqilgandim. Malikadagilar telefonni butunlay ochish kerak dedi, MobiPrice esa maxsus lazer bilan telefonni ochmasdan 45 minutda zavoddagidek qilib berdi. Narxi ham bozorga qaraganda ancha arzon tushdi!",
                "is_verified": True
            }
        )
        Review.objects.get_or_create(
            client_name="Azizbek Toirov",
            device_model="Galaxy S24 Ultra",
            service_type="Original displey qo'yish",
            defaults={
                "rating": 5,
                "comment": "Saytdan oldindan narxini ko'rib bordim. Qancha yozilgan bo'lsa, xuddi shunday narx olishdi, ustiga ortiqcha tiyin qo'shishmadi. Sifatiga 6 oy kafolat berishdi.",
                "is_verified": True
            }
        )

        self.stdout.write(self.style.SUCCESS("All seed data successfully loaded into MobiPrice!"))
