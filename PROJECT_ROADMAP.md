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

3. **Infratuzilma Soddaligi (No Docker, No PostgreSQL):**
   - **Baza:** Barcha muhitlar uchun yagona, qulay va yengil **`db.sqlite3`** (WAL rejimi bilan).
   - **Serverda ishga tushirish:** Linux'ning o‘zida oddiy va barqaror **`systemd` servislari** (`.service`) orqali fon jarayonlarida boshqarish.

4. **3 Tilli Tizim (i18n):**
   - Sayt va API 3 tilda ishlaydi: O‘zbekcha (`/uz/`), Ruscha (`/ru/`), Inglizcha (`/en/`).
   - Admin botda faqat 1 ta — O‘zbek tilida kiritadi, muammo nomlari avtomatik tarjima qilinadi.

---

## 🛠 TEXNOLOGIK STEK (TECH STACK)

- **Backend:** Python 3.12+ / Django 5.1+ (ORM, Asinxron funksiyalar, i18n).
- **Telegram Bot:** Aiogram 3.17+ (FSM, Polling/Webhook, Custom Keyboards).
- **Frontend:** Vanilla CSS / JavaScript (Ortiqcha og‘ir freymvorklarsiz), Dark Mode, Glassmorphism, Responsive Mobile-First.
- **Ma'lumotlar Bazasi:** **SQLite3 (`db.sqlite3`)** — tezkor, ortiqcha server resursini yemaydigan, bitta faylli qulay baza.
- **Serverda Yurgizish (Daemon/Process Manager):** Linux **`systemd` servislari** (`mobiprice_web.service` va `mobiprice_bot.service`).
- **Web Server & Reverse Proxy:** Gunicorn (WSGI) + Nginx (Statik fayllar keshi va SSL terminatsiyasi) + Let's Encrypt Certbot.

---

## 📋 BOSQICHLAR VA AMALGA OSHIRISH REJASI

### 1-BOSQICH: TIZIM ARXITEKTURASI VA INFRATUZILMA
- [✅] Django loyihasi yaratildi, app strukturasi (`core`, `bot`) sozlandi.
- [✅] Ko‘p tillilik sozlamalari (`uz`, `ru`, `en`) va i18n arxitekturasi ulandi.
- [✅] Statik fayllar va media fayllar yo‘llari (`media/brands/`, `media/phones/`, `static/img/icons/`) sozlandi.
- [✅] Virtualenv (`.venv`) va Makefile orqali dasturchi buyruqlari (`run`, `bot`, `migrate`, `shell`) sozlandi.
- [✅] SQLite3 bazasi sozlandi, WAL (Write-Ahead Logging) va 5000ms busy timeout yuqori yuklamalar uchun ulandi.

---

### 2-BOSQICH: 5-QADAMLI MA'LUMOTLAR BAZASI STRUKTURASI
- [✅] **1. Brendlar modeli (`Brand`):** Nomi, slug, SVG logo kodi, rasm, tartib raqami, aktivlik holati.
- [✅] **2. Model Seriyalari modeli (`DeviceSeries`):** `ForeignKey -> Brand`, seriya nomi, slug, tartibi (`unique_together=('brand', 'name')`).
- [✅] **3. Telefonlar modeli (`DevicePhone`):** `ForeignKey -> DeviceSeries`, telefon nomi, unikal avto-slug (to‘qnashuvlarni `name-1`, `name-2` qilib hal qiluvchi), rasm maydoni (`phones/`), chiqqan yili.
- [✅] **4. Muammolar modeli (`DeviceIssue`):** `ForeignKey -> DevicePhone`, o‘zbekcha nomi (`title`), ruscha nomi (`title_ru`), inglizcha nomi (`title_en`), 30 ta ikonka raqami (`icon_number`), SVG ikonka kodi (`icon_svg`).
- [✅] **5. Sifat va Narxlar modeli (`IssueComparison`):** `ForeignKey -> DeviceIssue`, sifati (`original` / `kopiya`), sarlavha, narxi so‘mda (`part_price_uzs`), USD ekvivalenti (`price_usd`), ombordagi soni (`quantity`), ombor holati (`is_in_stock`).
- [✅] **Yordamchi modellar:**
  - `RepairFAQ`: Ko‘p beriladigan savol-javoblar (3 tilda).
  - `Review`: Mijoz sharhlari va ta'mirdan "Oldin / Keyin" (`before_image`, `after_image`) fotolari.
  - `ServiceOrder`: Unikal `#ORD-XXXX` trek-kodli buyurtmalar modeli.
