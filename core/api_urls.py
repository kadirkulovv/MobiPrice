from django.urls import path
from . import views

urlpatterns = [
    path('models/by-brand/<int:brand_id>/', views.api_models_by_brand, name='api_models_by_brand'),
    path('models/search/', views.api_search_models, name='api_search_models'),
    path('parts/options/', views.api_part_options, name='api_part_options'),
    path('orders/submit/', views.api_submit_order, name='api_submit_order'),
]
