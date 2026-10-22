from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/models/by-brand/<int:brand_id>/', views.api_models_by_brand, name='api_models_by_brand'),
    path('api/models/search/', views.api_search_models, name='api_search_models'),
    path('api/parts/options/', views.api_part_options, name='api_part_options'),
    path('api/orders/submit/', views.api_submit_order, name='api_submit_order'),
]
