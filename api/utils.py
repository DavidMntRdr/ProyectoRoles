import bcrypt
import os
import uuid
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import PermisosPerfil

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def save_uploaded_file(file):
    if not file:
        return None
    
    ext = os.path.splitext(file.name)[1].lower()
    filename = f"{uuid.uuid4()}{ext}"
    
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    return f"/uploads/{filename}"

def validar_permiso(request, id_modulo, accion):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False

    token = auth_header.split(' ')[1]
    try:
        access_token = AccessToken(token)
        perfil_id = access_token.get('perfilId')
    except (InvalidToken, TokenError):
        return False

    if perfil_id == 1:
        return True

    try:
        permiso = PermisosPerfil.objects.filter(idPerfil=perfil_id, idModulo=id_modulo).first()
        if not permiso:
            return False
    except Exception:
        return False

    mapa = {
        'C': 'bitConsulta',
        'A': 'bitAgregar',
        'E': 'bitEditar',
        'D': 'bitEliminar',
        'V': 'bitDetalle'
    }
    
    return getattr(permiso, mapa.get(accion, 'bitConsulta'), False)