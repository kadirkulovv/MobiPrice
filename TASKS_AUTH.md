# MobiPrice — Telegram Auth, Buyurtma Cheklovi va Kuryer Lokatsiya Tizimi (`TASKS_AUTH.md`)

> **Maqsad:** Mavjud **Precision Tech-Lab** frontend dizayni va **Django 5.x + aiogram 3.x** funksionalligini buzmasdan, faqat Telegram orqali xavfsiz read-only autentifikatsiya, sharh/buyurtma cheklovi, servis lokatsiya kartasi va bot orqali kuryer lokatsiyasi + masofa asosida narx hisoblash tizimini joriy qilish.

---

## Qat'iy Cheklovlar va Texnik Qoidalar

- **Tegilmaydigan fayllar/papkalar:** `.env`, `.venv/`, `backups/`, `media/` — bu fayl va papkalarga umuman o'zgartirish kiritilmaydi.
- **Tashqi CSS qoidasi:** Barcha yangi UI stillari faqat `static/css/` ichidagi tashqi fayllarda (`auth_modal.css` hamda mavjud `navbar.css`, `order_modal.css`, `review_modal.css`) yoziladi. HTML shablonlarda inline `style="..."` yoki `<style>` bloki ishlatilmaydi.
- **Responsivlik (PC / iOS Safari / Android Chrome):**
  - Barcha `<input>`, `<select>`, `<textarea>` elementlarida `font-size: 16px` saqlanadi (iOS Safari auto-zoom oldini olish uchun).
  - Modallar `100dvh` va `env(safe-area-inset-*)` bilan ishlaydi.
  - Barcha breakpointlarda (`320px` — `1920px+`) `0%` gorizontal overflow va kamida `44px` touch-target ta'minlanadi.
- **Django va Tarjima (i18n) teglari:**
  - Mavjud barcha `{% url %}`, `{% static %}`, `{% csrf_token %}`, `{% load i18n %}`, `{% trans %}`, `{% blocktrans %}` teglari to'liq saqlanadi.
  - Barcha yangi matnlar `{% trans %}` / `{% blocktrans %}` teglarida yoziladi hamda `locale/` (UZ/RU/EN) va JS tarjimalari bilan sinxronlanadi.
- **Do'konning aniq koordinatalari va havolalari (`config/settings.py` default qiymatlari):**
  - `SHOP_LAT = 41.338306`
  - `SHOP_LON = 69.270389`
  - `SHOP_ADDRESS = "Malika bozor, B32 do'kon"`
  - Google Maps: `https://www.google.com/maps/search/?api=1&query=41.338306,69.270389`
  - Yandex Maps: `https://yandex.uz/maps/?pt=69.270389,41.338306&z=17&l=map` *(diqqat: `pt` parametrida avval `longitude`, keyin `latitude` keladi)*

---

## Arxitektura Xulosasi (Ta'sir Qiladigan Fayllar)

| Qatlam | Yangi fayllar | O'zgartiriladigan mavjud fayllar |
|---|---|---|
| **Django Config** | — | `config/settings.py` |
| **Django Core (Backend)** | `core/context_processors.py`, `core/telegram_auth.py`, `core/distance.py` | `core/models.py`, `core/views.py`, `core/api_urls.py`, `core/admin.py`, `core/tests.py` |
| **Telegram Bot (`aiogram 3.x`)** | `bot/handlers/client.py`, `bot/states/client_states.py` | `bot/main.py`, `bot/database.py`, `bot/handlers/start.py`, `bot/handlers/crm.py` |
| **Templates (HTML)** | `templates/components/auth_modal.html` | `templates/base.html`, `templates/components/navbar.html`, `templates/components/order_modal.html`, `templates/components/review_modal.html` |
| **Static (CSS / JS)** | `static/css/auth_modal.css`, `static/js/auth.js` | `static/css/style.css`, `static/css/navbar.css`, `static/css/order_modal.css`, `static/css/review_modal.css`, `static/js/app.js`, `static/js/calculator.js`, `static/js/modal.js`, `static/js/review.js` |
| **Locale (i18n)** | `locale/{uz,ru,en}/LC_MESSAGES/django.po` (+ `.mo`) | — |

---

## 1-bosqich: Faqat Telegram orqali Login (Auth) tizimi va Ngrok mosligi

