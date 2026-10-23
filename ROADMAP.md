# 📱 MOBIPRICE — PROFESSIONAL SMARTPHONE REPAIR & CATALOG PLATFORM
## 🚀 Loyiha Yo‘l Xaritasi va Texnik Arxitekturasi (Roadmap)

> **Loyiha maqsadi:** Telefon buzilganda bozorga bormasdan turib, har qanday model uchun ehtiyot qismlar narxini (Original vs Kopiya farqi, ombordagi qoldig‘i bilan) bilish, ta'mirlashga buyurtma berish va professional servis xizmatini taklif qiluvchi yuqori yuklamali (High-Load), 3 tilli portal hamda Telegram Admin Bot ekotizimi.

---

## 🧭 ASOSIY ARXITEKTURA VA BIZNES QOIDALARI

1. **5-Bosqichli Katalog Ierarxiyasi:**
   - **1-Qadam: Brend (`Brand`)** — Apple, Samsung, Xiaomi, Honor... (SVG logo bilan).
   - **2-Qadam: Model Seriyasi (`DeviceSeries`)** — Masalan: `Pro Model`, `Pro Max Model`, `S Seriya`, `A Seriya`, `Redmi Note`...
   - **3-Qadam: Telefon (`DevicePhone`)** — Aniq telefon nomi va rasmi (masalan: `iPhone 16 Pro Max`, `Galaxy S25 Ultra`...).
   - **4-Qadam: Muammo / Detal (`DeviceIssue`)** — 30 ta professional vektor SVG ikonka + 1 ta o‘zbekcha nom kiritilganda avtomatik Ruscha va Inglizcha tillariga tarjima qilinishi.
   - **5-Qadam: Solishtirish / Narx (`IssueComparison`)** — Soddalashtirilgan taqqoslash: Faqatgina **Original** yoki **Kopiya**, narxi (so‘mda) va ombordagi soni (**Quantity** — mavjud / tugagan). *Ortiqcha kafolat, ta'mirlash vaqti va usta haqqi kabi chalkash ma'lumotlar olib tashlangan.*

2. **Telegram Admin Bot Standartlari:**
   - Aiogram 3.x FSM (Finite State Machine) asosida.
   - Faqat xavfsiz Admin IDlar ro‘yxati (`ADMIN_IDS`) orqali kirish.
   - **Klaviatura ergonomikasi:** Har bir qatorda maksimal **3 tadan** tugma (`build_3_row_reply_kb`, `build_3_row_inline_kb`).
   - To‘liq CRUD (Yaratish, Ko‘rish, Tahrirlash, O‘chirish) barcha 5 ta bo‘lim uchun.

3. **3 Tilli Tizim (i18n):**
   - Sayt va API 3 tilda ishlaydi: O‘zbekcha (`/uz/`), Ruscha (`/ru/`), Inglizcha (`/en/`).
   - Admin botda faqat 1 ta — O‘zbek tilida kiritadi, muammo nomlari avtomatik tarjima qilinadi.

---

## 🛠 TEXNOLOGIK STEK (TECH STACK)

- **Backend:** Python 3.12+ / Django 5.1+ (ORM, Asinxron funksiyalar, i18n).
- **Telegram Bot:** Aiogram 3.17+ (FSM, Polling/Webhook, Custom Keyboards).
- **Frontend:** Vanilla CSS / JavaScript (No bulky frameworks), Dark Mode, Glassmorphism, Responsive Mobile-First.
- **Ma'lumotlar Bazasi:** PostgreSQL 16 (Production) / SQLite3 (Mahalliy ishlab chiqish).
- **Kesh & Xabarlar:** Redis + Celery.
- **Konteynerlashtirish:** Docker & Docker Compose (web, db, bot).
- **Web Server:** Nginx + Gunicorn + Certbot SSL.

---

## 📋 BOSQICHLAR VA AMALGA OSHIRISH REJASI

### 1-BOSQICH: TIZIM ARXITEKTURASI VA INFRATUZILMA
- [x] Django loyihasi yaratildi, app strukturasi (`core`, `bot`) sozlandi.
- [x] Ko‘p tillilik sozlamalari (`uz`, `ru`, `en`) va `django-modeltranslation` / i18n arxitekturasi ulandi.
- [x] Statik fayllar va media fayllar yo‘llari (`media/brands/`, `media/phones/`, `static/img/icons/`) sozlandi.
- [x] `Dockerfile` va `docker-compose.yml` (PostgreSQL 16, Django Web, Telegram Bot servislar bilan) tayyorlandi.
- [x] Makefile va muhit boshqaruv skriptlari yaratildi.

