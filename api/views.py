import bcrypt
import os
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .models import Perfil, Usuario, Modulo, PermisosPerfil, Menu, MenuModulo
from .serializers import (
    PerfilSerializer, UsuarioSerializer, UsuarioListSerializer, 
    ModuloSerializer, PermisosPerfilSerializer
)
from .utils import hash_password, check_password, save_uploaded_file, validar_permiso
from rest_framework.parsers import MultiPartParser, FormParser


# ==================== AUTH CONTROLLER ====================

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        usuario_nom = request.data.get('usuario')
        password = request.data.get('password')

        if not usuario_nom or not password:
            return Response({'message': 'Usuario y contraseña requeridos'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Usuario.objects.get(strNombreUsuario=usuario_nom)
        except Usuario.DoesNotExist:
            return Response({'message': 'Usuario o contraseña incorrectos'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.strPwd):
            return Response({'message': 'Usuario o contraseña incorrectos'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.idEstadoUsuario:
            return Response({'message': 'El usuario se encuentra INACTIVO o ha sido dado de baja.'}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        refresh['perfilId'] = user.idPerfil
        refresh['id'] = user.id

        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'username': user.strNombreUsuario,
            'id': user.id,
            'perfilId': user.idPerfil
        })


# ==================== MENU CONTROLLER ====================

class MenuConfigView(APIView):
    permission_classes = [AllowAny]  

    def get(self, request, id_usuario):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        print(f"MENU - Token recibido: {bool(token)}")
        
        try:
            usuario = Usuario.objects.get(id=id_usuario)
        except Usuario.DoesNotExist:
            return Response([])

        permisos = PermisosPerfil.objects.filter(idPerfil=usuario.idPerfil, bitConsulta=True)
        modulos_con_permiso = list(permisos.values_list('idModulo', flat=True))
        menu_modulos = MenuModulo.objects.filter(idModulo__in=modulos_con_permiso)
        menus_dict = {}

        for mm in menu_modulos:
            if mm.idMenu not in menus_dict:
                try:
                    menu = Menu.objects.get(id=mm.idMenu)
                    menus_dict[mm.idMenu] = {
                        'nombreMenu': menu.strNombreMenu,
                        'modulos': []
                    }
                except Menu.DoesNotExist:
                    continue

            try:
                modulo = Modulo.objects.get(id=mm.idModulo)
                permiso = permisos.get(idModulo=mm.idModulo)

                menus_dict[mm.idMenu]['modulos'].append({
                    'nombreModulo': modulo.strNombreModulo,
                    'url': f"/modulo/{modulo.strNombreModulo.lower().replace(' ', '-')}",
                    'permisos': {
                        'canAdd': permiso.bitAgregar,
                        'canEdit': permiso.bitEditar,
                        'canDelete': permiso.bitEliminar,
                        'canView': permiso.bitConsulta,
                        'canDetail': permiso.bitDetalle
                    }
                })
            except (Modulo.DoesNotExist, PermisosPerfil.DoesNotExist):
                continue

        resultado = [v for v in menus_dict.values() if v['modulos']]
        return Response(resultado)

class VincularMenuView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_menu = request.data.get('IdMenu')
        id_modulo = request.data.get('IdModulo')
        if not id_menu or not id_modulo:
            return Response({'message': 'IdMenu y IdModulo requeridos'}, status=400)
        
        MenuModulo.objects.create(idMenu=id_menu, idModulo=id_modulo)
        return Response({'message': 'Vinculado correctamente'})

# ==================== PERMISOS CONTROLLER ====================

class PermisosByPerfilView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id_perfil):
        if not validar_permiso(request, 3, 'C'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        todos_modulos = Modulo.objects.all()
        permisos_dict = {p.idModulo: p for p in PermisosPerfil.objects.filter(idPerfil=id_perfil)}

        resultado = []
        for m in todos_modulos:
            p = permisos_dict.get(m.id)
            resultado.append({
                'idModulo': m.id,
                'nombreModulo': m.strNombreModulo,
                'bitConsulta': p.bitConsulta if p else False,
                'bitAgregar': p.bitAgregar if p else False,
                'bitEditar': p.bitEditar if p else False,
                'bitEliminar': p.bitEliminar if p else False,
                'bitDetalle': p.bitDetalle if p else False
            })
        return Response(resultado)

class UpdatePermisosView(APIView):
    permission_classes = [AllowAny]

    def put(self, request):
        if not validar_permiso(request, 3, 'E'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        lista = request.data

        for item in lista:
            permiso, created = PermisosPerfil.objects.update_or_create(
                idModulo=item['idModulo'],
                idPerfil=item['idPerfil'],
                defaults={
                    'bitAgregar': item.get('bitAgregar', False),
                    'bitEditar': item.get('bitEditar', False),
                    'bitConsulta': item.get('bitConsulta', False),
                    'bitEliminar': item.get('bitEliminar', False),
                    'bitDetalle': item.get('bitDetalle', False)
                }
            )

        return Response({'message': 'Permisos actualizados correctamente'})


class MatrizPermisosView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id_perfil):
        if not validar_permiso(request, 3, 'C'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        todos_modulos = Modulo.objects.all()
        permisos_dict = {p.idModulo: p for p in PermisosPerfil.objects.filter(idPerfil=id_perfil)}

        resultado = []
        for m in todos_modulos:
            p = permisos_dict.get(m.id)
            resultado.append({
                'idModulo': m.id,
                'nombreModulo': m.strNombreModulo,
                'permisos': {
                    'bitAgregar': p.bitAgregar if p else False,
                    'bitEditar': p.bitEditar if p else False,
                    'bitEliminar': p.bitEliminar if p else False,
                    'bitConsulta': p.bitConsulta if p else False,
                    'bitDetalle': p.bitDetalle if p else False
                }
            })

        return Response(resultado)


# ==================== SEGURIDAD CONTROLLER (Perfiles) ====================

class PerfilesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not validar_permiso(request, 2, 'C'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        perfiles = Perfil.objects.all()
        serializer = PerfilSerializer(perfiles, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not validar_permiso(request, 2, 'A'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PerfilSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PerfilDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):
        if not validar_permiso(request, 2, 'C'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            perfil = Perfil.objects.get(id=id)
            serializer = PerfilSerializer(perfil)
            return Response(serializer.data)
        except Perfil.DoesNotExist:
            return Response({'message': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, id):
        if not validar_permiso(request, 2, 'E'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            perfil = Perfil.objects.get(id=id)
            serializer = PerfilSerializer(perfil, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Perfil.DoesNotExist:
            return Response({'message': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id):
        if not validar_permiso(request, 2, 'D'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            perfil = Perfil.objects.get(pk=id)
            
            PermisosPerfil.objects.filter(idPerfil=id).delete()
            
            perfil.delete()
            
            return Response({'message': 'Perfil eliminado correctamente'})
            
        except Perfil.DoesNotExist:
            return Response({'message': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:

            print(f"Error real: {str(e)}") 
            return Response({'message': f'Error de base de datos: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ==================== MÓDULOS CONTROLLER ====================

class ModulosView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        if not validar_permiso(request, 14, 'C'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        modulos = Modulo.objects.all()
        serializer = ModuloSerializer(modulos, many=True)
        return Response(serializer.data)

    def post(self, request):
        if not validar_permiso(request, 14, 'A'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ModuloSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ModuloDetailView(APIView):
    permission_classes = [AllowAny]
    def put(self, request, id):
        if not validar_permiso(request, 14, 'E'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            modulo = Modulo.objects.get(id=id)
            serializer = ModuloSerializer(modulo, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Modulo.DoesNotExist:
            return Response({'message': 'Módulo no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id):
        if not validar_permiso(request, 14, 'D'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            modulo = Modulo.objects.get(id=id)
            PermisosPerfil.objects.filter(idModulo=id).delete()
            MenuModulo.objects.filter(idModulo=id).delete()
            modulo.delete()
            return Response({'message': 'Módulo eliminado'})
        except Modulo.DoesNotExist:
            return Response({'message': 'Módulo no encontrado'}, status=status.HTTP_404_NOT_FOUND)


# ==================== USUARIO CONTROLLER ====================

class UsuarioView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        if not validar_permiso(request, 4, 'C'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('pageSize', 5))
        buscar = request.query_params.get('buscar', '')

        query = Usuario.objects.all().order_by('id')
        if buscar:
            query = query.filter(strNombreUsuario__icontains=buscar)

        total = query.count()
        start = (page - 1) * page_size
        usuarios = query[start:start + page_size]

        serializer = UsuarioListSerializer(usuarios, many=True)
        return Response({
            'total': total,
            'data': serializer.data,
            'page': page,
            'pageSize': page_size
        })

    def post(self, request):
        if not validar_permiso(request, 4, 'A'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        nombre = request.data.get('strNombreUsuario')
        if Usuario.objects.filter(strNombreUsuario=nombre).exists():
            return Response({'message': 'El nombre de usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)

        hashed = hash_password(request.data.get('strPwd', ''))

        usuario = Usuario.objects.create(
            strNombreUsuario=nombre,
            idPerfil=request.data.get('idPerfil'),
            strPwd=hashed,
            strCorreo=request.data.get('strCorreo', ''),
            strNumeroCelular=request.data.get('strNumeroCelular', ''),
            idEstadoUsuario=True
        )

        foto = request.FILES.get('strImagenUrl')
        if foto:
            import uuid
            path_directorio = os.path.join(settings.MEDIA_ROOT, 'uploads')
            if not os.path.exists(path_directorio):
                os.makedirs(path_directorio)
                
            extension = os.path.splitext(foto.name)[1]
            nombre_archivo = f"{uuid.uuid4()}{extension}"
            
            ruta_fisica = os.path.join(path_directorio, nombre_archivo)
            with open(ruta_fisica, 'wb+') as destination:
                for chunk in foto.chunks():
                    destination.write(chunk)
            
            usuario.strImagenUrl = f"/uploads/{nombre_archivo}"
            usuario.save()

        return Response({'id': usuario.id, 'message': 'Usuario creado'}, status=status.HTTP_201_CREATED)


class UsuarioDetailView(APIView):
    permission_classes = [AllowAny]
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request, id):
        if not validar_permiso(request, 4, 'C'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            usuario = Usuario.objects.get(id=id)
            serializer = UsuarioSerializer(usuario)
            return Response(serializer.data)
        except Usuario.DoesNotExist:
            return Response({'message': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, id):
        if not validar_permiso(request, 4, 'E'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            usuario = Usuario.objects.get(id=id)
            usuario.strNombreUsuario = request.data.get('strNombreUsuario', usuario.strNombreUsuario)
            usuario.idPerfil = request.data.get('idPerfil', usuario.idPerfil)
            usuario.strCorreo = request.data.get('strCorreo', usuario.strCorreo)
            usuario.strNumeroCelular = request.data.get('strNumeroCelular', usuario.strNumeroCelular)
            
            estado = request.data.get('idEstadoUsuario')
            if estado is not None:
                usuario.idEstadoUsuario = str(estado).lower() in ['true', '1']

            nueva_password = request.data.get('strPwd')
            if nueva_password:
                usuario.strPwd = hash_password(nueva_password)

            foto = request.FILES.get('strImagenUrl')
            if foto:
                import uuid
                path_directorio = os.path.join(settings.MEDIA_ROOT, 'uploads')
                if not os.path.exists(path_directorio):
                    os.makedirs(path_directorio)
                    
                extension = os.path.splitext(foto.name)[1]
                nombre_archivo = f"{uuid.uuid4()}{extension}"
                
                ruta_fisica = os.path.join(path_directorio, nombre_archivo)
                with open(ruta_fisica, 'wb+') as destination:
                    for chunk in foto.chunks():
                        destination.write(chunk)
                
                usuario.strImagenUrl = f"/uploads/{nombre_archivo}"

            usuario.save()
            return Response({'message': 'Usuario actualizado'})
        except Usuario.DoesNotExist:
            return Response({'message': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id):
        if not validar_permiso(request, 4, 'D'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            usuario = Usuario.objects.get(id=id)
            usuario.delete()
            return Response({'message': 'Usuario eliminado'})
        except Usuario.DoesNotExist:
            return Response({'message': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class UsuarioStatusView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, id):
        if not validar_permiso(request, 4, 'E'):
            return Response({'message': 'No tiene permiso'}, status=status.HTTP_403_FORBIDDEN)

        try:
            usuario = Usuario.objects.get(id=id)
            nuevo_estado = request.data
            usuario.idEstadoUsuario = str(nuevo_estado).lower() in ['true', '1']
            usuario.save()
            return Response({'message': 'Estado actualizado'})
        except Usuario.DoesNotExist:
            return Response({'message': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)