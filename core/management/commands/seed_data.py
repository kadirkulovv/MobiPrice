from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Brand, RepairFAQ, Review


class Command(BaseCommand):
    help = "Populate initial essential data: Superuser, Brands, FAQs, and Reviews"

    def handle(self, *args, **options):
        self.stdout.write("Initializing base data for MobiPrice...")

        # 1. Superuser
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@mobiprice.uz", "admin123")
            self.stdout.write(self.style.SUCCESS("Superuser: admin / admin123"))

        # 2. Brands (Roots of the hierarchy)
        Brand.objects.get_or_create(name="Apple", defaults={"slug": "apple", "order": 1})
        Brand.objects.get_or_create(name="Samsung", defaults={"slug": "samsung", "order": 2})
        Brand.objects.get_or_create(name="Xiaomi (Redmi)", defaults={"slug": "xiaomi", "order": 3})
        Brand.objects.get_or_create(name="Honor", defaults={"slug": "honor", "order": 4})

        # 3. FAQs (Site expert content)
        RepairFAQ.objects.get_or_create(
            question="Nega batareya shishib ketadi va bu xavflimi?",
            defaults={
                "question_ru": "Почему вздувается аккумулятор и опасно ли это?",
                "question_en": "Why does the battery swell and is it dangerous?",
                "answer": "Batareya asosan arzon va nooriginal zaryadlash moslamalari, kuchlanish tebranishi yoki zaryad paytida telefonni qizdirib ishlatish oqibatida gaz to‘planishidan shishadi. Bu xavfli bo‘lib, ekranni sindirishi yoki yonish xavfini keltirib chiqarishi mumkin.",
                "answer_ru": "Аккумулятор вздувается из-за некачественных зарядок, перепадов напряжения или перегрева. Это опасно: вздутая батарея может выдавить экран.",
                "order": 1
            }
        )
        RepairFAQ.objects.get_or_create(
            question="Nega original ekran qimmat, kopiyasi esa 2-3 barobar arzon?",
            defaults={
                "question_ru": "Почему оригинальный экран дорогой, а копия дешевле?",
                "question_en": "Why is an original screen expensive while copies are cheaper?",
                "answer": "Original ekranda millionlab piksellardan iborat Super Retina XDR yoki Dynamic AMOLED matritsa, 120Hz ProMotion va TrueTone datchiklari zavod standartida ishlaydi. Kopiyalarda oddiyroq matritsa qo‘llaniladi.",
                "answer_ru": "Оригинал имеет фирменную AMOLED/Retina матрицу, 120Hz и TrueTone. В копиях используются более простые компоненты.",
                "order": 2
            }
        )

        # 4. Verified Reviews
        Review.objects.get_or_create(
            client_name="Shoxrux Bekmurodov",
            device_model="iPhone 15 Pro Max",
            service_type="Orqa oyna almashtirish",
            defaults={
                "rating": 5,
                "comment": "Orqa oynasi singanda lazer texnologiyasi bilan telefonni ochmasdan 45 minutda zavoddagidek tiklab berishdi. Narxi ham juda qulay!",
                "is_verified": True
            }
        )

        self.stdout.write(self.style.SUCCESS("Base brands and reviews successfully prepared! Models, Phones, Issues, and Pricing can now be managed directly via Telegram Bot."))