---

### 2-BOSQICH: 5-QADAMLI MA'LUMOTLAR BAZASI STRUKTURASI
- [x] **1. Brendlar modeli (`Brand`):** Nomi, slug, SVG logo kodi, rasm, tartib raqami, aktivlik holati.
- [x] **2. Model Seriyalari modeli (`DeviceSeries`):** `ForeignKey -> Brand`, seriya nomi, slug, tartibi (`unique_together=('brand', 'name')`).
- [x] **3. Telefonlar modeli (`DevicePhone`):** `ForeignKey -> DeviceSeries`, telefon nomi, unikal avto-slug (to‘qnashuvlarni `name-1`, `name-2` qilib hal qiluvchi), rasm maydoni (`phones/`), chiqqan yili.
- [x] **4. Muammolar modeli (`DeviceIssue`):** `ForeignKey -> DevicePhone`, o‘zbekcha nomi (`title`), ruscha nomi (`title_ru`), inglizcha nomi (`title_en`), 30 ta ikonka raqami (`icon_number`), SVG ikonka kodi (`icon_svg`).
- [x] **5. Sifat va Narxlar modeli (`IssueComparison`):** `ForeignKey -> DeviceIssue`, sifati (`original` / `kopiya`), sarlavha, narxi so‘mda (`part_price_uzs`), USD ekvivalenti (`price_usd`), ombordagi soni (`quantity`), ombor holati (`is_in_stock`).
- [x] **Yordamchi modellar:**
  - `RepairFAQ`: Ko‘p beriladigan savol-javoblar (3 tilda).
  - `Review`: Mijoz sharhlari va ta'mirdan "Oldin / Keyin" (`before_image`, `after_image`) fotolari.
  - `ServiceOrder`: Unikal `#ORD-XXXX` trek-kodli buyurtmalar modeli.
- [x] Barcha modellar uchun Django migratsiyalari yaratildi va bazaga muvaffaqiyatli tatbiq qilindi (`0001_initial`, `0002_...`, `0003_...`).

---

### 3-BOSQICH: AIOGRAM 3 TELEGRAM ADMIN BOT PANELI
- [x] Admin avtorizatsiyasi: faqat ruxsat etilgan Admin IDlar (`ADMIN_IDS`) orqali boshqaruv.
- [x] Qulay Dashboard klaviaturasi: `📂 Brendlar`, `📁 Modellar`, `📱 Telefonlar`, `🔧 Muammolar`, `💰 Narxlar`, `📊 Statistika`.
- [x] **Qatorda maksimal 3 ta tugma** ergonomika qoidasi barcha Reply va Inline tugmalarga joriy etildi.
- [x] **1-Bo‘lim: Brendlar CRUD:**
  - Ro‘yxat ko‘rish, yangi brend qo‘shish (nomi + `.svg` logotip fayli), tahrirlash (nom va logo), o‘chirish.
- [x] **2-Bo‘lim: Modellar (Seriyalar) CRUD:**
  - Brend tanlash -> Seriya nomini kiritish, ro‘yxat, tahrirlash, o‘chirish.
- [x] **3-Bo‘lim: Telefonlar CRUD:**
  - Brend tanlash -> Seriya tanlash -> Telefon nomini kiritish -> JPG/PNG rasmini yuklash (rasm yoki fayl ko‘rinishida).
  - Ro‘yxat ko‘rish, nomini va rasmini alohida tahrirlash, o‘chirish.
  - Asinxron xavfsiz DB yuklanishi (`select_related`) va rasmlar xavfsiz saqlanishi.
- [x] **4-Bo‘lim: Muammolar CRUD va Avtomatik Tarjima:**
  - Brend -> Seriya -> Telefon tanlash.
  - O‘zbekcha nom kiritilganda avtomatik Ruscha va Inglizcha tarjimalarni yaratish (`bot/utils/translator.py`).
  - 30 ta vektorli SVG ikonka generatsiyasi va botda ko‘rsatiladigan 6x5 neonli cheatsheet infografika rasmi (`bot/assets/icons_cheatsheet.png`).
  - Ikonka raqamini (1-30) tanlash va SVG kodini bazaga yozish, tahrirlash, o‘chirish.
