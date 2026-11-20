from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroForm, EditarPerfilForm

def registro(request):
    if request.user.is_authenticated:
        return redirect('catalogo')
        
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.rol = 'solicitante' # Forzamos a que todos los nuevos sean solicitantes
            user.save()
            
            # Iniciar sesión automáticamente después de registrarse
            login(request, user)
            messages.success(request, "¡Bienvenido a SmartLocker! Tu cuenta ha sido creada exitosamente.")
            return redirect('catalogo')
    else:
        form = RegistroForm()
    
    return render(request, 'users/registro.html', {'form': form})

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos personales se han actualizado correctamente.")
            return redirect('editar_perfil')
    else:
        form = EditarPerfilForm(instance=request.user)
        
    return render(request, 'users/editar_perfil.html', {'form': form})