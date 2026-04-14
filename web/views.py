from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import update_last_login
from django.contrib.auth.signals import user_logged_in
import requests
import json
from django.http.multipartparser import MultiPartParser

from api.models import Usuario, PermisosPerfil, Modulo

# ==================== NÚCLEO DE SEGURIDAD DINÁMICA ====================

def get_session_context(request):
    return {
        'token': request.session.get('jwt_token'),
        'usuario_id': request.session.get('usuario_id'),
        'username': request.session.get('username'),
        'perfil_id': request.session.get('perfil_id'),
    }

def validar_permiso_completo(request, nombre_modulo, bit_requerido='bitConsulta'):
    perfil_id = request.session.get('perfil_id')
    token = request.session.get('jwt_token')

    if not token or not perfil_id: 
        return False
    
    if int(perfil_id) == 1: 
        return True

    try:
        modulo = Modulo.objects.filter(strNombreModulo__iexact=nombre_modulo).first()
        if not modulo:
            return False
            
        permiso = PermisosPerfil.objects.filter(idPerfil=perfil_id, idModulo=modulo.id).first()
        if permiso:
            return getattr(permiso, bit_requerido, False)
    except Exception as e:
        print(f"Error en validación local: {e}")
        
    return False

# ==================== PROXY API INTERNO ====================



@csrf_exempt
def proxy_api(request, path):
    if os.environ.get('RENDER'):
        api_url = f"http://127.0.0.1:10000/api/{path}"
    else:
        scheme = 'https' if request.is_secure() else 'http'
        api_url = f"{scheme}://{request.get_host()}/api/{path}"
    
    token = request.session.get('jwt_token')
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        if request.method in ['POST', 'PUT']:
            content_type = request.content_type or ''
            
            if 'multipart/form-data' in content_type:
                if request.method == 'PUT':
                    data_parser, files_parser = MultiPartParser(
                        request.META, request, request.upload_handlers
                    ).parse()
                    data = data_parser.dict()
                    files_dict = {k: (f.name, f.read(), f.content_type) for k, f in files_parser.items()}
                else:
                    data = request.POST.dict()
                    files_dict = {k: (f.name, f.read(), f.content_type) for k, f in request.FILES.items()}

                response = requests.request(
                    method=request.method,
                    url=api_url,
                    files=files_dict,
                    data=data,
                    headers=headers,
                    timeout=30
                )
            
            else:
                try:
                    body_data = json.loads(request.body.decode('utf-8')) if request.body else {}
                except:
                    body_data = {}
                
                response = requests.request(
                    method=request.method,
                    url=api_url,
                    json=body_data,
                    headers=headers,
                    timeout=30
                )

        elif request.method == 'GET':
            response = requests.get(api_url, headers=headers, params=request.GET, timeout=30)
            
        elif request.method == 'DELETE':
            response = requests.delete(api_url, headers=headers, timeout=30)
            
        else:
            return JsonResponse({'error': 'Metodo no soportado'}, status=405)

        try:
            return JsonResponse(response.json(), status=response.status_code, safe=False)
        except:
            return JsonResponse({'data': response.text}, status=response.status_code)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ==================== LOGIN / LOGOUT ====================

def login_view(request):
    if request.method == 'POST':
        usuario_val = request.POST.get('usuario')
        password_val = request.POST.get('password')
        recaptcha = request.POST.get('g-recaptcha-response')

        if not recaptcha and not settings.DEBUG:
            messages.error(request, "Por favor, completa el reCAPTCHA.")
            return render(request, 'login.html')

        from api.views import LoginView
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        api_request = factory.post('/api/Auth/login', {'usuario': usuario_val, 'password': password_val}, format='json')
        
        view = LoginView.as_view()
        response = view(api_request)

        if response.status_code == 200:
            data = response.data
            request.session['jwt_token'] = data['token']
            request.session['usuario_id'] = data['id']
            request.session['perfil_id'] = data['perfilId']
            request.session['username'] = data['username']
            
            print(f"LOGIN EXITOSO: {data['username']}")
            print(f"TOKEN guardado: {data['token'][:50]}...")
            
            return redirect('dashboard')
        else:
            messages.error(request, "Credenciales invalidas o cuenta no autorizada.")
            
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

# ==================== VISTAS DE MÓDULOS (CRUD) ====================

def dashboard_view(request):
    if not request.session.get('jwt_token'): 
        return redirect('login')
    return render(request, 'dashboard.html', get_session_context(request))

def usuarios_view(request):
    if not validar_permiso_completo(request, 'USUARIO', 'bitConsulta'):
        messages.error(request, "No tienes permiso para ver este módulo.")
        return redirect('dashboard')
    return render(request, 'usuarios.html', get_session_context(request))

def usuario_nuevo_view(request):
    if not validar_permiso_completo(request, 'USUARIO', 'bitAgregar'):
        return redirect('usuarios')
    return render(request, 'usuario_form.html', get_session_context(request))

def usuario_editar_view(request, id):
    if not validar_permiso_completo(request, 'USUARIO', 'bitEditar'):
        return redirect('usuarios')
    context = get_session_context(request)
    context['id_editar'] = id
    return render(request, 'usuario_form.html', context)

def perfiles_view(request):
    if not validar_permiso_completo(request, 'PERFIL', 'bitConsulta'):
        return redirect('dashboard')
    return render(request, 'perfiles.html', get_session_context(request))

def permisos_perfil_view(request):
    if not validar_permiso_completo(request, 'PERMISOS PERFIL', 'bitConsulta'):
        return redirect('dashboard')
    return render(request, 'permisos_perfil.html', get_session_context(request))

def modulos_view(request):
    if not validar_permiso_completo(request, 'MÓDULO', 'bitConsulta'):
        return redirect('dashboard')
    return render(request, 'modulos.html', get_session_context(request))

def modulo_nuevo_view(request):
    if not validar_permiso_completo(request, 'MÓDULO', 'bitAgregar'):
        return redirect('modulos')
    return render(request, 'modulo_form.html', get_session_context(request))

def modulo_estatico_view(request, nombre_modulo):
    nombre_limpio = nombre_modulo.replace("-", " ").upper()
    if not validar_permiso_completo(request, nombre_limpio, 'bitConsulta'):
        return redirect('dashboard')
    
    context = get_session_context(request)
    context['modulo'] = nombre_limpio
    return render(request, 'modulo_estatico.html', context)

# ==================== MANEJADORES DE ERROR ====================

def error_404_view(request, exception):
    return render(request, 'errors/404.html', status=404)

def error_500_view(request):
    return render(request, 'errors/500.html', status=500)