- [x] **5-Bo‘lim: Soddalashtirilgan Narxlar CRUD:**
  - Brend -> Seriya -> Telefon -> Muammoni tanlash.
  - Sifat turini tanlash: `🟢 Original` yoki `🟡 Sifatli Kopiya`.
  - Narxini kiritish (so‘mda).
  - Ombordagi qoldiq miqdorini kiritish (`quantity` — masalan: 5 yoki 0).
  - Narx va miqdorni tahrirlash, o‘chirish.

---

### 4-BOSQICH: MIJOZ INTERFEYSI (UI/UX) VA 5-QADAMLI KALKULYATOR
- [x] **Premium Dark Mode Dizayn:** Glassmorphism neon aksentlar, yuqori kontrastli zamonaviy tipografika, 100% mobil moslashuvchanlik.
- [x] **Interaktiv 5-Bosqichli Kalkulyator:**
  - 1-Qadam: Brend tanlash (Apple, Samsung, Xiaomi...).
  - 2-Qadam: Model Seriyasi tanlash (S seriya, A seriya, Pro seriya...).
  - 3-Qadam: Aniq telefonni tanlash (suratlari bilan).
  - 4-Qadam: Muammoni tanlash (30 ta aniq SVG ikonkalari bilan).
  - 5-Qadam: Solishtirish natijasi: Original vs Kopiya, Narxi, Omborda mavjudlik holati (`🟢 Omborda: X ta` yoki `🔴 Mavjud emas (Kutilmoqda)`).
- [x] **Interaktiv "Oldin va Keyin" (Before / After Slider):**
  - Foydalanuvchi sensorli ekranda yoki sichqoncha bilan siljitib ta'mirdan oldingi va keyingi holatni taqqoslay oladi.
- [x] **FAQ va Mijoz Sharhlari:**
  - Dinamik tez-tez beriladigan savollar akkordeoni va mijozlar fikrlari bloki.
- [x] **Til almashtirish interfeysi:** Sayt sarlavhasida `UZ | RU | EN` tillarini bir zumda almashtirish.
- [x] **Buyurtma berish modali:**
  - Mijoz o‘z ismi va telefon raqamini kiritib ariza qoldirishi mumkin bo‘lgan tezkor forma.
- [ ] **Jonli Model Qidiruvi (Live Search):**
  - Qidiruv qatoriga yozish bilan bir zumda telefon modellarini topib, to‘g‘ridan-to‘g‘ri kalkulyatorga yo‘naltirish.
- [ ] **"Telefonim holatini tekshirish" (Trek tekshirish UI & API):**
  - Mijoz o‘zining `#ORD-XXXX` kodi orqali saytdan telefon qaysi bosqichda ekanligini (Diagnostika, Qismlar kutilmoqda, Tuzatildi, Olib ketishga tayyor) bilishi.

---

### 5-BOSQICH: BUYURTMALAR EKOTIZIMI VA TELEGRAM CRM
- [ ] **Saytdan yangi buyurtma tushganda Telegram Botga / Guruhga xabar:**
  ```
  🚨 YANGI TA'MIRLASH BUYURTMASI! #ORD-1042
  👤 Mijoz: Alisher Karimov
  📞 Telefon: +998 90 123 45 67
  📱 Model: Samsung Galaxy S25 Ultra
  🔧 Muammo: Ekran almashtirish
  💎 Tanlangan detal: Original Service Pack
  💵 Narxi: 1,850,000 so‘m
  📦 Holati: Omborda mavjud
  ```
- [ ] **Bot orqali arizani tezkor boshqarish:**
  - Xabar tagidagi inline tugmalar: `[✅ Qabul qilish]` | `[👨‍🔧 Ustaga biriktirish]` | `[📞 Qo‘ng‘iroq qilindi]` | `[❌ Bekor qilish]`.
- [ ] **Buyurtmalar Mini-CRM interfeysi:**
  - Saytdan tushgan arizalar ro‘yxati, ustalar hisobi va holatni o‘zgartirish mexanizmi.
- [ ] **Mijozga avtomatik SMS / Telegram bildirishnoma (Ixtiyoriy):**
  - Arizangiz qabul qilindi, telefoningiz tayyor bo‘ldi kabi xabarnomalar.

---

### 6-BOSQICH: OMMAVIY MA'LUMOT BOSHQARUVI (EXCEL IMPORT / EXPORT)
- [ ] **Excel / CSV orqali ommaviy yuklash (Bulk Import):**
  - Yuzlab telefonlar, seriyalar va ehtiyot qismlar narxlarini 1 ta Excel fayli orqali bazaga avtomatik kiritish.
