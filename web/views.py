from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
import json

# ==================== NÚCLEO DE SEGURIDAD DINÁMICA ====================

def get_session_context(request):
    """Contexto estandarizado para los templates"""
    return {
        'token': request.session.get('jwt_token'),
        'usuario_id': request.session.get('usuario_id'),
        'username': request.session.get('username'),
        'perfil_id': request.session.get('perfil_id'),
    }

def validar_permiso_completo(request, nombre_modulo, bit_requerido='bitConsulta'):
    """
    Busca por NOMBRE de módulo y por el BIT específico (bitConsulta, bitAgregar, etc.)
    """
    perfil_id = request.session.get('perfil_id')
    token = request.session.get('jwt_token')

    if not token or not perfil_id: return False
    if int(perfil_id) == 1: return True  # SuperAdmin siempre pasa

    try:
        api_url = f"https://apirolescorp.bsite.net/api/Permisos/{perfil_id}"
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(api_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            permisos = response.json()
            for p in permisos:
                if p.get('nombreModulo', '').upper() == nombre_modulo.upper():
                    # Retorna el valor del bit que pedimos (True/False)
                    return p.get(bit_requerido, False)
    except:
        pass
    return False

# ==================== PROXY API (JSON Y ARCHIVOS) ====================

@csrf_exempt
def proxy_api(request, path):
    token = request.session.get('jwt_token')
    api_url = f"https://apirolescorp.bsite.net/api/{path}"
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        if request.method == 'GET':
            # AGREGAMOS params=request.GET para pasar la paginación y filtros
            response = requests.get(api_url, headers=headers, params=request.GET)
        elif request.method in ['POST', 'PUT']:
            if request.content_type and 'multipart' in request.content_type:
                files = {k: (f.name, f.read(), f.content_type) for k, f in request.FILES.items()}
                response = requests.request(request.method, api_url, files=files, data=dict(request.POST), headers=headers)
            else:
                data = json.loads(request.body) if request.body else {}
                response = requests.request(request.method, api_url, json=data, headers=headers)
        elif request.method == 'DELETE':
            response = requests.delete(api_url, headers=headers)
        else:
            return JsonResponse({'error': 'Método no permitido'}, status=405)
        
        # Devolvemos la respuesta de la API tal cual
        return JsonResponse(response.json(), status=response.status_code, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
# ==================== VISTAS DE USUARIOS (BIT CHECK) ====================

def usuarios_view(request):
    if not validar_permiso_completo(request, 'USUARIO', 'bitConsulta'):
        messages.error(request, "No tienes permiso para ver el listado de Usuarios.")
        return redirect('dashboard')
    return render(request, 'usuarios.html', get_session_context(request))

def usuario_nuevo_view(request):
    # AQUÍ ESTÁ EL CANDADO: Revisa el bitAgregar
    if not validar_permiso_completo(request, 'USUARIO', 'bitAgregar'):
        messages.error(request, "Tu perfil no tiene autoridad para crear usuarios.")
        return redirect('usuarios')
    return render(request, 'usuario_form.html', get_session_context(request))

def usuario_editar_view(request, id):
    # AQUÍ ESTÁ EL CANDADO: Revisa el bitEditar
    if not validar_permiso_completo(request, 'USUARIO', 'bitEditar'):
        messages.error(request, "No tienes permiso para editar registros.")
        return redirect('usuarios')
    context = get_session_context(request)
    context['id_editar'] = id
    return render(request, 'usuario_form.html', context)

# ==================== VISTAS DE SEGURIDAD ====================

def perfiles_view(request):
    if not validar_permiso_completo(request, 'PERFIL', 'bitConsulta'):
        return redirect('dashboard')
    return render(request, 'perfiles.html', get_session_context(request))

def permisos_perfil_view(request):
    if not validar_permiso_completo(request, 'PERMISOS PERFIL', 'bitConsulta'):
        return redirect('dashboard')
    return render(request, 'permisos_perfil.html', get_session_context(request))

# ==================== GESTIÓN DE MÓDULOS (DINÁMICO) ====================

def modulos_view(request):
    if not validar_permiso_completo(request, 'MÓDULO', 'bitConsulta'):
        return redirect('dashboard')
    return render(request, 'modulos.html', get_session_context(request))

def modulo_nuevo_view(request):
    """Vista para agregar módulos nuevos"""
    if not validar_permiso_completo(request, 'MÓDULO', 'bitAgregar'):
        messages.error(request, "Acceso denegado para crear módulos.")
        return redirect('modulos')
    return render(request, 'modulo_form.html', get_session_context(request))

# ==================== OTROS MÓDULOS Y DASHBOARD ====================

def dashboard_view(request):
    if not request.session.get('jwt_token'): return redirect('login')
    return render(request, 'dashboard.html', get_session_context(request))

def modulo_estatico_view(request, nombre_modulo):
    nombre_limpio = nombre_modulo.replace("-", " ").upper()
    if not validar_permiso_completo(request, nombre_limpio, 'bitConsulta'):
        messages.error(request, f"Acceso denegado al módulo {nombre_limpio}.")
        return redirect('dashboard')
    
    context = get_session_context(request)
    context['modulo'] = nombre_limpio
    return render(request, 'modulo_estatico.html', context)

# ==================== LOGIN / LOGOUT ====================

def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('usuario')
        password = request.POST.get('password')
        recaptcha = request.POST.get('g-recaptcha-response')

        if not recaptcha:
            messages.error(request, "Completa el captcha.")
            return render(request, 'login.html')

        api_url = "https://apirolescorp.bsite.net/api/Auth/login"
        try:
            response = requests.post(api_url, json={"usuario": usuario, "password": password}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                request.session['jwt_token'] = data['token']
                request.session['usuario_id'] = data['id']
                request.session['perfil_id'] = data['perfilId']
                request.session['username'] = data['username']
                return redirect('dashboard')
            else:
                messages.error(request, "Credenciales inválidas.")
        except:
            messages.error(request, "Error de conexión con la API.")
            
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    return redirect('login')

# ==================== HANDLERS ====================

# web/views.py
def error_404_view(request, exception):
    return render(request, 'errors/404.html', status=404)

def error_500_view(request):
    return render(request, 'errors/500.html', status=500)