from django.shortcuts import redirect

class JwtAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rutas libres (Login y archivos CSS/JS)
        exempt_urls = ['/login/', '/static/', '/captcha/']
        
        path = request.path
        if not any(path.startswith(url) for url in exempt_urls):
            # Si no hay token en la sesión de Django, pa' fuera
            if 'jwt_token' not in request.session:
                return redirect('/login/')

        return self.get_response(request)