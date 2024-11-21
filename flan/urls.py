from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    #path('accounts/', include('dj_rest_auth.urls')),
    #path('accounts/', include('allauth.urls')),
    path('ads/', include('ads.urls')),
    path('family/', include('family.urls')),
    path('', include('personal.urls')),
    path('sch_requests/', include('sch_requests.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)