- [✅] Django Admin boshqaruvi: barcha modellar uchun qidiruv, filtrlar, tartiblash va ombordagi sonini tezkor tahrirlash (`list_editable`) sozlandi.
- [✅] Barcha modellar uchun Django migratsiyalari yaratildi va bazaga muvaffaqiyatli tatbiq qilindi (`0001_initial`, `0002_...`, `0003_...`).

---

### 3-BOSQICH: AIOGRAM 3 TELEGRAM ADMIN BOT PANELI
- [✅] Admin avtorizatsiyasi: faqat ruxsat etilgan Admin IDlar (`ADMIN_IDS`) orqali boshqaruv.
- [✅] Qulay Dashboard klaviaturasi: `📂 Brendlar`, `📁 Modellar`, `📱 Telefonlar`, `🔧 Muammolar`, `💰 Narxlar`, `📊 Statistika`.
- [✅] **Qatorda maksimal 3 ta tugma** ergonomika qoidasi barcha Reply va Inline tugmalarga joriy etildi.
- [✅] **1-Bo‘lim: Brendlar CRUD:**
  - Ro‘yxat ko‘rish, yangi brend qo‘shish (nomi + `.svg` logotip fayli), tahrirlash (nom va logo), o‘chirish.
- [✅] **2-Bo‘lim: Modellar (Seriyalar) CRUD:**
  - Brend tanlash -> Seriya nomini kiritish, ro‘yxat, tahrirlash, o‘chirish.
- [✅] **3-Bo‘lim: Telefonlar CRUD:**
  - Brend tanlash -> Seriya tanlash -> Telefon nomini kiritish -> JPG/PNG rasmini yuklash (rasm yoki fayl ko‘rinishida).
  - Ro‘yxat ko‘rish, nomini va rasmini alohida tahrirlash, o‘chirish.
  - Asinxron xavfsiz DB yuklanishi (`select_related`) va rasmlar xavfsiz saqlanishi.
- [✅] **4-Bo‘lim: Muammolar CRUD va Avtomatik Tarjima:**
  - Brend -> Seriya -> Telefon tanlash.
  - O‘zbekcha nom kiritilganda avtomatik Ruscha va Inglizcha tarjimalarni yaratish (`bot/utils/translator.py`).
  - 30 ta vektorli SVG ikonka generatsiyasi va botda ko‘rsatiladigan 6x5 neonli cheatsheet infografika rasmi (`bot/assets/icons_cheatsheet.png`).
  - Ikonka raqamini (1-30) tanlash va SVG kodini bazaga yozish, tahrirlash, o‘chirish.
- [✅] **5-Bo‘lim: Soddalashtirilgan Narxlar CRUD:**
  - Brend -> Seriya -> Telefon -> Muammoni tanlash.
  - Sifat turini tanlash: `🟢 Original` yoki `🟡 Sifatli Kopiya`.
  - Narxini kiritish (so‘mda).
  - Ombordagi qoldiq miqdorini kiritish (`quantity` — masalan: 5 yoki 0).
  - Narx va miqdorni tahrirlash, o‘chirish.
- [✅] **Statistika va Buyurtmalar hisoblagichi:**
  - Bosh menyudagi `📊 Statistika` tugmasi orqali bazadagi barcha brendlar, seriyalar, telefonlar, muammolar, narxlar va kelib tushgan arizalar soni real vaqtda ko‘rinadi.

---

