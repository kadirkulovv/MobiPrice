import uuid
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Brand(models.Model):
    name = models.CharField(_("Brend nomi"), max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    logo = models.FileField(_("Logotip (SVG/PNG)"), upload_to='brands/', blank=True, null=True)
    order = models.PositiveIntegerField(_("Tartib raqami"), default=0)
    is_active = models.BooleanField(_("Aktiv"), default=True)

    class Meta:
        verbose_name = _("1. Brend")
        verbose_name_plural = _("1. Brendlar")
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DeviceSeries(models.Model):
    """2-Qadam: Model seriyasi (Pro seriya, S seriya, A seriya, Redmi Note seriya va h.k.)"""
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='series', verbose_name=_("Brend"))
    name = models.CharField(_("Model seriyasi nomi"), max_length=150)
    slug = models.SlugField(max_length=150, blank=True)
    order = models.PositiveIntegerField(_("Tartib"), default=0)

    class Meta:
        verbose_name = _("2. Model seriyasi")
        verbose_name_plural = _("2. Model seriyalari")
        ordering = ['order', 'name']
        unique_together = ('brand', 'name')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.brand.slug}-{self.name}") or str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.brand.name} → {self.name}"


class DevicePhone(models.Model):
    """3-Qadam: Aniq telefon (iPhone 16 Pro Max, Galaxy S24 Ultra va h.k.)"""
    series = models.ForeignKey(DeviceSeries, on_delete=models.CASCADE, related_name='phones', verbose_name=_("Model seriyasi"))
    name = models.CharField(_("Telefon nomi"), max_length=150)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    image = models.ImageField(_("Telefon rasmi (JPG/PNG)"), upload_to='phones/', blank=True, null=True)
    release_year = models.PositiveIntegerField(_("Chiqqan yili"), default=2024, blank=True, null=True)
    order = models.PositiveIntegerField(_("Tartib"), default=0)

    class Meta:
        verbose_name = _("3. Telefon")
        verbose_name_plural = _("3. Telefonlar")
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or str(uuid.uuid4())[:8]
            slug = base_slug
            counter = 1
            while DevicePhone.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.series.brand.name} {self.name}"


class DeviceIssue(models.Model):
    """4-Qadam: Muammo / Detal (Ekran, Batareya, Orqa shisha va h.k. — 30 ta ikonka bilan)"""
    phone = models.ForeignKey(DevicePhone, on_delete=models.CASCADE, related_name='issues', verbose_name=_("Telefon"))
    title = models.CharField(_("Muammo / Detal nomi"), max_length=150)
    title_ru = models.CharField(_("Nomi (Ruscha)"), max_length=150, blank=True)
    title_en = models.CharField(_("Nomi (Inglizcha)"), max_length=150, blank=True)
    icon_number = models.PositiveSmallIntegerField(_("Ikonka raqami (1-30)"), default=1)
    icon_svg = models.TextField(_("SVG ikonka kodi"), blank=True)
    order = models.PositiveIntegerField(_("Tartib"), default=0)

    class Meta:
        verbose_name = _("4. Muammo / Detal")
        verbose_name_plural = _("4. Muammolar va Detallar")
        ordering = ['order', 'title']

    def __str__(self):
        return f"{self.phone.name} → {self.title} (#{self.icon_number})"


