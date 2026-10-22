import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from django.utils.translation import get_language
from .models import Brand, DeviceModel, PartCategory, PartOption, RepairFAQ, Review, ServiceOrder


def index_view(request):
    current_lang = get_language() or 'uz'
    brands = Brand.objects.filter(is_active=True).order_by('order', 'name')
    categories = PartCategory.objects.all().order_by('order')
    faqs = RepairFAQ.objects.all().order_by('order')
    reviews = Review.objects.filter(is_verified=True).order_by('-created_at')[:6]

    context = {
        'brands': brands,
        'categories': categories,
        'faqs': faqs,
        'reviews': reviews,
        'current_lang': current_lang,
    }
    return render(request, 'index.html', context)


@require_GET
def api_models_by_brand(request, brand_id):
    models_qs = DeviceModel.objects.filter(brand_id=brand_id).order_by('order', 'name')
    data = [
        {
            'id': m.id,
            'name': m.name,
            'slug': m.slug,
            'model_code': m.model_code,
            'release_year': m.release_year,
            'is_popular': m.is_popular,
        }
        for m in models_qs
    ]
    return JsonResponse({'models': data})


@require_GET
def api_search_models(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'models': []})

    models_qs = DeviceModel.objects.filter(name__icontains=query).select_related('brand').order_by('order')[:10]
    data = [
        {
            'id': m.id,
            'name': m.name,
            'brand_id': m.brand.id,
            'brand_name': m.brand.name,
            'slug': m.slug,
        }
        for m in models_qs
    ]
    return JsonResponse({'models': data})


@require_GET
def api_part_options(request):
    model_id = request.GET.get('model_id')
    category_id = request.GET.get('category_id')

    if not model_id or not category_id:
        return JsonResponse({'error': 'model_id and category_id are required'}, status=400)

    lang = get_language() or 'uz'
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
