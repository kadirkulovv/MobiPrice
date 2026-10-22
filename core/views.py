import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.utils.translation import get_language
from .models import Brand, DeviceModel, PartCategory, PartOption, RepairFAQ, Review, ServiceOrder


UI_TRANSLATIONS = {
    'uz': {
        'hero_badge': '⚡️ Shaffof narxlar & 100% Kafolat',
        'hero_title': "Telefoningiz buzildimi? <br>Bozorga bormasdan <span>aniq narxini</span> 10 soniyada bilib oling!",
        'hero_desc': "Bozor kezib sarson bo‘lmang. iPhone, Samsung, Xiaomi original va sifatli dublikat ehtiyot qismlari narxlari, usta haqqi va kafolati bilan tanishing.",
        'search_placeholder': "Telefon modelingizni yozing (masalan: 16 Pro Max, S24 Ultra...)",
        'step_1_title': "Brend",
        'step_2_title': "Model",
        'step_3_title': "Muammo",
        'step_4_title': "Solishtirish",
        'step_1_head': "1-Qadam: Telefoningiz brendini tanlang",
        'step_2_head': "2-Qadam: Modelni tanlang",
        'step_2_sub': "Quyidagi modellardan birini bosing:",
        'step_3_prompt': "Qurilmangizning qaysi qismi shikastlangan yoki almashtirish talab qilinadi?",
        'back_step_1': "← Brendni o'zgartirish",
        'back_step_2': "← Modelni o'zgartirish",
        'back_step_3': "← Detalni o'zgartirish",
        'compare_prompt': "Narxlarni solishtirish →",
        'choose_prompt': "Tanlash →",
        'ba_badge': "iPhone 15 Pro Max — White Titanium",
        'ba_title': "Bizning ishlarimiz: <span>Oldin va Keyin</span>",
        'ba_sub': "Orqa oynasi singan iPhone 15 Pro Max'ni ochmasdan lazer texnologiyasi bilan 100% tiklash jarayoni",
        'ba_before_badge': "Oldin: Singan holati",
        'ba_after_badge': "Keyin: 100% Zavod holati",
        'faq_title': "Ekspert maslahati: <span>Eng ko'p beriladigan savollar</span>",
        'faq_sub': "Nega batareya shishadi? Nega original qimmat? Ustalarimiz ochiq tushuntirish beradi.",
        'reviews_title': "Mijozlarimiz <span>fikrlari</span>",
        'reviews_sub': "Shaffof narxlar va tezkor servisimizdan foydalangan mijozlar sharhlari",
        'modal_title': "Buyurtmani tasdiqlash",
        'name_label': "Ismingiz *",
        'phone_label': "Telefon raqamingiz *",
        'format_label': "Xizmat formati",
        'format_opt_1': "Servis markaziga boraman (30 daqiqada)",
        'format_opt_2': "Usta chaqirish (Manzilga usta boradi)",
        'format_opt_3': "Kuryer orqali yuborish (Bepul olib ketish)",
        'btn_submit': "Tasdiqlash va Yuborish",
    },
    'ru': {
        'hero_badge': '⚡️ Прозрачные цены и 100% Гарантия',
        'hero_title': "Сломался телефон? <br>Узнайте <span>точную цену</span> ремонта за 10 секунд без поездки на базар!",
        'hero_desc': "Не тратьте время на поездки на рынок. Узнайте цены на оригинальные запчасти и качественные копии для iPhone, Samsung, Xiaomi с гарантией.",
        'search_placeholder': "Введите модель телефона (например: 16 Pro Max, S24 Ultra...)",
        'step_1_title': "Бренд",
        'step_2_title': "Модель",
        'step_3_title': "Деталь",
        'step_4_title': "Сравнение",
        'step_1_head': "Шаг 1: Выберите бренд вашего телефона",
        'step_2_head': "Шаг 2: Выберите модель",
        'step_2_sub': "Выберите одну из моделей ниже:",
        'step_3_prompt': "Какая часть вашего устройства повреждена или требует замены?",
        'back_step_1': "← Изменить бренд",
        'back_step_2': "← Изменить модель",
        'back_step_3': "← Изменить деталь",
        'compare_prompt': "Сравнить цены →",
        'choose_prompt': "Выбрать →",
        'ba_badge': "iPhone 15 Pro Max — White Titanium",
        'ba_title': "Наши работы: <span>До и После</span>",
        'ba_sub': "Лазерная замена разбитого заднего стекла iPhone 15 Pro Max без вскрытия корпуса",
        'ba_before_badge': "До: Разбитое стекло",
        'ba_after_badge': "После: 100% Заводской вид",
        'faq_title': "Советы экспертов: <span>Частые вопросы</span>",
        'faq_sub': "Почему вздувается батарея? Почему оригинал дороже? Мастера дают открытый ответ.",
        'reviews_title': "Отзывы <span>наших клиентов</span>",
        'reviews_sub': "Отзывы клиентов, выбравших прозрачные цены и быстрый ремонт",
        'modal_title': "Подтверждение заявки",
        'name_label': "Ваше имя *",
        'phone_label': "Номер телефона *",
        'format_label': "Формат услуги",
        'format_opt_1': "Приеду в сервис (ремонт за 30 минут)",
        'format_opt_2': "Вызов мастера (мастер приедет по адресу)",
        'format_opt_3': "Курьерская доставка (заберем бесплатно)",
        'btn_submit': "Подтвердить и отправить",
    },
    'en': {
        'hero_badge': '⚡️ Transparent Pricing & 100% Warranty',
        'hero_title': "Broken phone? <br>Find out the <span>exact price</span> in 10 seconds without going to the market!",
        'hero_desc': "Don't waste time visiting markets. Check original and high-quality replacement parts pricing for iPhone, Samsung, Xiaomi with full warranty.",
        'search_placeholder': "Type your phone model (e.g. 16 Pro Max, S24 Ultra...)",
        'step_1_title': "Brand",
        'step_2_title': "Model",
        'step_3_title': "Issue",
        'step_4_title': "Compare",
        'step_1_head': "Step 1: Select your phone brand",
        'step_2_head': "Step 2: Select your model",
        'step_2_sub': "Select one of the models below:",
        'step_3_prompt': "Which part of your device is damaged or needs replacement?",
        'back_step_1': "← Change brand",
        'back_step_2': "← Change model",
        'back_step_3': "← Change part",
        'compare_prompt': "Compare Prices →",
        'choose_prompt': "Select →",
        'ba_badge': "iPhone 15 Pro Max — White Titanium",
        'ba_title': "Our Work: <span>Before & After</span>",
        'ba_sub': "Laser rear glass restoration on iPhone 15 Pro Max without disassembling the device",
        'ba_before_badge': "Before: Shattered glass",
        'ba_after_badge': "After: 100% Factory pristine",
        'faq_title': "Expert Advice: <span>Frequently Asked Questions</span>",
        'faq_sub': "Why do batteries swell? Why are genuine screens costly? Our technicians explain.",
        'reviews_title': "Customer <span>Reviews</span>",
        'reviews_sub': "Verified customer feedback about our transparent pricing and rapid service",
        'modal_title': "Confirm Request",
        'name_label': "Your Name *",
        'phone_label': "Phone Number *",
        'format_label': "Service Format",
        'format_opt_1': "Visit service center (ready in 30 mins)",
        'format_opt_2': "Call a technician (on-site repair)",
        'format_opt_3': "Free courier pickup and return",
        'btn_submit': "Confirm and Send",
    }
}


