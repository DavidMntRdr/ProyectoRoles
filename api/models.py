from django.db import models

class Perfil(models.Model):
    strNombrePerfil = models.CharField(max_length=50, db_column='strNombrePerfil')
    bitAdministrador = models.BooleanField(default=False, db_column='bitAdministrador')

    class Meta:
        managed = False
        db_table = 'Seguridad_Perfil'

class Modulo(models.Model):
    strNombreModulo = models.CharField(max_length=100, db_column='strNombreModulo')

    class Meta:
        managed = False
        db_table = 'Seguridad_Modulo'

class Menu(models.Model):
    strNombreMenu = models.CharField(max_length=50, db_column='strNombreMenu')

    class Meta:
        managed = False
        db_table = 'Seguridad_Menu'

class MenuModulo(models.Model):
    idMenu = models.IntegerField(db_column='idMenu')
    idModulo = models.IntegerField(db_column='idModulo')

    class Meta:
        managed = False
        db_table = 'Seguridad_MenuModulo'

class PermisosPerfil(models.Model):
    idModulo = models.IntegerField(db_column='idModulo')
    idPerfil = models.IntegerField(db_column='idPerfil')
    bitAgregar = models.BooleanField(default=False, db_column='bitAgregar')
    bitEditar = models.BooleanField(default=False, db_column='bitEditar')
    bitConsulta = models.BooleanField(default=False, db_column='bitConsulta')
    bitEliminar = models.BooleanField(default=False, db_column='bitEliminar')
    bitDetalle = models.BooleanField(default=False, db_column='bitDetalle')

    class Meta:
        managed = False
        db_table = 'Seguridad_PermisosPerfil'

class Usuario(models.Model):
    
    strNombreUsuario = models.CharField(max_length=50, unique=True, db_column='strNombreUsuario')
    idPerfil = models.IntegerField(db_column='idPerfil')
    strPwd = models.CharField(max_length=255, db_column='strPwd')
    idEstadoUsuario = models.BooleanField(default=True, db_column='idEstadoUsuario')
    strCorreo = models.CharField(max_length=100, db_column='strCorreo')
    strNumeroCelular = models.CharField(max_length=15, db_column='strNumeroCelular')
    strImagenUrl = models.CharField(max_length=255, null=True, blank=True, db_column='strImagenUrl')

    class Meta:
        managed = False
        db_table = 'Seguridad_Usuario'