### 4-BOSQICH: MIJOZ INTERFEYSI (UI/UX) VA 5-QADAMLI KALKULYATOR
- [✅] **Premium Dark Mode Dizayn:** Glassmorphism neon aksentlar, yuqori kontrastli zamonaviy tipografika, 100% mobil moslashuvchanlik.
- [✅] **Interaktiv 5-Bosqichli Kalkulyator:**
  - 1-Qadam: Brend tanlash (Apple, Samsung, Xiaomi...).
  - 2-Qadam: Model Seriyasi tanlash (S seriya, A seriya, Pro seriya...).
  - 3-Qadam: Aniq telefonni tanlash (suratlari bilan).
  - 4-Qadam: Muammoni tanlash (30 ta aniq SVG ikonkalari bilan).
  - 5-Qadam: Solishtirish natijasi: Original vs Kopiya, Narxi, Omborda mavjudlik holati (`🟢 Omborda: X ta` yoki `🔴 Mavjud emas (Kutilmoqda)`).
- [✅] **Interaktiv "Oldin va Keyin" (Before / After Slider):**
  - Foydalanuvchi sensorli ekranda yoki sichqoncha bilan siljitib ta'mirdan oldingi va keyingi holatni taqqoslay oladi.
- [✅] **FAQ va Mijoz Sharhlari:**
  - Dinamik tez-tez beriladigan savollar akkordeoni va mijozlar fikrlari bloki.
- [✅] **Til almashtirish interfeysi:** Sayt sarlavhasida `UZ | RU | EN` tillarini bir zumda almashtirish.
- [✅] **Buyurtma berish modali:**
  - Mijoz o‘z ismi va telefon raqamini kiritib ariza qoldirishi mumkin bo‘lgan tezkor forma.
- [✅] **Jonli Model Qidiruvi (Live Search):**
  - Qidiruv qatoriga yozish bilan bir zumda telefon modellarini topib, to‘g‘ridan-to‘g‘ri kalkulyatorga yo‘naltirish (`/api/phones/search/`).
