import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.utils.translation import get_language
from .models import (
    Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison,
    RepairFAQ, Review, ServiceOrder
)


UI_TRANSLATIONS = {
    'uz': {
        'hero_badge': '⚡️ Shaffof narxlar & 100% Kafolat',
        'hero_title': "Telefoningiz buzildimi? <br>Bozorga bormasdan <span>aniq narxini</span> 10 soniyada bilib oling!",
        'hero_desc': "Bozor kezib sarson bo‘lmang. iPhone, Samsung, Xiaomi original va sifatli dublikat ehtiyot qismlari narxlari, usta haqqi va kafolati bilan tanishing.",
        'search_placeholder': "Telefon modelingizni yozing (masalan: 16 Pro Max, S24 Ultra...)",
        'step_1_title': "Brend",
        'step_2_title': "Model",
        'step_3_title': "Telefon",
        'step_4_title': "Muammo",
        'step_5_title': "Solishtirish",
        'step_1_head': "1-Qadam: Telefoningiz brendini tanlang",
        'step_2_head': "2-Qadam: Model seriyasini tanlang",
        'step_2_sub': "Quyidagi seriyalardan birini tanlang:",
        'step_3_head': "3-Qadam: Telefoningizni tanlang",
        'step_3_sub': "Aniq modelingiz ustiga bosing:",
        'step_4_head': "4-Qadam: Shikastlangan qismni tanlang",
        'step_4_prompt': "Qurilmangizning qaysi qismi ta'mirlash yoki almashtirishni talab qiladi?",
        'step_5_head': "5-Qadam: Narxlarni solishtirish",
        'back_step_1': "← Brendni o'zgartirish",
        'back_step_2': "← Model seriyasini o'zgartirish",
        'back_step_3': "← Telefonni o'zgartirish",
        'back_step_4': "← Muammoni o'zgartirish",
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
        'step_3_title': "Телефон",
        'step_4_title': "Деталь",
        'step_5_title': "Сравнение",
        'step_1_head': "Шаг 1: Выберите бренд вашего телефона",
        'step_2_head': "Шаг 2: Выберите серию модели",
        'step_2_sub': "Выберите нужную серию ниже:",
        'step_3_head': "Шаг 3: Выберите телефон",
        'step_3_sub': "Нажмите на точную модель телефона:",
        'step_4_head': "Шаг 4: Выберите поврежденную деталь",
        'step_4_prompt': "Какая часть вашего устройства требует замены?",
        'step_5_head': "Шаг 5: Сравнение цен и качества",
        'back_step_1': "← Изменить бренд",
        'back_step_2': "← Изменить серию",
        'back_step_3': "← Изменить телефон",
        'back_step_4': "← Изменить деталь",
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
        'step_3_title': "Phone",
        'step_4_title': "Issue",
        'step_5_title': "Compare",
        'step_1_head': "Step 1: Select your phone brand",
        'step_2_head': "Step 2: Select model series",
        'step_2_sub': "Choose one of the model series below:",
        'step_3_head': "Step 3: Select your phone",
        'step_3_sub': "Click on your exact device:",
        'step_4_head': "Step 4: Select damaged part",
        'step_4_prompt': "Which part of your device needs repair or replacement?",
        'step_5_head': "Step 5: Price & Quality Comparison",
        'back_step_1': "← Change brand",
        'back_step_2': "← Change series",
        'back_step_3': "← Change phone",
        'back_step_4': "← Change issue",
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
    faqs = RepairFAQ.objects.all().order_by('order')
    reviews = Review.objects.filter(is_verified=True).order_by('-created_at')[:6]

    t = UI_TRANSLATIONS.get(current_lang, UI_TRANSLATIONS['uz'])

    context = {
        'brands': brands,
        'faqs': faqs,
        'reviews': reviews,
        'current_lang': current_lang,
        't': t,
    }
    return render(request, 'index.html', context)


# --- 5-Step Dynamic APIs ---

@require_GET
def api_series_by_brand(request, brand_id):
    """Step 2: Model seriyalari (Pro seriya, S seriya, va h.k.)"""
    series_qs = DeviceSeries.objects.filter(brand_id=brand_id).order_by('order', 'name')
    data = []
    for s in series_qs:
        data.append({
            'id': s.id,
            'name': s.name,
            'slug': s.slug,
            'brand_id': s.brand.id,
            'brand_name': s.brand.name,
            'brand_slug': s.brand.slug,
        })
    return JsonResponse({'series': data})


@require_GET
def api_phones_by_series(request, series_id):
    """Step 3: Aniq telefon modellari (iPhone 16 Pro Max va h.k.)"""
    phones_qs = DevicePhone.objects.filter(series_id=series_id).select_related('series', 'series__brand').order_by('order', 'name')
    data = []
    for p in phones_qs:
        image_url = p.image.url if p.image else f"/static/img/models/{p.slug.replace('-', '_')}.jpg"
        data.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'release_year': p.release_year,
            'image_url': image_url,
            'series_id': p.series.id,
            'series_name': p.series.name,
            'brand_name': p.series.brand.name,
        })
    return JsonResponse({'phones': data})


@require_GET
def api_issues_by_phone(request, phone_id):
    """Step 4: Muammolar / Detallar (30 ta ikonka bilan)"""
    lang = request.GET.get('lang') or get_language() or 'uz'
    issues_qs = DeviceIssue.objects.filter(phone_id=phone_id).order_by('order', 'title')
    data = []
    for issue in issues_qs:
        title = issue.title
        if lang == 'ru' and issue.title_ru:
            title = issue.title_ru
        elif lang == 'en' and issue.title_en:
            title = issue.title_en

        icon_svg_url = f"/static/img/icons/{issue.icon_number}.svg" if issue.icon_number else "/static/img/brands/apple.svg"

        data.append({
            'id': issue.id,
            'title': title,
            'icon_number': issue.icon_number,
            'icon_svg_url': icon_svg_url,
        })
    return JsonResponse({'issues': data})


