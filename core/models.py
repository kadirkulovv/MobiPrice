import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class Brand(models.Model):
    name = models.CharField(_("Brend nomi"), max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    logo = models.ImageField(_("Logotip"), upload_to='brands/', blank=True, null=True)
    order = models.PositiveIntegerField(_("Tartib raqami"), default=0)
    is_active = models.BooleanField(_("Aktiv"), default=True)

    class Meta:
        verbose_name = _("Brend")
        verbose_name_plural = _("Brendlar")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class DeviceModel(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='models', verbose_name=_("Brend"))
    name = models.CharField(_("Model nomi"), max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    image = models.ImageField(_("Rasm"), upload_to='models/', blank=True, null=True)
    model_code = models.CharField(_("Model kodi (A3084 va h.k.)"), max_length=50, blank=True)
    release_year = models.PositiveIntegerField(_("Chiqqan yili"), default=2024)
    is_popular = models.BooleanField(_("Ommabop model"), default=False)
    order = models.PositiveIntegerField(_("Tartib"), default=0)

    class Meta:
        verbose_name = _("Telefon modeli")
        verbose_name_plural = _("Telefon modellari")
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class PartCategory(models.Model):
    code = models.CharField(_("Kod"), max_length=50, unique=True)
    name = models.CharField(_("Nomi (O'zbekcha)"), max_length=100)
    name_ru = models.CharField(_("Nomi (Ruscha)"), max_length=100, blank=True)
    name_en = models.CharField(_("Nomi (Inglizcha)"), max_length=100, blank=True)
    icon_svg = models.TextField(_("SVG ikonka kodi"), blank=True)
    order = models.PositiveIntegerField(_("Tartib"), default=0)

    class Meta:
        verbose_name = _("Zapchast kategoriyasi")
        verbose_name_plural = _("Zapchast kategoriyalari")
        ordering = ['order']

    def __str__(self):
        return self.name

    def get_localized_name(self, lang='uz'):
        if lang == 'ru' and self.name_ru:
            return self.name_ru
        elif lang == 'en' and self.name_en:
            return self.name_en
        return self.name


class PartOption(models.Model):
    QUALITY_CHOICES = [
        ('original_service_pack', _('Original Zavod (Service Pack)')),
        ('original_donor', _('Original Donar (Yechib olingan)')),
        ('oled_gx', _('OLED GX / ZY (Originalga eng yaqin)')),
        ('tft_incell', _('Incell / TFT (Hamyonbop Kopiya)')),
    ]

    STOCK_CHOICES = [
        ('in_stock', _('Omborda mavjud')),
        ('order_1day', _('Zakazga 1 kun')),
        ('out_of_stock', _('Vaqtincha yo‘q')),
    ]

    device_model = models.ForeignKey(DeviceModel, on_delete=models.CASCADE, related_name='part_options', verbose_name=_("Telefon modeli"))
    category = models.ForeignKey(PartCategory, on_delete=models.CASCADE, related_name='options', verbose_name=_("Zapchast turi"))
    quality_type = models.CharField(_("Sifat toifasi"), max_length=50, choices=QUALITY_CHOICES, default='original_service_pack')

    title = models.CharField(_("Sarlavha (UZ)"), max_length=200)
    title_ru = models.CharField(_("Sarlavha (RU)"), max_length=200, blank=True)
    title_en = models.CharField(_("Sarlavha (EN)"), max_length=200, blank=True)

    part_price_uzs = models.DecimalField(_("Zapchast narxi (so'm)"), max_digits=12, decimal_places=0, default=0)
    service_fee_uzs = models.DecimalField(_("Usta haqqi (so'm)"), max_digits=12, decimal_places=0, default=0)
    price_usd = models.DecimalField(_("Narxi (USD)"), max_digits=8, decimal_places=0, default=0)

    warranty = models.CharField(_("Kafolat (UZ)"), max_length=100, default="6 oy kafolat")
    warranty_ru = models.CharField(_("Kafolat (RU)"), max_length=100, default="6 месяцев гарантии")
    warranty_en = models.CharField(_("Kafolat (EN)"), max_length=100, default="6 months warranty")

    repair_time = models.CharField(_("Ta'mirlash vaqti"), max_length=50, default="40 daqiqa")
    badge = models.CharField(_("Belgi (Masalan: Tavsiya etiladi)"), max_length=50, blank=True)

    description = models.TextField(_("Tavsif (Farqi nimada) UZ"))
    description_ru = models.TextField(_("Tavsif (RU)"), blank=True)
    description_en = models.TextField(_("Tavsif (EN)"), blank=True)

    features = models.JSONField(_("Xususiyatlari ro‘yxati"), default=list, blank=True)

    stock_status = models.CharField(_("Ombor holati"), max_length=30, choices=STOCK_CHOICES, default='in_stock')

    class Meta:
        verbose_name = _("Sifat varianti va narx")
        verbose_name_plural = _("Sifat variantlari va narxlar")
        ordering = ['device_model', 'category', '-quality_type']

    def __str__(self):
        return f"{self.device_model.name} - {self.category.name} ({self.get_quality_type_display()})"

    @property
    def total_price_uzs(self):
        return self.part_price_uzs + self.service_fee_uzs


class RepairFAQ(models.Model):
    category = models.ForeignKey(PartCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='faqs', verbose_name=_("Zapchast turi"))
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

    before_image = models.ImageField(_("Oldingi holati (singan)"), upload_to='reviews/', blank=True, null=True)
    after_image = models.ImageField(_("Keyingi holati (tuzalgan)"), upload_to='reviews/', blank=True, null=True)

    is_verified = models.BooleanField(_("Tasdiqlangan"), default=True)
    created_at = models.DateTimeField(_("Yaratilgan sana"), auto_now_add=True)

    class Meta:
        verbose_name = _("Mijoz sharhi")
        verbose_name_plural = _("Mijozlar sharhlari")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client_name} - {self.device_model} ({self.rating}★)"


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
    device_model = models.ForeignKey(DeviceModel, on_delete=models.SET_NULL, null=True, verbose_name=_("Telefon modeli"))
    part_option = models.ForeignKey(PartOption, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Tanlangan variant"))

    service_type = models.CharField(_("Xizmat turi"), max_length=50, choices=SERVICE_CHOICES, default='in_service')
    status = models.CharField(_("Holati"), max_length=50, choices=STATUS_CHOICES, default='new')

    notes = models.TextField(_("Izohlar"), blank=True)
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
