import json
import requests
from datetime import timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from django.utils import timezone
from django.utils.translation import get_language
from django.core.cache import cache
from django.utils.html import escape
from .models import (
    Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison,
    RepairFAQ, Review, ServiceOrder, TeamMember, BotAdmin
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
        'team_title': "Bizning <span>jamoamiz!</span>",
        'team_sub': "Mutaxassislarimiz qurilmangizga ehtiyotkorlik bilan yondashadi",
        'faq_title': "Ekspert maslahati: <span>Eng ko'p beriladigan savollar</span>",
        'faq_sub': "Nega batareya shishadi? Nega original qimmat? Ustalarimiz ochiq tushuntirish beradi.",
        'reviews_title': "Mijozlarimiz <span>fikrlari</span>",
        'reviews_sub': "Shaffof narxlar va tezkor servisimizdan foydalangan mijozlar sharhlari",
        'leave_review_btn': "✍️ Fikr qoldirish",
        'review_modal_title': "Fikr va mulohaza qoldirish",
        'modal_title': "Buyurtmani tasdiqlash",
        'name_label': "Ismingiz *",
        'phone_label': "Telefon raqamingiz *",
        'format_label': "Xizmat formati",
        'format_opt_1': "Servis markaziga boraman (30 daqiqada)",
        'format_opt_2': "Usta chaqirish (Manzilga usta boradi)",
        'format_opt_3': "Kuryer orqali yuborish (Bepul olib ketish)",
        'btn_submit': "Tasdiqlash va Yuborish",
        'consult_badge': "🛠 Ko'p Yillik Tajribali Telefon Ustalari",
        'consult_title': "Saytdan o'zingizga kerakli modelni topa olmadingizmi?",
        'consult_desc': "Siz ishlatib turgan har qanday smartfon uchun biz bilan bog‘lanib o‘zingizga kerakli bo‘lgan ehtiyot qismni topishingiz mumkin va siz ko‘p yillik tajribali telefon ustalariga bemalol omonatlaringizni ishonib topshirishingiz mumkin.",
        'consult_call_1': "+998 (90) 919-76-00",
        'consult_call_2': "+998 (90) 918-76-00",
        'consult_tg': "Telegram orqali bog‘lanish",
        'consult_ig': "Instagram sahifamiz",
        'consult_qr_hint': "Kamerangizni qarating yoki bosing",
        'track_order_btn': "Buyurtma holatini tekshirish",
        'track_modal_title': "Buyurtma holatini tekshirish",
        'track_placeholder': "Buyurtma ID sini kiriting (masalan: MP-XXXXXX)",
        'track_btn': "Tekshirish",
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
        'team_title': "Наша <span>команда!</span>",
        'team_sub': "Наши специалисты бережно относятся к вашему устройству",
        'faq_title': "Советы экспертов: <span>Частые вопросы</span>",
        'faq_sub': "Почему вздувается батарея? Почему оригинал дороже? Мастера дают открытый ответ.",
        'reviews_title': "Отзывы <span>наших клиентов</span>",
        'reviews_sub': "Отзывы клиентов, выбравших прозрачные цены и быстрый ремонт",
        'leave_review_btn': "✍️ Оставить отзыв",
        'review_modal_title': "Оставить отзыв о сервисе",
        'modal_title': "Подтверждение заявки",
        'name_label': "Ваше имя *",
        'phone_label': "Номер телефона *",
        'format_label': "Формат услуги",
        'format_opt_1': "Приеду в сервис (ремонт за 30 минут)",
        'format_opt_2': "Вызов мастера (мастер приедет по адресу)",
        'format_opt_3': "Курьерская доставка (заберем бесплатно)",
        'btn_submit': "Подтвердить и отправить",
        'consult_badge': "🛠 Опытные мастера с многолетним стажем",
        'consult_title': "Не нашли нужную модель на сайте?",
        'consult_desc': "Свяжитесь с нами для любой модели смартфона, и наши специалисты подберут нужную деталь. Вы можете смело доверить свои устройства опытным мастерам с многолетним стажем.",
        'consult_call_1': "+998 (90) 919-76-00",
        'consult_call_2': "+998 (90) 918-76-00",
        'consult_tg': "Написать в Telegram",
        'consult_ig': "Наш Instagram",
        'consult_qr_hint': "Наведите камеру или нажмите",
        'track_order_btn': "Проверить статус заказа",
        'track_modal_title': "Проверка статуса ремонта",
        'track_placeholder': "Введите ID заказа (например: MP-XXXXXX)",
        'track_btn': "Проверить",
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
        'team_title': "Our <span>Team!</span>",
        'team_sub': "Our experienced specialists handle your device with maximum care",
        'faq_title': "Expert Advice: <span>Frequently Asked Questions</span>",
        'faq_sub': "Why do batteries swell? Why are genuine screens costly? Our technicians explain.",
        'reviews_title': "Customer <span>Reviews</span>",
        'reviews_sub': "Verified customer feedback about our transparent pricing and rapid service",
        'leave_review_btn': "✍️ Leave a Review",
        'review_modal_title': "Leave Customer Feedback",
        'modal_title': "Confirm Request",
        'name_label': "Your Name *",
        'phone_label': "Phone Number *",
        'format_label': "Service Format",
        'format_opt_1': "Visit service center (ready in 30 mins)",
        'format_opt_2': "Call a technician (on-site repair)",
        'format_opt_3': "Free courier pickup and return",
        'btn_submit': "Confirm and Send",
        'consult_badge': "🛠 Expert Phone Technicians with Years of Experience",
        'consult_title': "Can't find your phone model on the site?",
        'consult_desc': "Contact us for any smartphone you use to find the exact spare part you need. You can confidently trust your device to experienced repair masters.",
        'consult_call_1': "+998 (90) 919-76-00",
        'consult_call_2': "+998 (90) 918-76-00",
        'consult_tg': "Message on Telegram",
        'consult_ig': "Our Instagram",
        'consult_qr_hint': "Scan with camera or tap",
        'track_order_btn': "Check Repair Status",
        'track_modal_title': "Track Your Repair Order",
        'track_placeholder': "Enter Order ID (e.g. MP-XXXXXX)",
        'track_btn': "Check Status",
    }
}