@require_GET
def api_comparisons_by_issue(request, issue_id):
    """Step 5: Narxlar va solishtirish kartalari"""
    lang = request.GET.get('lang') or get_language() or 'uz'
    comp_qs = IssueComparison.objects.filter(issue_id=issue_id).order_by('-quality_type')

    data = []
    for c in comp_qs:
        title = c.title
        is_original = (c.quality_type == 'original_service_pack')

        if lang == 'ru':
            title = c.title_ru or ("Оригинал Завод" if is_original else "Качественная Копия")
            badge = "Оригинал" if is_original else "Копия"
            warranty = c.warranty_ru or c.warranty or ""
            desc = c.description_ru or c.description or ""
        elif lang == 'en':
            title = c.title_en or ("Original Factory" if is_original else "High-Quality Copy")
            badge = "Original" if is_original else "Copy"
            warranty = c.warranty_en or c.warranty or ""
            desc = c.description_en or c.description or ""
        else:
            title = c.title or ("Original Zavod" if is_original else "Sifatli Kopiya")
            badge = "Original" if is_original else "Kopiya"
            warranty = c.warranty or ""
            desc = c.description or ""

        is_available = bool(c.is_in_stock and (c.quantity > 0))
        if lang == 'ru':
            stock_display = f"В наличии: {c.quantity} шт." if is_available else "Нет в наличии (Под заказ)"
        elif lang == 'en':
            stock_display = f"In Stock: {c.quantity} pcs" if is_available else "Out of stock (On order)"
        else:
            stock_display = f"Omborda: {c.quantity} ta" if is_available else "Mavjud emas (Kutilmoqda)"

        data.append({
            'id': c.id,
            'quality_type': c.quality_type,
            'quality_display': c.get_quality_type_display(),
            'title': title,
            'part_price_uzs': int(c.part_price_uzs),
            'service_fee_uzs': int(c.service_fee_uzs),
            'total_price_uzs': int(c.total_price_uzs),
            'price_usd': int(c.price_usd),
            'quantity': c.quantity,
            'is_in_stock': is_available,
            'stock_display': stock_display,
            'warranty': warranty,
            'repair_time': c.repair_time,
            'badge': badge,
            'description': desc,
            'features': c.features if isinstance(c.features, list) else [],
        })
    return JsonResponse({'options': data})


@require_GET
def api_search_phones(request):
    """Jonli qidiruv (Telefon nomi bo'yicha)"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'phones': []})

    phones_qs = DevicePhone.objects.filter(name__icontains=query).select_related('series', 'series__brand').order_by('order')[:10]
    data = []
    for p in phones_qs:
        image_url = p.image.url if p.image else f"/static/img/models/{p.slug.replace('-', '_')}.jpg"
        data.append({
            'id': p.id,
            'name': p.name,
            'series_id': p.series.id,
            'series_name': p.series.name,
            'brand_id': p.series.brand.id,
            'brand_name': p.series.brand.name,
            'image_url': image_url,
        })
    return JsonResponse({'phones': data})


@require_POST
def api_submit_order(request):
    """Ariza qabul qilish va Telegram admin(lar)ga xabar yuborish"""
    try:
        data = json.loads(request.body)
        client_name = data.get('client_name', '').strip()
        phone_number = data.get('phone_number', '').strip()
        phone_id = data.get('phone_id')
        comparison_id = data.get('comparison_id') or data.get('option_id')
        service_type = data.get('service_type', 'in_service')

        if not client_name or not phone_number:
            return JsonResponse({'success': False, 'error': "Ism va telefon raqami kiritilishi shart!"}, status=400)

        order = ServiceOrder.objects.create(
            client_name=client_name,
            phone_number=phone_number,
            phone_id=phone_id if phone_id else None,
            comparison_id=comparison_id if comparison_id else None,
            service_type=service_type,
        )

        # Telegram notification to all configured admins
        bot_token = settings.TELEGRAM_BOT_TOKEN
        admin_chat_ids_raw = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '') or ''
        admin_ids = [i.strip() for i in str(admin_chat_ids_raw).split(',') if i.strip()]

        if bot_token and admin_ids:
            try:
                phone_str = order.phone.name if order.phone else "Ko'rsatilmagan"
                part_str = order.comparison.title if order.comparison else "Umumiy konsultatsiya"
                price_str = f"{order.comparison.total_price_uzs:,} so'm" if order.comparison else "-"

                text = (
                    f"🚨 <b>YANGI BUYURTMA! #{order.order_id}</b>\n\n"
                    f"👤 <b>Mijoz:</b> {client_name}\n"
                    f"📞 <b>Telefon:</b> {phone_number}\n"
                    f"📱 <b>Telefon:</b> {phone_str}\n"
                    f"🔧 <b>Xizmat:</b> {part_str}\n"
                    f"💵 <b>Narx:</b> {price_str}\n"
                    f"📍 <b>Format:</b> {order.get_service_type_display()}"
                )
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

                for aid in admin_ids:
                    try:
                        requests.post(url, json={
                            'chat_id': aid,
                            'text': text,
                            'parse_mode': 'HTML'
                        }, timeout=4)
                    except Exception:
                        pass
            except Exception:
                pass

        return JsonResponse({
            'success': True,
            'order_id': order.order_id,
            'message': "Arizangiz muvaffaqiyatli qabul qilindi! Tez orada mutaxassisimiz siz bilan bog‘lanadi."
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
