from django.urls import path
from . import views

urlpatterns = [
    # 5-Step Hierarchy Endpoints
    path('series/by-brand/<int:brand_id>/', views.api_series_by_brand, name='api_series_by_brand'),
    path('phones/by-series/<int:series_id>/', views.api_phones_by_series, name='api_phones_by_series'),
    path('issues/by-phone/<int:phone_id>/', views.api_issues_by_phone, name='api_issues_by_phone'),
    path('comparisons/by-issue/<int:issue_id>/', views.api_comparisons_by_issue, name='api_comparisons_by_issue'),
    path('phones/search/', views.api_search_phones, name='api_search_phones'),
    path('orders/submit/', views.api_submit_order, name='api_submit_order'),
]
