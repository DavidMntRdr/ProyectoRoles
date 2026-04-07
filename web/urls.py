from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/login/'), name='index'),
    path('login/', views.login_view, name='login'),
    path('modulos/nuevo/', views.modulo_nuevo_view, name='modulo_nuevo'),
    path('logout/', views.logout_view, name='logout'),
    path('api/proxy/<path:path>', views.proxy_api, name='proxy_api'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('perfiles/', views.perfiles_view, name='perfiles'),
    path('modulos/', views.modulos_view, name='modulos'),
    path('permisos_perfil/', views.permisos_perfil_view, name='permisos_perfil'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_nuevo_view, name='usuario_nuevo'),
    path('usuarios/editar/<int:id>/', views.usuario_editar_view, name='usuario_editar'),    
    path('modulo/<str:nombre_modulo>/', views.modulo_estatico_view, name='modulo_estatico'),
]

handler404 = 'web.views.error_404_view'
handler500 = 'web.views.error_500_view'