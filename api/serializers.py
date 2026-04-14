from rest_framework import serializers
from .models import Perfil, Usuario, Modulo, PermisosPerfil, Menu, MenuModulo

class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'



class UsuarioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 
            'strNombreUsuario', 
            'idPerfil', 
            'strCorreo', 
            'strNumeroCelular', 
            'idEstadoUsuario', 
            'strImagenUrl'  
        ]

class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = '__all__'


class PermisosPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = PermisosPerfil
        fields = '__all__'


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = '__all__'


class MenuModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuModulo
        fields = '__all__'