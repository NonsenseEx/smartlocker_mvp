from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Equipo

# @login_required obliga a que el usuario inicie sesión antes de ver esto (Seguridad OWASP)
@login_required 
def catalogo_view(request):
    # El ORM de Django trae todos los equipos (evita Inyección SQL)
    equipos = Equipo.objects.all()
    
    # Pasamos los equipos al template
    context = {
        'equipos': equipos
    }
    return render(request, 'inventory/catalogo.html', context)