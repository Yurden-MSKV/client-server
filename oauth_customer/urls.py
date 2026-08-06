from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from core.views import sync_user_view, profile_page, index

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('', index, name='index'),
    path('profile/', profile_page, name='profile_page'),
    path('social/', include('social_django.urls', namespace='social')),
    path('logout/', include('django.contrib.auth.urls')),
    path('api/sync/user/', sync_user_view, name='sync_user'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
