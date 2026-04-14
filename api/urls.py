from django.urls import path
from .views import *

urlpatterns = [
    path('Auth/login', LoginView.as_view(), name='login'),
    path('Menu/configuracion/<int:id_usuario>', MenuConfigView.as_view(), name='menu_config'),
    path('Permisos/<int:id_perfil>', PermisosByPerfilView.as_view(), name='permisos_by_perfil'),
    path('Permisos/update', UpdatePermisosView.as_view(), name='permisos_update'),
    path('Permisos/matriz/<int:id_perfil>', MatrizPermisosView.as_view(), name='permisos_matriz'),
    path('Seguridad/perfiles', PerfilesView.as_view(), name='perfiles'),
    path('Seguridad/perfil/<int:id>', PerfilDetailView.as_view(), name='perfil_detail'),
    path('Seguridad/modulos', ModulosView.as_view(), name='modulos'),
    path('Seguridad/modulo/<int:id>', ModuloDetailView.as_view(), name='modulo_detail'),
    path('Seguridad/vincular-menu', VincularMenuView.as_view(), name='vincular_menu'),
    path('Usuario', UsuarioView.as_view(), name='usuarios'),
    path('Usuario/<int:id>', UsuarioDetailView.as_view(), name='usuario_detail'),
    path('Usuario/status/<int:id>', UsuarioStatusView.as_view(), name='usuario_status'),
]