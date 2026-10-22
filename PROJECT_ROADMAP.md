# 📱 SMART PHONE REPAIR & SPARE PARTS PLATFORM
## Katta Ko‘lamli (Production) Loyiha Yo‘l Xaritasi va Texnik Arxitekturasi (Roadmap)

> **Loyiha maqsadi:** Telefon buzilganda bozorga bormasdan turib, har qanday model uchun ehtiyot qismlar narxini (Original vs Kopiyalar farqi, kafolati bilan) bilish, ta'mirlashga buyurtma berish va professional servis xizmatini taklif qiluvchi yuqori yuklamali (High-Load), 3 tilli portal.

---

## 📑 MUNDARIJA
1. [Loyiha Texnologik Staki (Tech Stack)](#1-loyiha-texnologik-staki)
2. [1-Bosqich: Tizim Arxitekturasi va Dastlabki Sozlash](#1-bosqich-tizim-arxitekturasi-va-sozlash)
3. [2-Bosqich: Ma'lumotlar Bazasi Strukturasi (Database Modeling)](#2-bosqich-malumotlar-bazasi-strukturasi)
4. [3-Bosqich: Admin Panel va Maxsus CRM Tizimi](#3-bosqich-admin-panel-va-crm)
5. [4-Bosqich: Mijoz Interfeysi (UI/UX) va Interaktiv Funksiyalar](#4-bosqich-mijoz-interfeysi-va-uiux)
6. [5-Bosqich: Telegram Bot va Xabarnomalar Ekotizimi](#5-bosqich-telegram-bot-va-xabarnomalar)
7. [6-Bosqich: 3 Tilli (Multilingual) Tizim va SEO Strategiyasi](#6-bosqich-3-tilli-tizim-va-seo)
8. [7-Bosqich: Yuqori Yuklama (High-Load 10,000+), Kesh va Xavfsizlik](#7-bosqich-yuqori-yuklama-va-xavfsizlik)
9. [8-Bosqich: Docker, Serverga Joylash (Deploy) va Zaxira Nusxalash](#8-bosqich-deploy-va-monitoring)

---

## 1. LOYIHA TEXNOLOGIK STAKI
- **Asosiy Backend:** Python 3.12+ / Django 5.x (ishonchli, kengayuvchan, xavfsiz).
- **REST API:** Django REST Framework (kelajakda mobil ilova va bot uchun).
- **Asosiy Ma'lumotlar Bazasi:** PostgreSQL (tranzaksiyalar, qidiruv indekslari uchun).
- **Kesh va Navbatlar (Message Broker):** Redis + Celery (kataloglarni tezkor yuklash, bot xabarlarini navbatda yuborish).
- **Frontend / UI:** Zamonaviy Dark Theme, CSS Grid/Flexbox, Vanilla JS / Fetch API (sahifa yangilanmasdan ishlovchi SPA effektlari).
- **Konteynerlashtirish:** Docker & Docker Compose.
- **Veb-server & Proksi:** Nginx + Gunicorn + Certbot (SSL/HTTPS).

---

## 2. 1-BOSQICH: TIZIM ARXITEKTURASI VA SOZLASH
- [ ] **Loyiha muhitini yaratish:** Docker va Docker Compose konfiguratsiyasi (`web`, `db`, `redis`, `celery`, `nginx`).
- [ ] **Django Apps arxitekturasi:**
  - `core` — umumiy sozlamalar, bosh sahifa, statik modullar.
  - `catalog` — brendlar, modellar, zapchast turlari, sifat variantlari (Original/Kopiya).
  - `orders` — mijoz arizalari, narx kalkulyatsiyasi, statusni tekshirish tizimi.
  - `knowledge` — FAQ (Nega batareya shishadi?, Nega original qimmat?), tushuntirish maqolalari.
  - `reviews` — sharhlar va "Oldin / Keyin" (Before/After) fotogalereyasi.
  - `bot` — Telegram orqali xodimlarni xabardor qilish webhook moduli.

---

## 3. 2-BOSQICH: MA'LUMOTLAR BAZASI STRUKTURASI
Bazani kelajakda minglab modellar va ehtiyot qismlarni sig‘dira oladigan qilib loyihalashtirish:

1. **Brendlar (`Brand`):**
   - Nomi (`Apple`, `Samsung`, `Xiaomi`, `Honor`, `Huawei`...)
   - Logotip, slug, tartib raqami, aktivlik holati.
2. **Qurilma Modellari (`DeviceModel`):**
   - Brend bilan bog‘liqlik (`ForeignKey -> Brand`).
   - Model nomi (`iPhone 16 Pro Max`, `Galaxy S24 Ultra`, `Redmi Note 13 Pro`...)
   - Chiqqan yili, modeli kodi (masalan, `A3084`), asosiy rasm.
   - Tezkor qidiruv indekslari.
3. **Ehtiyot Qism Kategoriyalari (`PartCategory`):**
   - Kategoriya nomi: `Ekran (Displey)`, `Orqa oyna (Kopust/Krishka)`, `Batareya (Akkumulyator)`, `Kamera oynasi`, `Zaryadka porti`, `Dinamik`, `Plata ta'miri`.
   - Ikonkasi va qisqa tavsifi.
4. **Sifat Variantlari va Narxlar (`PartOption`):**
   - Model va Kategoriya bilan bog‘liqlik.
   - Sifat darajasi:
     - `1. Original Service Pack` (100% zavod)
     - `2. Original Donar` (Boshqa telefondan yechib olingan ideal holatda)
     - `3. OLED GX / ZY` (Originalga eng yaqin sifatli dublikat)
     - `4. Incell / TFT` (Hamyonbop variant)
   - Narx (zapchast narxi + usta o‘rnatib berish haqqi).
   - Kafolat muddati (`6 oy`, `3 oy`, `1 oy`, `Kafolatsiz`).
   - Ta'mirlash muddati (`30 daqiqa`, `1 soat`, `1 kun`).
   - Tavsif va Farqlar: "Originalda nima bor, kopiyasida nima yo‘q?".
   - Solishtirish rasmlari (Taqqoslash uchun).
   - Ombor holati (`Mavjud`, `Zakazga 1 kun`, `Tugagan`).
5. **Bilimlar Bazasi / FAQ (`RepairFAQ`):**
   - Qaysi qismga tegishliligi (Batareya, Ekran...).
   - Savol: *"Nega batareya shishadi?"*, *"Nega original ekran qimmat?"*.
   - Batafsil professional javob va tushuntiruvchi rasm/video havola.
6. **Mijoz Sharhlari va Before/After (`Review`):**
   - Mijoz ismi, ta'mirlangan telefon modeli va qilingan ish.
   - Reyting (1 dan 5 gacha).
   - Mijoz izohi.
   - Ta'mirdan oldingi rasm (`before_image`) va Ta'mirdan keyingi rasm (`after_image`).
   - Tasdiqlangan holat (Admin tekshiruvidan so‘ng saytda ko‘rinadi).
7. **Arizalar / Buyurtmalar (`ServiceOrder`):**
   - Unikal Trek-kod (Masalan: `#ORD-7894`).
   - Mijoz ismi va Telefon raqami.
   - Tanlangan Model va Detal varianti.
   - Xizmat formati: `Filialga kelish`, `Usta chaqirish`, `Kuryer orqali yuborish`.
   - Buyurtma holati: `Yangi` -> `Qabul qilindi` -> `Usta ta'mirlamoqda` -> `Tayyor` -> `Topshirildi` -> `Bekor qilindi`.
   - Admin va usta uchun ichki izohlar.

---

## 4. 3-BOSQICH: ADMIN PANEL VA CRM
- [ ] **Brendlangan qulay Admin Panel:**
  - O‘zbek, rus tillarida qulay boshqaruv.
  - Excel orqali yuzlab modellarni bir marta yuklash (Bulk Import/Export).
  - Narxlarni bir zumda yangilash (foizda yoki qo‘lda oshirish/tushirish).
- [ ] **Buyurtmalar Kanbani (Mini-CRM):**
  - Yangi kelgan arizalarni bosqichma-bosqich o‘tkazish (Drag & Drop yoki status o‘zgartirish).
  - Ustalarni biriktirish (Qaysi usta qaysi telefonni ta'mirlayotgani hisobi).

---

## 5. 4-BOSQICH: MIJOZ INTERFEYSI (UI/UX) VA FUNKSIYALAR
- [ ] **Dizayn Konsepsiyasi:**
  - Zamonaviy "Chorniy" (Dark Mode) premium ko‘rinish.
  - Shishasimon (Glassmorphism) kartochkalar, yuqori kontrastli shriftlar.
  - Telefon ekranlariga 100% moslashgan (Mobile-First responsive).
- [ ] **Asosiy Bloklar:**
  1. **Header:** Logotip, 3 ta til tugmasi (`UZ` | `RU` | `EN`), "Telefonim holatini tekshirish", Tezkor qo‘ng‘iroq / Telegram havolasi.
  2. **Hero & Smart Live Search:** Telefon modelini qidiruvga yozish bilan bir zumda takliflar chiqishi (`iPhone 16...`).
  3. **Interaktiv Qadamma-qadam Kalkulyator (Wizard):**
     - *1-qadam:* Brendni tanlash (Apple, Samsung, Xiaomi...).
     - *2-qadam:* Modelni tanlash (Rasmlari bilan ro‘yxat).
     - *3-qadam:* Muammo / Detalni tanlash (Ekran, Orqa oyna, Batareya...).
     - *4-qadam:* Natija: Sifat variantlari taqqoslash jadvali (Original vs Kopiyalar yonma-yon).
  4. **Vizual Solishtiruvchi Karta:**
     - Narx, Kafolat, Ta'mirlash tezligi va Farqlari.
  5. **Interaktiv "Oldin va Keyin" (Before / After Slider):**
     - Foydalanuvchi barmog‘i bilan surib, singan telefon qanday tiklanganini ko‘ra oladi.
  6. **"Ekspert maslahati" (FAQ Akkordeon):**
     - Odamlarni eng ko‘p qiziqtirgan savollar (Nega batareya shishadi?, Qaysi ekranni tanlagan ma'qul?).
  7. **Buyurtma berish modali:**
     - Telefon raqam kiritish -> Telegramga lahzada tushishi.
  8. **"Telefonim qayerda?" (Trek tekshirish):**
     - Mijoz telefonini topshirgach, unga berilgan ID orqali saytga kirib: *"Telefoningiz hozir diagnostikada"* yoki *"Tuzatildi, olib ketishingiz mumkin"* holatini ko‘ra oladi.

---

## 6. 5-BOSQICH: TELEGRAM BOT VA XABARNOMALAR
- [ ] **Admin va Ustalar Guruhiga Bot:**
  - Saytdan har qanday ariza tushishi bilan 1 soniyada xabar:
    ```
    🚨 YANGI BUYURTMA! #ORD-1042
    👤 Mijoz: Alisher Karimov
    📞 Tel: +998 90 123 45 67
    📱 Model: iPhone 16 Pro Max
    🔧 Xizmat: Orqa oyna almashtirish
    💎 Tanlangan sifat: Original Zavod ($120)
    ⏱ Kafolat: 6 oy
    ```
  - Xabar tagida tugmalar: `[Qabul qilish]` | `[Mijozga qo'ng'iroq qilindi]` | `[Bekor qilish]`.
- [ ] **Mijozga SMS / Telegram Bildirishnoma (Ixtiyoriy kengaytmalar):**
  - "Sizning arizangiz qabul qilindi. Usta tez orada bog‘lanadi".

---

## 7. 6-BOSQICH: 3 TILLI TIZIM VA SEO (QIDIRUV TIZIMLARIDA 1-O‘RIN)
- [ ] **Ko‘p tillilik (i18n):**
  - O‘zbekcha (`/uz/`), Ruscha (`/ru/`), Inglizcha (`/en/`).
  - Dinamik ma'lumotlar (zapchast nomlari, tavsiflar) 3 tilda kiritilishi.
- [ ] **SEO Avtomatizatsiyasi (Biznesga tekin mijozlar oqimi):**
  - Har bir model va zapchast uchun avtomatik generatsiya bo‘ladigan meta-teglar:
    - *Title:* "iPhone 16 Pro Max ekran almashtirish narxi Toshkentda | Murod Service"
    - *Description:* "iPhone 16 Pro Max original va sifatli kopiya ekranlari narxi, 6 oylik kafolat, 30 daqiqada o‘rnatib berish."
  - Google va Yandex uchun `sitemap.xml` va `robots.txt` sozlash.
  - Schema.org (Product / Service mikroformati) — Google qidiruvida yulduzchalar va narxlar to‘g‘ridan-to‘g‘ri ko‘rinishi uchun.

---

## 8. 7-BOSQICH: YUQORI YUKLAMA (HIGH-LOAD 10,000+), KESH VA XAVFSIZLIK
- [ ] **Redis Kesh:**
  - Brendlar, modellar, zapchast narxlari Redis xotirasida saqlanadi. 10,000 ta mijoz bir vaqtda kirsa ham baza qiynalmaydi (so‘rovlar 0.005 soniyada chiqadi).
- [ ] **PostgreSQL Optimallashtirish:**
  - Model nomlari, brendlar bo‘yicha indekslar (`db_index=True`).
- [ ] **Spam va Hujumlardan Himoya:**
  - Ariza yuborishda Rate Limiting (1 ta IP dan 1 daqiqada faqat 2 ta so‘rov).
  - Cloudflare Turnstile yoki reCAPTCHA integratsiyasi.
  - CSRF va XSS himoyasi.

---

## 9. 8-BOSQICH: DOCKER, SERVERGA JOYLASH (DEPLOY) VA ZAXIRA
- [ ] **Docker Compose Prod Konfiguratsiyasi:**
  - `web` (Django Gunicorn bilan).
  - `postgres` (Ma'lumotlar doimiy `volumes`da saqlanadi).
  - `redis` (Kesh va navbatlar uchun).
  - `nginx` (Statik fayllar, SSL sertifikat, kompressiya Gzip/Brotli).
- [ ] **Avtomatik Zaxira (Backup):**
  - Har kechasi ma'lumotlar bazasining zaxira nusxasini (dump) olib, xavfsiz joyga (yoki maxfiy Telegram kanalga) yuborish cron-skripti.
- [ ] **Monitoring:**
  - Serverning xotirasi va holatini kuzatuvchi sodda monitoring.

---

## 🚀 AMALGA OSHIRISH KETMA-KETLIGI (HARAKAT REJASI)

| Bosqich | Vazifa | Muddat (Taxminiy) |
| :--- | :--- | :--- |
| **Sprint 1** | Django, Docker, 3 ta til, Baza modellari va Demo ma'lumotlar (Seed) | 2-3 kun |
| **Sprint 2** | Dark Mode interfeysi, Kalkulyator Wizard, Before/After slayderi | 3-4 kun |
| **Sprint 3** | FAQ moduli, Otzivlar, Buyurtma formasi, Telegram Bot | 2-3 kun |
| **Sprint 4** | Trek tekshirish, Admin CRM sozlash, Excel orqali ma'lumot to‘ldirish | 2-3 kun |
| **Sprint 5** | Redis kesh, SEO optimallashtirish, Serverga deploy qilish | 2 kun |

---
*Ushbu hujjat loyiha uchun to‘liq texnik ko‘rsatma (specification) hisoblanadi.*