def index_view(request):
    current_lang = getattr(request, 'LANGUAGE_CODE', None) or get_language() or 'uz'
    if current_lang not in ('uz', 'ru', 'en'):
        current_lang = 'uz'

    brands = Brand.objects.filter(is_active=True).order_by('order', 'name')
    categories = PartCategory.objects.all().order_by('order')
    faqs = RepairFAQ.objects.all().order_by('order')
    reviews = Review.objects.filter(is_verified=True).order_by('-created_at')[:6]

    t = UI_TRANSLATIONS.get(current_lang, UI_TRANSLATIONS['uz'])

    context = {
        'brands': brands,
        'categories': categories,
        'faqs': faqs,
        'reviews': reviews,
        'current_lang': current_lang,
        't': t,
    }
    return render(request, 'index.html', context)


@require_GET
def api_models_by_brand(request, brand_id):
    models_qs = DeviceModel.objects.filter(brand_id=brand_id).order_by('order', 'name')
    data = []
    for m in models_qs:
        image_url = m.image.url if m.image else f"/static/img/models/{m.slug.replace('-', '_')}.jpg"
        data.append({
            'id': m.id,
            'name': m.name,
            'slug': m.slug,
            'model_code': m.model_code,
            'release_year': m.release_year,
            'is_popular': m.is_popular,
            'image_url': image_url,
        })
    return JsonResponse({'models': data})


