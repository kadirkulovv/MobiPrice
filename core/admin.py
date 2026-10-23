from django.contrib import admin
from django.utils.html import format_html
from .models import Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison, RepairFAQ, Review, ServiceOrder


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')
    search_fields = ('name',)


@admin.register(DeviceSeries)
class DeviceSeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'order')
    list_filter = ('brand',)
    search_fields = ('name', 'brand__name')
    list_editable = ('order',)


@admin.register(DevicePhone)
class DevicePhoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'series', 'release_year', 'order')
    list_filter = ('series__brand', 'series')
    search_fields = ('name', 'series__name')
    list_editable = ('order',)


@admin.register(DeviceIssue)
class DeviceIssueAdmin(admin.ModelAdmin):
    list_display = ('title', 'phone', 'icon_number', 'order')
    list_filter = ('phone__series__brand', 'phone')
    search_fields = ('title', 'phone__name')
    list_editable = ('order',)


@admin.register(IssueComparison)
class IssueComparisonAdmin(admin.ModelAdmin):
    list_display = ('title', 'issue', 'quality_type', 'total_price_display', 'quantity', 'is_in_stock')
    list_editable = ('quantity', 'is_in_stock')
    list_filter = ('quality_type', 'is_in_stock', 'issue__phone__series__brand')
    search_fields = ('title', 'issue__title', 'issue__phone__name')

    def total_price_display(self, obj):
        return f"{obj.total_price_uzs:,} so'm (${obj.price_usd})"
    total_price_display.short_description = "Umumiy narx"


@admin.register(RepairFAQ)
class RepairFAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order')
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
    list_display = ('order_id', 'client_name', 'phone_number', 'phone', 'status_badge', 'created_at')
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