def index_view(request):
    current_lang = getattr(request, 'LANGUAGE_CODE', None) or get_language() or 'uz'
    if current_lang not in ('uz', 'ru', 'en'):
        current_lang = 'uz'

    brands = Brand.objects.filter(is_active=True).order_by('order', 'name')
    faqs = RepairFAQ.objects.all().order_by('order')
    reviews = Review.objects.filter(is_verified=True).order_by('-created_at')[:8]
    team_members = TeamMember.objects.filter(is_active=True).order_by('order', 'id')

    t = UI_TRANSLATIONS.get(current_lang, UI_TRANSLATIONS['uz'])

    context = {
        'brands': brands,
        'faqs': faqs,
        'reviews': reviews,
        'team_members': team_members,
        'current_lang': current_lang,
        't': t,
    }
    return render(request, 'index.html', context)


def get_client_ip(request):
    """Mijozning haqiqiy IP manzilini aniqlash"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'


# --- 5-Step Dynamic APIs (Cached for High-Load 10,000+ RPS) ---

@require_GET
def api_series_by_brand(request, brand_id):
    """Step 2: Model seriyalari (Pro seriya, S seriya, va h.k.)"""
    cache_key = f"api_series_brand_{brand_id}"
    data = cache.get(cache_key)
    if data is None:
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
        cache.set(cache_key, data, 300)
    return JsonResponse({'series': data})


@require_GET
def api_phones_by_series(request, series_id):
    """Step 3: Aniq telefon modellari (iPhone 16 Pro Max va h.k.)"""
    cache_key = f"api_phones_series_{series_id}"
    data = cache.get(cache_key)
    if data is None:
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
        cache.set(cache_key, data, 300)
    return JsonResponse({'phones': data})


@require_GET
def api_issues_by_phone(request, phone_id):
    """Step 4: Muammolar / Detallar (30 ta ikonka bilan)"""
    lang = request.GET.get('lang') or get_language() or 'uz'
    cache_key = f"api_issues_phone_{phone_id}_{lang}"
    data = cache.get(cache_key)
    if data is None:
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
        cache.set(cache_key, data, 300)
    return JsonResponse({'issues': data})


@require_GET
def api_comparisons_by_issue(request, issue_id):
    """Step 5: Narxlar va solishtirish kartalari"""
    lang = request.GET.get('lang') or get_language() or 'uz'
    cache_key = f"api_comparisons_issue_{issue_id}_{lang}"
    data = cache.get(cache_key)
    if data is None:
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
        cache.set(cache_key, data, 300)
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


@csrf_exempt
@require_POST
def api_submit_order(request):
    """Ariza qabul qilish va Telegram admin(lar)ga xabar yuborish (Rate Limiter: max 2/min per IP)"""
    try:
        # Rate Limiting (Anti-Spam: max 2 per minute from same IP)
        client_ip = get_client_ip(request)
        rate_key = f"order_ratelimit_{client_ip}"
        submits = cache.get(rate_key, 0)
        if submits >= 2:
            return JsonResponse({
                'success': False,
                'error': "Spam himoyasi: 1 daqiqada maksimum 2 ta ariza yuborish mumkin. Iltimos, ozroq kuting."
            }, status=429)
        cache.set(rate_key, submits + 1, 60)

        data = json.loads(request.body)
        client_name = escape(data.get('client_name', '').strip())
        phone_number = escape(data.get('phone_number', '').strip())
        phone_id = data.get('phone_id')
        comparison_id = data.get('comparison_id') or data.get('option_id')
        service_type = escape(data.get('service_type', 'in_service'))

        if not client_name or not phone_number:
            return JsonResponse({'success': False, 'error': "Ism va telefon raqami kiritilishi shart!"}, status=400)

        order = ServiceOrder.objects.create(
            client_name=client_name,
            phone_number=phone_number,
            phone_id=phone_id if phone_id else None,
            comparison_id=comparison_id if comparison_id else None,
            service_type=service_type,
        )

        # Telegram notification to all configured admins and dynamic BotAdmins
        bot_token = settings.TELEGRAM_BOT_TOKEN
        admin_chat_ids_raw = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '') or ''
        admin_ids = [i.strip() for i in str(admin_chat_ids_raw).split(',') if i.strip()]

        try:
            db_admin_ids = list(BotAdmin.objects.exclude(telegram_id__isnull=True).values_list('telegram_id', flat=True))
            for aid in db_admin_ids:
                if str(aid) not in admin_ids:
                    admin_ids.append(str(aid))
        except Exception:
            pass

        if bot_token and admin_ids:
            try:
                phone_str = order.phone.name if order.phone else "Ko'rsatilmagan"
                part_str = order.comparison.title if order.comparison else "Umumiy konsultatsiya"
                price_str = f"{order.comparison.total_price_uzs:,} so'm" if order.comparison else "-"

                text = (
                    f"🚨 <b>YANGI TA'MIRLASH BUYURTMASI! #{order.order_id}</b>\n\n"
                    f"👤 <b>Mijoz:</b> {client_name}\n"
                    f"📞 <b>Telefon:</b> <code>{phone_number}</code>\n"
                    f"📱 <b>Model:</b> {phone_str}\n"
                    f"🔧 <b>Muammo / Qism:</b> {part_str}\n"
                    f"💵 <b>Narxi:</b> {price_str}\n"
                    f"📦 <b>Holati:</b> 🔴 Yangi ariza\n"
                    f"📍 <b>Format:</b> {order.get_service_type_display()}"
                )

                inline_kb = {
                    'inline_keyboard': [
                        [
                            {'text': "✅ Qabul qilish", 'callback_data': f"crm_st:{order.id}:contacted"},
                            {'text': "👨‍🔧 Ustaga biriktirish", 'callback_data': f"crm_assign:{order.id}"},
                        ],
                        [
                            {'text': "📞 Bog‘lanildi", 'callback_data': f"crm_st:{order.id}:contacted"},
                            {'text': "🎉 Tayyor", 'callback_data': f"crm_st:{order.id}:ready"},
                        ],
                        [
                            {'text': "❌ Bekor qilish", 'callback_data': f"crm_st:{order.id}:cancelled"}
                        ]
                    ]
                }

                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

                for aid in admin_ids:
                    try:
                        requests.post(url, json={
                            'chat_id': aid,
                            'text': text,
                            'parse_mode': 'HTML',
                            'reply_markup': inline_kb
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



@require_GET
def api_track_order(request):
    """Mijoz uchun ta'mirlash holatini (Order tracking) tekshirish API"""
    raw_code = request.GET.get('order_id', '').strip()
    clean_code = raw_code.replace('#', '').strip().upper()
    lang = request.GET.get('lang', 'uz')

    if not clean_code:
        err_msg = {
            'ru': "Пожалуйста, введите код заказа (например: MP-A1B2C3)",
            'en': "Please enter your order ID (e.g. MP-A1B2C3)",
            'uz': "Iltimos, buyurtma kodini kiriting (masalan: MP-A1B2C3)"
        }.get(lang, "Iltimos, buyurtma kodini kiriting")
        return JsonResponse({'found': False, 'error': err_msg}, status=400)

    try:
        order = ServiceOrder.objects.filter(order_id__iexact=clean_code).select_related('phone', 'comparison').first()
        if not order:
            not_found_msg = {
                'ru': f"Заказ с кодом #{clean_code} не найден. Проверьте правильность кода.",
                'en': f"Order #{clean_code} was not found. Please double-check your code.",
                'uz': f"#{clean_code} raqamli buyurtma topilmadi. Kodni to'g'ri kiritganingizni tekshiring."
            }.get(lang, "Buyurtma topilmadi.")
            return JsonResponse({'found': False, 'error': not_found_msg}, status=404)

        # Mapping status to 4-step progress:
        # 1: Qabul qilindi
        # 2: Diagnostika / Bog'lanildi
        # 3: Ta'mirlanmoqda
        # 4: Tayyor / Topshirildi
        step_map = {
            'new': 1,
            'contacted': 2,
            'in_progress': 3,
            'ready': 4,
            'completed': 4,
            'cancelled': 0,
        }
        current_step = step_map.get(order.status, 1)

        # Status labels per language
        status_labels = {
            'uz': {
                'new': 'Qabul qilindi',
                'contacted': 'Diagnostika jarayonida',
                'in_progress': "Ta'mirlanmoqda",
                'ready': "Tayyor (Olib ketishingiz mumkin)",
                'completed': "Topshirildi",
                'cancelled': "Bekor qilingan"
            },
            'ru': {
                'new': 'Принято',
                'contacted': 'На диагностике',
                'in_progress': 'В процессе ремонта',
                'ready': 'Готов к выдаче',
                'completed': 'Выдан клиенту',
                'cancelled': 'Отменен'
            },
            'en': {
                'new': 'Received',
                'contacted': 'Diagnostic in progress',
                'in_progress': 'In repair',
                'ready': 'Ready for pickup',
                'completed': 'Completed',
                'cancelled': 'Cancelled'
            }
        }
        status_text = status_labels.get(lang, status_labels['uz']).get(order.status, order.get_status_display())

        # Mask client name for privacy (e.g., "Murodjon" -> "Mu***on")
        name = order.client_name
        masked_name = f"{name[:2]}***{name[-2:]}" if len(name) > 4 else f"{name[:1]}***"

        phone_name = order.phone.name if order.phone else "Smartfon"
        part_name = order.comparison.title if order.comparison else "-"
        price_val = int(order.comparison.total_price_uzs) if (order.comparison and order.comparison.total_price_uzs) else None

        return JsonResponse({
            'found': True,
            'order_id': order.order_id,
            'client_masked': masked_name,
            'device_model': phone_name,
            'issue_title': part_name,
            'price_uzs': price_val,
            'status': order.status,
            'status_display': status_text,
            'current_step': current_step,
            'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
        })
    except Exception as e:
        return JsonResponse({'found': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_submit_review(request):
    """Mijoz fikri qabul qilish (Anti-Spam: 1 ta qurilma + 1 ta IP dan 24 soatda faqat 1 marta)"""
    try:
        data = json.loads(request.body)
        client_name = escape(data.get('client_name', '').strip())
        device_model = escape(data.get('device_model', '').strip())
        service_type = escape(data.get('service_type', '').strip())
        rating = int(data.get('rating', 5))
        comment = escape(data.get('comment', '').strip())
        device_fp = escape(data.get('device_fingerprint', '').strip())
        lang = data.get('lang', 'uz')

        if not client_name or not comment:
            err_msg = {
                'ru': "Пожалуйста, укажите имя и напишите отзыв.",
                'en': "Please enter your name and review text.",
                'uz': "Iltimos, ismingizni va fikringizni yozing."
            }.get(lang, "Ism va fikr matni kiritilishi shart.")
            return JsonResponse({'success': False, 'error': err_msg}, status=400)

        if rating < 1 or rating > 5:
            rating = 5

        client_ip = get_client_ip(request)
        one_day_ago = timezone.now() - timedelta(hours=24)

        # 1. IP tekshiruvi (Oxirgi 24 soat ichida)
        ip_has_reviewed = Review.objects.filter(
            ip_address=client_ip,
            created_at__gte=one_day_ago
        ).exists()

        # 2. Qurilma identifikatori (Fingerprint) tekshiruvi (Oxirgi 24 soat ichida)
        device_has_reviewed = False
        if device_fp:
            device_has_reviewed = Review.objects.filter(
                device_fingerprint=device_fp,
                created_at__gte=one_day_ago
            ).exists()

        if ip_has_reviewed or device_has_reviewed:
            limit_msg = {
                'ru': "Вы уже оставляли отзыв за последние 24 часа. С одного устройства и IP разрешен только 1 отзыв в день!",
                'en': "You have already submitted a review in the last 24 hours. Only 1 review per day is allowed from the same device and IP!",
                'uz': "Siz oxirgi 24 soat ichida fikr qoldirgansiz. 1 ta qurilma va IP dan kunda faqat 1 marta sharh yozish mumkin!"
            }.get(lang, "Kunda faqat 1 marta fikr qoldirish mumkin!")
            return JsonResponse({'success': False, 'error': limit_msg}, status=429)

        # Sharhni bazaga saqlash
        review = Review.objects.create(
            client_name=client_name,
            device_model=device_model or "Smartfon",
            service_type=service_type or "Servis xizmati",
            rating=rating,
            comment=comment,
            ip_address=client_ip,
            device_fingerprint=device_fp or None,
            is_verified=True,
        )

        # Telegram bot orqali barcha adminlarga bildirishnoma yuborish
        bot_token = settings.TELEGRAM_BOT_TOKEN
        admin_chat_ids_raw = getattr(settings, 'TELEGRAM_ADMIN_CHAT_ID', '') or ''
        admin_ids = [i.strip() for i in str(admin_chat_ids_raw).split(',') if i.strip()]

        # Dinamik BotAdmin larni ham qo'shamiz
        try:
            db_admin_ids = list(BotAdmin.objects.exclude(telegram_id__isnull=True).values_list('telegram_id', flat=True))
            for aid in db_admin_ids:
                if str(aid) not in admin_ids:
                    admin_ids.append(str(aid))
        except Exception:
            pass

        if bot_token and admin_ids:
            try:
                stars_str = '⭐️' * review.rating
                text = (
                    f"💬 <b>YANGI MIJOZ SHARHI!</b>\n\n"
                    f"👤 <b>Mijoz:</b> {review.client_name}\n"
                    f"📱 <b>Model:</b> {review.device_model}\n"
                    f"🔧 <b>Xizmat:</b> {review.service_type}\n"
                    f"⭐️ <b>Baho:</b> {stars_str} ({review.rating}/5)\n"
                    f"📝 <b>Fikr:</b> \"<i>{review.comment}</i>\"\n"
                    f"🌐 <b>IP:</b> <code>{client_ip}</code>"
                )
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                for aid in admin_ids:
                    try:
                        requests.post(url, json={
                            'chat_id': aid,
                            'text': text,
                            'parse_mode': 'HTML'
                        }, timeout=3)
                    except Exception:
                        pass
            except Exception:
                pass

        success_msg = {
            'ru': "Большое спасибо! Ваш отзыв успешно добавлен и опубликован.",
            'en': "Thank you very much! Your review has been successfully published.",
            'uz': "Katta rahmat! Sizning fikringiz muvaffaqiyatli qabul qilindi va saytda e'lon qilindi."
        }.get(lang, "Fikringiz muvaffaqiyatli saqlandi.")

        return JsonResponse({
            'success': True,
            'message': success_msg,
            'review': {
                'id': review.id,
                'client_name': review.client_name,
                'device_model': review.device_model,
                'service_type': review.service_type,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.strftime('%d.%m.%Y'),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