### 1.1. Vaqtinchalik Ngrok, Proxy va Telegram/Do'kon sozlamalari (`config/settings.py`)
- [x] `config/settings.py` da `DEBUG=True` holati uchun alohida izohli (keyin domen ulanganda oson olib tashlanadigan/o'zgartiriladigan) blok qo'shish:
  - `ALLOWED_HOSTS` ga `.ngrok-free.app`, `.ngrok-free.dev`, `.ngrok.io` domenlarini qo'shish (agar ro'yxatda yo'q bo'lsa).
  - `CSRF_TRUSTED_ORIGINS` ga `https://*.ngrok-free.app`, `https://*.ngrok-free.dev`, `https://*.ngrok.io` (va lokal `http://localhost:8080`, `http://127.0.0.1:8080`) manzillarini qo'shish.
  - `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` ni yoqish (ngrok HTTPS proksi ortida `request.is_secure()` va CSRF/canonical URL to'g'ri ishlashi uchun).
- [x] `SESSION_COOKIE_HTTPONLY = True` va `SESSION_COOKIE_SAMESITE = 'Lax'` ni aniq belgilash.
- [x] Telegram bot username sozlamasini qo'shish:
  - `TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', '').lstrip('@').strip()`
  - `.env` ga tegmagan holda avtomatik ishlashi uchun `core/telegram_auth.py` da `get_bot_username()` helperini yozish: agar `settings.TELEGRAM_BOT_USERNAME` bo'sh bo'lsa, `TELEGRAM_BOT_TOKEN` orqali Telegram API `getMe` ni 1 marta so'rab, natijani `django.core.cache` da (masalan, 1 soat) keshlab saqlash.
- [x] Do'kon lokatsiya sozlamalarini (`.env` orqali o'zgartiriladigan default qiymatlar bilan) `config/settings.py` ga qo'shish:
  - `SHOP_LAT = float(os.getenv('SHOP_LAT', '41.338306'))`
  - `SHOP_LON = float(os.getenv('SHOP_LON', '69.270389'))`
  - `SHOP_ADDRESS = os.getenv('SHOP_ADDRESS', "Malika bozor, B32 do'kon")`
  - `SHOP_GOOGLE_MAPS_URL = os.getenv('SHOP_GOOGLE_MAPS_URL', f'https://www.google.com/maps/search/?api=1&query={SHOP_LAT},{SHOP_LON}')`
  - `SHOP_YANDEX_MAPS_URL = os.getenv('SHOP_YANDEX_MAPS_URL', f'https://yandex.uz/maps/?pt={SHOP_LON},{SHOP_LAT}&z=17&l=map')`
- [x] `TEMPLATES[0]['OPTIONS']['context_processors']` ro'yxatiga `core.context_processors.telegram_auth_context` ni qo'shish.

### 1.2. Ma'lumotlar Bazasi Modellari (`core/models.py`, `core/admin.py`, `bot/database.py`)
- [x] `TelegramUser` modelini yaratish:
  - `telegram_id` (`BigIntegerField`, `unique=True`, `db_index=True`)
  - `first_name` (`CharField`, `max_length=150`, `blank=True`)
  - `last_name` (`CharField`, `max_length=150`, `blank=True`)
  - `username` (`CharField`, `max_length=150`, `blank=True`, `db_index=True`)
  - `photo_url` (`URLField`, `max_length=500`, `blank=True`)
  - `created_at` (`DateTimeField`, `auto_now_add=True`)
  - `updated_at` (`DateTimeField`, `auto_now=True`)
  - Yordamchi property'lar: `full_name`, `display_handle`, `tg_profile_url`, `initials`.