- [ ] **Excel orqali eksport va narxlarni yoppasiga yangilash:**
  - Hamma narxlarni Excel jadval ko‘rinishida yuklab olish va o‘zgartirib qayta yuklash imkoniyati.

---

### 7-BOSQICH: YUQORI YUKLAMA (HIGH-LOAD 10,000+), KESH VA XAVFSIZLIK
- [ ] **Redis Kesh:**
  - Katalog ma'lumotlarini (Brendlar, Seriyalar, Telefonlar va Narxlar) Redis xotirasida saqlash (so‘rovlar tezligini < 5ms darajasiga yetkazish).
- [ ] **PostgreSQL Indexing & Optimization:**
  - Qidiruv va tanlovlar bo‘yicha indekslarni chuqur optimallashtirish (`db_index=True`, `select_related`).
- [ ] **Spam va Hujumlardan Himoya (Rate Limiting):**
  - Buyurtma formasiga 1 ta IP manzildan daqiqasiga 2 tadan ortiq so‘rov yuborishni cheklash (Anti-spam protection).
  - CSRF va XSS himoyasi.

---

### 8-BOSQICH: SEO VA QIDIRUV TIZIMLARIDA PESHQADAMLIK
- [ ] Har bir model va muammo uchun avtomatik generatsiya qilinadigan SEO meta-teglar (Title, Meta Description, OpenGraph).
- [ ] Dinamik `sitemap.xml` va `robots.txt` generatsiyasi.
- [ ] **Schema.org mikroformati:** Google qidiruv natijalarida to‘g‘ridan-to‘g‘ri yulduzchalar (reyting) va ta'mirlash narxi ko‘rinib turishi uchun `Product` / `Service` JSON-LD formatini integratsiya qilish.

---

### 9-BOSQICH: DOCKER PRODUCTION DEPLOY VA MONITORING
- [ ] **Production Docker Compose:**
  - `web` konteyneri (Gunicorn production serveri).
  - `db` konteyneri (PostgreSQL 16 doimiy docker volumes bilan).
  - `redis` konteyneri.
  - `bot` konteyneri (Aiogram fon jarayoni).
  - `nginx` konteyneri (Statik fayllar keshlanishi, Gzip kompressiya, SSL terminatsiyasi).
- [ ] **Let's Encrypt SSL/HTTPS:**
  - Domen uchun Certbot orqali avtomatik yangilanuvchi bepul xavfsiz SSL sertifikati.
- [ ] **Avtomatik Backup (Zaxiralash):**
  - Har kechasi PostgreSQL ma'lumotlar bazasining to‘liq nusxasini (dump) olib, maxfiy zaxira joyiga saqlash cron skripti.
- [ ] **Avtomatik qayta tiklanish (Healthcheck & Restart policies):**
  - Server o‘chib yonganda barcha konteynerlarning avtomatik ishga tushishi (`restart: unless-stopped`).

---

## 📊 HOZIRGI HOLAT XULOSASI (STATUS OVERVIEW)

| Bo‘lim | Holati | Izoh |
| :--- | :--- | :--- |
| **5-Bosqichli Baza Modeli** | ✅ **Bajarildi (100%)** | `Brand` -> `Series` -> `Phone` -> `Issue` -> `Comparison` to‘liq tayyor |
| **Aiogram 3 Admin Bot** | ✅ **Bajarildi (100%)** | 5 ta bo‘lim uchun to‘liq CRUD, 30 ta SVG ikonka, avto-tarjima, 3-tugmali menyu |
| **Kalkulyator UI (Web)** | ✅ **Bajarildi (95%)** | 5 ta bosqich, Before/After slider, Dark UI, 3 ta til faol |
| **Telegram Xabarnomalar** | ⏳ **Keyingi navbatda** | Saytdan tushgan buyurtmani botga / guruhga uzatish |
| **Trek Tekshirish (Track Order)** | ⏳ **Keyingi navbatda** | Saytda `#ORD-XXXX` kodi bilan status ko‘rish |
| **Excel Import / Export** | ⏳ **Rejada** | Ommaviy ma'lumot kiritish |
| **Redis Kesh & High-Load** | ⏳ **Rejada** | 10,000+ so‘rovlar uchun optimizatsiya |
| **Production Deploy** | ⏳ **Rejada** | Nginx, SSL, Postgres Volume va Serverga o‘rnatish |