- [✅] **"Telefonim holatini tekshirish" (Trek tekshirish UI & API):**
  - Mijoz o‘zining `#ORD-XXXX` kodi orqali saytdan telefon qaysi bosqichda ekanligini (Qabul qilindi, Diagnostika, Ta'mirlanmoqda, Tayyor) ko'rish uchun interaktiv stepper va `/api/orders/track/` API.
- [✅] **Scroll bo'yicha kirib keluvchi animatsiyalar (Scroll Reveal Engine):**
  - Sayt bo'ylab pastga tushganda har bir bo'lim va div kartalar `IntersectionObserver` yordamida silliq neon fade-up va zoom effekti bilan ochiladi (`static/js/scroll_reveal.js` va `static/css/animations.css`).
- [✅] **Saytdan topilmagan modellar va Tajribali ustalar bloki:**
  - Saytdan topilmagan har qanday smartfon va ehtiyot qismlari uchun tajribali ustalar bilan bog'lanish vitrinasi, orqa fonga laboratoriya ustaxonasi surati (`static/img/team_workshop_bg.jpg`).
- [✅] **Instagram QR-kod kartasi va 2 ta rasmiy telefon raqami:**
  - `@MURODJONMILYAZOV_` Instagram skaner kartasi, `+998 (90) 919-76-00` va `+998 (90) 918-76-00` raqamlari hamda Telegram/Instagram havolalari.
- [✅] **"Bizning jamoamiz!" Mutaxassislar vitrinasi:**
  - Saytda tajribali ustalar jamoasi kartalari (Ismi, lavozimi, tajribasi, surati va kafolati) (`templates/components/team.html`, `static/css/team.css`).
- [✅] **Mijozlar fikri va Anti-Spam (1 IP + 1 Qurilma / 24 soat):**
  - Saytda mijozlar uchun 5 yulduzli interaktiv sharh qoldirish modali (`templates/components/review_modal.html`), IP va doimiy qurilma identifikatori (fingerprint) orqali kunda faqat 1 marta sharh yozish cheklovi (`/api/reviews/submit/`) hamda Telegram botga lahzada xabar yuborish.
- [✅] **Bot: Dinamik Adminlar boshqaruvi (`👥 Adminlar`):**
  - Username (masalan `@username`) yoki Telegram ID orqali yangi adminlarni botdan to‘g‘ridan-to‘g‘ri qo‘shish va o‘chirish mexanizmi (`bot/handlers/admins.py`).
- [✅] **Bot: Jamoa ustalarini boshqarish CRUD (`👨‍🔧 Ustalar (Jamoa)`):**
  - Bot orqali yangi usta (ismi, roli, ish staji va surati) qo‘shish, ro‘yxat ko‘rish va o‘chirish (`bot/handlers/masters.py`).

---

### 5-BOSQICH: BUYURTMALAR EKOTIZIMI VA TELEGRAM CRM
- [✅] **Saytdan yangi buyurtma tushganda Telegram Botga / Guruhga xabar:**
  ```
  🚨 YANGI TA'MIRLASH BUYURTMASI! #MP-D37FF1
  👤 Mijoz: Alisher Karimov
  📞 Telefon: +998 90 123 45 67
  📱 Model: Samsung Galaxy S25 Ultra
  🔧 Muammo: Ekran almashtirish
  💵 Narxi: 1,850,000 so‘m
  📦 Holati: 🔴 Yangi ariza
  ```
- [✅] **Bot orqali arizani tezkor boshqarish:**
  - Xabar tagidagi inline tugmalar: `[✅ Qabul qilish]` | `[👨‍🔧 Ustaga biriktirish]` | `[📞 Bog‘lanildi]` | `[🎉 Tayyor]` | `[❌ Bekor qilish]`.
- [✅] **Buyurtmalar Mini-CRM interfeysi:**
  - Bot bosh menyusida `📦 Buyurtmalar (CRM)` bo‘limi, yangi arizalar, ta'mirlanayotganlar, tayyor bo‘lganlar ro‘yxati va kod bo‘yicha qidirish (`bot/handlers/crm.py`).
- [✅] **Ustaga biriktirish mexanizmi:**
  - Har bir buyurtmaga bazadagi jamoa ustalaridan birini biriktirish, statusni `in_progress` ga o'tkazish va saytdagi trekkerda aks ettirish.
- [✅] **Mijoz uchun avtomatik yangilanish:**
  - Usta buyurtmani `Tayyor` deb belgilaganda, mijoz saytda `#MP-XXXXXX` kodini tekshirganida darhol "4-bosqich: Tayyor (Olib ketishingiz mumkin)" holatida ko‘rinadi.

---

### 6-BOSQICH: OMMAVIY MA'LUMOT BOSHQARUVI (EXCEL IMPORT / EXPORT)
- [✅] **Excel / CSV orqali ommaviy yuklash (Bulk Import):**
  - Yuzlab telefonlar, seriyalar va ehtiyot qismlar narxlarini 1 ta Excel fayli orqali bazaga avtomatik kiritish (`core/excel_manager.py`).
- [✅] **Excel orqali eksport va narxlarni yoppasiga yangilash:**
  - Hamma narxlarni Excel jadval ko‘rinishida yuklab olish va o‘zgartirib qayta yuklash imkoniyati hamda botda namuna shablon yuklab olish (`bot/handlers/excel.py`).

---

### 7-BOSQICH: YUQORI YUKLAMA (HIGH-LOAD 10,000+), KESH VA XAVFSIZLIK
- [✅] **SQLite3 WAL (Write-Ahead Logging) rejimi:**
  - Bir vaqtda yuzlab o‘qish (read) so‘rovlarini bloklanmasdan o‘ta tez ishlashini ta'minlash (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA busy_timeout=30000;`).
- [✅] **Tezkor xotira keshi (In-Memory / File Caching):**
  - Brendlar, Seriyalar, Telefonlar va Narxlar API javoblarini `django.core.cache` orqali keshda saqlash va ma'lumot yangilanganda avtomatik keshni tozalash (`core/views.py`, `core/apps.py`).
- [✅] **Spam va Hujumlardan Himoya (Rate Limiting):**
  - Buyurtma formasiga 1 ta IP manzildan daqiqasiga 2 tadan ortiq so‘rov yuborishni cheklash (429 Too Many Requests), Sharhlar uchun 1 IP + 1 Device / 24 soat cheklovi, hamda CSRF va XSS himoyasi (`escape()`).

---

### 8-BOSQICH: SEO VA QIDIRUV TIZIMLARIDA PESHQADAMLIK
- [ ] Har bir model va muammo uchun avtomatik generatsiya qilinadigan SEO meta-teglar (Title, Meta Description, OpenGraph).
- [ ] Dinamik `sitemap.xml` va `robots.txt` generatsiyasi.
- [ ] **Schema.org mikroformati:** Google qidiruv natijalarida to‘g‘ridan-to‘g‘ri yulduzchalar (reyting) va ta'mirlash narxi ko‘rinib turishi uchun `Product` / `Service` JSON-LD formatini integratsiya qilish.

---

### 9-BOSQICH: LINUX SYSTEMD SERVUSLARI VA SERVERGA JOYLASH (DEPLOY)
- [ ] **Gunicorn sozlamalari:** Veb-saytni barqaror ko‘p ishchi oqimlar (workers) bilan yurgizish.
- [ ] **`mobiprice_web.service` yaratish:**
  - Linux `systemd` servisi orqali Gunicorn'ni fonda doimiy ishlatish (`systemctl enable --now mobiprice_web`).
- [ ] **`mobiprice_bot.service` yaratish:**
  - Telegram botni fonda uzluksiz ishlatish va server o‘chib yonganda avtomatik qayta tiklanishi (`Restart=always`).
- [ ] **Nginx Reverse Proxy:**
  - Saytni 80-port (HTTP) va 443-port (HTTPS) orqali Gunicorn'ga ulash, barcha statik va media fayllarni Nginx orqali maksimal tezlikda tarqatish.
- [ ] **Let's Encrypt SSL/HTTPS:**
  - Bepul xavfsiz yashil qulf (SSL sertifikati) va avtomatik yangilanishi (`certbot --nginx`).
- [ ] **Avtomatik Backup (Zaxiralash) skripti:**
  - Har kechasi `db.sqlite3` va `media/` papkasini zaxira arxiviga nusxalab qo‘yish cron skripti.

---

## 📊 HOZIRGI HOLAT XULOSASI (STATUS OVERVIEW)

| Bo‘lim | Holati | Izoh |
| :--- | :--- | :--- |
| **5-Bosqichli Baza Modeli** | ✅ **Bajarildi** | `Brand` -> `Series` -> `Phone` -> `Issue` -> `Comparison` to‘liq tayyor |
| **Aiogram 3 Admin Bot** | ✅ **Bajarildi** | 5 ta bo‘lim uchun to‘liq CRUD, 30 ta SVG ikonka, avto-tarjima, 3-tugmali menyu |
| **Kalkulyator UI (Web)** | ✅ **Bajarildi** | 5 ta bosqich, Before/After slider, Dark UI, 3 ta til faol |
| **Trek Tekshirish (Track Order)** | ✅ **Bajarildi** | `#ORD-XXXX` kodi bilan 4 bosqichli status stepper va modal |
| **Scroll Animatsiyalar & Konsultatsiya** | ✅ **Bajarildi** | IntersectionObserver animatsiyalari, QR kod, 2 ta telefon raqami |
| **Telegram CRM & Xabarnomalar** | ✅ **Bajarildi** | Saytdan tushgan buyurtmani botga lahzada uzatish, inline boshqaruv va ustaga biriktirish |
| **Excel Import / Export** | ⏳ **Keyingi navbatda** | Ommaviy ma'lumot kiritish |
| **Tezkor Kesh & Anti-Spam** | ⏳ **Rejada** | SQLite WAL rejimi, xotira keshi va cheklovlar |
| **Serverga Joylash (Deploy)** | ⏳ **Rejada** | Linux systemd (`.service`), Gunicorn, Nginx, SSL, SQLite3 |