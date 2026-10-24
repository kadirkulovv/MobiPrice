from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

from core import views as core_views

# Global non-prefixed routes
urlpatterns = [
    path('robots.txt', core_views.robots_txt_view, name='robots_txt'),
    path('sitemap.xml', core_views.sitemap_xml_view, name='sitemap_xml'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('api/', include('core.api_urls')),
]

# Language prefixed routes (/uz/, /ru/, /en/)
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
