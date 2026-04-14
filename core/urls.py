
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('web.urls')),
]

if settings.DEBUG:
    urlpatterns += static('/uploads/', document_root=os.path.join(settings.BASE_DIR, 'wwwroot', 'uploads'))

handler404 = 'web.views.error_404_view'
handler500 = 'web.views.error_500_view'