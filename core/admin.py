from django.contrib import admin
from django.utils.html import format_html
from .models import Brand, DeviceModel, PartCategory, PartOption, RepairFAQ, Review, ServiceOrder


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    search_fields = ('name',)


@admin.register(DeviceModel)
class DeviceModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'release_year', 'is_popular', 'order')
    list_filter = ('brand', 'is_popular', 'release_year')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_popular', 'order')
    search_fields = ('name', 'model_code')


@admin.register(PartCategory)
class PartCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_ru', 'code', 'order')
    list_editable = ('order',)
    search_fields = ('name', 'name_ru', 'code')


@admin.register(PartOption)
class PartOptionAdmin(admin.ModelAdmin):
    list_display = ('device_model', 'category', 'quality_type', 'total_price_display', 'warranty', 'stock_status')
    list_filter = ('category', 'quality_type', 'stock_status', 'device_model__brand')
    search_fields = ('device_model__name', 'title', 'description')

    def total_price_display(self, obj):
        return f"{obj.total_price_uzs:,} so'm (${obj.price_usd})"
    total_price_display.short_description = "Umumiy narx"


@admin.register(RepairFAQ)
class RepairFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order')
    list_filter = ('category',)
    search_fields = ('question', 'answer')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'device_model', 'service_type', 'rating_stars', 'is_verified', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at')
    search_fields = ('client_name', 'device_model', 'comment')
    list_editable = ('is_verified',)

    def rating_stars(self, obj):
        return '★' * obj.rating
    rating_stars.short_description = "Baho"


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'client_name', 'phone_number', 'device_model', 'status_badge', 'created_at')
    list_filter = ('status', 'service_type', 'created_at')
    search_fields = ('order_id', 'client_name', 'phone_number', 'notes')
    readonly_fields = ('order_id', 'created_at')

    def status_badge(self, obj):
        colors = {
            'new': '#ef4444',
            'contacted': '#f59e0b',
            'in_progress': '#3b82f6',
            'ready': '#10b981',
            'completed': '#6b7280',
            'cancelled': '#374151',
        }
        color = colors.get(obj.status, '#3b82f6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Status"