@require_GET
def api_search_models(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'models': []})

    models_qs = DeviceModel.objects.filter(name__icontains=query).select_related('brand').order_by('order')[:10]
    data = []
    for m in models_qs:
        image_url = m.image.url if m.image else f"/static/img/models/{m.slug.replace('-', '_')}.jpg"
        data.append({
            'id': m.id,
            'name': m.name,
            'brand_id': m.brand.id,
            'brand_name': m.brand.name,
            'slug': m.slug,
            'image_url': image_url,
        })
    return JsonResponse({'models': data})


@require_GET
def api_part_options(request):
    model_id = request.GET.get('model_id')
    category_id = request.GET.get('category_id')

    if not model_id or not category_id:
        return JsonResponse({'error': 'model_id and category_id are required'}, status=400)

    lang = request.GET.get('lang') or request.COOKIES.get('django_language') or get_language() or 'uz'
    options_qs = PartOption.objects.filter(
        device_model_id=model_id,
        category_id=category_id
    ).order_by('-quality_type')

    data = []
    for opt in options_qs:
        title = opt.title
        desc = opt.description
        warranty = opt.warranty

        if lang == 'ru':
            title = opt.title_ru or opt.title
            desc = opt.description_ru or opt.description
            warranty = opt.warranty_ru or opt.warranty
        elif lang == 'en':
            title = opt.title_en or opt.title
            desc = opt.description_en or opt.description
            warranty = opt.warranty_en or opt.warranty

        data.append({
            'id': opt.id,
            'quality_type': opt.quality_type,
            'quality_display': opt.get_quality_type_display(),
            'title': title,
            'part_price_uzs': int(opt.part_price_uzs),
            'service_fee_uzs': int(opt.service_fee_uzs),
            'total_price_uzs': int(opt.total_price_uzs),
            'price_usd': int(opt.price_usd),
            'warranty': warranty,
            'repair_time': opt.repair_time,
            'badge': opt.badge,
            'description': desc,
            'features': opt.features if isinstance(opt.features, list) else [],
            'stock_status': opt.stock_status,
            'stock_display': opt.get_stock_status_display(),
        })

    return JsonResponse({'options': data})


@require_POST
def api_submit_order(request):
    try:
        data = json.loads(request.body)
        client_name = data.get('client_name', '').strip()
        phone_number = data.get('phone_number', '').strip()
        model_id = data.get('model_id')
        option_id = data.get('option_id')
        service_type = data.get('service_type', 'in_service')

        if not client_name or not phone_number:
            return JsonResponse({'success': False, 'error': "Ism va telefon raqami kiritilishi shart!"}, status=400)

        order = ServiceOrder.objects.create(
            client_name=client_name,
            phone_number=phone_number,
            device_model_id=model_id if model_id else None,
            part_option_id=option_id if option_id else None,
            service_type=service_type,
        )

        # Telegram notification if configured
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_ADMIN_CHAT_ID:
            try:
                model_str = order.device_model.name if order.device_model else "Ko'rsatilmagan"
                part_str = order.part_option.title if order.part_option else "Umumiy konsultatsiya"
                price_str = f"{order.part_option.total_price_uzs:,} so'm" if order.part_option else "-"
                
                text = (
                    f"🚨 <b>YANGI BUYURTMA! #{order.order_id}</b>\n\n"
                    f"👤 <b>Mijoz:</b> {client_name}\n"
                    f"📞 <b>Telefon:</b> {phone_number}\n"
                    f"📱 <b>Model:</b> {model_str}\n"
                    f"🔧 <b>Xizmat:</b> {part_str}\n"
                    f"💵 <b>Narx:</b> {price_str}\n"
                    f"📍 <b>Format:</b> {order.get_service_type_display()}"
                )
                url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(url, json={
                    'chat_id': settings.TELEGRAM_ADMIN_CHAT_ID,
                    'text': text,
                    'parse_mode': 'HTML'
                }, timeout=5)
            except Exception as e:
                pass  # Do not block client response if Telegram fails

        return JsonResponse({
            'success': True,
            'order_id': order.order_id,
            'message': "Arizangiz muvaffaqiyatli qabul qilindi! Tez orada mutaxassisimiz siz bilan bog‘lanadi."
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
