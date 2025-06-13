"""
URL configuration for Casino project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic.base import TemplateView
from Core.views import custom_csrf_failure

# Import sitemaps
from .sitemaps import StaticSitemap, GameCardsSitemap, AboutSitemap

# changing admin panel title and info
admin.site.site_header = "Casino Admin"
admin.site.site_title = "Casino Admin Portal"
admin.site.index_title = "Welcome to Casino Game Portal"

sitemaps = {
    'static': StaticSitemap,
    'gamecards': GameCardsSitemap,
    'about': AboutSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('Core.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    
    # SEO URLs
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', include('robots.urls')),
    
    # Debug toolbar URLs (only active in DEBUG mode)
    # path('__debug__/', include('debug_toolbar.urls')),
]

# Add custom CSRF failure view
handler403 = custom_csrf_failure

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)