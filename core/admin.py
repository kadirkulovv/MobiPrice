from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison,
    RepairFAQ, Review, ServiceOrder, TeamMember, BotAdmin, TelegramUser, AuthToken
)



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
    list_display = ('client_name', 'telegram_user', 'device_model', 'service_type', 'rating_stars', 'is_verified', 'created_at')
    list_filter = ('rating', 'is_verified', 'created_at')
    search_fields = ('client_name', 'telegram_user__username', 'device_model', 'comment')
    list_editable = ('is_verified',)

    def rating_stars(self, obj):
        return '★' * obj.rating
    rating_stars.short_description = "Baho"


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id',
        'client_name',
        'phone_number',
        'telegram_user',
        'phone',
        'service_type',
        'distance_display',
        'delivery_fee_display',
        'final_total_display',
        'status_badge',
        'created_at',
    )
    list_filter = ('status', 'service_type', 'created_at')
    search_fields = (
        'order_id',
        'client_name',
        'phone_number',
        'telegram_user__username',
        'telegram_user__first_name',
        'telegram_user__phone_number',
        'telegram_user__telegram_id',
        'notes',
    )
    readonly_fields = ('order_id', 'courier_token', 'courier_token_expires_at', 'created_at')

    def distance_display(self, obj):
        if obj.distance_km is None:
            return '-'
        return f"{obj.distance_km:.2f} km"
    distance_display.short_description = "Masofa"

    def delivery_fee_display(self, obj):
        if obj.delivery_fee_uzs is None:
            return '-'
        return f"{int(obj.delivery_fee_uzs):,} so'm"
    delivery_fee_display.short_description = "Kuryer narxi"

    def final_total_display(self, obj):
        if obj.final_total_uzs is not None:
            return f"{int(obj.final_total_uzs):,} so'm"
        if obj.comparison_id and obj.comparison:
            return f"{int(obj.comparison.total_price_uzs):,} so'm"
        return '-'
    final_total_display.short_description = "Jami summa"

    def status_badge(self, obj):
        colors = {
            'pending_location': '#8b5cf6',
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


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'role', 'experience', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('full_name', 'role')


@admin.register(BotAdmin)
class BotAdminAdmin(admin.ModelAdmin):
    list_display = ('user_display', 'full_name', 'role', 'is_active', 'telegram_id', 'added_by', 'created_at')
    list_filter = ('role', 'is_active')
    list_editable = ('role', 'is_active')
    search_fields = ('username', 'full_name', 'telegram_id')

    def user_display(self, obj):
        return f"@{obj.username}" if obj.username else (obj.full_name or str(obj.telegram_id))
    user_display.short_description = "Admin / Menejer"


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'full_name', 'username', 'phone_number', 'created_at', 'updated_at')
    search_fields = ('telegram_id', 'first_name', 'last_name', 'username', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ('short_token', 'telegram_user', 'expected_telegram_id', 'is_confirmed', 'is_used', 'rejected_reason', 'expires_at', 'created_at')
    list_filter = ('is_confirmed', 'is_used', 'rejected_reason', 'created_at')
    search_fields = ('token', 'session_key', 'expected_telegram_id', 'telegram_user__username', 'telegram_user__first_name')
    readonly_fields = ('token', 'session_key', 'created_at')

    def short_token(self, obj):
        return f"{obj.token[:12]}..." if len(obj.token) > 12 else obj.token
    short_token.short_description = "Token"