class IssueComparison(models.Model):
    """5-Qadam: Solishtirish / Narxlar (Original, OLED GX, Incell va h.k.)"""
    QUALITY_CHOICES = [
        ('original_service_pack', _('Original Zavod (Service Pack)')),
        ('original_donor', _('Original Donar (Yechib olingan)')),
        ('oled_gx', _('OLED GX / ZY (Originalga eng yaqin)')),
        ('tft_incell', _('Incell / TFT (Hamyonbop Kopiya)')),
    ]

    issue = models.ForeignKey(DeviceIssue, on_delete=models.CASCADE, related_name='comparisons', verbose_name=_("Muammo / Detal"))
    quality_type = models.CharField(_("Sifat toifasi"), max_length=50, choices=QUALITY_CHOICES, default='original_service_pack')

    title = models.CharField(_("Sarlavha (UZ)"), max_length=200)
    title_ru = models.CharField(_("Sarlavha (RU)"), max_length=200, blank=True)
    title_en = models.CharField(_("Sarlavha (EN)"), max_length=200, blank=True)

    part_price_uzs = models.DecimalField(_("Zapchast narxi (so'm)"), max_digits=12, decimal_places=0, default=0)
    service_fee_uzs = models.DecimalField(_("Usta haqqi (so'm)"), max_digits=12, decimal_places=0, default=0)
    price_usd = models.DecimalField(_("Narxi (USD)"), max_digits=8, decimal_places=0, default=0)

    quantity = models.PositiveIntegerField(_("Ombordagi soni"), default=5)
    is_in_stock = models.BooleanField(_("Mavjud"), default=True)

    warranty = models.CharField(_("Kafolat (UZ)"), max_length=100, default="6 oy kafolat")
    warranty_ru = models.CharField(_("Kafolat (RU)"), max_length=100, default="6 месяцев гарантии")
    warranty_en = models.CharField(_("Kafolat (EN)"), max_length=100, default="6 months warranty")

    repair_time = models.CharField(_("Ta'mirlash vaqti"), max_length=50, default="30 daqiqa")
    badge = models.CharField(_("Belgi (Masalan: Tavsiya etiladi)"), max_length=50, blank=True)

    description = models.TextField(_("Tavsif (Farqi nimada) UZ"), blank=True)
    description_ru = models.TextField(_("Tavsif (RU)"), blank=True)
    description_en = models.TextField(_("Tavsif (EN)"), blank=True)

    features = models.JSONField(_("Xususiyatlari ro‘yxati"), default=list, blank=True)

    class Meta:
        verbose_name = _("5. Solishtirish va Narx")
        verbose_name_plural = _("5. Solishtirish va Narxlar")
        ordering = ['issue', '-quality_type']

    def __str__(self):
        return f"{self.issue.phone.name} → {self.issue.title} ({self.get_quality_type_display()}) - {self.total_price_uzs:,} so'm"

    @property
    def total_price_uzs(self):
        return self.part_price_uzs + self.service_fee_uzs


class RepairFAQ(models.Model):
    question = models.CharField(_("Savol (UZ)"), max_length=255)
    question_ru = models.CharField(_("Savol (RU)"), max_length=255, blank=True)
    question_en = models.CharField(_("Savol (EN)"), max_length=255, blank=True)

    answer = models.TextField(_("Javob (UZ)"))
    answer_ru = models.TextField(_("Javob (RU)"), blank=True)
    answer_en = models.TextField(_("Javob (EN)"), blank=True)

    order = models.PositiveIntegerField(_("Tartib"), default=0)

    class Meta:
        verbose_name = _("FAQ / Savol-javob")
        verbose_name_plural = _("FAQ / Savol-javoblar")
        ordering = ['order']

    def __str__(self):
        return self.question


class Review(models.Model):
    client_name = models.CharField(_("Mijoz ismi"), max_length=100)
    device_model = models.CharField(_("Telefon modeli"), max_length=100)
    service_type = models.CharField(_("Qilingan ish"), max_length=100)
    rating = models.PositiveSmallIntegerField(_("Reyting (1-5)"), default=5)
    comment = models.TextField(_("Mijoz sharhi"))

    ip_address = models.GenericIPAddressField(_("IP manzil"), null=True, blank=True, db_index=True)
    device_fingerprint = models.CharField(_("Qurilma identifikatori"), max_length=100, null=True, blank=True, db_index=True)

    is_verified = models.BooleanField(_("Tasdiqlangan"), default=True)
    created_at = models.DateTimeField(_("Yaratilgan sana"), auto_now_add=True)

    class Meta:
        verbose_name = _("Mijoz sharhi")
        verbose_name_plural = _("Mijozlar sharhlari")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client_name} - {self.device_model} ({self.rating}★)"


