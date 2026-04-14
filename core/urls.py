from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('web.urls')),
]

urlpatterns += [
    re_path(r'^uploads/(?P<path>.*)$', serve, {
        'document_root': os.path.join(settings.BASE_DIR, 'wwwroot', 'uploads'),
    }),
]

handler404 = 'web.views.error_404_view'
handler500 = 'web.views.error_500_view'