- [x] Bir martalik `AuthToken` modelini yaratish (Bot Deep-Link zaxira login uchun):
  - `token` (`CharField`, `max_length=64`, `unique=True`, `db_index=True`) — `secrets.token_urlsafe(24)` (Telegram `/start` payload limitiga `<= 64` belgi to'liq mos: `login_` + 32 belgi = 38 belgi).
  - `session_key` (`CharField`, `max_length=64`, `blank=True`, `db_index=True`) — faqat tokenni yaratgan brauzer sessiyasi loginni yakunlay olishi uchun.
  - `telegram_user` (`ForeignKey(TelegramUser, null=True, blank=True, on_delete=models.CASCADE, related_name='auth_tokens')`).
  - `is_confirmed` (`BooleanField`, `default=False`) — botda `/start login_<token>` tasdiqlanganda `True`.
  - `is_used` (`BooleanField`, `default=False`) — sayt sessiyasiga biriktirilgach `True` (bir martalik).
  - `created_at` (`DateTimeField`, `auto_now_add=True`).
  - `expires_at` (`DateTimeField`) — 5 daqiqalik TTL.
- [x] `TelegramUser` va `AuthToken` modellarini `core/admin.py` da ro'yxatdan o'tkazish hamda `bot/database.py` da eksport qilish.

### 1.3. Xavfsiz Read-Only Telegram Autentifikatsiya Logikasi (`core/telegram_auth.py`, `core/views.py`, `core/api_urls.py`)
- [x] `core/telegram_auth.py` modulini yaratish:
  - `verify_telegram_widget_data(payload: dict, bot_token: str, max_age_seconds: int = 300) -> tuple[bool, str]`:
    - `hash` maydonini ajratib olish; qolgan barcha bo'sh bo'lmagan maydonlarni alifbo tartibida `key=value` ko'rinishida `\n` bilan birlashtirish (`data_check_string`).
    - `secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()`
    - `expected_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()`
    - `hmac.compare_digest(expected_hash, received_hash)` orqali qat'iy tekshirish.
    - `auth_date` ni tekshirish: butun son bo'lishi, kelajakda bo'lmasligi (`+60s` ruxsat) va eskirib ketmaganligi (`now - auth_date <= max_age_seconds`).
  - `upsert_telegram_user(data: dict) -> TelegramUser`: foydalanuvchi ma'lumotlarini yaratish yoki yangilash (faqat ochiq profil maydonlari; `BOT_TOKEN` o'z ichiga olgan fayl URL'lari hech qachon saqlanmaydi).
  - `get_current_telegram_user(request) -> TelegramUser | None`: `request.session.get('telegram_user_id')` bo'yicha aktiv foydalanuvchini olish.
  - `login_telegram_session(request, tg_user: TelegramUser)`: `request.session['telegram_user_id'] = tg_user.id` va `request.session.cycle_key()` (session fixation himoyasi).
  - `logout_telegram_session(request)`: `request.session.pop('telegram_user_id', None)` va `request.session.cycle_key()`.
- [x] Auth API endpointlarini (`core/api_urls.py` va `core/views.py`) qo'shish:
  - `GET /api/auth/me/` — joriy login holati (`authenticated`, `user`, `bot_username`).
  - `POST /api/auth/telegram/widget/` — Telegram Login Widget ma'lumotlarini HMAC-SHA256 + `auth_date` tekshiruvi bilan qabul qilib sessiyaga yozish.
  - `POST /api/auth/telegram/deeplink/start/` — bir martalik `AuthToken` yaratish, brauzer `session_key` ga bog'lash va `https://t.me/<BOT_USERNAME>?start=login_<token>` havolasini qaytarish.
  - `GET /api/auth/telegram/deeplink/status/?token=<token>` — frontend polling endpointi; botda tasdiqlangan bo'lsa, atomar tarzda `is_used=True` qilib Django sessiyasini ochish va foydalanuvchi obyektini qaytarish.
  - `POST /api/auth/logout/` — Telegram sessiyasidan chiqish.
- [x] `core/context_processors.py` da `telegram_auth_context(request)` yozish: har bir shablonga `tg_user`, `telegram_bot_username`, `shop_info` uzatish.

### 1.4. Bot Deep-Link Login Handleri (`bot/handlers/client.py`, `bot/main.py`)
- [x] `bot/handlers/client.py` routerini yaratish va `bot/main.py` da `start.router` dan **OLDIN** ro'yxatdan o'tkazish (oddiy mijozlar `/start login_<token>` bosganda admin ruxsat tekshiruviga tushib qolmasligi uchun).
- [x] `@router.message(StateFilter("*"), CommandStart(deep_link=True, magic=F.args.startswith("login_")))` handlerini yozish:
  - Tokenni bazadan tekshirish (`is_used=False`, `is_confirmed=False`, `expires_at > now`).
  - Token yaroqsiz yoki muddati o'tgan bo'lsa mijozga tushunarli xabar berish.
  - Yaroqli bo'lsa: `message.from_user` (`id`, `first_name`, `last_name`, `username`) asosida `TelegramUser` yaratish/yangilash, `AuthToken.telegram_user` va `is_confirmed=True` ni saqlash.
  - Mijozga Telegramda tasdiqlovchi xabar yuborish: *"✅ Saytga kirish tasdiqlandi! Endi brauzerga qaytishingiz mumkin."* (hech qanday admin menyusi ko'rsatilmaydi).

### 1.5. Auth UI va Topbar Til Tanlagichni Birlashtirish
- [x] **Dublikat til tanlagichni bartaraf etish (`templates/components/navbar.html`, `static/css/navbar.css`):**
  - Topbar o'ng burchagidagi ikkita takroriy element (`.lang-pills` `UZ RU EN` va yonidagi `.lang-select-box` `UZ v`) o'rniga **bitta toza til tanlagich** (`.lang-select-box` ichida `#lang-select`) qoldirish; `.lang-pills` HTML va keraksiz CSS qoidalarini olib tashlash.
  - `static/js/app.js` dagi `#lang-select` routing va `django_language` cookie saqlash mantiqi to'liq ishlashini saqlash.
- [x] **Topbar va Sidebar da Auth / Profil bloki (`templates/components/navbar.html`, `static/css/navbar.css`, `static/css/auth_modal.css`):**
  - Login qilmagan holatda: Topbar o'ng qismida va Sidebar pastki blokida *"Telegram orqali kirish"* tugmasi (`#btn-open-auth-topbar`, `#btn-open-auth-sidebar`).
  - Login qilingan holatda: Telegram avatari (`photo_url` + rasm bo'lmasa/yuklanmasa monogramma/initials fallback), foydalanuvchi ismi, `@username` (sidebarda) va *"Chiqish"* (`#btn-logout-topbar`, `#btn-logout-sidebar`) tugmasi.
- [x] **Telegram Login Modali (`templates/components/auth_modal.html`, `static/css/auth_modal.css`, `static/js/auth.js`):**
  - Xavfsizlik tushuntirish bloki (`{% trans %}`): faqat read-only kirish, Telegram akkountga kirish yoki foydalanuvchi nomidan xabar yuborish huquqi olinmasligi aniq ko'rsatiladi.
  - **1-usul (Asosiy, darhol faol):** Rasmiy Telegram Login Widget (`https://telegram.org/js/telegram-widget.js?22`, `data-telegram-login`, `data-size="large"`, `data-onauth="onTelegramAuth(user)"`, `data-request-access` qo'shilmaydi). *(Izoh: ngrok domeni ishlatilganda BotFather → `/setdomain` orqali joriy ngrok domenini biriktirish kerak; aks holda darhol 2-usul ishlaydi).*
  - **2-usul (Zaxira / Fallback):** *"Telegram Bot orqali kirish"* tugmasi — bosilganda `/api/auth/telegram/deeplink/start/` chaqiriladi, `https://t.me/<BOT_USERNAME>?start=login_<token>` havolasi ochiladi va frontend har 2 soniyada `/api/auth/telegram/deeplink/status/` ni polling qilib, tasdiqlangach sahifani qayta yuklamasdan (yoki holatni saqlab) avtomatik login qiladi.
  - `window.mobiAuth` global API (`isAuthenticated()`, `getUser()`, `openLoginModal(pendingAction)`, `logout()`): login muvaffaqiyatli tugagach UI ni darhol yangilash va kutilayotgan harakatni (`order` yoki `review`) avtomatik davom ettirish.

---

## 2-bosqich: Sharhlar va Buyurtmalarni faqat Login qilganlarga cheklash (2 ta xizmat turi)

### 2.1. Narx Ko'rish Ochiq, Harakatlar Yopiq (Frontend Gate)
- [x] Kalkulyatorning 1–5 qadamlari va jonli qidiruv (`/api/series/...`, `/api/phones/...`, `/api/issues/...`, `/api/comparisons/...`, `/api/phones/search/`) hamma uchun ochiq qolishini ta'minlash.
- [x] **Sharh qoldirish cheklovi (`static/js/review.js`, `templates/components/review_modal.html`):**
  - `"✍️ Fikr qoldirish"` (`#btn-open-review-modal`) bosilganda `window.mobiAuth.isAuthenticated()` tekshiriladi; login qilmagan bo'lsa, `#review-modal` ochilmasdan avval Telegram Login modali (`pendingAction = 'review'`) chiqadi.
  - `templates/components/review_modal.html` dan `#review-client-name` inputi butunlay olib tashlanadi; uning o'rniga login qilingan foydalanuvchining Telegram ismi va avatari read-only ko'rinishda chiqadi hamda forma ichiga `{% csrf_token %}` qo'shiladi.
  - `static/js/review.js` da `X-CSRFToken` header yuboriladi, `401` qaytsa Login modali ochiladi.
- [x] **Buyurtma berish cheklovi (`static/js/calculator.js`, `static/js/modal.js`):**
  - 5-qadamda `"Buyurtma berish"` (`.btn-book-option`) bosilganda `window.mobiState` saqlanadi, so'ng `window.mobiAuth.isAuthenticated()` tekshiriladi; login qilmagan bo'lsa, `#order-modal` ochilmasdan avval Telegram Login modali (`pendingAction = 'order'`) chiqadi.
  - Login yakunlangach, foydalanuvchi tanlagan telefon va zapchast ma'lumotlari saqlangan holda `#order-modal` avtomatik ochiladi.

### 2.2. Backend Himoyasi (`core/views.py`, `core/models.py`)
- [x] `Review` modeliga `telegram_user = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')` maydonini qo'shish.
- [x] `api_submit_review` endpointida:
  - Majburiy sessiya tekshiruvi: login qilinmagan so'rovga `401 Unauthorized` (`{'success': False, 'auth_required': True, 'error': ...}`) qaytarish.
  - `client_name` ni mijoz yuborgan JSON'dan emas, faqat sessiyadagi `tg_user.full_name` dan avtomatik olish.
  - 24 soatlik anti-spam cheklovini `telegram_user` (shuningdek IP/fingerprint) bo'yicha tekshirish.
  - Adminga yuboriladigan sharh xabarida mijozning Telegram `@username` / profil havolasini ko'rsatish.
- [x] `api_submit_order` endpointida:
  - Majburiy sessiya tekshiruvi: login qilinmagan so'rovga `401 Unauthorized` (`{'success': False, 'auth_required': True, 'error': ...}`) qaytarish.
  - `client_name` va `phone_number` kiritish talabini olib tashlash; `telegram_user = tg_user`, `client_name = tg_user.full_name[:100]`, `phone_number = ''` sifatida saqlash.
  - `service_type` faqat `('in_service', 'courier')` qiymatlarini qabul qilishini qat'iy tekshirish (`call_master` yuborilsa `400 Bad Request` qaytarish).

### 2.3. Buyurtma Modalini Soddalashtirish va Xizmat Turlarini 2 taga Tushirish
- [x] `ServiceOrder.SERVICE_CHOICES` (`core/models.py`) ni 3 tadan **2 taga** tushirish:
  - **O'CHIRILSIN:** `('call_master', _('Usta chaqirish (Manzilga)'))`
  - **QOLSIN:**
    1. `('in_service', _("O'zim boraman (Servis markaziga)"))`
    2. `('courier', _("Kuryer orqali olib ketish"))`
- [x] `ServiceOrder.phone_number` maydonini `blank=True, default=''` qilish (eski buyurtmalar buzilmasligi uchun ustun saqlanadi, yangi buyurtmalarda talab qilinmaydi).
- [x] `templates/components/order_modal.html` ni soddalashtirish:
  - `#client-name` (Ism/Familiya) va `#phone-number` (Telefon raqami) input bloklarini butunlay olib tashlash.
  - Login qilingan Telegram profili (avatar + ism + `@username`) ko'rinadigan ixcham blok qo'shish.
  - Xizmat formati (`#service-type`) da faqat 2 ta variant qoldirish:
    1. `in_service` — *"O'zim boraman (Servis markaziga)"*
    2. `courier` — *"Kuryer orqali olib ketish"*
  - `"Usta chaqirish (Manzilga usta boradi)"` va `"Bepul olib ketish"` / `"заберем бесплатно"` / `"Free courier"` yozuvlarini `core/views.py` (`UI_TRANSLATIONS`), `templates/components/order_modal.html`, `core/models.py` va barcha tarjimalardan butunlay olib tashlash.
- [x] `static/js/modal.js` dan `#client-name` va `#phone-number` o'qish/formatlash kodlarini olib tashlash va `401` holatida login modalini ochishni ulash.

---

## 3-bosqich: Servis Lokatsiyasi va Kuryer (Bot orqali lokatsiya + km narx hisoblash)

### 3.1. `ServiceOrder` Kuryer va Lokatsiya Maydonlari (`core/models.py`, `core/admin.py`)
- [x] `ServiceOrder.STATUS_CHOICES` ga `('pending_location', _('Lokatsiya kutilmoqda'))` holatini qo'shish.
- [x] `ServiceOrder` modeliga quyidagi maydonlarni qo'shish:
  - `telegram_user` (`ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')`)
  - `courier_token` (`CharField`, `max_length=64`, `unique=True`, `null=True`, `blank=True`, `db_index=True`)
  - `courier_token_expires_at` (`DateTimeField`, `null=True`, `blank=True`)
  - `latitude` (`FloatField`, `null=True`, `blank=True`)
  - `longitude` (`FloatField`, `null=True`, `blank=True`)
  - `distance_km` (`DecimalField`, `max_digits=6`, `decimal_places=2`, `null=True`, `blank=True`)
  - `delivery_fee_uzs` (`DecimalField`, `max_digits=12`, `decimal_places=0`, `null=True`, `blank=True`)
  - `final_total_uzs` (`DecimalField`, `max_digits=12`, `decimal_places=0`, `null=True`, `blank=True`)
- [x] `ServiceOrder.__str__` va `ServiceOrderAdmin` (`core/admin.py`) ni yangi maydonlar (`telegram_user`, `pending_location` badge, `distance_km`, `delivery_fee_uzs`, `final_total_uzs`) bilan yangilash.
- [x] `api_track_order` (`core/views.py`) da `pending_location` statusini qo'llab-quvvatlash va `final_total_uzs` (kuryer xizmati bilan birga) qiymatini to'g'ri qaytarish.

### 3.2. 1-variant — "O'zim boraman (Servis markaziga)" (`service_type == 'in_service'`)
- [x] `api_submit_order` (`core/views.py`):
  - `status='new'`, `final_total_uzs = comp_obj.total_price_uzs` (agar variant tanlangan bo'lsa) bilan `ServiceOrder` yaratish.
  - Barcha faol menejer va bosh adminlarga (`TELEGRAM_ADMIN_CHAT_ID` + `BotAdmin` `role__in=['manager', 'both']`) Telegram xabarini yuborish:
    - Buyurtma ID (`#MP-XXXXXX`), mijoz Telegram ismi, `@username`, bosiladigan profil havolasi (`https://t.me/...` yoki `tg://user?id=...`), telefon modeli, muammo/detal, zapchast narxi, xizmat formati (`O'zim boraman (Servis markaziga)`), hamda mavjud CRM inline tugmalari.
  - JSON javobida `service_type: 'in_service'`, `order_id`, va `shop_location` obyektini (`address: "Malika bozor, B32 do'kon"`, `lat: 41.338306`, `lon: 69.270389`, `google_maps_url`, `yandex_maps_url`) qaytarish.
- [x] Frontend (`templates/components/order_modal.html`, `static/js/modal.js`, `static/css/order_modal.css`):
  - Buyurtma tasdiqlangach forma o'rniga natija oynasini chiqarish (avtomatik yopilib ketmasligi kerak, foydalanuvchi o'zi yopadi).
  - Buyurtma raqami (`#MP-XXXXXX`), holatni kuzatish havolasi va **Servis Markazi Lokatsiya Kartasi**ni ko'rsatish:
    - Aniq manzil: **"Malika bozor, B32 do'kon"**
    - To'g'ridan-to'g'ri ochiladigan tugmalar: **Google Maps** (`https://www.google.com/maps/search/?api=1&query=41.338306,69.270389`) va **Yandex Maps** (`https://yandex.uz/maps/?pt=69.270389,41.338306&z=17&l=map`).

### 3.3. 2-variant — "Kuryer orqali olib ketish" (`service_type == 'courier'`)
- [x] **Sayt va Backend (`core/views.py`, `templates/components/order_modal.html`, `static/js/modal.js`):**
  - `api_submit_order` da bir martalik xavfsiz `courier_token = secrets.token_urlsafe(24)` yaratish (`courier_` + 32 belgi = 40 belgi `<= 64`).
  - Bazada `status='pending_location'`, `courier_token`, `courier_token_expires_at = now + 60 min`, `telegram_user`, `phone`, `comparison` bilan `ServiceOrder` saqlash (lokatsiya kelmaguncha adminga xabar yuborilmaydi).
  - Javobda `service_type: 'courier'`, `order_id`, `bot_url: https://t.me/<BOT_USERNAME>?start=courier_<token>` qaytarish.
  - Frontendda yangi oynada `bot_url` ni ochishga urinish + modal ichida (iOS Safari popup-blocker holati uchun ham 100% ishonchli) buyurtma raqami va yorqin **"📍 Botga o'tib lokatsiya yuborish"** (`<a target="_blank" rel="noopener">`) tugmasini ko'rsatish.

- [x] **Masofa va Kuryer Narxini Hisoblash Moduli (`core/distance.py`):**
  - `calculate_road_distance_km(client_lat: float, client_lon: float) -> tuple[float, str]`:
    - Boshlang'ich nuqta: `(settings.SHOP_LAT, settings.SHOP_LON)` = `(41.338306, 69.270389)`.
    - **Asosiy usul (OSRM):** `https://router.project-osrm.org/route/v1/driving/{shop_lon},{shop_lat};{client_lon},{client_lat}?overview=false` so'rovi (timeout: 5 soniya) → `routes[0]['distance'] / 1000.0` (source: `'osrm'`).
    - **Zaxira usul (Fallback):** OSRM xatolik bersa yoki javob bermasa, avtomatik ravishda `Haversine(shop, client) * 1.25` formulasi ishlaydi (source: `'haversine'`).
  - `calculate_courier_fee_uzs(distance_km: float) -> int`:
    - Aniq formula: `5000 + round(distance_km * 10000)`
    - Nazorat misoli: `2.5 km` → `5000 + round(2.5 * 10000) = 5000 + 25000 = 30 000 so'm`.

- [x] **Telegram Bot (`aiogram 3.x`) Kuryer Mantiqi (`bot/states/client_states.py`, `bot/handlers/client.py`, `bot/handlers/crm.py`):**
  - `CourierLocationStates.waiting_for_location` FSM holatini yaratish.
  - `@router.message(StateFilter("*"), CommandStart(deep_link=True, magic=F.args.startswith("courier_")))`:
    - Tokenni tekshirish (`status='pending_location'`, muddati o'tmagan, `order.telegram_user.telegram_id == message.from_user.id`).
    - Xatolik/begona foydalanuvchi holatida xavfsiz rad etish xabari.
    - Yaroqli bo'lsa: FSM ga `order_id` ni saqlash, mijozga saytda tanlangan telefon modeli, muammo/detal va zapchast narxini ko'rsatish hamda `ReplyKeyboardMarkup` (`KeyboardButton(text="📍 Hozirgi lokatsiyangizni yuborish", request_location=True)` + `"❌ Bekor qilish"`) tugmasini chiqarish.
  - `@router.message(CourierLocationStates.waiting_for_location, F.text == "❌ Bekor qilish")`:
    - Jarayonni bekor qilib FSM ni tozalash va `ReplyKeyboardRemove()` bilan klaviaturani olib tashlash.
  - `@router.message(CourierLocationStates.waiting_for_location, F.location)`:
    - `core/distance.py` orqali `distance_km` va `delivery_fee_uzs` ni (async thread ichida, bot loopini bloklamasdan) hisoblash.
    - `final_total_uzs = part_price_total + delivery_fee_uzs` ni hisoblash.
    - `ServiceOrder` ni yangilash: `latitude`, `longitude`, `distance_km`, `delivery_fee_uzs`, `final_total_uzs`, `status='new'`, `courier_token=None` (bir martalik tokenni bekor qilish).
    - **Adminga / Menejerlarga yuborish:**
      1. Batafsil buyurtma xabari (*"📍 Shu yerdan olib ketasiz"*, mijoz Telegram profili va `@username`/havola, telefon modeli, muammo/detal, zapchast narxi, masofa `km`, kuryer narxi, **jami summa**, mijoz lokatsiyasiga Google Maps va Yandex Maps havolalari) + CRM inline tugmalari (`build_order_action_kb`).
      2. Alohida `bot.send_location(chat_id=aid, latitude=lat, longitude=lon)` lokatsiya pin yuborish.
    - **Mijozga yakuniy chek yuborish:**
      - `ReplyKeyboardRemove()` bilan klaviaturani olib tashlash.
      - Yakuniy chek matni: Buyurtma ID, telefon/detal, Zapchast narxi + Kuryer xizmati (`km` ko'rsatilgan holda) = **Jami summa**.
  - `bot/handlers/crm.py` da `format_order_card(order)` va qidiruvni yangilash:
    - Telegram foydalanuvchi profili (`@username` / link), kuryer masofasi (`km`), kuryer narxi, jami summa, mijoz lokatsiya havolalari va `pending_location` holati to'g'ri ko'rinishi.

---

## 4-bosqich: Yakuniy Tekshiruv, Migratsiyalar va Responsivlik

### 4.1. Stil, Cache-Busting va Responsivlik Tekshiruvi
- [x] Barcha yangi UI qismlari (Login modal, Topbar/Sidebar profil bloki, Malika bozor lokatsiya kartasi, Kuryer botga o'tish bloki) faqat `static/css/` tashqi fayllarida yozilganini va HTML shablonlarda inline `style=` / `<style>` yo'qligini tekshirish.
- [x] `static/css/style.css` ga `@import 'auth_modal.css';` qo'shish.
- [x] `templates/base.html` dagi barcha CSS linklar versiyasini `?v=3.2` dan **`?v=5`** ga yangilash (va yangi `auth_modal.css?v=5`, `auth.js?v=5` ni ulash).
- [x] PC (`1440px`, `1024px`), iOS Safari (`390px`, `375px`), Android Chrome (`360px`, `412px`) va kichik ekran (`320px`) o'lchamlari bo'yicha:
  - `16px` input/select shrifti,
  - `100dvh` va `safe-area-inset-*` modal chetlari,
  - `0%` gorizontal overflow,
  - Topbarda bitta til tanlagich + Auth tugmasi/profil bloki sig'ishini tekshirish.

### 4.2. Tarjimalar (i18n) va Django Teglari Tekshiruvi
- [x] Barcha shablonlarda `{% load static i18n %}`, `{% url %}`, `{% static %}`, `{% csrf_token %}`, `{% trans %}`, `{% blocktrans %}` saqlangani va barcha yangi matnlar tarjima teglarida yozilganini tekshirish.
- [x] `locale/uz/`, `locale/ru/`, `locale/en/` uchun `.po` tarjima fayllarini yaratish/yangilash va `.mo` fayllarga kompilyatsiya qilish (`manage.py compilemessages` yoki Python kompilyatori bilan).

### 4.3. Django Migratsiyalari, Check va Avtomatik Testlar
- [x] Django migratsiyalarini yaratish va qo'llash (faqat tasdiqlangandan keyingi bosqichda bajariladi):
  - `python manage.py makemigrations core`
  - `python manage.py migrate`
- [x] `python manage.py check` buyrug'ini xatosiz o'tkazish.
- [x] `bot/` barcha modullari sintaksisi va importlarini (`bot.main`, `bot.handlers.client`, `bot.handlers.start`, `bot.handlers.crm`, `core.distance`, `core.telegram_auth`) xatosiz tekshirish.
- [x] `core/tests.py` ga unit testlar yozish va `python manage.py test core` ni ishga tushirish:
  - Telegram Login Widget HMAC-SHA256 valid/invalid/expired `auth_date` tekshiruvi.
  - Deep-Link `AuthToken` yaratish, botda `ReplyKeyboard` (`request_contact=True`) orqali 100% haqiqiy o'z telefon raqamini qat'iy tasdiqlash (qo'lda kiritish, boshqa odam kontakti, vCard va forward rad etilishi), polling, bir martalik ishlatilish va muddati o'tishi.
  - Login qilmasdan `api_submit_order` va `api_submit_review` chaqirilganda `401 Unauthorized` qaytishi.
  - `call_master` rad etilishi va faqat `in_service` hamda `courier` ishlashi.
  - `in_service` buyurtmada `Malika bozor, B32 do'kon` + Google/Yandex Maps (`pt=69.270389,41.338306`) havolalari qaytishi va tasdiqlangan telefon raqami saqlanishi.
  - `courier` buyurtmada `pending_location` yaratilishi, masofa hisoblash (OSRM va `Haversine * 1.25` fallback) va narx formulasi (`2.5 km` → `30 000 so'm`, `final_total = zapchast + kuryer`).
- [x] `.env`, `.venv/`, `backups/`, `media/` ga hech qanday o'zgartirish kiritilmaganini `git status` orqali tasdiqlash.