class TeamMember(models.Model):
    """Bizning jamoamiz — Tajribali ustalar va mutaxassislar"""
    full_name = models.CharField(_("Usta / Mutaxassis ismi"), max_length=120)
    role = models.CharField(_("Mutaxassisligi / Lavozimi"), max_length=120, help_text=_("Masalan: iPhone bo'yicha ekspert"))
    experience = models.CharField(_("Tajribasi"), max_length=60, default="5+ yillik tajriba", help_text=_("Masalan: 7 yillik tajriba"))
    photo = models.ImageField(_("Surati"), upload_to='masters/', blank=True, null=True)
    order = models.PositiveIntegerField(_("Tartib raqami"), default=0)
    is_active = models.BooleanField(_("Faol"), default=True)
    created_at = models.DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)

    class Meta:
        verbose_name = _("Jamoa a'zosi / Usta")
        verbose_name_plural = _("Jamoa a'zolari / Ustalar")
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class BotAdmin(models.Model):
    """Telegram Bot Admin va Menejerlari (Dinamik huquqlar bilan)"""
    ROLE_CHOICES = [
        ('admin', _('Admin (Sayt va resurslar boshqaruvi)')),
        ('manager', _('Menejer (Faqat zayavkalar va CRM)')),
        ('both', _('Admin + Menejer (Ikkala huquq ham)')),
    ]

    telegram_id = models.BigIntegerField(_("Telegram ID"), unique=True, null=True, blank=True)
    username = models.CharField(_("Username (@siz)"), max_length=100, blank=True, null=True, db_index=True)
    full_name = models.CharField(_("Xodim ismi / Izoh"), max_length=150, blank=True)
    role = models.CharField(
        _("Vazifasi / Roli"),
        max_length=20,
        choices=ROLE_CHOICES,
        default='both',
        help_text=_("admin = sayt resurslari; manager = zayavkalar; both = ikkalasi")
    )
    is_active = models.BooleanField(_("Faol"), default=True)
    added_by = models.CharField(_("Kim qo'shgan"), max_length=100, blank=True)
    created_at = models.DateTimeField(_("Qo'shilgan sana"), auto_now_add=True)

    class Meta:
        verbose_name = _("Bot Admin / Menejer")
        verbose_name_plural = _("Bot Adminlar va Menejerlar")
        ordering = ['-created_at']

    def __str__(self):
        user_str = f"@{self.username}" if self.username else str(self.telegram_id)
        return f"{self.full_name or user_str} [{self.get_role_display()}]"

    @property
    def can_manage_site(self) -> bool:
        return self.is_active and self.role in ('admin', 'both')

    @property
    def can_handle_leads(self) -> bool:
        return self.is_active and self.role in ('manager', 'both')

    @property
    def role_badge(self) -> str:
        if self.role == 'admin':
            return "🛠️ Admin (Sayt)"
        elif self.role == 'manager':
            return "📋 Menejer (Zayavka)"
        return "🌟 Admin + Menejer"



class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('new', _('Yangi ariza')),
        ('contacted', _('Bog‘lanildi')),
        ('in_progress', _('Ta’mirlanmoqda')),
        ('ready', _('Tayyor')),
        ('completed', _('Topshirildi')),
        ('cancelled', _('Bekor qilindi')),
    ]

    SERVICE_CHOICES = [
        ('in_service', _('Servis markaziga borish')),
        ('call_master', _('Usta chaqirish (Manzilga)')),
        ('courier', _('Kuryer orqali yuborish')),
    ]

    order_id = models.CharField(_("Buyurtma ID"), max_length=30, unique=True, editable=False)
    client_name = models.CharField(_("Mijoz ismi"), max_length=100)
    phone_number = models.CharField(_("Telefon raqami"), max_length=30)
    phone = models.ForeignKey(DevicePhone, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Telefon"))
    comparison = models.ForeignKey(IssueComparison, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Tanlangan variant"))

    service_type = models.CharField(_("Xizmat turi"), max_length=50, choices=SERVICE_CHOICES, default='in_service')
    status = models.CharField(_("Holati"), max_length=50, choices=STATUS_CHOICES, default='new')
    master = models.ForeignKey(TeamMember, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Biriktirilgan usta"))

    notes = models.TextField(_("Mijoz izohi"), blank=True)
    admin_notes = models.TextField(_("Admin / Usta qaydlari"), blank=True)
    created_at = models.DateTimeField(_("Yaratilgan vaqt"), auto_now_add=True)


    class Meta:
        verbose_name = _("Buyurtma / Ariza")
        verbose_name_plural = _("Buyurtmalar va Arizalar")
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"MP-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_id} - {self.client_name} ({self.phone_number})"
